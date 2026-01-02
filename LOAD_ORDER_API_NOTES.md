# Load Order Engine Test Fixes

## API Summary

### generate_structure
```python
def generate_structure(
    self,
    mods: dict[str, list[ModFile]],
    output: Path,
) -> dict[str, Path]:
```
- **Parameters**: mods dict AND output path
- **Returns**: dict[str, Path] of created paths

### assign_mod_to_slot
```python
def assign_mod_to_slot(self, mod: ModFile) -> str:
```
- **Returns**: str (slot name only, e.g., "000_Core", "040_CC")
- **NOT a tuple** - just returns slot prefix

### validate_structure
```python
def validate_structure(self, path: Path) -> tuple[bool, list[str]]:
```
- **Returns**: (is_valid: bool, warnings: list[str])
- **NOT just bool** - returns tuple

### get_load_order
```python
def get_load_order(self, path: Path) -> list[str]:
```
- **Returns**: list[str] of mod names in load order

## Fixes Needed

1. All `generate_structure(tmp_path)` → `generate_structure({}, tmp_path)`
2. All `slot_name, priority = assign_mod_to_slot(mod)` → `slot_name = assign_mod_to_slot(mod)`
3. All `result = validate_structure(path); assert result is bool` → `is_valid, warnings = validate_structure(path); assert is_valid is bool`
4. `get_load_order` should work but files need to be in slot folders
