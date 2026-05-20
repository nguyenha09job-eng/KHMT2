import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk, ImageDraw
import os
import sys
from datetime import datetime
from decimal import Decimal

from database import DatabaseConnection
from navigation import bind_click, bind_nav_item, logout_to_login, open_popup, switch_to


class StaffBackend:
    def __init__(self, db=None):
        self.db = db or DatabaseConnection()

    @staticmethod
    def _money(value):
        if value is None:
            value = 0
        if isinstance(value, Decimal):
            value = int(value)
        return f"{int(value):,}đ"

    @staticmethod
    def _hours(value):
        if value is None:
            return 0.0
        return float(value)

    @staticmethod
    def _role_label(role):
        labels = {
            "manager": "Manager",
            "fulltime": "Fulltime",
            "parttime": "Partime",
        }
        return labels.get(str(role or "").lower(), str(role or "-").title())

    @staticmethod
    def _time(value):
        if not value:
            return "-"
        return value.strftime("%H:%M")

    @staticmethod
    def _emp_code(employee_id):
        try:
            return f"EMP{int(employee_id):03d}"
        except (TypeError, ValueError):
            return "EMP---"

    def _active_where(self):
        return "(is_active = 1 OR is_active = b'1')"

    def get_employees(self, limit=5):
        rows = self.db.fetch_all(
            f"""
            SELECT
                e.employee_id,
                e.full_name,
                e.role,
                e.phone,
                e.base_salary_per_hour,
                COALESCE(SUM(CASE
                    WHEN YEAR(a.work_date) = YEAR(CURDATE())
                     AND MONTH(a.work_date) = MONTH(CURDATE())
                    THEN a.penalty ELSE 0 END), 0) AS month_penalty
            FROM employees e
            LEFT JOIN attendance a ON a.employee_id = e.employee_id
            WHERE {self._active_where()}
            GROUP BY e.employee_id, e.full_name, e.role, e.phone, e.base_salary_per_hour
            ORDER BY
                CASE LOWER(e.role)
                    WHEN 'manager' THEN 0
                    WHEN 'fulltime' THEN 1
                    WHEN 'parttime' THEN 2
                    ELSE 3
                END,
                e.employee_id
            LIMIT %s
            """,
            (limit,),
        )
        staff = []
        for row in rows or []:
            penalty = int(row.get("month_penalty") or 0)
            role = row.get("role")
            chip = self._role_label(role)
            staff.append({
                "employee_id": row.get("employee_id"),
                "name": row.get("full_name") or "-",
                "emp": self._emp_code(row.get("employee_id")),
                "phone": row.get("phone") or "-",
                "role": role,
                "chip": chip,
                "has_penalty": penalty > 0,
            })
        return staff

    def get_summary(self):
        row = self.db.fetch_one(
            f"""
            SELECT
                COUNT(*) AS total_employees,
                SUM(CASE WHEN LOWER(role) = 'manager' THEN 1 ELSE 0 END) AS managers,
                SUM(CASE WHEN LOWER(role) = 'parttime' THEN 1 ELSE 0 END) AS parttime,
                SUM(CASE WHEN LOWER(role) = 'fulltime' THEN 1 ELSE 0 END) AS fulltime
            FROM employees
            WHERE {self._active_where()}
            """
        ) or {}
        present = self.db.fetch_one(
            """
            SELECT COUNT(DISTINCT employee_id) AS present_today
            FROM attendance
            WHERE work_date = CURDATE()
            """
        ) or {}
        month = self.db.fetch_one(
            f"""
            SELECT
                COALESCE(SUM(a.working_hours), 0) AS working_hours,
                COALESCE(SUM((a.working_hours + COALESCE(a.overtime_hours, 0))
                    * e.base_salary_per_hour - COALESCE(a.penalty, 0)), 0) AS salary_total
            FROM attendance a
            JOIN employees e ON e.employee_id = a.employee_id
            WHERE YEAR(a.work_date) = YEAR(CURDATE())
              AND MONTH(a.work_date) = MONTH(CURDATE())
              AND {self._active_where().replace('is_active', 'e.is_active')}
            """
        ) or {}

        total = int(row.get("total_employees") or 0)
        managers = int(row.get("managers") or 0)
        parttime = int(row.get("parttime") or 0)
        fulltime = int(row.get("fulltime") or 0)
        expected_today = max(total - managers, 0) or total
        salary_total = int(month.get("salary_total") or 0)
        salary_million = salary_total / 1_000_000
        salary_big = f"{salary_million:.1f}".rstrip("0").rstrip(".")

        return {
            "total": total,
            "role_sub": f"{parttime} partime - {fulltime} fulltime - {managers} manager",
            "present_today": int(present.get("present_today") or 0),
            "expected_today": expected_today,
            "salary_big": salary_big,
            "working_hours": int(round(self._hours(month.get("working_hours")))),
        }

    def get_focus_attendance(self):
        row = self.db.fetch_one(
            f"""
            SELECT
                a.attendance_id,
                a.employee_id,
                e.full_name,
                e.role,
                e.base_salary_per_hour,
                a.check_in,
                a.check_out,
                a.working_hours,
                a.overtime_hours,
                a.penalty,
                a.note
            FROM attendance a
            JOIN employees e ON e.employee_id = a.employee_id
            WHERE a.work_date = CURDATE()
              AND {self._active_where().replace('is_active', 'e.is_active')}
            ORDER BY
                CASE LOWER(e.role) WHEN 'manager' THEN 1 ELSE 0 END,
                a.attendance_id DESC
            LIMIT 1
            """
        )
        if not row:
            return None

        employee_id = row.get("employee_id")
        salary = self.get_salary_breakdown(employee_id)
        working = self._hours(row.get("working_hours"))
        overtime = self._hours(row.get("overtime_hours"))
        penalty = int(row.get("penalty") or 0)
        return {
            "name": row.get("full_name") or "-",
            "emp": self._emp_code(employee_id),
            "present": True,
            "clock_in": self._time(row.get("check_in")),
            "clock_out": self._time(row.get("check_out")),
            "working_hour": f"{working:g} hours",
            "overtime_hour": f"{overtime:g} hours",
            "penalty": self._money(penalty),
            "note": row.get("note") or "Good job",
            "salary": salary,
        }

    def get_salary_breakdown(self, employee_id):
        periods = {
            "Day": "a.work_date = CURDATE()",
            "Week": "YEARWEEK(a.work_date, 1) = YEARWEEK(CURDATE(), 1)",
            "Month": "YEAR(a.work_date) = YEAR(CURDATE()) AND MONTH(a.work_date) = MONTH(CURDATE())",
        }
        result = {}
        for label, where_clause in periods.items():
            row = self.db.fetch_one(
                f"""
                SELECT COALESCE(SUM((a.working_hours + COALESCE(a.overtime_hours, 0))
                    * e.base_salary_per_hour - COALESCE(a.penalty, 0)), 0) AS salary
                FROM attendance a
                JOIN employees e ON e.employee_id = a.employee_id
                WHERE a.employee_id = %s AND {where_clause}
                """,
                (employee_id,),
            ) or {}
            result[label] = self._money(row.get("salary"))
        return result

    def get_data(self):
        try:
            employees = self.get_employees()
            return {
                "summary": self.get_summary(),
                "staff_list": employees,
                "focus_attendance": self.get_focus_attendance(),
                "month_label": datetime.now().strftime("%m/%Y"),
                "manager_name": next(
                    (item["name"] for item in employees
                     if str(item.get("role") or "").lower() == "manager"),
                    employees[0]["name"] if employees else "Staff",
                ),
            }
        except Exception as exc:
            print(f"Staff backend error: {exc}")
            return self.fallback_data()

    def fallback_data(self):
        return {
            "summary": {
                "total": 0,
                "role_sub": "0 partime - 0 fulltime - 0 manager",
                "present_today": 0,
                "expected_today": 0,
                "salary_big": "0",
                "working_hours": 0,
            },
            "staff_list": [],
            "focus_attendance": None,
            "month_label": datetime.now().strftime("%m/%Y"),
            "manager_name": "Staff",
        }


