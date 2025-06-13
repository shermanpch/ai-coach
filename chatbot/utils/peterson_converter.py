#!/usr/bin/env python3
"""
Main entry point for Peterson Data to Markdown Converter.

Run with: python chatbot/utils/peterson_converter.py
Requires: pip install -e .
"""

import sys

if __name__ == "__main__":
    try:
        from chatbot.utils.peterson_converter.core import main
    except ImportError as e:
        print(
            f"ERROR: Import failed. Run 'pip install -e .' first. Details: {e}",
            file=sys.stderr,
        )
        sys.exit(1)

    try:
        main()
    except Exception as e:
        print(f"ERROR: Conversion failed: {e}", file=sys.stderr)
        sys.exit(1)
