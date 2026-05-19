import tkinter as tk
from PIL import Image, ImageTk, ImageDraw
import os
import sys
from datetime import datetime


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


class StaffDashboard(tk.Tk):
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
        self._salary_values = {"Day": "328,570đ", "Week": "2,300,000đ", "Month": "9,200,000đ"}

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
            fill = self.C_ACTIVE if i == 6 else "#efefef"
            _round_rect(cv, pad_x, y, right_x, y + item_h, radius=item_r, fill=fill, outline="")
            cv.create_text(pad_x + 20, y + 20, text=item, font=self.F_NAV,
                           fill=self.C_WHITE if i == 6 else self.C_TEXT, anchor="w")
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
        cv.tag_bind("logout_btn", "<Button-1>", lambda e: self.destroy())

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
        _round_rect(cv, 302 + dx, 30 + y, 1169 + dx, 70 + y, radius=20, fill=self.C_WHITE)
        cv.create_text(332 + dx, 50 + y, text="Staff",
                       font=self.F_TITLE, fill=self.C_TEXT, anchor="w")
        cv.create_text(402 + dx, 50 + y, text="Employee",
                       font=self.F_DATE, fill=self.C_TEXT_LIGHT, anchor="w")
        cv.create_text(512 + dx, 50 + y,
                       text=datetime.now().strftime("%d/%m/%Y"),
                       font=self.F_DATE, fill=self.C_TEXT_LIGHT, anchor="w")

        # Clock in button (dark pill, right side of header)
        ci_w, ci_h = 150, 38
        ci_x2 = 1169 + dx
        ci_x1 = ci_x2 - ci_w
        ci_y1 = 31 + y
        ci_y2 = ci_y1 + ci_h
        _round_rect(cv, ci_x1, ci_y1, ci_x2, ci_y2,
                    radius=ci_h // 2, fill=self.C_CLOCKIN_BG, tags="clockin")
        cv.create_text((ci_x1 + ci_x2) // 2, (ci_y1 + ci_y2) // 2,
                       text="Clock in", font=self.F_CLOCKIN_BTN,
                       fill=self.C_WHITE, tags="clockin")

        # ── EMPLOYEE NAME + ID + MONTH SELECTOR ──
        name_y = 120 + y
        cv.create_text(300 + dx, name_y + 12, text="Anh Tuấn",
                       font=self.F_EMP_NAME, fill=self.C_TEXT, anchor="w")
        cv.create_text(300 + dx, name_y + int(36 * s), text="EMP002",
                       font=self.F_EMP_ID, fill=self.C_TEXT_LIGHT, anchor="w")

        # Month selector pill
        ms_x1, ms_y1 = 480 + dx, name_y - 4
        ms_x2, ms_y2 = 670 + dx, name_y + 38
        ms_r = (ms_y2 - ms_y1) // 2
        _round_rect(cv, ms_x1, ms_y1, ms_x2, ms_y2, radius=ms_r, fill=self.C_WHITE)
        cv.create_text(ms_x1 + 20, (ms_y1 + ms_y2) // 2,
                       text="05/2026", font=self.F_MONTH_SEL,
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
                       text="4", font=self.F_STAT_VAL, fill=self.C_TEXT)

        # Total Hours card
        _round_rect(cv, 475 + dx, card_y1, 665 + dx, card_y2, radius=20, fill=self.C_WHITE)
        cv.create_text(570 + dx, card_y1 + 22,
                       text="Total Hours", font=self.F_STAT_LABEL, fill=self.C_TEXT)
        cv.create_text(570 + dx, card_y1 + 73,
                       text="40", font=self.F_STAT_VAL, fill=self.C_TEXT)

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
        attendance_data = [
            ("06/05/2025", "08:02", "–",     "–", "–", "–"),
            ("05/05/2025", "08:02", "10:00", "2", "0", "0"),
            ("05/05/2025", "08:02", "10:00", "2", "0", "0"),
            ("05/05/2025", "08:02", "10:00", "2", "0", "0"),
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