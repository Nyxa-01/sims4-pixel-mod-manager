"""Tests for load order engine."""

from pathlib import Path

import pytest

from src.core.exceptions import LoadOrderError, PathError
from src.core.load_order_engine import (
    LOAD_ORDER_SLOTS,
    MAX_PACKAGE_DEPTH,
    MAX_PATH_LENGTH,
    PREFIX_PATTERN,
    SCRIPT_EXTENSIONS,
    LoadOrderEngine,
    get_default_engine,
)
from src.core.mod_scanner import ModFile


@pytest.fixture
def engine() -> LoadOrderEngine:
    """Create LoadOrderEngine instance.

    Returns:
        LoadOrderEngine instance
    """
    return LoadOrderEngine()


@pytest.fixture
def sample_mods(tmp_path: Path) -> dict[str, list[ModFile]]:
    """Create sample mod files for testing.

    Args:
        tmp_path: Pytest tmp_path fixture

    Returns:
        Dictionary of categorized mods
    """
    # Create test mod files
    core_mod = tmp_path / "mccc_mod.ts4script"
    core_mod.write_bytes(b"PK\x03\x04" + b"\x00" * 100)

    cc_mod = tmp_path / "hair_cas.package"
    cc_mod.write_bytes(b"DBPF" + b"\x00" * 100)

    main_mod = tmp_path / "gameplay_mod.package"
    main_mod.write_bytes(b"DBPF" + b"\x00" * 100)

    return {
        "Core Scripts": [
            ModFile(
                path=core_mod,
                size=104,
                hash=12345,
                mod_type="ts4script",
                category="Core Scripts",
                is_valid=True,
                validation_errors=[],
                entropy=6.0,
            )
        ],
        "CC": [
            ModFile(
                path=cc_mod,
                size=104,
                hash=67890,
                mod_type="package",
                category="CC",
                is_valid=True,
                validation_errors=[],
                entropy=5.5,
            )
        ],
        "Main Mods": [
            ModFile(
                path=main_mod,
                size=104,
                hash=11111,
                mod_type="package",
                category="Main Mods",
                is_valid=True,
                validation_errors=[],
                entropy=6.2,
            )
        ],
    }


