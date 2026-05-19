import tkinter as tk
from PIL import Image, ImageTk, ImageDraw
import os
import sys
from datetime import date, datetime, timedelta
from decimal import Decimal

from database import DatabaseConnection


def format_large_number(num):
    """Format large numbers for the dashboard cards."""
    if num is None:
        num = 0

    if isinstance(num, Decimal):
        num = float(num)

    if num >= 1_000_000_000:
        s = f"{num / 1_000_000_000:.1f}".rstrip("0").rstrip(".")
        return f"{s}B"
    if num >= 1_000_000:
        s = f"{num / 1_000_000:.1f}".rstrip("0").rstrip(".")
        return f"{s}M"
    if num >= 1_000:
        s = f"{num / 1_000:.1f}".rstrip("0").rstrip(".")
        return f"{s}K"
    return f"{num:,.0f}"


class DashboardBackend:
    """Data layer for the dashboard screen using the PetHotel schema."""

    def __init__(self, db=None):
        self.db = db or DatabaseConnection()

    def get_currently_staying(self):
        total = self.db.fetch_one(
            """
            SELECT COUNT(*) AS cnt
            FROM bookings b
            JOIN booking_statuses bs ON bs.status_id = b.booking_status_id
            JOIN pets p ON p.pet_id = b.pet_id
            WHERE bs.status_name = 'checked_in'
              AND DATE(b.check_in) <= CURDATE()
              AND DATE(b.check_out) >= CURDATE()
              AND LOWER(p.species) IN ('dog', 'cat')
            """
        )
        dogs = self.db.fetch_one(
            """
            SELECT COUNT(*) AS cnt
            FROM bookings b
            JOIN booking_statuses bs ON bs.status_id = b.booking_status_id
            JOIN pets p ON p.pet_id = b.pet_id
            WHERE bs.status_name = 'checked_in'
              AND DATE(b.check_in) <= CURDATE()
              AND DATE(b.check_out) >= CURDATE()
              AND LOWER(p.species) = 'dog'
            """
        )
        cats = self.db.fetch_one(
            """
            SELECT COUNT(*) AS cnt
            FROM bookings b
            JOIN booking_statuses bs ON bs.status_id = b.booking_status_id
            JOIN pets p ON p.pet_id = b.pet_id
            WHERE bs.status_name = 'checked_in'
              AND DATE(b.check_in) <= CURDATE()
              AND DATE(b.check_out) >= CURDATE()
              AND LOWER(p.species) = 'cat'
            """
        )

        t = total["cnt"] if total else 0
        d = dogs["cnt"] if dogs else 0
        c = cats["cnt"] if cats else 0

        return {
            "total": t,
            "dogs": d,
            "cats": c,
            "display": format_large_number(t),
            "subtext": f"{d} dogs - {c} cats",
        }

    def get_available_rooms(self):
        total = self.db.fetch_one(
            """
            SELECT COUNT(*) AS cnt
            FROM rooms
            WHERE is_active = 1
            """
        )
        occupied = self.db.fetch_one(
            """
            SELECT COUNT(DISTINCT b.room_id) AS cnt
            FROM bookings b
            JOIN booking_statuses bs ON bs.status_id = b.booking_status_id
            WHERE bs.status_name IN ('booked', 'checked_in')
              AND DATE(b.check_in) <= CURDATE()
              AND DATE(b.check_out) >= CURDATE()
            """
        )

        t = total["cnt"] if total else 0
        o = occupied["cnt"] if occupied else 0
        available = max(t - o, 0)

        return {
            "available": available,
            "total": t,
            "display": format_large_number(available),
            "subtext": f"out of {t} rooms",
        }

    def get_monthly_revenue(self):
        today = date.today()
        first_this_month = today.replace(day=1)

        this_month = self.db.fetch_one(
            """
            SELECT COALESCE(SUM(total_amount), 0) AS total
            FROM billing
            WHERE payment_date >= %s
              AND payment_date < %s
            """,
            (
                first_this_month.strftime("%Y-%m-%d"),
                (today + timedelta(days=1)).strftime("%Y-%m-%d"),
            ),
        )

        # MTD vs same period last month
        if today.month == 1:
            first_prev_month = date(today.year - 1, 12, 1)
            last_day_prev = 31
        else:
            first_prev_month = date(today.year, today.month - 1, 1)
            last_day_prev = (first_this_month - timedelta(days=1)).day
        day_capped = min(today.day, last_day_prev)
        prev_end = first_prev_month.replace(day=day_capped) + timedelta(days=1)

        prev_month = self.db.fetch_one(
            """
            SELECT COALESCE(SUM(total_amount), 0) AS total
            FROM billing
            WHERE payment_date >= %s
              AND payment_date < %s
            """,
            (
                first_prev_month.strftime("%Y-%m-%d"),
                prev_end.strftime("%Y-%m-%d"),
            ),
        )

        cur = float(this_month["total"]) if this_month else 0.0
        prev = float(prev_month["total"]) if prev_month else 0.0

        if prev > 0:
            pct = round((cur - prev) / prev * 100)
            sign = "+" if pct >= 0 else ""
            subtext = f"{sign}{pct}% vs last month"
        else:
            subtext = "0% vs last month"

        return {
            "current": cur,
            "previous": prev,
            "display": format_large_number(cur),
            "subtext": subtext,
        }

    def get_checkouts_today(self):
        total = self.db.fetch_one(
            """
            SELECT COUNT(*) AS cnt
            FROM bookings b
            JOIN booking_statuses bs ON bs.status_id = b.booking_status_id
            WHERE DATE(b.check_out) = CURDATE()
              AND bs.status_name IN ('booked', 'checked_in')
            """
        )
        pending = self.db.fetch_one(
            """
            SELECT COUNT(*) AS cnt
            FROM bookings b
            JOIN booking_statuses bs ON bs.status_id = b.booking_status_id
            LEFT JOIN billing bl ON bl.booking_id = b.booking_id
            WHERE DATE(b.check_out) = CURDATE()
              AND bs.status_name IN ('booked', 'checked_in')
              AND (bl.payment_id IS NULL OR bl.payment_method_id IS NULL)
            """
        )

        t = total["cnt"] if total else 0
        p = pending["cnt"] if pending else 0

        if t == 0:
            subtext = "No check-outs today"
        elif p > 0:
            subtext = "Pending billing"
        else:
            subtext = "All billed"

        return {
            "total": t,
            "pending_billing": p,
            "display": format_large_number(t),
            "subtext": subtext,
        }

    def get_active_bookings(self):
        rows = self.db.fetch_all(
            """
            SELECT
                p.pet_name AS pet,
                c.full_name AS owner,
                DATE_FORMAT(b.check_in, '%d/%m') AS check_in,
                DATE_FORMAT(b.check_out, '%d/%m') AS check_out,
                bs.status_name AS status,
                CONCAT('R-', LPAD(r.room_id, 2, '0')) AS room
            FROM bookings b
            JOIN pets p ON p.pet_id = b.pet_id
            JOIN customers c ON c.customer_id = b.customer_id
            JOIN booking_statuses bs ON bs.status_id = b.booking_status_id
            JOIN rooms r ON r.room_id = b.room_id
            WHERE bs.status_name IN ('checked_in', 'booked')
              AND DATE(b.check_in) <= CURDATE()
              AND DATE(b.check_out) >= CURDATE()
            ORDER BY b.check_in DESC
            LIMIT 50
            """
        )
        return rows or []

    def get_today_services(self):
        rows = self.db.fetch_all(
            """
            SELECT
                p.pet_name AS pet,
                sc.service_type AS service,
                CONCAT('R-', LPAD(r.room_id, 2, '0')) AS room,
                s.status AS status,
                COALESCE(s.frequency_tag, CONCAT(s.quantity, 'x')) AS frequency
            FROM services s
            JOIN bookings b ON b.booking_id = s.booking_id
            JOIN booking_statuses bs ON bs.status_id = b.booking_status_id
            JOIN pets p ON p.pet_id = s.pet_id
            JOIN service_catalog sc ON sc.service_type_id = s.service_type_id
            JOIN rooms r ON r.room_id = b.room_id
            WHERE bs.status_name IN ('checked_in', 'booked')
              AND DATE(b.check_in) <= CURDATE()
              AND DATE(b.check_out) >= CURDATE()
            ORDER BY s.status, p.pet_name
            LIMIT 100
            """
        )
        return rows or []

    def get_all_dashboard_data(self):
        return {
            "currently_staying": self.get_currently_staying(),
            "available_rooms": self.get_available_rooms(),
            "monthly_revenue": self.get_monthly_revenue(),
            "checkouts_today": self.get_checkouts_today(),
            "active_bookings": self.get_active_bookings(),
            "today_services": self.get_today_services(),
        }

