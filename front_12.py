import tkinter as tk
from tkinter import messagebox


def _round_rect(cv, x1, y1, x2, y2, radius=25, **kwargs):
    """Draw a rounded rectangle using arcs for true rounded corners."""
    d = 2 * radius
    kwargs["outline"] = kwargs.get("outline", kwargs.get("fill", ""))
    fill = kwargs.get("fill", "")
    outline = kwargs.get("outline", fill)
    items = []
    items.append(cv.create_rectangle(x1 + radius, y1, x2 - radius, y2, fill=fill, outline=fill))
    items.append(cv.create_rectangle(x1, y1 + radius, x2, y2 - radius, fill=fill, outline=fill))
    items.append(cv.create_arc(x1, y1, x1 + d, y1 + d, start=90, extent=90, style='pieslice', fill=fill, outline=fill))
    items.append(cv.create_arc(x2 - d, y1, x2, y1 + d, start=0, extent=90, style='pieslice', fill=fill, outline=fill))
    items.append(cv.create_arc(x2 - d, y2 - d, x2, y2, start=270, extent=90, style='pieslice', fill=fill, outline=fill))
    items.append(cv.create_arc(x1, y2 - d, x1 + d, y2, start=180, extent=90, style='pieslice', fill=fill, outline=fill))
    return tuple(items)