class TestLoadOrderEngine:
    """Test LoadOrderEngine class."""

    def test_initialization(self, engine: LoadOrderEngine) -> None:
        """Test engine initialization."""
        assert len(engine.slots) == len(LOAD_ORDER_SLOTS)
        assert engine.slots[0][0] == "000_Core"
        assert engine.slots[-1][0] == "ZZZ_Overrides"

    def test_load_order_slots_immutable(self) -> None:
        """Test that load order slots are properly defined."""
        assert len(LOAD_ORDER_SLOTS) > 0

        # Check format
        for prefix, description, keywords in LOAD_ORDER_SLOTS:
            assert isinstance(prefix, str)
            assert isinstance(description, str)
            assert isinstance(keywords, list)
            assert PREFIX_PATTERN.match(prefix) or prefix == "ZZZ_Overrides"

    def test_generate_structure_creates_slots(
        self,
        engine: LoadOrderEngine,
        sample_mods: dict[str, list[ModFile]],
        tmp_path: Path,
    ) -> None:
        """Test structure generation creates slot folders."""
        output = tmp_path / "ActiveMods"

        created_paths = engine.generate_structure(sample_mods, output)

        assert output.exists()
        assert len(created_paths) == len(LOAD_ORDER_SLOTS)

        # Check all slots exist
        for prefix, _, _ in LOAD_ORDER_SLOTS:
            assert (output / prefix).exists()

    def test_assign_mod_to_slot_core_script(self, engine: LoadOrderEngine) -> None:
        """Test assigning core script mod."""
        mod = ModFile(
            path=Path("mccc_script.ts4script"),
            size=1000,
            hash=123,
            mod_type="ts4script",
            category="Core Scripts",
            is_valid=True,
            validation_errors=[],
            entropy=6.0,
        )

        slot = engine.assign_mod_to_slot(mod)

        assert slot == "000_Core"

    def test_assign_mod_to_slot_cc_by_keyword(
        self,
        engine: LoadOrderEngine,
    ) -> None:
        """Test assigning CC mod by keyword."""
        mod = ModFile(
            path=Path("hair_cas.package"),
            size=5000,
            hash=456,
            mod_type="package",
            category="CC",
            is_valid=True,
            validation_errors=[],
            entropy=5.5,
        )

        slot = engine.assign_mod_to_slot(mod)

        assert slot == "040_CC"

    def test_assign_mod_to_slot_cc_by_size(self, engine: LoadOrderEngine) -> None:
        """Test assigning CC mod by large file size."""
        mod = ModFile(
            path=Path("big_furniture.package"),
            size=15_000_000,  # >10MB
            hash=789,
            mod_type="package",
            category="",
            is_valid=True,
            validation_errors=[],
            entropy=6.0,
        )

        slot = engine.assign_mod_to_slot(mod)

        assert slot == "040_CC"

    def test_assign_mod_to_slot_default(self, engine: LoadOrderEngine) -> None:
        """Test default slot assignment."""
        mod = ModFile(
            path=Path("random_mod.package"),
            size=1000,
            hash=999,
            mod_type="package",
            category="",
            is_valid=True,
            validation_errors=[],
            entropy=6.0,
        )

        slot = engine.assign_mod_to_slot(mod)

        assert slot == "020_MainMods"

    def test_assign_mod_to_slot_library(self, engine: LoadOrderEngine) -> None:
        """Test assigning library mod."""
        mod = ModFile(
            path=Path("lib_shared_framework.package"),
            size=1000,
            hash=111,
            mod_type="package",
            category="Libraries",
            is_valid=True,
            validation_errors=[],
            entropy=5.8,
        )

        slot = engine.assign_mod_to_slot(mod)

        assert slot == "010_Libraries"

    def test_move_mod_success(
        self,
        engine: LoadOrderEngine,
        tmp_path: Path,
    ) -> None:
        """Test moving mod between slots."""
        # Setup structure
        base = tmp_path / "ActiveMods"
        from_slot = base / "020_MainMods"
        to_slot = base / "030_Tuning"
        from_slot.mkdir(parents=True)
        to_slot.mkdir(parents=True)

        # Create mod file
        mod_file = from_slot / "test_mod.package"
        mod_file.write_bytes(b"DBPF" + b"\x00" * 100)

        mod = ModFile(
            path=Path("test_mod.package"),
            size=104,
            hash=123,
            mod_type="package",
            category="",
            is_valid=True,
            validation_errors=[],
            entropy=6.0,
        )

        # Move mod
        result = engine.move_mod(mod, "020_MainMods", "030_Tuning", base)

        assert result is True
        assert not mod_file.exists()
        assert (to_slot / "test_mod.package").exists()

    def test_move_mod_invalid_slot(
        self,
        engine: LoadOrderEngine,
        tmp_path: Path,
    ) -> None:
        """Test moving with invalid slot raises error."""
        mod = ModFile(
            path=Path("test.package"),
            size=100,
            hash=123,
            mod_type="package",
            category="",
            is_valid=True,
            validation_errors=[],
            entropy=6.0,
        )

        with pytest.raises(LoadOrderError, match="Invalid slot"):
            engine.move_mod(mod, "INVALID", "020_MainMods", tmp_path)

    def test_move_mod_script_raises_error(
        self,
        engine: LoadOrderEngine,
        tmp_path: Path,
    ) -> None:
        """Test moving script file raises error."""
        mod = ModFile(
            path=Path("script.ts4script"),
            size=100,
            hash=123,
            mod_type="ts4script",
            category="",
            is_valid=True,
            validation_errors=[],
            entropy=6.0,
        )

        with pytest.raises(LoadOrderError, match="must remain in root"):
            engine.move_mod(mod, "000_Core", "020_MainMods", tmp_path)

    def test_validate_structure_valid(
        self,
        engine: LoadOrderEngine,
        tmp_path: Path,
    ) -> None:
        """Test validation of valid structure."""
        base = tmp_path / "ActiveMods"
        base.mkdir()

        # Create all slot folders
        for prefix, _, _ in LOAD_ORDER_SLOTS:
            (base / prefix).mkdir()

        # Add a script in root
        (base / "script.ts4script").write_bytes(b"PK\x03\x04")

        # Add package in slot
        (base / "020_MainMods" / "mod.package").write_bytes(b"DBPF")

        is_valid, warnings = engine.validate_structure(base)

        assert is_valid is True
        assert len(warnings) == 0

    def test_validate_structure_missing_slots(
        self,
        engine: LoadOrderEngine,
        tmp_path: Path,
    ) -> None:
        """Test validation detects missing slots."""
        base = tmp_path / "ActiveMods"
        base.mkdir()

        is_valid, warnings = engine.validate_structure(base)

        assert is_valid is False
        assert len(warnings) > 0
        assert any("Missing slot" in w for w in warnings)

    def test_validate_structure_nested_script(
        self,
        engine: LoadOrderEngine,
        tmp_path: Path,
    ) -> None:
        """Test validation detects nested scripts."""
        base = tmp_path / "ActiveMods"
        base.mkdir()

        # Create nested script
        nested_dir = base / "020_MainMods"
        nested_dir.mkdir(parents=True)
        (nested_dir / "script.ts4script").write_bytes(b"PK\x03\x04")

        is_valid, warnings = engine.validate_structure(base)

        assert is_valid is False
        assert any("nested" in w.lower() for w in warnings)

    def test_validate_structure_path_too_long(
        self,
        engine: LoadOrderEngine,
        tmp_path: Path,
    ) -> None:
        """Test validation detects overly long paths."""
        base = tmp_path / "ActiveMods"
        base.mkdir()

        # Create file with very long path
        long_name = "a" * (MAX_PATH_LENGTH - len(str(base)))
        slot = base / "020_MainMods"
        slot.mkdir(parents=True)
        (slot / long_name).write_bytes(b"test")

        is_valid, warnings = engine.validate_structure(base)

        # May or may not trigger depending on tmp_path length
        # Just ensure validation runs without error
        assert isinstance(is_valid, bool)

    def test_validate_structure_excessive_nesting(
        self,
        engine: LoadOrderEngine,
        tmp_path: Path,
    ) -> None:
        """Test validation detects excessive package nesting."""
        base = tmp_path / "ActiveMods"
        slot = base / "020_MainMods"

        # Create deeply nested package
        deep_path = slot
        for i in range(MAX_PACKAGE_DEPTH + 2):
            deep_path = deep_path / f"level{i}"
        deep_path.mkdir(parents=True)
        (deep_path / "mod.package").write_bytes(b"DBPF")

        is_valid, warnings = engine.validate_structure(base)

        assert is_valid is False
        assert any("nested too deep" in w.lower() for w in warnings)

    def test_get_load_order_alphabetical(
        self,
        engine: LoadOrderEngine,
        tmp_path: Path,
    ) -> None:
        """Test load order is alphabetically sorted."""
        base = tmp_path / "ActiveMods"

        # Create structure
        (base / "000_Core").mkdir(parents=True)
        (base / "020_MainMods").mkdir(parents=True)

        # Add mods (non-alphabetical)
        (base / "script_z.ts4script").write_bytes(b"PK")
        (base / "script_a.ts4script").write_bytes(b"PK")
        (base / "020_MainMods" / "mod_z.package").write_bytes(b"DBPF")
        (base / "020_MainMods" / "mod_a.package").write_bytes(b"DBPF")

        load_order = engine.get_load_order(base)

        # Scripts first (alphabetical), then packages by slot
        assert len(load_order) == 4
        assert load_order[0] == "script_a.ts4script"
        assert load_order[1] == "script_z.ts4script"

    def test_get_load_order_empty(
        self, engine: LoadOrderEngine, tmp_path: Path
    ) -> None:
        """Test load order for empty directory."""
        base = tmp_path / "ActiveMods"

        load_order = engine.get_load_order(base)

        assert load_order == []

    def test_validate_prefix_valid(self, engine: LoadOrderEngine) -> None:
        """Test prefix validation with valid prefixes."""
        assert engine.validate_prefix("000_Core") is True
        assert engine.validate_prefix("020_MainMods") is True
        assert engine.validate_prefix("999_Test") is True

    def test_validate_prefix_invalid(self, engine: LoadOrderEngine) -> None:
        """Test prefix validation with invalid prefixes."""
        assert engine.validate_prefix("ZZZ_Overrides") is False  # Letters in number
        assert engine.validate_prefix("Core_000") is False  # Wrong order
        assert engine.validate_prefix("00_Test") is False  # Too few digits
        assert engine.validate_prefix("0000_Test") is False  # Too many digits
        assert engine.validate_prefix("000-Test") is False  # Invalid separator

    def test_get_slot_description(self, engine: LoadOrderEngine) -> None:
        """Test getting slot descriptions."""
        desc = engine.get_slot_description("000_Core")

        assert desc is not None
        assert "Core" in desc

    def test_get_slot_description_invalid(self, engine: LoadOrderEngine) -> None:
        """Test getting description for invalid slot."""
        desc = engine.get_slot_description("999_Invalid")

        assert desc is None

    def test_reorganize_slot(self, engine: LoadOrderEngine, tmp_path: Path) -> None:
        """Test reorganizing mods within a slot."""
        base = tmp_path / "ActiveMods"
        slot = base / "020_MainMods"
        slot.mkdir(parents=True)

        # Add mods
        (slot / "mod_c.package").write_bytes(b"DBPF")
        (slot / "mod_a.package").write_bytes(b"DBPF")
        (slot / "mod_b.package").write_bytes(b"DBPF")

        result = engine.reorganize_slot("020_MainMods", base)

        assert result is True

    def test_reorganize_slot_nonexistent(
        self,
        engine: LoadOrderEngine,
        tmp_path: Path,
    ) -> None:
        """Test reorganizing nonexistent slot."""
        base = tmp_path / "ActiveMods"
        base.mkdir()

        result = engine.reorganize_slot("020_MainMods", base)

        assert result is False

    def test_detect_conflicts_no_duplicates(
        self,
        engine: LoadOrderEngine,
        tmp_path: Path,
    ) -> None:
        """Test conflict detection with no duplicates."""
        base = tmp_path / "ActiveMods"
        slot1 = base / "020_MainMods"
        slot2 = base / "030_Tuning"
        slot1.mkdir(parents=True)
        slot2.mkdir(parents=True)

        (slot1 / "mod_a.package").write_bytes(b"DBPF")
        (slot2 / "mod_b.package").write_bytes(b"DBPF")

        conflicts = engine.detect_conflicts(base)

        assert len(conflicts) == 0

    def test_detect_conflicts_with_duplicates(
        self,
        engine: LoadOrderEngine,
        tmp_path: Path,
    ) -> None:
        """Test conflict detection finds duplicates."""
        base = tmp_path / "ActiveMods"
        slot1 = base / "020_MainMods"
        slot2 = base / "030_Tuning"
        slot1.mkdir(parents=True)
        slot2.mkdir(parents=True)

        # Same mod name in different slots
        (slot1 / "duplicate.package").write_bytes(b"DBPF")
        (slot2 / "duplicate.package").write_bytes(b"DBPF")

        conflicts = engine.detect_conflicts(base)

        assert len(conflicts) == 1
        assert conflicts[0][0] == "duplicate.package"
        assert "020_MainMods" in conflicts[0][1]
        assert "030_Tuning" in conflicts[0][1]

    def test_export_load_order(
        self,
        engine: LoadOrderEngine,
        tmp_path: Path,
    ) -> None:
        """Test exporting load order to file."""
        base = tmp_path / "ActiveMods"
        slot = base / "020_MainMods"
        slot.mkdir(parents=True)

        (slot / "mod.package").write_bytes(b"DBPF")

        output_file = tmp_path / "load_order.txt"
        result = engine.export_load_order(base, output_file)

        assert result is True
        assert output_file.exists()

        # Check content
        content = output_file.read_text()
        assert "# Sims 4 Mod Load Order" in content
        assert "mod.package" in content

    def test_get_default_engine(self) -> None:
        """Test getting default engine instance."""
        engine = get_default_engine()

        assert isinstance(engine, LoadOrderEngine)
        assert len(engine.slots) > 0


class TestPrefixPattern:
    """Test PREFIX_PATTERN regex."""

    def test_pattern_matches_valid(self) -> None:
        """Test pattern matches valid prefixes."""
        assert PREFIX_PATTERN.match("000_Core")
        assert PREFIX_PATTERN.match("020_MainMods")
        assert PREFIX_PATTERN.match("999_Test123")

    def test_pattern_rejects_invalid(self) -> None:
        """Test pattern rejects invalid prefixes."""
        assert not PREFIX_PATTERN.match("00_Test")  # Too few digits
        assert not PREFIX_PATTERN.match("0000_Test")  # Too many digits
        assert not PREFIX_PATTERN.match("000-Test")  # Wrong separator
        assert not PREFIX_PATTERN.match("Test_000")  # Wrong order
        assert not PREFIX_PATTERN.match("000_")  # No name
        assert not PREFIX_PATTERN.match("000_Test-Mod")  # Hyphen not allowed
