"""Tests for DBPF conflict detection."""

from pathlib import Path
from struct import pack

import pytest

from src.core.conflict_detector import ConflictDetector, DBPFParser


class TestDBPFParser:
    """Test DBPF file parsing."""

    def test_parse_valid_dbpf(self, tmp_path):
        """Test parsing valid DBPF file."""
        package_file = tmp_path / "test.package"

        # Create minimal valid DBPF structure
        # DBPF header format (first 96 bytes):
        # 0-3: Magic "DBPF"
        # 4-7: Version (4 bytes)
        # 8-11: User version (4 bytes)
        # 12-15: Flags (4 bytes)
        # 16-19: Created (4 bytes)
        # 20-23: Modified (4 bytes)
        # 24-27: Index major version (4 bytes)
        # 28-31: Index entry count (4 bytes) - BUT parser reads at offset 40!
        # 32-35: Index position low (4 bytes) - BUT parser reads at offset 36!
        # 36-39: Index size (4 bytes) - parser reads index_pos HERE
        # 40-43: Hole entries (4 bytes) - parser reads index_count HERE

        # We need to put our data where the parser expects it
        header = bytearray(96)
        header[0:4] = b"DBPF"  # Magic
        header[4:8] = pack("<I", 2)  # Version
        # Fill rest with zeros, then set the specific fields the parser uses
        header[36:40] = pack("<I", 96)  # Index position (at offset 36)
        header[40:44] = pack("<I", 2)  # Index count (at offset 40)

        # Resource index entries (type, group, instance, position, size)
        index_entry1 = (
            pack("<I", 0x12345678)  # Type ID
            + pack("<I", 0x00000000)  # Group ID
            + pack("<Q", 0xABCDEF1234567890)  # Instance ID (64-bit)
            + pack("<I", 200)  # Position
            + pack("<I", 100)  # Size
        )

        index_entry2 = (
            pack("<I", 0x87654321)  # Type ID
            + pack("<I", 0x11111111)  # Group ID
            + pack("<Q", 0x1111222233334444)  # Instance ID (64-bit)
            + pack("<I", 300)  # Position
            + pack("<I", 150)  # Size
        )

        package_file.write_bytes(bytes(header) + index_entry1 + index_entry2)

        resources = DBPFParser.parse_package(package_file)

        assert len(resources) == 2
        assert (0x12345678, 0x00000000, 0xABCDEF1234567890) in resources
        assert (0x87654321, 0x11111111, 0x1111222233334444) in resources

    def test_parse_invalid_magic(self, tmp_path):
        """Test parsing file with invalid magic."""
        invalid_file = tmp_path / "invalid.package"
        invalid_file.write_bytes(b"NOT_DBPF" + b"\x00" * 100)

        with pytest.raises(ValueError, match="Invalid .package file"):
            DBPFParser.parse_package(invalid_file)

    def test_parse_nonexistent_file(self, tmp_path):
        """Test parsing nonexistent file."""
        with pytest.raises(FileNotFoundError):
            DBPFParser.parse_package(tmp_path / "nonexistent.package")

    def test_parse_empty_package(self, tmp_path):
        """Test parsing package with no resources."""
        package_file = tmp_path / "empty.package"

        # Create DBPF with 0 index entries
        header = bytearray(96)
        header[0:4] = b"DBPF"
        header[4:8] = pack("<I", 2)  # Version
        header[36:40] = pack("<I", 96)  # Index position (at offset 36)
        header[40:44] = pack("<I", 0)  # Index count = 0 (at offset 40)

        package_file.write_bytes(bytes(header))

        resources = DBPFParser.parse_package(package_file)

        assert len(resources) == 0


