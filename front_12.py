import tkinter as tk
from tkinter import messagebox

from PIL import Image, ImageTk, ImageDraw

from app_window import AppWindow
from database import DatabaseConnection


class NewStaffBackend:
    DEFAULT_ROLE = "parttime"
    DEFAULT_BASE_SALARY = 200000

    def __init__(self, db=None):
        self.db = db or DatabaseConnection()

    @staticmethod
    def _clean(value):
        return (value or "").strip()

    @staticmethod
    def _is_placeholder(value, placeholder):
        return (value or "").strip().lower() == placeholder.lower()

    def add_staff(self, phone, full_name):
        phone = self._clean(phone)
        full_name = self._clean(full_name)

        if self._is_placeholder(phone, "ex: 012345678"):
            phone = ""
        if self._is_placeholder(full_name, "ex: Thuy Hang"):
            full_name = ""

        if not phone or not full_name:
            raise ValueError("Phone number and full name are required")
        if not phone.isdigit() or not 9 <= len(phone) <= 15:
            raise ValueError("Phone number must be 9-15 digits")

        existing = self.db.fetch_one(
            "SELECT employee_id FROM employees WHERE phone = %s LIMIT 1",
            (phone,),
        )
        if existing:
            employee_id = existing["employee_id"]
            self.db.execute(
                """
                UPDATE employees
                SET full_name = %s,
                    role = COALESCE(NULLIF(role, ''), %s),
                    base_salary_per_hour = COALESCE(base_salary_per_hour, %s),
                    is_active = b'1'
                WHERE employee_id = %s
                """,
                (full_name, self.DEFAULT_ROLE, self.DEFAULT_BASE_SALARY, employee_id),
            )
            return {"employee_id": employee_id, "updated": True}

        employee_id = self.db.execute(
            """
            INSERT INTO employees (full_name, role, phone, base_salary_per_hour, is_active)
            VALUES (%s, %s, %s, %s, b'1')
            """,
            (full_name, self.DEFAULT_ROLE, phone, self.DEFAULT_BASE_SALARY),
        )
        return {"employee_id": employee_id, "updated": False}


# =========================
# Rounded Rectangle (pieslice - mượt hơn)
# =========================
def _round_rect(cv, x1, y1, x2, y2, radius=25, **kwargs):
    d = 2 * radius
    outline = kwargs.pop("outline", kwargs.get("fill", ""))
    fill    = kwargs.get("fill", "")
    width   = kwargs.pop("width", 1)
    kw = {"fill": fill, "outline": outline, "width": width}
    cv.create_rectangle(x1 + radius, y1, x2 - radius, y2, **kw)
    cv.create_rectangle(x1, y1 + radius, x2, y2 - radius, **kw)
    cv.create_arc(x1,      y1,      x1+d, y1+d, start=90,  extent=90,  style="pieslice", **kw)
    cv.create_arc(x2-d,    y1,      x2,   y1+d, start=0,   extent=90,  style="pieslice", **kw)
    cv.create_arc(x2-d,    y2-d,    x2,   y2,   start=270, extent=90,  style="pieslice", **kw)
    cv.create_arc(x1,      y2-d,    x1+d, y2,   start=180, extent=90,  style="pieslice", **kw)


def _round_rect_outline(cv, x1, y1, x2, y2, radius=20, color="#D7D0CB", lw=1):
    d = 2 * radius
    cv.create_arc(x1,   y1,   x1+d, y1+d, start=90,  extent=90,  style=tk.ARC, outline=color, width=lw)
    cv.create_arc(x2-d, y1,   x2,   y1+d, start=0,   extent=90,  style=tk.ARC, outline=color, width=lw)
    cv.create_arc(x2-d, y2-d, x2,   y2,   start=270, extent=90,  style=tk.ARC, outline=color, width=lw)
    cv.create_arc(x1,   y2-d, x1+d, y2,   start=180, extent=90,  style=tk.ARC, outline=color, width=lw)
    cv.create_line(x1+radius, y1,   x2-radius, y1,   fill=color, width=lw)
    cv.create_line(x2,        y1+radius, x2,   y2-radius, fill=color, width=lw)
    cv.create_line(x1+radius, y2,   x2-radius, y2,   fill=color, width=lw)
    cv.create_line(x1,        y1+radius, x1,   y2-radius, fill=color, width=lw)


