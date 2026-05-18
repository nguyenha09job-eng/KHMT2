import tkinter as tk
from PIL import Image, ImageTk, ImageDraw
import os
import sys
from datetime import datetime


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
        self.F_HEADER_TAB   = ("Baghdad", max(10, int(17 * s)), "bold")
        self.F_HEADER_LIGHT = ("Baghdad", max(10, int(15 * s)))
        self.F_TITLE_BIG    = ("Arial Rounded MT Bold", max(18, int(32 * s)), "bold")
        self.F_SECTION      = ("Arial Rounded MT Bold", max(14, int(28 * s)), "bold")
        self.F_CARD_LABEL   = ("Baghdad", max(9, int(15 * s)), "bold")
        self.F_CARD_NUM     = ("Arial Rounded MT Bold", max(28, int(70 * s)), "bold")
        self.F_CARD_NUM_MED = ("Arial Rounded MT Bold", max(22, int(55 * s)), "bold")
        self.F_CARD_SUB     = ("Baghdad", max(9, int(15 * s)))
        self.F_STAFF_NAME   = ("Baghdad", max(10, int(16 * s)), "bold")
        self.F_STAFF_INFO   = ("Baghdad", max(9, int(14 * s)))
        self.F_CHIP         = ("Baghdad", max(9, int(13 * s)), "bold")
        self.F_CHIP_SMALL   = ("Baghdad", max(9, int(12 * s)))
        self.F_ATT_TITLE    = ("Baghdad", max(11, int(17 * s)), "bold")
        self.F_ATT_BODY     = ("Baghdad", max(9, int(14 * s)))
        self.F_ATT_VALUE    = ("Baghdad", max(9, int(14 * s)))
        self.F_SALARY_NUM   = ("Arial Rounded MT Bold", max(14, int(22 * s)), "bold")
        self.F_TOGGLE       = ("Baghdad", max(9, int(13 * s)), "bold")
        self.F_DROPDOWN     = ("Baghdad", max(10, int(16 * s)))
        self.F_NEW_BTN      = ("Arial Rounded MT Bold", max(12, int(18 * s)), "bold")

        self.images = []

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
            fill = self.C_ACTIVE if i == 6 else "#efefef"
            _round_rect(cv, pad_x, y, right_x, y + item_h, radius=item_r, fill=fill, outline="")
            cv.create_text(pad_x + 20, y + 20, text=item,
                           font=self.F_NAV, fill=self.C_TEXT, anchor="w")
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

    def _draw_chip(self, cv, cx, cy, text, bg, fg, font=None):
        if font is None:
            font = self.F_CHIP
        tw = len(text) * 9 + 24
        th = 26
        x1, y1 = cx - tw // 2, cy - th // 2
        x2, y2 = cx + tw // 2, cy + th // 2
        _round_rect(cv, x1, y1, x2, y2, radius=th // 2, fill=bg, outline="")
        cv.create_text(cx, cy, text=text, font=font, fill=fg)

    # ─────────────────── MAIN CONTENT ──────────────────────
    def draw_content(self):
        cv = self.canvas
        dx = -self.BASE_SIDE_W      # offset because sidebar is separate
        y  = self.Y_OFF

        # ══════════════════════════════════════════════════
        # 1.  HEADER BAR
        # ══════════════════════════════════════════════════
        hbar_x1 = 300 + dx
        hbar_y1 = 30  + y
        hbar_x2 = 1168 + dx
        hbar_y2 = 70  + y
        _round_rect(cv, hbar_x1, hbar_y1, hbar_x2, hbar_y2, radius=20, fill=self.C_WHITE)

        # "Staff" (bold) | Manager | date
        cv.create_text(hbar_x1 + 30, (hbar_y1 + hbar_y2) // 2,
                       text="Staff", font=self.F_HEADER_TAB, fill=self.C_TEXT, anchor="w")
        cv.create_text(hbar_x1 + 100, (hbar_y1 + hbar_y2) // 2,
                       text="Manager", font=self.F_HEADER_LIGHT, fill=self.C_TEXT_LIGHT, anchor="w")
        today_str = datetime.now().strftime("%d/%m/%Y")
        cv.create_text(hbar_x1 + 210, (hbar_y1 + hbar_y2) // 2,
                       text=today_str, font=self.F_HEADER_LIGHT, fill=self.C_TEXT_LIGHT, anchor="w")

        # "+ New staff" dark pill button (right side)
        nbtn_w, nbtn_h = 190, 40
        nbtn_x2 = hbar_x2 - 14
        nbtn_x1 = nbtn_x2 - nbtn_w
        nbtn_cy = (hbar_y1 + hbar_y2) // 2
        nbtn_y1 = nbtn_cy - nbtn_h // 2
        nbtn_y2 = nbtn_cy + nbtn_h // 2
        _round_rect(cv, nbtn_x1, nbtn_y1, nbtn_x2, nbtn_y2,
                    radius=nbtn_h // 2, fill=self.C_DARK_BTN, outline="")
        cv.create_text((nbtn_x1 + nbtn_x2) // 2, nbtn_cy,
                       text="+ New staff", font=self.F_NEW_BTN, fill=self.C_WHITE)

        # ══════════════════════════════════════════════════
        # 2.  TITLE "Thu Lan"
        # ══════════════════════════════════════════════════
        title_y = hbar_y2 + 42
        cv.create_text(hbar_x1, title_y,
                       text="Thu Lan", font=self.F_TITLE_BIG, fill=self.C_TEXT, anchor="w")

        # ══════════════════════════════════════════════════
        # 3.  DROPDOWN "05/2026"
        # ══════════════════════════════════════════════════
        dd_x1 = hbar_x1
        dd_y1 = title_y + 28
        dd_x2 = hbar_x1 + 260
        dd_y2 = dd_y1 + 40
        _round_rect(cv, dd_x1, dd_y1, dd_x2, dd_y2, radius=20, fill=self.C_WHITE, outline="")

        cv.create_text(dd_x1 + 16, (dd_y1 + dd_y2) // 2,
                       text="05/2026", font=self.F_DROPDOWN, fill=self.C_TEXT, anchor="w")
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
        cv.create_text(card_cx, row1_y1 + 88,
                       text="4", font=self.F_CARD_NUM, fill=self.C_TEXT)
        cv.create_text(card_cx, row1_y2 - 22,
                       text="3 partime - 1 manager", font=self.F_CARD_SUB, fill=self.C_TEXT_LIGHT)

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
                "big":    "2",
                "sub":    "expected 3",
                "font":   self.F_CARD_NUM,
            },
            {
                "label":  "Estimated Salary This Month",
                "big":    "12.7",
                "sub":    "millions",
                "font":   self.F_CARD_NUM_MED,
            },
            {
                "label":  "Total Working Hours",
                "big":    "148",
                "sub":    "May (up to now)",
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
            cv.create_text(scx, row2_y1 + 88,
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

        staff_list = [
            {"name": "Thu Lan",  "emp": "EMP001", "phone": "0901111222",
             "chip": "Manager", "chip_bg": self.C_GREEN_BG, "chip_fg": self.C_GREEN_FG},
            {"name": "Anh Tuấn", "emp": "EMP002", "phone": "0902222333",
             "chip": "+ Penalty", "chip_bg": self.C_PINK_BG, "chip_fg": self.C_PINK_FG},
            {"name": "Anh Tuấn", "emp": "EMP002", "phone": "0902222333",
             "chip": "+ Penalty", "chip_bg": self.C_PINK_BG, "chip_fg": self.C_PINK_FG},
            {"name": "Anh Tuấn", "emp": "EMP002", "phone": "0902222333",
             "chip": "+ Penalty", "chip_bg": self.C_PINK_BG, "chip_fg": self.C_PINK_FG},
            {"name": "Anh Tuấn", "emp": "EMP002", "phone": "0902222333",
             "chip": "+ Penalty", "chip_bg": self.C_PINK_BG, "chip_fg": self.C_PINK_FG},
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

            # Chip
            self._draw_chip(cv, chip_x_right, cy,
                            st["chip"], st["chip_bg"], st["chip_fg"], self.F_CHIP_SMALL)

            # Divider (not after last)
            if ri < len(staff_list) - 1:
                cv.create_line(left_x1 + 36, ry2, left_x2 - 36, ry2,
                               fill=self.C_DIVIDER, width=1)

        # ── RIGHT: Attendance Today card ──
        _round_rect(cv, right_x1, bot_y1, right_x2, bot_y2, radius=26, fill=self.C_CARD)

        # Card header row
        att_title_y = bot_y1 + 28
        cv.create_text(right_x1 + 22, att_title_y,
                       text="Attendance Today", font=self.F_ATT_TITLE, fill=self.C_TEXT, anchor="w")
        # "Yes" green chip
        self._draw_chip(cv, right_x2 - 38, att_title_y,
                        "Yes", self.C_GREEN_BG, self.C_GREEN_FG, self.F_CHIP_SMALL)

        # Divider
        cv.create_line(right_x1 + 15, att_title_y + 18,
                       right_x2 - 15, att_title_y + 18,
                       fill=self.C_DIVIDER, width=1)

        # Employee name
        emp_name_y = att_title_y + 38
        cv.create_text(right_x1 + 22, emp_name_y,
                       text="Anh Tuấn   EMP002",
                       font=self.F_STAFF_NAME, fill=self.C_TEXT, anchor="w")

        # Attendance details table
        details = [
            ("Clock - in",      "08:00"),
            ("Clock - out",     "10:00"),
            ("Working hour",    "2 hours"),
            ("Overtime hour",   "0 hours"),
            ("Penalty",         "0"),
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
                       text="Good job", font=self.F_ATT_BODY, fill=self.C_TEXT_LIGHT, anchor="w")

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
                       text="2,300,000đ", font=self.F_SALARY_NUM, fill=self.C_TEXT, anchor="e")


if __name__ == "__main__":
    app = StaffPage()
    app.mainloop()
