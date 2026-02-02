# Assets Directory

This directory contains visual assets for the Iceberg Launcher website and application.

## Files Needed:

### Root Directory:
- `logo.png` - Main logo for the launcher (recommended: 120x120px, PNG format)
  - *Used for both the main logo and favicon*

### Screenshots Directory:
- `screenshots/main-interface.png` - Main launcher interface screenshot
- `screenshots/download-dialog.png` - Download dialog screenshot
- `screenshots/options-menu.png` - Options menu screenshot
- `screenshots/console-output.png` - Console output showing game logs

## Placeholder Behavior:

The website is designed to gracefully handle missing assets:
- If `logo.png` is missing, the hero section will show an iceberg icon placeholder
- If screenshot images are missing, they will show icon placeholders
- If favicon (logo.png) is missing, the browser will use default icon

## Recommended Specifications:

### Logo:
- **Format**: PNG with transparency
- **Size**: 120x120px (will be resized automatically for both logo and favicon)
- **Style**: Clean, modern design that works on both light and dark backgrounds
- **Note**: This single file serves as both the main logo and website favicon

### Screenshots:
- **Format**: PNG or JPG
- **Size**: Minimum 800x600px for good quality
- **Content**: Show actual launcher interface with realistic data
- **Style**: Clear, well-lit screenshots that showcase features

## Adding Assets:

1. Place `logo.png` in the root directory (used for both logo and favicon)
2. Place screenshot images in the `screenshots/` directory
3. The website will automatically use them when available

The website will work perfectly without these assets, showing elegant placeholders until the real assets are added.