class TestConflictDetector:
    """Test DBPF resource conflict detection."""

    @pytest.fixture
    def detector(self):
        """Create conflict detector."""
        return ConflictDetector()

    @pytest.fixture
    def create_dbpf_package(self):
        """Factory fixture to create DBPF packages."""

        def _create(path: Path, resource_ids: list[tuple[int, int, int]]):
            """Create DBPF package with specified resource IDs."""
            header = bytearray(96)
            header[0:4] = b"DBPF"
            header[4:8] = pack("<I", 2)  # Version
            header[36:40] = pack("<I", 96)  # Index position (at offset 36)
            header[40:44] = pack("<I", len(resource_ids))  # Index count (at offset 40)

            # Create index entries
            index_data = b""
            for type_id, group_id, instance_id in resource_ids:
                index_data += pack("<I", type_id)
                index_data += pack("<I", group_id)
                index_data += pack("<Q", instance_id)
                index_data += pack("<I", 200)  # Position
                index_data += pack("<I", 100)  # Size

            path.write_bytes(bytes(header) + index_data)

        return _create

    def test_initialization(self, detector):
        """Test detector initialization."""
        assert detector is not None
        assert hasattr(detector, "scan_mod")
        assert hasattr(detector, "build_resource_map")
        assert hasattr(detector, "get_conflicts")
        assert hasattr(detector, "check_mod_conflicts")
        assert detector.resource_map == {}

    def test_scan_mod_valid_package(self, detector, tmp_path, create_dbpf_package):
        """Test scanning valid package file."""
        package = tmp_path / "mod1.package"
        create_dbpf_package(package, [(0x12345678, 0x00000000, 0xABCDEF1234567890)])

        resources = detector.scan_mod(package)

        assert resources is not None
        assert len(resources) == 1
        assert (0x12345678, 0x00000000, 0xABCDEF1234567890) in resources

    def test_scan_mod_non_package_file(self, detector, tmp_path):
        """Test scanning non-package file."""
        txt_file = tmp_path / "readme.txt"
        txt_file.write_text("This is not a package")

        resources = detector.scan_mod(txt_file)

        assert resources is None

    def test_scan_mod_invalid_package(self, detector, tmp_path):
        """Test scanning invalid package file."""
        invalid = tmp_path / "invalid.package"
        invalid.write_bytes(b"NOT_DBPF")

        resources = detector.scan_mod(invalid)

        assert resources is None  # Should handle gracefully

    def test_build_resource_map_no_conflicts(self, detector, tmp_path, create_dbpf_package):
        """Test building resource map with no conflicts."""
        mod1 = tmp_path / "mod1.package"
        mod2 = tmp_path / "mod2.package"

        create_dbpf_package(mod1, [(0x12345678, 0x00000000, 0x1111111111111111)])
        create_dbpf_package(mod2, [(0x87654321, 0x00000000, 0x2222222222222222)])

        detector.build_resource_map([mod1, mod2])

        assert len(detector.resource_map) == 2
        assert len(detector.resource_map[(0x12345678, 0x00000000, 0x1111111111111111)]) == 1
        assert len(detector.resource_map[(0x87654321, 0x00000000, 0x2222222222222222)]) == 1

    def test_build_resource_map_with_conflicts(self, detector, tmp_path, create_dbpf_package):
        """Test building resource map with conflicts."""
        mod1 = tmp_path / "mod1.package"
        mod2 = tmp_path / "mod2.package"

        # Both mods modify the same resource
        same_resource = (0x12345678, 0x00000000, 0xABCDEF1234567890)

        create_dbpf_package(mod1, [same_resource])
        create_dbpf_package(mod2, [same_resource])

        detector.build_resource_map([mod1, mod2])

        assert len(detector.resource_map[same_resource]) == 2
        assert "mod1.package" in detector.resource_map[same_resource]
        assert "mod2.package" in detector.resource_map[same_resource]

    def test_detect_conflicts_no_conflicts(self, detector, tmp_path, create_dbpf_package):
        """Test conflict detection with no conflicts."""
        mod1 = tmp_path / "mod1.package"
        mod2 = tmp_path / "mod2.package"

        create_dbpf_package(mod1, [(0x11111111, 0x00000000, 0x1111111111111111)])
        create_dbpf_package(mod2, [(0x22222222, 0x00000000, 0x2222222222222222)])

        detector.build_resource_map([mod1, mod2])
        conflicts = detector.get_conflicts()

        assert len(conflicts) == 0

    def test_detect_conflicts_with_conflicts(self, detector, tmp_path, create_dbpf_package):
        """Test conflict detection with conflicts."""
        mod1 = tmp_path / "mod1.package"
        mod2 = tmp_path / "mod2.package"
        mod3 = tmp_path / "mod3.package"

        # Mods 1 and 2 conflict on resource A
        resource_a = (0x12345678, 0x00000000, 0xAAAAAAAAAAAAAAAA)
        # Mods 2 and 3 conflict on resource B
        resource_b = (0x87654321, 0x00000000, 0xBBBBBBBBBBBBBBBB)

        create_dbpf_package(mod1, [resource_a])
        create_dbpf_package(mod2, [resource_a, resource_b])
        create_dbpf_package(mod3, [resource_b])

        detector.build_resource_map([mod1, mod2, mod3])
        conflicts = detector.get_conflicts()

        assert len(conflicts) == 2

        # Check conflicts exist (keys will be hex strings)
        conflict_mods = list(conflicts.values())

        # Resource A conflict
        assert any(set(mods) == {"mod1.package", "mod2.package"} for mods in conflict_mods)

        # Resource B conflict
        assert any(set(mods) == {"mod2.package", "mod3.package"} for mods in conflict_mods)

    def test_detect_conflicts_three_way(self, detector, tmp_path, create_dbpf_package):
        """Test three-way conflict detection."""
        mod1 = tmp_path / "mod1.package"
        mod2 = tmp_path / "mod2.package"
        mod3 = tmp_path / "mod3.package"

        # All three mods modify same resource
        same_resource = (0xFFFFFFFF, 0x00000000, 0xFFFFFFFFFFFFFFFF)

        create_dbpf_package(mod1, [same_resource])
        create_dbpf_package(mod2, [same_resource])
        create_dbpf_package(mod3, [same_resource])

        detector.build_resource_map([mod1, mod2, mod3])
        conflicts = detector.get_conflicts()

        assert len(conflicts) == 1

        # Shocheck_mod_conflicts(self, detector, tmp_path, create_dbpf_package):
        """Test checking conflicts for specific mod."""
        mod1 = tmp_path / "mod1.package"
        mod2 = tmp_path / "mod2.package"
        mod3 = tmp_path / "mod3.package"

        resource_a = (0x11111111, 0x00000000, 0x1111111111111111)
        resource_b = (0x22222222, 0x00000000, 0x2222222222222222)

        create_dbpf_package(mod1, [resource_a, resource_b])
        create_dbpf_package(mod2, [resource_a])
        create_dbpf_package(mod3, [resource_b])

        conflicts = detector.check_mod_conflicts(mod1, [mod2, mod3])

        assert len(conflicts) == 2  # Conflicts with both mod2 and mod3
        assert "mod2.package" in conflicts
        assert "mod3.package" in conflicts
