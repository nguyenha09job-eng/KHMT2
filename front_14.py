import tkinter as tk
from PIL import Image, ImageTk, ImageDraw
import os
import sys
import math
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


def _round_rect_outline(cv, x1, y1, x2, y2, radius=25, fill="", outline="", width=1, tags=""):
    _round_rect(cv, x1, y1, x2, y2, radius=radius, fill=fill)
    d = 2 * radius
    items = []
    items.append(cv.create_arc(x1, y1, x1 + d, y1 + d, start=90, extent=90, style='arc', outline=outline, width=width, tags=tags))
    items.append(cv.create_arc(x2 - d, y1, x2, y1 + d, start=0, extent=90, style='arc', outline=outline, width=width, tags=tags))
    items.append(cv.create_arc(x2 - d, y2 - d, x2, y2, start=270, extent=90, style='arc', outline=outline, width=width, tags=tags))
    items.append(cv.create_arc(x1, y2 - d, x1 + d, y2, start=180, extent=90, style='arc', outline=outline, width=width, tags=tags))
    items.append(cv.create_line(x1 + radius, y1, x2 - radius, y1, fill=outline, width=width, tags=tags))
    items.append(cv.create_line(x1 + radius, y2, x2 - radius, y2, fill=outline, width=width, tags=tags))
    items.append(cv.create_line(x1, y1 + radius, x1, y2 - radius, fill=outline, width=width, tags=tags))
    items.append(cv.create_line(x2, y1 + radius, x2, y2 - radius, fill=outline, width=width, tags=tags))
    return tuple(items)