def _round_rect(cv, x1, y1, x2, y2, radius=25, **kwargs):
    d = 2 * radius
    kwargs["outline"] = kwargs.get("outline", kwargs.get("fill", ""))
    fill = kwargs.get("fill", "")
    outline = kwargs.get("outline", "")
    width = kwargs.get("width", 1)

    # Build clean kwargs for each call
    rect_kw = {"fill": fill, "outline": outline, "width": width}
    arc_kw = {"fill": fill, "outline": outline, "width": width}

    items = []
    items.append(cv.create_rectangle(x1 + radius, y1, x2 - radius, y2, **rect_kw))
    items.append(cv.create_rectangle(x1, y1 + radius, x2, y2 - radius, **rect_kw))
    items.append(cv.create_arc(x1, y1, x1 + d, y1 + d, start=90, extent=90, style='pieslice', **arc_kw))
    items.append(cv.create_arc(x2 - d, y1, x2, y1 + d, start=0, extent=90, style='pieslice', **arc_kw))
    items.append(cv.create_arc(x2 - d, y2 - d, x2, y2, start=270, extent=90, style='pieslice', **arc_kw))
    items.append(cv.create_arc(x1, y2 - d, x1 + d, y2, start=180, extent=90, style='pieslice', **arc_kw))
    return tuple(items)


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


