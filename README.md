# Titanic Launcher

A modern GUI launcher for Titanic osu! versions on Linux that automatically fetches, downloads, and launches different game versions using osu-wine.

## Features

- **Modern UI**: Clean dark theme interface using CustomTkinter
- **Automatic Version Fetching**: Scrapes Titanic website to find available versions
- **Smart Download**: Tries multiple download URLs to find the correct one
- **Version Management**: Install, launch, and delete different versions
- **Progress Tracking**: Shows download and extraction progress with visual feedback
- **Size Display**: Shows installed version sizes in human-readable format
- **Linux Support**: Launches games using `osu-wine --wine` command

## Requirements

- Python 3.6+
- `osu-wine` command (must be installed and available in PATH)
- Requirements from `requirements.txt`:
  - `requests>=2.25.1`
  - `customtkinter>=5.0.0`
  - `beautifulsoup4>=4.9.0`

## Installation

1. Clone or download this repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Ensure `osu-wine` is installed and properly configured

## Usage

1. Run the launcher:
   ```bash
   python main.py
   ```

2. **Automatic Version Fetching**:
   - The launcher automatically scrapes the Titanic website for available versions
   - Versions are sorted from newest to oldest
   - Falls back to known versions if scraping fails

3. **Download a version**:
   - Select a version from the dropdown
   - Click "Download" to fetch and install it
   - Progress is shown with a progress bar

4. **Launch a version**:
   - Select an installed version from the list (click the "Select" button)
   - Click "Launch" to start the game
   - Uses `osu-wine --wine` command automatically

5. **Manage versions**:
   - View all installed versions with their sizes
   - Delete unwanted versions using "Delete Selected"

## Web Scraping Features

The launcher automatically fetches versions from the Titanic website using the correct structure:
- Scrapes `https://osu.titanic.sh/download/` for available versions
- Extracts version numbers from `<p class="version">` elements
- Gets download URLs from `<a class="download-link">` elements
- Versions are in format like `b20151228.3`, `b20150826.3`, etc.
- Downloads from `https://cdn.titanic.sh/clients/{version}.zip`
- Falls back to known versions if scraping fails
- Versions are sorted from newest to oldest by date

## Configuration

- Versions are stored in `~/.titaniclauncher/`
- The launcher uses dark theme by default
- Download URLs are tried in multiple patterns for maximum compatibility

## Notes

- The web scraping uses the correct Titanic website structure at `https://osu.titanic.sh/download/`
- Currently finds 76+ available versions from 2008-2015
- Uses scraped download URLs from `https://cdn.titanic.sh/clients/` for maximum reliability
- Multiple download URL patterns are attempted as fallbacks
- The launcher creates a dedicated directory for each version to prevent conflicts
- Requires `osu-wine` to be properly configured for optimal performance

## Troubleshooting

- If version fetching fails, the launcher falls back to known versions
- If downloads fail, check your internet connection and verify Titanic's availability
- If launching fails, ensure `osu-wine` is installed and properly configured
- Check that Wine is properly set up on your system
- The launcher shows detailed error messages for debugging
