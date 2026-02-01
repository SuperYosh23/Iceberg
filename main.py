#!/usr/bin/env python3
import customtkinter as ctk
from tkinter import messagebox, filedialog
import requests
import os
import subprocess
import threading
import zipfile
import json
import re
from urllib.parse import urljoin
import shutil
import sys
from PIL import Image, ImageTk
import io
import tempfile
import base64

# Set appearance mode and color theme
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

class TitanicLauncher(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Iceberg Launcher")
        self.geometry("1000x700")

        # Configuration
        self.titanic_base_url = "https://osu.titanic.sh/"
        self.versions_dir = os.path.expanduser("~/.titaniclauncher")
        self.config_file = os.path.join(self.versions_dir, "config.json")
        self.logo_path = os.path.join(self.versions_dir, "logo.png")
        self.logo_url = "https://osu.titanic.sh/images/logo/main-vector.min.svg"
        
        # Ensure versions directory exists
        os.makedirs(self.versions_dir, exist_ok=True)
        
        # Variables
        self.versions = []
        self.modified_versions = []  # Store modified clients separately
        self.download_links = {}
        self.version_descriptions = {}
        self.version_images = {}
        self.version_configs = {}  # Per-version configuration
        self.selected_version = ctk.StringVar()
        self.download_progress = ctk.DoubleVar()
        self.status_text = ctk.StringVar(value="Ready")
        self.current_version_name = None
        self.current_tab = "official"  # Track current tab
        
        # Options variables
        self.appearance_mode = ctk.StringVar(value="dark")
        self.accent_color = ctk.StringVar(value="blue")
        
        # Authentication variables
        self.auth_token = None
        self.user_data = {}
        self.username = ctk.StringVar(value="Not logged in")
        self.user_rank = ctk.StringVar(value="-")
        self.user_pp = ctk.StringVar(value="-")
        self.user_country = ctk.StringVar(value="-")
        self.avatar_image = None
        
        # Grid configuration
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.setup_ui()
        self.load_options_config()
        self.load_auth_config()
        self.load_config()
        self.load_versions()

    def setup_ui(self):
        # === SIDEBAR ===
        self.sidebar_frame = ctk.CTkFrame(self, width=250, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(2, weight=1)

        # Title only - no logo
        ctk.CTkLabel(self.sidebar_frame, text="ICEBERG", font=ctk.CTkFont(size=18, weight="bold")).grid(row=0, column=0, pady=(20, 10))
        
        # User info section
        user_frame = ctk.CTkFrame(self.sidebar_frame)
        user_frame.grid(row=1, column=0, padx=15, pady=(0, 10), sticky="ew")
        
        # Avatar and username row
        avatar_username_frame = ctk.CTkFrame(user_frame)
        avatar_username_frame.pack(fill="x", padx=10, pady=(10, 5))
        
        # Avatar placeholder
        self.avatar_label = ctk.CTkLabel(avatar_username_frame, text="👤", font=ctk.CTkFont(size=20), width=40, height=40)
        self.avatar_label.pack(side="left", padx=(0, 10))
        
        # Username
        username_label = ctk.CTkLabel(avatar_username_frame, textvariable=self.username, font=ctk.CTkFont(size=14, weight="bold"))
        username_label.pack(side="left", anchor="w")
        
        # User stats
        stats_frame = ctk.CTkFrame(user_frame)
        stats_frame.pack(fill="x", padx=10, pady=(0, 10))
        
        # Rank
        rank_frame = ctk.CTkFrame(stats_frame)
        rank_frame.pack(fill="x", pady=2)
        ctk.CTkLabel(rank_frame, text="Rank:", font=ctk.CTkFont(size=10)).pack(side="left", padx=(5, 2))
        ctk.CTkLabel(rank_frame, textvariable=self.user_rank, font=ctk.CTkFont(size=10)).pack(side="left")
        
        # PP
        pp_frame = ctk.CTkFrame(stats_frame)
        pp_frame.pack(fill="x", pady=2)
        ctk.CTkLabel(pp_frame, text="PP:", font=ctk.CTkFont(size=10)).pack(side="left", padx=(5, 2))
        ctk.CTkLabel(pp_frame, textvariable=self.user_pp, font=ctk.CTkFont(size=10)).pack(side="left")
        
        # Country
        country_frame = ctk.CTkFrame(stats_frame)
        country_frame.pack(fill="x", pady=2)
        ctk.CTkLabel(country_frame, text="Country:", font=ctk.CTkFont(size=10)).pack(side="left", padx=(5, 2))
        ctk.CTkLabel(country_frame, textvariable=self.user_country, font=ctk.CTkFont(size=10)).pack(side="left")
        
        # Login/Logout button
        self.auth_btn = ctk.CTkButton(user_frame, text="🔑 Login", command=self.open_login_dialog, height=30)
        self.auth_btn.pack(fill="x", padx=10, pady=(0, 10))

        # Version list with scroll wheel support
        self.version_tabs = ctk.CTkTabview(self.sidebar_frame, width=220)
        self.version_tabs.grid(row=2, column=0, padx=15, pady=10, sticky="nsew")
        
        # Create tabs for official and modified clients
        self.official_tab = self.version_tabs.add("Official")
        self.modified_tab = self.version_tabs.add("Modified")
        
        # Create scrollable frames for each tab
        self.official_scrollable = ctk.CTkScrollableFrame(self.official_tab, label_text="Installed Versions")
        self.official_scrollable.pack(fill="both", expand=True, padx=5, pady=5)
        
        self.modified_scrollable = ctk.CTkScrollableFrame(self.modified_tab, label_text="Installed Versions")
        self.modified_scrollable.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Enable scroll wheel support for both scrollable frames
        for scrollable in [self.official_scrollable, self.modified_scrollable]:
            scrollable.bind("<MouseWheel>", self._on_mousewheel)
            scrollable.bind("<Button-4>", self._on_mousewheel)  # Linux scroll up
            scrollable.bind("<Button-5>", self._on_mousewheel)  # Linux scroll down
        
        # Set up tab change callback
        self.version_tabs.configure(command=self.on_tab_changed)

        # Action buttons
        self.download_clients_btn = ctk.CTkButton(self.sidebar_frame, text="📥 Download Clients", command=self.open_download_dialog, fg_color="#1bd964", hover_color="#15a34a", text_color="black")
        self.download_clients_btn.grid(row=3, column=0, padx=20, pady=5)
        
        self.options_btn = ctk.CTkButton(self.sidebar_frame, text="⚙️ Options", command=self.open_options_dialog, fg_color="#6c757d")
        self.options_btn.grid(row=4, column=0, padx=20, pady=5)
        
        self.refresh_btn = ctk.CTkButton(self.sidebar_frame, text="🔄 Refresh Versions", command=self.load_versions, fg_color="gray25")
        self.refresh_btn.grid(row=5, column=0, padx=20, pady=5)

        self.delete_btn = ctk.CTkButton(self.sidebar_frame, text="🗑️ Delete Version", fg_color="#cf3838", hover_color="#8a2525", command=self.delete_version)
        self.delete_btn.grid(row=6, column=0, padx=20, pady=(5, 20))

        # === MAIN PANEL ===
        self.main_frame = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self.main_frame.grid(row=0, column=1, sticky="nsew", padx=30, pady=30)

        self.header_label = ctk.CTkLabel(self.main_frame, text="Select a Version", font=ctk.CTkFont(size=32, weight="bold"))
        self.header_label.pack(pady=(10, 20))

        # Single column layout for installed versions
        self.content_frame = ctk.CTkFrame(self.main_frame)
        self.content_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        # Version details section (collapsible)
        self.details_frame = ctk.CTkFrame(self.content_frame)
        self.details_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        # Collapsible header for version details
        self.details_header_frame = ctk.CTkFrame(self.details_frame)
        self.details_header_frame.pack(fill="x", padx=10, pady=(10, 5))
        self.details_header_frame.grid_columnconfigure(1, weight=1)
        
        self.details_toggle_btn = ctk.CTkButton(
            self.details_header_frame,
            text="▼",
            width=30,
            fg_color="transparent",
            text_color=("gray10", "gray90"),
            hover_color=("gray70", "gray30"),
            command=self.toggle_details_section
        )
        self.details_toggle_btn.grid(row=0, column=0, padx=5, pady=5)
        
        self.details_title_label = ctk.CTkLabel(
            self.details_header_frame,
            text="Version Information",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        self.details_title_label.grid(row=0, column=1, sticky="w", padx=5, pady=5)
        
        # Collapsible content for version details
        self.details_content_frame = ctk.CTkFrame(self.details_frame)
        self.details_content_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        
        self.description_text = ctk.CTkTextbox(self.details_content_frame, height=200, font=ctk.CTkFont(size=12))
        self.description_text.pack(fill="both", expand=True, padx=10, pady=10)
        self.description_text.insert("0.0", "Select a version to see details...")
        self.description_text.configure(state="disabled")
        
        # Version settings section (collapsible)
        self.settings_frame = ctk.CTkFrame(self.content_frame)
        self.settings_frame.pack(fill="x", padx=20, pady=(0, 20))
        
        # Collapsible header for version settings
        self.settings_header_frame = ctk.CTkFrame(self.settings_frame)
        self.settings_header_frame.pack(fill="x", padx=10, pady=(10, 5))
        self.settings_header_frame.grid_columnconfigure(1, weight=1)
        
        self.settings_toggle_btn = ctk.CTkButton(
            self.settings_header_frame,
            text="▼",
            width=30,
            fg_color="transparent",
            text_color=("gray10", "gray90"),
            hover_color=("gray70", "gray30"),
            command=self.toggle_settings_section
        )
        self.settings_toggle_btn.grid(row=0, column=0, padx=5, pady=5)
        
        self.settings_title_label = ctk.CTkLabel(
            self.settings_header_frame,
            text="Version Settings",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        self.settings_title_label.grid(row=0, column=1, sticky="w", padx=5, pady=5)
        
        # Collapsible content for version settings
        self.settings_content_frame = ctk.CTkFrame(self.settings_frame)
        self.settings_content_frame.pack(fill="x", padx=10, pady=(0, 10))
        
        # Settings form
        self.settings_form = ctk.CTkFrame(self.settings_content_frame)
        self.settings_form.pack(fill="x", padx=10, pady=10)
        
        # Custom name
        ctk.CTkLabel(self.settings_form, text="Custom Name:", font=ctk.CTkFont(weight="bold")).pack(anchor="w", pady=(10, 2))
        self.name_entry = ctk.CTkEntry(self.settings_form, width=250)
        self.name_entry.pack(fill="x", pady=(0, 10))
        
        # Launch arguments
        ctk.CTkLabel(self.settings_form, text="Launch Arguments:", font=ctk.CTkFont(weight="bold")).pack(anchor="w", pady=(10, 2))
        self.launch_args_entry = ctk.CTkEntry(self.settings_form, width=250)
        self.launch_args_entry.pack(fill="x", pady=(0, 10))
        
        # Save button
        self.save_settings_btn = ctk.CTkButton(self.settings_form, text="💾 Save Settings", command=self.save_current_version_settings, fg_color="#28a745")
        self.save_settings_btn.pack(pady=10)
        
        # Help text
        help_text = ctk.CTkTextbox(self.settings_content_frame, height=120, font=ctk.CTkFont(size=10))
        help_text.pack(fill="x", pady=(10, 10))
        help_text.insert("0.0", 
            "Launch Arguments: Additional arguments passed to osu!.exe\n\n"
            "Examples:\n"
            "Launch: -fullscreen -noaudio\n\n"
            "Changes are saved automatically when you click Save Settings."
        )
        help_text.configure(state="disabled")
        
        # Console output section (collapsible)
        self.console_frame = ctk.CTkFrame(self.content_frame)
        self.console_frame.pack(fill="x", padx=20, pady=(0, 20))
        
        # Collapsible header for console
        self.console_header_frame = ctk.CTkFrame(self.console_frame)
        self.console_header_frame.pack(fill="x", padx=10, pady=(10, 5))
        self.console_header_frame.grid_columnconfigure(1, weight=1)
        
        self.console_toggle_btn = ctk.CTkButton(
            self.console_header_frame,
            text="▼",
            width=30,
            fg_color="transparent",
            text_color=("gray10", "gray90"),
            hover_color=("gray70", "gray30"),
            command=self.toggle_console_section
        )
        self.console_toggle_btn.grid(row=0, column=0, padx=5, pady=5)
        
        self.console_title_label = ctk.CTkLabel(
            self.console_header_frame,
            text="Console Output",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        self.console_title_label.grid(row=0, column=1, sticky="w", padx=5, pady=5)
        
        # Clear console button
        self.clear_console_btn = ctk.CTkButton(
            self.console_header_frame,
            text="🗑️ Clear",
            width=60,
            fg_color="gray30",
            command=self.clear_console
        )
        self.clear_console_btn.grid(row=0, column=2, padx=5, pady=5)
        
        # Collapsible content for console
        self.console_content_frame = ctk.CTkFrame(self.console_frame)
        self.console_content_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        
        # Console text widget
        self.console_text = ctk.CTkTextbox(self.console_content_frame, height=150, font=ctk.CTkFont(family="Courier", size=10))
        self.console_text.pack(fill="both", expand=True, padx=10, pady=10)
        self.console_text.insert("0.0", "Console output will appear here...\n")
        self.console_text.configure(state="disabled")
        
        # Track console collapse state
        self.console_collapsed = False

        # Progress section (move to main frame)
        ctk.CTkLabel(self.main_frame, text="Download Progress").pack(anchor="w", padx=20, pady=(10, 0))
        self.progress_bar = ctk.CTkProgressBar(self.main_frame)
        self.progress_bar.pack(fill="x", padx=20, pady=(5, 10))
        self.progress_bar.set(0)

        # Folder buttons (move to main frame)
        self.folder_btn = ctk.CTkButton(self.main_frame, text="📂 Open Versions Folder", command=self.open_versions_folder, fg_color="gray30")
        self.folder_btn.pack(fill="x", padx=20, pady=(10, 5))

        # Status and dynamic launch/download button
        self.status_label = ctk.CTkLabel(self.main_frame, textvariable=self.status_text, text_color="gray")
        self.status_label.pack(side="bottom", pady=5)
        
        self.launch_btn = ctk.CTkButton(self.main_frame, text="🎮 LAUNCH GAME", height=55, font=ctk.CTkFont(size=20, weight="bold"), command=self.handle_main_action)
        self.launch_btn.pack(side="bottom", fill="x", padx=20, pady=10)

    def load_versions(self):
        """Load available Titanic versions from the API"""
        self.log_to_console("Fetching versions from Titanic API...")
        self.status_text.set("Fetching versions from Titanic API...")
        self.update()
        
        # Start fetching in separate thread to avoid blocking UI
        thread = threading.Thread(target=self._fetch_versions_thread)
        thread.daemon = True
        thread.start()

    def _fetch_versions_thread(self):
        """Fetch versions from Titanic API in background thread"""
        try:
            self.log_to_console("Connecting to Titanic API...")
            
            # Fetch official versions from the official Titanic API
            response = requests.get("https://api.titanic.sh/releases", timeout=10)
            response.raise_for_status()
            
            self.log_to_console("Successfully fetched official releases")
            
            # Parse JSON response
            api_data = response.json()
            
            versions = []
            download_links = {}
            version_descriptions = {}
            version_images = {}
            
            # Process each version from the API
            for version_data in api_data:
                version = version_data['name']
                description = version_data.get('description', 'No description available.')
                
                # Get download URL (API provides a list, take the first one)
                downloads = version_data.get('downloads', [])
                download_url = downloads[0] if downloads else None
                
                # Get screenshot URLs (API provides a list, prefer the first one)
                screenshots = version_data.get('screenshots', [])
                image_url = None
                
                if screenshots:
                    screenshot = screenshots[0]
                    # Convert relative URLs to absolute
                    if screenshot.startswith('/images/clients/'):
                        image_url = self.titanic_base_url + screenshot.lstrip('/')
                    elif screenshot.startswith('/ss/'):
                        image_url = self.titanic_base_url + screenshot.lstrip('/')
                    elif screenshot.startswith('http'):
                        image_url = screenshot
                
                versions.append(version)
                if download_url:
                    download_links[version] = download_url
                version_descriptions[version] = description
                version_images[version] = image_url
            
            # Fetch modified clients
            modified_versions = []
            try:
                self.log_to_console("Fetching modified clients...")
                mod_response = requests.get("https://api.titanic.sh/releases/modded", timeout=10)
                mod_response.raise_for_status()
                mod_data = mod_response.json()
                
                for mod_client in mod_data:
                    client_name = mod_client.get('name', 'Unknown Client')
                    client_id = mod_client.get('id', 'unknown')
                    
                    # Create a unique identifier for modified clients
                    mod_version = f"mod_{client_id}_{client_name.lower().replace(' ', '_')}"
                    
                    modified_versions.append(mod_version)
                    version_descriptions[mod_version] = f"Modified Client: {client_name}"
                    version_images[mod_version] = None  # Modified clients might not have screenshots
                    
                    # Store additional info for modified clients
                    download_links[mod_version] = f"https://api.titanic.sh/releases/modded/{client_id}/entries"
                
                self.log_to_console(f"Successfully fetched {len(modified_versions)} modified clients")
                    
            except Exception as e:
                self.log_to_console(f"Failed to fetch modified clients: {e}", "WARNING")
                modified_versions = []
            
            # Sort versions from newest to oldest using the existing version_key method
            versions.sort(key=TitanicLauncher.version_key, reverse=True)
            
            # Store data for later use
            self.versions = versions
            self.modified_versions = modified_versions
            self.download_links = download_links
            self.version_descriptions = version_descriptions
            self.version_images = version_images
            
            # Update UI in main thread
            current_versions = self.modified_versions if self.current_tab == "modified" else self.versions
            self.after(0, self._update_versions_ui, current_versions)
            self.after(0, lambda: self.status_text.set(f"Loaded {len(versions)} official and {len(modified_versions)} modified clients from Titanic API"))
            self.log_to_console(f"Successfully loaded {len(versions)} official and {len(modified_versions)} modified clients", "SUCCESS")
            
        except Exception as e:
            # Fallback to known versions on error
            self.log_to_console(f"API error: {str(e)}", "ERROR")
            fallback_versions = ["b20151228.3", "b20150826.3", "b20150331.2", "b20141216.1", "b20131216.1"]
            self.download_links = {}
            self.version_descriptions = {v: "Fallback version" for v in fallback_versions}
            self.version_images = {}
            self.versions = fallback_versions
            self.modified_versions = []
            self.after(0, self._update_versions_ui, fallback_versions)
            self.after(0, lambda: self.status_text.set(f"Using fallback versions (API error: {str(e)})"))
            self.log_to_console("Using fallback versions due to API error", "WARNING")

    def _update_versions_ui(self, versions):
        """Update UI with fetched versions"""
        self.versions = versions
        if versions:
            self.selected_version.set(versions[0])
        
        self.status_text.set(f"Found {len(versions)} versions")
        self.refresh_version_buttons()
    
    @staticmethod
    def version_key(v):
        """Helper method to sort versions by date"""
        # Remove 'b' prefix if present
        clean_v = v.lstrip('b')
        # Try to extract date parts
        import re
        match = re.match(r'(\d{4})(\d{2})(\d{2})(?:\.(\d+))?', clean_v)
        if match:
            year, month, day, build = match.groups()
            build_num = int(build) if build else 0
            return (int(year), int(month), int(day), build_num)
        return (0, 0, 0, 0)

    def on_tab_changed(self):
        """Handle tab change between official and modified clients"""
        selected_tab = self.version_tabs.get()
        self.current_tab = selected_tab.lower()
        
        # Refresh version buttons for both tabs to ensure they're up to date
        self.refresh_version_buttons()
        
        self.log_to_console(f"Switched to {self.current_tab} clients")
        self.status_text.set(f"Showing {self.current_tab} clients")

    def refresh_version_buttons(self):
        """Refresh the version buttons in the sidebar - show only installed versions"""
        # Clear existing buttons from both tabs
        for widget in self.official_scrollable.winfo_children():
            widget.destroy()
        for widget in self.modified_scrollable.winfo_children():
            widget.destroy()
        
        self.official_scrollable.grid_columnconfigure(0, weight=1)
        self.modified_scrollable.grid_columnconfigure(0, weight=1)
        
        # Handle official versions tab
        official_installed = []
        for version in self.versions:
            version_path = os.path.join(self.versions_dir, version)
            if os.path.exists(version_path) and os.path.exists(os.path.join(version_path, "osu!.exe")):
                official_installed.append(version)
        
        # Add buttons for installed official versions
        for i, version in enumerate(official_installed):
            config = self.get_version_config(version)
            display_name = config['custom_name']
            
            btn = ctk.CTkButton(
                self.official_scrollable,
                text=display_name,
                fg_color="transparent",
                border_width=1,
                anchor="w",
                height=40,
                command=lambda v=version: self.select_version(v)
            )
            btn.grid(row=i, column=0, sticky="ew", pady=2)
            btn.configure(text_color=("gray10", "gray90"))
        
        # Show message if no official versions installed
        if not official_installed:
            no_versions_label = ctk.CTkLabel(
                self.official_scrollable,
                text="No official versions installed\nClick 'Download Clients' to get started",
                font=ctk.CTkFont(size=12),
                text_color="gray"
            )
            no_versions_label.grid(row=0, column=0, pady=20)
        
        # Handle modified versions tab
        modified_installed = []
        for version in self.modified_versions:
            version_path = os.path.join(self.versions_dir, version)
            if os.path.exists(version_path) and os.path.exists(os.path.join(version_path, "osu!.exe")):
                modified_installed.append(version)
        
        # Add buttons for installed modified versions
        for i, version in enumerate(modified_installed):
            config = self.get_version_config(version)
            display_name = config['custom_name']
            
            btn = ctk.CTkButton(
                self.modified_scrollable,
                text=display_name,
                fg_color="transparent",
                border_width=1,
                anchor="w",
                height=40,
                command=lambda v=version: self.select_version(v)
            )
            btn.grid(row=i, column=0, sticky="ew", pady=2)
            btn.configure(text_color=("gray10", "gray90"))
        
        # Show message if no modified versions installed
        if not modified_installed:
            no_versions_label = ctk.CTkLabel(
                self.modified_scrollable,
                text="No modified versions installed\nClick 'Download Clients' to get started",
                font=ctk.CTkFont(size=12),
                text_color="gray"
            )
            no_versions_label.grid(row=0, column=0, pady=20)

    def select_version(self, version):
        """Select a version and display its details"""
        self.current_version_name = version
        self.selected_version.set(version)
        
        # Get custom name for display
        config = self.get_version_config(version)
        display_name = config['custom_name']
        self.header_label.configure(text=display_name)
        
        # Update version info
        version_path = os.path.join(self.versions_dir, version)
        
        # Update description - simplified for installed versions
        self.description_text.configure(state="normal")
        self.description_text.delete("0.0", "end")
        
        # Add installation status and config info
        if os.path.exists(version_path):
            size = self.get_directory_size(version_path)
            size_str = self.format_size(size)
            config_info = []
            if config['launch_args']:
                config_info.append(f"Launch Args: {config['launch_args']}")
            
            config_text = "\n".join(config_info) if config_info else "No custom arguments set"
            
            self.description_text.insert("end", f"Status: Installed ✓\nSize: {size_str}\nPath: {version_path}\n\n{config_text}")
            # Update button to launch
            self.launch_btn.configure(text="🎮 LAUNCH GAME", fg_color=("#3B8ED0", "#1F6AA5"))
        else:
            # This shouldn't happen with the new UI, but handle it gracefully
            self.description_text.insert("end", f"Status: Not installed\nUse 'Download Clients' to install this version.")
            self.launch_btn.configure(text="🎮 LAUNCH GAME", fg_color=("#3B8ED0", "#1F6AA5"), state="disabled")
        
        self.description_text.configure(state="disabled")
        
        # Update settings fields
        self.name_entry.delete(0, 'end')
        self.name_entry.insert(0, config['custom_name'])
        self.launch_args_entry.delete(0, 'end')
        self.launch_args_entry.insert(0, config['launch_args'])
        
        self.status_text.set(f"Selected {display_name}")

    def load_preview_image(self, image_url):
        """Load and display preview image for a version"""
        try:
            # Add proper headers to mimic browser request
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Referer': 'https://osu.titanic.sh/download/',
                'Accept': 'image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1'
            }
            
            response = requests.get(image_url, headers=headers, timeout=10)
            if response.status_code == 200:
                # Load image from response
                image_data = io.BytesIO(response.content)
                pil_image = Image.open(image_data)
                
                # Get original dimensions
                original_width, original_height = pil_image.size
                
                # Calculate display size - match description box width but account for padding
                # Description box has padx=20, image frame has padx=20+10=30, so available width is frame width - 60
                # We'll use a fixed width that works well with the layout and padding
                target_width = 340  # Reduced from 380 to account for 20px padding on each side
                
                # Calculate height to maintain aspect ratio
                aspect_ratio = original_height / original_width
                target_height = int(target_width * aspect_ratio)
                
                # Limit maximum height to prevent overly tall images
                max_height = 250
                if target_height > max_height:
                    target_height = max_height
                    # Recalculate width to maintain aspect ratio
                    target_width = int(max_height / aspect_ratio)
                
                # Resize image with proper dimensions
                pil_image = pil_image.resize((target_width, target_height), Image.Resampling.LANCZOS)
                
                # Create CTkImage with proper size
                ctk_image = ctk.CTkImage(light_image=pil_image, dark_image=pil_image, size=(target_width, target_height))
                
                # Update UI in main thread
                self.after(0, lambda: self.update_preview_image(ctk_image))
            else:
                print(f"Image request failed with status {response.status_code} for URL: {image_url}")
                # If it's an /ss/ URL that failed, try to find an alternative
                if '/ss/' in image_url:
                    self.after(0, lambda: self.clear_preview_image("Preview image unavailable (protected)"))
                else:
                    self.after(0, lambda: self.clear_preview_image("Preview image unavailable"))
        except Exception as e:
            print(f"Failed to load preview image: {e}")
            self.after(0, lambda: self.clear_preview_image("Failed to load preview image"))

    def clear_preview_image(self, text="No preview image available"):
        """Clear the preview image and show placeholder text"""
        try:
            if hasattr(self, 'preview_image_label') and self.preview_image_label.winfo_exists():
                # Create a new label without image reference
                self.preview_image_label.configure(image="", text=text)
        except Exception as e:
            print(f"Error clearing preview image: {e}")
            # Fallback: just set text
            try:
                self.preview_image_label.configure(text=text)
            except:
                pass

    def update_preview_image(self, ctk_image):
        """Update the preview image display"""
        try:
            if hasattr(self, 'preview_image_label') and self.preview_image_label.winfo_exists():
                self.preview_image_label.configure(image=ctk_image, text="")
        except Exception as e:
            print(f"Error updating preview image: {e}")
            # Fallback to clear image
            self.clear_preview_image("Preview image unavailable")

    def _on_mousewheel(self, event):
        """Handle mouse wheel scrolling for the sidebar"""
        if sys.platform == "win32" or sys.platform == "darwin":
            delta = -1 * (event.delta / 120)
        else:  # Linux
            delta = -1 if event.num == 4 else 1
        
        # Get the scrollable canvas and scroll
        canvas = self.scrollable_list._canvas
        scroll_y = canvas.yview()
        if scroll_y[0] > 0 or scroll_y[1] < 1:
            canvas.yview_scroll(int(delta), "units")

    def download_logo(self):
        """Load and set the logo from local file"""
        # Logo functionality has been removed - this method is kept for compatibility
        # but no longer loads any logo since we removed the logo display
        pass

    def update_logo(self):
        """Update the logo display"""
        # Logo functionality has been removed - this method is kept for compatibility
        # but no longer updates any logo since we removed the logo display
        pass

    def handle_main_action(self):
        """Handle the main action button - always launch for installed versions"""
        version = self.selected_version.get()
        if not version:
            messagebox.showerror("Error", "Please select a version first")
            return
        
        # Always launch since we only show installed versions in sidebar
        self.launch_game()

    def download_version(self):
        """Download selected Titanic version"""
        version = self.selected_version.get()
        if not version:
            messagebox.showerror("Error", "Please select a version to download")
            return
        
        # Start download in separate thread
        thread = threading.Thread(target=self._download_version_thread, args=(version,))
        thread.daemon = True
        thread.start()

    def _download_version_thread(self, version):
        """Download version in background thread"""
        try:
            self.log_to_console(f"Starting download for {version}...")
            self.status_text.set(f"Downloading {version}...")
            self.download_progress.set(0)
            self.update()
            
            # Try scraped download URL first, then fallback patterns
            download_url = None
            response = None
            
            # Use scraped URL if available
            if version in self.download_links:
                download_url = self.download_links[version]
                self.log_to_console(f"Trying download URL: {download_url}")
                try:
                    response = requests.get(download_url, stream=True, timeout=10)
                    if response.status_code == 200:
                        self.log_to_console(f"Using API URL for {version}")
                        self.after(0, lambda: self.status_text.set(f"Using API URL for {version}"))
                except Exception as e:
                    self.log_to_console(f"API URL failed: {e}", "WARNING")
                    download_url = None
            
            # If scraped URL failed, try fallback patterns
            if not download_url or not response or response.status_code != 200:
                self.log_to_console("Trying fallback download URLs...")
                possible_urls = [
                    f"https://cdn.titanic.sh/clients/{version}.zip",
                    f"https://osu.titanic.sh/releases/{version}.zip",
                    f"https://osu.titanic.sh/download/{version}",
                    f"https://osu.titanic.sh/files/{version}.zip",
                    f"https://osu.titanic.sh/get/{version}.zip"
                ]
                
                for url in possible_urls:
                    try:
                        self.log_to_console(f"Trying: {url}")
                        response = requests.get(url, stream=True, timeout=10)
                        if response.status_code == 200:
                            download_url = url
                            self.log_to_console(f"Found working URL: {url}")
                            self.after(0, lambda: self.status_text.set(f"Using fallback URL for {version}"))
                            break
                    except Exception as e:
                        self.log_to_console(f"URL failed: {url} - {e}", "WARNING")
                        continue
            
            if not download_url or not response or response.status_code != 200:
                raise Exception("Could not find valid download URL")
            
            # Download path
            download_path = os.path.join(self.versions_dir, f"{version}.zip")
            extract_path = os.path.join(self.versions_dir, version)
            
            self.log_to_console(f"Downloading to: {download_path}")
            
            # Remove existing extraction directory if it exists
            if os.path.exists(extract_path):
                self.log_to_console(f"Removing existing directory: {extract_path}")
                shutil.rmtree(extract_path)
            
            # Download file with better progress tracking
            total_size = int(response.headers.get('content-length', 0))
            downloaded = 0
            last_progress_update = 0
            
            self.log_to_console(f"Total download size: {self.format_size(total_size)}")
            
            with open(download_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        if total_size > 0:
                            progress = (downloaded / total_size) * 100
                            # Update progress bar less frequently to avoid UI lag
                            current_time = downloaded
                            if current_time - last_progress_update > 1024 * 1024:  # Update every 1MB
                                self.download_progress.set(progress)
                                self.after(0, lambda p=progress: self.status_text.set(f"Downloading {version}: {p:.1f}%"))
                                last_progress_update = current_time
                                self.update()
            
            # Final progress update
            self.download_progress.set(100)
            self.log_to_console("Download completed successfully", "SUCCESS")
            
            self.status_text.set(f"Extracting {version}...")
            self.log_to_console(f"Extracting to: {extract_path}")
            self.update()
            
            # Extract archive
            with zipfile.ZipFile(download_path, 'r') as zip_ref:
                zip_ref.extractall(extract_path)
            
            self.log_to_console("Extraction completed successfully", "SUCCESS")
            
            # Clean up zip file
            os.remove(download_path)
            self.log_to_console(f"Cleaned up zip file: {download_path}")
            
            self.status_text.set(f"Successfully installed {version}")
            self.log_to_console(f"Successfully installed {version}", "SUCCESS")
            self.download_progress.set(100)
            self.refresh_version_buttons()
            self.select_version(version)  # Update the display and button
            
        except Exception as e:
            error_msg = f"Failed to download {version}: {str(e)}"
            self.log_to_console(error_msg, "ERROR")
            messagebox.showerror("Error", error_msg)
            self.status_text.set(f"Failed to download {version}")
            self.download_progress.set(0)

    def launch_game(self):
        """Launch selected Titanic version using osu-wine with custom arguments"""
        version = self.selected_version.get()
        if not version:
            messagebox.showerror("Error", "Please select a version to launch")
            return
        
        version_path = os.path.join(self.versions_dir, version)
        osu_exe = os.path.join(version_path, "osu!.exe")
        
        if not os.path.exists(version_path):
            messagebox.showerror("Error", f"Version {version} is not installed")
            return
        
        if not os.path.exists(osu_exe):
            messagebox.showerror("Error", f"osu!.exe not found in {version_path}")
            return
        
        try:
            # Get version configuration
            config = self.get_version_config(version)
            display_name = config['custom_name']
            
            self.log_to_console(f"Launching {display_name}...")
            self.status_text.set(f"Launching {display_name}...")
            self.launch_btn.configure(state="disabled", text="Launching...")
            self.update()
            
            # Find osu-wine executable path
            osuwine_cmd = self.find_osuwine_executable()
            if not osuwine_cmd:
                error_msg = ("osu-wine not found!\n\n"
                           "Please install osu-wine first:\n"
                           "1. Go to Options → Download osu-wine\n"
                           "2. Or install manually from https://github.com/NelloKudo/osu-winello")
                self.log_to_console("osu-wine not found", "ERROR")
                messagebox.showerror("Error", error_msg)
                return
            
            # Build command with custom arguments
            cmd = [osuwine_cmd, "--wine", osu_exe]
            
            # Add launch arguments if specified
            if config['launch_args']:
                launch_args = config['launch_args'].split()
                cmd.extend(launch_args)
                self.log_to_console(f"Using launch arguments: {config['launch_args']}")
            
            command_str = ' '.join(cmd)
            self.log_to_console(f"Executing: {command_str}")
            print(f"Launching with command: {command_str}")
            subprocess.Popen(cmd, cwd=version_path)
            
            self.status_text.set(f"Launched {display_name}")
            self.log_to_console(f"Successfully launched {display_name}", "SUCCESS")
            
            # Re-enable button after a delay
            self.after(2000, lambda: self.launch_btn.configure(state="normal", text="🎮 LAUNCH GAME"))
            
        except Exception as e:
            error_msg = f"Failed to launch {version}: {str(e)}"
            self.log_to_console(error_msg, "ERROR")
            messagebox.showerror("Error", error_msg)
            self.status_text.set(f"Failed to launch {version}")
            self.launch_btn.configure(state="normal", text="🎮 LAUNCH GAME")

    def delete_version(self):
        """Delete selected installed version"""
        version = self.selected_version.get()
        if not version:
            messagebox.showerror("Error", "Please select a version to delete")
            return
        
        version_path = os.path.join(self.versions_dir, version)
        
        if not os.path.exists(version_path):
            messagebox.showerror("Error", f"Version {version} is not installed")
            return
        
        if messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete {version}?"):
            try:
                shutil.rmtree(version_path)
                self.status_text.set(f"Deleted {version}")
                self.refresh_version_buttons()
                
                # Clear selection if deleted version was selected
                if self.selected_version.get() == version:
                    self.selected_version.set("")
                    self.current_version_name = None
                    self.header_label.configure(text="Select a Version")
                    
                    # Reset description and image
                    self.description_text.configure(state="normal")
                    self.description_text.delete("0.0", "end")
                    self.description_text.insert("0.0", "Select a version to see details...")
                    self.description_text.configure(state="disabled")
                    self.clear_preview_image("No version selected")
                    
                    # Reset settings fields
                    self.name_entry.delete(0, 'end')
                    self.launch_args_entry.delete(0, 'end')
                    
                    # Reset button to default state
                    self.launch_btn.configure(text="🎮 LAUNCH GAME", fg_color=("#3B8ED0", "#1F6AA5"))
                
            except Exception as e:
                messagebox.showerror("Error", f"Failed to delete {version}: {str(e)}")
                self.status_text.set(f"Failed to delete {version}")

    def open_versions_folder(self):
        """Open the versions folder in the file manager"""
        try:
            if sys.platform == "win32":
                os.startfile(self.versions_dir)
            else:
                subprocess.Popen(["xdg-open", self.versions_dir])
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open folder: {str(e)}")

    def save_current_version_settings(self):
        """Save settings for the currently selected version"""
        version = self.selected_version.get()
        if not version:
            messagebox.showerror("Error", "Please select a version first")
            return
        
        try:
            new_config = {
                'custom_name': self.name_entry.get().strip() or version,
                'launch_args': self.launch_args_entry.get().strip()
            }
            
            self.update_version_config(version, new_config)
            self.refresh_version_buttons()  # Update display
            
            # Update header with new custom name
            self.header_label.configure(text=new_config['custom_name'])
            
            messagebox.showinfo("Success", "Settings saved successfully!")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save settings: {str(e)}")

    def open_download_dialog(self):
        """Open download dialog showing available clients to download"""
        # Create download window
        download_window = ctk.CTkToplevel(self)
        download_window.title("Download Clients")
        download_window.geometry("800x600")
        download_window.transient(self)
        
        # Main frame
        main_frame = ctk.CTkFrame(download_window)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Title
        client_type = "Modified" if self.current_tab == "modified" else "Official"
        ctk.CTkLabel(main_frame, text=f"Available {client_type} Clients", font=ctk.CTkFont(size=24, weight="bold")).pack(pady=(10, 20))
        
        # Scrollable frame for client list
        scrollable_frame = ctk.CTkScrollableFrame(main_frame, height=400)
        scrollable_frame.pack(fill="both", expand=True, pady=(0, 20))
        scrollable_frame.grid_columnconfigure(0, weight=1)
        scrollable_frame.grid_columnconfigure(1, weight=1)
        scrollable_frame.grid_columnconfigure(2, weight=1)
        
        # Add available clients (not installed)
        row = 0
        current_versions = self.modified_versions if self.current_tab == "modified" else self.versions
        for version in current_versions:
            version_path = os.path.join(self.versions_dir, version)
            if not (os.path.exists(version_path) and os.path.exists(os.path.join(version_path, "osu!.exe"))):
                # Get version info
                config = self.get_version_config(version)
                display_name = config['custom_name']
                description = self.version_descriptions.get(version, "No description available")
                image_url = self.version_images.get(version)
                
                # Create client card
                client_frame = ctk.CTkFrame(scrollable_frame)
                client_frame.grid(row=row, column=0, columnspan=3, sticky="ew", pady=5, padx=5)
                client_frame.grid_columnconfigure(1, weight=1)
                
                # Version name - make it clickable
                name_label = ctk.CTkLabel(
                    client_frame, 
                    text=display_name, 
                    font=ctk.CTkFont(size=16, weight="bold"),
                    text_color=("#1B5E20", "#4CAF50"),
                    cursor="hand2"
                )
                name_label.grid(row=0, column=0, sticky="w", padx=10, pady=(10, 5))
                name_label.bind("<Button-1>", lambda e, v=version: self.show_client_preview(v))
                
                # Download button
                download_btn = ctk.CTkButton(
                    client_frame,
                    text="📥 Download",
                    fg_color="#1bd964",
                    hover_color="#15a34a",
                    text_color="black",
                    width=100,
                    command=lambda v=version, w=download_window: self.download_from_dialog(v, w)
                )
                download_btn.grid(row=0, column=2, sticky="e", padx=10, pady=(10, 5))
                
                # Description
                desc_label = ctk.CTkLabel(client_frame, text=description, font=ctk.CTkFont(size=12), text_color="gray")
                desc_label.grid(row=1, column=0, columnspan=3, sticky="w", padx=10, pady=(0, 10))
                
                row += 1
        
        # Close button
        close_btn = ctk.CTkButton(main_frame, text="Close", command=download_window.destroy, fg_color="#6c757d")
        close_btn.pack(pady=(10, 0))
        
        # Set grab after window is fully configured
        def set_grab_safely():
            try:
                # Release any existing grabs first
                current_focus = self.focus_get()
                if current_focus and hasattr(current_focus, 'grab_release'):
                    try:
                        current_focus.grab_release()
                    except:
                        pass
                
                # Set new grab
                download_window.grab_set()
                download_window.focus_set()
            except Exception as e:
                print(f"Grab failed: {e}")
        
        download_window.after(100, set_grab_safely)

    def download_from_dialog(self, version, window):
        """Download a version from the download dialog"""
        # Close the dialog first
        window.destroy()
        
        # Start download
        self.selected_version.set(version)
        self.download_version()

    def show_client_preview(self, version):
        """Show preview window for a client with description and image"""
        # Get version info
        config = self.get_version_config(version)
        display_name = config['custom_name']
        description = self.version_descriptions.get(version, "No description available")
        image_url = self.version_images.get(version)
        
        # Create preview window
        preview_window = ctk.CTkToplevel(self)
        preview_window.title(f"Preview - {display_name}")
        preview_window.geometry("600x500")
        preview_window.transient(self)
        
        # Main frame
        main_frame = ctk.CTkFrame(preview_window)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Title
        title_label = ctk.CTkLabel(main_frame, text=display_name, font=ctk.CTkFont(size=24, weight="bold"))
        title_label.pack(pady=(10, 20))
        
        # Preview image frame
        image_frame = ctk.CTkFrame(main_frame, corner_radius=10)
        image_frame.pack(pady=10, padx=20, fill="x")
        
        image_label = ctk.CTkLabel(image_frame, text="Loading preview...", font=ctk.CTkFont(size=14), corner_radius=8)
        image_label.pack(pady=10, padx=10)
        
        # Description
        desc_frame = ctk.CTkFrame(main_frame)
        desc_frame.pack(fill="both", expand=True, pady=(10, 20), padx=20)
        
        desc_label = ctk.CTkLabel(desc_frame, text="Description", font=ctk.CTkFont(size=16, weight="bold"))
        desc_label.pack(anchor="w", padx=10, pady=(10, 5))
        
        desc_text = ctk.CTkTextbox(desc_frame, height=150, font=ctk.CTkFont(size=12))
        desc_text.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        desc_text.insert("0.0", description)
        desc_text.configure(state="disabled")
        
        # Action buttons
        button_frame = ctk.CTkFrame(main_frame)
        button_frame.pack(pady=(0, 10))
        
        download_btn = ctk.CTkButton(
            button_frame,
            text="📥 Download",
            fg_color="#1bd964",
            hover_color="#15a34a",
            text_color="black",
            width=120,
            command=lambda: self.download_from_preview(version, preview_window)
        )
        download_btn.pack(side="left", padx=5)
        
        close_btn = ctk.CTkButton(
            button_frame,
            text="Close",
            fg_color="#6c757d",
            width=120,
            command=preview_window.destroy
        )
        close_btn.pack(side="left", padx=5)
        
        # Load preview image if available
        if image_url:
            threading.Thread(target=self.load_preview_image_for_window, args=(image_url, image_label), daemon=True).start()
        else:
            image_label.configure(text="No preview image available")
        
        # Set grab after window is fully configured
        def set_grab_safely():
            try:
                # Release any existing grabs first
                current_focus = self.focus_get()
                if current_focus and hasattr(current_focus, 'grab_release'):
                    try:
                        current_focus.grab_release()
                    except:
                        pass
                
                # Set new grab
                preview_window.grab_set()
                preview_window.focus_set()
            except Exception as e:
                print(f"Grab failed: {e}")
        
        preview_window.after(100, set_grab_safely)

    def load_preview_image_for_window(self, image_url, image_label):
        """Load preview image for preview window"""
        try:
            # Add proper headers to mimic browser request
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Referer': 'https://osu.titanic.sh/download/',
                'Accept': 'image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1'
            }
            
            response = requests.get(image_url, headers=headers, timeout=10)
            if response.status_code == 200:
                # Load image from response
                image_data = io.BytesIO(response.content)
                pil_image = Image.open(image_data)
                
                # Get original dimensions
                original_width, original_height = pil_image.size
                
                # Calculate display size - smaller for preview window
                target_width = 300
                
                # Calculate height to maintain aspect ratio
                aspect_ratio = original_height / original_width
                target_height = int(target_width * aspect_ratio)
                
                # Limit maximum height to prevent overly tall images
                max_height = 200
                if target_height > max_height:
                    target_height = max_height
                    # Recalculate width to maintain aspect ratio
                    target_width = int(max_height / aspect_ratio)
                
                # Resize image with proper dimensions
                pil_image = pil_image.resize((target_width, target_height), Image.Resampling.LANCZOS)
                
                # Create CTkImage with proper size
                ctk_image = ctk.CTkImage(light_image=pil_image, dark_image=pil_image, size=(target_width, target_height))
                
                # Update UI in main thread
                self.after(0, lambda: image_label.configure(image=ctk_image, text=""))
            else:
                self.after(0, lambda: image_label.configure(text="Preview image unavailable", image=""))
        except Exception as e:
            print(f"Failed to load preview image: {e}")
            self.after(0, lambda: image_label.configure(text="Failed to load preview image", image=""))

    def download_from_preview(self, version, window):
        """Download a version from the preview window"""
        # Close the preview window first
        window.destroy()
        
        # Start download
        self.selected_version.set(version)
        self.download_version()

    def open_options_dialog(self):
        """Open options dialog for appearance and settings"""
        # Create options window
        options_window = ctk.CTkToplevel(self)
        options_window.title("Options")
        options_window.geometry("500x400")
        options_window.transient(self)
        
        # Main frame
        main_frame = ctk.CTkFrame(options_window)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Title
        ctk.CTkLabel(main_frame, text="Options", font=ctk.CTkFont(size=24, weight="bold")).pack(pady=(10, 20))
        
        # Appearance section
        appearance_frame = ctk.CTkFrame(main_frame)
        appearance_frame.pack(fill="x", pady=(0, 20))
        
        ctk.CTkLabel(appearance_frame, text="Appearance", font=ctk.CTkFont(size=18, weight="bold")).pack(anchor="w", padx=10, pady=(10, 5))
        
        # Dark/Light mode toggle
        mode_frame = ctk.CTkFrame(appearance_frame)
        mode_frame.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkLabel(mode_frame, text="Theme:", font=ctk.CTkFont(weight="bold")).pack(side="left", padx=10)
        
        mode_switch = ctk.CTkSwitch(
            mode_frame,
            text="Dark Mode",
            variable=self.appearance_mode,
            onvalue="dark",
            offvalue="light",
            command=lambda: self.update_appearance_mode()
        )
        mode_switch.pack(side="left", padx=10)
        
        # Set initial state
        mode_switch.select() if self.appearance_mode.get() == "dark" else mode_switch.deselect()
        
        # Accent color selection
        color_frame = ctk.CTkFrame(appearance_frame)
        color_frame.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkLabel(color_frame, text="Accent Color:", font=ctk.CTkFont(weight="bold")).pack(side="left", padx=10)
        
        color_options = ["blue", "green", "dark-blue", "red"]
        color_menu = ctk.CTkOptionMenu(
            color_frame,
            variable=self.accent_color,
            values=color_options,
            command=lambda choice: self.update_accent_color(choice)
        )
        color_menu.pack(side="left", padx=10)
        
        # Tools section
        tools_frame = ctk.CTkFrame(main_frame)
        tools_frame.pack(fill="x", pady=(0, 20))
        
        ctk.CTkLabel(tools_frame, text="Tools", font=ctk.CTkFont(size=18, weight="bold")).pack(anchor="w", padx=10, pady=(10, 5))
        
        # osu-wine download button
        self.osuwine_btn = ctk.CTkButton(
            tools_frame,
            text="📥 Download osu-wine",
            fg_color="#ff6b35",
            hover_color="#e55a2b",
            command=self.download_osuwine_placeholder
        )
        self.osuwine_btn.pack(fill="x", padx=10, pady=5)
        
        # Update button state based on installation status
        self.update_osuwine_button_state()
        
        # Help text
        help_text = ctk.CTkTextbox(main_frame, height=80, font=ctk.CTkFont(size=10))
        help_text.pack(fill="x", pady=(0, 20))
        help_text.insert("0.0", 
            "Theme: Switch between dark and light modes\n"
            "Accent Color: Change the primary color theme\n"
            "osu-wine: Download the osu-wine launcher for running Titanic clients"
        )
        help_text.configure(state="disabled")
        
        # Close button
        close_btn = ctk.CTkButton(main_frame, text="Close", command=options_window.destroy, fg_color="#6c757d")
        close_btn.pack(pady=(10, 0))
        
        # Set grab after window is fully configured
        def set_grab_safely():
            try:
                # Release any existing grabs first
                current_focus = self.focus_get()
                if current_focus and hasattr(current_focus, 'grab_release'):
                    try:
                        current_focus.grab_release()
                    except:
                        pass
                
                # Set new grab
                options_window.grab_set()
                options_window.focus_set()
            except Exception as e:
                print(f"Grab failed: {e}")
        
        options_window.after(100, set_grab_safely)

    def update_appearance_mode(self):
        """Update the appearance mode"""
        mode = self.appearance_mode.get()
        ctk.set_appearance_mode(mode)
        # Save to config
        self.save_options_config()

    def update_accent_color(self, color):
        """Update the accent color"""
        ctk.set_default_color_theme(color)
        self.accent_color.set(color)
        # Save to config
        self.save_options_config()
        # Note: Color theme change requires restart to take full effect
        messagebox.showinfo("Color Changed", f"Accent color changed to {color}.\nRestart the launcher for full effect.")

    def download_osuwine_placeholder(self):
        """Install osu-wine automatically"""
        # Check if osu-wine is already installed
        if self.check_osuwine_installed():
            messagebox.showinfo("Already Installed", "osu-wine is already installed on your system!")
            return
        
        # Ask for confirmation
        if not messagebox.askyesno("Install osu-wine", 
            "This will download and install osu-wine.\n\n"
            "The installation will:\n"
            "1. Clone the osu-winello repository\n"
            "2. Run the installation script\n\n"
            "Continue?"):
            return
        
        # Start installation in background thread
        threading.Thread(target=self.install_osuwine, daemon=True).start()

    def check_osuwine_installed(self):
        """Check if osu-wine is installed"""
        try:
            # Try multiple methods to find osu-wine
            import shutil
            
            # Method 1: Check if command exists in PATH
            osuwine_path = shutil.which("osu-wine")
            if osuwine_path:
                result = subprocess.run(["osu-wine", "--help"], 
                                      capture_output=True, 
                                      text=True, 
                                      timeout=5)
                return result.returncode == 0 and "osu-wine" in result.stdout.lower()
            
            # Method 2: Check common installation paths (for bundled executables)
            common_paths = [
                "/usr/local/bin/osu-wine",
                "/usr/bin/osu-wine",
                os.path.expanduser("~/.local/bin/osu-wine"),
                os.path.expanduser("~/bin/osu-wine")
            ]
            
            for path in common_paths:
                if os.path.exists(path) and os.access(path, os.X_OK):
                    result = subprocess.run([path, "--help"], 
                                          capture_output=True, 
                                          text=True, 
                                          timeout=5)
                    if result.returncode == 0 and "osu-wine" in result.stdout.lower():
                        return True
            
            return False
            
        except (subprocess.TimeoutExpired, FileNotFoundError, subprocess.CalledProcessError, ImportError):
            return False

    def find_osuwine_executable(self):
        """Find the full path to osu-wine executable"""
        try:
            import shutil
            
            # Method 1: Check if command exists in PATH
            osuwine_path = shutil.which("osu-wine")
            if osuwine_path:
                return osuwine_path
            
            # Method 2: Check common installation paths
            common_paths = [
                "/usr/local/bin/osu-wine",
                "/usr/bin/osu-wine",
                os.path.expanduser("~/.local/bin/osu-wine"),
                os.path.expanduser("~/bin/osu-wine")
            ]
            
            for path in common_paths:
                if os.path.exists(path) and os.access(path, os.X_OK):
                    return path
            
            return None
            
        except ImportError:
            # Fallback without shutil
            common_paths = [
                "/usr/local/bin/osu-wine",
                "/usr/bin/osu-wine",
                os.path.expanduser("~/.local/bin/osu-wine"),
                os.path.expanduser("~/bin/osu-wine")
            ]
            
            for path in common_paths:
                if os.path.exists(path) and os.access(path, os.X_OK):
                    return path
            
            return None

    def install_osuwine(self):
        """Install osu-wine in background thread"""
        try:
            # Update UI to show installation in progress
            self.after(0, lambda: self.status_text.set("Installing osu-wine..."))
            
            # Create temporary directory for installation
            temp_dir = tempfile.mkdtemp()
            clone_path = os.path.join(temp_dir, "osu-winello")
            
            # Clone the repository
            self.after(0, lambda: self.status_text.set("Cloning osu-winello repository..."))
            clone_result = subprocess.run([
                "git", "clone", 
                "https://github.com/NelloKudo/osu-winello.git",
                clone_path
            ], capture_output=True, text=True, timeout=60)
            
            if clone_result.returncode != 0:
                raise Exception(f"Failed to clone repository: {clone_result.stderr}")
            
            # Make script executable
            self.after(0, lambda: self.status_text.set("Preparing installation script..."))
            script_path = os.path.join(clone_path, "osu-winello.sh")
            subprocess.run(["chmod", "+x", script_path], check=True)
            
            # Run installation script with proper environment
            self.after(0, lambda: self.status_text.set("Running osu-wine installation..."))
            
            # Set up environment for proper PATH handling
            env = os.environ.copy()
            
            # Try to install to user's local bin directory
            install_result = subprocess.run([
                "./osu-winello.sh"
            ], cwd=clone_path, capture_output=True, text=True, timeout=300, env=env)  # 5 minute timeout
            
            if install_result.returncode != 0:
                # Try alternative installation method
                self.after(0, lambda: self.status_text.set("Trying alternative installation..."))
                
                # Try manual installation to user bin directory
                user_bin = os.path.expanduser("~/.local/bin")
                os.makedirs(user_bin, exist_ok=True)
                
                # Create a simple installation script
                install_script = f"""
#!/bin/bash
set -e

echo "Installing osu-wine to {user_bin}..."

# Download osu-wine script
curl -fsSL https://raw.githubusercontent.com/NelloKudo/osu-winello/main/osu-wine.sh -o {user_bin}/osu-wine
chmod +x {user_bin}/osu-wine

# Add to PATH if not already there
if ! echo $PATH | grep -q "{user_bin}"; then
    echo 'export PATH="$PATH:{user_bin}"' >> ~/.bashrc
    echo 'export PATH="$PATH:{user_bin}"' >> ~/.profile
fi

echo "Installation complete! Please restart your terminal or run:"
echo "export PATH=\"$PATH:{user_bin}\""
"""
                
                alt_install_result = subprocess.run(["bash", "-c", install_script], 
                                                  capture_output=True, text=True, timeout=120)
                
                if alt_install_result.returncode != 0:
                    raise Exception(f"Both installation methods failed. Manual: {alt_install_result.stderr}")
            
            # Clean up temporary directory
            shutil.rmtree(temp_dir, ignore_errors=True)
            
            # Update UI to show success
            self.after(0, lambda: self.status_text.set("osu-wine installed successfully!"))
            
            # Show success message with PATH instructions
            success_msg = ("osu-wine has been successfully installed!\n\n"
                          "If you still get 'not found' errors, you may need to:\n"
                          "1. Restart the launcher\n"
                          "2. Or restart your terminal\n"
                          "3. Or run: export PATH=\"$PATH:~/.local/bin\"\n\n"
                          "You can now launch Titanic clients using the launcher.")
            
            self.after(0, lambda: messagebox.showinfo("Installation Complete", success_msg))
            
            # Update button state
            self.after(0, self.update_osuwine_button_state)
            
        except subprocess.TimeoutExpired:
            self.after(0, lambda: self.status_text.set("Installation timed out"))
            self.after(0, lambda: messagebox.showerror(
                "Installation Failed", 
                "Installation timed out. Please try again or install manually.\n\n"
                "Manual installation:\n"
                "1. Visit: https://github.com/NelloKudo/osu-winello\n"
                "2. Follow the installation instructions"
            ))
        except Exception as e:
            self.after(0, lambda: self.status_text.set(f"Installation failed: {str(e)}"))
            self.after(0, lambda: messagebox.showerror(
                "Installation Failed", 
                f"Failed to install osu-wine:\n{str(e)}\n\n"
                "Manual installation:\n"
                "1. Visit: https://github.com/NelloKudo/osu-winello\n"
                "2. Follow the installation instructions\n\n"
                "After installation, restart the launcher."
            ))
        finally:
            # Clean up temporary directory
            try:
                if 'temp_dir' in locals():
                    shutil.rmtree(temp_dir, ignore_errors=True)
            except:
                pass

    def update_osuwine_button_state(self):
        """Update osu-wine button state based on installation status"""
        if hasattr(self, 'osuwine_btn'):
            if self.check_osuwine_installed():
                self.osuwine_btn.configure(
                    text="✓ osu-wine Installed",
                    fg_color="#28a745",
                    state="disabled"
                )
            else:
                self.osuwine_btn.configure(
                    text="📥 Download osu-wine",
                    fg_color="#ff6b35",
                    hover_color="#e55a2b",
                    state="normal"
                )

    def save_options_config(self):
        """Save options configuration"""
        try:
            # Load existing config
            config = {}
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
            
            # Add options
            config['options'] = {
                'appearance_mode': self.appearance_mode.get(),
                'accent_color': self.accent_color.get()
            }
            
            # Add auth data if logged in
            if self.auth_token:
                config['auth'] = {
                    'token': self.auth_token,
                    'user_data': self.user_data
                }
            
            # Save config
            with open(self.config_file, 'w') as f:
                json.dump(config, f, indent=2)
        except Exception as e:
            print(f"Failed to save options config: {e}")

    def load_auth_config(self):
        """Load authentication configuration"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                    
                if 'auth' in config:
                    self.auth_token = config['auth'].get('token')
                    self.user_data = config['auth'].get('user_data', {})
                    self.update_user_display()
        except Exception as e:
            print(f"Failed to load auth config: {e}")

    def open_login_dialog(self):
        """Open login dialog"""
        if self.auth_token:
            # Already logged in, show logout confirmation
            if messagebox.askyesno("Logout", f"Logout from {self.username.get()}?"):
                self.logout()
            return
        
        # Create login dialog
        login_window = ctk.CTkToplevel(self)
        login_window.title("Login to Titanic")
        login_window.geometry("400x300")
        login_window.transient(self)
        
        # Make window visible before grabbing
        login_window.update()
        
        # Set grab after window is visible
        def set_grab_safely():
            try:
                # Release any existing grabs first
                current_focus = self.focus_get()
                if current_focus and hasattr(current_focus, 'grab_release'):
                    try:
                        current_focus.grab_release()
                    except:
                        pass
                
                # Set new grab
                login_window.grab_set()
                login_window.focus_set()
            except Exception as e:
                print(f"Grab failed: {e}")
        
        login_window.after(100, set_grab_safely)
        
        # Center the dialog
        login_window.update_idletasks()
        x = (login_window.winfo_screenwidth() // 2) - (400 // 2)
        y = (login_window.winfo_screenheight() // 2) - (300 // 2)
        login_window.geometry(f"400x300+{x}+{y}")
        
        main_frame = ctk.CTkFrame(login_window)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Title
        ctk.CTkLabel(main_frame, text="Login to Titanic", font=ctk.CTkFont(size=20, weight="bold")).pack(pady=(0, 20))
        
        # Username
        ctk.CTkLabel(main_frame, text="Username:").pack(anchor="w")
        username_entry = ctk.CTkEntry(main_frame, width=300)
        username_entry.pack(fill="x", pady=(0, 10))
        
        # Password
        ctk.CTkLabel(main_frame, text="Password:").pack(anchor="w")
        password_entry = ctk.CTkEntry(main_frame, width=300, show="*")
        password_entry.pack(fill="x", pady=(0, 20))
        
        # Buttons
        button_frame = ctk.CTkFrame(main_frame)
        button_frame.pack(fill="x")
        
        def do_login():
            username = username_entry.get().strip()
            password = password_entry.get().strip()
            
            if not username or not password:
                messagebox.showerror("Error", "Please enter username and password")
                return
            
            # Disable buttons during login
            login_btn.configure(state="disabled")
            cancel_btn.configure(state="disabled")
            
            # Start login in background thread
            threading.Thread(target=self.login_to_titanic, args=(username, password, login_window), daemon=True).start()
        
        login_btn = ctk.CTkButton(button_frame, text="Login", command=do_login)
        login_btn.pack(side="left", padx=(0, 10))
        
        cancel_btn = ctk.CTkButton(button_frame, text="Cancel", command=login_window.destroy, fg_color="#6c757d")
        cancel_btn.pack(side="left")
        
        # Focus on username entry
        username_entry.focus()
        login_window.bind("<Return>", lambda e: do_login())

    def login_to_titanic(self, username, password, login_window):
        """Login to Titanic API"""
        try:
            # Create Basic Auth header
            credentials = f"{username}:{password}"
            encoded_credentials = base64.b64encode(credentials.encode()).decode()
            
            headers = {
                "Authorization": f"Basic {encoded_credentials}",
                "Content-Type": "application/json"
            }
            
            # Make login request
            response = requests.post(
                "https://api.titanic.sh/account/login",
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                token_data = response.json()
                self.auth_token = token_data["access_token"]
                
                # Get user data
                self.fetch_user_data()
                
                # Update UI
                self.after(0, lambda: self.update_user_display())
                self.after(0, lambda: self.save_options_config())
                self.after(0, lambda: login_window.destroy())
                self.after(0, lambda: messagebox.showinfo("Success", f"Logged in as {self.username.get()}!"))
            else:
                error_msg = "Login failed"
                try:
                    error_data = response.json()
                    error_msg = error_data.get("details", error_msg)
                except:
                    pass
                
                self.after(0, lambda: messagebox.showerror("Login Failed", error_msg))
                
        except Exception as e:
            self.after(0, lambda: messagebox.showerror("Login Error", f"An error occurred: {str(e)}"))
        finally:
            # Re-enable buttons
            self.after(0, lambda: login_window.children["!ctkframe"].children["!ctkframe"].children["!ctkbutton"].configure(state="normal"))
            self.after(0, lambda: login_window.children["!ctkframe"].children["!ctkframe"].children["!ctkbutton2"].configure(state="normal"))

    def fetch_user_data(self):
        """Fetch user data from API"""
        try:
            if not self.auth_token:
                return
            
            headers = {
                "Authorization": f"Bearer {self.auth_token}",
                "Content-Type": "application/json"
            }
            
            # Get user profile
            response = requests.get(
                "https://api.titanic.sh/account/profile",
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                user_profile = response.json()
                self.user_data = {
                    'username': user_profile.get('name', 'Unknown'),
                    'id': user_profile.get('id', 0),
                    'country': user_profile.get('country', 'US'),
                    'stats': user_profile.get('stats', [])
                }
                
                # Extract stats for the preferred mode
                stats = user_profile.get('stats', [])
                if stats:
                    # Find stats for the preferred mode (usually first one or mode 0 for osu!std)
                    preferred_stats = None
                    for stat in stats:
                        if stat.get('mode') == user_profile.get('preferred_mode', 0):
                            preferred_stats = stat
                            break
                    
                    # If no preferred mode found, use first stats
                    if not preferred_stats and stats:
                        preferred_stats = stats[0]
                    
                    if preferred_stats:
                        self.user_data['rank'] = preferred_stats.get('rank', 0)
                        self.user_data['pp'] = preferred_stats.get('pp', 0)
                        self.user_data['country_rank'] = preferred_stats.get('country_rank', 0)
                
                # Fetch user avatar
                self.fetch_user_avatar(user_profile.get('id', 0))
                
                # Store user ID for avatar fetching
                self.user_data['id'] = user_profile.get('id', 0)
                        
            else:
                # Use basic info
                self.user_data = {
                    'username': 'User',
                    'id': 0,
                    'country': 'US',
                    'rank': 0,
                    'pp': 0,
                    'country_rank': 0
                }
                
        except Exception as e:
            print(f"Failed to fetch user data: {e}")
            self.user_data = {
                'username': 'User',
                'id': 0,
                'country': 'US',
                'rank': 0,
                'pp': 0,
                'country_rank': 0
            }

    def fetch_user_avatar(self, user_id):
        """Fetch user avatar from Titanic API"""
        try:
            if not user_id or user_id == 0:
                return
            
            # Try common avatar URL patterns for osu-like servers
            avatar_urls = [
                f"https://osu.titanic.sh/a/{user_id}",  # Correct pattern: osu.titanic.sh/a/user_id
                f"https://a.titanic.sh/{user_id}",  # Alternative pattern
                f"https://osu.titanic.sh/images/avatars/{user_id}",  # Fallback pattern
                f"https://cdn.titanic.sh/avatars/{user_id}",  # CDN pattern
            ]
            
            # Try each URL pattern
            for avatar_url in avatar_urls:
                try:
                    response = requests.head(avatar_url, timeout=5)
                    if response.status_code == 200:
                        print(f"Found avatar at: {avatar_url}")
                        self.load_avatar_image(avatar_url)
                        return
                except:
                    continue
            
            print(f"No avatar found for user {user_id}")
            
        except Exception as e:
            print(f"Failed to fetch user avatar: {e}")
            # Keep default avatar

    def load_avatar_image(self, avatar_url):
        """Load user avatar image from URL"""
        try:
            # Add proper headers to mimic browser request
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Referer': 'https://osu.titanic.sh/',
                'Accept': 'image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.9'
            }
            
            response = requests.get(avatar_url, headers=headers, timeout=10)
            response.raise_for_status()
            
            # Load image
            img = Image.open(io.BytesIO(response.content))
            # Resize to avatar size (40x40)
            img = img.resize((40, 40), Image.Resampling.LANCZOS)
            
            # Create CTkImage
            self.avatar_image = ctk.CTkImage(light_image=img, dark_image=img, size=(40, 40))
            
            # Update avatar display
            self.after(0, self.update_avatar_display)
            
        except Exception as e:
            print(f"Failed to load avatar image: {e}")
            # Keep default avatar

    def update_user_display(self):
        """Update user display in sidebar"""
        if self.auth_token and self.user_data:
            self.username.set(self.user_data.get('username', 'Unknown'))
            self.auth_btn.configure(text="🚪 Logout")
            
            # Display real user stats
            rank = self.user_data.get('rank', 0)
            pp = self.user_data.get('pp', 0)
            country = self.user_data.get('country', 'US')
            
            self.user_rank.set(f"#{rank:,}" if rank > 0 else "-")
            self.user_pp.set(f"{pp:.2f}" if pp > 0 else "-")
            self.user_country.set(country)
        else:
            self.username.set("Not logged in")
            self.user_rank.set("-")
            self.user_pp.set("-")
            self.user_country.set("-")
            self.auth_btn.configure(text="🔑 Login")
            # Reset avatar
            self.avatar_image = None
            self.update_avatar_display()

    def update_avatar_display(self):
        """Update avatar display in sidebar"""
        if self.avatar_image and hasattr(self.avatar_image, 'cget'):
            try:
                self.avatar_label.configure(image=self.avatar_image, text="")
            except Exception as e:
                print(f"Failed to update avatar: {e}")
                self.avatar_label.configure(text="👤")
        else:
            self.avatar_label.configure(text="👤")

    def logout(self):
        """Logout user"""
        self.auth_token = None
        self.user_data = {}
        self.update_user_display()
        self.save_options_config()
        messagebox.showinfo("Logged Out", "You have been logged out.")

    def load_options_config(self):
        """Load options configuration"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                    
                options = config.get('options', {})
                self.appearance_mode.set(options.get('appearance_mode', 'dark'))
                self.accent_color.set(options.get('accent_color', 'blue'))
                
                # Apply settings
                ctk.set_appearance_mode(self.appearance_mode.get())
                ctk.set_default_color_theme(self.accent_color.get())
        except Exception as e:
            print(f"Failed to load options config: {e}")

    def toggle_console_section(self):
        """Toggle collapse state of console section"""
        if self.console_collapsed:
            # Expand
            self.console_content_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))
            self.console_toggle_btn.configure(text="▼")
            self.console_collapsed = False
        else:
            # Collapse
            self.console_content_frame.pack_forget()
            self.console_toggle_btn.configure(text="▶")
            self.console_collapsed = True

    def clear_console(self):
        """Clear the console output"""
        self.console_text.configure(state="normal")
        self.console_text.delete("0.0", "end")
        self.console_text.insert("0.0", "Console cleared...\n")
        self.console_text.configure(state="disabled")

    def log_to_console(self, message, level="INFO"):
        """Log a message to the console"""
        import datetime
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        
        # Color coding for different levels
        if level == "ERROR":
            prefix = f"[{timestamp}] [ERROR] "
        elif level == "WARNING":
            prefix = f"[{timestamp}] [WARN]  "
        elif level == "SUCCESS":
            prefix = f"[{timestamp}] [SUCCESS] "
        else:
            prefix = f"[{timestamp}] [INFO]  "
        
        full_message = f"{prefix}{message}\n"
        
        # Update console in main thread
        self.after(0, lambda: self._update_console(full_message))

    def _update_console(self, message):
        """Update console text widget (must be called from main thread)"""
        try:
            self.console_text.configure(state="normal")
            self.console_text.insert("end", message)
            self.console_text.see("end")  # Auto-scroll to bottom
            self.console_text.configure(state="disabled")
        except Exception as e:
            print(f"Failed to update console: {e}")

    def toggle_details_section(self):
        """Toggle collapse state of version details section"""
        if self.details_collapsed:
            # Expand
            self.details_content_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))
            self.details_toggle_btn.configure(text="▼")
            self.details_collapsed = False
        else:
            # Collapse
            self.details_content_frame.pack_forget()
            self.details_toggle_btn.configure(text="▶")
            self.details_collapsed = True

    def toggle_settings_section(self):
        """Toggle collapse state of version settings section"""
        if self.settings_collapsed:
            # Expand
            self.settings_content_frame.pack(fill="x", padx=10, pady=(0, 10))
            self.settings_toggle_btn.configure(text="▼")
            self.settings_collapsed = False
        else:
            # Collapse
            self.settings_content_frame.pack_forget()
            self.settings_toggle_btn.configure(text="▶")
            self.settings_collapsed = True

    def get_directory_size(self, path):
        """Calculate total size of a directory"""
        total_size = 0
        try:
            for dirpath, dirnames, filenames in os.walk(path):
                for filename in filenames:
                    filepath = os.path.join(dirpath, filename)
                    if os.path.exists(filepath):
                        total_size += os.path.getsize(filepath)
        except Exception:
            pass
        return total_size

    def format_size(self, size_bytes):
        """Format size in human readable format"""
        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.1f} KB"
        elif size_bytes < 1024 * 1024 * 1024:
            return f"{size_bytes / (1024 * 1024):.1f} MB"
        else:
            return f"{size_bytes / (1024 * 1024 * 1024):.1f} GB"

    def load_config(self):
        """Load version configurations from file"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    self.version_configs = json.load(f)
        except Exception as e:
            print(f"Failed to load config: {e}")
            self.version_configs = {}

    def save_config(self):
        """Save version configurations to file"""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.version_configs, f, indent=2)
        except Exception as e:
            print(f"Failed to save config: {e}")

    def get_version_config(self, version):
        """Get configuration for a specific version"""
        return self.version_configs.get(version, {
            'custom_name': version,
            'launch_args': ''
        })

    def update_version_config(self, version, config):
        """Update configuration for a specific version"""
        self.version_configs[version] = config
        self.save_config()

def main():
    app = TitanicLauncher()
    app.mainloop()

if __name__ == "__main__":
    main()
