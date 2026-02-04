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
        self.download_links = {}
        self.version_descriptions = {}
        self.version_images = {}
        self.version_configs = {}  # Per-version configuration
        self.selected_version = ctk.StringVar()
        self.download_progress = ctk.DoubleVar()
        self.status_text = ctk.StringVar(value="Ready")
        self.current_version_name = None
        
        # Drag and drop variables
        self.version_buttons = {}  # Store references to version buttons
        
        # Initialize collapse states before UI setup
        self.details_collapsed = True
        self.settings_collapsed = True
        self.console_collapsed = True
        
        # Options variables
        self.appearance_mode = ctk.StringVar(value="dark")
        self.accent_color = ctk.StringVar(value="blue")
        
        # Visual customization variables
        self.custom_bg_image = ctk.StringVar(value="")
        self.custom_font_size = ctk.IntVar(value=12)
        self.button_corner_radius = ctk.IntVar(value=8)
        self.sidebar_width = ctk.IntVar(value=250)
        
        # Layout customization variables
        self.sidebar_position = ctk.StringVar(value="left")
        self.custom_window_width = ctk.IntVar(value=1000)
        self.custom_window_height = ctk.IntVar(value=700)
        
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
        self.load_customization_config()
        
        # Bind window resize event to update background
        self.bind("<Configure>", self.on_window_resize)

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

        # Version list with scroll wheel support
        self.scrollable_list = ctk.CTkScrollableFrame(self.sidebar_frame, label_text="Installed Versions")
        self.scrollable_list.grid(row=2, column=0, padx=15, pady=10, sticky="nsew")
        
        # Enable scroll wheel support
        self.scrollable_list.bind("<MouseWheel>", self._on_mousewheel)
        self.scrollable_list.bind("<Button-4>", self._on_mousewheel)  # Linux scroll up
        self.scrollable_list.bind("<Button-5>", self._on_mousewheel)  # Linux scroll down

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

        # Single column layout for installed versions with scrolling
        self.main_scrollable = ctk.CTkScrollableFrame(self.main_frame)
        self.main_scrollable.pack(fill="both", expand=True, padx=20, pady=10)
        
        # Enable scroll wheel support for main area
        self.main_scrollable.bind("<MouseWheel>", self._on_mousewheel)
        self.main_scrollable.bind("<Button-4>", self._on_mousewheel)  # Linux scroll up
        self.main_scrollable.bind("<Button-5>", self._on_mousewheel)  # Linux scroll down
        
        self.content_frame = ctk.CTkFrame(self.main_scrollable)
        self.content_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Version details section (collapsible)
        self.details_frame = ctk.CTkFrame(self.content_frame)
        self.details_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        # Collapsible header for version details
        self.details_header_frame = ctk.CTkFrame(self.details_frame)
        self.details_header_frame.pack(fill="x", padx=10, pady=(10, 5))
        self.details_header_frame.grid_columnconfigure(1, weight=1)
        
        self.details_toggle_btn = ctk.CTkButton(
            self.details_header_frame,
            text="▶",
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
        # Don't pack initially - start collapsed
        
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
            text="▶",
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
        # Don't pack initially - start collapsed
        
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
            text="▶",
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
        # Don't pack initially - start collapsed
        
        # Console text widget
        self.console_text = ctk.CTkTextbox(self.console_content_frame, height=150, font=ctk.CTkFont(family="Courier", size=10))
        self.console_text.pack(fill="both", expand=True, padx=10, pady=10)
        self.console_text.insert("0.0", "Console output will appear here...\n")
        self.console_text.configure(state="disabled")

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
            
            # Sort versions from newest to oldest using the existing version_key method
            versions.sort(key=TitanicLauncher.version_key, reverse=True)
            
            # Store data for later use
            self.versions = versions
            self.download_links = download_links
            self.version_descriptions = version_descriptions
            self.version_images = version_images
            
            # Update UI in main thread
            self.after(0, self._update_versions_ui)
            self.after(0, lambda: self.status_text.set(f"Loaded {len(versions)} versions from Titanic API"))
            self.log_to_console(f"Successfully loaded {len(versions)} versions", "SUCCESS")
            
        except Exception as e:
            # Fallback to known versions on error
            self.log_to_console(f"API error: {str(e)}", "ERROR")
            fallback_versions = ["b20151228.3", "b20150826.3", "b20150331.2", "b20141216.1", "b20131216.1"]
            self.download_links = {}
            self.version_descriptions = {v: "Fallback version" for v in fallback_versions}
            self.version_images = {}
            self.versions = fallback_versions
            self.after(0, self._update_versions_ui)
            self.after(0, lambda: self.status_text.set(f"Using fallback versions (API error: {str(e)})"))
            self.log_to_console("Using fallback versions due to API error", "WARNING")

    def _update_versions_ui(self):
        """Update UI with fetched versions - this method should not overwrite the version lists"""
        # Don't overwrite self.versions or self.modified_versions here
        # They should only be set in the _fetch_versions_thread method
        
        # Add imported versions to the list
        imported_versions = self.version_configs.get('_imported_versions', [])
        for imported_version in imported_versions:
            if imported_version not in self.versions:
                self.versions.append(imported_version)
        
        # Just refresh the version buttons to show current state
        self.refresh_version_buttons()
        
        self.status_text.set("Versions loaded")
    
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

    def refresh_version_buttons(self):
        """Refresh the version buttons in the sidebar - show only installed versions"""
        # Clear existing buttons
        for widget in self.scrollable_list.winfo_children():
            widget.destroy()
        
        self.scrollable_list.grid_columnconfigure(0, weight=1)
        self.version_buttons.clear()
        
        # Get installed versions in custom order if available, otherwise default order
        installed_versions = self.get_installed_versions_in_order()
        
        # Add buttons for installed versions only
        for i, version in enumerate(installed_versions):
            # Get custom name
            config = self.get_version_config(version)
            display_name = config['custom_name']
            
            # Create frame for version button and controls
            version_frame = ctk.CTkFrame(self.scrollable_list)
            version_frame.grid(row=i, column=0, sticky="ew", pady=2)
            version_frame.grid_columnconfigure(0, weight=1)
            
            # Create version button
            btn = ctk.CTkButton(
                version_frame,
                text=display_name,
                fg_color="transparent",
                border_width=1,
                anchor="w",
                height=40,
                command=lambda v=version: self.select_version(v)
            )
            btn.grid(row=0, column=0, sticky="ew", padx=(0, 5))
            btn.configure(text_color=("gray10", "gray90"))
            
            # Create control buttons frame
            control_frame = ctk.CTkFrame(version_frame, fg_color="transparent")
            control_frame.grid(row=0, column=1, sticky="ns")
            
            # Up button
            up_btn = ctk.CTkButton(
                control_frame,
                text="▲",
                width=25,
                height=20,
                fg_color="gray30",
                text_color=("gray10", "gray90"),
                command=lambda v=version: self.move_version_up(v)
            )
            up_btn.grid(row=0, column=0, padx=(0, 2))
            
            # Down button
            down_btn = ctk.CTkButton(
                control_frame,
                text="▼",
                width=25,
                height=20,
                fg_color="gray30",
                text_color=("gray10", "gray90"),
                command=lambda v=version: self.move_version_down(v)
            )
            down_btn.grid(row=1, column=0, padx=(0, 0))
            
            # Store reference
            self.version_buttons[version] = btn
        
        # If no versions installed, show message
        if not installed_versions:
            no_versions_label = ctk.CTkLabel(
                self.scrollable_list,
                text="No versions installed\nClick 'Download Clients' to get started",
                font=ctk.CTkFont(size=12),
                text_color="gray"
            )
            no_versions_label.grid(row=0, column=0, pady=20)

    def get_installed_versions_in_order(self):
        """Get installed versions in custom order if available"""
        # Get all installed versions
        installed_versions = []
        for version in self.versions:
            version_path = os.path.join(self.versions_dir, version)
            if os.path.exists(version_path) and os.path.exists(os.path.join(version_path, "osu!.exe")):
                installed_versions.append(version)
        
        # Check if we have a custom order saved
        version_order = self.version_configs.get('_version_order', [])
        
        # Filter the order to only include installed versions
        ordered_versions = [v for v in version_order if v in installed_versions]
        
        # Add any newly installed versions that aren't in the order yet
        for version in installed_versions:
            if version not in ordered_versions:
                ordered_versions.append(version)
        
        return ordered_versions

    def move_version_up(self, version):
        """Move a version up in the list"""
        version_order = self.get_installed_versions_in_order()
        
        try:
            current_index = version_order.index(version)
            if current_index > 0:
                # Swap with previous version
                version_order[current_index], version_order[current_index - 1] = \
                    version_order[current_index - 1], version_order[current_index]
                
                # Save the new order
                self.version_configs['_version_order'] = version_order
                self.save_config()
                
                # Refresh the buttons
                self.refresh_version_buttons()
        except ValueError:
            pass

    def move_version_down(self, version):
        """Move a version down in the list"""
        version_order = self.get_installed_versions_in_order()
        
        try:
            current_index = version_order.index(version)
            if current_index < len(version_order) - 1:
                # Swap with next version
                version_order[current_index], version_order[current_index + 1] = \
                    version_order[current_index + 1], version_order[current_index]
                
                # Save the new order
                self.version_configs['_version_order'] = version_order
                self.save_config()
                
                # Refresh the buttons
                self.refresh_version_buttons()
        except ValueError:
            pass

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
            
            # If API URL failed, try fallback patterns
            if not response or response.status_code != 200:
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
            
            if not response or response.status_code != 200:
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
            
            # Refresh UI with a delay to avoid canvas errors
            self.after(1000, lambda: self.refresh_version_buttons())
            self.after(1000, lambda: self.select_version(version))  # Update the display and button
            
        except Exception as e:
            error_msg = f"Failed to download {version}: {str(e)}"
            self.log_to_console(error_msg, "ERROR")
            messagebox.showerror("Error", error_msg)
            self.status_text.set(f"Failed to download {version}")
            self.download_progress.set(0)

    def is_windows(self):
        """Check if running on Windows (with test mode override)"""
        # Check for test mode environment variable
        if os.environ.get("FORCE_WINDOWS_MODE", "false").lower() == "true":
            self.log_to_console("🧪 TEST MODE: Simulating Windows detection", "WARNING")
            return True
        
        is_win = sys.platform == "win32"
        self.log_to_console(f"Platform detection: {sys.platform} -> {'Windows' if is_win else 'Linux'}")
        return is_win

    def launch_game(self):
        """Launch selected Titanic version using osu-wine with custom arguments (Linux) or directly (Windows)"""
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
            
            # Check if running on Windows
            if self.is_windows():
                # Windows: Launch directly without wine
                cmd = [osu_exe]
                
                # Add launch arguments if specified
                if config['launch_args']:
                    launch_args = config['launch_args'].split()
                    cmd.extend(launch_args)
                    self.log_to_console(f"Using launch arguments: {config['launch_args']}")
                
                command_str = ' '.join(cmd)
                self.log_to_console(f"Executing on Windows: {command_str}")
                print(f"Launching on Windows with command: {command_str}")
                
                # Launch with output capture
                try:
                    process = subprocess.Popen(
                        cmd, 
                        cwd=version_path,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.STDOUT,
                        text=True,
                        bufsize=1,
                        universal_newlines=True
                    )
                    
                    # Start a thread to read output and send to console
                    def read_output():
                        try:
                            for line in iter(process.stdout.readline, ''):
                                if line:
                                    # Remove trailing whitespace and log to console
                                    clean_line = line.rstrip()
                                    if clean_line:  # Only log non-empty lines
                                        self.log_to_console(f"[GAME] {clean_line}")
                            
                            # Wait for process to complete
                            process.wait()
                            self.log_to_console(f"[GAME] Process exited with code: {process.returncode}")
                            
                        except Exception as e:
                            self.log_to_console(f"[GAME] Error reading output: {e}", "ERROR")
                    
                    # Start output reader thread
                    output_thread = threading.Thread(target=read_output, daemon=True)
                    output_thread.start()
                    
                    self.log_to_console(f"Successfully launched {display_name} on Windows (PID: {process.pid})", "SUCCESS")
                    
                except Exception as e:
                    self.log_to_console(f"Failed to start process: {e}", "ERROR")
                    raise e
            else:
                # Linux: Use osu-wine
                # Find osu-wine executable path
                osuwine_cmd = self.find_osuwine_executable()
                if not osuwine_cmd:
                    error_msg = ("osu-wine not found!\n\n"
                               "Please install osu-wine first:\n"
                               "1. Go to Options → Download osu-wine\n"
                               "2. Or install manually from https://github.com/NelloKudo/osu-winello\n\n"
                               "Note: osu-wine is only needed on Linux systems.")
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
                
                # Launch with output capture
                try:
                    process = subprocess.Popen(
                        cmd, 
                        cwd=version_path,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.STDOUT,
                        text=True,
                        bufsize=1,
                        universal_newlines=True
                    )
                    
                    # Start a thread to read output and send to console
                    def read_output():
                        try:
                            for line in iter(process.stdout.readline, ''):
                                if line:
                                    # Remove trailing whitespace and log to console
                                    clean_line = line.rstrip()
                                    if clean_line:  # Only log non-empty lines
                                        self.log_to_console(f"[GAME] {clean_line}")
                            
                            # Wait for process to complete
                            process.wait()
                            self.log_to_console(f"[GAME] Process exited with code: {process.returncode}")
                            
                        except Exception as e:
                            self.log_to_console(f"[GAME] Error reading output: {e}", "ERROR")
                    
                    # Start output reader thread
                    output_thread = threading.Thread(target=read_output, daemon=True)
                    output_thread.start()
                    
                    self.log_to_console(f"Successfully launched {display_name} (PID: {process.pid})", "SUCCESS")
                    
                except Exception as e:
                    self.log_to_console(f"Failed to start process: {e}", "ERROR")
                    raise e
            
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
        ctk.CTkLabel(main_frame, text="Available Clients", font=ctk.CTkFont(size=24, weight="bold")).pack(pady=(10, 20))
        
        # Import section
        import_frame = ctk.CTkFrame(main_frame)
        import_frame.pack(fill="x", pady=(0, 20))
        import_frame.grid_columnconfigure(1, weight=1)
        
        ctk.CTkLabel(import_frame, text="Import Client:", font=ctk.CTkFont(size=16, weight="bold")).grid(row=0, column=0, sticky="w", padx=10, pady=10)
        
        # Import buttons
        import_zip_btn = ctk.CTkButton(
            import_frame,
            text="📁 Import from Zip/.iceclient",
            fg_color="#ff6b35",
            hover_color="#e55a2b",
            command=self.import_from_zip
        )
        import_zip_btn.grid(row=0, column=1, sticky="e", padx=10, pady=10)
        
        import_folder_btn = ctk.CTkButton(
            import_frame,
            text="📂 Import from Folder",
            fg_color="#17a2b8",
            hover_color="#138496",
            command=self.import_from_folder
        )
        import_folder_btn.grid(row=0, column=2, sticky="e", padx=10, pady=10)
        
        # Scrollable frame for client list
        scrollable_frame = ctk.CTkScrollableFrame(main_frame, height=400)
        scrollable_frame.pack(fill="both", expand=True, pady=(0, 20))
        scrollable_frame.grid_columnconfigure(0, weight=1)
        scrollable_frame.grid_columnconfigure(1, weight=1)
        scrollable_frame.grid_columnconfigure(2, weight=1)
        
        # Add available clients (not installed)
        row = 0
        for version in self.versions:
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
        options_window.geometry("500x700")  # Increased height for more content
        options_window.transient(self)
        
        # Create scrollable frame for all content
        scrollable_frame = ctk.CTkScrollableFrame(options_window, width=460, height=650)
        scrollable_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Title
        ctk.CTkLabel(scrollable_frame, text="Options", font=ctk.CTkFont(size=24, weight="bold")).pack(pady=(10, 20))
        
        # Appearance section
        appearance_frame = ctk.CTkFrame(scrollable_frame)
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
        
        # Visual Customization section
        visual_frame = ctk.CTkFrame(scrollable_frame)
        visual_frame.pack(fill="x", pady=(0, 20))
        
        ctk.CTkLabel(visual_frame, text="Visual Customization", font=ctk.CTkFont(size=18, weight="bold")).pack(anchor="w", padx=10, pady=(10, 5))
        
        # Custom background image
        bg_frame = ctk.CTkFrame(visual_frame)
        bg_frame.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkLabel(bg_frame, text="Background Image:", font=ctk.CTkFont(weight="bold")).pack(side="left", padx=10)
        
        bg_btn = ctk.CTkButton(
            bg_frame,
            text="Choose Image",
            width=100,
            command=self.choose_background_image
        )
        bg_btn.pack(side="left", padx=10)
        
        bg_clear_btn = ctk.CTkButton(
            bg_frame,
            text="Clear",
            width=60,
            fg_color="#dc3545",
            hover_color="#c82333",
            command=self.clear_background_image
        )
        bg_clear_btn.pack(side="left", padx=5)
        
        # Font size
        font_frame = ctk.CTkFrame(visual_frame)
        font_frame.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkLabel(font_frame, text="Font Size:", font=ctk.CTkFont(weight="bold")).pack(side="left", padx=10)
        
        font_slider = ctk.CTkSlider(
            font_frame,
            from_=8,
            to=20,
            variable=self.custom_font_size,
            command=lambda value: self.update_font_size(int(value))
        )
        font_slider.pack(side="left", padx=10, fill="x", expand=True)
        
        font_label = ctk.CTkLabel(font_frame, textvariable=self.custom_font_size, width=30)
        font_label.pack(side="left", padx=5)
        
        # Button corner radius
        corner_frame = ctk.CTkFrame(visual_frame)
        corner_frame.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkLabel(corner_frame, text="Button Corner Radius:", font=ctk.CTkFont(weight="bold")).pack(side="left", padx=10)
        
        corner_slider = ctk.CTkSlider(
            corner_frame,
            from_=0,
            to=20,
            variable=self.button_corner_radius,
            command=lambda value: self.update_corner_radius(int(value))
        )
        corner_slider.pack(side="left", padx=10, fill="x", expand=True)
        
        corner_label = ctk.CTkLabel(corner_frame, textvariable=self.button_corner_radius, width=30)
        corner_label.pack(side="left", padx=5)
        
        # Layout Customization section
        layout_frame = ctk.CTkFrame(scrollable_frame)
        layout_frame.pack(fill="x", pady=(0, 20))
        
        ctk.CTkLabel(layout_frame, text="Layout Customization", font=ctk.CTkFont(size=18, weight="bold")).pack(anchor="w", padx=10, pady=(10, 5))
        
        # Sidebar position
        sidebar_pos_frame = ctk.CTkFrame(layout_frame)
        sidebar_pos_frame.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkLabel(sidebar_pos_frame, text="Sidebar Position:", font=ctk.CTkFont(weight="bold")).pack(side="left", padx=10)
        
        sidebar_pos_menu = ctk.CTkOptionMenu(
            sidebar_pos_frame,
            variable=self.sidebar_position,
            values=["left", "right"],
            command=lambda choice: self.update_sidebar_position(choice)
        )
        sidebar_pos_menu.pack(side="left", padx=10)
        
        # Sidebar width
        sidebar_width_frame = ctk.CTkFrame(layout_frame)
        sidebar_width_frame.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkLabel(sidebar_width_frame, text="Sidebar Width:", font=ctk.CTkFont(weight="bold")).pack(side="left", padx=10)
        
        sidebar_width_slider = ctk.CTkSlider(
            sidebar_width_frame,
            from_=200,
            to=400,
            variable=self.sidebar_width,
            command=lambda value: self.update_sidebar_width(int(value))
        )
        sidebar_width_slider.pack(side="left", padx=10, fill="x", expand=True)
        
        sidebar_width_label = ctk.CTkLabel(sidebar_width_frame, textvariable=self.sidebar_width, width=40)
        sidebar_width_label.pack(side="left", padx=5)
        
        # Window size
        window_size_frame = ctk.CTkFrame(layout_frame)
        window_size_frame.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkLabel(window_size_frame, text="Window Size:", font=ctk.CTkFont(weight="bold")).pack(anchor="w", padx=10, pady=(5, 2))
        
        size_controls = ctk.CTkFrame(window_size_frame)
        size_controls.pack(fill="x", padx=20, pady=2)
        
        ctk.CTkLabel(size_controls, text="Width:").pack(side="left", padx=5)
        width_entry = ctk.CTkEntry(size_controls, textvariable=self.custom_window_width, width=80)
        width_entry.pack(side="left", padx=5)
        
        ctk.CTkLabel(size_controls, text="Height:").pack(side="left", padx=5)
        height_entry = ctk.CTkEntry(size_controls, textvariable=self.custom_window_height, width=80)
        height_entry.pack(side="left", padx=5)
        
        apply_size_btn = ctk.CTkButton(
            size_controls,
            text="Apply",
            width=60,
            command=self.apply_window_size
        )
        apply_size_btn.pack(side="left", padx=10)
        
        # Tools section
        tools_frame = ctk.CTkFrame(scrollable_frame)
        tools_frame.pack(fill="x", pady=(0, 20))
        
        ctk.CTkLabel(tools_frame, text="Tools", font=ctk.CTkFont(size=18, weight="bold")).pack(anchor="w", padx=10, pady=(10, 5))
        
        # Login/Logout button
        auth_btn_text = "🚪 Logout" if self.auth_token else "🔑 Login"
        auth_btn = ctk.CTkButton(
            tools_frame,
            text=auth_btn_text,
            fg_color="#17a2b8",
            hover_color="#138496",
            command=self.open_login_dialog
        )
        auth_btn.pack(fill="x", padx=10, pady=5)
        
        # osu-wine download button (only show on Linux)
        if not self.is_windows():
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
        
        # Audio Fix button (only show on Linux)
        if not self.is_windows():
            audio_fix_frame = ctk.CTkFrame(tools_frame)
            audio_fix_frame.pack(fill="x", padx=10, pady=5)
            
            audio_fix_btn = ctk.CTkButton(
                audio_fix_frame,
                text="🔊 Run Audio Fix",
                fg_color="#28a745",
                hover_color="#218838",
                command=self.run_audio_fix
            )
            audio_fix_btn.pack(fill="x", pady=(0, 5))
            
            # Help message for audio fix
            audio_help_label = ctk.CTkLabel(
                audio_fix_frame,
                text="If you are having audio issues and/or cannot submit scores, try this",
                font=ctk.CTkFont(size=10),
                text_color="gray"
            )
            audio_help_label.pack(pady=(0, 5))
            
            # Run other program button (only show on Linux)
            run_program_frame = ctk.CTkFrame(tools_frame)
            run_program_frame.pack(fill="x", padx=10, pady=5)
            
            run_program_btn = ctk.CTkButton(
                run_program_frame,
                text="🚀 Run other program under wine-osu",
                fg_color="#6f42c1",
                hover_color="#5a32a3",
                command=self.run_other_program
            )
            run_program_btn.pack(fill="x", pady=(0, 5))
            
            # Help message for run other program
            run_help_label = ctk.CTkLabel(
                run_program_frame,
                text="Run .bat, .exe, or .scr files using osu-wine",
                font=ctk.CTkFont(size=10),
                text_color="gray"
            )
            run_help_label.pack(pady=(0, 5))
        
        # Help text
        help_text = ctk.CTkTextbox(scrollable_frame, height=80, font=ctk.CTkFont(size=10))
        help_text.pack(fill="x", pady=(0, 20))
        
        # Different help text for Windows vs Linux
        if self.is_windows():
            help_content = ("Theme: Switch between dark and light modes\n"
                          "Accent Color: Change the primary color theme\n"
                          "Login/Logout: Sign in or out of your Titanic account\n"
                          "Windows detected: Games will launch directly without wine")
        else:
            help_content = ("Theme: Switch between dark and light modes\n"
                          "Accent Color: Change the primary color theme\n"
                          "Login/Logout: Sign in or out of your Titanic account\n"
                          "osu-wine: Download the osu-wine launcher for running Titanic clients\n"
                          "Audio Fix: Fix audio issues and score submission problems\n"
                          "Run Program: Execute .bat, .exe, or .scr files using osu-wine")
        
        help_text.insert("0.0", help_content)
        help_text.configure(state="disabled")
        
        # Close button
        close_btn = ctk.CTkButton(scrollable_frame, text="Close", command=options_window.destroy, fg_color="#6c757d")
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

    def run_audio_fix(self):
        """Run the audio fix command using osu-wine"""
        try:
            # Check if osu-wine is available
            if not self.check_osuwine_installed():
                messagebox.showerror("osu-wine Not Found", 
                    "osu-wine is not installed or not found in PATH.\n\n"
                    "Please install osu-wine first using the 'Download osu-wine' button.")
                return
            
            # Ask for confirmation
            if not messagebox.askyesno("Run Audio Fix", 
                "This will run the following command:\n"
                "osu-wine –winetricks sound=alsa\n\n"
                "This may take a few moments to complete.\n\n"
                "Continue?"):
                return
            
            # Run the command
            self.log_to_console("Running audio fix: osu-wine –winetricks sound=alsa")
            self.status_text.set("Running audio fix...")
            
            # Run in a separate thread to avoid blocking UI
            def run_command():
                try:
                    result = subprocess.run(
                        ["osu-wine", "–winetricks", "sound=alsa"],
                        capture_output=True,
                        text=True,
                        timeout=60
                    )
                    
                    # Update UI in main thread
                    self.after(0, lambda: self._handle_audio_fix_result(result))
                    
                except subprocess.TimeoutExpired:
                    self.after(0, lambda: self._handle_audio_fix_timeout())
                except Exception as e:
                    self.after(0, lambda: self._handle_audio_fix_error(str(e)))
            
            threading.Thread(target=run_command, daemon=True).start()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to run audio fix: {str(e)}")

    def _handle_audio_fix_result(self, result):
        """Handle the result of the audio fix command"""
        if result.returncode == 0:
            self.log_to_console("Audio fix completed successfully", "SUCCESS")
            self.status_text.set("Audio fix completed successfully")
            messagebox.showinfo("Success", 
                "Audio fix completed successfully!\n\n"
                "Try launching the game again to see if the audio issues are resolved.")
        else:
            self.log_to_console(f"Audio fix failed: {result.stderr}", "ERROR")
            self.status_text.set("Audio fix failed")
            messagebox.showerror("Audio Fix Failed", 
                f"The audio fix command failed.\n\n"
                f"Error: {result.stderr}\n\n"
                f"Please check the console output for more details.")

    def _handle_audio_fix_timeout(self):
        """Handle timeout of the audio fix command"""
        self.log_to_console("Audio fix timed out", "ERROR")
        self.status_text.set("Audio fix timed out")
        messagebox.showerror("Timeout", 
            "The audio fix command timed out after 60 seconds.\n\n"
            "Please try running it manually in the terminal:\n"
            "osu-wine –winetricks sound=alsa")

    def _handle_audio_fix_error(self, error_msg):
        """Handle error in the audio fix command"""
        self.log_to_console(f"Audio fix error: {error_msg}", "ERROR")
        self.status_text.set("Audio fix error")
        messagebox.showerror("Error", 
            f"An error occurred while running the audio fix:\n\n"
            f"{error_msg}")

    def run_other_program(self):
        """Run a selected program using osu-wine"""
        try:
            # Check if osu-wine is available
            if not self.check_osuwine_installed():
                messagebox.showerror("osu-wine Not Found", 
                    "osu-wine is not installed or not found in PATH.\n\n"
                    "Please install osu-wine first using the 'Download osu-wine' button.")
                return
            
            # Ask user to select a file
            file_path = filedialog.askopenfilename(
                title="Select Program to Run",
                filetypes=[
                    ("Executable files", "*.exe *.bat *.scr"),
                    ("Windows Executable", "*.exe"),
                    ("Batch Files", "*.bat"),
                    ("Screen Savers", "*.scr"),
                    ("All files", "*.*")
                ]
            )
            
            if not file_path:
                return
            
            # Ask for confirmation
            filename = os.path.basename(file_path)
            if not messagebox.askyesno("Run Program", 
                f"This will run the following program using osu-wine:\n\n"
                f"{filename}\n\n"
                f"Full path: {file_path}\n\n"
                "Continue?"):
                return
            
            # Run the program
            self.log_to_console(f"Running program with osu-wine: {file_path}")
            self.status_text.set(f"Running {filename}...")
            
            # Run in a separate thread to avoid blocking UI
            def run_command():
                try:
                    result = subprocess.run(
                        ["osu-wine", "--wine", file_path],
                        capture_output=True,
                        text=True,
                        timeout=300  # 5 minute timeout
                    )
                    
                    # Update UI in main thread
                    self.after(0, lambda: self._handle_program_result(result, filename))
                    
                except subprocess.TimeoutExpired:
                    self.after(0, lambda: self._handle_program_timeout(filename))
                except Exception as e:
                    self.after(0, lambda: self._handle_program_error(str(e), filename))
            
            threading.Thread(target=run_command, daemon=True).start()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to run program: {str(e)}")

    def _handle_program_result(self, result, filename):
        """Handle the result of running a program"""
        if result.returncode == 0:
            self.log_to_console(f"Program '{filename}' completed successfully", "SUCCESS")
            self.status_text.set(f"Program completed successfully")
            messagebox.showinfo("Success", 
                f"Program '{filename}' completed successfully!")
        else:
            self.log_to_console(f"Program '{filename}' failed: {result.stderr}", "ERROR")
            self.status_text.set("Program failed")
            messagebox.showerror("Program Failed", 
                f"The program '{filename}' failed to run.\n\n"
                f"Error: {result.stderr}\n\n"
                f"Please check the console output for more details.")

    def _handle_program_timeout(self, filename):
        """Handle timeout of the program"""
        self.log_to_console(f"Program '{filename}' timed out", "ERROR")
        self.status_text.set("Program timed out")
        messagebox.showerror("Timeout", 
            f"The program '{filename}' timed out after 5 minutes.\n\n"
            f"The program may still be running in the background.")

    def _handle_program_error(self, error_msg, filename):
        """Handle error in running the program"""
        self.log_to_console(f"Program '{filename}' error: {error_msg}", "ERROR")
        self.status_text.set("Program error")
        messagebox.showerror("Error", 
            f"An error occurred while running the program:\n\n"
            f"{error_msg}")

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
        if hasattr(self, 'osuwine_btn') and self.osuwine_btn:
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
        """Load authentication configuration and refresh user stats"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                    
                if 'auth' in config:
                    self.auth_token = config['auth'].get('token')
                    self.user_data = config['auth'].get('user_data', {})
                    
                    # Update display with cached data first
                    self.update_user_display()
                    
                    # Refresh user data from API in background
                    if self.auth_token:
                        print("Refreshing user stats on startup...")
                        self.log_to_console("Refreshing user stats...", "INFO")
                        
                        # Start refresh in background thread to avoid blocking UI
                        thread = threading.Thread(target=self._refresh_user_data_thread)
                        thread.daemon = True
                        thread.start()
        except Exception as e:
            print(f"Failed to load auth config: {e}")
            self.log_to_console(f"Failed to load auth config: {e}", "ERROR")

    def _refresh_user_data_thread(self):
        """Refresh user data in background thread"""
        try:
            # Fetch fresh data from API
            self.fetch_user_data()
            
            # Update UI in main thread
            self.after(0, lambda: self.update_user_display())
            self.after(0, lambda: self.save_options_config())
            
            if self.user_data.get('username'):
                self.log_to_console(f"User stats refreshed for {self.user_data['username']}", "SUCCESS")
            else:
                self.log_to_console("User stats refresh completed", "SUCCESS")
                
        except Exception as e:
            self.log_to_console(f"Failed to refresh user stats: {e}", "ERROR")
            print(f"Failed to refresh user data: {e}")

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
            
            # Use the correct avatar URL pattern
            avatar_url = f"https://osu.titanic.sh/a/{user_id}"
            
            # Directly try to load the avatar image
            print(f"Attempting to load avatar from: {avatar_url}")
            self.load_avatar_image(avatar_url)
            
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
        
        # Check if this is a game message
        is_game_message = message.startswith("[GAME]")
        
        # Color coding for different levels
        if level == "ERROR":
            prefix = f"[{timestamp}] [ERROR] "
        elif level == "WARNING":
            prefix = f"[{timestamp}] [WARN]  "
        elif level == "SUCCESS":
            prefix = f"[{timestamp}] [SUCCESS] "
        elif is_game_message:
            prefix = f"[{timestamp}] [GAME]  "
        else:
            prefix = f"[{timestamp}] [INFO]  "
        
        full_message = f"{prefix}{message}\n"
        
        # Update console in main thread
        self.after(0, lambda: self._update_console(full_message, is_game_message))

    def _update_console(self, message, is_game_message=False):
        """Update console text widget (must be called from main thread)"""
        try:
            self.console_text.configure(state="normal")
            
            # For game messages, we'll just insert them normally since CTkTextbox doesn't support tags
            # The [GAME] prefix will help distinguish them
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

    def import_from_zip(self):
        """Import a client from a zip or .iceclient file"""
        # Ask user to select a file
        file_path = filedialog.askopenfilename(
            title="Select Client File",
            filetypes=[
                ("Client files", "*.zip *.iceclient"),
                ("Zip files", "*.zip"),
                ("IceClient files", "*.iceclient"),
                ("All files", "*.*")
            ]
        )
        
        if not file_path:
            return
        
        # Ask for version name
        version_name = ctk.CTkInputDialog(
            text="Enter a name for this client version:",
            title="Import Client"
        ).get_input()
        
        if not version_name:
            return
        
        # Sanitize version name
        version_name = "".join(c for c in version_name if c.isalnum() or c in "._-")
        if not version_name:
            messagebox.showerror("Error", "Invalid version name")
            return
        
        # Start import in background thread
        threading.Thread(
            target=self._import_zip_thread,
            args=(file_path, version_name),
            daemon=True
        ).start()

    def import_from_folder(self):
        """Import a client from a folder"""
        # Ask user to select a folder
        folder_path = filedialog.askdirectory(title="Select Client Folder")
        
        if not folder_path:
            return
        
        # Check if folder contains osu!.exe
        osu_exe_path = os.path.join(folder_path, "osu!.exe")
        if not os.path.exists(osu_exe_path):
            messagebox.showerror("Error", "Selected folder does not contain osu!.exe")
            return
        
        # Ask for version name
        version_name = ctk.CTkInputDialog(
            text="Enter a name for this client version:",
            title="Import Client"
        ).get_input()
        
        if not version_name:
            return
        
        # Sanitize version name
        version_name = "".join(c for c in version_name if c.isalnum() or c in "._-")
        if not version_name:
            messagebox.showerror("Error", "Invalid version name")
            return
        
        # Start import in background thread
        threading.Thread(
            target=self._import_folder_thread,
            args=(folder_path, version_name),
            daemon=True
        ).start()

    def _import_zip_thread(self, file_path, version_name):
        """Import client from zip file in background thread"""
        try:
            self.log_to_console(f"Importing client from {file_path}...")
            self.status_text.set("Importing client...")
            
            # Create destination directory
            dest_path = os.path.join(self.versions_dir, version_name)
            if os.path.exists(dest_path):
                self.after(0, lambda: messagebox.showerror("Error", f"Version {version_name} already exists"))
                return
            
            os.makedirs(dest_path, exist_ok=True)
            
            # Extract zip file
            with zipfile.ZipFile(file_path, 'r') as zip_ref:
                zip_ref.extractall(dest_path)
            
            # Check if osu!.exe exists in extracted files
            osu_exe_path = os.path.join(dest_path, "osu!.exe")
            if not os.path.exists(osu_exe_path):
                # Look for osu!.exe in subdirectories
                found = False
                for root, dirs, files in os.walk(dest_path):
                    if "osu!.exe" in files:
                        # Move everything from this subdirectory to dest_path
                        sub_dir = root
                        for item in os.listdir(sub_dir):
                            s = os.path.join(sub_dir, item)
                            d = os.path.join(dest_path, item)
                            if os.path.isfile(s):
                                shutil.move(s, d)
                            else:
                                if not os.path.exists(d):
                                    shutil.move(s, d)
                        found = True
                        break
                
                if not found:
                    self.after(0, lambda: messagebox.showerror("Error", "Imported file does not contain osu!.exe"))
                    shutil.rmtree(dest_path)
                    return
            
            # Add to versions list if not already there
            if version_name not in self.versions:
                self.versions.append(version_name)
            
            # Save imported versions to config
            imported_versions = self.version_configs.get('_imported_versions', [])
            if version_name not in imported_versions:
                imported_versions.append(version_name)
                self.version_configs['_imported_versions'] = imported_versions
                self.save_config()
            
            # Refresh UI
            self.after(0, self.refresh_version_buttons)
            self.after(0, lambda: self.status_text.set(f"Successfully imported {version_name}"))
            self.log_to_console(f"Successfully imported {version_name}", "SUCCESS")
            
        except Exception as e:
            self.after(0, lambda: messagebox.showerror("Import Error", f"Failed to import client: {str(e)}"))
            self.after(0, lambda: self.status_text.set("Import failed"))
            self.log_to_console(f"Import failed: {str(e)}", "ERROR")

    def _import_folder_thread(self, folder_path, version_name):
        """Import client from folder in background thread"""
        try:
            self.log_to_console(f"Importing client from {folder_path}...")
            self.status_text.set("Importing client...")
            
            # Create destination directory
            dest_path = os.path.join(self.versions_dir, version_name)
            if os.path.exists(dest_path):
                self.after(0, lambda: messagebox.showerror("Error", f"Version {version_name} already exists"))
                return
            
            # Copy folder contents
            shutil.copytree(folder_path, dest_path)
            
            # Add to versions list if not already there
            if version_name not in self.versions:
                self.versions.append(version_name)
            
            # Save imported versions to config
            imported_versions = self.version_configs.get('_imported_versions', [])
            if version_name not in imported_versions:
                imported_versions.append(version_name)
                self.version_configs['_imported_versions'] = imported_versions
                self.save_config()
            
            # Refresh UI
            self.after(0, self.refresh_version_buttons)
            self.after(0, lambda: self.status_text.set(f"Successfully imported {version_name}"))
            self.log_to_console(f"Successfully imported {version_name}", "SUCCESS")
            
        except Exception as e:
            self.after(0, lambda: messagebox.showerror("Import Error", f"Failed to import client: {str(e)}"))
            self.after(0, lambda: self.status_text.set("Import failed"))
            self.log_to_console(f"Import failed: {str(e)}", "ERROR")

    # === CUSTOMIZATION FUNCTIONS ===
    
    def choose_background_image(self):
        """Choose a custom background image"""
        from tkinter import filedialog
        file_path = filedialog.askopenfilename(
            title="Choose Background Image",
            filetypes=[
                ("Image files", "*.png *.jpg *.jpeg *.gif *.bmp"),
                ("PNG files", "*.png"),
                ("JPEG files", "*.jpg *.jpeg"),
                ("All files", "*.*")
            ]
        )
        
        if file_path:
            self.custom_bg_image.set(file_path)
            self.apply_background_image()
            self.save_customization_config()
    
    def clear_background_image(self):
        """Clear the custom background image"""
        self.custom_bg_image.set("")
        self.apply_background_image()
        self.save_customization_config()
    
    def apply_background_image(self):
        """Apply the custom background image using a background label"""
        try:
            if self.custom_bg_image.get():
                from PIL import Image
                
                # Load and set background image
                bg_image = Image.open(self.custom_bg_image.get())
                
                # Target the main scrollable frame
                if hasattr(self, 'main_scrollable'):
                    # Get scrollable frame size
                    scroll_width = 750  # Default size
                    scroll_height = 550  # Default size
                    
                    # Try to get actual size if available
                    try:
                        scroll_width = self.main_scrollable.winfo_width()
                        scroll_height = self.main_scrollable.winfo_height()
                        if scroll_width <= 1:
                            scroll_width = 750
                        if scroll_height <= 1:
                            scroll_height = 550
                    except:
                        pass
                    
                    bg_image = bg_image.resize((scroll_width, scroll_height), Image.Resampling.LANCZOS)
                    ctk_bg_image = ctk.CTkImage(light_image=bg_image, dark_image=bg_image, size=(scroll_width, scroll_height))
                    
                    # Remove old background label if exists
                    if hasattr(self, 'bg_label'):
                        self.bg_label.destroy()
                    
                    # Create a background label inside the scrollable frame
                    self.bg_label = ctk.CTkLabel(self.main_scrollable, image=ctk_bg_image, text="")
                    self.bg_label.place(x=0, y=0, relwidth=1, relheight=1)
                    self.bg_label.lower()  # Send to back
                    
                    # Make all section frames transparent so background shows through
                    for widget in self.main_scrollable.winfo_children():
                        if isinstance(widget, ctk.CTkFrame):
                            widget.configure(fg_color="transparent")
                    
                    self.log_to_console(f"Background image applied with transparent sections ({scroll_width}x{scroll_height})", "SUCCESS")
                else:
                    self.log_to_console("Main scrollable frame not found for background image", "ERROR")
                
            else:
                # Remove background image
                if hasattr(self, 'bg_label'):
                    self.bg_label.destroy()
                    delattr(self, 'bg_label')
                    
                    # Restore section frame backgrounds
                    if hasattr(self, 'main_scrollable'):
                        for widget in self.main_scrollable.winfo_children():
                            if isinstance(widget, ctk.CTkFrame):
                                widget.configure(fg_color=("gray95", "gray15"))
                    
                    self.log_to_console("Background image cleared and backgrounds restored", "SUCCESS")
                    
        except Exception as e:
            self.log_to_console(f"Failed to apply background image: {e}", "ERROR")
    
    def on_window_resize(self, event):
        """Handle window resize events to update background image"""
        # Only update if we have a background image and this is a resize event
        if self.custom_bg_image.get():
            # Debounce rapid resize events
            if hasattr(self, '_resize_timer'):
                self.after_cancel(self._resize_timer)
            
            self._resize_timer = self.after(100, self.update_background_size)
    
    def update_background_size(self):
        """Update background image size when window is resized"""
        try:
            if self.custom_bg_image.get() and hasattr(self, 'bg_label') and hasattr(self, 'main_scrollable'):
                from PIL import Image
                
                # Reload and resize image to scrollable frame size
                bg_image = Image.open(self.custom_bg_image.get())
                scroll_width = self.main_scrollable.winfo_width()
                scroll_height = self.main_scrollable.winfo_height()
                
                if scroll_width > 1 and scroll_height > 1:
                    bg_image = bg_image.resize((scroll_width, scroll_height), Image.Resampling.LANCZOS)
                    ctk_bg_image = ctk.CTkImage(light_image=bg_image, dark_image=bg_image, size=(scroll_width, scroll_height))
                    
                    # Destroy old label and create new one
                    if hasattr(self, 'bg_label'):
                        self.bg_label.destroy()
                    
                    self.bg_label = ctk.CTkLabel(self.main_scrollable, image=ctk_bg_image, text="")
                    self.bg_label.place(x=0, y=0, relwidth=1, relheight=1)
                    self.bg_label.lower()
                    
                    # Keep sections transparent
                    for widget in self.main_scrollable.winfo_children():
                        if isinstance(widget, ctk.CTkFrame):
                            widget.configure(fg_color="transparent")
        except Exception as e:
            pass  # Silently fail on resize to avoid spamming errors
    
    def update_font_size(self, size):
        """Update font size throughout the application"""
        try:
            # Create new font with specified size
            new_font = ctk.CTkFont(size=size)
            
            # Update main title in sidebar
            if hasattr(self, 'sidebar_frame'):
                for widget in self.sidebar_frame.winfo_children():
                    if isinstance(widget, ctk.CTkLabel):
                        widget.configure(font=new_font)
            
            # Update section headers by finding them directly
            section_headers = {
                'Version Information': 'details',
                'Version Settings': 'settings', 
                'Console Output': 'console'
            }
            
            # Search through all widgets to find section headers
            for widget in self.main_scrollable.winfo_children():
                if isinstance(widget, ctk.CTkFrame):
                    for child in widget.winfo_children():
                        if isinstance(child, ctk.CTkLabel):
                            text = child.cget("text")
                            if any(header in text for header in section_headers.keys()):
                                child.configure(font=ctk.CTkFont(size=size, weight="bold"))
            
            # Update description text if exists
            if hasattr(self, 'description_text'):
                self.description_text.configure(font=ctk.CTkFont(size=size))
            
            # Update console text if exists
            if hasattr(self, 'console_text'):
                self.console_text.configure(font=ctk.CTkFont(family="Courier", size=size))
            
            self.save_customization_config()
            self.log_to_console(f"Font size updated to {size}", "SUCCESS")
            
        except Exception as e:
            self.log_to_console(f"Failed to update font size: {e}", "ERROR")
    
    def update_corner_radius(self, radius):
        """Update button corner radius"""
        try:
            # List of specific buttons to update
            buttons_to_update = [
                'launch_btn', 'download_btn', 'options_btn', 'folder_btn',
                'details_toggle_btn', 'settings_toggle_btn', 'console_toggle_btn',
                'clear_console_btn', 'save_settings_btn'
            ]
            
            # Update specific buttons
            for button_name in buttons_to_update:
                if hasattr(self, button_name):
                    try:
                        button = getattr(self, button_name)
                        button.configure(corner_radius=radius)
                    except:
                        pass
            
            # Update version buttons in sidebar
            if hasattr(self, 'version_buttons'):
                for version_name, button_frame in self.version_buttons.items():
                    for child in button_frame.winfo_children():
                        if isinstance(child, ctk.CTkButton):
                            child.configure(corner_radius=radius)
            
            self.save_customization_config()
            self.log_to_console(f"Button corner radius updated to {radius}", "SUCCESS")
            
        except Exception as e:
            self.log_to_console(f"Failed to update corner radius: {e}", "ERROR")
    
    def apply_corner_radius_recursive(self, widget, radius):
        """Recursively apply corner radius to all CTkButton widgets"""
        if hasattr(widget, 'configure'):
            try:
                config = widget.configure()
                if config and 'corner_radius' in config:
                    widget.configure(corner_radius=radius)
            except:
                pass  # Some widgets might not support corner_radius
        
        for child in widget.winfo_children():
            self.apply_corner_radius_recursive(child, radius)
    
    def update_sidebar_position(self, position):
        """Update sidebar position (left/right)"""
        try:
            if position == "right":
                # Move sidebar to right
                self.sidebar_frame.grid_forget()
                self.sidebar_frame.grid(row=0, column=1, sticky="nsew")
                # Move main content to left
                self.main_frame.grid_forget()
                self.main_frame.grid(row=0, column=0, sticky="nsew")
                # Adjust column weights - main content gets most space
                self.grid_columnconfigure(0, weight=1)  # Main content
                self.grid_columnconfigure(1, weight=0)   # Sidebar (fixed width)
                self.log_to_console("Sidebar moved to right", "SUCCESS")
            else:
                # Move sidebar to left (default)
                self.sidebar_frame.grid_forget()
                self.sidebar_frame.grid(row=0, column=0, sticky="nsew")
                # Move main content to right
                self.main_frame.grid_forget()
                self.main_frame.grid(row=0, column=1, sticky="nsew")
                # Adjust column weights - main content gets most space
                self.grid_columnconfigure(0, weight=0)   # Sidebar (fixed width)
                self.grid_columnconfigure(1, weight=1)  # Main content
                self.log_to_console("Sidebar moved to left", "SUCCESS")
            
            self.save_customization_config()
            
        except Exception as e:
            self.log_to_console(f"Failed to update sidebar position: {e}", "ERROR")
            messagebox.showerror("Error", f"Failed to update sidebar position: {e}")
    
    def update_sidebar_width(self, width):
        """Update sidebar width"""
        try:
            self.sidebar_frame.configure(width=width)
            # Force grid update to take effect
            self.sidebar_frame.grid_columnconfigure(0, minsize=width)
            self.save_customization_config()
        except Exception as e:
            self.log_to_console(f"Failed to update sidebar width: {e}", "ERROR")
    
    def update_section_visibility(self):
        """Update visibility of main sections"""
        try:
            # Update details section
            if hasattr(self, 'details_frame'):
                if not self.show_details_section.get():
                    self.details_frame.pack_forget()
                else:
                    # Make sure it's in the correct order
                    self.details_frame.pack(fill="both", expand=True, padx=20, pady=10, before=self.settings_frame if hasattr(self, 'settings_frame') else None)
            
            # Update settings section
            if hasattr(self, 'settings_frame'):
                if not self.show_settings_section.get():
                    self.settings_frame.pack_forget()
                else:
                    self.settings_frame.pack(fill="x", padx=20, pady=(0, 20), before=self.console_frame if hasattr(self, 'console_frame') else None)
            
            # Update console section
            if hasattr(self, 'console_frame'):
                if not self.show_console_section.get():
                    self.console_frame.pack_forget()
                else:
                    self.console_frame.pack(fill="x", padx=20, pady=(0, 20))
            
            # Save the settings immediately
            self.save_customization_config()
            self.log_to_console("Section visibility updated and saved", "SUCCESS")
            
        except Exception as e:
            self.log_to_console(f"Failed to update section visibility: {e}", "ERROR")
    
    def apply_window_size(self):
        """Apply custom window size"""
        try:
            width = self.custom_window_width.get()
            height = self.custom_window_height.get()
            
            # Validate dimensions
            if width < 400 or height < 300:
                messagebox.showerror("Error", "Window size too small. Minimum: 400x300")
                return
            
            if width > 2000 or height > 1500:
                messagebox.showerror("Error", "Window size too large. Maximum: 2000x1500")
                return
            
            # Apply new size
            self.geometry(f"{width}x{height}")
            self.save_customization_config()
            self.log_to_console(f"Window size set to {width}x{height}", "SUCCESS")
            
        except Exception as e:
            self.log_to_console(f"Failed to set window size: {e}", "ERROR")
            messagebox.showerror("Error", f"Failed to set window size: {e}")
    
    def save_customization_config(self):
        """Save customization settings to config"""
        customization = {
            'custom_bg_image': self.custom_bg_image.get(),
            'custom_font_size': self.custom_font_size.get(),
            'button_corner_radius': self.button_corner_radius.get(),
            'sidebar_width': self.sidebar_width.get(),
            'sidebar_position': self.sidebar_position.get(),
            'custom_window_width': self.custom_window_width.get(),
            'custom_window_height': self.custom_window_height.get()
        }
        self.version_configs['_customization'] = customization
        self.save_config()
    
    def load_customization_config(self):
        """Load customization settings from config"""
        customization = self.version_configs.get('_customization', {})
        
        if customization:
            self.custom_bg_image.set(customization.get('custom_bg_image', ''))
            self.custom_font_size.set(customization.get('custom_font_size', 12))
            self.button_corner_radius.set(customization.get('button_corner_radius', 8))
            self.sidebar_width.set(customization.get('sidebar_width', 250))
            self.sidebar_position.set(customization.get('sidebar_position', 'left'))
            self.custom_window_width.set(customization.get('custom_window_width', 1000))
            self.custom_window_height.set(customization.get('custom_window_height', 700))
            
            # Apply loaded settings after UI is fully ready
            self.after(100, self.apply_loaded_customizations)
    
    def apply_loaded_customizations(self):
        """Apply customization settings after UI is ready"""
        try:
            # Apply background image
            self.apply_background_image()
            
            # Apply corner radius
            self.update_corner_radius(self.button_corner_radius.get())
            
            # Apply sidebar width
            self.update_sidebar_width(self.sidebar_width.get())
            
            # Apply window size
            self.geometry(f"{self.custom_window_width.get()}x{self.custom_window_height.get()}")
            
            # Apply font size
            self.update_font_size(self.custom_font_size.get())
            
            # Apply sidebar position
            self.update_sidebar_position(self.sidebar_position.get())
            
        except Exception as e:
            self.log_to_console(f"Failed to apply loaded customizations: {e}", "ERROR")

def main():
    app = TitanicLauncher()
    app.mainloop()

if __name__ == "__main__":
    main()
