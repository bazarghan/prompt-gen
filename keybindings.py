# keybindings.py

import curses
import json
import os
import platform  # To detect OS

# --- Configuration File Path Logic ---
APP_NAME = "prompt-gen"


def get_config_dir():
    """Gets the platform-specific configuration directory for the application."""
    if platform.system() == "Windows":
        # APPDATA is typically C:\Users\<user>\AppData\Roaming
        app_data_dir = os.getenv("APPDATA")
        if app_data_dir:
            return os.path.join(app_data_dir, APP_NAME)
        else:
            # Fallback if APPDATA is not set (less common)
            return os.path.join(os.path.expanduser("~"), f".{APP_NAME}")
    elif platform.system() == "Darwin":  # macOS
        return os.path.join(
            os.path.expanduser("~"), "Library", "Application Support", APP_NAME
        )
    else:  # Linux and other Unix-like
        # Follow XDG Base Directory Specification if XDG_CONFIG_HOME is set
        xdg_config_home = os.getenv("XDG_CONFIG_HOME")
        if xdg_config_home:
            return os.path.join(xdg_config_home, APP_NAME)
        else:
            # Default to ~/.config/
            return os.path.join(os.path.expanduser("~"), ".config", APP_NAME)


CONFIG_DIR = get_config_dir()
DEFAULT_KEYBIND_FILE_NAME = "keybinds.json"
KEYBIND_FILE_PATH = os.path.join(CONFIG_DIR, DEFAULT_KEYBIND_FILE_NAME)
# --- End Configuration File Path Logic ---


# Define actions as constants for internal use
ACTION_QUIT = "QUIT"
ACTION_NAVIGATE_UP = "NAVIGATE_UP"
ACTION_NAVIGATE_DOWN = "NAVIGATE_DOWN"
ACTION_ENTER_DIRECTORY = "ENTER_DIRECTORY"
ACTION_PARENT_DIRECTORY = "PARENT_DIRECTORY"
ACTION_TOGGLE_SELECT = "TOGGLE_SELECT"
ACTION_GENERATE_OUTPUT = "GENERATE_OUTPUT"

DEFAULT_KEYBINDS_CONFIG = {
    ACTION_QUIT: ["q"],
    ACTION_NAVIGATE_UP: ["KEY_UP", "k"],
    ACTION_NAVIGATE_DOWN: ["KEY_DOWN", "j"],
    ACTION_ENTER_DIRECTORY: ["KEY_ENTER", "\n", "l"],
    ACTION_PARENT_DIRECTORY: ["h"],
    ACTION_TOGGLE_SELECT: [" "],
    ACTION_GENERATE_OUTPUT: ["g"],
}

CURSES_KEY_MAP = {
    "KEY_UP": curses.KEY_UP,
    "KEY_DOWN": curses.KEY_DOWN,
    "KEY_LEFT": curses.KEY_LEFT,
    "KEY_RIGHT": curses.KEY_RIGHT,
    "KEY_ENTER": curses.KEY_ENTER,
}

KEY_ACTIONS = {}
ALT_KEY_ACTIONS = {}
LOADED_CONFIG_FOR_DISPLAY = {}


def _populate_key_maps(config_to_use):
    KEY_ACTIONS.clear()
    ALT_KEY_ACTIONS.clear()
    LOADED_CONFIG_FOR_DISPLAY.clear()

    for action, keys_list in config_to_use.items():
        if action not in DEFAULT_KEYBINDS_CONFIG:
            print(
                f"Warning: Unknown action '{action}' in loaded keybindings. Ignoring."
            )
            continue

        LOADED_CONFIG_FOR_DISPLAY[action] = keys_list

        for key_specifier in keys_list:
            if not isinstance(key_specifier, str):
                print(
                    f"Warning: Invalid key specifier type '{type(key_specifier)}' for action '{action}'. Must be a string. Ignoring."
                )
                continue

            key_spec_upper = key_specifier.upper()
            if key_spec_upper.startswith("ALT+"):
                if len(key_specifier) > 4:
                    char_after_alt = key_specifier[4:]
                    ALT_KEY_ACTIONS[ord(char_after_alt)] = action
                else:
                    print(
                        f"Warning: Invalid ALT key specifier '{key_specifier}' for action '{action}'. Needs a character after 'ALT+'. Ignoring."
                    )
            elif key_spec_upper in CURSES_KEY_MAP:
                KEY_ACTIONS[CURSES_KEY_MAP[key_spec_upper]] = action
            elif len(key_specifier) == 1:
                KEY_ACTIONS[ord(key_specifier)] = action
            else:
                print(
                    f"Warning: Unknown or invalid key specifier '{key_specifier}' for action '{action}'. Ignoring."
                )


