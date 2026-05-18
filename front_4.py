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


class BookingHistory(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Pet&Bed - Booking History")
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
        self.C_BG = "#A8D3CF"
        self.C_SIDEBAR = "#FFFFFF"
        self.C_TEXT = "#4A3525"
        self.C_TEXT_LIGHT = "#7A685F"
        self.C_WHITE = "#FFFFFF"
        self.C_ACTIVE = "#68BBB2"
        self.C_CARD_BG = "#FFFFFF"
        self.C_DIVIDER = "#DDD8D2"
        self.C_GREEN_CHIP_BG = "#D4EDBA"
        self.C_GREEN_CHIP_TEXT = "#5A8A1A"
        self.C_PINK_CHIP_BG = "#F8D7E0"
        self.C_PINK_CHIP_TEXT = "#C05070"
        self.C_FILTER_BORDER = "#C8C2BC"

        # Fonts
        self.F_LOGO = ("Arial Rounded MT Bold", max(16, int(40 * s)), "bold")
        self.F_NAV = ("Baghdad", max(10, int(18 * s)))
        self.F_TITLE = ("Arial Rounded MT Bold", max(10, int(18 * s)), "bold")
        self.F_DATE = ("Baghdad", max(10, int(18 * s)))
        self.F_SECTION = ("Arial Rounded MT Bold", max(14, int(28 * s)), "bold")
        self.F_TABLE_HEAD = ("Baghdad", max(10, int(16 * s)), "bold")
        self.F_TABLE_BODY = ("Baghdad", max(10, int(15 * s)))
        self.F_CHIP = ("Baghdad", max(9, int(13 * s)))
        self.F_TOGGLE_BTN = ("Baghdad", max(9, int(14 * s)), "bold")
        self.F_SEARCH = ("Baghdad", max(10, int(16 * s)))
        self.F_FILTER = ("Baghdad", max(10, int(15 * s)))

        self.images = []

        # Layout
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

    # ───────────────────── SIDEBAR ─────────────────────
    def draw_sidebar(self):
        cv = self.sidebar_canvas
        _round_rect(cv, -80, 0, 250, 820, radius=30, fill=self.C_SIDEBAR, outline="")
        cv.create_text(125, 70, text="Pet&Bed", font=self.F_LOGO, fill=self.C_TEXT)

        nav_items = ["Dashboard", "Care View", "Booking", "Rooms",
                     "Customer & Pet", "Billing", "Staff", "Report"]
        y = 110
        item_h, item_r, pad_x, right_x, gap = 37, 18, 36, 215, 10

        for i, item in enumerate(nav_items):
            fill = self.C_ACTIVE if i == 2 else "#efefef"
            _round_rect(cv, pad_x, y, right_x, y + item_h, radius=item_r, fill=fill, outline="")
            cv.create_text(pad_x + 20, y + 20, text=item, font=self.F_NAV, fill=self.C_TEXT, anchor="w")
            y += item_h + gap

        # Side icon
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

    # ───────────────────── HELPERS ─────────────────────
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
            if isinstance(crop_align, float) or isinstance(crop_align, int):
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
            if isinstance(crop_align, float) or isinstance(crop_align, int):
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

    def _draw_chip(self, cv, cx, cy, text, bg, fg):
        tw = len(text) * 9 + 24
        th = 24
        x1, y1 = cx - tw // 2, cy - th // 2
        x2, y2 = cx + tw // 2, cy + th // 2
        _round_rect(cv, x1, y1, x2, y2, radius=th // 2, fill=bg, outline="")
        cv.create_text(cx, cy, text=text, font=self.F_CHIP, fill=fg)

    def _draw_filter_btn(self, cv, x1, y1, x2, y2, text):
        r = (y2 - y1) // 2
        # White fill
        _round_rect(cv, x1, y1, x2, y2, radius=r, fill=self.C_WHITE, outline="")
        # Border using line segments + arcs
        d = r * 2
        cv.create_arc(x1, y1, x1 + d, y1 + d, start=90, extent=90,
                      style='arc', outline=self.C_FILTER_BORDER, width=1)
        cv.create_arc(x2 - d, y1, x2, y1 + d, start=0, extent=90,
                      style='arc', outline=self.C_FILTER_BORDER, width=1)
        cv.create_arc(x2 - d, y2 - d, x2, y2, start=270, extent=90,
                      style='arc', outline=self.C_FILTER_BORDER, width=1)
        cv.create_arc(x1, y2 - d, x1 + d, y2, start=180, extent=90,
                      style='arc', outline=self.C_FILTER_BORDER, width=1)
        cv.create_line(x1 + r, y1, x2 - r, y1, fill=self.C_FILTER_BORDER)
        cv.create_line(x1 + r, y2, x2 - r, y2, fill=self.C_FILTER_BORDER)
        cv.create_text((x1 + x2) // 2, (y1 + y2) // 2,
                       text=text, font=self.F_FILTER, fill=self.C_TEXT)

    # ───────────────────── MAIN CONTENT ─────────────────────
    def draw_content(self):
        cv = self.canvas
        dx = -self.BASE_SIDE_W
        y = self.Y_OFF

        # ── HEADER BAR ──
        _round_rect(cv, 300 + dx, 30 + y, 1150 + dx, 70 + y, radius=20, fill=self.C_WHITE)
        cv.create_text(330 + dx, 50 + y, text="Booking",
                       font=self.F_TITLE, fill=self.C_TEXT, anchor="w")
        today_str = datetime.now().strftime("%A, %d/%m/%Y")
        cv.create_text(430 + dx, 50 + y, text=today_str,
                       font=self.F_DATE, fill=self.C_TEXT_LIGHT, anchor="w")

        # Toggle: Bookings | History  (History = active/dark)
        tgl_r = 18
        # Active "History" pill
        _round_rect(cv, 1010 + dx, 32 + y, 1145 + dx, 68 + y, radius=tgl_r, fill=self.C_TEXT)
        cv.create_text(950 + dx, 50 + y, text="Bookings",
                       font=self.F_TOGGLE_BTN, fill=self.C_TEXT)
        cv.create_text(1077 + dx, 50 + y, text="History",
                       font=self.F_TOGGLE_BTN, fill=self.C_WHITE)

        # ── SECTION TITLE ──
        cv.create_text(300 + dx, 95 + y, text="History",
                       font=self.F_SECTION, fill=self.C_TEXT, anchor="w")

        # ── FILTER BOX ──
        fx1, fy1, fx2, fy2 = 300 + dx, 120 + y, 530 + dx, 230 + y
        _round_rect(cv, fx1, fy1, fx2, fy2, radius=20, fill=self.C_WHITE)

        btn_w, btn_h_f = 95, 36
        col_gap, row_gap = 10, 12
        sx = fx1 + 15
        sy = fy1 + 15

        filter_labels = ["Check - in", "Check - out", "Staying", "Cancelled"]
        for idx, label in enumerate(filter_labels):
            col = idx % 2
            row = idx // 2
            bx1 = sx + col * (btn_w + col_gap)
            by1 = sy + row * (btn_h_f + row_gap)
            bx2 = bx1 + btn_w
            by2 = by1 + btn_h_f
            self._draw_filter_btn(cv, bx1, by1, bx2, by2, label)

        # ── CAT IMAGE ──
        _dir = os.path.dirname(__file__)
        cat_path = os.path.join(_dir, "image", "history.jpg")
        cat_w, cat_h = 600, 200
        cat_tk = self.create_rounded_image(cat_path, cat_w, cat_h, radius=18, crop_align=0.7)
        self.images.append(cat_tk)
        cv.create_image(550 + dx, 85 + y, image=cat_tk, anchor="nw")

        # ── TABLE CARD ──
        tbl_y1 = 315 + y
        tbl_y2 = 870 + y
        _round_rect(cv, 300 + dx, tbl_y1, 1150 + dx, tbl_y2, radius=25, fill=self.C_WHITE)

        # Header
        hdr_y = tbl_y1 + 35
        cols = ["#", "Pet", "Owner", "Check in", "Check out", "Room", "Service", "Status"]
        col_xs = [330 + dx, 368 + dx, 435 + dx, 535 + dx, 640 + dx, 730 + dx, 800 + dx, 960 + dx]

        for col, cx in zip(cols, col_xs):
            cv.create_text(cx, hdr_y, text=col, font=self.F_TABLE_HEAD,
                           fill=self.C_TEXT, anchor="w")

        cv.create_line(325 + dx, hdr_y + 22, 1130 + dx, hdr_y + 22,
                       fill=self.C_DIVIDER, width=1)

        # Rows
        table_data = [
            {
                "num": "001", "pet": "Milo", "owner": "Nguyen\nLan",
                "checkin": "04/05", "checkout": "08/05", "room": "R-01",
                "services": [
                    ("Grooming", self.C_GREEN_CHIP_BG, self.C_GREEN_CHIP_TEXT),
                    ("Daycare",  self.C_PINK_CHIP_BG,  self.C_PINK_CHIP_TEXT),
                ],
                "status": "Staying",
            },
            {
                "num": "002", "pet": "Moa", "owner": "Nguyen\nLan",
                "checkin": "04/05", "checkout": "08/05", "room": "R-02",
                "services": [
                    ("Grooming", self.C_GREEN_CHIP_BG, self.C_GREEN_CHIP_TEXT),
                    ("Daycare",  self.C_PINK_CHIP_BG,  self.C_PINK_CHIP_TEXT),
                ],
                "status": "Staying",
            },
        ]

        row_h = 80
        for ri, row in enumerate(table_data):
            ry = hdr_y + 30 + ri * row_h
            cy = ry + row_h // 2

            cv.create_text(col_xs[0], cy, text=row["num"],
                           font=self.F_TABLE_BODY, fill=self.C_TEXT, anchor="w")
            cv.create_text(col_xs[1], cy, text=row["pet"],
                           font=self.F_TABLE_BODY, fill=self.C_TEXT, anchor="w")
            # Owner has newline — centre vertically between the two text lines
            cv.create_text(col_xs[2], cy, text=row["owner"],
                           font=self.F_TABLE_BODY, fill=self.C_TEXT, anchor="w")
            cv.create_text(col_xs[3], cy, text=row["checkin"],
                           font=self.F_TABLE_BODY, fill=self.C_TEXT, anchor="w")
            cv.create_text(col_xs[4], cy, text=row["checkout"],
                           font=self.F_TABLE_BODY, fill=self.C_TEXT, anchor="w")
            cv.create_text(col_xs[5], cy, text=row["room"],
                           font=self.F_TABLE_BODY, fill=self.C_TEXT, anchor="w")

            # Service chips stacked
            chip_cx = col_xs[6] + 52
            chip_y0 = cy - 18
            for ci, (svc, bg, fg) in enumerate(row["services"]):
                self._draw_chip(cv, chip_cx, chip_y0 + ci * 30, svc, bg, fg)

            cv.create_text(col_xs[7], cy, text=row["status"],
                           font=self.F_TABLE_BODY, fill=self.C_TEXT, anchor="w")

            # Row divider (not after last row)
            if ri < len(table_data) - 1:
                cv.create_line(325 + dx, ry + row_h - 1, 1130 + dx, ry + row_h - 1,
                               fill=self.C_DIVIDER, width=1)


if __name__ == "__main__":
    app = BookingHistory()
    app.mainloop()