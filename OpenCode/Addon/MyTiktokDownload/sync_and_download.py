#!/usr/bin/env python3
"""
TikTok Download Manager - Entry point
Uu tien mo GUI. Neu khong co man hinh, chuyen sang menu CLI.
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

def main():
    # Thu mo GUI
    try:
        import tkinter as tk
        root = tk.Tk()
        root.destroy()  # Test co the mo cua so khong
        from gui_manager import launch_gui
        launch_gui()
    except Exception:
        # Fallback: menu CLI
        from main import main as cli_main
        import argparse
        sys.argv = [sys.argv[0]]
        cli_main()

if __name__ == "__main__":
    main()