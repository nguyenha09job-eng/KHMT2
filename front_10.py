import tkinter as tk
from PIL import Image, ImageTk, ImageDraw
import os
import sys
from datetime import date
from decimal import Decimal

from database import DatabaseConnection


class BillingBackend:
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
    def _short_date(value):
        if not value:
            return "-"
        return value.strftime("%d/%m")

    @staticmethod
    def _full_date(value):
        if not value:
            return "-"
        return value.strftime("%d/%m/%Y")

    @staticmethod
    def _title(value, default="-"):
        if value in (None, ""):
            return default
        return str(value).replace("_", " ").title()

    def _services_for_booking(self, booking_id):
        rows = self.db.fetch_all(
            """
            SELECT
                sc.service_type,
                s.quantity,
                s.total_price
            FROM services s
            JOIN service_catalog sc ON sc.service_type_id = s.service_type_id
            WHERE s.booking_id = %s
            ORDER BY sc.service_type
            """,
            (booking_id,),
        )
        return rows or []

    def _booking_query(self, where_clause, order_clause, params=None):
        rows = self.db.fetch_all(
            f"""
            SELECT
                b.booking_id,
                c.full_name,
                c.phone,
                c.district,
                p.pet_name,
                p.species,
                r.room_id,
                rt.type_name,
                b.check_in,
                b.check_out,
                b.room_price,
                bs.status_name,
                bl.payment_id,
                bl.total_amount,
                bl.discount_amount,
                bl.payment_date,
                bl.payment_method_id,
                pm.method_name
            FROM bookings b
            JOIN customers c ON c.customer_id = b.customer_id
            JOIN pets p ON p.pet_id = b.pet_id
            JOIN rooms r ON r.room_id = b.room_id
            JOIN room_types rt ON rt.room_type_id = r.room_type_id
            JOIN booking_statuses bs ON bs.status_id = b.booking_status_id
            LEFT JOIN billing bl ON bl.booking_id = b.booking_id
            LEFT JOIN payment_methods pm ON pm.method_id = bl.payment_method_id
            {where_clause}
            {order_clause}
            LIMIT 1
            """,
            params or (),
        )
        return rows[0] if rows else None

    def _format_booking(self, row, source_label):
        services = self._services_for_booking(row["booking_id"])
        check_in = row.get("check_in")
        check_out = row.get("check_out")
        nights = 1
        if check_in and check_out:
            nights = max(1, (check_out.date() - check_in.date()).days)

        room_total = int(row.get("room_price") or 0) * nights
        service_total = sum(int(s.get("total_price") or 0) for s in services)
        discount = int(row.get("discount_amount") or 0)
        computed_total = max(room_total + service_total - discount, 0)
        total = int(row.get("total_amount") or computed_total)
        method = self._title(row.get("method_name"), "Card")
        paid = row.get("payment_id") is not None and row.get("payment_method_id") is not None

        service_labels = []
        for item in services[:4]:
            service_labels.append({
                "label": f"{self._title(item.get('service_type'))} x{item.get('quantity') or 1}",
                "amount": int(item.get("total_price") or 0),
            })

        return {
            "booking_id": row["booking_id"],
            "customer": row.get("full_name") or "-",
            "phone": row.get("phone") or "-",
            "district": row.get("district") or "-",
            "pet": row.get("pet_name") or "-",
            "species": self._title(row.get("species"), "Pet"),
            "room": f"Room {row.get('room_id')} - {row.get('type_name') or '-'}",
            "type_name": row.get("type_name") or "-",
            "check_in": self._short_date(check_in),
            "check_out": self._short_date(check_out),
            "checkout_date": self._full_date(check_out),
            "payment_date": self._full_date(row.get("payment_date") or check_out),
            "nights": nights,
            "room_total": room_total,
            "services": service_labels,
            "service_total": service_total,
            "discount": discount,
            "total": total,
            "points": int(total // 1000),
            "method": method,
            "method_key": str(row.get("method_name") or "card").lower(),
            "status": "Paid" if paid else "Unpaid",
            "source_label": source_label,
        }

    def get_focus_booking(self):
        candidates = [
            (
                "WHERE DATE(b.check_out) = CURDATE() "
                "AND bs.status_name IN ('booked', 'checked_in') "
                "AND (bl.payment_id IS NULL OR bl.payment_method_id IS NULL)",
                "ORDER BY b.check_out, b.booking_id",
                (),
                "Due today",
            ),
            (
                "WHERE bs.status_name IN ('booked', 'checked_in') "
                "AND (bl.payment_id IS NULL OR bl.payment_method_id IS NULL)",
                "ORDER BY b.check_out, b.booking_id",
                (),
                "Next unpaid",
            ),
        ]
        for where_clause, order_clause, params, label in candidates:
            row = self._booking_query(where_clause, order_clause, params)
            if row:
                return self._format_booking(row, label)
        return None

    def get_history(self, limit=4):
        rows = self.db.fetch_all(
            """
            SELECT
                b.booking_id,
                c.full_name,
                p.pet_name,
                b.check_out,
                b.room_price
            FROM bookings b
            JOIN customers c ON c.customer_id = b.customer_id
            JOIN pets p ON p.pet_id = b.pet_id
            JOIN booking_statuses bs ON bs.status_id = b.booking_status_id
            LEFT JOIN billing bl ON bl.booking_id = b.booking_id
            WHERE (bl.payment_id IS NULL OR bl.payment_method_id IS NULL)
              AND bs.status_name IN ('booked', 'checked_in')
            ORDER BY b.check_out, b.booking_id
            LIMIT %s
            """,
            (limit,),
        )
        history = []
        for row in rows or []:
            history.append({
                "booking_id": row.get("booking_id"),
                "customer_pet": f"{row.get('full_name') or '-'} - {row.get('pet_name') or '-'}",
                "date": self._full_date(row.get("check_out")),
                "amount": self._money(row.get("room_price")),
                "method": "-",
                "status": "Unpaid",
            })
        return history

    def get_data(self):
        return {
            "today": date.today().strftime("%A, %d/%m/%Y"),
            "focus": self.get_focus_booking(),
            "history": self.get_history(),
        }

def _round_rect(cv, x1, y1, x2, y2, radius=25, **kwargs):
    """Vẽ hình chữ nhật bo góc bằng pieslice để mượt mà."""
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

def _round_rect_outline(cv, x1, y1, x2, y2, radius=25, color="#000", width=1):
    """Vẽ viền hình chữ nhật bo góc mảnh không có ruột màu."""
    d = 2 * radius
    cv.create_arc(x1, y1, x1+d, y1+d, start=90, extent=90, style=tk.ARC, outline=color, width=width)
    cv.create_arc(x2-d, y1, x2, y1+d, start=0, extent=90, style=tk.ARC, outline=color, width=width)
    cv.create_arc(x2-d, y2-d, x2, y2, start=270, extent=90, style=tk.ARC, outline=color, width=width)
    cv.create_arc(x1, y2-d, x1+d, y2, start=180, extent=90, style=tk.ARC, outline=color, width=width)
    cv.create_line(x1+radius, y1, x2-radius, y1, fill=color, width=width)
    cv.create_line(x2, y1+radius, x2, y2-radius, fill=color, width=width)
    cv.create_line(x1+radius, y2, x2-radius, y2, fill=color, width=width)
    cv.create_line(x1, y1+radius, x1, y2-radius, fill=color, width=width)


class BillingDashboard(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("Pet&Bed - Billing")
        self.attributes("-fullscreen", True)
        self.configure(bg="#DDE89D")
        self.update_idletasks()

        self.W = self.winfo_width()
        self.H = self.winfo_height()

        self.BASE_W = 1200.0
        self.BASE_H = 880.0
        self._s = self.W / self.BASE_W
        s = self._s
        self.Y_OFF = 20

        # --- Bảng màu chuẩn giống front_2.py ---
        self.C_BG = "#DDE89D"
        self.C_SIDEBAR = "#FFFFFF"
        self.C_TEXT = "#4A3525"
        self.C_TEXT_LIGHT = "#7A685F"
        self.C_WHITE = "#FFFFFF"
        self.C_ACTIVE = "#C8DB6D"
        self.C_UNPAID_BG = "#FADAB5"
        self.C_PAID_BG = "#E5EFC3"
        self.C_BTN_GREEN = "#8BB553"
        self.C_TAG_GREEN = "#DDEAA9"
        self.C_TAG_PINK = "#F6C6D3"
        self.C_LINE = "#E5DFDA"

        # --- Fonts chuẩn cao cấp từ front_2.py ---
        self.F_LOGO = ("Arial Rounded MT Bold", max(16, int(40 * s)), "bold")
        self.F_NAV = ("Baghdad", max(10, int(18 * s)))
        self.F_TITLE_LARGE = ("Arial Rounded MT Bold", max(20, int(34 * s)), "bold")
        self.F_TITLE_MED = ("Arial Rounded MT Bold", max(14, int(22 * s)), "bold")
        self.F_DATE = ("Baghdad", max(10, int(18 * s)))
        self.F_REGULAR = ("Baghdad", max(10, int(16 * s)))
        self.F_BOLD = ("Baghdad", max(10, int(16 * s)), "bold")
        self.F_PRICE = ("Arial Rounded MT Bold", max(11, int(17 * s)), "bold")

        self.images = []
        self.backend = BillingBackend()
        try:
            self.data = self.backend.get_data()
        except Exception as exc:
            self.data = {"today": date.today().strftime("%A, %d/%m/%Y"), "focus": None, "history": []}
            self.data_error = str(exc)
        else:
            self.data_error = None

        # -- Layout --
        main = tk.Frame(self, bg=self.C_BG)
        main.pack(fill=tk.BOTH, expand=True)

        self.BASE_SIDE_W = 260
        side_w = int(self.BASE_SIDE_W * s)

        # Sidebar Left
        self.side_frame = tk.Frame(main, width=side_w, bg=self.C_BG)
        self.side_frame.pack(side=tk.LEFT, fill=tk.Y)
        self.side_frame.pack_propagate(False)

        self.sidebar_canvas = tk.Canvas(self.side_frame, width=side_w, height=self.H,
                                        bg=self.C_BG, highlightthickness=0)
        self.sidebar_canvas.pack(fill=tk.BOTH, expand=True)

        # Content Right (With Scrollbar)
        self.content_container = tk.Frame(main, bg=self.C_BG)
        self.content_container.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        scrollbar = tk.Scrollbar(self.content_container, orient=tk.VERTICAL)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.canvas = tk.Canvas(self.content_container, bg=self.C_BG, highlightthickness=0)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.configure(command=self.canvas.yview)

        # Draw
        self.draw_sidebar()
        self.draw_billing_page()

        # Scale Canvas
        self.sidebar_canvas.scale("all", 0, 0, s, s)
        self.canvas.scale("all", 0, 0, s, s)

        # Scroll bindings
        self.canvas.update_idletasks()
        bbox = self.canvas.bbox("all")
        if bbox:
            self.canvas.configure(scrollregion=(bbox[0], 0, bbox[2], bbox[3] + 60 * s))
        else:
            self.canvas.configure(scrollregion=self.canvas.bbox("all"))

        def _on_mw(event):
            delta = event.delta
            if sys.platform == "darwin":
                self.canvas.yview_scroll(int(-delta), "units")
            else:
                self.canvas.yview_scroll(int(-delta / 120), "units")

        self.canvas.bind("<MouseWheel>", _on_mw, add="+")
        self.canvas.bind("<Button-4>", lambda e: self.canvas.yview_scroll(-1, "units"), add="+")
        self.canvas.bind("<Button-5>", lambda e: self.canvas.yview_scroll(1, "units"), add="+")
        self.bind("<Escape>", lambda e: self.destroy())

    # =====================================================
    # SIDEBAR (Identical to front_2.py - Billing Active)
    # =====================================================
    def draw_sidebar(self):
        cv = self.sidebar_canvas
        _round_rect(cv, -80, 0, 250, 820, radius=30, fill=self.C_SIDEBAR, outline="")

        cv.create_text(125, 70, text="Pet&Bed", font=self.F_LOGO, fill=self.C_TEXT)

        nav_items = ["Dashboard", "Care View", "Booking", "Rooms",
                     "Customer & Pet", "Billing", "Staff", "Report"]
        y = 110
        item_h = 37
        item_r = item_h // 2
        pad_x = 36
        right_x = 215
        gap = 10

        for i, item in enumerate(nav_items):
            if i == 5:  # Billing active
                _round_rect(cv, pad_x, y, right_x, y + item_h,
                            radius=item_r, fill=self.C_ACTIVE, outline="")
            else:
                _round_rect(cv, pad_x, y, right_x, y + item_h,
                            radius=item_r, fill="#efefef", outline="")
            cv.create_text(pad_x + 20, y + 20, text=item,
                           font=self.F_NAV, fill=self.C_TEXT, anchor="w")
            y += item_h + gap

        # Duck image (Identical to front_2.py crop & round logic)
        _dir = os.path.dirname(__file__)
        duck_path = os.path.join(_dir, "image", "duck.png")
        rabbit_w, rabbit_h = 130, 130
        s = self._s
        sw = int(rabbit_w * s)
        sh = int(rabbit_h * s)
        sr = int(20 * s)
        if os.path.exists(duck_path):
            img = Image.open(duck_path).convert("RGBA")
        else:
            img = Image.new("RGBA", (sw, sh), color="#CCCCCC")
        img_ratio = img.width / img.height
        target_ratio = sw / sh
        if img_ratio > target_ratio:
            new_width = int(sh * img_ratio)
            img = img.resize((new_width, sh), Image.Resampling.LANCZOS)
            left = (new_width - sw) // 2
            img = img.crop((left, 0, left + sw, sh))
        else:
            new_height = int(sw / img_ratio)
            img = img.resize((sw, new_height), Image.Resampling.LANCZOS)
            top = (new_height - sh) // 2
            img = img.crop((0, top, sw, top + sh))
        mask = Image.new("L", (sw, sh), 0)
        draw = ImageDraw.Draw(mask)
        draw.rounded_rectangle((0, 0, sw, sh), radius=sr, fill=255)
        result = Image.new("RGBA", (sw, sh), (0, 0, 0, 0))
        result.paste(img, (0, 0), mask=mask)
        duck_tk = ImageTk.PhotoImage(result)
        self.images.append(duck_tk)
        duck_x = 125 - rabbit_w / 2
        cv.create_image(duck_x, 550, image=duck_tk, anchor="nw")

        # Logout
        base_bottom = self.H / self._s
        btn_h = 42
        btn_pad_bottom = 25
        btn_y2 = base_bottom - btn_pad_bottom
        btn_y1 = btn_y2 - btn_h
        btn_x1 = 30
        btn_x2 = 220
        btn_cx = (btn_x1 + btn_x2) / 2
        btn_cy = (btn_y1 + btn_y2) / 2

        _round_rect(cv, btn_x1, btn_y1, btn_x2, btn_y2,
                    radius=btn_h // 2, fill=self.C_TEXT, outline="",
                    tags="logout_btn")
        cv.create_text(btn_cx, btn_cy, text="Log out",
                       font=self.F_NAV, fill="#FFFFFF",
                       tags="logout_btn")
        cv.tag_bind("logout_btn", "<Button-1>", lambda e: self.destroy())

    # =====================================================
    # ROUNDED IMAGE HELPER
    # =====================================================
    def create_rounded_image(self, image_path, width, height, radius, crop_y=0.5):
        s = self._s
        sw = int(width * s)
        sh = int(height * s)
        sr = int(radius * s)
        if not os.path.exists(image_path):
            img = Image.new("RGB", (sw, sh), color="#CCCCCC")
        else:
            img = Image.open(image_path).convert("RGB")
        img_ratio = img.width / img.height
        target_ratio = sw / sh
        if img_ratio > target_ratio:
            new_width = int(sh * img_ratio)
            img = img.resize((new_width, sh), Image.Resampling.LANCZOS)
            max_left = new_width - sw
            left = int(max_left * crop_y) if max_left > 0 else 0
            img = img.crop((left, 0, left + sw, sh))
        else:
            new_height = int(sw / img_ratio)
            img = img.resize((sw, new_height), Image.Resampling.LANCZOS)
            max_top = new_height - sh
            top = int(max_top * crop_y) if max_top > 0 else 0
            img = img.crop((0, top, sw, top + sh))
        mask = Image.new("L", (sw, sh), 0)
        draw = ImageDraw.Draw(mask)
        draw.rounded_rectangle((0, 0, sw, sh), radius=sr, fill=255)
        result = Image.new("RGBA", (sw, sh), (0, 0, 0, 0))
        result.paste(img, (0, 0), mask=mask)
        return ImageTk.PhotoImage(result)

    def _money(self, value):
        return BillingBackend._money(value)

    def _chip_width(self, text, min_width=75):
        return max(min_width, len(str(text)) * 8 + 26)

    def _draw_status_chip(self, cv, x2, cy, status):
        fill = self.C_PAID_BG if status == "Paid" else self.C_UNPAID_BG
        width = 90
        _round_rect(cv, x2 - width, cy - 12, x2, cy + 13, radius=12, fill=fill)
        cv.create_text(x2 - width / 2, cy, text=status, font=self.F_BOLD, fill=self.C_TEXT)

    def _draw_payment_option(self, cv, x1, y1, x2, label, active=False):
        if active:
            _round_rect(cv, x1, y1, x2, y1 + 34, radius=15, fill=self.C_ACTIVE)
        else:
            _round_rect_outline(cv, x1, y1, x2, y1 + 34, radius=15, color="#A89F95", width=1)
        cv.create_text((x1 + x2) / 2, y1 + 17, text=label, font=self.F_REGULAR, fill=self.C_TEXT)

    # =====================================================
    # MAIN BILLING PAGE RENDER
    # =====================================================
    def draw_billing_page(self):
        cv = self.canvas
        dx = -self.BASE_SIDE_W
        y_off = self.Y_OFF

        L_PAD = 300 + dx
        R_PAD = 1150 + dx
        card_w = R_PAD - L_PAD

        # -------------------------------------------------
        # 1. TOP HEADER PILL (Billing)
        # -------------------------------------------------
        hdr_y1 = 30 + y_off
        hdr_y2 = 70 + y_off
        _round_rect(cv, L_PAD, hdr_y1, R_PAD, hdr_y2, radius=20, fill=self.C_WHITE, outline="")
        cv.create_text(L_PAD + 25, (hdr_y1 + hdr_y2)/2, text="Billing", font=self.F_BOLD, fill=self.C_TEXT, anchor="w")

        # -------------------------------------------------
        # 2. MAIN TITLE & DOG BANNER ROW
        # -------------------------------------------------
        focus = self.data.get("focus")
        history = self.data.get("history", [])
        title_y = 95 + y_off
        cv.create_text(L_PAD, title_y + 15, text="DUE TODAY\n(Check-outs)", font=self.F_TITLE_LARGE, fill=self.C_TEXT, anchor="nw")
        cv.create_text(L_PAD, title_y + 90, text=self.data.get("today", ""), font=self.F_DATE, fill=self.C_TEXT, anchor="nw")

        # Dog Banner
        _dir = os.path.dirname(__file__)
        banner_path = os.path.join(_dir, "image", "billing.jpg")
        banner_w = 440
        banner_h = 130
        banner_tk = self.create_rounded_image(banner_path, banner_w, banner_h, radius=24, crop_y=0.3)
        self.images.append(banner_tk)
        cv.create_image(R_PAD - banner_w, title_y, image=banner_tk, anchor="nw")

        # -------------------------------------------------
        # 3. SEARCH BAR BELOW BANNER
        # -------------------------------------------------
        search_y = 240 + y_off
        _round_rect(cv, L_PAD, search_y, R_PAD, search_y + 45, radius=22, fill=self.C_WHITE, outline="")
        cv.create_text(L_PAD + 20, search_y + 22, text="Search by name, phone number, or pet name", font=self.F_REGULAR, fill="#A5A5A5", anchor="w")
        
        # Simple search loop icon
        cv.create_oval(R_PAD - 40, search_y + 14, R_PAD - 26, search_y + 28, outline=self.C_TEXT, width=2)
        cv.create_line(R_PAD - 29, search_y + 27, R_PAD - 21, search_y + 35, fill=self.C_TEXT, width=2)

        # -------------------------------------------------
        # 4. BOOKING CARD
        # -------------------------------------------------
        card_y1 = 305 + y_off
        card_y2 = 705 + y_off
        _round_rect(cv, L_PAD, card_y1, R_PAD, card_y2, radius=25, fill=self.C_WHITE, outline="")

        if not focus:
            msg = "No billing data found"
            if self.data_error:
                msg = f"Database error: {self.data_error}"
            cv.create_text((L_PAD + R_PAD) / 2, card_y1 + 180, text=msg,
                           font=self.F_TITLE_MED, fill=self.C_TEXT_LIGHT)
        else:
            # Title
            cv.create_text(L_PAD + 25, card_y1 + 28, text=f"Booking #{focus['booking_id']}",
                           font=self.F_TITLE_MED, fill=self.C_TEXT, anchor="w")

            pet_text = f"{focus['species']} {focus['pet']}"
            pet_w = self._chip_width(pet_text, 95)
            _round_rect(cv, L_PAD + 190, card_y1 + 16, L_PAD + 190 + pet_w, card_y1 + 41,
                        radius=12, fill=self.C_UNPAID_BG)
            cv.create_text(L_PAD + 190 + pet_w / 2, card_y1 + 28, text=pet_text,
                           font=self.F_BOLD, fill=self.C_TEXT)

            self._draw_status_chip(cv, R_PAD - 25, card_y1 + 28, focus["status"])
            cv.create_text(R_PAD - 125, card_y1 + 28, text=focus["source_label"],
                           font=self.F_REGULAR, fill=self.C_TEXT_LIGHT, anchor="e")

            subtitle = (
                f"{focus['customer']} - {focus['room']} - "
                f"{focus['check_in']} -> {focus['check_out']}"
            )
            cv.create_text(L_PAD + 25, card_y1 + 58, text=subtitle,
                           font=self.F_REGULAR, fill=self.C_TEXT_LIGHT, anchor="w")
            cv.create_line(L_PAD + 25, card_y1 + 78, R_PAD - 25, card_y1 + 78, fill=self.C_LINE)

            y_item = card_y1 + 105
            room_label = f"Room ({focus['type_name']} x {focus['nights']} nights)"
            cv.create_text(L_PAD + 25, y_item, text=room_label,
                           font=self.F_REGULAR, fill=self.C_TEXT, anchor="w")
            cv.create_text(R_PAD - 25, y_item, text=self._money(focus["room_total"]),
                           font=self.F_PRICE, fill=self.C_TEXT, anchor="e")

            y_item += 35
            if focus["services"]:
                chip_x = L_PAD + 25
                colors = [self.C_TAG_GREEN, self.C_TAG_PINK, self.C_PAID_BG, self.C_UNPAID_BG]
                for idx, service in enumerate(focus["services"]):
                    chip_w = self._chip_width(service["label"], 100)
                    _round_rect(cv, chip_x, y_item - 12, chip_x + chip_w, y_item + 12,
                                radius=12, fill=colors[idx % len(colors)])
                    cv.create_text(chip_x + chip_w / 2, y_item, text=service["label"],
                                   font=self.F_BOLD, fill=self.C_TEXT)
                    chip_x += chip_w + 10
                cv.create_text(R_PAD - 25, y_item, text=self._money(focus["service_total"]),
                               font=self.F_PRICE, fill=self.C_TEXT, anchor="e")
                y_item += 35
            else:
                cv.create_text(L_PAD + 25, y_item, text="No extra services",
                               font=self.F_REGULAR, fill=self.C_TEXT_LIGHT, anchor="w")
                cv.create_text(R_PAD - 25, y_item, text=self._money(0),
                               font=self.F_PRICE, fill=self.C_TEXT, anchor="e")
                y_item += 35

            cv.create_text(L_PAD + 25, y_item, text=f"Customer phone ({focus['phone']})",
                           font=self.F_REGULAR, fill=self.C_TEXT, anchor="w")
            cv.create_text(R_PAD - 25, y_item, text=focus["district"],
                           font=self.F_REGULAR, fill=self.C_TEXT_LIGHT, anchor="e")

            y_item += 35
            cv.create_text(L_PAD + 25, y_item, text="Discount",
                           font=self.F_REGULAR, fill=self.C_TEXT, anchor="w")
            cv.create_text(R_PAD - 25, y_item, text=f"-{self._money(focus['discount'])}",
                           font=self.F_PRICE, fill=self.C_TEXT, anchor="e")

            y_line = y_item + 25
            cv.create_line(L_PAD + 25, y_line, R_PAD - 25, y_line, fill=self.C_LINE)

            y_total = y_line + 30
            cv.create_text(L_PAD + 25, y_total, text="Total amount",
                           font=self.F_TITLE_MED, fill=self.C_TEXT, anchor="w")
            cv.create_text(R_PAD - 25, y_total, text=self._money(focus["total"]),
                           font=("Arial Rounded MT Bold", max(15, int(21*self._s)), "bold"),
                           fill=self.C_TEXT, anchor="e")

            cv.create_text(R_PAD - 25, y_total + 25,
                           text=f"Add {focus['points']:,} pts to account",
                           font=self.F_REGULAR, fill=self.C_TEXT_LIGHT, anchor="e")

            y_btn = y_total + 30
            method_key = focus.get("method_key", "card")
            self._draw_payment_option(cv, L_PAD + 25, y_btn, L_PAD + 115, "Cash", method_key == "cash")
            self._draw_payment_option(cv, L_PAD + 130, y_btn, L_PAD + 280, "Bank Transfer", method_key == "transfer")
            self._draw_payment_option(cv, L_PAD + 295, y_btn, L_PAD + 385, "Card", method_key == "card")

            cv.create_text(L_PAD + 25, y_btn + 58, text=focus["payment_date"],
                           font=self.F_REGULAR, fill=self.C_TEXT_LIGHT, anchor="w")

            _round_rect(cv, R_PAD - 125, y_btn + 22, R_PAD - 25, y_btn + 62,
                        radius=20, fill=self.C_BTN_GREEN)
            cv.create_text(R_PAD - 75, y_btn + 42, text="Done", font=self.F_BOLD, fill=self.C_WHITE)

        # -------------------------------------------------
        # 5. BOOKING HISTORY
        # -------------------------------------------------
        hist_y = card_y2 + 40
        cv.create_text(L_PAD, hist_y, text="Unpaid Bookings", font=self.F_TITLE_MED, fill=self.C_TEXT, anchor="w")

        tbl_y1 = hist_y + 20
        row_count = max(len(history), 1)
        tbl_y2 = tbl_y1 + 70 + row_count * 45
        _round_rect(cv, L_PAD, tbl_y1, R_PAD, tbl_y2, radius=25, fill=self.C_WHITE, outline="")

        # Table Header
        h_y = tbl_y1 + 25
        cols_x = [L_PAD + 30, L_PAD + 80, L_PAD + 280, L_PAD + 420, L_PAD + 560, L_PAD + 700]
        headers = ["#", "Customer / Pet", "Date", "Amount", "Method", "Status"]
        for x_pos, text in zip(cols_x, headers):
            cv.create_text(x_pos, h_y, text=text, font=self.F_BOLD, fill=self.C_TEXT, anchor="w")
        
        cv.create_line(L_PAD + 20, h_y + 15, R_PAD - 20, h_y + 15, fill=self.C_LINE)

        row_y = h_y + 40
        if not history:
            cv.create_text((L_PAD + R_PAD) / 2, row_y, text="No unpaid bookings found",
                           font=self.F_REGULAR, fill=self.C_TEXT_LIGHT)
        for i, item in enumerate(history):
            cv.create_text(cols_x[0], row_y, text=str(item["booking_id"]), font=self.F_REGULAR, fill=self.C_TEXT, anchor="w")
            cv.create_text(cols_x[1], row_y, text=item["customer_pet"], font=self.F_REGULAR, fill=self.C_TEXT, anchor="w")
            cv.create_text(cols_x[2], row_y, text=item["date"], font=self.F_REGULAR, fill=self.C_TEXT, anchor="w")
            cv.create_text(cols_x[3], row_y, text=item["amount"], font=self.F_BOLD, fill=self.C_TEXT, anchor="w")
            cv.create_text(cols_x[4], row_y, text=item["method"], font=self.F_REGULAR, fill=self.C_TEXT, anchor="w")

            fill = self.C_PAID_BG if item["status"] == "Paid" else self.C_UNPAID_BG
            _round_rect(cv, cols_x[5]-10, row_y - 12, cols_x[5] + 80, row_y + 12, radius=12, fill=fill)
            cv.create_text(cols_x[5] + 35, row_y, text=item["status"], font=self.F_BOLD, fill=self.C_TEXT)

            if i < len(history) - 1:
                cv.create_line(L_PAD + 20, row_y + 20, R_PAD - 20, row_y + 20, fill=self.C_LINE)
            row_y += 45

if __name__ == "__main__":
    app = BillingDashboard()
    app.mainloop()
