# Prompt-Gen CLI

**Prompt-Gen CLI** is an interactive command-line tool designed to help developers and users generate comprehensive project overviews. By navigating your project structure in a Text-based User Interface (TUI), you can select specific files and directories. The tool then compiles their structure and content into a single `output.txt` file, formatted to be an effective context prompt for Large Language Models (LLMs).

This allows you to easily provide LLMs with the necessary background information for tasks like code analysis, documentation generation, debugging assistance, and more.

The project is hosted at: [github.com/bazarghan/prompt-gen](https://github.com/bazarghan/prompt-gen)

## Features

- **Interactive TUI:** Easily browse and select files/directories using a curses-based interface.
- **Recursive Selection:** Select a folder to include all its contents.
- **Granular Exclusion:** Deselect specific sub-folders or files within a selected folder to fine-tune the output.
- **Customizable Keybindings:** Configure your preferred keys for navigation and actions via a `keybinds.json` file.
- **LLM-Optimized Output:** Generates an `output.txt` with a boilerplate prompt, relative file paths, project structure, and selected file contents.
- **Cross-Platform:** Works on Linux, macOS, and Windows (requires a compatible terminal for curses).
- **Configurable Content:** Ignores common binary files, logs, and `node_modules`-like directories by default (configurable in `config.py`).

## Prerequisites

- **Python 3:** Version 3.7 or newer is recommended.
- **pip:** Python's package installer (usually comes with Python).

## Installation

1.  **Clone the repository:**

    ```bash
    git clone [https://github.com/bazarghan/prompt-gen.git](https://github.com/bazarghan/prompt-gen.git)
    ```

2.  **Navigate to the project directory:**

    ```bash
    cd prompt-gen
    ```

3.  **Install the tool:**
    It's highly recommended to use a Python virtual environment:

    ```bash
    # Create a virtual environment (e.g., named .venv)
    python3 -m venv .venv

    # Activate it:
    # On macOS/Linux:
    source .venv/bin/activate
    # On Windows (Command Prompt):
    # .venv\Scripts\activate.bat
    # On Windows (PowerShell):
    # .venv\Scripts\Activate.ps1

    # Install the tool (and its dependencies, if any were defined)
    pip install .
    ```

    For development, you can install it in editable mode:

    ```bash
    pip install -e .
    ```

## Usage

Once installed, the command `project-lister` will be available in your terminal.

- **Run in the current directory:**

  ```bash
  project-lister
  ```

- **Run with a specific initial path:**
  ```bash
  project-lister /path/to/your/project
  ```

The TUI will launch, allowing you to:

- Navigate using the configured keys (defaults: Arrow keys, `k`/`j` for up/down, `l`/Enter for entering directories, `h` for parent directory - check `keybinds.json` for current settings).
- Press `Space` (or configured key) to toggle selection for the highlighted item.
  - Selecting a folder marks it as a "selection root," implicitly selecting all its contents.
  - Pressing `Space` again on a selected item within a root folder will mark it as an "explicit exclusion."
- Press `g` (or configured key) to generate the `output.txt` file.
- Press `q` (or configured key) to quit.

## Configuration

### Keybindings

Keybindings are configurable via a `keybinds.json` file.

- When you first run `project-lister` in a directory where `keybinds.json` does not exist, a default `keybinds.json` file will be created in that **current working directory**.
- You can edit this JSON file to customize the keys for various actions.
- The TUI will display the currently active keybindings in the instruction bar.

### Content Inclusion/Exclusion

Default ignored directories, files, and extensions, as well as the max file size for content inclusion, are defined in `config.py`. You can modify this file directly if you need to change these defaults globally for your installation.

## Output

The tool generates an `output.txt` file in the **current working directory** from where `project-lister` was executed. This file includes:

1.  A boilerplate prompt explaining the content to an LLM.
2.  A list of the selection roots and explicit exclusions (using relative paths).
3.  The combined project structure (using relative paths).
4.  The content of all selected files that meet the criteria (not too large, not an ignored extension, etc.).

## Contributing

Contributions are welcome! If you have suggestions for improvements or find a bug, please feel free to:

1.  Fork the repository.
2.  Create a new branch (`git checkout -b feature/YourFeature` or `bugfix/YourBug`).
3.  Make your changes.
4.  Commit your changes (`git commit -m 'Add some feature'`).
5.  Push to the branch (`git push origin feature/YourFeature`).
6.  Open a Pull Request.

Please ensure your code follows general Python best practices.

## License

This project is licensed under the MIT License - see the license specified in `pyproject.toml`.