def _round_rect(cv, x1, y1, x2, y2, radius=25, **kwargs):
    """Draw a rounded rectangle using arcs for true rounded corners."""
    d = 2 * radius
    kwargs["outline"] = kwargs.get("fill", "")
    items = []
    # Body
    items.append(cv.create_rectangle(x1 + radius, y1, x2 - radius, y2, **kwargs))
    items.append(cv.create_rectangle(x1, y1 + radius, x2, y2 - radius, **kwargs))
    # Four corners
    items.append(cv.create_arc(x1, y1, x1 + d, y1 + d, start=90, extent=90, style='pieslice', **kwargs))
    items.append(cv.create_arc(x2 - d, y1, x2, y1 + d, start=0, extent=90, style='pieslice', **kwargs))
    items.append(cv.create_arc(x2 - d, y2 - d, x2, y2, start=270, extent=90, style='pieslice', **kwargs))
    items.append(cv.create_arc(x1, y2 - d, x1 + d, y2, start=180, extent=90, style='pieslice', **kwargs))
    return tuple(items)

class PetDashboard(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("Pet&Bed Dashboard")
        self.attributes("-fullscreen", True)
        self.configure(bg="#F2D5D5")
        self.update_idletasks()

        self.W = self.winfo_width()
        self.H = self.winfo_height()
        
        # Base dimensions from original design (Mặc định chuẩn)
        self.BASE_W = 1200.0
        self.BASE_H = 850.0
        
        # Calculate scale factor to fill screen (using width)
        self._s = self.W / self.BASE_W
        s = self._s
        self.Y_OFF =20

        # Colors
        self.C_BG = "#F2D5D5"
        self.C_SIDEBAR = "#FFFFFF"
        self.C_TEXT = "#4A3525"
        self.C_TEXT_LIGHT = "#7A685F"
        self.C_WHITE = "#FFFFFF"
        self.C_ACTIVE = "#E6B8B8"

        # Fonts (Đã nhân với hệ số scale s)
        self.F_LOGO = ("Arial Rounded MT Bold", max(16, int(40 * s)), "bold")
        self.F_NAV = ("Baghdad", max(10, int(18 * s)))
        self.F_TITLE = ("Arial Rounded MT Bold", max(10, int(18 * s)), "bold") # Giống Pet&Bed
        self.F_HEADER = ("Baghdad", max(10, int(18 * s)), "bold")
        self.F_DATE = ("Baghdad", max(10, int(18 * s)))
        self.F_STAT_VAL = ("Helvetica", max(24, int(64 * s)), "bold")
        self.F_STAT_LBL = ("Baghdad", max(10, int(18 * s)), "bold")
        self.F_STAT_SUB = ("Baghdad", max(10, int(18 * s)))
        self.F_SECTION = ("Arial Rounded MT Bold", max(10, int(20 * s)), "bold")
        self.F_TABLE_HEAD = ("Arial Rounded MT Bold", max(10, int(15 * s)), "bold")
        self.F_TABLE_ROW = ("Baghdad", max(10, int(15 * s)))

        self.images = []
        self.service_filter = "all"  # "all", "done", "not_done"

        # -- Data from backend --
        self.backend = DashboardBackend()
        self.data = self.backend.get_all_dashboard_data()

        # -- Layout --
        main = tk.Frame(self, bg=self.C_BG)
        main.pack(fill=tk.BOTH, expand=True)

        # Base Sidebar Width is 260px in 1200x850 design
        # The main content starts at 300px. Gap is 40px.
        self.BASE_SIDE_W = 260
        side_w = int(self.BASE_SIDE_W * s)

        # Sidebar Frame (Fixed/Đứng yên)
        self.side_frame = tk.Frame(main, width=side_w, bg=self.C_BG)
        self.side_frame.pack(side=tk.LEFT, fill=tk.Y)
        self.side_frame.pack_propagate(False)

        self.sidebar_canvas = tk.Canvas(self.side_frame, width=side_w, height=self.H,
                                        bg=self.C_BG, highlightthickness=0)
        self.sidebar_canvas.pack(fill=tk.BOTH, expand=True)

        # Content Frame (Scrollable/Cuộn được)
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
        self.draw_main_content()
        self.draw_tables()

        # Scale contents based on base coordinates
        self.sidebar_canvas.scale("all", 0, 0, s, s)
        self.canvas.scale("all", 0, 0, s, s)

        # Add scrollable table rows (after scaling so positions are final)
        self._add_scrollable_rows()

        # Update scrollregion
        self.canvas.update_idletasks()
        
        # Thêm padding ở dưới cùng
        bbox = self.canvas.bbox("all")
        if bbox:
            self.canvas.configure(scrollregion=(bbox[0], 0, bbox[2], bbox[3] + 50 * s))
        else:
            self.canvas.configure(scrollregion=self.canvas.bbox("all"))

        # Scroll bindings
        def _on_mw(event):
            # macOS uses delta as is. Windows uses delta / 120
            delta = event.delta
            if sys.platform == "darwin":
                self.canvas.yview_scroll(int(-delta), "units")
            else:
                self.canvas.yview_scroll(int(-delta / 120), "units")

        self.canvas.bind("<MouseWheel>", _on_mw, add="+")
        # For Linux
        self.canvas.bind("<Button-4>", lambda e: self.canvas.yview_scroll(-1, "units"), add="+")
        self.canvas.bind("<Button-5>", lambda e: self.canvas.yview_scroll(1, "units"), add="+")

        # Handle resize
        def _update_scrollregion(_e=None):
            bbox = self.canvas.bbox("all")
            if bbox:
                self.canvas.configure(scrollregion=(bbox[0], 0, bbox[2], bbox[3] + 50 * s))
        self.canvas.bind("<Configure>", _update_scrollregion)
        
        # Exit shortcut
        self.bind("<Escape>", lambda e: self.destroy())

    def draw_sidebar(self):
        cv = self.sidebar_canvas
        
        # Base coordinates for sidebar - Thêm lề và bo tròn mạnh hơn
        _round_rect(cv, -80 , 0 , 250, 820, radius=30, fill=self.C_SIDEBAR, outline="")

        # Logo
        cv.create_text(125, 70, text="Pet&Bed", font=self.F_LOGO, fill=self.C_TEXT)

        # Nav items
        nav_items = ["Dashboard", "Care View", "Booking", "Rooms",
                     "Customer & Pet", "Billing", "Staff", "Report"]
        y = 110
        item_h = 37
        item_r = item_h // 2  # pill shape (half height)
        pad_x = 36
        right_x = 215
        gap = 10

        for i, item in enumerate(nav_items):
            if i == 0:
                _round_rect(cv, pad_x, y, right_x, y + item_h,
                            radius=item_r, fill=self.C_ACTIVE, outline="")
            else:
                _round_rect(cv, pad_x, y, right_x, y + item_h,
                            radius=item_r, fill="#efefef", outline="")
            cv.create_text(pad_x + 20, y + 20, text=item,
                           font=self.F_NAV, fill=self.C_TEXT, anchor="w")
            y += item_h + gap

        # -- Rabbit image above logout --
        _dir = os.path.dirname(__file__)
        rabbit_path = os.path.join(_dir, "image", "rabbit.png")
        rabbit_w, rabbit_h = 130, 130
        s = self._s
        sw = int(rabbit_w * s)
        sh = int(rabbit_h * s)
        sr = int(20 * s)
        if os.path.exists(rabbit_path):
            img = Image.open(rabbit_path).convert("RGBA")
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
        rabbit_tk = ImageTk.PhotoImage(result)
        self.images.append(rabbit_tk)
        rabbit_x = 125 - rabbit_w / 2
        cv.create_image(rabbit_x, 550, image=rabbit_tk, anchor="nw")

        # -- Logout button (fixed at sidebar bottom) --
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

        cv.tag_bind("logout_btn", "<Button-1>", lambda e: self.logout())

    def logout(self):
        self.destroy()

    def _set_service_filter(self, tag):
        """Update Today's Services filter and redraw only that table."""
        self.service_filter = tag
        # Save current scroll position so view doesn't jump
        yview_pos = self.canvas.yview()[0]
        # Destroy old TS child widgets
        if hasattr(self, 'ts_child') and self.ts_child:
            self.ts_child.destroy()
            self.ts_child = None
        if hasattr(self, 'ts_sb') and self.ts_sb:
            self.ts_sb.destroy()
            self.ts_sb = None
        # Redraw only the TS portion of the header (filter chips + card)
        self._redraw_ts_header()
        # Recreate scrollable rows for TS
        self._add_today_services_rows()
        # Restore scroll position to prevent view from jumping
        self.canvas.update_idletasks()
        self.canvas.yview_moveto(yview_pos)

    def _redraw_ts_header(self):
        """Redraw only Today's Services section header and filter chips on main canvas."""
        cv = self.canvas
        dx = -self.BASE_SIDE_W
        y_off = self.Y_OFF
        # Delete old TS header items by tag
        cv.delete("ts_header")
        cv.delete("svc_filter_all")
        cv.delete("svc_filter_done")
        cv.delete("svc_filter_not_done")
        # Redraw title and card background
        cv.create_text(315+dx, 695+y_off, text="Today's Services",
                       font=self.F_SECTION, fill=self.C_TEXT, anchor="w", tags="ts_header")
        filters = [("All", 45, "all"), ("Done", 55, "done"), ("Not Done", 80, "not_done")]
        fx = 500 + dx
        fy = 683 + y_off
        fh = 22
        fr = fh // 2
        for label, fw, tag in filters:
            is_active = (self.service_filter == tag)
            chip_tag = f"svc_filter_{tag}"
            if is_active:
                _round_rect(cv, fx, fy, fx + fw, fy + fh, radius=fr,
                            fill=self.C_TEXT, outline="", tags=(chip_tag, "ts_header"))
                cv.create_text(fx + fw / 2, fy + fh / 2, text=label,
                               font=("Baghdad", max(9, int(13 * self._s)), "bold"),
                               fill=self.C_WHITE, tags=(chip_tag, "ts_header"))
            else:
                _round_rect(cv, fx, fy, fx + fw, fy + fh, radius=fr,
                            fill="#E8DDD8", outline="", tags=(chip_tag, "ts_header"))
                cv.create_text(fx + fw / 2, fy + fh / 2, text=label,
                               font=("Baghdad", max(9, int(13 * self._s)), "bold"),
                               fill=self.C_TEXT, tags=(chip_tag, "ts_header"))
            cv.tag_bind(chip_tag, "<Button-1>",
                        lambda e, name=tag: self._set_service_filter(name))
            fx += fw + 8
        _round_rect(cv, 300+dx, 715+y_off, 1150+dx, 990+y_off, radius=30,
                    fill=self.C_WHITE, outline="", tags="ts_header")
        # Column headers
        cols2 = ["Pet", "Service", "Room", "Status", "Frequency"]
        xs2 = [365+dx, 475+dx, 605+dx, 765+dx, 905+dx]
        for i, col in enumerate(cols2):
            cv.create_text(xs2[i], 740+y_off, text=col, font=self.F_TABLE_HEAD,
                           fill=self.C_TEXT, anchor="w", tags="ts_header")
        cv.create_line(320+dx, 765+y_off, 1130+dx, 765+y_off,
                       fill=self.C_TEXT_LIGHT, tags="ts_header")
        # Re-scale these new items
        s = self._s
        cv.scale("ts_header", 0, 0, s, s)
        for f in ["svc_filter_all", "svc_filter_done", "svc_filter_not_done"]:
            cv.scale(f, 0, 0, s, s)

    def create_rounded_image(self, image_path, width, height, radius):
        s = self._s
        # Scale width, height, radius physically for the image
        sw = int(width * s)
        sh = int(height * s)
        sr = int(radius * s)
        
        if not os.path.exists(image_path):
            print(f"Warning: Không tìm thấy ảnh {image_path}")
            img = Image.new("RGB", (sw, sh), color="#CCCCCC")
        else:
            img = Image.open(image_path).convert("RGB")

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
        return ImageTk.PhotoImage(result)

    def draw_main_content(self):
        cv = self.canvas
        dx = -self.BASE_SIDE_W
        y_off = self.Y_OFF

        # =========================
        # HEADER (y: 30 → 70)
        # =========================
        _round_rect(cv, 300+dx, 30+y_off, 1150+dx, 70+y_off, radius=20, fill=self.C_WHITE, outline="")
        cv.create_text(330+dx, 50+y_off, text="Dashboard", font=self.F_TITLE, fill=self.C_TEXT, anchor="w")
        today_str = datetime.now().strftime("%A, %d/%m/%Y")
        cv.create_text(460+dx, 52+y_off, text=today_str, font=self.F_DATE, fill=self.C_TEXT_LIGHT, anchor="w")

        # New Booking button
        _round_rect(cv, 960+dx, 30+y_off, 1150+dx, 70+y_off, radius=20, fill=self.C_TEXT, outline="")
        cv.create_text(1045+dx, 50+y_off, text= "+ New Booking", font=self.F_TITLE, fill=self.C_WHITE)

        # =========================
        # STAT CARDS (y: 90 → 355)
        # =========================
        cs = self.data["currently_staying"]
        ar = self.data["available_rooms"]
        mr = self.data["monthly_revenue"]
        co = self.data["checkouts_today"]

        self.draw_stat_card(300+dx, 90+y_off,  520+dx, 215+y_off, "Currently staying", cs["display"], cs["subtext"])
        self.draw_stat_card(540+dx, 90+y_off,  760+dx, 215+y_off, "Available rooms",  ar["display"], ar["subtext"])
        self.draw_stat_card(300+dx, 230+y_off, 520+dx, 355+y_off, "Monthly revenue",  mr["display"], mr["subtext"])
        self.draw_stat_card(540+dx, 230+y_off, 760+dx, 355+y_off, "Check-outs today", co["display"], co["subtext"])

        # =========================
        # DOG IMAGE (y: 90 → 355, aligned with cards)
        # =========================
        _dir = os.path.dirname(__file__)
        dog_path = os.path.join(_dir, "image", "dog_1.jpg")
        dog_w, dog_h = 370, 265
        dog_tk = self.create_rounded_image(dog_path, dog_w, dog_h, radius=20)
        self.images.append(dog_tk)
        cv.create_image(780+dx, 90+y_off, image=dog_tk, anchor="nw")

        # =========================
        # CAT BANNER (y: 940 → 1090)
        # =========================
        cat_path = os.path.join(_dir, "image", "cat_1.jpg")
        cat_w, cat_h = 850, 150
        cat_tk = self.create_rounded_image(cat_path, cat_w, cat_h, radius=20)
        self.images.append(cat_tk)
        cv.create_image(300+dx, 1020+y_off, image=cat_tk, anchor="nw")

        cv.create_text(1130+dx, 1095+y_off,
                       text='"Until one has loved an animal, a part of one\'s\nsoul remains unawakened"',
                       font=("Baghdad", max(10, int(18 * self._s)), "bold"), fill=self.C_WHITE, anchor="e", justify="right")

    def draw_stat_card(self, x1, y1, x2, y2, title, value, subtext):
        cv = self.canvas
        _round_rect(cv, x1, y1, x2, y2, radius=30, fill=self.C_WHITE, outline="")
        cx = (x1 + x2) / 2
        cv.create_text(cx, y1 + 22, text=title, font=self.F_STAT_LBL, fill=self.C_TEXT)
        cv.create_text(cx, y1 + 60, text=value, font=self.F_STAT_VAL, fill=self.C_TEXT)
        cv.create_text(cx, y2 - 20, text=subtext, font=self.F_STAT_SUB, fill=self.C_TEXT_LIGHT)

    def draw_tables(self):
        """Draw section titles, card backgrounds and column headers only.
        Scrollable rows are added after scaling via _add_scrollable_rows()."""
        cv = self.canvas
        dx = -self.BASE_SIDE_W
        y_off = self.Y_OFF

        # =========================
        # ACTIVE BOOKINGS (y: 380 → 670)
        # =========================
        cv.create_text(315+dx, 380+y_off, text="Active Bookings", font=self.F_SECTION, fill=self.C_TEXT, anchor="w")
        _round_rect(cv, 300+dx, 400+y_off, 1150+dx, 670+y_off, radius=30, fill=self.C_WHITE, outline="")

        cols1 = ["Pet", "Owner", "Check in", "Check out", "Status", "Room"]
        xs1 = [365+dx, 475+dx, 605+dx, 745+dx, 880+dx, 1005+dx]
        for i, col in enumerate(cols1):
            cv.create_text(xs1[i], 425+y_off, text=col, font=self.F_TABLE_HEAD, fill=self.C_TEXT, anchor="w")
        cv.create_line(320+dx, 450+y_off, 1130+dx, 450+y_off, fill=self.C_TEXT_LIGHT)

        # =========================
        # TODAY'S SERVICES (y: 695 → 990)
        # =========================
        cv.create_text(315+dx, 695+y_off, text="Today's Services", font=self.F_SECTION,
                       fill=self.C_TEXT, anchor="w", tags="ts_header")

        # Service status filter chips
        filters = [("All", 45, "all"), ("Done", 55, "done"), ("Not Done", 80, "not_done")]
        fx = 500 + dx
        fy = 683 + y_off
        fh = 22
        fr = fh // 2
        for label, fw, tag in filters:
            is_active = (self.service_filter == tag)
            chip_tag = f"svc_filter_{tag}"
            if is_active:
                _round_rect(cv, fx, fy, fx + fw, fy + fh, radius=fr,
                            fill=self.C_TEXT, outline="", tags=(chip_tag, "ts_header"))
                cv.create_text(fx + fw / 2, fy + fh / 2, text=label,
                               font=("Baghdad", max(9, int(13 * self._s)), "bold"),
                               fill=self.C_WHITE, tags=(chip_tag, "ts_header"))
            else:
                _round_rect(cv, fx, fy, fx + fw, fy + fh, radius=fr,
                            fill="#E8DDD8", outline="", tags=(chip_tag, "ts_header"))
                cv.create_text(fx + fw / 2, fy + fh / 2, text=label,
                               font=("Baghdad", max(9, int(13 * self._s)), "bold"),
                               fill=self.C_TEXT, tags=(chip_tag, "ts_header"))
            cv.tag_bind(chip_tag, "<Button-1>",
                        lambda e, name=tag: self._set_service_filter(name))
            fx += fw + 8

        _round_rect(cv, 300+dx, 715+y_off, 1150+dx, 990+y_off, radius=30,
                    fill=self.C_WHITE, outline="", tags="ts_header")

        cols2 = ["Pet", "Service", "Room", "Status", "Frequency"]
        xs2 = [365+dx, 475+dx, 605+dx, 765+dx, 905+dx]
        for i, col in enumerate(cols2):
            cv.create_text(xs2[i], 740+y_off, text=col, font=self.F_TABLE_HEAD,
                           fill=self.C_TEXT, anchor="w", tags="ts_header")
        cv.create_line(320+dx, 765+y_off, 1130+dx, 765+y_off,
                       fill=self.C_TEXT_LIGHT, tags="ts_header")

    def _add_scrollable_rows(self):
        """Create child canvases with scrollbars for table rows (called after scaling)."""
        s = self._s
        dx = -self.BASE_SIDE_W
        y_off = self.Y_OFF
        row_h = int(35 * s)

        # ---- Active Bookings rows ----
        ab_data = [
            (b["pet"], b["owner"], b["check_in"], b["check_out"], b["status"], b["room"])
            for b in self.data["active_bookings"]
        ]
        ab_rel_xs = [45, 155, 285, 425, 560, 685]
        ab_x = int((300 + dx + 20) * s)
        ab_y = int((456 + y_off) * s)
        ab_w = int(810 * s)
        ab_h = int(200 * s)
        self._make_scrollable_table(ab_x, ab_y, ab_w, ab_h, ab_data, ab_rel_xs, row_h)

        # ---- Today's Services rows ----
        self._add_today_services_rows()

    def _add_today_services_rows(self):
        """Create scrollable Today's Services rows, filtered by service_filter."""
        s = self._s
        dx = -self.BASE_SIDE_W
        y_off = self.Y_OFF
        row_h = int(35 * s)

        ts_all = [
            (s["pet"], s["service"], s["room"], s["status"], s["frequency"])
            for s in self.data["today_services"]
        ]
        if self.service_filter == "done":
            ts_data = [r for r in ts_all if str(r[3]).lower() == "done"]
        elif self.service_filter == "not_done":
            ts_data = [r for r in ts_all if str(r[3]).lower() != "done"]
        else:
            ts_data = ts_all

        ts_rel_xs = [45, 155, 285, 445, 585]
        ts_x = int((300 + dx + 20) * s)
        ts_y = int((771 + y_off) * s)
        ts_w = int(810 * s)
        ts_h = int(205 * s)
        self.ts_child, self.ts_sb = self._make_scrollable_table(
            ts_x, ts_y, ts_w, ts_h, ts_data, ts_rel_xs, row_h)

    def _make_scrollable_table(self, x, y, w, h, data, rel_xs, row_h):
        """Create a child canvas + optional scrollbar for table rows at scaled position."""
        s = self._s
        total_h = len(data) * row_h + 5

        if not data:
            return

        sb_w_base = 15
        sb_w = int(sb_w_base * s)
        child_w = w - sb_w - 4 if total_h > h else w

        # Scale X coordinates to match the scaled canvas
        xs = [int(rx * s) for rx in rel_xs]
        line_y_off = int(17 * s)

        child = tk.Canvas(self.canvas, bg=self.C_WHITE, highlightthickness=0, bd=0)
        child.configure(scrollregion=(0, 0, child_w, total_h))

        yy = row_h // 2
        for ri, row in enumerate(data):
            for i, val in enumerate(row):
                child.create_text(xs[i], yy, text=str(val) if val else "",
                                  font=self.F_TABLE_ROW, fill=self.C_TEXT, anchor="w")
            if ri < len(data) - 1:
                child.create_line(5, yy + line_y_off, child_w - 10, yy + line_y_off,
                                  fill=self.C_TEXT_LIGHT)
            yy += row_h

        self.canvas.create_window(x, y, anchor="nw", window=child,
                                  width=child_w, height=h)

        if total_h > h:
            sb = tk.Scrollbar(self.canvas, orient=tk.VERTICAL, command=child.yview)
            child.configure(yscrollcommand=sb.set)
            self.canvas.create_window(x + child_w + 2, y, anchor="nw",
                                      window=sb, height=h)
            if not hasattr(self, '_scrollbars'):
                self._scrollbars = []
            self._scrollbars.append(sb)

            def _on_mw(event, ccv=child):
                if sys.platform == "darwin":
                    ccv.yview_scroll(int(-event.delta), "units")
                else:
                    ccv.yview_scroll(int(-event.delta / 120), "units")
                return "break"

            child.bind("<MouseWheel>", _on_mw)
            child.bind("<Button-4>", lambda e, ccv=child: ccv.yview_scroll(-1, "units"))
            child.bind("<Button-5>", lambda e, ccv=child: ccv.yview_scroll(1, "units"))
            sb.bind("<MouseWheel>", lambda e: "break")

        if not hasattr(self, '_table_children'):
            self._table_children = []
        self._table_children.append(child)

        return child, (sb if total_h > h else None)


if __name__ == "__main__":
    app = PetDashboard()
    app.mainloop()
