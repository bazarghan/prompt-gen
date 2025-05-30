# tui.py

import curses
import os

import keybindings
import theme_manager  # Import the new theme manager
from file_operations import get_dir_contents
from output_generator import generate_output_from_selection


# --- Helper function to determine effective selection (from previous step) ---
def is_effectively_selected(item_path, selection_roots, explicit_exclusions):
    norm_item_path = os.path.normpath(item_path)
    current_path_segment = norm_item_path
    selected_ancestor_root = None
    while True:
        if current_path_segment in selection_roots:
            selected_ancestor_root = current_path_segment
            break
        parent = os.path.dirname(current_path_segment)
        if parent == current_path_segment:
            break
        current_path_segment = parent
    if selected_ancestor_root is None:
        return False
    if norm_item_path == selected_ancestor_root:
        return True
    current_path_segment = norm_item_path
    while current_path_segment != selected_ancestor_root:
        if current_path_segment in explicit_exclusions:
            return False
        parent = os.path.dirname(current_path_segment)
        if parent == current_path_segment:
            return False
        if not current_path_segment.startswith(selected_ancestor_root):
            break
        current_path_segment = parent
        if not current_path_segment:
            break
    return True


def display_files(
    stdscr,
    current_path,
    items,
    current_selection_idx,
    selection_roots,
    explicit_exclusions,
    error_message=None,
):
    h, w = stdscr.getmaxyx()

    # Apply background for the whole screen (important for consistent theming)
    # The bkgd call also clears the screen with the new background attribute
    stdscr.bkgd(" ", theme_manager.get_pair("app_background"))
    stdscr.erase()  # Ensure screen is cleared with new background

    # --- Header ---
    header_pair = theme_manager.get_pair("header")
    header_text = f"Interactive Project Lister - Path: {current_path}"
    try:
        stdscr.addstr(
            0, 0, header_text[: w - 1].ljust(w - 1), header_pair | curses.A_BOLD
        )
    except curses.error:
        pass  # Terminal too small

    # --- Instructions ---
    instr_pair = theme_manager.get_pair("instructions")
    nav_up_keys = "/".join(
        keybindings.get_display_for_action(keybindings.ACTION_NAVIGATE_UP)
    )
    nav_down_keys = "/".join(
        keybindings.get_display_for_action(keybindings.ACTION_NAVIGATE_DOWN)
    )
    enter_keys = "/".join(
        keybindings.get_display_for_action(keybindings.ACTION_ENTER_DIRECTORY)
    )
    parent_keys = "/".join(
        keybindings.get_display_for_action(keybindings.ACTION_PARENT_DIRECTORY)
    )
    select_keys = "/".join(
        keybindings.get_display_for_action(keybindings.ACTION_TOGGLE_SELECT)
    )
    generate_keys = "/".join(
        keybindings.get_display_for_action(keybindings.ACTION_GENERATE_OUTPUT)
    )
    quit_keys = "/".join(keybindings.get_display_for_action(keybindings.ACTION_QUIT))
    instructions_parts = [
        f"[{nav_up_keys}/{nav_down_keys}] Nav",
        f"[{enter_keys}] Enter",
        f"[{parent_keys}] Parent",
        f"[{select_keys}] Sel",
        f"[{generate_keys}] Gen",
        f"[{quit_keys}] Quit",
    ]
    instructions_text = " | ".join(instructions_parts)
    instruction_line = h - 2
    try:
        if instruction_line > 0:  # Ensure there's space for instructions
            stdscr.addstr(
                instruction_line, 0, instructions_text[: w - 1].ljust(w - 1), instr_pair
            )
    except curses.error:
        pass

    # --- Error Message ---
    error_start_line = 1
    if error_message:
        error_pair = theme_manager.get_pair("error_message")
        try:
            stdscr.addstr(
                error_start_line,
                0,
                f"Error: {error_message}"[: w - 1].ljust(w - 1),
                error_pair,
            )
            start_line = error_start_line + 1
        except curses.error:
            start_line = error_start_line  # Could not draw error, proceed
    else:
        start_line = error_start_line

    # --- File/Directory Listing ---
    display_offset = 0
    # Number of lines available for items (header, error (if any), instructions, status bar)
    displayable_lines = (
        h - start_line - (1 if instruction_line > 0 else 0) - 1
    )  # -1 for status bar
    if displayable_lines < 0:
        displayable_lines = 0

    if current_selection_idx >= display_offset + displayable_lines:
        display_offset = current_selection_idx - displayable_lines + 1
    elif current_selection_idx < display_offset:
        display_offset = current_selection_idx

    for i, item in enumerate(items):
        if i < display_offset:
            continue

        # Calculate actual line number on screen
        line_num_abs = start_line + (i - display_offset)
        # Ensure we don't draw over instructions or status bar
        if line_num_abs >= instruction_line and instruction_line > 0:
            break
        if line_num_abs >= h - 1:
            break  # Stop before status bar line

        display_name = item["name"]
        is_dir = item["is_dir"]
        if is_dir:
            display_name += "/"

        path_is_effectively_selected = is_effectively_selected(
            item["path"], selection_roots, explicit_exclusions
        )

        # Determine style based on selection and type
        item_style = curses.A_NORMAL
        if i == current_selection_idx:  # Highlighted item
            if is_dir:
                item_pair = theme_manager.get_pair("item_selected_dir")
            else:
                item_pair = theme_manager.get_pair("item_selected")
            item_style = (
                curses.A_REVERSE
            )  # Often themes define selected bg/fg, reverse might not be needed
            # Or, themes can define specific "selected_*" pairs
        else:  # Not highlighted
            if is_dir:
                item_pair = theme_manager.get_pair("item_dir")
            else:
                item_pair = theme_manager.get_pair("item_file")

        # Selection marker
        if path_is_effectively_selected:
            marker = "[*] "
            marker_pair = theme_manager.get_pair("item_selection_marker_selected")
        else:
            marker = "[ ] "
            marker_pair = theme_manager.get_pair("item_selection_marker_unselected")

        line_str_name = f"{display_name}"

        try:
            # Draw selection marker
            stdscr.addstr(line_num_abs, 0, marker, marker_pair)
            # Draw item name
            # Ensure enough space for the marker before drawing the name
            stdscr.addstr(
                line_num_abs,
                len(marker),
                line_str_name[: w - 1 - len(marker)],
                item_pair | item_style,
            )
            # Clear rest of the line with the item's base background (if not selected) or app background
            # This prevents visual artifacts if item_pair has a different background than app_background
            # This is a bit tricky. If item_pair has its own bg, clearing with app_background might look odd.
            # For now, let's assume item_pair's bg is what we want for the whole line segment.
            # Or, if item_style is A_REVERSE, it handles the background for the selected part.
            # A simpler approach: pad the string with spaces and let addstr handle it.
            full_line_display = (marker + line_str_name)[: w - 1].ljust(w - 1)
            # Re-draw with combined attributes if selected for full line effect
            if i == current_selection_idx:
                stdscr.addstr(
                    line_num_abs, 0, marker, marker_pair | item_style
                )  # Apply style to marker too
                stdscr.addstr(
                    line_num_abs,
                    len(marker),
                    line_str_name[: w - 1 - len(marker)],
                    item_pair | item_style,
                )
                # Clear rest of line with selected style
                remaining_len = (
                    w - 1 - len(marker) - len(line_str_name[: w - 1 - len(marker)])
                )
                if remaining_len > 0:
                    stdscr.addstr(" " * remaining_len, item_pair | item_style)

            else:  # Not selected, draw marker and name separately
                stdscr.addstr(line_num_abs, 0, marker, marker_pair)
                stdscr.addstr(
                    line_num_abs,
                    len(marker),
                    line_str_name[: w - 1 - len(marker)],
                    item_pair,
                )
                # Clear rest of line with default item background or app background
                default_bg_pair = (
                    theme_manager.get_pair("item_default")
                    if not is_dir
                    else theme_manager.get_pair("item_dir")
                )
                # If item_pair has specific bg, use it, else use app_background
                # This part is complex to get perfect without knowing theme structure well.
                # Simplest for now: rely on stdscr.bkgd and ensure elements draw fg only if bg is "default"
                # Or, ensure elements draw their full bg.
                # Let's try padding with the item's pair.
                current_text_len = len(marker) + len(
                    line_str_name[: w - 1 - len(marker)]
                )
                if current_text_len < w - 1:
                    stdscr.addstr(
                        line_num_abs,
                        current_text_len,
                        " " * (w - 1 - current_text_len),
                        item_pair,
                    )

        except curses.error:
            pass  # Terminal too small

    if (
        not items
        and not error_message
        and start_line < (instruction_line if instruction_line > 0 else h - 1)
    ):
        try:
            stdscr.addstr(
                start_line,
                2,
                "(Directory is empty or not accessible)",
                theme_manager.get_pair("item_default"),
            )
        except curses.error:
            pass

    # stdscr.refresh() # Refresh is called in the main loop after status bar


