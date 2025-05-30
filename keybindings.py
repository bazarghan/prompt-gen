# keybindings.py

import curses
import json
import os

DEFAULT_KEYBIND_FILE = "keybinds.json"

# Define actions as constants for internal use
ACTION_QUIT = "QUIT"
ACTION_NAVIGATE_UP = "NAVIGATE_UP"
ACTION_NAVIGATE_DOWN = "NAVIGATE_DOWN"
ACTION_ENTER_DIRECTORY = "ENTER_DIRECTORY"
ACTION_PARENT_DIRECTORY = "PARENT_DIRECTORY"
ACTION_TOGGLE_SELECT = "TOGGLE_SELECT"
ACTION_GENERATE_OUTPUT = "GENERATE_OUTPUT"

# Default keybindings if keybinds.json is missing or invalid
DEFAULT_KEYBINDS_CONFIG = {
    ACTION_QUIT: ["q"],
    ACTION_NAVIGATE_UP: ["KEY_UP", "k"],
    ACTION_NAVIGATE_DOWN: ["KEY_DOWN", "j"],
    ACTION_ENTER_DIRECTORY: ["KEY_ENTER", "\n", "l"],
    ACTION_PARENT_DIRECTORY: ["h"],  # Handle k and K after Alt
    ACTION_TOGGLE_SELECT: [" "],
    ACTION_GENERATE_OUTPUT: ["g"],
}

# Map special key strings from JSON to actual curses constants
CURSES_KEY_MAP = {
    "KEY_UP": curses.KEY_UP,
    "KEY_DOWN": curses.KEY_DOWN,
    "KEY_LEFT": curses.KEY_LEFT,  # Add if you plan to use it
    "KEY_RIGHT": curses.KEY_RIGHT,
    "KEY_ENTER": curses.KEY_ENTER,
    # Add other curses.KEY_ constants if needed, e.g. curses.KEY_BACKSPACE
}

# These dictionaries will be populated by load_keybindings()
# and used by tui.py
KEY_ACTIONS = {}  # Maps direct key_code -> ACTION_CONSTANT
ALT_KEY_ACTIONS = {}  # Maps char_code_after_alt -> ACTION_CONSTANT
LOADED_CONFIG_FOR_DISPLAY = {}  # Stores the raw loaded strings for display purposes


def _populate_key_maps(config_to_use):
    """Helper function to process the configuration into usable key maps."""
    KEY_ACTIONS.clear()
    ALT_KEY_ACTIONS.clear()
    LOADED_CONFIG_FOR_DISPLAY.clear()  # Clear and repopulate for display

    for action, keys_list in config_to_use.items():
        if action not in DEFAULT_KEYBINDS_CONFIG:  # Ensure action is known
            print(
                f"Warning: Unknown action '{action}' in loaded keybindings. Ignoring."
            )
            continue

        LOADED_CONFIG_FOR_DISPLAY[action] = keys_list  # Store for display

        for key_specifier in keys_list:
            if not isinstance(key_specifier, str):
                print(
                    f"Warning: Invalid key specifier type '{type(key_specifier)}' for action '{action}'. Must be a string. Ignoring."
                )
                continue

            key_spec_upper = key_specifier.upper()
            if key_spec_upper.startswith("ALT+"):
                if len(key_specifier) > 4:  # Must have a character after "ALT+"
                    char_after_alt = key_specifier[
                        4:
                    ]  # Get the actual character (case-sensitive)
                    ALT_KEY_ACTIONS[ord(char_after_alt)] = action
                else:
                    print(
                        f"Warning: Invalid ALT key specifier '{key_specifier}' for action '{action}'. Needs a character after 'ALT+'. Ignoring."
                    )
            elif key_spec_upper in CURSES_KEY_MAP:
                KEY_ACTIONS[CURSES_KEY_MAP[key_spec_upper]] = action
            elif len(key_specifier) == 1:  # Regular character key (like 'q', ' ', '\n')
                KEY_ACTIONS[ord(key_specifier)] = action
            else:
                print(
                    f"Warning: Unknown or invalid key specifier '{key_specifier}' for action '{action}'. Ignoring."
                )


def load_keybindings(filepath=DEFAULT_KEYBIND_FILE):
    """Loads keybindings from the specified file or uses defaults."""
    config_source = DEFAULT_KEYBINDS_CONFIG.copy()
    created_default_file = False

    if os.path.exists(filepath):
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                loaded_config = json.load(f)

            if not isinstance(loaded_config, dict):
                print(
                    f"Warning: '{filepath}' does not contain a valid dictionary. Using default keybindings."
                )
            else:
                # Merge: User's config updates defaults.
                # This way, if user deletes an action from JSON, it still falls back to default.
                # And if we add new actions to DEFAULT_KEYBINDS_CONFIG, they'll be available.
                merged_config = DEFAULT_KEYBINDS_CONFIG.copy()
                for action, keys in loaded_config.items():
                    if action in merged_config:  # Only update known actions
                        if isinstance(keys, list):
                            merged_config[action] = keys
                        else:
                            print(
                                f"Warning: Value for action '{action}' in '{filepath}' is not a list. Using default for this action."
                            )
                    else:
                        print(
                            f"Warning: Unknown action '{action}' in '{filepath}'. Ignoring."
                        )
                config_source = merged_config
                print(f"Loaded keybindings from '{filepath}'.")

        except json.JSONDecodeError:
            print(
                f"Error: Could not decode JSON from '{filepath}'. Using default keybindings."
            )
        except Exception as e:
            print(f"Error loading '{filepath}': {e}. Using default keybindings.")
    else:
        print(
            f"'{filepath}' not found. Using default keybindings and creating a default file."
        )
        try:
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(DEFAULT_KEYBINDS_CONFIG, f, indent=2, sort_keys=True)
            print(f"A default keybinding file has been created at '{filepath}'.")
            created_default_file = True
        except Exception as e:
            print(f"Could not create default keybinding file at '{filepath}': {e}")

    _populate_key_maps(config_source)
    if created_default_file:
        print(
            "Please review the generated 'keybinds.json' and restart the application if you made changes while it was running."
        )

    # Return the populated maps for the TUI to use
    return KEY_ACTIONS, ALT_KEY_ACTIONS, LOADED_CONFIG_FOR_DISPLAY


def get_display_for_action(action_name):
    """Generates a user-friendly string list of keys for an action, e.g., ['Up', 'k']."""
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
            # e.g., "KEY_UP" -> "Up"
            display_keys.append(key_spec.replace("KEY_", "").capitalize())
        elif key_spec == "\n":
            display_keys.append("Enter")  # More user-friendly than '\n'
        else:
            display_keys.append(key_spec)  # Regular character
    return display_keys
