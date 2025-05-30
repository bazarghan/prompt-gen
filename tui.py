# tui.py

import curses
import os

import keybindings  # Import the new module
from file_operations import get_dir_contents
from output_generator import generate_output_from_selection


# --- Helper function to determine effective selection ---
def is_effectively_selected(item_path, selection_roots, explicit_exclusions):
    """
    Determines if an item should be considered selected.
    An item is selected if:
    1. It is itself a selection_root.
    2. Or, an ancestor is a selection_root AND neither the item nor any ancestor
       between it and that selection_root is in explicit_exclusions.
    """
    # Normalize path for consistent comparisons
    norm_item_path = os.path.normpath(item_path)

    # Check if the path itself or any ancestor is a selection root
    # Iterates from item_path upwards to find the closest (or self) selection root.
    current_path_segment = norm_item_path
    selected_ancestor_root = None
    while True:
        if current_path_segment in selection_roots:
            selected_ancestor_root = current_path_segment
            break
        parent = os.path.dirname(current_path_segment)
        if parent == current_path_segment:  # Reached filesystem root
            break
        current_path_segment = parent

    if selected_ancestor_root is None:
        return False  # Not selected via any root

    # If item_path is the selection_root itself, it's selected.
    # (Toggle logic ensures a root isn't also an active exclusion for itself).
    if (
        norm_item_path == selected_ancestor_root
    ):  # norm_item_path in selection_roots also works
        return True

    # Now check for exclusions on the path from item_path up to (but not including) selected_ancestor_root
    current_path_segment = norm_item_path
    while current_path_segment != selected_ancestor_root:
        if current_path_segment in explicit_exclusions:
            return False  # Excluded at this level

        parent = os.path.dirname(current_path_segment)
        if (
            parent == current_path_segment
        ):  # Safety break, unexpected if selected_ancestor_root was found
            return False
        if not parent.startswith(
            os.path.dirname(selected_ancestor_root)
        ):  # Optimization/safety
            # This check ensures we don't go "above" the selected_ancestor_root's parent
            # especially if selected_ancestor_root is deep. If parent is shallower than selected_ancestor_root's dir, something is wrong or we are done.
            # A simpler check: ensure parent is still a sub-path of selected_ancestor_root's parent, or selected_ancestor_root itself
            if not current_path_segment.startswith(
                selected_ancestor_root
            ):  # ensure current is under root
                break  # stop if current path is no longer under the identified root
        current_path_segment = parent
        if not current_path_segment:  # Reached very top
            break

    return True  # Implicitly selected, not excluded along the path from root.


def display_files(
    stdscr,
    current_path,
    items,
    current_selection_idx,
    selection_roots,  # CHANGED
    explicit_exclusions,  # NEW
    error_message=None,
):
    stdscr.clear()
    h, w = stdscr.getmaxyx()

    header = f"Interactive Project Lister - Path: {current_path}"
    stdscr.addstr(0, 0, header[: w - 1], curses.A_REVERSE)

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
    instructions = " | ".join(instructions_parts)
    instruction_line = h - 2
    try:
        if len(instructions) >= w:
            stdscr.addstr(instruction_line, 0, instructions[: w - 1])
        else:
            stdscr.addstr(instruction_line, 0, instructions)
    except curses.error:
        pass

    if error_message:
        stdscr.addstr(1, 0, f"Error: {error_message}"[: w - 1], curses.color_pair(1))
        start_line = 2
    else:
        start_line = 1

    display_offset = 0
    displayable_lines = h - start_line - 2
    if displayable_lines < 0:
        displayable_lines = 0

    if current_selection_idx >= display_offset + displayable_lines:
        display_offset = current_selection_idx - displayable_lines + 1
    elif current_selection_idx < display_offset:
        display_offset = current_selection_idx

    for i, item in enumerate(items):
        if i < display_offset:
            continue
        line_num_abs = start_line + (i - display_offset)
        if line_num_abs >= instruction_line:
            break

        display_name = item["name"]
        if item["is_dir"]:
            display_name += "/"

        path_is_effectively_selected = is_effectively_selected(
            item["path"], selection_roots, explicit_exclusions
        )
        prefix = "[*] " if path_is_effectively_selected else "[ ] "

        line_str = f"{prefix}{display_name}"
        try:
            if i == current_selection_idx:
                stdscr.addstr(line_num_abs, 0, line_str[: w - 1], curses.A_REVERSE)
            else:
                stdscr.addstr(line_num_abs, 0, line_str[: w - 1])
        except curses.error:
            pass

    if not items and not error_message and start_line < instruction_line:
        stdscr.addstr(start_line, 2, "(Directory is empty or not accessible)")

    stdscr.refresh()


