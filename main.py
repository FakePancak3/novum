#!/usr/bin/env python3
"""
NOVUM — a compact, dark-themed auto-clicker utility.

Run with: python main.py
See README.md for setup, packaging, and architecture notes.
"""

import tkinter as tk

from gui import NovumApp


def main():
    root = tk.Tk()
    NovumApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
