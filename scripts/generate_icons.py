"""
Generate application icons in multiple sizes.

Creates icon.png (256x256) and icon.ico (multi-resolution) with 8-bit pixel aesthetic.
Requires Pillow: pip install pillow
"""

from PIL import Image, ImageDraw
from pathlib import Path


def create_pixel_icon(size: int = 256) -> Image.Image:
    """Create 8-bit style icon.

    Args:
        size: Icon size in pixels

    Returns:
        PIL Image
    """
    # Create base image with dark background
    img = Image.new("RGBA", (size, size), (26, 26, 26, 255))
    draw = ImageDraw.Draw(img)

    # Calculate grid
    grid_size = size // 16

    # Draw pixelated "S4" text in center
    # S letter (cyan)
    s_pattern = [
        [0, 1, 1, 1, 0],
        [1, 0, 0, 0, 0],
        [0, 1, 1, 0, 0],
        [0, 0, 0, 1, 0],
        [1, 1, 1, 0, 0],
    ]

    # 4 digit (magenta)
    four_pattern = [
        [1, 0, 0, 1, 0],
        [1, 0, 0, 1, 0],
        [1, 1, 1, 1, 0],
        [0, 0, 0, 1, 0],
        [0, 0, 0, 1, 0],
    ]

    # Colors
    cyan = (0, 224, 255, 255)
    magenta = (255, 110, 199, 255)

    # Draw S
    x_offset = 3 * grid_size
    y_offset = 5 * grid_size
    for y, row in enumerate(s_pattern):
        for x, pixel in enumerate(row):
            if pixel:
                draw.rectangle(
                    [
                        x_offset + x * grid_size,
                        y_offset + y * grid_size,
                        x_offset + (x + 1) * grid_size - 1,
                        y_offset + (y + 1) * grid_size - 1,
                    ],
                    fill=cyan,
                )

    # Draw 4
    x_offset = 9 * grid_size
    y_offset = 5 * grid_size
    for y, row in enumerate(four_pattern):
        for x, pixel in enumerate(row):
            if pixel:
                draw.rectangle(
                    [
                        x_offset + x * grid_size,
                        y_offset + y * grid_size,
                        x_offset + (x + 1) * grid_size - 1,
                        y_offset + (y + 1) * grid_size - 1,
                    ],
                    fill=magenta,
                )

    # Draw border
    border_color = (0, 224, 255, 255)
    border_width = max(2, size // 64)
    draw.rectangle(
        [border_width, border_width, size - border_width, size - border_width],
        outline=border_color,
        width=border_width,
    )

    return img


def generate_all_icons(output_dir: Path):
    """Generate all required icon formats.

    Args:
        output_dir: Directory to save icons
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    # Generate PNG (256x256)
    print("Generating icon.png (256x256)...")
    icon_256 = create_pixel_icon(256)
    icon_256.save(output_dir / "icon.png")

    # Generate ICO with multiple sizes (Windows)
    print("Generating icon.ico (multi-resolution)...")
    sizes = [16, 32, 48, 64, 128, 256]
    icons = [create_pixel_icon(size) for size in sizes]
    icons[0].save(
        output_dir / "icon.ico",
        format="ICO",
        sizes=[(s, s) for s in sizes],
        append_images=icons[1:],
    )

    # Generate ICNS (macOS) - requires pillow-icns or manual conversion
    print("Generating icon.icns (macOS)...")
    try:
        # Requires: pip install pillow-icns
        from PIL import IcnsImagePlugin

        icon_256.save(output_dir / "icon.icns", format="ICNS")
    except ImportError:
        print("  ⚠️ Skipped icon.icns (requires pillow-icns)")
        print("  Install with: pip install pillow-icns")

    print(f"\n✅ Icons generated in {output_dir}")


if __name__ == "__main__":
    assets_dir = Path(__file__).parent.parent / "assets" / "icons"
    generate_all_icons(assets_dir)
