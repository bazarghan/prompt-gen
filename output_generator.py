"""output_generator.py

Generates the `output.txt` file that Prompt‑Gen CLI uses as an LLM‑friendly
project overview.  This revision prints the directory tree in **depth‑first
(directories‑first)** order so the visual structure now matches the classic
`tree` command with the `--dirsfirst` flag.
"""

from __future__ import annotations

import os
from typing import List, Set

import config

# ---------------------------------------------------------------------------
# Boilerplate prompt that is inserted at the top of every generated file
# ---------------------------------------------------------------------------
BOILERPLATE_PROMPT = """The following is a detailed overview of a software project.\n\n"
    "It includes the directory structure and the content of selected source "
    "code files.\n\n"
    "Please analyze this information to understand the project's components, "
    "relationships, and functionality.  This context can be used to answer "
    "questions about the project, assist with debugging, suggest refactorings, "
    "or generate documentation.\n"""


# ---------------------------------------------------------------------------
# Helper – exclusion logic that honours explicit exclusions as well as the
#          implicit ones from config.py
# ---------------------------------------------------------------------------


def _is_path_excluded_for_generation(
    path_to_check: str,
    current_selection_root_path: str,
    explicit_exclusions: Set[str],
) -> bool:
    """Returns *True* if *path_to_check* should be skipped.  The rule is:

    * If the path itself or any of its ancestors **between** it and the
      *selection root* is explicitly excluded by the user, we skip it.
    * The selection root itself is **never** excluded here – that check is
      performed by the caller.  This allows us to call the helper for the root
      without it instantly excluding itself.
    """

    norm_path = os.path.normpath(path_to_check)
    norm_root = os.path.normpath(current_selection_root_path)

    # Walk up from the path towards the selection root, looking for explicit
    # exclusions on the way.  We stop once we reach the root or escape it.
    while True:
        if norm_path in explicit_exclusions:
            return True
        if norm_path == norm_root:
            break
        parent = os.path.dirname(norm_path)
        if parent == norm_path or not norm_path.startswith(norm_root):
            break  # hit the FS root or stepped outside selection root
        norm_path = parent

    return False


# ---------------------------------------------------------------------------
# Public API – the single function the rest of the programme uses.
# ---------------------------------------------------------------------------


