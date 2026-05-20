import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk, ImageDraw
import os
import sys
from datetime import datetime
from decimal import Decimal

from app_window import AppWindow
from database import DatabaseConnection
from navigation import bind_click, bind_nav_item, logout_to_login


class EmployeeDashboardBackend:
    def __init__(self, db=None, employee_id=None):
        self.db = db or DatabaseConnection()
        self.employee_id = employee_id

    @staticmethod
    def _money(value):
        if value is None:
            value = 0
        if isinstance(value, Decimal):
            value = int(value)
        return f"{int(value):,}đ"

    @staticmethod
    def _emp_code(employee_id):
        try:
            return f"EMP{int(employee_id):03d}"
        except (TypeError, ValueError):
            return "EMP---"

    @staticmethod
    def _time(value):
        return value.strftime("%H:%M") if value else "-"

    @staticmethod
    def _date(value):
        return value.strftime("%d/%m/%Y") if value else "-"

    @staticmethod
    def _number(value):
        if value is None:
            return "0"
        try:
            return str(int(float(value)))
        except (ValueError, TypeError):
            return "0"

    def _active_where(self, alias=""):
        prefix = f"{alias}." if alias else ""
        return f"({prefix}is_active = 1 OR {prefix}is_active = b'1')"

    def _selected_employee_id(self):
        if self.employee_id:
            return self.employee_id

        row = self.db.fetch_one(
            f"""
            SELECT e.employee_id
            FROM employees e
            LEFT JOIN attendance a ON a.employee_id = e.employee_id
            WHERE {self._active_where("e")}
            ORDER BY
                CASE LOWER(e.role) WHEN 'manager' THEN 1 ELSE 0 END,
                CASE WHEN a.attendance_id IS NULL THEN 1 ELSE 0 END,
                a.work_date DESC,
                a.attendance_id DESC,
                e.employee_id
            LIMIT 1
            """
        )
        return row["employee_id"] if row else None

    def get_employee(self):
        employee_id = self._selected_employee_id()
        if not employee_id:
            return None
        return self.db.fetch_one(
            """
            SELECT employee_id, full_name, role, base_salary_per_hour
            FROM employees
            WHERE employee_id = %s
            LIMIT 1
            """,
            (employee_id,),
        )

    def get_attendance_summary(self, employee_id):
        row = self.db.fetch_one(
            """
            SELECT
                COUNT(DISTINCT work_date) AS working_days,
                COALESCE(SUM(working_hours), 0) AS total_hours
            FROM attendance
            WHERE employee_id = %s
              AND YEAR(work_date) = YEAR(CURDATE())
              AND MONTH(work_date) = MONTH(CURDATE())
            """,
            (employee_id,),
        ) or {}
        return {
            "working_days": int(row.get("working_days") or 0),
            "total_hours": self._number(row.get("total_hours")),
        }

    def get_attendance_history(self, employee_id, limit=6):
        rows = self.db.fetch_all(
            """
            SELECT work_date, check_in, check_out, working_hours, overtime_hours, penalty
            FROM attendance
            WHERE employee_id = %s
            ORDER BY work_date DESC, attendance_id DESC
            LIMIT %s
            """,
            (employee_id, limit),
        )
        return [
            (
                self._date(row.get("work_date")),
                self._time(row.get("check_in")),
                self._time(row.get("check_out")),
                self._number(row.get("working_hours")) if row.get("check_out") else "-",
                self._number(row.get("overtime_hours")) if row.get("check_out") else "-",
                self._money(row.get("penalty") or 0),
            )
            for row in rows or []
        ]

    def get_salary_values(self, employee_id):
        periods = {
            "Day": "a.work_date = CURDATE()",
            "Week": "YEARWEEK(a.work_date, 1) = YEARWEEK(CURDATE(), 1)",
            "Month": "YEAR(a.work_date) = YEAR(CURDATE()) AND MONTH(a.work_date) = MONTH(CURDATE())",
        }
        values = {}
        for label, where_clause in periods.items():
            row = self.db.fetch_one(
                f"""
                SELECT COALESCE(SUM((COALESCE(a.working_hours, 0) + COALESCE(a.overtime_hours, 0))
                    * e.base_salary_per_hour - COALESCE(a.penalty, 0)), 0) AS salary
                FROM attendance a
                JOIN employees e ON e.employee_id = a.employee_id
                WHERE a.employee_id = %s AND {where_clause}
                """,
                (employee_id,),
            ) or {}
            values[label] = self._money(row.get("salary"))
        return values

    def is_employee_clocked_in(self, employee_id):
        if not employee_id:
            return False
        row = self.db.fetch_one(
            """
            SELECT attendance_id
            FROM attendance
            WHERE employee_id = %s
              AND work_date = CURDATE()
              AND check_out IS NULL
            LIMIT 1
            """,
            (employee_id,),
        )
        return row is not None

    def get_data(self):
        try:
            employee = self.get_employee()
            if not employee:
                return self.fallback_data()

            employee_id = employee["employee_id"]
            is_clocked_in = self.is_employee_clocked_in(employee_id)
            return {
                "employee_id": employee_id,
                "name": employee.get("full_name") or "-",
                "emp": self._emp_code(employee_id),
                "month_label": datetime.now().strftime("%m/%Y"),
                "summary": self.get_attendance_summary(employee_id),
                "attendance": self.get_attendance_history(employee_id),
                "salary": self.get_salary_values(employee_id),
                "is_clocked_in": is_clocked_in,
            }
        except Exception as exc:
            print(f"Employee dashboard backend error: {exc}")
            return self.fallback_data()

    def fallback_data(self):
        return {
            "employee_id": None,
            "name": "No active staff",
            "emp": "EMP---",
            "month_label": datetime.now().strftime("%m/%Y"),
            "summary": {"working_days": 0, "total_hours": "0"},
            "attendance": [],
            "salary": {"Day": "0đ", "Week": "0đ", "Month": "0đ"},
            "is_clocked_in": False,
        }

    def clock_in_or_out(self, employee_id):
        if not employee_id:
            raise ValueError("No employee selected")

        open_shift = self.db.fetch_one(
            """
            SELECT attendance_id
            FROM attendance
            WHERE employee_id = %s
              AND work_date = CURDATE()
              AND check_out IS NULL
            ORDER BY attendance_id DESC
            LIMIT 1
            """,
            (employee_id,),
        )
        if open_shift:
            self.db.execute(
                """
                UPDATE attendance
                SET check_out = NOW(),
                    working_hours = ROUND(TIMESTAMPDIFF(MINUTE, check_in, NOW()) / 60, 2),
                    overtime_hours = GREATEST(ROUND(TIMESTAMPDIFF(MINUTE, check_in, NOW()) / 60 - 8, 2), 0)
                WHERE attendance_id = %s
                """,
                (open_shift["attendance_id"],),
            )
            return "Clock out saved"

        attendance_id = self.db.execute(
            """
            INSERT INTO attendance (
                employee_id, work_date, check_in, working_hours, overtime_hours, penalty, note
            )
            VALUES (%s, CURDATE(), NOW(), 0, 0, 0, 'Working')
            """,
            (employee_id,),
        )
        return f"Clock in saved #{attendance_id}"