# =========================
# APP
# =========================
class NewStaffPopup(AppWindow):

    def __init__(self):
        super().__init__()
        self.backend = NewStaffBackend()

        # ===== WINDOW (Thu nhỏ vừa vặn) =====
        WIDTH  = 540
        HEIGHT = 420

        self.title("New Staff")
        self.geometry(f"{WIDTH}x{HEIGHT}")
        self.configure(bg="#A8D3CF")
        self.resizable(False, False)

        # Center on screen
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        x = (sw - WIDTH) // 2
        y = (sh - HEIGHT) // 2
        self.geometry(f"{WIDTH}x{HEIGHT}+{x}+{y}")

        # ===== COLORS =====
        C_BG     = "#A8D3CF"
        C_WHITE  = "#FFFFFF"
        C_TEXT   = "#4A3525"
        C_BORDER = "#D7D0CB"
        C_PLACE  = "#B6AEA9"
        C_BTN    = "#68BBB2"

        # ===== CANVAS =====
        cv = tk.Canvas(self, width=WIDTH, height=HEIGHT,
                       bg=C_BG, highlightthickness=0)
        cv.pack(fill="both", expand=True)
        self._cv = cv

        # ===== CARD =====
        PAD   = 15          # margin around card
        CX1   = PAD
        CY1   = PAD
        CX2   = WIDTH  - PAD
        CY2   = HEIGHT - PAD

        _round_rect(cv, CX1, CY1, CX2, CY2, radius=28,
                    fill=C_WHITE, outline="")

        # Inner horizontal padding inside card
        IP = 35             # left/right inner padding

        # ───── TITLE (Cỡ chữ ngang Booking = 18pt) ─────
        title_y = CY1 + 38
        cv.create_text(CX1 + IP, title_y,
                       text="New staff", anchor="w",
                       fill=C_TEXT,
                       font=("Arial Rounded MT Bold", 18, "bold"))

        # Divider
        div_y = title_y + 24
        cv.create_line(CX1 + IP, div_y, CX2 - IP, div_y,
                       fill="#DCD6D2", width=1)

        # ───── PHONE LABEL (Size 18pt) ─────
        lbl1_y = div_y + 28
        cv.create_text(CX1 + IP, lbl1_y,
                       text="Phone number", anchor="w",
                       fill=C_TEXT,
                       font=("Baghdad", 18, "bold"))

        # Phone input box
        box1_y1 = lbl1_y + 12
        box1_y2 = box1_y1 + 44
        box1_x1 = CX1 + IP - 4
        box1_x2 = CX2 - IP + 4

        _round_rect(cv, box1_x1, box1_y1, box1_x2, box1_y2,
                    radius=22, fill=C_WHITE, outline="")
        _round_rect_outline(cv, box1_x1, box1_y1, box1_x2, box1_y2,
                            radius=22, color=C_BORDER, lw=1)

        self.phone_entry = tk.Entry(
            self, bd=0, relief="flat",
            bg=C_WHITE, fg=C_PLACE,
            font=("Baghdad", 18),
            insertbackground=C_TEXT,
            highlightthickness=0
        )
        self.phone_entry.insert(0, "ex: 012345678")
        self.phone_entry.place(
            x=box1_x1 + 20,
            y=(box1_y1 + box1_y2) // 2 - 12,
            width=box1_x2 - box1_x1 - 40,
            height=24
        )

        # ───── FULL NAME LABEL (Size 18pt) ─────
        lbl2_y = box1_y2 + 22
        cv.create_text(CX1 + IP, lbl2_y,
                       text="Full Name", anchor="w",
                       fill=C_TEXT,
                       font=("Baghdad", 18, "bold"))

        # Name input box
        box2_y1 = lbl2_y + 12
        box2_y2 = box2_y1 + 44
        box2_x1 = box1_x1
        box2_x2 = box1_x2

        _round_rect(cv, box2_x1, box2_y1, box2_x2, box2_y2,
                    radius=22, fill=C_WHITE, outline="")
        _round_rect_outline(cv, box2_x1, box2_y1, box2_x2, box2_y2,
                            radius=22, color=C_BORDER, lw=1)

        self.name_entry = tk.Entry(
            self, bd=0, relief="flat",
            bg=C_WHITE, fg=C_PLACE,
            font=("Baghdad", 18),
            insertbackground=C_TEXT,
            highlightthickness=0
        )
        self.name_entry.insert(0, "ex: Thuy Hang")
        self.name_entry.place(
            x=box2_x1 + 20,
            y=(box2_y1 + box2_y2) // 2 - 12,
            width=box2_x2 - box2_x1 - 40,
            height=24
        )

        # ───── ADD STAFF BUTTON ─────
        btn_w  = 180
        btn_h  = 44
        btn_cx = WIDTH // 2
        btn_y1 = box2_y2 + 24
        btn_y2 = btn_y1 + btn_h
        btn_x1 = btn_cx - btn_w // 2
        btn_x2 = btn_cx + btn_w // 2

        _round_rect(cv, btn_x1, btn_y1, btn_x2, btn_y2,
                    radius=btn_h // 2, fill=C_BTN, outline="",
                    tags="add_btn")

        cv.create_text(btn_cx, (btn_y1 + btn_y2) // 2,
                       text="Add staff", fill=C_WHITE,
                       font=("Arial Rounded MT Bold", 18, "bold"),
                       tags="add_btn")

        cv.tag_bind("add_btn", "<Button-1>", self.add_staff)
        self.bind("<Escape>", lambda e: self.destroy())

    # =========================
    def add_staff(self, event=None):
        try:
            result = self.backend.add_staff(
                self.phone_entry.get(),
                self.name_entry.get(),
            )
            action = "updated" if result["updated"] else "added"
            messagebox.showinfo(
                "Success",
                f"Staff #{result['employee_id']} {action} successfully.",
                parent=self,
            )
            self.destroy()
        except Exception as exc:
            messagebox.showerror("Add staff failed", str(exc), parent=self)


# =========================
# RUN
# =========================
if __name__ == "__main__":
    app = NewStaffPopup()
    app.mainloop()
