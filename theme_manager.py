# theme_manager.py
import curses
import json
import os

# Global dictionary to store loaded theme color pairs
# Keys will be element names (e.g., "header"), values will be curses.color_pair(n)
THEME_COLOR_PAIRS = {}
CURRENT_THEME_DATA = {}  # Stores the raw loaded theme JSON

# Mapping of common color names to curses color constants
# We'll try to initialize bright colors if the terminal supports them (COLORS >= 16)
COLOR_NAME_MAP = {
    "black": curses.COLOR_BLACK,
    "red": curses.COLOR_RED,
    "green": curses.COLOR_GREEN,
    "yellow": curses.COLOR_YELLOW,
    "blue": curses.COLOR_BLUE,
    "magenta": curses.COLOR_MAGENTA,
    "cyan": curses.COLOR_CYAN,
    "white": curses.COLOR_WHITE,
    # Placeholder for bright colors, will be populated in init_colors
    "bright_black": curses.COLOR_BLACK + 8,  # Often grey
    "bright_red": curses.COLOR_RED + 8,
    "bright_green": curses.COLOR_GREEN + 8,
    "bright_yellow": curses.COLOR_YELLOW + 8,
    "bright_blue": curses.COLOR_BLUE + 8,
    "bright_magenta": curses.COLOR_MAGENTA + 8,
    "bright_cyan": curses.COLOR_CYAN + 8,
    "bright_white": curses.COLOR_WHITE + 8,
    "default": -1,  # For using terminal's default foreground or background
}

# To keep track of allocated color pairs (fg_curses_const, bg_curses_const) -> pair_number
_allocated_pairs_map = {}
_next_pair_number = 1  # Color pair numbers start from 1


def _get_curses_color(color_name_or_int, default_color=curses.COLOR_WHITE):
    """Converts a color name or int to a curses color constant."""
    if isinstance(color_name_or_int, int):
        return color_name_or_int  # Assume it's already a curses.COLOR_* constant or -1

    color_name = str(color_name_or_int).lower()

    # Handle bright colors dynamically based on terminal capability
    if color_name.startswith("bright_") and curses.COLORS < 16:
        # Fallback for terminals with less than 16 colors (e.g., use normal version)
        fallback_color_name = color_name.replace("bright_", "")
        return COLOR_NAME_MAP.get(fallback_color_name, default_color)

    return COLOR_NAME_MAP.get(color_name, default_color)


def _get_or_create_color_pair(fg_name, bg_name):
    """
    Gets an existing color pair for the fg/bg combination or creates a new one.
    Returns the curses.color_pair(n) attribute.
    """
    global _next_pair_number, _allocated_pairs_map

    fg_curses = _get_curses_color(fg_name, curses.COLOR_WHITE)
    bg_curses = _get_curses_color(bg_name, curses.COLOR_BLACK)

    if (fg_curses, bg_curses) in _allocated_pairs_map:
        pair_number = _allocated_pairs_map[(fg_curses, bg_curses)]
    else:
        if _next_pair_number >= curses.COLOR_PAIRS:
            # Ran out of color pairs, reuse pair 1 (or handle error)
            # This is a limitation of curses.
            print(
                f"Warning: Ran out of color pairs (max: {curses.COLOR_PAIRS}). Reusing pair 1."
            )
            pair_number = 1
        else:
            curses.init_pair(_next_pair_number, fg_curses, bg_curses)
            _allocated_pairs_map[(fg_curses, bg_curses)] = _next_pair_number
            pair_number = _next_pair_number
            _next_pair_number += 1

    return curses.color_pair(pair_number)