def generate_output_from_selection(
    selection_roots: Set[str],
    explicit_exclusions: Set[str],
    output_filename: str = "output.txt",
) -> str:
    """Walk the *selection_roots* and write *output_filename*.

    Returns a short status message suitable for the TUI status‑bar.
    """

    base_run_directory = os.getcwd()

    # Parts of the eventual file ------------------------------------------------
    structure_lines: List[str] = []  # tree listing – DFS, dirs‑first
    content_lines: List[str] = []  # full file contents (for selected files)

    # We also build these for bookkeeping / de‑duplication ----------------------
    paths_in_structure: Set[str] = set()  # absolute, normalised paths already shown
    files_to_include: Set[str] = set()  # abs paths whose content we will embed

    # ---------------------------------------------------------------------
    # 1. Header section
    # ---------------------------------------------------------------------
    structure_lines.append(BOILERPLATE_PROMPT + "\n")
    structure_lines.append("PROJECT CONTEXT OVERVIEW\n")
    structure_lines.append("========================\n\n")

    # -- 1.1 Selection roots ----------------------------------------------------
    structure_lines.append(
        "SELECTION ROOTS (items explicitly chosen to start the project scan):\n"
    )
    if not selection_roots:
        structure_lines.append("(None – the overview will be empty.)\n")
    for p_abs in sorted(selection_roots):
        rel = os.path.relpath(os.path.normpath(p_abs), base_run_directory)
        structure_lines.append(f"- {rel}\n")

    # -- 1.2 Explicit exclusions ------------------------------------------------
    if explicit_exclusions:
        structure_lines.append(
            "\nEXPLICIT EXCLUSIONS (items specifically excluded from the scan):\n"
        )
        for p_abs in sorted(explicit_exclusions):
            rel = os.path.relpath(os.path.normpath(p_abs), base_run_directory)
            structure_lines.append(f"- {rel}\n")

    # -- 1.3 Start of combined tree --------------------------------------------
    structure_lines.append(
        "\nCOMBINED PROJECT STRUCTURE (based on selections and exclusions):\n"
    )

    if not selection_roots:
        structure_lines.append("(Project structure is empty.)\n")

    # ---------------------------------------------------------------------
    # 2. Depth‑first walk per selection root
    # ---------------------------------------------------------------------

    def _emit_tree(
        current_abs: str, sel_root_abs: str, indent_level: int
    ) -> None:  # noqa: N802 – internal helper
        """Recursive DFS emitter – directories first, then files."""
        nonlocal structure_lines, paths_in_structure, files_to_include

        try:
            entries = sorted(os.listdir(current_abs))
        except PermissionError:
            return  # silently skip unreadable dirs

        # Separate dirs from files and apply default ignore rules
        dir_names = [e for e in entries if os.path.isdir(os.path.join(current_abs, e))]
        file_names = [
            e for e in entries if os.path.isfile(os.path.join(current_abs, e))
        ]

        # Apply hidden‑file and configured ignores to *dir_names* ----------------
        dir_names = [
            d
            for d in dir_names
            if not d.startswith(".") and d not in config.IGNORE_DIRS
        ]

        # Apply ignores to *file_names* -----------------------------------------
        file_names = [
            f
            for f in file_names
            if not f.startswith(".") and f not in config.IGNORE_FILES
        ]

        indent = "    " * indent_level

        # First emit directories -------------------------------------------------
        for idx, d in enumerate(dir_names):
            d_abs = os.path.normpath(os.path.join(current_abs, d))
            if _is_path_excluded_for_generation(
                d_abs, sel_root_abs, explicit_exclusions
            ):
                continue
            if d_abs not in paths_in_structure:
                structure_lines.append(f"{indent}├── {d}/\n")
                paths_in_structure.add(d_abs)
            _emit_tree(d_abs, sel_root_abs, indent_level + 1)

        # Then emit files --------------------------------------------------------
        for f in file_names:
            f_abs = os.path.normpath(os.path.join(current_abs, f))
            if _is_path_excluded_for_generation(
                f_abs, sel_root_abs, explicit_exclusions
            ):
                continue
            if f_abs not in paths_in_structure:
                structure_lines.append(f"{indent}├── {f}\n")
                paths_in_structure.add(f_abs)
            files_to_include.add(f_abs)

    # Walk each selection root --------------------------------------------------
    for root_abs in sorted(os.path.normpath(p) for p in selection_roots):
        if root_abs in explicit_exclusions:
            continue  # user explicitly deselected the root itself

        is_dir = os.path.isdir(root_abs)
        rel_root = os.path.relpath(root_abs, base_run_directory)

        # Print the root itself (unless already covered by a parent root)
        parent_already_printed = any(
            parent_dir
            for parent_dir in paths_in_structure
            if is_dir and root_abs.startswith(parent_dir + os.sep)
        )
        if not parent_already_printed:
            structure_lines.append(f"{rel_root}{'/' if is_dir else ''}\n")
            paths_in_structure.add(root_abs)

        if os.path.isfile(root_abs):
            files_to_include.add(root_abs)
        elif is_dir:
            _emit_tree(root_abs, root_abs, indent_level=1)

    # ---------------------------------------------------------------------
    # 3. File‑content section
    # ---------------------------------------------------------------------
    if not files_to_include:
        content_lines.append("\n--- File Contents ---\n")
        content_lines.append("(No files selected for content inclusion.)\n")
    else:
        content_lines.append("\n\n--- File Contents ---\n")

        included_count = 0

        for file_path in sorted(files_to_include):
            rel = os.path.relpath(file_path, base_run_directory)
            content_lines.append(f"\n--- File: {rel} ---\n")

            ext = os.path.splitext(file_path)[1].lower()
            if ext in config.IGNORE_EXTENSIONS:
                # Skip silently – we already have the path in the tree
                content_lines.append("(Skipped – ignored file type)\n")
                content_lines.append(f"--- END OF {rel} (SKIPPED) ---\n")
                continue

            try:
                size = os.path.getsize(file_path)
                if size > config.MAX_FILE_SIZE_BYTES:
                    mb = size / 1024**2
                    content_lines.append(
                        f"Content skipped: File size ({mb:.2f} MB) exceeds the configured maximum "
                        f"({config.MAX_FILE_SIZE_MB} MB).\n"
                    )
                    content_lines.append(f"--- END OF {rel} (SKIPPED) ---\n")
                    continue

                if size == 0:
                    content_lines.append("(This file is empty)\n")
                    content_lines.append(f"--- END OF {rel} (EMPTY) ---\n")
                    included_count += 1
                    continue

                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                    content_lines.append(f.read())
                included_count += 1
            except (
                Exception
            ) as exc:  # pylint: disable=broad-except – we want to continue on any error
                content_lines.append(f"Error reading file: {exc}\n")
            finally:
                content_lines.append(f"\n--- END OF {rel} ---\n")

    # ---------------------------------------------------------------------
    # 4. Write the file and return status
    # ---------------------------------------------------------------------
    with open(output_filename, "w", encoding="utf-8") as fh:
        fh.write("".join(structure_lines))
        fh.write("".join(content_lines))
        fh.write("\n\n--- End of Project Overview ---\n")

    return f"Output generated to {output_filename}. {len(files_to_include)} files' content included."