class NewStaffPopup(tk.Toplevel):
    """
    Popup dialog for adding new staff.
    Matches the Pet&Bed dashboard design system.

    Usage:
        popup = NewStaffPopup(parent, scale=1.0)
        parent.wait_window(popup)
        result = popup.result  # {"phone": "...", "name": "..."} or None
    """

    # Design constants (base 1200×850)
    C_BG        = "#F2D5D5"
    C_WHITE     = "#FFFFFF"
    C_TEXT      = "#4A3525"
    C_TEXT_LIGHT = "#7A685F"
    C_DARK_BTN  = "#4A3525"
    C_INPUT_BG  = "#F7F7F7"
    C_INPUT_BD  = "#D9D0CB"

    # Base popup size
    BASE_W = 400
    BASE_H = 340

    def __init__(self, parent, scale: float = 1.0):
        super().__init__(parent)
        self.result = None
        self._s = scale

        s = scale
        W = int(self.BASE_W * s)
        H = int(self.BASE_H * s)

        # ── Window chrome ──────────────────────────────────────────────
        self.title("")
        self.resizable(False, False)
        self.configure(bg=self.C_BG)
        self.overrideredirect(True)   # borderless, just like the card in screenshot

        # Centre over parent
        self.update_idletasks()
        px = parent.winfo_rootx() + parent.winfo_width()  // 2 - W // 2
        py = parent.winfo_rooty() + parent.winfo_height() // 2 - H // 2
        self.geometry(f"{W}x{H}+{px}+{py}")

        # ── Fonts (same logic as PetDashboard, "Booking" size = F_NAV) ──
        nav_size  = max(10, int(18 * s))   # same as F_NAV / sidebar booking size
        lbl_size  = max(10, int(15 * s))   # slightly smaller for field labels
        btn_size  = max(12, int(18 * s))
        title_size = max(12, int(20 * s))

        F_TITLE  = ("Arial Rounded MT Bold", title_size, "bold")
        F_LABEL  = ("Baghdad", lbl_size, "bold")
        F_INPUT  = ("Baghdad", nav_size)
        F_HINT   = ("Baghdad", nav_size)
        F_BTN    = ("Arial Rounded MT Bold", btn_size, "bold")

        # ── Canvas (draws the white card + divider) ─────────────────────
        cv = tk.Canvas(self, width=W, height=H,
                       bg=self.C_BG, highlightthickness=0)
        cv.pack(fill=tk.BOTH, expand=True)

        pad = int(20 * s)
        card_r = int(20 * s)

        # White card background
        _round_rect(cv, pad, pad, W - pad, H - pad,
                    radius=card_r, fill=self.C_WHITE)

        # Title
        title_y = int(55 * s)
        cv.create_text(int(40 * s), title_y,
                       text="New staff",
                       font=F_TITLE, fill=self.C_TEXT, anchor="w")

        # Divider under title
        div_y = int(75 * s)
        cv.create_line(int(35 * s), div_y, W - int(35 * s), div_y,
                       fill=self.C_INPUT_BD, width=max(1, int(1 * s)))

        # ── Helper: draw a labelled text-entry field ────────────────────
        def make_field(label_text, placeholder, field_y, var):
            lbl_y = field_y
            cv.create_text(int(40 * s), lbl_y,
                           text=label_text,
                           font=F_LABEL, fill=self.C_TEXT, anchor="w")

            input_x1 = int(35 * s)
            input_y1 = lbl_y + int(18 * s)
            input_x2 = W - int(35 * s)
            input_y2 = input_y1 + int(40 * s)
            input_r  = (input_y2 - input_y1) // 2

            _round_rect(cv, input_x1, input_y1, input_x2, input_y2,
                        radius=input_r, fill=self.C_INPUT_BG)

            entry = tk.Entry(
                self,
                textvariable=var,
                font=F_INPUT,
                bg=self.C_INPUT_BG,
                fg=self.C_TEXT,
                insertbackground=self.C_TEXT,
                relief=tk.FLAT,
                bd=0,
                highlightthickness=0,
            )
            entry_w = int((input_x2 - input_x1) - 30 * s)
            entry_h = int(input_y2 - input_y1 - 8 * s)
            entry.place(x=input_x1 + int(18 * s),
                        y=input_y1 + int(4 * s),
                        width=entry_w,
                        height=entry_h)

            # Placeholder behaviour
            def _on_focus_in(e, ph=placeholder, v=var, en=entry):
                if v.get() == ph:
                    v.set("")
                    en.config(fg=self.C_TEXT)

            def _on_focus_out(e, ph=placeholder, v=var, en=entry):
                if v.get() == "":
                    v.set(ph)
                    en.config(fg=self.C_TEXT_LIGHT)

            var.set(placeholder)
            entry.config(fg=self.C_TEXT_LIGHT)
            entry.bind("<FocusIn>",  _on_focus_in)
            entry.bind("<FocusOut>", _on_focus_out)

            return entry

        # Phone field
        self.phone_var = tk.StringVar()
        phone_y = int(100 * s)
        self.phone_entry = make_field(
            "Phone number", "ex: 012345678", phone_y, self.phone_var
        )

        # Name field
        self.name_var = tk.StringVar()
        name_y = int(178 * s)
        self.name_entry = make_field(
            "Full Name", "ex: Thuy Hang", name_y, self.name_var
        )

        # ── "Add staff" button ──────────────────────────────────────────
        btn_w  = int(220 * s)
        btn_h  = int(48 * s)
        btn_cx = W // 2
        btn_y1 = int(265 * s)
        btn_y2 = btn_y1 + btn_h
        btn_x1 = btn_cx - btn_w // 2
        btn_x2 = btn_cx + btn_w // 2
        btn_r  = btn_h // 2

        _round_rect(cv, btn_x1, btn_y1, btn_x2, btn_y2,
                    radius=btn_r, fill=self.C_DARK_BTN, outline="", tags="add_btn")
        cv.create_text(btn_cx, (btn_y1 + btn_y2) // 2,
                       text="+ New staff",
                       font=F_BTN, fill=self.C_WHITE,
                       tags="add_btn")

        cv.tag_bind("add_btn", "<Button-1>", self._on_add)
        cv.tag_bind("add_btn", "<Enter>",
                    lambda e: cv.config(cursor="hand2"))
        cv.tag_bind("add_btn", "<Leave>",
                    lambda e: cv.config(cursor=""))

        # Close on Escape
        self.bind("<Escape>", lambda e: self.destroy())
        self.bind("<Return>",  self._on_add)

        # Make modal
        self.grab_set()
        self.focus_set()
        self.phone_entry.focus_set()

    # ── Callbacks ──────────────────────────────────────────────────────
    def _on_add(self, _event=None):
        phone = self.phone_var.get().strip()
        name  = self.name_var.get().strip()

        placeholders = {"ex: 012345678", "ex: Thuy Hang", ""}
        if phone in placeholders or name in placeholders:
            messagebox.showwarning(
                "Missing info",
                "Please fill in both Phone number and Full Name.",
                parent=self
            )
            return

        self.result = {"phone": phone, "name": name}
        self.destroy()


# ── Demo / standalone test ──────────────────────────────────────────────
if __name__ == "__main__":
    root = tk.Tk()
    root.title("Pet&Bed Dashboard (demo)")
    root.configure(bg="#F2D5D5")
    root.geometry("900x600")

    def open_popup():
        popup = NewStaffPopup(root, scale=1.0)
        root.wait_window(popup)
        if popup.result:
            print("New staff added:", popup.result)
        else:
            print("Cancelled")

    btn = tk.Button(
        root, text="+ New staff",
        command=open_popup,
        bg="#4A3525", fg="white",
        font=("Arial Rounded MT Bold", 18, "bold"),
        relief=tk.FLAT, padx=20, pady=10, cursor="hand2"
    )
    btn.place(relx=0.5, rely=0.5, anchor="center")

    root.mainloop()
