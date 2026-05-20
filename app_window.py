from __future__ import annotations

import tkinter as tk


_APP_ROOT: tk.Tk | None = None


def get_app_root() -> tk.Tk:
    global _APP_ROOT
    if _APP_ROOT is None or not _APP_ROOT.winfo_exists():
        _APP_ROOT = tk.Tk()
        _APP_ROOT.withdraw()
    return _APP_ROOT


class AppWindow(tk.Toplevel):
    def __init__(self, *args, **kwargs):
        super().__init__(get_app_root(), *args, **kwargs)
        self._app_fullscreen = False

    def attributes(self, *args):
        if args and args[0] == "-fullscreen":
            if len(args) == 1:
                return self._app_fullscreen

            enabled = bool(args[1])
            self._app_fullscreen = enabled
            if enabled:
                self.overrideredirect(False)
                width = self.winfo_screenwidth()
                height = self.winfo_screenheight()
                self.geometry(f"{width}x{height}+0+0")
                self.after(50, self._focus_window)
            return None

        return super().attributes(*args)

    def _focus_window(self):
        try:
            self.deiconify()
            self.lift()
            self.focus_force()
        except Exception:
            pass

    def destroy(self):
        root = get_app_root()
        try:
            super().destroy()
        finally:
            visible_windows = [
                child for child in root.winfo_children()
                if isinstance(child, tk.Toplevel) and child.winfo_exists()
            ]
            if not visible_windows:
                root.after_idle(root.quit)