class PenaltyPopup(tk.Toplevel):
    def __init__(self, parent, employee_id, emp_name, db, callback):
        super().__init__(parent)
        self.employee_id = employee_id
        self.emp_name = emp_name
        self.db = db
        self.callback = callback

        # ===== WINDOW (Thu nhỏ vừa vặn) =====
        WIDTH  = 540
        HEIGHT = 380

        self.title("Add Penalty")
        self.geometry(f"{WIDTH}x{HEIGHT}")
        self.configure(bg="#A8D3CF")
        self.resizable(False, False)

        # Center on screen relative to parent
        parent_x = parent.winfo_x()
        parent_y = parent.winfo_y()
        parent_w = parent.winfo_width()
        parent_h = parent.winfo_height()
        x = parent_x + (parent_w - WIDTH) // 2
        y = parent_y + (parent_h - HEIGHT) // 2
        self.geometry(f"{WIDTH}x{HEIGHT}+{x}+{y}")
        self.transient(parent)
        self.grab_set()

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

        # ===== CARD =====
        PAD   = 15          # margin around card
        CX1   = PAD
        CY1   = PAD
        CX2   = WIDTH  - PAD
        CY2   = HEIGHT - PAD

        _round_rect(cv, CX1, CY1, CX2, CY2, radius=28,
                    fill=C_WHITE, outline="")

        IP = 35             # left/right inner padding

        # ───── TITLE ─────
        title_y = CY1 + 38
        cv.create_text(CX1 + IP, title_y,
                       text="Add Penalty", anchor="w",
                       fill=C_TEXT,
                       font=("Arial Rounded MT Bold", 18, "bold"))

        # Divider
        div_y = title_y + 24
        cv.create_line(CX1 + IP, div_y, CX2 - IP, div_y,
                       fill="#DCD6D2", width=1)

        # ───── EMPLOYEE INFO ─────
        name_y = div_y + 26
        cv.create_text(CX1 + IP, name_y,
                       text=f"Employee: {self.emp_name}", anchor="w",
                       fill="#7A685F",
                       font=("Baghdad", 16))

        # ───── AMOUNT LABEL ─────
        lbl_y = name_y + 36
        cv.create_text(CX1 + IP, lbl_y,
                       text="Amount (VND)", anchor="w",
                       fill=C_TEXT,
                       font=("Baghdad", 18, "bold"))

        # Amount input box
        box_y1 = lbl_y + 12
        box_y2 = box_y1 + 44
        box_x1 = CX1 + IP - 4
        box_x2 = CX2 - IP + 4

        _round_rect(cv, box_x1, box_y1, box_x2, box_y2,
                    radius=22, fill=C_WHITE, outline="")
        _round_rect_outline(cv, box_x1, box_y1, box_x2, box_y2,
                            radius=22, color=C_BORDER, lw=1)

        self.amount_entry = tk.Entry(
            self, bd=0, relief="flat",
            bg=C_WHITE, fg=C_TEXT,
            font=("Baghdad", 18),
            insertbackground=C_TEXT,
            highlightthickness=0
        )
        self.amount_entry.insert(0, "50000")
        self.amount_entry.place(
            x=box_x1 + 20,
            y=(box_y1 + box_y2) // 2 - 12,
            width=box_x2 - box_x1 - 40,
            height=24
        )
        self.amount_entry.focus_set()

        # ───── SAVE BUTTON ─────
        btn_w  = 180
        btn_h  = 44
        btn_cx = WIDTH // 2
        btn_y1 = box_y2 + 28
        btn_y2 = btn_y1 + btn_h
        btn_x1 = btn_cx - btn_w // 2
        btn_x2 = btn_cx + btn_w // 2

        _round_rect(cv, btn_x1, btn_y1, btn_x2, btn_y2,
                    radius=btn_h // 2, fill=C_BTN, outline="",
                    tags="save_btn")

        cv.create_text(btn_cx, (btn_y1 + btn_y2) // 2,
                       text="Add Penalty", fill=C_WHITE,
                       font=("Arial Rounded MT Bold", 18, "bold"),
                       tags="save_btn")

        cv.tag_bind("save_btn", "<Button-1>", self.save)
        cv.tag_bind("save_btn", "<Enter>", lambda e: cv.config(cursor="hand2"))
        cv.tag_bind("save_btn", "<Leave>", lambda e: cv.config(cursor=""))
        self.bind("<Escape>", lambda e: self.destroy())

    def save(self, event=None):
        val_str = self.amount_entry.get().strip()
        try:
            val = int(val_str)
            if val <= 0:
                raise ValueError()
        except ValueError:
            messagebox.showerror("Error", "Please enter a valid positive number for the penalty amount.", parent=self)
            return

        try:
            # First check if attendance exists for today
            exists = self.db.fetch_one(
                "SELECT attendance_id FROM attendance WHERE employee_id = %s AND work_date = CURDATE()",
                (self.employee_id,)
            )
            if exists:
                self.db.execute(
                    "UPDATE attendance SET penalty = COALESCE(penalty, 0) + %s WHERE employee_id = %s AND work_date = CURDATE()",
                    (val, self.employee_id)
                )
            else:
                self.db.execute(
                    "INSERT INTO attendance (employee_id, work_date, penalty, clock_in, clock_out) VALUES (%s, CURDATE(), %s, '09:00:00', '17:00:00')",
                    (self.employee_id, val)
                )

            messagebox.showinfo("Success", f"Successfully added {val:,}đ penalty for {self.emp_name}!", parent=self)
            self.destroy()
            self.callback()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to add penalty: {e}", parent=self)