def tui_main(stdscr, initial_path):
    # --- Initialize Curses and Theming ---
    curses.curs_set(0)  # Hide cursor
    stdscr.keypad(True)  # Enable special keys

    theme_manager.init_curses_colors()  # Initialize color system (must be after start_color/curses.initscr)
    if not theme_manager.load_theme("default_theme.json"):  # Load your default theme
        # Fallback or error handling if theme loading fails
        print("CRITICAL: Default theme could not be loaded. Exiting.")
        return

    # Apply initial background for the whole screen
    stdscr.bkgd(" ", theme_manager.get_pair("app_background"))
    # --- End Initialization ---

    keybindings.load_keybindings()  # Load keybindings

    current_path = os.path.abspath(initial_path)
    items, error_msg = get_dir_contents(current_path)
    current_selection_idx = 0

    selection_roots = set()
    explicit_exclusions = set()
    status_message = ""

    while True:
        stdscr.erase()  # Clear screen at the start of each loop iteration
        display_files(
            stdscr,
            current_path,
            items,
            current_selection_idx,
            selection_roots,
            explicit_exclusions,
            error_msg,
        )

        # --- Status Bar ---
        status_bar_pair = theme_manager.get_pair("status_bar")
        h, w = stdscr.getmaxyx()
        current_status_text = (
            status_message
            if status_message
            else f"Items: {len(items)} | Selected Roots: {len(selection_roots)}"
        )
        try:
            if h > 1:  # Ensure there's a line for status bar
                stdscr.addstr(
                    h - 1, 0, current_status_text[: w - 1].ljust(w - 1), status_bar_pair
                )
        except curses.error:
            pass

        stdscr.refresh()  # Refresh the screen once all elements are drawn

        status_message = ""  # Clear status message for next iteration
        error_msg = None  # Clear error message for next iteration

        raw_key = stdscr.getch()
        effective_action = None

        if raw_key == 27:
            stdscr.timeout(50)
            second_key = stdscr.getch()
            stdscr.timeout(-1)
            if second_key != -1:
                effective_action = keybindings.ALT_KEY_ACTIONS.get(second_key)
        else:
            effective_action = keybindings.KEY_ACTIONS.get(raw_key)

        if effective_action == keybindings.ACTION_QUIT:
            break
        elif effective_action == keybindings.ACTION_NAVIGATE_UP:
            if items:
                current_selection_idx = (current_selection_idx - 1 + len(items)) % len(
                    items
                )
        elif effective_action == keybindings.ACTION_NAVIGATE_DOWN:
            if items:
                current_selection_idx = (current_selection_idx + 1) % len(items)
        elif effective_action == keybindings.ACTION_ENTER_DIRECTORY:
            if (
                items
                and 0 <= current_selection_idx < len(items)
                and items[current_selection_idx]["is_dir"]
            ):
                new_path_candidate = items[current_selection_idx]["path"]
                temp_items, test_err = get_dir_contents(
                    new_path_candidate
                )  # Store items to check if dir is accessible
                if not test_err:
                    current_path = new_path_candidate
                    items = temp_items  # Use the already fetched items
                    current_selection_idx = 0
                else:
                    error_msg = test_err  # Show error if dir not accessible
            # else: error_msg = None # No error if trying to enter file
        elif effective_action == keybindings.ACTION_PARENT_DIRECTORY:
            parent_path = os.path.dirname(current_path)
            if parent_path != current_path:
                current_path = parent_path
                items, error_msg = get_dir_contents(current_path)
                current_selection_idx = 0
        elif effective_action == keybindings.ACTION_TOGGLE_SELECT:
            if items and 0 <= current_selection_idx < len(items):
                item_path = os.path.normpath(items[current_selection_idx]["path"])
                currently_selected_eff = is_effectively_selected(
                    item_path, selection_roots, explicit_exclusions
                )
                if currently_selected_eff:
                    if item_path in selection_roots:
                        selection_roots.remove(item_path)
                        explicit_exclusions.discard(item_path)
                    else:
                        explicit_exclusions.add(item_path)
                else:
                    if item_path in explicit_exclusions:
                        explicit_exclusions.remove(item_path)
                    else:
                        selection_roots.add(item_path)
                        explicit_exclusions.discard(item_path)
        elif effective_action == keybindings.ACTION_GENERATE_OUTPUT:
            if not selection_roots:
                status_message = "No selection roots. Use 'Select' key to mark items."
            else:
                generating_msg = "Generating output... please wait."
                # Display generating message in status bar temporarily
                try:
                    if h > 1:
                        stdscr.addstr(
                            h - 1,
                            0,
                            generating_msg[: w - 1].ljust(w - 1),
                            theme_manager.get_pair("status_bar") | curses.A_BOLD,
                        )
                    stdscr.refresh()
                except curses.error:
                    pass

                output_filename = "output.txt"
                status_message = generate_output_from_selection(
                    selection_roots, explicit_exclusions, output_filename
                )
                items, error_msg = get_dir_contents(current_path)  # Refresh view
        elif effective_action is None and raw_key == 27:
            pass
        # else: error_msg = None # No error for unmapped keys

        if not items:
            current_selection_idx = 0
        elif current_selection_idx >= len(items):
            current_selection_idx = len(items) - 1 if items else 0
        elif current_selection_idx < 0 and items:
            current_selection_idx = 0
