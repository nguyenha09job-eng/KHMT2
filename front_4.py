import tkinter as tk
from PIL import Image, ImageTk, ImageDraw
import os
import sys
from datetime import datetime

from database import DatabaseConnection


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


class BookingHistoryBackend:
    """Data layer for Booking History, kept in this screen file."""

    STATUS_FILTERS = {
        "Check - in": "booked",
        "Check - out": "completed",
        "Staying": "checked_in",
        "Cancelled": "cancelled",
    }

    STATUS_LABELS = {
        "booked": "Check-in",
        "checked_in": "Staying",
        "completed": "Check-out",
        "cancelled": "Cancelled",
    }

    def __init__(self, db=None):
        self.db = db or DatabaseConnection()

    @staticmethod
    def _title(value, default="-"):
        if value in (None, ""):
            return default
        return str(value).replace("_", " ").title()

    @staticmethod
    def _format_owner(name):
        if not name:
            return "-"
        parts = str(name).split()
        if len(parts) <= 1:
            return parts[0]
        mid = max(1, len(parts) // 2)
        return " ".join(parts[:mid]) + "\n" + " ".join(parts[mid:])

    @staticmethod
    def _format_room(room_id):
        if room_id is None:
            return "-"
        return f"R-{int(room_id):02d}"

    def get_bookings(self, filter_label=None, limit=80):
        status_name = self.STATUS_FILTERS.get(filter_label)
        where_clause = ""
        params = []
        if status_name:
            where_clause = "WHERE bs.status_name = %s"
            params.append(status_name)

        params.append(limit)
        rows = self.db.fetch_all(
            f"""
            SELECT
                b.booking_id,
                p.pet_name,
                c.full_name AS owner_name,
                DATE_FORMAT(b.check_in, '%d/%m') AS checkin,
                DATE_FORMAT(b.check_out, '%d/%m') AS checkout,
                r.room_id,
                bs.status_name,
                GROUP_CONCAT(DISTINCT sc.service_type ORDER BY sc.service_type SEPARATOR ', ') AS services
            FROM bookings b
            JOIN pets p ON p.pet_id = b.pet_id
            JOIN customers c ON c.customer_id = b.customer_id
            JOIN rooms r ON r.room_id = b.room_id
            JOIN booking_statuses bs ON bs.status_id = b.booking_status_id
            LEFT JOIN services s ON s.booking_id = b.booking_id
            LEFT JOIN service_catalog sc ON sc.service_type_id = s.service_type_id
            {where_clause}
            GROUP BY
                b.booking_id, p.pet_name, c.full_name, b.check_in,
                b.check_out, r.room_id, bs.status_name
            ORDER BY b.check_in DESC, b.booking_id DESC
            LIMIT %s
            """,
            tuple(params),
        )

        data = []
        for idx, row in enumerate(rows or [], start=1):
            service_names = [
                self._title(item.strip())
                for item in (row.get("services") or "").split(",")
                if item.strip()
            ]
            if len(service_names) > 2:
                service_names = service_names[:2] + [f"+{len(service_names) - 2} more"]

            data.append({
                "num": f"{idx:03d}",
                "pet": row.get("pet_name") or "-",
                "owner": self._format_owner(row.get("owner_name")),
                "checkin": row.get("checkin") or "-",
                "checkout": row.get("checkout") or "-",
                "room": self._format_room(row.get("room_id")),
                "services": service_names or ["No service"],
                "status": self.STATUS_LABELS.get(row.get("status_name"), self._title(row.get("status_name"))),
            })
        return data


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
        self.content_images = []
        self.backend = BookingHistoryBackend()
        self.current_filter = None
        self.table_data = self.load_bookings()

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

    def load_bookings(self):
        try:
            return self.backend.get_bookings(self.current_filter)
        except Exception as exc:
            print(f"Khong the tai du lieu Booking History: {exc}")
            return []

    def _refresh_scrollregion(self):
        self.canvas.update_idletasks()
        bbox = self.canvas.bbox("all")
        if bbox:
            self.canvas.configure(scrollregion=(bbox[0], 0, bbox[2], bbox[3] + int(50 * self._s)))

    def _redraw_content(self):
        self.content_images = []
        self.canvas.delete("all")
        self.draw_content()
        self.canvas.scale("all", 0, 0, self._s, self._s)
        self._refresh_scrollregion()

    def set_filter(self, filter_label):
        self.current_filter = None if self.current_filter == filter_label else filter_label
        self.table_data = self.load_bookings()
        self._redraw_content()

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
        tw = min(max(len(text) * 9 + 24, 70), 105)
        th = 24
        x1, y1 = cx - tw // 2, cy - th // 2
        x2, y2 = cx + tw // 2, cy + th // 2
        _round_rect(cv, x1, y1, x2, y2, radius=th // 2, fill=bg, outline="")
        cv.create_text(cx, cy, text=text, font=self.F_CHIP, fill=fg, width=tw - 10)

    def _service_colors(self, service, index):
        name = service.lower()
        if "daycare" in name or "swim" in name or "more" in name:
            return self.C_PINK_CHIP_BG, self.C_PINK_CHIP_TEXT
        if "no service" in name:
            return "#EFEFEF", self.C_TEXT_LIGHT
        if index % 2:
            return self.C_PINK_CHIP_BG, self.C_PINK_CHIP_TEXT
        return self.C_GREEN_CHIP_BG, self.C_GREEN_CHIP_TEXT

    def _draw_filter_btn(self, cv, x1, y1, x2, y2, text):
        r = (y2 - y1) // 2
        active = self.current_filter == text
        tag = f"filter_{text.lower().replace(' ', '_').replace('-', '')}"
        fill = self.C_ACTIVE if active else self.C_WHITE
        fg = self.C_WHITE if active else self.C_TEXT
        # White fill
        _round_rect(cv, x1, y1, x2, y2, radius=r, fill=fill, outline="", tags=tag)
        # Border using line segments + arcs
        d = r * 2
        border = self.C_ACTIVE if active else self.C_FILTER_BORDER
        cv.create_arc(x1, y1, x1 + d, y1 + d, start=90, extent=90,
                      style='arc', outline=border, width=1, tags=tag)
        cv.create_arc(x2 - d, y1, x2, y1 + d, start=0, extent=90,
                      style='arc', outline=border, width=1, tags=tag)
        cv.create_arc(x2 - d, y2 - d, x2, y2, start=270, extent=90,
                      style='arc', outline=border, width=1, tags=tag)
        cv.create_arc(x1, y2 - d, x1 + d, y2, start=180, extent=90,
                      style='arc', outline=border, width=1, tags=tag)
        cv.create_line(x1 + r, y1, x2 - r, y1, fill=border, tags=tag)
        cv.create_line(x1 + r, y2, x2 - r, y2, fill=border, tags=tag)
        cv.create_text((x1 + x2) // 2, (y1 + y2) // 2,
                       text=text, font=self.F_FILTER, fill=fg, tags=tag)
        cv.tag_bind(tag, "<Button-1>", lambda _e, value=text: self.set_filter(value))

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
        self.content_images.append(cat_tk)
        cv.create_image(550 + dx, 85 + y, image=cat_tk, anchor="nw")

        # ── TABLE CARD ──
        table_data = self.table_data
        row_h = 80
        tbl_y1 = 315 + y
        tbl_y2 = max(870 + y, tbl_y1 + 70 + max(len(table_data), 1) * row_h)
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
        if not table_data:
            cv.create_text(725 + dx, hdr_y + 75,
                           text="No booking history found",
                           font=self.F_TABLE_BODY, fill=self.C_TEXT_LIGHT)
            return

        for ri, row in enumerate(table_data):
            ry = hdr_y + 30 + ri * row_h
            cy = ry + row_h // 2

            cv.create_text(col_xs[0], cy, text=row["num"],
                           font=self.F_TABLE_BODY, fill=self.C_TEXT, anchor="w")
            cv.create_text(col_xs[1], cy, text=row["pet"],
                           font=self.F_TABLE_BODY, fill=self.C_TEXT, anchor="w", width=62)
            # Owner has newline — centre vertically between the two text lines
            cv.create_text(col_xs[2], cy, text=row["owner"],
                           font=self.F_TABLE_BODY, fill=self.C_TEXT, anchor="w", width=86)
            cv.create_text(col_xs[3], cy, text=row["checkin"],
                           font=self.F_TABLE_BODY, fill=self.C_TEXT, anchor="w")
            cv.create_text(col_xs[4], cy, text=row["checkout"],
                           font=self.F_TABLE_BODY, fill=self.C_TEXT, anchor="w")
            cv.create_text(col_xs[5], cy, text=row["room"],
                           font=self.F_TABLE_BODY, fill=self.C_TEXT, anchor="w")

            # Service chips stacked
            chip_cx = col_xs[6] + 52
            chip_y0 = cy - 24 if len(row["services"]) >= 3 else cy - 18
            for ci, svc in enumerate(row["services"][:3]):
                bg, fg = self._service_colors(svc, ci)
                self._draw_chip(cv, chip_cx, chip_y0 + ci * 30, svc, bg, fg)

            cv.create_text(col_xs[7], cy, text=row["status"],
                           font=self.F_TABLE_BODY, fill=self.C_TEXT, anchor="w", width=110)

            # Row divider (not after last row)
            if ri < len(table_data) - 1:
                cv.create_line(325 + dx, ry + row_h - 1, 1130 + dx, ry + row_h - 1,
                               fill=self.C_DIVIDER, width=1)


if __name__ == "__main__":
    app = BookingHistory()
    app.mainloop()