def init_curses_colors():
    """Initializes curses color system and populates bright color map if possible."""
    curses.start_color()
    # Use terminal's default background and foreground for pair 0 if -1 is used for colors
    # This allows for transparency if terminal supports it.
    try:
        curses.use_default_colors()
        COLOR_NAME_MAP["default"] = -1  # Enable use of "default" for fg/bg
    except Exception:
        # use_default_colors might not be available or fail on some terminals
        print(
            "Warning: Terminal does not support default colors. Using black as default background."
        )
        COLOR_NAME_MAP["default"] = (
            curses.COLOR_BLACK
        )  # Fallback for bg if use_default_colors fails

    if curses.COLORS >= 16:
        # Standard ANSI bright colors are usually the base color + 8
        COLOR_NAME_MAP["bright_black"] = curses.COLOR_BLACK + 8
        COLOR_NAME_MAP["bright_red"] = curses.COLOR_RED + 8
        COLOR_NAME_MAP["bright_green"] = curses.COLOR_GREEN + 8
        COLOR_NAME_MAP["bright_yellow"] = curses.COLOR_YELLOW + 8
        COLOR_NAME_MAP["bright_blue"] = curses.COLOR_BLUE + 8
        COLOR_NAME_MAP["bright_magenta"] = curses.COLOR_MAGENTA + 8
        COLOR_NAME_MAP["bright_cyan"] = curses.COLOR_CYAN + 8
        COLOR_NAME_MAP["bright_white"] = curses.COLOR_WHITE + 8
    else:
        # For 8-color terminals, map bright colors to their normal counterparts
        print(
            f"Terminal supports {curses.COLORS} colors. Bright colors will map to normal colors."
        )
        for i in range(8):
            COLOR_NAME_MAP[list(COLOR_NAME_MAP.keys())[i + 8]] = (
                i  # e.g. bright_black maps to black
            )


def load_theme(theme_filepath="default_theme.json"):
    """Loads a theme from a JSON file and populates THEME_COLOR_PAIRS."""
    global THEME_COLOR_PAIRS, CURRENT_THEME_DATA, _next_pair_number, _allocated_pairs_map

    # Reset for re-loading themes
    THEME_COLOR_PAIRS.clear()
    CURRENT_THEME_DATA = {}
    _allocated_pairs_map = {}
    _next_pair_number = 1  # Reset pair number counter

    # Ensure curses colors are initialized before we try to use them
    # This is typically called once in tui_main, but good to have a check
    if not curses.has_colors():
        print("Error: Terminal does not support colors.")
        return False

    theme_data = {}
    if os.path.exists(theme_filepath):
        try:
            with open(theme_filepath, "r") as f:
                theme_data = json.load(f)
            CURRENT_THEME_DATA = theme_data
            print(
                f"Theme '{theme_data.get('name', 'Unknown')}' loaded from {theme_filepath}"
            )
        except json.JSONDecodeError:
            print(
                f"Error: Could not decode JSON from '{theme_filepath}'. Using fallback."
            )
        except Exception as e:
            print(f"Error loading theme '{theme_filepath}': {e}. Using fallback.")
    else:
        print(f"Theme file '{theme_filepath}' not found. Using fallback.")

    # Fallback default element definitions if theme is missing or elements are missing
    default_elements = {
        "app_background": {"fg": "white", "bg": "black"},
        "header": {"fg": "white", "bg": "black"},
        "instructions": {"fg": "yellow", "bg": "black"},
        "status_bar": {"fg": "black", "bg": "green"},
        "error_message": {"fg": "white", "bg": "red"},
        "item_default": {"fg": "white", "bg": "black"},
        "item_dir": {"fg": "blue", "bg": "black"},
        "item_file": {"fg": "white", "bg": "black"},
        "item_selected": {"fg": "white", "bg": "black"},
        "item_selected_dir": {"fg": "white", "bg": "black"},
        "item_selection_marker_selected": {"fg": "white", "bg": "black"},
        "item_selection_marker_unselected": {"fg": "white", "bg": "black"},
    }

    elements_to_style = theme_data.get("elements", default_elements)

    # Ensure all default elements have at least a fallback style
    for element_name, default_style in default_elements.items():
        if element_name not in elements_to_style:
            elements_to_style[element_name] = default_style
            print(f"Theme missing '{element_name}', using fallback style.")

    for element_name, colors in elements_to_style.items():
        fg = colors.get("fg", "white")
        bg = colors.get("bg", "default")  # Use terminal default background
        THEME_COLOR_PAIRS[element_name] = _get_or_create_color_pair(fg, bg)

    # Special case: ensure app_background is applied to stdscr if defined
    if "app_background" in THEME_COLOR_PAIRS:
        # This pair will be used by stdscr.bkgd() in tui_main
        pass

    return True


def get_pair(element_name):
    """Gets the color pair for a UI element. Falls back if element not defined."""
    return THEME_COLOR_PAIRS.get(
        element_name, curses.color_pair(0)
    )  # Fallback to default pair 0
