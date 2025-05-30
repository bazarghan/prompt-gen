# output_generator.py

import os
from datetime import datetime

import config

# --- Boilerplate Prompt for LLMs ---
BOILERPLATE_PROMPT = """The following is a detailed overview of a software project.
It includes the directory structure and the content of selected source code files.
Please analyze this information to understand the project's components, relationships, and functionality.
This context can be used to answer questions about the project, assist with debugging, suggest refactorings, or generate documentation.
"""


def _is_path_excluded_for_generation(
    path_to_check, current_selection_root_path, explicit_exclusions
):
    norm_path_to_check = os.path.normpath(path_to_check)
    norm_current_selection_root_path = os.path.normpath(current_selection_root_path)

    path_segment = norm_path_to_check
    while True:
        if path_segment in explicit_exclusions:
            return True
        if path_segment == norm_current_selection_root_path:
            break
        parent_segment = os.path.dirname(path_segment)
        if parent_segment == path_segment:
            break
        if not path_segment.startswith(norm_current_selection_root_path):
            break
        path_segment = parent_segment
    return False


def generate_output_from_selection(
    selection_roots, explicit_exclusions, output_filename="output.txt"
):
    base_run_directory = os.getcwd()

    structure_output = []
    content_output = []
    files_processed_count = 0
    files_content_included_count = 0

    paths_added_to_structure_output = set()

    structure_output.append(BOILERPLATE_PROMPT + "\n")
    structure_output.append("PROJECT CONTEXT OVERVIEW\n")
    structure_output.append("========================\n\n")

    structure_output.append(
        "SELECTION ROOTS (items explicitly chosen to start the project scan):\n"
    )
    if not selection_roots:
        structure_output.append(
            "(No specific items were chosen as selection roots for this overview.)\n"
        )
    for p_abs in sorted(list(selection_roots)):
        p_rel = os.path.relpath(os.path.normpath(p_abs), base_run_directory)
        structure_output.append(f"- {p_rel}\n")

    if explicit_exclusions:
        structure_output.append(
            "\nEXPLICIT EXCLUSIONS (items specifically excluded from the scan):\n"
        )
        for p_abs in sorted(list(explicit_exclusions)):
            p_rel = os.path.relpath(os.path.normpath(p_abs), base_run_directory)
            structure_output.append(f"- {p_rel}\n")

    structure_output.append(
        "\nCOMBINED PROJECT STRUCTURE (based on selections and exclusions):\n"
    )

    all_files_to_process_for_content = set()

    if not selection_roots:
        structure_output.append(
            "(Project structure is empty as no selection roots were defined.)\n"
        )

    for sel_root_orig_abs in sorted(list(selection_roots)):
        sel_root_abs = os.path.normpath(sel_root_orig_abs)

        if sel_root_abs in explicit_exclusions:
            continue

        is_sel_root_dir = os.path.isdir(sel_root_abs)
        display_sel_root_rel = os.path.relpath(sel_root_abs, base_run_directory)

        if sel_root_abs not in paths_added_to_structure_output:
            is_sub_path_of_other_root = False
            for processed_r_abs in paths_added_to_structure_output:
                if os.path.isdir(processed_r_abs) and sel_root_abs.startswith(
                    processed_r_abs + os.sep
                ):
                    is_sub_path_of_other_root = True
                    break
            if not is_sub_path_of_other_root:
                structure_output.append(
                    f"{display_sel_root_rel}{'/' if is_sel_root_dir else ''}\n"
                )
            paths_added_to_structure_output.add(sel_root_abs)

        if os.path.isfile(sel_root_abs):
            all_files_to_process_for_content.add(sel_root_orig_abs)
        elif is_sel_root_dir:
            for current_walk_root_abs_orig, dirs, files in os.walk(
                sel_root_abs, topdown=True
            ):
                current_walk_root_abs = os.path.normpath(current_walk_root_abs_orig)

                dirs[:] = [
                    d
                    for d in dirs
                    if not d.startswith(".") and d not in config.IGNORE_DIRS
                ]

                dirs_to_remove = []
                for d_name in dirs:
                    dir_full_path_abs = os.path.join(current_walk_root_abs_orig, d_name)
                    if _is_path_excluded_for_generation(
                        dir_full_path_abs, sel_root_abs, explicit_exclusions
                    ):
                        dirs_to_remove.append(d_name)
                for d_name in dirs_to_remove:
                    dirs.remove(d_name)

                depth = 0
                if current_walk_root_abs != sel_root_abs:
                    try:
                        if current_walk_root_abs.startswith(sel_root_abs):
                            relative_to_sel_root = os.path.relpath(
                                current_walk_root_abs, sel_root_abs
                            )
                            depth = (
                                relative_to_sel_root.count(os.sep) + 1
                                if relative_to_sel_root != "."
                                else 1
                            )
                    except ValueError:
                        depth = 0

                indent_for_children_of_current_walk_root = "    " * (depth + 1)
                indent_for_current_walk_root_dir = "    " * depth

                if current_walk_root_abs != sel_root_abs:
                    if current_walk_root_abs not in paths_added_to_structure_output:
                        structure_output.append(
                            f"{indent_for_current_walk_root_dir}├── {os.path.basename(current_walk_root_abs)}/\n"
                        )
                        paths_added_to_structure_output.add(current_walk_root_abs)

                for dir_name in sorted(dirs):
                    dir_full_path_abs_orig = os.path.join(
                        current_walk_root_abs_orig, dir_name
                    )
                    norm_dir_full_path_abs = os.path.normpath(dir_full_path_abs_orig)
                    if norm_dir_full_path_abs not in paths_added_to_structure_output:
                        structure_output.append(
                            f"{indent_for_children_of_current_walk_root}├── {dir_name}/\n"
                        )
                        paths_added_to_structure_output.add(norm_dir_full_path_abs)

                for file_name in sorted(files):
                    if file_name.startswith(".") or file_name in config.IGNORE_FILES:
                        continue

                    file_full_path_abs_orig = os.path.join(
                        current_walk_root_abs_orig, file_name
                    )
                    norm_file_full_path_abs = os.path.normpath(file_full_path_abs_orig)

                    if not _is_path_excluded_for_generation(
                        norm_file_full_path_abs, sel_root_abs, explicit_exclusions
                    ):
                        if (
                            norm_file_full_path_abs
                            not in paths_added_to_structure_output
                        ):
                            structure_output.append(
                                f"{indent_for_children_of_current_walk_root}├── {file_name}\n"
                            )
                            paths_added_to_structure_output.add(norm_file_full_path_abs)
                        all_files_to_process_for_content.add(file_full_path_abs_orig)

    # --- File Contents Section ---
    if not all_files_to_process_for_content:
        content_output.append("\n--- File Contents ---\n")
        content_output.append(
            "(No files selected or all selected files were empty/inaccessible/too large/ignored.)\n"
        )
    else:
        content_output.append(f"\n\n--- File Contents ---\n")
        for file_path_abs_orig in sorted(list(all_files_to_process_for_content)):
            files_processed_count += 1
            file_ext = os.path.splitext(file_path_abs_orig)[1].lower()
            display_path_rel = os.path.relpath(
                os.path.abspath(file_path_abs_orig), base_run_directory
            )

            if (
                file_ext in config.TARGET_EXTENSIONS
                and file_ext not in config.IGNORE_EXTENSIONS
            ):
                try:
                    file_size = os.path.getsize(file_path_abs_orig)
                    if file_size > config.MAX_FILE_SIZE_BYTES:
                        content_output.append(f"\n--- File: {display_path_rel} ---\n")
                        content_output.append(
                            f"Content skipped: File size ({file_size / (1024*1024):.2f} MB) "
                            f"exceeds maximum ({config.MAX_FILE_SIZE_MB} MB).\n"
                        )
                        content_output.append(
                            f"--- END OF {display_path_rel} (SKIPPED) ---\n"
                        )
                        continue
                    if file_size == 0:
                        content_output.append(f"\n--- File: {display_path_rel} ---\n")
                        content_output.append("(This file is empty)\n")
                        content_output.append(
                            f"--- END OF {display_path_rel} (EMPTY) ---\n"
                        )
                        files_content_included_count += 1
                        continue
                    with open(
                        file_path_abs_orig, "r", encoding="utf-8", errors="ignore"
                    ) as f_content:
                        content = f_content.read()
                    content_output.append(f"\n--- File: {display_path_rel} ---\n")
                    content_output.append(content)
                    content_output.append(f"\n--- END OF {display_path_rel} ---\n")
                    files_content_included_count += 1
                except Exception as e:
                    content_output.append(f"\n--- File: {display_path_rel} ---\n")
                    content_output.append(f"Error reading file: {e}\n")
                    content_output.append(
                        f"--- END OF {display_path_rel} (ERROR) ---\n"
                    )
            elif file_ext in config.IGNORE_EXTENSIONS:
                # This log is now removed for LLM output clarity
                # content_output.append(
                #     f"\n--- File: {display_path_rel} (Content Ignored due to extension: {file_ext}) ---\n"
                # )
                pass  # Do nothing for ignored extensions in the content section

    # --- Summary Section ---
    summary = []
    summary.append("\n\n--- End of Project Overview ---\n")

    try:
        with open(output_filename, "w", encoding="utf-8") as f_out:
            f_out.write("".join(structure_output))
            f_out.write("".join(content_output))
            f_out.write("".join(summary))
        return f"Output generated to {output_filename}. {files_content_included_count} files' content included."
    except IOError as e:
        return f"Error writing to output file '{output_filename}': {e}"