def tui_main(stdscr, initial_path):
    keybindings.load_keybindings()

    curses.curs_set(0)
    stdscr.keypad(True)
    curses.start_color()
    curses.init_pair(1, curses.COLOR_RED, curses.COLOR_BLACK)

    current_path = os.path.abspath(initial_path)
    items, error_msg = get_dir_contents(current_path)
    current_selection_idx = 0

    selection_roots = set()
    explicit_exclusions = set()
    status_message = ""

    while True:
        display_files(
            stdscr,
            current_path,
            items,
            current_selection_idx,
            selection_roots,
            explicit_exclusions,
            error_msg,
        )
        if status_message:
            h, w = stdscr.getmaxyx()
            stdscr.move(h - 1, 0)
            stdscr.clrtoeol()
            stdscr.addstr(h - 1, 0, status_message[: w - 1])
            stdscr.refresh()
            status_message = ""
            error_msg = None

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
            error_msg = None
        elif effective_action == keybindings.ACTION_NAVIGATE_DOWN:
            if items:
                current_selection_idx = (current_selection_idx + 1) % len(items)
            error_msg = None
        elif effective_action == keybindings.ACTION_ENTER_DIRECTORY:
            if (
                items
                and 0 <= current_selection_idx < len(items)
                and items[current_selection_idx]["is_dir"]
            ):
                new_path_candidate = items[current_selection_idx]["path"]
                _, test_err = get_dir_contents(new_path_candidate)
                if not test_err:
                    current_path = new_path_candidate
                    items, error_msg = get_dir_contents(current_path)
                    current_selection_idx = 0
                else:
                    error_msg = test_err
            else:
                error_msg = None
        elif effective_action == keybindings.ACTION_PARENT_DIRECTORY:
            parent_path = os.path.dirname(current_path)
            if parent_path != current_path:
                current_path = parent_path
                items, error_msg = get_dir_contents(current_path)
                current_selection_idx = 0
            error_msg = None
        elif effective_action == keybindings.ACTION_TOGGLE_SELECT:
            if items and 0 <= current_selection_idx < len(items):
                item_path = os.path.normpath(
                    items[current_selection_idx]["path"]
                )  # Normalize for consistency
                currently_selected_eff = is_effectively_selected(
                    item_path, selection_roots, explicit_exclusions
                )

                if currently_selected_eff:  # Currently [*], so deselecting
                    if item_path in selection_roots:  # It's a root
                        selection_roots.remove(item_path)
                        explicit_exclusions.discard(item_path)  # Ensure consistency
                    else:  # Implicitly selected
                        explicit_exclusions.add(item_path)
                else:  # Currently [ ], so selecting
                    if item_path in explicit_exclusions:  # Was an exclusion
                        explicit_exclusions.remove(
                            item_path
                        )  # No longer excluded (becomes implicitly selected if ancestor root exists)
                    else:  # Genuinely unselected
                        selection_roots.add(item_path)
                        explicit_exclusions.discard(
                            item_path
                        )  # New root overrides exclusion status for itself
            error_msg = None
        elif effective_action == keybindings.ACTION_GENERATE_OUTPUT:
            if not selection_roots:
                status_message = "No selection roots. Use 'Select' key to mark items."
            else:
                h, w = stdscr.getmaxyx()
                generating_msg = "Generating output... please wait."
                try:
                    stdscr.addstr(
                        h // 2,
                        (w - len(generating_msg)) // 2,
                        generating_msg,
                        curses.A_REVERSE,
                    )
                except:
                    stdscr.addstr(h - 1, 0, generating_msg, curses.A_REVERSE)
                stdscr.refresh()
                output_filename = "output.txt"
                status_message = generate_output_from_selection(
                    selection_roots, explicit_exclusions, output_filename
                )
                items, error_msg = get_dir_contents(current_path)  # Refresh view
        elif effective_action is None and raw_key == 27:
            pass
        else:
            error_msg = None

        if not items:
            current_selection_idx = 0
        elif current_selection_idx >= len(items):
            current_selection_idx = len(items) - 1 if items else 0
        elif current_selection_idx < 0 and items:
            current_selection_idx = 0
