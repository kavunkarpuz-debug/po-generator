"""
Entry point for PO Generator v2.
- No .env config -> SetupScreen (first-run wizard)
- Config + template exist -> GenerateScreen (normal use)
"""

import sys
import tkinter as tk
from tkinter import messagebox
import traceback
import logging

from core.config import is_setup_complete
from gui.setup_screen import SetupScreen
from gui.generate_screen import GenerateScreen

# Configure logging to help debug issues in the field
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='app.log',
    filemode='a'
)

def launch_generate(root: tk.Tk):
    """Replace window contents with GenerateScreen after setup."""
    for widget in root.winfo_children():
        widget.destroy()
    root.title("PO Generator")
    GenerateScreen(root)

def main():
    try:
        root = tk.Tk()
        root.withdraw()  # hide until screen is ready

        if is_setup_complete():
            logging.info("Starting in Generation mode.")
            root.deiconify()
            GenerateScreen(root)
        else:
            logging.info("Starting in Setup mode.")
            root.deiconify()
            SetupScreen(root, on_complete_callback=lambda: launch_generate(root))

        root.mainloop()
    except Exception as e:
        error_msg = f"Uygulama beklenmedik bir hata ile karşılaştı:\n\n{str(e)}"
        logging.error(f"Uncaught exception: {traceback.format_exc()}")
        # Show error even if root is hidden
        temp_root = tk.Tk()
        temp_root.withdraw()
        messagebox.showerror("Kritik Hata", error_msg)
        sys.exit(1)

if __name__ == "__main__":
    main()
