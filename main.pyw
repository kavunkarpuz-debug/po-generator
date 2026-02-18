"""
Entry point for PO Generator v2.
- No config.json -> SetupScreen (first-run wizard)
- Config + template exist -> GenerateScreen (normal use)
"""

import tkinter as tk
from core.config import is_setup_complete
from gui.setup_screen import SetupScreen
from gui.generate_screen import GenerateScreen


def launch_generate(root: tk.Tk):
    """Replace window contents with GenerateScreen after setup."""
    for widget in root.winfo_children():
        widget.destroy()
    root.title("PO Generator")
    GenerateScreen(root)


def main():
    root = tk.Tk()
    root.withdraw()  # hide until screen is ready

    if is_setup_complete():
        root.deiconify()
        GenerateScreen(root)
    else:
        root.deiconify()
        SetupScreen(root, on_complete_callback=lambda: launch_generate(root))

    root.mainloop()


if __name__ == "__main__":
    main()