class StaffPage(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Pet&Bed - Staff")
        self.attributes("-fullscreen", True)
        self.configure(bg="#A8D3CF")
        self.update_idletasks()

        self.W = self.winfo_width()
        self.H = self.winfo_height()
        self.BASE_W = 1200.0
        self.BASE_H = 850.0
        self._s = self.W / self.BASE_W
        s = self._s
        self.Y_OFF = 20

        # ── Colors ──────────────────────────────────────────
        self.C_BG           = "#A8D3CF"
        self.C_SIDEBAR      = "#FFFFFF"
        self.C_TEXT         = "#4A3525"
        self.C_TEXT_LIGHT   = "#7A685F"
        self.C_WHITE        = "#FFFFFF"
        self.C_ACTIVE       = "#68BBB2"
        self.C_DIVIDER      = "#DDD8D2"
        self.C_GREEN_BG     = "#D4EDBA"
        self.C_GREEN_FG     = "#5A8A1A"
        self.C_PINK_BG      = "#F8D7E0"
        self.C_PINK_FG      = "#C05070"
        self.C_BORDER       = "#C8C2BC"
        self.C_CARD         = "#FFFFFF"
        self.C_DARK_BTN     = "#4A3525"
        self.C_WEEK_CHIP    = "#D4EDBA"

        # ── Fonts ────────────────────────────────────────────
        self.F_LOGO         = ("Arial Rounded MT Bold", max(16, int(40 * s)), "bold")
        self.F_NAV          = ("Baghdad", max(10, int(18 * s)))
        self.F_HEADER_TAB   = ("Baghdad", max(10, int(18 * s)), "bold")   # = F_NAV
        self.F_HEADER_LIGHT = ("Baghdad", max(10, int(18 * s)))            # = F_NAV
        self.F_TITLE_BIG    = ("Arial Rounded MT Bold", max(18, int(32 * s)), "bold")
        self.F_SECTION      = ("Arial Rounded MT Bold", max(14, int(28 * s)), "bold")
        self.F_CARD_LABEL   = ("Baghdad", max(10, int(18 * s)), "bold")    # = F_NAV
        self.F_CARD_NUM     = ("Arial Rounded MT Bold", max(28, int(85 * s)), "bold")
        self.F_CARD_NUM_MED = ("Arial Rounded MT Bold", max(22, int(70 * s)), "bold")
        self.F_CARD_SUB     = ("Baghdad", max(10, int(18 * s)))            # = F_NAV
        self.F_STAFF_NAME   = ("Baghdad", max(10, int(18 * s)), "bold")   # = F_NAV
        self.F_STAFF_INFO   = ("Baghdad", max(10, int(18 * s)))            # = F_NAV
        self.F_CHIP         = ("Baghdad", max(10, int(18 * s)), "bold")   # = F_NAV
        self.F_CHIP_SMALL   = ("Baghdad", max(10, int(18 * s)))            # = F_NAV
        self.F_ATT_TITLE    = ("Baghdad", max(10, int(18 * s)), "bold")   # = F_NAV
        self.F_ATT_BODY     = ("Baghdad", max(10, int(18 * s)))            # = F_NAV
        self.F_ATT_VALUE    = ("Baghdad", max(10, int(18 * s)))            # = F_NAV
        self.F_SALARY_NUM   = ("Arial Rounded MT Bold", max(14, int(22 * s)), "bold")
        self.F_TOGGLE       = ("Baghdad", max(10, int(18 * s)), "bold")   # = F_NAV
        self.F_DROPDOWN     = ("Baghdad", max(10, int(18 * s)))            # = F_NAV
        self.F_NEW_BTN      = ("Arial Rounded MT Bold", max(12, int(18 * s)), "bold")

        self.images = []
        self.backend = StaffBackend()
        self.staff_data = self.backend.get_data()

        # ── Layout ──────────────────────────────────────────
        main = tk.Frame(self, bg=self.C_BG)
        main.pack(fill=tk.BOTH, expand=True)

        self.BASE_SIDE_W = 260
        side_w = int(self.BASE_SIDE_W * s)

        self.side_frame = tk.Frame(main, width=side_w, bg=self.C_BG)
        self.side_frame.pack(side=tk.LEFT, fill=tk.Y)
        self.side_frame.pack_propagate(False)
        self.sidebar_canvas = tk.Canvas(self.side_frame, width=side_w, height=self.H,
                                        bg=self.C_BG, highlightthickness=0)
        self.sidebar_canvas.pack(fill=tk.BOTH, expand=True)

        self.content_container = tk.Frame(main, bg=self.C_BG)
        self.content_container.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        scrollbar = tk.Scrollbar(self.content_container, orient=tk.VERTICAL)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.canvas = tk.Canvas(self.content_container, bg=self.C_BG, highlightthickness=0)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.configure(command=self.canvas.yview)

        self.draw_sidebar()
        self.sidebar_canvas.scale("all", 0, 0, s, s)
        self.draw_content()
        self.canvas.scale("all", 0, 0, s, s)

        self.canvas.update_idletasks()
        bbox = self.canvas.bbox("all")
        if bbox:
            self.canvas.configure(scrollregion=(bbox[0], 0, bbox[2], bbox[3] + int(50 * s)))

        def _on_mw(event):
            if sys.platform == "darwin":
                self.canvas.yview_scroll(int(-event.delta), "units")
            else:
                self.canvas.yview_scroll(int(-event.delta / 120), "units")

        self.canvas.bind("<MouseWheel>", _on_mw, add="+")
        self.canvas.bind("<Button-4>", lambda e: self.canvas.yview_scroll(-1, "units"), add="+")
        self.canvas.bind("<Button-5>", lambda e: self.canvas.yview_scroll(1, "units"), add="+")
        self.bind("<Escape>", lambda e: self.destroy())

    # ─────────────────── SIDEBAR ───────────────────────────
    def draw_sidebar(self):
        cv = self.sidebar_canvas
        _round_rect(cv, -80, 0, 250, 820, radius=30, fill=self.C_SIDEBAR, outline="")
        cv.create_text(125, 70, text="Pet&Bed", font=self.F_LOGO, fill=self.C_TEXT)

        nav_items = ["Dashboard", "Care View", "Booking", "Rooms",
                     "Customer & Pet", "Billing", "Staff", "Report"]
        y = 110
        item_h, item_r, pad_x, right_x, gap = 37, 18, 36, 215, 10

        for i, item in enumerate(nav_items):
            # "Staff" is index 6 → active
            nav_tag = f"nav_{i}"
            fill = self.C_ACTIVE if i == 6 else "#efefef"
            _round_rect(cv, pad_x, y, right_x, y + item_h, radius=item_r,
                        fill=fill, outline="", tags=nav_tag)
            cv.create_text(pad_x + 20, y + 20, text=item,
                           font=self.F_NAV, fill=self.C_TEXT, anchor="w", tags=nav_tag)
            bind_nav_item(cv, nav_tag, self, item, "Staff")
            y += item_h + gap

        # Turtle icon
        _dir = os.path.dirname(__file__)
        icon_path = os.path.join(_dir, "image", "turtle.png")
        s = self._s
        iw, ih = int(130 * s), int(130 * s)
        sr = int(20 * s)
        if os.path.exists(icon_path):
            img = Image.open(icon_path).convert("RGBA")
        else:
            img = Image.new("RGBA", (iw, ih), color="#CCCCCC")
        img = img.resize((iw, ih), Image.Resampling.LANCZOS)
        mask = Image.new("L", (iw, ih), 0)
        ImageDraw.Draw(mask).rounded_rectangle((0, 0, iw, ih), radius=sr, fill=255)
        result = Image.new("RGBA", (iw, ih), (0, 0, 0, 0))
        result.paste(img, (0, 0), mask=mask)
        icon_tk = ImageTk.PhotoImage(result)
        self.images.append(icon_tk)
        cv.create_image(125 - 65, 550, image=icon_tk, anchor="nw")

        base_bottom = self.H / self._s
        btn_h, btn_pad = 42, 25
        btn_y2 = base_bottom - btn_pad
        btn_y1 = btn_y2 - btn_h
        _round_rect(cv, 30, btn_y1, 220, btn_y2, radius=btn_h // 2,
                    fill=self.C_TEXT, outline="", tags="logout_btn")
        cv.create_text(125, (btn_y1 + btn_y2) / 2, text="Log out",
                       font=self.F_NAV, fill="#FFFFFF", tags="logout_btn")
        bind_click(cv, "logout_btn", lambda e: logout_to_login(self))

    # ─────────────────── HELPERS ───────────────────────────
    def create_rounded_image(self, image_path, width, height, radius, crop_align="center"):
        s = self._s
        sw, sh, sr = int(width * s), int(height * s), int(radius * s)
        if not os.path.exists(image_path):
            img = Image.new("RGB", (sw, sh), color="#8FBFBA")
        else:
            img = Image.open(image_path).convert("RGB")
        img_ratio = img.width / img.height
        target_ratio = sw / sh
        if img_ratio > target_ratio:
            nw = int(sh * img_ratio)
            img = img.resize((nw, sh), Image.Resampling.LANCZOS)
            if isinstance(crop_align, (float, int)):
                left = int((nw - sw) * crop_align)
            elif crop_align == "left":
                left = 0
            elif crop_align == "right":
                left = nw - sw
            else:
                left = (nw - sw) // 2
            img = img.crop((left, 0, left + sw, sh))
        else:
            nh = int(sw / img_ratio)
            img = img.resize((sw, nh), Image.Resampling.LANCZOS)
            if isinstance(crop_align, (float, int)):
                top = int((nh - sh) * crop_align)
            elif crop_align == "bottom":
                top = nh - sh
            elif crop_align == "top":
                top = 0
            else:
                top = (nh - sh) // 2
            img = img.crop((0, top, sw, top + sh))
        mask = Image.new("L", (sw, sh), 0)
        ImageDraw.Draw(mask).rounded_rectangle((0, 0, sw, sh), radius=sr, fill=255)
        result = Image.new("RGBA", (sw, sh), (0, 0, 0, 0))
        result.paste(img, (0, 0), mask=mask)
        return ImageTk.PhotoImage(result)

    def _draw_chip(self, cv, cx, cy, text, bg, fg, font=None, tags=None):
        if font is None:
            font = self.F_CHIP
        tw = len(text) * 9 + 24
        th = 26
        x1, y1 = cx - tw // 2, cy - th // 2
        x2, y2 = cx + tw // 2, cy + th // 2
        kw = {"tags": tags} if tags else {}
        _round_rect(cv, x1, y1, x2, y2, radius=th // 2, fill=bg, outline="", **kw)
        cv.create_text(cx, cy, text=text, font=font, fill=fg, **kw)

    def show_penalty_dialog(self, employee_id, emp_name):
        PenaltyPopup(self, employee_id, emp_name, self.backend.db, self.refresh_ui)

    def refresh_ui(self):
        self.staff_data = self.backend.get_data()
        self.canvas.delete("all")
        self.draw_content()
        self.canvas.scale("all", 0, 0, self._s, self._s)
        self.canvas.update_idletasks()
        bbox = self.canvas.bbox("all")
        if bbox:
            self.canvas.configure(scrollregion=(bbox[0], 0, bbox[2], bbox[3] + int(50 * self._s)))

    # ─────────────────── MAIN CONTENT ──────────────────────
    def draw_content(self):
        cv = self.canvas
        dx = -self.BASE_SIDE_W      # offset because sidebar is separate
        y  = self.Y_OFF

        # ══════════════════════════════════════════════════
        # 1.  HEADER BAR
        # ══════════════════════════════════════════════════
        hbar_x1 = 302 + dx
        hbar_y1 = 30  + y
        hbar_x2 = 1169 + dx
        hbar_y2 = 70  + y
        _round_rect(cv, hbar_x1, hbar_y1, hbar_x2, hbar_y2, radius=20, fill=self.C_WHITE)

        # "Staff" (bold) | Manager | date
        cv.create_text(hbar_x1 + 30, (hbar_y1 + hbar_y2) // 2,
                       text="Staff", font=self.F_HEADER_TAB, fill=self.C_TEXT, anchor="w")
        cv.create_text(hbar_x1 + 100, (hbar_y1 + hbar_y2) // 2,
                       text="Manager", font=self.F_HEADER_LIGHT, fill=self.C_TEXT_LIGHT,
                       anchor="w", tags="staff_dashboard_link")
        bind_click(cv, "staff_dashboard_link",
                   lambda _e: switch_to(self, "Staff Dashboard", "Staff"))
        today_str = datetime.now().strftime("%d/%m/%Y")
        cv.create_text(hbar_x1 + 210, (hbar_y1 + hbar_y2) // 2,
                       text=today_str, font=self.F_HEADER_LIGHT, fill=self.C_TEXT_LIGHT, anchor="w")

        # "+ New staff" dark pill button (right side)
        nbtn_w, nbtn_h = 190, 40
        nbtn_x2 = hbar_x2            # flush với cạnh phải header
        nbtn_x1 = nbtn_x2 - nbtn_w
        nbtn_cy = (hbar_y1 + hbar_y2) // 2
        nbtn_y1 = nbtn_cy - nbtn_h // 2
        nbtn_y2 = nbtn_cy + nbtn_h // 2
        _round_rect(cv, nbtn_x1, nbtn_y1, nbtn_x2, nbtn_y2,
                    radius=nbtn_h // 2, fill=self.C_DARK_BTN, outline="",
                    tags="new_staff_btn")
        cv.create_text((nbtn_x1 + nbtn_x2) // 2, nbtn_cy,
                       text="+ New staff", font=self.F_NEW_BTN, fill=self.C_WHITE,
                       tags="new_staff_btn")
        bind_click(cv, "new_staff_btn", lambda _e: open_popup("New Staff"))

        # ══════════════════════════════════════════════════
        # 2.  TITLE "Thu Lan"
        # ══════════════════════════════════════════════════
        title_y = hbar_y2 + 42
        cv.create_text(hbar_x1, title_y,
                       text=self.staff_data["manager_name"], font=self.F_TITLE_BIG, fill=self.C_TEXT, anchor="w")

        # ══════════════════════════════════════════════════
        # 3.  DROPDOWN "05/2026"
        # ══════════════════════════════════════════════════
        dd_x1 = hbar_x1
        dd_y1 = title_y + 28
        dd_x2 = hbar_x1 + 260
        dd_y2 = dd_y1 + 40
        _round_rect(cv, dd_x1, dd_y1, dd_x2, dd_y2, radius=20, fill=self.C_WHITE, outline="")

        cv.create_text(dd_x1 + 16, (dd_y1 + dd_y2) // 2,
                       text=self.staff_data["month_label"], font=self.F_DROPDOWN, fill=self.C_TEXT, anchor="w")
        # Arrow triangle
        ax = dd_x2 - 18
        ay = (dd_y1 + dd_y2) // 2
        cv.create_polygon(ax - 8, ay - 4, ax + 8, ay - 4, ax, ay + 6,
                          fill=self.C_TEXT_LIGHT, outline="")

        # ══════════════════════════════════════════════════
        # 4.  TOP ROW:  "Total Employees" card  +  Cat image
        # ══════════════════════════════════════════════════
        row1_y1 = dd_y2 + 18
        row1_y2 = row1_y1 + 155

        # --- Total Employees card ---
        emp_card_x2 = hbar_x1 + 260
        _round_rect(cv, hbar_x1, row1_y1, emp_card_x2, row1_y2, radius=26, fill=self.C_CARD)
        card_cx = (hbar_x1 + emp_card_x2) // 2
        cv.create_text(card_cx, row1_y1 + 28,
                       text="Total Employees", font=self.F_CARD_LABEL, fill=self.C_TEXT)
        cv.create_text(card_cx, row1_y1 + 75,
                       text=str(self.staff_data["summary"]["total"]), font=self.F_CARD_NUM, fill=self.C_TEXT)
        cv.create_text(card_cx, row1_y2 - 22,
                       text=self.staff_data["summary"]["role_sub"], font=self.F_CARD_SUB, fill=self.C_TEXT_LIGHT)

        # --- Cat (manage.jpg) rounded image ---
        _dir = os.path.dirname(__file__)
        cat_path = os.path.join(_dir, "image", "manage.jpg")
        cat_x1 = emp_card_x2 + 24
        cat_y1 = hbar_y2 + 18
        cat_img_w = int(hbar_x2 - cat_x1)
        cat_img_h = int(row1_y2 - cat_y1)
        cat_tk = self.create_rounded_image(cat_path, cat_img_w, cat_img_h, radius=28, crop_align=0.36)
        self.images.append(cat_tk)
        cv.create_image(cat_x1, cat_y1, image=cat_tk, anchor="nw")

        # ══════════════════════════════════════════════════
        # 5.  SECOND STATS ROW: 3 equal cards
        # ══════════════════════════════════════════════════
        row2_y1 = row1_y2 + 26
        row2_y2 = row2_y1 + 155

        total_w = hbar_x2 - hbar_x1
        card_gap = 26
        card_w3 = (total_w - card_gap * 2) // 3

        stats = [
            {
                "label":  "Present Today",
                "big":    str(self.staff_data["summary"]["present_today"]),
                "sub":    f"expected {self.staff_data['summary']['expected_today']}",
                "font":   self.F_CARD_NUM,
            },
            {
                "label":  "Estimated Salary This Month",
                "big":    self.staff_data["summary"]["salary_big"],
                "sub":    "millions",
                "font":   self.F_CARD_NUM_MED,
            },
            {
                "label":  "Total Working Hours",
                "big":    str(self.staff_data["summary"]["working_hours"]),
                "sub":    f"{datetime.now().strftime('%b')} (up to now)",
                "font":   self.F_CARD_NUM,
            },
        ]

        for i, stat in enumerate(stats):
            sx1 = hbar_x1 + i * (card_w3 + card_gap)
            sx2 = sx1 + card_w3
            _round_rect(cv, sx1, row2_y1, sx2, row2_y2, radius=26, fill=self.C_CARD)
            scx = (sx1 + sx2) // 2
            cv.create_text(scx, row2_y1 + 28,
                           text=stat["label"], font=self.F_CARD_LABEL, fill=self.C_TEXT)
            cv.create_text(scx, row2_y1 + 75,
                           text=stat["big"], font=stat["font"], fill=self.C_TEXT)
            cv.create_text(scx, row2_y2 - 22,
                           text=stat["sub"], font=self.F_CARD_SUB, fill=self.C_TEXT_LIGHT)

        # ══════════════════════════════════════════════════
        # 6.  BOTTOM ROW: Staff list  +  Attendance Today
        # ══════════════════════════════════════════════════
        bot_y1 = row2_y2 + 28
        bot_h  = 410
        bot_y2 = bot_y1 + bot_h

        bot_gap = 28
        left_w  = int(total_w * 0.515)
        right_w = total_w - left_w - bot_gap

        left_x1  = hbar_x1
        left_x2  = left_x1 + left_w
        right_x1 = left_x2 + bot_gap
        right_x2 = hbar_x2

        # ── LEFT: Staff list card ──
        _round_rect(cv, left_x1, bot_y1, left_x2, bot_y2, radius=26, fill=self.C_CARD)

        staff_list = self.staff_data["staff_list"] or [
            {"name": "No active staff", "emp": "", "phone": "-", "chip": "-", "has_penalty": False}
        ]

        row_h_s = (bot_h - 46) // len(staff_list)
        pad_l = 36
        chip_x_right = left_x2 - 72

        for ri, st in enumerate(staff_list):
            ry1 = bot_y1 + 28 + ri * row_h_s
            ry2 = ry1 + row_h_s
            cy  = ry1 + row_h_s // 2

            name_x = left_x1 + pad_l

            # Line 1: Name + EMP (bold)
            cv.create_text(name_x, cy - 10,
                           text=f"{st['name']}  {st['emp']}",
                           font=self.F_STAFF_NAME, fill=self.C_TEXT, anchor="w")

            # Line 2: phone icon + phone number (same line)
            phone_y = cy + 10
            cv.create_text(name_x, phone_y,
                           text="📞", font=("Arial", max(8, int(12 * self._s))), anchor="w")
            cv.create_text(name_x + 22, phone_y,
                           text=st["phone"],
                           font=self.F_STAFF_INFO, fill=self.C_TEXT_LIGHT, anchor="w")

            # 1. Role Chip (always green, aligned top right)
            self._draw_chip(cv, chip_x_right, cy - 12,
                            st["chip"], self.C_GREEN_BG, self.C_GREEN_FG, self.F_CHIP_SMALL)

            # 2. Add Penalty button/chip (placed under the role tag)
            if st.get("employee_id"):
                penalty_tag = f"penalty_btn_{st['employee_id']}"
                
                # Soft pink background if they already have a penalty, otherwise nice soft gray
                p_bg = self.C_PINK_BG if st.get("has_penalty") else "#EFEFEF"
                p_fg = self.C_PINK_FG if st.get("has_penalty") else self.C_TEXT_LIGHT
                
                self._draw_chip(cv, chip_x_right, cy + 16,
                                "+ Penalty", p_bg, p_fg, self.F_CHIP_SMALL, tags=penalty_tag)
                                
                # Bind the click handler to trigger the penalty dialog
                cv.tag_bind(penalty_tag, "<Button-1>", lambda _e, eid=st["employee_id"], name=st["name"]: self.show_penalty_dialog(eid, name))
                cv.tag_bind(penalty_tag, "<Enter>", lambda _e: cv.config(cursor="hand2"))
                cv.tag_bind(penalty_tag, "<Leave>", lambda _e: cv.config(cursor=""))

            # Divider (not after last)
            if ri < len(staff_list) - 1:
                cv.create_line(left_x1 + 36, ry2, left_x2 - 36, ry2,
                               fill=self.C_DIVIDER, width=1)

        # ── RIGHT: Attendance Today card ──
        _round_rect(cv, right_x1, bot_y1, right_x2, bot_y2, radius=26, fill=self.C_CARD)
        focus_att = self.staff_data["focus_attendance"] or {
            "name": "No attendance",
            "emp": "",
            "present": False,
            "clock_in": "-",
            "clock_out": "-",
            "working_hour": "0 hours",
            "overtime_hour": "0 hours",
            "penalty": "0đ",
            "note": "No attendance today",
            "salary": {"Day": "0đ", "Week": "0đ", "Month": "0đ"},
        }

        # Card header row
        att_title_y = bot_y1 + 28
        cv.create_text(right_x1 + 22, att_title_y,
                       text="Attendance Today", font=self.F_ATT_TITLE, fill=self.C_TEXT, anchor="w")
        # "Yes" green chip
        att_chip = "Yes" if focus_att["present"] else "No"
        att_bg = self.C_GREEN_BG if focus_att["present"] else self.C_PINK_BG
        att_fg = self.C_GREEN_FG if focus_att["present"] else self.C_PINK_FG
        self._draw_chip(cv, right_x2 - 38, att_title_y,
                        att_chip, att_bg, att_fg, self.F_CHIP_SMALL)

        # Divider
        cv.create_line(right_x1 + 15, att_title_y + 18,
                       right_x2 - 15, att_title_y + 18,
                       fill=self.C_DIVIDER, width=1)

        # Employee name
        emp_name_y = att_title_y + 38
        cv.create_text(right_x1 + 22, emp_name_y,
                       text=f"{focus_att['name']}   {focus_att['emp']}",
                       font=self.F_STAFF_NAME, fill=self.C_TEXT, anchor="w")

        # Attendance details table
        details = [
            ("Clock - in",      focus_att["clock_in"]),
            ("Clock - out",     focus_att["clock_out"]),
            ("Working hour",    focus_att["working_hour"]),
            ("Overtime hour",   focus_att["overtime_hour"]),
            ("Penalty",         focus_att["penalty"]),
        ]
        att_row_h = 26
        att_start_y = emp_name_y + 24
        att_val_x = right_x2 - 22
        for i, (label, value) in enumerate(details):
            ry = att_start_y + i * att_row_h
            cv.create_text(right_x1 + 22, ry,
                           text=label, font=self.F_ATT_BODY, fill=self.C_TEXT, anchor="w")
            cv.create_text(att_val_x, ry,
                           text=value, font=self.F_ATT_VALUE, fill=self.C_TEXT, anchor="e")

        # Divider before Note
        note_div_y = att_start_y + len(details) * att_row_h + 4
        cv.create_line(right_x1 + 15, note_div_y, right_x2 - 15, note_div_y,
                       fill=self.C_DIVIDER, width=1)

        note_y = note_div_y + 18
        cv.create_text(right_x1 + 22, note_y,
                       text="Note", font=self.F_STAFF_NAME, fill=self.C_TEXT, anchor="w")
        cv.create_text(right_x1 + 22, note_y + 22,
                       text=focus_att["note"], font=self.F_ATT_BODY, fill=self.C_TEXT_LIGHT, anchor="w")

        # Divider before Estimate salary
        sal_div_y = note_y + 48
        cv.create_line(right_x1 + 15, sal_div_y, right_x2 - 15, sal_div_y,
                       fill=self.C_DIVIDER, width=1)

        sal_label_y = sal_div_y + 22
        cv.create_text(right_x1 + 22, sal_label_y,
                       text="Estimate salary", font=self.F_STAFF_NAME, fill=self.C_TEXT, anchor="w")

        # Day / Week (active green) / Month toggle chips
        toggle_cx = right_x1 + 195
        for t_idx, t_label in enumerate(["Day", "Week", "Month"]):
            if t_label == "Week":
                self._draw_chip(cv, toggle_cx + t_idx * 65, sal_label_y,
                                t_label, self.C_GREEN_BG, self.C_GREEN_FG, self.F_TOGGLE)
            else:
                # bordered chip
                tw2 = len(t_label) * 9 + 22
                th2 = 24
                tcx = toggle_cx + t_idx * 65
                x1c, y1c = tcx - tw2 // 2, sal_label_y - th2 // 2
                x2c, y2c = tcx + tw2 // 2, sal_label_y + th2 // 2
                r2 = th2 // 2
                # White fill
                _round_rect(cv, x1c, y1c, x2c, y2c, radius=r2, fill=self.C_WHITE)
                # Draw border arcs
                d2 = r2 * 2
                cv.create_arc(x1c, y1c, x1c + d2, y1c + d2, start=90, extent=90,
                              style='arc', outline=self.C_BORDER, width=1)
                cv.create_arc(x2c - d2, y1c, x2c, y1c + d2, start=0, extent=90,
                              style='arc', outline=self.C_BORDER, width=1)
                cv.create_arc(x2c - d2, y2c - d2, x2c, y2c, start=270, extent=90,
                              style='arc', outline=self.C_BORDER, width=1)
                cv.create_arc(x1c, y2c - d2, x1c + d2, y2c, start=180, extent=90,
                              style='arc', outline=self.C_BORDER, width=1)
                cv.create_line(x1c + r2, y1c, x2c - r2, y1c, fill=self.C_BORDER)
                cv.create_line(x1c + r2, y2c, x2c - r2, y2c, fill=self.C_BORDER)
                cv.create_text(tcx, sal_label_y, text=t_label,
                               font=self.F_TOGGLE, fill=self.C_TEXT)

        # Salary amount
        sal_amt_y = sal_label_y + 32
        cv.create_text(right_x2 - 22, sal_amt_y,
                       text=focus_att["salary"]["Week"], font=self.F_SALARY_NUM, fill=self.C_TEXT, anchor="e")


if __name__ == "__main__":
    app = StaffPage()
    app.mainloop()