def _round_rect(cv, x1, y1, x2, y2, radius=25, **kwargs):
    d = 2 * radius
    kwargs["outline"] = kwargs.get("fill", "")
    items = []
    items.append(cv.create_rectangle(x1 + radius, y1, x2 - radius, y2, **kwargs))
    items.append(cv.create_rectangle(x1, y1 + radius, x2, y2 - radius, **kwargs))
    items.append(cv.create_arc(x1, y1, x1 + d, y1 + d, start=90, extent=90, style='pieslice', **kwargs))
    items.append(cv.create_arc(x2 - d, y1, x2, y1 + d, start=0, extent=90, style='pieslice', **kwargs))
    items.append(cv.create_arc(x2 - d, y2 - d, x2, y2, start=270, extent=90, style='pieslice', **kwargs))
    items.append(cv.create_arc(x1, y2 - d, x1 + d, y2, start=180, extent=90, style='pieslice', **kwargs))
    return tuple(items)


class StaffDashboard(AppWindow):
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

        # Colors
        self.C_BG         = "#A8D3CF"
        self.C_SIDEBAR    = "#FFFFFF"
        self.C_TEXT       = "#4A3525"
        self.C_TEXT_LIGHT = "#7A685F"
        self.C_WHITE      = "#FFFFFF"
        self.C_ACTIVE     = "#68BBB2"
        self.C_DIVIDER    = "#DDD8D2"
        self.C_CARD_BG    = "#FFFFFF"
        self.C_CLOCKIN_BG = "#4A3525"   # dark brown "Clock in" button
        self.C_SALARY_ACTIVE = "#A8D050"  # yellow-green active tab
        self.C_STAT_CARD  = "#FFFFFF"

        # Fonts
        self.F_LOGO        = ("Arial Rounded MT Bold", max(16, int(40 * s)), "bold")
        self.F_NAV         = ("Baghdad", max(10, int(18 * s)))
        self.F_TITLE       = ("Arial Rounded MT Bold", max(10, int(18 * s)), "bold")
        self.F_DATE        = ("Baghdad", max(10, int(18 * s)))
        self.F_SECTION     = ("Arial Rounded MT Bold", max(14, int(28 * s)), "bold")
        self.F_EMP_NAME    = ("Arial Rounded MT Bold", max(16, int(32 * s)), "bold")
        self.F_EMP_ID      = ("Baghdad", max(10, int(18 * s)))
        self.F_STAT_LABEL  = ("Baghdad", max(10, int(18 * s)), "bold")
        self.F_STAT_VAL    = ("Arial Rounded MT Bold", max(28, int(85 * s)), "bold")
        self.F_TABLE_HEAD  = ("Baghdad", max(10, int(18 * s)), "bold")
        self.F_TABLE_BODY  = ("Baghdad", max(10, int(18 * s)))
        self.F_MONTH_SEL   = ("Baghdad", max(10, int(18 * s)))
        self.F_SALARY_TAB  = ("Baghdad", max(10, int(18 * s)), "bold")
        self.F_SALARY_VAL  = ("Arial Rounded MT Bold", max(14, int(22 * s)), "bold")
        self.F_CLOCKIN_BTN = ("Baghdad", max(10, int(18 * s)), "bold")

        # Salary tab state
        self._salary_tab = tk.StringVar(value="Week")
        self.backend = EmployeeDashboardBackend(employee_id=os.environ.get("PETBED_EMPLOYEE_ID"))
        self.staff_data = self.backend.get_data()
        self._salary_values = self.staff_data["salary"]

        self.images = []

        # ── Layout ──
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
            self.canvas.configure(scrollregion=(bbox[0], 0, bbox[2], bbox[3] + int(60 * s)))

        def _on_mw(event):
            if sys.platform == "darwin":
                self.canvas.yview_scroll(int(-event.delta), "units")
            else:
                self.canvas.yview_scroll(int(-event.delta / 120), "units")

        self.canvas.bind("<MouseWheel>", _on_mw, add="+")
        self.canvas.bind("<Button-4>", lambda e: self.canvas.yview_scroll(-1, "units"), add="+")
        self.canvas.bind("<Button-5>", lambda e: self.canvas.yview_scroll(1, "units"), add="+")
        self.bind("<Escape>", lambda e: self.destroy())

    # ─────────────────────────── SIDEBAR ───────────────────────────
    def draw_sidebar(self):
        cv = self.sidebar_canvas
        _round_rect(cv, -80, 0, 250, 820, radius=30, fill=self.C_SIDEBAR, outline="")
        cv.create_text(125, 70, text="Pet&Bed", font=self.F_LOGO, fill=self.C_TEXT)

        nav_items = ["Dashboard", "Care View", "Booking", "Rooms",
                     "Customer & Pet", "Billing", "Staff", "Report"]
        y = 110
        item_h, item_r, pad_x, right_x, gap = 37, 18, 36, 215, 10

        for i, item in enumerate(nav_items):
            nav_tag = f"nav_{i}"
            fill = self.C_ACTIVE if i == 6 else "#efefef"
            _round_rect(cv, pad_x, y, right_x, y + item_h, radius=item_r,
                        fill=fill, outline="", tags=nav_tag)
            cv.create_text(pad_x + 20, y + 20, text=item, font=self.F_NAV,
                           fill=self.C_WHITE if i == 6 else self.C_TEXT,
                           anchor="w", tags=nav_tag)
            bind_nav_item(cv, nav_tag, self, item, "Staff Dashboard")
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

    # ─────────────────────────── IMAGE HELPER ───────────────────────
    def create_rounded_image(self, image_path, width, height, radius):
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
            left = (nw - sw) // 2
            img = img.crop((left, 0, left + sw, sh))
        else:
            nh = int(sw / img_ratio)
            img = img.resize((sw, nh), Image.Resampling.LANCZOS)
            top = (nh - sh) // 2
            img = img.crop((0, top, sw, top + sh))
        mask = Image.new("L", (sw, sh), 0)
        ImageDraw.Draw(mask).rounded_rectangle((0, 0, sw, sh), radius=sr, fill=255)
        result = Image.new("RGBA", (sw, sh), (0, 0, 0, 0))
        result.paste(img, (0, 0), mask=mask)
        return ImageTk.PhotoImage(result)

    # ─────────────────────────── MAIN CONTENT ───────────────────────
    def draw_content(self):
        cv = self.canvas
        dx = -self.BASE_SIDE_W
        y  = self.Y_OFF
        s  = self._s

        # ── HEADER BAR ──
        header_x1 = 300 + dx
        header_y1 = 30 + y
        header_x2 = 1150 + dx
        header_y2 = 70 + y
        header_cy = (header_y1 + header_y2) // 2
        _round_rect(cv, header_x1, header_y1, header_x2, header_y2,
                    radius=20, fill=self.C_WHITE)
        cv.create_text(header_x1 + 30, header_cy, text="Staff",
                       font=self.F_TITLE, fill=self.C_TEXT, anchor="w")
        cv.create_text(header_x1 + 100, header_cy, text="Employee",
                       font=self.F_DATE, fill=self.C_TEXT_LIGHT, anchor="w")
        cv.create_text(header_x1 + 210, header_cy,
                       text=datetime.now().strftime("%d/%m/%Y"),
                       font=self.F_DATE, fill=self.C_TEXT_LIGHT, anchor="w")

        # Clock in button (dark pill, right side of header)
        ci_w, ci_h = 150, 38
        ci_x2 = header_x2
        ci_x1 = ci_x2 - ci_w
        ci_y1 = header_cy - ci_h // 2
        ci_y2 = ci_y1 + ci_h
        
        is_clocked_in = self.staff_data.get("is_clocked_in", False)
        btn_text = "Clock out" if is_clocked_in else "Clock in"
        btn_bg = "#A24E4E" if is_clocked_in else self.C_CLOCKIN_BG
        
        _round_rect(cv, ci_x1, ci_y1, ci_x2, ci_y2,
                    radius=ci_h // 2, fill=btn_bg, tags="clockin")
        cv.create_text((ci_x1 + ci_x2) // 2, (ci_y1 + ci_y2) // 2,
                       text=btn_text, font=self.F_CLOCKIN_BTN,
                       fill=self.C_WHITE, tags="clockin")
        cv.tag_bind("clockin", "<Button-1>", self._clock_in_or_out)
        cv.tag_bind("clockin", "<Enter>", lambda e: cv.config(cursor="hand2"))
        cv.tag_bind("clockin", "<Leave>", lambda e: cv.config(cursor=""))

        # ── EMPLOYEE NAME + ID + MONTH SELECTOR ──
        name_y = 120 + y
        cv.create_text(300 + dx, name_y + 12, text=self.staff_data["name"],
                       font=self.F_EMP_NAME, fill=self.C_TEXT, anchor="w")
        cv.create_text(300 + dx, name_y + int(36 * s), text=self.staff_data["emp"],
                       font=self.F_EMP_ID, fill=self.C_TEXT_LIGHT, anchor="w")

        # Month selector pill
        ms_x1, ms_y1 = 480 + dx, name_y - 4
        ms_x2, ms_y2 = 670 + dx, name_y + 38
        ms_r = (ms_y2 - ms_y1) // 2
        _round_rect(cv, ms_x1, ms_y1, ms_x2, ms_y2, radius=ms_r, fill=self.C_WHITE)
        cv.create_text(ms_x1 + 20, (ms_y1 + ms_y2) // 2,
                       text=self.staff_data["month_label"], font=self.F_MONTH_SEL,
                       fill=self.C_TEXT, anchor="w")
        # Dropdown arrow
        arr_x = ms_x2 - 22
        arr_y = (ms_y1 + ms_y2) // 2
        cv.create_polygon(arr_x - 7, arr_y - 4,
                          arr_x + 7, arr_y - 4,
                          arr_x,     arr_y + 5,
                          fill=self.C_TEXT)

        # ── STAT CARDS + PHOTO ──
        card_y1 = name_y + int(50 * s)
        card_y2 = card_y1 + 120

        # Working Days card
        _round_rect(cv, 300 + dx, card_y1, 460 + dx, card_y2, radius=20, fill=self.C_WHITE)
        cv.create_text(380 + dx, card_y1 + 22,
                       text="Working Days", font=self.F_STAT_LABEL, fill=self.C_TEXT)
        cv.create_text(380 + dx, card_y1 + 73,
                       text=str(self.staff_data["summary"]["working_days"]),
                       font=self.F_STAT_VAL, fill=self.C_TEXT)

        # Total Hours card
        _round_rect(cv, 475 + dx, card_y1, 665 + dx, card_y2, radius=20, fill=self.C_WHITE)
        cv.create_text(570 + dx, card_y1 + 22,
                       text="Total Hours", font=self.F_STAT_LABEL, fill=self.C_TEXT)
        cv.create_text(570 + dx, card_y1 + 73,
                       text=str(self.staff_data["summary"]["total_hours"]),
                       font=self.F_STAT_VAL, fill=self.C_TEXT)

        # Staff photo
        _dir = os.path.dirname(__file__)
        photo_path = os.path.join(_dir, "image", "staff.jpg")
        photo_w = 450
        photo_h = int((card_y2 - (name_y - 12)))
        photo_tk = self.create_rounded_image(photo_path, photo_w, photo_h // int(s) + 10, radius=18)
        self.images.append(photo_tk)
        cv.create_image(719 + dx, name_y - 12, image=photo_tk, anchor="nw")

        # ── MY ATTENDANCE HISTORY ──
        att_title_y = card_y2 + 30
        cv.create_text(300 + dx, att_title_y,
                       text="My Attendance History",
                       font=self.F_SECTION, fill=self.C_TEXT, anchor="w")

        tbl_y1 = att_title_y + 28
        tbl_y2 = tbl_y1 + 340
        _round_rect(cv, 300 + dx, tbl_y1, 1150 + dx, tbl_y2, radius=20, fill=self.C_WHITE)

        # Table header
        hdr_y = tbl_y1 + 32
        cols   = ["Date", "Clock in", "Clock out", "Hours", "Overtime hours", "Penalty"]
        col_xs = [335 + dx, 460 + dx, 565 + dx, 680 + dx, 760 + dx, 930 + dx]

        for col, cx in zip(cols, col_xs):
            cv.create_text(cx, hdr_y, text=col, font=self.F_TABLE_HEAD,
                           fill=self.C_TEXT, anchor="w")

        cv.create_line(325 + dx, hdr_y + 20, 1130 + dx, hdr_y + 20,
                       fill=self.C_DIVIDER, width=1)

        # Table rows
        attendance_data = self.staff_data["attendance"] or [
            ("-", "-", "-", "-", "-", "-"),
        ]

        row_h = 46
        for ri, row in enumerate(attendance_data):
            ry  = hdr_y + 22 + ri * row_h
            rcy = ry + row_h // 2

            for ci, (val, cx) in enumerate(zip(row, col_xs)):
                cv.create_text(cx, rcy, text=val,
                               font=self.F_TABLE_BODY, fill=self.C_TEXT, anchor="w")

            if ri < len(attendance_data) - 1:
                cv.create_line(325 + dx, ry + row_h - 1, 1130 + dx, ry + row_h - 1,
                               fill=self.C_DIVIDER, width=1)

        # ── ESTIMATE SALARY ──
        sal_title_y = tbl_y2 + 28
        cv.create_text(300 + dx, sal_title_y,
                       text="Estimate Salary",
                       font=self.F_SECTION, fill=self.C_TEXT, anchor="w")

        sal_card_y1 = sal_title_y + 28
        sal_card_y2 = sal_card_y1 + 66
        _round_rect(cv, 300 + dx, sal_card_y1, 1150 + dx, sal_card_y2,
                    radius=(sal_card_y2 - sal_card_y1) // 2, fill=self.C_WHITE)

        # Salary tabs
        tabs = ["Day", "Week", "Month"]
        tab_w, tab_h = 88, 42
        tab_x = 320 + dx
        tab_y1 = sal_card_y1 + (sal_card_y2 - sal_card_y1 - tab_h) // 2
        tab_y2 = tab_y1 + tab_h
        tab_r  = tab_h // 2

        for tab in tabs:
            active = self._salary_tab.get() == tab
            fill   = self.C_SALARY_ACTIVE if active else self.C_WHITE
            tag    = f"sal_tab_{tab}"
            # Border outline pill
            _round_rect(cv, tab_x, tab_y1, tab_x + tab_w, tab_y2,
                        radius=tab_r, fill="#DDDDDD", tags=tag)
            # Inner fill
            _round_rect(cv, tab_x + 1, tab_y1 + 1, tab_x + tab_w - 1, tab_y2 - 1,
                        radius=tab_r - 1, fill=fill, tags=tag)
            cv.create_text(tab_x + tab_w // 2, (tab_y1 + tab_y2) // 2,
                           text=tab, font=self.F_SALARY_TAB,
                           fill=self.C_TEXT, tags=tag)
            cv.tag_bind(tag, "<Button-1>", lambda e, t=tab: self._switch_salary_tab(t))
            cv.tag_bind(tag, "<Enter>", lambda e: cv.config(cursor="hand2"))
            cv.tag_bind(tag, "<Leave>", lambda e: cv.config(cursor=""))
            tab_x += tab_w + 8

        # Salary value (right side)
        self._salary_text_id = cv.create_text(
            1120 + dx, (sal_card_y1 + sal_card_y2) // 2,
            text=self._salary_values[self._salary_tab.get()],
            font=self.F_SALARY_VAL, fill=self.C_TEXT, anchor="e"
        )

        # Store refs for tab redraw
        self._sal_cv  = cv
        self._sal_dx  = dx
        self._sal_tab_y1  = tab_y1
        self._sal_tab_y2  = tab_y2
        self._sal_tab_r   = tab_r
        self._sal_tab_w   = tab_w
        self._sal_base_x  = 320 + dx

    def _refresh_content(self):
        self.staff_data = self.backend.get_data()
        self._salary_values = self.staff_data["salary"]
        self.canvas.delete("all")
        self.draw_content()
        self.canvas.scale("all", 0, 0, self._s, self._s)
        self.canvas.update_idletasks()
        bbox = self.canvas.bbox("all")
        if bbox:
            self.canvas.configure(scrollregion=(bbox[0], 0, bbox[2], bbox[3] + int(60 * self._s)))

    def _clock_in_or_out(self, event=None):
        try:
            self.backend.clock_in_or_out(self.staff_data.get("employee_id"))
            self._refresh_content()
        except Exception as exc:
            messagebox.showerror("Attendance failed", str(exc), parent=self)

    # ─────────────────────────── SALARY TAB SWITCH ─────────────────
    def _switch_salary_tab(self, tab_name):
        s  = self._s
        cv = self._sal_cv
        tabs = ["Day", "Week", "Month"]

        tab_x = self._sal_base_x
        for tab in tabs:
            tag    = f"sal_tab_{tab}"
            active = tab == tab_name
            fill   = self.C_SALARY_ACTIVE if active else self.C_WHITE

            # Redraw inner pill fill
            cv.delete(tag)
            tab_y1, tab_y2 = self._sal_tab_y1, self._sal_tab_y2
            tab_r  = self._sal_tab_r
            _round_rect(cv, tab_x * s, tab_y1 * s, (tab_x + self._sal_tab_w) * s, tab_y2 * s,
                        radius=int(tab_r * s), fill="#DDDDDD", tags=tag)
            _round_rect(cv, (tab_x + 1) * s, (tab_y1 + 1) * s,
                        (tab_x + self._sal_tab_w - 1) * s, (tab_y2 - 1) * s,
                        radius=int((tab_r - 1) * s), fill=fill, tags=tag)
            cv.create_text((tab_x + self._sal_tab_w // 2) * s,
                           ((tab_y1 + tab_y2) // 2) * s,
                           text=tab,
                           font=("Baghdad", max(9, int(15 * s)), "bold"),
                           fill=self.C_TEXT, tags=tag)
            cv.tag_bind(tag, "<Button-1>", lambda e, t=tab: self._switch_salary_tab(t))
            cv.tag_bind(tag, "<Enter>", lambda e: cv.config(cursor="hand2"))
            cv.tag_bind(tag, "<Leave>", lambda e: cv.config(cursor=""))
            tab_x += self._sal_tab_w + 8

        self._salary_tab.set(tab_name)
        cv.itemconfig(self._salary_text_id,
                      text=self._salary_values[tab_name])


if __name__ == "__main__":
    app = StaffDashboard()
    app.mainloop()
