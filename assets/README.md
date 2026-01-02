# Assets Directory

This directory contains fonts, icons, and other static assets for the 8-bit retro UI.

## Fonts

### Press Start 2P
Download from: https://fonts.google.com/specimen/Press+Start+2P

**Installation:**
1. Download the font ZIP file
2. Extract `PressStart2P-Regular.ttf`
3. Place in `assets/fonts/Press_Start_2P.ttf`

The application will fall back to Courier New if this font is not found.

## Icons

Icons are generated programmatically using PIL/Pillow. See `src/ui/pixel_theme.py` for implementation.

## Directory Structure

```
assets/
├── fonts/
│   └── Press_Start_2P.ttf  (Download separately)
├── icons/                  (Generated at runtime)
└── README.md
```

## License

Press Start 2P font is licensed under the Open Font License (OFL).