def load_keybindings():  # Removed filepath argument, now uses global KEYBIND_FILE_PATH
    """Loads keybindings from the user's config directory or uses defaults."""
    config_source = DEFAULT_KEYBINDS_CONFIG.copy()
    created_default_file = False
    filepath_to_load = KEYBIND_FILE_PATH  # Use the determined config path

    if os.path.exists(filepath_to_load):
        try:
            with open(filepath_to_load, "r", encoding="utf-8") as f:
                loaded_config = json.load(f)

            if not isinstance(loaded_config, dict):
                print(
                    f"Warning: '{filepath_to_load}' does not contain a valid dictionary. Using default keybindings."
                )
            else:
                merged_config = DEFAULT_KEYBINDS_CONFIG.copy()
                for action, keys in loaded_config.items():
                    if action in merged_config:
                        if isinstance(keys, list):
                            merged_config[action] = keys
                        else:
                            print(
                                f"Warning: Value for action '{action}' in '{filepath_to_load}' is not a list. Using default for this action."
                            )
                    else:
                        print(
                            f"Warning: Unknown action '{action}' in '{filepath_to_load}'. Ignoring."
                        )
                config_source = merged_config
                print(f"Loaded keybindings from '{filepath_to_load}'.")

        except json.JSONDecodeError:
            print(
                f"Error: Could not decode JSON from '{filepath_to_load}'. Using default keybindings."
            )
        except Exception as e:
            print(
                f"Error loading '{filepath_to_load}': {e}. Using default keybindings."
            )
    else:
        print(
            f"Keybinding file '{filepath_to_load}' not found. Using default keybindings and creating a default file."
        )
        try:
            # Ensure the configuration directory exists
            os.makedirs(CONFIG_DIR, exist_ok=True)
            with open(filepath_to_load, "w", encoding="utf-8") as f:
                json.dump(DEFAULT_KEYBINDS_CONFIG, f, indent=2, sort_keys=True)
            print(
                f"A default keybinding file has been created at '{filepath_to_load}'."
            )
            created_default_file = True
        except Exception as e:
            print(
                f"Could not create default keybinding file at '{filepath_to_load}': {e}"
            )

    _populate_key_maps(config_source)
    if created_default_file:
        print(
            f"Please review the generated '{filepath_to_load}' and restart the application if you made changes while it was running."
        )

    return KEY_ACTIONS, ALT_KEY_ACTIONS, LOADED_CONFIG_FOR_DISPLAY


def get_display_for_action(action_name):
    if not LOADED_CONFIG_FOR_DISPLAY or action_name not in LOADED_CONFIG_FOR_DISPLAY:
        return []

    display_keys = []
    for key_spec in LOADED_CONFIG_FOR_DISPLAY[action_name]:
        if key_spec.upper().startswith("ALT+"):
            char_after_alt = key_spec[4:]
            display_keys.append(f"Alt+{char_after_alt}")
        elif key_spec == " ":
            display_keys.append("Space")
        elif key_spec.upper() in CURSES_KEY_MAP:
            display_keys.append(key_spec.replace("KEY_", "").capitalize())
        elif key_spec == "\n":
            display_keys.append("Enter")
        else:
            display_keys.append(key_spec)
    return display_keys
