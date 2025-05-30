#!/usr/bin/env python3
# main.py

import argparse
import curses
import os
import sys

from tui import tui_main  # Import the TUI main function


def main():
    parser = argparse.ArgumentParser(
        description="Interactive TUI to select project files/dirs for an overview."
    )
    parser.add_argument(
        "initial_path",
        nargs="?",
        default=".",
        help="The initial path to explore (default: current directory).",
    )

    args = parser.parse_args()

    if not os.path.isdir(args.initial_path):
        print(f"Error: Initial path '{args.initial_path}' is not a valid directory.")
        sys.exit(1)

    try:
        curses.wrapper(tui_main, args.initial_path)
        print("Exited TUI. If output was generated, it's typically in 'output.txt'.")
    except curses.error as e:
        print(f"Curses error: {e}")
        print("Your terminal might not be fully compatible or might be too small.")
    except KeyboardInterrupt:
        print("\nExiting...")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")


if __name__ == "__main__":
    main()