class ReportDashboard(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Pet&Bed - Report")
        self.attributes("-fullscreen", True)
        self.configure(bg="#F5C97A")
        self.update_idletasks()

        self.W = self.winfo_width()
        self.H = self.winfo_height()
        self.BASE_W = 1200.0
        self.BASE_H = 850.0
        self._s = self.W / self.BASE_W
        s = self._s
        self.Y_OFF = 20

        # Colors
        self.C_BG          = "#F5C97A"
        self.C_SIDEBAR     = "#FFFFFF"
        self.C_TEXT        = "#4A3525"
        self.C_TEXT_LIGHT  = "#7A685F"
        self.C_WHITE       = "#FFFFFF"
        self.C_ACTIVE      = "#F5A623"
        self.C_DIVIDER     = "#ECD8C0"
        self.C_CARD_BG     = "#FFFFFF"
        self.C_BAR         = "#C8E066"   # yellow-green bars
        self.C_GREEN_LIGHT = "#C8E066"
        self.C_PINK        = "#F4A0B0"
        self.C_TEAL        = "#60C0B8"
        self.C_ORANGE_PIE  = "#E8A040"
        self.C_GREY_PIE    = "#C8C8C8"

        # Quick-filter tab active bg
        self.C_TAB_ACTIVE  = "#C8E066"
        self._active_tab   = "This week"

        # Fonts
        self.F_LOGO        = ("Arial Rounded MT Bold", max(16, int(40 * s)), "bold")
        self.F_NAV         = ("Baghdad", max(10, int(18 * s)))
        self.F_TITLE       = ("Arial Rounded MT Bold", max(10, int(18 * s)), "bold")
        self.F_DATE        = ("Baghdad", max(10, int(15 * s)))
        self.F_SECTION     = ("Arial Rounded MT Bold", max(12, int(18 * s)), "bold")
        self.F_CARD_LBL    = ("Baghdad", max(10, int(15 * s)), "bold")
        self.F_CARD_VAL    = ("Arial Rounded MT Bold", max(20, int(52 * s)), "bold")
        self.F_CARD_SUB    = ("Baghdad", max(9,  int(13 * s)))
        self.F_AXIS        = ("Baghdad", max(9,  int(13 * s)))
        self.F_BAR_VAL     = ("Baghdad", max(9,  int(12 * s)), "bold")
        self.F_PIE_LBL     = ("Baghdad", max(9,  int(13 * s)))
        self.F_TAB         = ("Baghdad", max(10, int(14 * s)))
        self.F_TABLE_HEAD  = ("Baghdad", max(10, int(14 * s)), "bold")
        self.F_TABLE_BODY  = ("Baghdad", max(9,  int(13 * s)))
        self.F_CHIP        = ("Baghdad", max(9,  int(12 * s)), "bold")

        self.images = []

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
            self.canvas.configure(scrollregion=(bbox[0], 0, bbox[2], bbox[3] + int(80 * s)))

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
            fill = self.C_ACTIVE if i == 7 else "#efefef"
            _round_rect(cv, pad_x, y, right_x, y + item_h, radius=item_r, fill=fill, outline="")
            cv.create_text(pad_x + 20, y + 20, text=item, font=self.F_NAV,
                           fill=self.C_WHITE if i == 7 else self.C_TEXT, anchor="w")
            y += item_h + gap

        # Hedgehog / porcupine icon
        _dir = os.path.dirname(__file__)
        icon_path = os.path.join(_dir, "image", "hedgehog.png")
        s = self._s
        iw, ih = int(130 * s), int(90 * s)
        sr = int(16 * s)
        if os.path.exists(icon_path):
            img = Image.open(icon_path).convert("RGBA")
            img = img.resize((iw, ih), Image.Resampling.LANCZOS)
            mask = Image.new("L", (iw, ih), 0)
            ImageDraw.Draw(mask).rounded_rectangle((0, 0, iw, ih), radius=sr, fill=255)
            result = Image.new("RGBA", (iw, ih), (0, 0, 0, 0))
            result.paste(img, (0, 0), mask=mask)
            icon_tk = ImageTk.PhotoImage(result)
            self.images.append(icon_tk)
            cv.create_image(125 - iw // 2, 570, image=icon_tk, anchor="nw")

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
            img = Image.new("RGB", (sw, sh), color="#C8A860")
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

    # ─────────────────────────── BAR CHART ──────────────────────────
    def _draw_bar_chart(self, cv, x1, y1, x2, y2, title, data):
        """Draw a bar chart inside the given bounding box."""
        _round_rect(cv, x1, y1, x2, y2, radius=20, fill=self.C_WHITE)
        cx = (x1 + x2) // 2

        cv.create_text(cx, y1 + 22, text=title, font=self.F_SECTION, fill=self.C_TEXT)

        pad_l, pad_r, pad_t, pad_b = 52, 20, 50, 50
        chart_x1 = x1 + pad_l
        chart_x2 = x2 - pad_r
        chart_y1 = y1 + pad_t
        chart_y2 = y2 - pad_b

        max_val   = max(v for _, v in data)
        n         = len(data)
        bar_gap   = 14
        bar_w     = (chart_x2 - chart_x1 - bar_gap * (n - 1)) / n
        chart_h   = chart_y2 - chart_y1

        # Y-axis label "Million"
        cv.create_text(x1 + 14, (chart_y1 + chart_y2) // 2,
                       text="Million", font=self.F_AXIS, fill=self.C_TEXT_LIGHT,
                       angle=90)

        # Y grid lines and labels
        for val in [0, 20, 40, 60, 80]:
            gy = chart_y2 - (val / max_val) * chart_h
            cv.create_line(chart_x1, gy, chart_x2, gy,
                           fill="#E8E0D8", dash=(4, 4))
            cv.create_text(chart_x1 - 6, gy, text=str(val),
                           font=self.F_AXIS, fill=self.C_TEXT_LIGHT, anchor="e")

        # Bars
        for i, (label, val) in enumerate(data):
            bx1 = chart_x1 + i * (bar_w + bar_gap)
            bx2 = bx1 + bar_w
            bh  = (val / max_val) * chart_h
            by1 = chart_y2 - bh
            by2 = chart_y2
            br  = int(bar_w * 0.25)
            _round_rect(cv, bx1, by1, bx2, by2, radius=br, fill=self.C_BAR)
            # Value label above bar
            cv.create_text((bx1 + bx2) / 2, by1 - 8, text=str(val),
                           font=self.F_BAR_VAL, fill=self.C_TEXT)
            # X label
            cv.create_text((bx1 + bx2) / 2, chart_y2 + 16, text=label,
                           font=self.F_AXIS, fill=self.C_TEXT)

        # X axis line
        cv.create_line(chart_x1, chart_y2, chart_x2, chart_y2,
                       fill=self.C_TEXT_LIGHT)

    # ─────────────────────────── DONUT CHART ────────────────────────
    def _draw_donut(self, cv, cx, cy, r_out, r_in, segments, title, x1, y1, x2, y2):
        """Draw a donut chart. segments = [(pct, color, label_str), ...]"""
        _round_rect(cv, x1, y1, x2, y2, radius=20, fill=self.C_WHITE)
        cv.create_text((x1 + x2) // 2, y1 + 20,
                       text=title, font=self.F_SECTION, fill=self.C_TEXT)

        start_angle = 90
        for pct, color, label in segments:
            extent = pct / 100 * 360
            cv.create_arc(cx - r_out, cy - r_out, cx + r_out, cy + r_out,
                          start=start_angle, extent=-extent,
                          fill=color, outline="")
            # Label placement
            mid_angle = math.radians(start_angle - extent / 2)
            lx = cx + (r_out + 18) * math.cos(mid_angle)
            ly = cy - (r_out + 18) * math.sin(mid_angle)
            cv.create_text(lx, ly, text=label, font=self.F_PIE_LBL, fill=self.C_TEXT)
            start_angle -= extent

        # White hole for donut
        cv.create_oval(cx - r_in, cy - r_in, cx + r_in, cy + r_in,
                       fill=self.C_WHITE, outline="")

    # ─────────────────────────── MAIN CONTENT ───────────────────────
    def draw_content(self):
        cv   = self.canvas
        dx   = -self.BASE_SIDE_W
        y    = self.Y_OFF
        cw   = 848        # content width (1150-300-2)
        cx0  = 300 + dx   # left edge of content
        cx1  = cx0 + cw   # right edge
        _dir = os.path.dirname(__file__)

        # ── HEADER BAR ──
        _round_rect(cv, cx0, 30 + y, cx1, 68 + y, radius=20, fill=self.C_WHITE)
        cv.create_text(cx0 + 30, 49 + y, text="Report",
                       font=self.F_TITLE, fill=self.C_TEXT, anchor="w")
        cv.create_text(cx0 + 115, 49 + y,
                       text="06/05/2025",
                       font=self.F_DATE, fill=self.C_TEXT_LIGHT, anchor="w")

        # ── DATE RANGE + QUICK TABS ──
        dr_y1, dr_y2 = 82 + y, 118 + y
        dr_r = (dr_y2 - dr_y1) // 2
        _round_rect(cv, cx0, dr_y1, cx0 + 390, dr_y2, radius=dr_r, fill=self.C_WHITE)
        cv.create_text(cx0 + 18, (dr_y1 + dr_y2) // 2,
                       text="Custom", font=self.F_TAB, fill=self.C_TEXT, anchor="w")
        cv.create_text(cx0 + 90, (dr_y1 + dr_y2) // 2,
                       text="01/04/2025", font=self.F_DATE, fill=self.C_TEXT, anchor="w")
        # calendar icon placeholder
        cv.create_text(cx0 + 185, (dr_y1 + dr_y2) // 2,
                       text="🗓", font=("Segoe UI Emoji", 14), anchor="w")
        cv.create_text(cx0 + 210, (dr_y1 + dr_y2) // 2,
                       text="→", font=self.F_DATE, fill=self.C_TEXT, anchor="w")
        cv.create_text(cx0 + 238, (dr_y1 + dr_y2) // 2,
                       text="06/05/2025", font=self.F_DATE, fill=self.C_TEXT, anchor="w")
        cv.create_text(cx0 + 343, (dr_y1 + dr_y2) // 2,
                       text="🗓", font=("Segoe UI Emoji", 14), anchor="w")

        # ── CAT BANNER IMAGE ──
        img_path = os.path.join(_dir, "image", "report.jpg")
        img_tk   = self.create_rounded_image(img_path, 550, 160, radius=18)
        self.images.append(img_tk)
        cv.create_image(cx0, 130 + y, image=img_tk, anchor="nw")

        # ── QUICK FILTER CONTAINER CARD & TABS ──
        card_x1 = cx0 + 568
        card_y1 = 130 + y
        card_x2 = cx1
        card_y2 = card_y1 + 160
        _round_rect(cv, card_x1, card_y1, card_x2, card_y2, radius=26, fill=self.C_WHITE)

        tabs = ["Today", "This week", "This month", "Last month"]
        tab_w, tab_h = 240, 28
        tab_gap = 8
        tab_y_start = card_y1 + 12

        for tab in tabs:
            ty1 = tab_y_start
            ty2 = ty1 + tab_h
            active = (tab == self._active_tab)
            tx1 = card_x1 + 20
            tx2 = card_x2 - 20
            tag = f"qtab_{tab.replace(' ', '_')}"
            
            if active:
                _round_rect(cv, tx1, ty1, tx2, ty2, radius=tab_h // 2, fill=self.C_TAB_ACTIVE, tags=tag)
            else:
                _round_rect_outline(cv, tx1, ty1, tx2, ty2, radius=tab_h // 2, fill=self.C_WHITE, outline="#C8C2BC", width=1, tags=tag)
                
            cv.create_text((tx1 + tx2) // 2, (ty1 + ty2) // 2,
                           text=tab, font=self.F_TAB, fill=self.C_TEXT, tags=tag)
            tab_y_start += tab_h + tab_gap

        # ── BAR CHART: Revenue Trend ──
        bar_data = [("Mon", 60), ("Tue", 45), ("Wed", 78),
                    ("Thu", 30), ("Fri", 20), ("Sat", 10), ("Sun", 50)]
        bar_y1 = 308 + y
        bar_y2 = bar_y1 + 240
        self._draw_bar_chart(cv, cx0, bar_y1, cx1, bar_y2,
                             "Revenue Trend – This Week", bar_data)

        # ── STAT CARDS ──
        sc_y1 = bar_y2 + 18
        sc_y2 = sc_y1 + 130
        sc_w  = (cw - 20) // 3

        stats = [
            ("Total Revenue", "4.2M", "+8% vs prior period"),
            ("Transactions",  "12",   "avg 350k / order"),
            ("Room Occupancy","72%",  ""),
        ]
        for i, (lbl, val, sub) in enumerate(stats):
            sx1 = cx0 + i * (sc_w + 10)
            sx2 = sx1 + sc_w
            _round_rect(cv, sx1, sc_y1, sx2, sc_y2, radius=20, fill=self.C_WHITE)
            scx = (sx1 + sx2) // 2
            cv.create_text(scx, sc_y1 + 22, text=lbl,
                           font=self.F_CARD_LBL, fill=self.C_TEXT)
            cv.create_text(scx, sc_y1 + 72, text=val,
                           font=self.F_CARD_VAL, fill=self.C_TEXT)
            if sub:
                cv.create_text(scx, sc_y2 - 18, text=sub,
                               font=self.F_CARD_SUB, fill=self.C_TEXT_LIGHT)

        # ── DONUT CHARTS ──
        donut_y1 = sc_y2 + 18
        donut_y2 = donut_y1 + 200
        donut_w  = (cw - 16) // 2

        # Revenue by Service
        d1x1, d1x2 = cx0, cx0 + donut_w
        d1cx = d1x1 + donut_w // 2 - 20
        d1cy = (donut_y1 + donut_y2) // 2 + 10
        self._draw_donut(cv, d1cx, d1cy, 68, 38,
                         [(61, self.C_BAR,       "Room Stay\n61%"),
                          (21, self.C_PINK,      "Grooming\n21%"),
                          (11, self.C_TEAL,      "Transport\n11%"),
                          (7,  self.C_ORANGE_PIE,"")],
                         "Revenue by Service",
                         d1x1, donut_y1, d1x2, donut_y2)

        # Revenue by Memberships
        d2x1, d2x2 = cx0 + donut_w + 16, cx1
        d2cx = d2x1 + (d2x2 - d2x1) // 2 - 10
        d2cy = (donut_y1 + donut_y2) // 2 + 10
        self._draw_donut(cv, d2cx, d2cy, 68, 38,
                         [(74, self.C_BAR,      "VIP\n74,4%"),
                          (26, self.C_GREY_PIE, "Non - VIP\n25,6%")],
                         "Revenue by Memberships",
                         d2x1, donut_y1, d2x2, donut_y2)

        # ── PAYMENT METHODS STACKED BAR ──
        pm_y1 = donut_y2 + 18
        pm_y2 = pm_y1 + 150
        _round_rect(cv, cx0, pm_y1, cx1, pm_y2, radius=20, fill=self.C_WHITE)
        pmcx = (cx0 + cx1) // 2
        cv.create_text(pmcx, pm_y1 + 20, text="Payment Methods",
                       font=self.F_SECTION, fill=self.C_TEXT)

        # Legend
        legend_items = [("Cash", self.C_PINK), ("Bank Transfer", self.C_TEAL), ("Card", self.C_ORANGE_PIE)]
        lx = pmcx - 160
        for lbl, col in legend_items:
            cv.create_oval(lx - 6, pm_y1 + 40, lx + 6, pm_y1 + 52, fill=col, outline="")
            cv.create_text(lx + 12, pm_y1 + 46, text=lbl,
                           font=self.F_PIE_LBL, fill=self.C_TEXT, anchor="w")
            lx += 130

        # Stacked bar
        bar_x1  = cx0 + 20
        bar_x2  = cx1 - 20
        bbar_y1 = pm_y1 + 65
        bbar_y2 = bbar_y1 + 30
        bar_r   = (bbar_y2 - bbar_y1) // 2
        total_w = bar_x2 - bar_x1
        segments = [(0.42, self.C_PINK), (0.45, self.C_TEAL), (0.13, self.C_ORANGE_PIE)]
        cur_x = bar_x1
        for i, (pct, col) in enumerate(segments):
            seg_w = int(pct * total_w)
            if i == 0:
                cv.create_arc(cur_x, bbar_y1, cur_x + bar_r * 2, bbar_y2,
                              start=90, extent=180, fill=col, outline=col)
                cv.create_rectangle(cur_x + bar_r, bbar_y1, cur_x + seg_w, bbar_y2, fill=col, outline=col)
            elif i == len(segments) - 1:
                cv.create_rectangle(cur_x, bbar_y1, cur_x + seg_w - bar_r, bbar_y2, fill=col, outline=col)
                cv.create_arc(cur_x + seg_w - bar_r * 2, bbar_y1, cur_x + seg_w, bbar_y2,
                              start=270, extent=180, fill=col, outline=col)
            else:
                cv.create_rectangle(cur_x, bbar_y1, cur_x + seg_w, bbar_y2, fill=col, outline=col)
            cur_x += seg_w

        # X-axis labels
        x_labels = ["0%", "20%", "40%", "60%", "80%", "100%"]
        for i, lbl in enumerate(x_labels):
            lx = bar_x1 + int(i / 5 * total_w)
            cv.create_text(lx, bbar_y2 + 14, text=lbl,
                           font=self.F_AXIS, fill=self.C_TEXT_LIGHT)

        # ── DISCOUNTS & PROMOTIONS TABLE ──
        disc_y = pm_y2 + 30
        cv.create_text(cx0, disc_y, text="Discounts & Promotions Applied",
                       font=self.F_SECTION, fill=self.C_TEXT, anchor="w")

        tbl_y1 = disc_y + 24
        tbl_y2 = tbl_y1 + 130
        _round_rect(cv, cx0, tbl_y1, cx1, tbl_y2, radius=18, fill=self.C_WHITE)

        cols   = ["Booking", "Customer", "Original", "Discount", "Type", "Final Paid"]
        col_xs = [cx0 + 30, cx0 + 130, cx0 + 270, cx0 + 400, cx0 + 520, cx0 + 660]
        hdr_y  = tbl_y1 + 24

        for col, lcx in zip(cols, col_xs):
            cv.create_text(lcx, hdr_y, text=col, font=self.F_TABLE_HEAD,
                           fill=self.C_TEXT, anchor="w")
        cv.create_line(cx0 + 15, hdr_y + 18, cx1 - 15, hdr_y + 18,
                       fill=self.C_DIVIDER, width=1)

        disc_data = [
            ("#1042", "Nguyễn Lan", "875.000đ", "-87.500đ", "VIP",     "787.500đ", "#F9D0D8", "#C05070"),
            ("#1042", "Nguyễn Lan", "875.000đ", "-87.500đ", "Premium", "787.500đ", "#D4EDBA", "#5A8A1A"),
        ]
        row_h = 36
        for ri, row in enumerate(disc_data):
            ry  = hdr_y + 22 + ri * row_h
            rcy = ry + row_h // 2

            for ci, (val, lcx) in enumerate(zip(row[:6], col_xs)):
                if ci == 4:   # Type chip
                    chip_bg, chip_fg = row[6], row[7]
                    cw2 = 72
                    _round_rect(cv, lcx, rcy - 12, lcx + cw2, rcy + 12,
                                radius=12, fill=chip_bg)
                    cv.create_text(lcx + cw2 // 2, rcy, text=val,
                                   font=self.F_CHIP, fill=chip_fg)
                else:
                    cv.create_text(lcx, rcy, text=val,
                                   font=self.F_TABLE_BODY, fill=self.C_TEXT, anchor="w")

            if ri < len(disc_data) - 1:
                cv.create_line(cx0 + 15, ry + row_h - 1, cx1 - 15, ry + row_h - 1,
                               fill=self.C_DIVIDER, width=1)

        # ── TOTAL VALUE GIVEN AWAY ──
        tot_y = tbl_y2 + 18
        cv.create_text(cx1 - 180, tot_y,
                       text="Total value given away this period",
                       font=self.F_CARD_SUB, fill=self.C_TEXT, anchor="e")
        cv.create_text(cx1 - 15, tot_y,
                       text="-527.500đ",
                       font=("Baghdad", max(10, int(16 * self._s)), "bold"),
                       fill="#C83040", anchor="e")


if __name__ == "__main__":
    app = ReportDashboard()
    app.mainloop()