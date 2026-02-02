# Iceberg Launcher

A modern, feature-rich GUI launcher for Titanic osu! versions on Linux. Automatically fetches, downloads, and manages different game versions with a polished user interface and advanced configuration options.

## Features

### Core Functionality
- **Modern UI**: Clean, professional interface using CustomTkinter with dark/light mode support
- **API-Based Version Fetching**: Uses official Titanic API to find available versions
- **Smart Download**: Tries multiple download URLs to find the correct one
- **Version Management**: Install, launch, and delete different versions
- **Progress Tracking**: Shows download and extraction progress with visual feedback
- **Size Display**: Shows installed version sizes in human-readable format
- **Linux Support**: Launches games using `osu-wine --wine` command
- **Scrollable Interface**: Both sidebar and main area support mouse wheel scrolling

### Advanced Features
- **Per-Version Configuration**: Custom names and launch arguments for each version
- **Collapsible UI Sections**: Clean, organized interface with expandable/collapsible panels
- **Download Dialog**: Rich preview system with screenshots and descriptions
- **Options Dialog**: Theme customization (dark/light mode, accent colors)
- **osu-wine Auto-Install**: One-click osu-wine installation with progress tracking
- **Preview System**: View screenshots and descriptions before downloading
- **Custom Logo Support**: Uses logo.png file if available (falls back to emoji)
- **Persistent Settings**: All configurations saved automatically
- **Console Logging**: Built-in console output for debugging and progress tracking

## Requirements

- Python 3.6+
- Requirements from `requirements.txt`:
  - `requests>=2.25.1`
  - `customtkinter>=5.0.0`
  - `beautifulsoup4>=4.9.0`
  - `Pillow>=8.0.0`
- `osu-wine` command (can be auto-installed through the launcher)
- Git (for osu-wine auto-installation)

## Installation

1. Clone or download this repository:
   ```bash
   git clone https://github.com/SuperYosh23/Iceberg.git
   cd Iceberg
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Run the launcher:
   ```bash
   python main.py
   ```

4. (Optional) Add a custom logo:
   - Place a `logo.png` file in the same directory as `main.py`
   - Recommended size: 60x60 pixels (will be automatically resized)
   - If no logo is found, the launcher will use the 🚢 emoji

## Usage

### Basic Workflow

1. **Install osu-wine** (if not already installed):
   - Click "⚙️ Options" in the sidebar
   - Click "📥 Download osu-wine" in the Tools section
   - Follow the installation prompts

2. **Download Clients**:
   - Click "📥 Download Clients" in the sidebar
   - Browse available versions with descriptions and screenshots
   - Click on version names to see detailed previews
   - Click "📥 Download" to install desired versions

3. **Configure Versions**:
   - Select an installed version from the sidebar
   - Expand "Version Settings" section
   - Set custom names and launch arguments
   - Click "💾 Save Settings"

4. **Launch Games**:
   - Select an installed version from the sidebar
   - Click "🎮 LAUNCH GAME" button
   - Game launches with your custom configuration

### Advanced Features

**Customization Options**:
- **Theme**: Switch between dark and light modes
- **Accent Colors**: Choose from blue, green, dark-blue, or red themes
- **Custom Logo**: Add logo.png for branding
- **Collapsible Sections**: Organize interface by collapsing unused sections
- **Scrollable Interface**: Use mouse wheel to scroll through content

**Version Management**:
- **Custom Names**: Rename versions for better organization
- **Launch Arguments**: Add custom arguments for each version
- **Preview System**: See screenshots and descriptions before downloading
- **Size Tracking**: Monitor disk usage of installed versions
- **Console Logging**: View detailed logs for debugging and progress tracking

## API Integration

The launcher automatically fetches versions from the official Titanic API:
- **API Endpoint**: `https://api.titanic.sh/releases`
- **Version Data**: Fetches names, descriptions, download URLs, and screenshots
- **Smart Fallbacks**: Uses multiple URL patterns if primary downloads fail
- **Version Format**: Standard Titanic format like `b20151228.3`, `b20150826.3`, etc.
- **Automatic Sorting**: Versions sorted from newest to oldest by date
- **Error Handling**: Graceful fallback to known versions if API is unavailable

## Configuration

### Storage Locations
- **Versions**: Stored in `~/.titaniclauncher/`
- **Configuration**: Saved in `~/.titaniclauncher/config.json`
- **Custom Logo**: Place `logo.png` in the same directory as `main.py`

### Settings Structure
```json
{
  "options": {
    "appearance_mode": "dark",
    "accent_color": "blue"
  },
  "b20151228.3": {
    "custom_name": "Christmas 2015 Edition",
    "launch_args": "-fullscreen -noaudio"
  }
}
```

### Available Themes
- **Appearance Modes**: Dark, Light
- **Accent Colors**: Blue, Green, Dark-Blue, Red
- **Custom Logo**: Supports logo.png (60x60px recommended)

### Launch Command Format
```bash
osu-wine --wine '/path/to/osu!.exe' [custom-arguments]
```

## Notes

- The launcher uses the official Titanic API for reliable version fetching
- Currently supports official Titanic clients from 2008-2015 era
- Downloads from official CDN URLs with automatic fallbacks
- Multiple download URL patterns are attempted for reliability
- The launcher creates a dedicated directory for each version to prevent conflicts
- Requires `osu-wine` to be properly configured for optimal performance
- Both sidebar and main content areas support mouse wheel scrolling
- Built-in console provides detailed logging for debugging

## Troubleshooting

### Common Issues

**Launcher won't start**:
- Ensure all dependencies are installed: `pip install -r requirements.txt`
- Check Python version (3.6+ required)
- Verify CustomTkinter installation: `python -c "import customtkinter"`

**osu-wine not found**:
- Use the built-in auto-install: Click "⚙️ Options" → "📥 Download osu-wine"
- Or install manually: Follow the osu-winello installation guide
- Verify installation: Run `osu-wine --help` in terminal

**Download failures**:
- Check internet connection
- Verify Titanic API accessibility: `curl https://api.titanic.sh/releases`
- Check available disk space in `~/.titaniclauncher/`
- Try refreshing versions: Click "🔄 Refresh Versions"

**Launch failures**:
- Ensure osu-wine is properly installed and accessible
- Check that the version is fully downloaded (no partial downloads)
- Verify Wine configuration on your system
- Check launch arguments for syntax errors

**Image loading issues**:
- Some preview images may be protected and won't load
- This is normal and doesn't affect functionality
- Custom logo (logo.png) should be in PNG format

**Configuration issues**:
- Settings are stored in `~/.titaniclauncher/config.json`
- Delete this file to reset all settings
- Backup this file to preserve custom configurations

**Scrolling issues**:
- Use mouse wheel to scroll through both sidebar and main content
- On Linux, both scroll wheel buttons (Button-4/Button-5) are supported
- If scrolling doesn't work, try clicking in the area first to focus it

### Debug Information

The launcher provides detailed console output for debugging. Check the built-in console or terminal output for specific error details if issues occur.

### Getting Help

- **GitHub Repository**: https://github.com/SuperYosh23/Iceberg
- **Issue Reporting**: File issues on GitHub with error details
- **Console Logs**: Check the built-in console for detailed error information
