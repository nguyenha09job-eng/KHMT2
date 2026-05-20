import tkinter as tk
from PIL import Image, ImageTk, ImageDraw
import os
import sys
from datetime import datetime

from app_window import AppWindow
from database import DatabaseConnection
from navigation import bind_click, bind_nav_item, logout_to_login


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


def _round_outline(cv, x1, y1, x2, y2, radius=25, color="white", width=4, tags=None):
    d = 2 * radius
    items = []
    items.append(cv.create_arc(x1, y1, x1 + d, y1 + d, start=90, extent=90, style='arc', outline=color, width=width, tags=tags))
    items.append(cv.create_arc(x2 - d, y1, x2, y1 + d, start=0, extent=90, style='arc', outline=color, width=width, tags=tags))
    items.append(cv.create_arc(x2 - d, y2 - d, x2, y2, start=270, extent=90, style='arc', outline=color, width=width, tags=tags))
    items.append(cv.create_arc(x1, y2 - d, x1 + d, y2, start=180, extent=90, style='arc', outline=color, width=width, tags=tags))
    items.append(cv.create_line(x1 + radius, y1, x2 - radius, y1, fill=color, width=width, tags=tags))
    items.append(cv.create_line(x2, y1 + radius, x2, y2 - radius, fill=color, width=width, tags=tags))
    items.append(cv.create_line(x1 + radius, y2, x2 - radius, y2, fill=color, width=width, tags=tags))
    items.append(cv.create_line(x1, y1 + radius, x1, y2 - radius, fill=color, width=width, tags=tags))
    return tuple(items)


class RoomsBackend:
    """Data layer for the Rooms screen."""

    def __init__(self, db=None):
        self.db = db or DatabaseConnection()

    @staticmethod
    def _bit_to_bool(value):
        if isinstance(value, (bytes, bytearray)):
            return value != b"\x00"
        return bool(value)

    @staticmethod
    def _format_room(room_id):
        if room_id is None:
            return "-"
        return f"R-{int(room_id):02d}"

    @staticmethod
    def _title(value, default="-"):
        if value in (None, ""):
            return default
        return str(value).replace("_", " ").title()

    def get_rooms(self):
        rows = self.db.fetch_all(
            """
            SELECT
                r.room_id,
                r.is_active,
                rt.type_name,
                rt.species,
                EXISTS (
                    SELECT 1
                    FROM bookings b
                    JOIN booking_statuses bs ON bs.status_id = b.booking_status_id
                    WHERE b.room_id = r.room_id
                      AND bs.status_name IN ('booked', 'checked_in')
                      AND b.check_in <= NOW()
                      AND b.check_out >= NOW()
                ) AS is_occupied
            FROM rooms r
            JOIN room_types rt ON rt.room_type_id = r.room_type_id
            ORDER BY
                CASE rt.species
                    WHEN 'dog' THEN 1
                    WHEN 'cat' THEN 2
                    ELSE 3
                END,
                r.room_id
            """
        )

        data = {"dog": [], "cat": [], "both": []}
        summary = {"occupied": 0, "available": 0, "cleaning": 0, "total": 0}

        for row in rows or []:
            active = self._bit_to_bool(row.get("is_active"))
            occupied = bool(row.get("is_occupied"))
            if not active:
                status = "Cleaning"
                summary["cleaning"] += 1
            elif occupied:
                status = "Occupied"
                summary["occupied"] += 1
            else:
                status = "Available"
                summary["available"] += 1

            room = {
                "room": self._format_room(row.get("room_id")),
                "type": row.get("type_name") or "-",
                "species": self._title(row.get("species")),
                "status": status,
                "available": status == "Available",
            }
            species = str(row.get("species") or "").lower()
            if species in data:
                data[species].append(room)
            else:
                data["both"].append(room)
            summary["total"] += 1

        return {"summary": summary, "rooms": data}


class RoomsDashboard(AppWindow):
    def __init__(self):
        super().__init__()
        self.title("Pet&Bed - Rooms")
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
        self.C_BG         = "#F5C97A"   # warm orange background
        self.C_SIDEBAR    = "#FFFFFF"
        self.C_TEXT       = "#4A3525"
        self.C_TEXT_LIGHT = "#7A685F"
        self.C_WHITE      = "#FFFFFF"
        self.C_ACTIVE     = "#F5A623"   # orange for active nav

        # Room card colors
        self.C_PINK_CARD  = "#F9D0D8"   # occupied / default card bg
        self.C_GREEN_CARD = "#D6EDBB"   # available card bg
        self.C_CLEAN_CARD = "#EFEFEF"
        self.C_PINK_BTN   = "#F4A7B5"   # status button on pink card
        self.C_GREEN_BTN  = "#A8D878"   # status button on green card
        self.C_CLEAN_BTN  = "#D8D4CF"

        # Legend chips
        self.C_OCC_CHIP   = "#F9D0D8"
        self.C_AVL_CHIP   = "#D6EDBB"
        self.C_CLEAN_CHIP = "#EFEFEF"

        # Fonts
        self.F_LOGO        = ("Arial Rounded MT Bold", max(16, int(40 * s)), "bold")
        self.F_NAV         = ("Baghdad", max(10, int(18 * s)))
        self.F_TITLE       = ("Arial Rounded MT Bold", max(10, int(18 * s)), "bold")
        self.F_HEADER_SUB  = ("Baghdad", max(10, int(16 * s)))
        self.F_SECTION     = ("Arial Rounded MT Bold", max(14, int(28 * s)), "bold")
        self.F_CARD_ID     = ("Baghdad", max(10, int(15 * s)), "bold")
        self.F_CARD_INFO   = ("Baghdad", max(9,  int(13 * s)))
        self.F_CARD_BTN    = ("Baghdad", max(9,  int(13 * s)), "bold")
        self.F_SEARCH      = ("Baghdad", max(10, int(16 * s)))
        self.F_LEGEND      = ("Baghdad", max(10, int(15 * s)))
        self.F_IMG_LABEL   = ("Arial Rounded MT Bold", max(14, int(26 * s)), "bold")

        self.images = []
        self.search_text = ""
        self._search_entry = None
        self.current_filter = "all"  # "all", "dog", or "cat"
        self.status_filter = "all"   # "all", "Occupied", "Available", or "Cleaning"
        self.backend = RoomsBackend()
        self.data = self.load_rooms()

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

    def load_rooms(self):
        try:
            return self.backend.get_rooms()
        except Exception as exc:
            print(f"Khong the tai du lieu Rooms: {exc}")
            return {
                "summary": {"occupied": 0, "available": 0, "cleaning": 0, "total": 0},
                "rooms": {"dog": [], "cat": [], "both": []},
            }

    def set_filter(self, new_filter):
        """Toggle filter: click same filter again → show all."""
        if self.current_filter == new_filter:
            self.current_filter = "all"
        else:
            self.current_filter = new_filter
        self.canvas.delete("all")
        self.draw_content()
        self.canvas.scale("all", 0, 0, self._s, self._s)
        self.canvas.update_idletasks()
        bbox = self.canvas.bbox("all")
        if bbox:
            self.canvas.configure(scrollregion=(bbox[0], 0, bbox[2], bbox[3] + int(60 * self._s)))


    def set_status_filter(self, new_filter):
        """Toggle status filter: click same filter again → show all."""
        if self.status_filter == new_filter:
            self.status_filter = "all"
        else:
            self.status_filter = new_filter
        self.canvas.delete("all")
        self.draw_content()
        self.canvas.scale("all", 0, 0, self._s, self._s)
        self.canvas.update_idletasks()
        bbox = self.canvas.bbox("all")
        if bbox:
            self.canvas.configure(scrollregion=(bbox[0], 0, bbox[2], bbox[3] + int(60 * self._s)))

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
            fill = self.C_ACTIVE if i == 3 else "#efefef"
            _round_rect(cv, pad_x, y, right_x, y + item_h, radius=item_r,
                        fill=fill, outline="", tags=nav_tag)
            cv.create_text(pad_x + 20, y + 20, text=item, font=self.F_NAV,
                           fill=self.C_WHITE if i == 3 else self.C_TEXT,
                           anchor="w", tags=nav_tag)
            bind_nav_item(cv, nav_tag, self, item, "Rooms")
            y += item_h + gap

        # Decorative animal icon in sidebar
        _dir = os.path.dirname(__file__)
        icon_path = os.path.join(_dir, "image", "cat.png")
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
            img = Image.new("RGB", (sw, sh), color="#CCAA66")
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

    # ─────────────────────────── ROOM CARD ──────────────────────────
    def _draw_room_card(self, cv, x, y, card_w, card_h, room):
        """Draw a single room card at (x,y). Green if available, pink otherwise."""
        r = 14
        available = room["available"]
        if room["status"] == "Cleaning":
            card_bg = self.C_CLEAN_CARD
            btn_bg = self.C_CLEAN_BTN
        else:
            card_bg  = self.C_GREEN_CARD if available else self.C_PINK_CARD
            btn_bg   = self.C_GREEN_BTN  if available else self.C_PINK_BTN

        _round_rect(cv, x, y, x + card_w, y + card_h, radius=r, fill=card_bg)

        # Text content
        mid_x = x + card_w // 2
        cv.create_text(mid_x, y + 22, text=room["room"], font=self.F_CARD_ID, fill=self.C_TEXT)
        cv.create_text(mid_x, y + 43, text=room["type"], font=self.F_CARD_INFO,
                       fill=self.C_TEXT, width=card_w - 18)
        cv.create_text(mid_x, y + 62, text=room["species"], font=self.F_CARD_INFO,
                       fill=self.C_TEXT)

        # Status button
        bw, bh = card_w - 24, 26
        bx1 = x + 12
        by1 = y + card_h - bh - 10
        bx2 = bx1 + bw
        by2 = by1 + bh
        _round_rect(cv, bx1, by1, bx2, by2, radius=bh // 2, fill=btn_bg)
        cv.create_text(mid_x, by1 + bh // 2, text=room["status"],
                       font=self.F_CARD_BTN, fill=self.C_TEXT)

    # ─────────────────────────── MAIN CONTENT ───────────────────────
    def draw_content(self):
        cv = self.canvas
        dx = -self.BASE_SIDE_W
        y  = self.Y_OFF
        _dir = os.path.dirname(__file__)
        summary = self.data["summary"]
        if self.status_filter != "all":
            rooms = {
                "dog": [r for r in self.data["rooms"]["dog"] if r["status"] == self.status_filter],
                "cat": [r for r in self.data["rooms"]["cat"] if r["status"] == self.status_filter],
                "both": [r for r in self.data["rooms"]["both"] if r["status"] == self.status_filter],
            }
        else:
            rooms = self.data["rooms"]

        # Apply search filter
        search_lower = self.search_text.strip().lower()
        if search_lower:
            rooms = {
                k: [r for r in v if search_lower in r["room"].lower()
                    or search_lower in r["type"].lower()]
                for k, v in rooms.items()
            }

        # ── HEADER BAR ──
        header_x1 = 300 + dx
        header_y1 = 30 + y
        header_x2 = 1150 + dx
        header_y2 = 70 + y
        header_cy = (header_y1 + header_y2) // 2
        _round_rect(cv, header_x1, header_y1, header_x2, header_y2,
                    radius=20, fill=self.C_WHITE)
        cv.create_text(header_x1 + 30, header_cy, text="Rooms",
                       font=self.F_TITLE, fill=self.C_TEXT, anchor="w")
        cv.create_text(header_x1 + 120, header_cy,
                       text=(f"{summary['occupied']} occupied  -  "
                             f"{summary['available']} available  -  "
                             f"{summary['cleaning']} cleaning"),
                       font=self.F_HEADER_SUB, fill=self.C_TEXT_LIGHT, anchor="w")

        # ── TOP IMAGE STRIP  (Dog | Cat | Legend) ──
        img_y = 82 + y
        img_h = 120

        # Dog image (clickable filter)
        dog_path = os.path.join(_dir, "image", "dog_room.jpg")
        dog_tk = self.create_rounded_image(dog_path, 265, img_h, radius=16)
        self.images.append(dog_tk)
        cv.create_image(300 + dx, img_y, image=dog_tk, anchor="nw", tags="filter_dog")
        cv.create_text(330 + dx, img_y + img_h - 22,
                       text="Dog", font=self.F_IMG_LABEL, fill=self.C_WHITE, anchor="w",
                       tags="filter_dog")
        cv.tag_bind("filter_dog", "<Button-1>", lambda e: self.set_filter("dog"))

        # Cat image (clickable filter)
        cat_path = os.path.join(_dir, "image", "cat_room.jpg")
        cat_tk = self.create_rounded_image(cat_path, 265, img_h, radius=16)
        self.images.append(cat_tk)
        cv.create_image(578 + dx, img_y, image=cat_tk, anchor="nw", tags="filter_cat")
        cv.create_text(608 + dx, img_y + img_h - 22,
                       text="Cat", font=self.F_IMG_LABEL, fill=self.C_WHITE, anchor="w",
                       tags="filter_cat")
        cv.tag_bind("filter_cat", "<Button-1>", lambda e: self.set_filter("cat"))

        # Active filter highlight border
        border_w = 265
        if self.current_filter == "dog":
            bx = 300 + dx
        elif self.current_filter == "cat":
            bx = 578 + dx
        else:
            bx = None
        if bx is not None:
            _round_outline(cv, bx, img_y, bx + border_w, img_y + img_h,
                           radius=16, color=self.C_WHITE, width=4, tags="filter_border")

        # Legend box
        leg_x1, leg_y1 = 856 + dx, img_y
        leg_x2, leg_y2 = 1148 + dx, img_y + img_h
        _round_rect(cv, leg_x1, leg_y1, leg_x2, leg_y2, radius=16, fill=self.C_WHITE)

        chip_w, chip_h = 252, 28
        chip_r = chip_h // 2
        chip_cx = (leg_x1 + leg_x2) // 2

        # Occupied chip
        occ_y1 = leg_y1 + 12
        occ_x1 = chip_cx - chip_w // 2
        _round_rect(cv, occ_x1, occ_y1, occ_x1 + chip_w, occ_y1 + chip_h,
                    radius=chip_r, fill=self.C_OCC_CHIP, tags="filter_occupied")
        cv.create_text(chip_cx, occ_y1 + chip_h // 2,
                       text="Occupied", font=self.F_LEGEND, fill=self.C_TEXT, tags="filter_occupied")
        cv.tag_bind("filter_occupied", "<Button-1>", lambda e: self.set_status_filter("Occupied"))

        # Available chip
        avl_y1 = occ_y1 + chip_h + 8
        _round_rect(cv, occ_x1, avl_y1, occ_x1 + chip_w, avl_y1 + chip_h,
                    radius=chip_r, fill=self.C_AVL_CHIP, tags="filter_available")
        cv.create_text(chip_cx, avl_y1 + chip_h // 2,
                       text="Available", font=self.F_LEGEND, fill=self.C_TEXT, tags="filter_available")
        cv.tag_bind("filter_available", "<Button-1>", lambda e: self.set_status_filter("Available"))

        clean_y1 = avl_y1 + chip_h + 8
        _round_rect(cv, occ_x1, clean_y1, occ_x1 + chip_w, clean_y1 + chip_h,
                    radius=chip_r, fill=self.C_CLEAN_CHIP, tags="filter_cleaning")
        cv.create_text(chip_cx, clean_y1 + chip_h // 2,
                       text="Cleaning", font=self.F_LEGEND, fill=self.C_TEXT, tags="filter_cleaning")
        cv.tag_bind("filter_cleaning", "<Button-1>", lambda e: self.set_status_filter("Cleaning"))

        # Highlight active status filter border
        if self.status_filter == "Occupied":
            _round_outline(cv, occ_x1 - 1, occ_y1 - 1, occ_x1 + chip_w + 1, occ_y1 + chip_h + 1,
                           radius=chip_r + 1, color="#A89F95", width=3, tags="status_border")
        elif self.status_filter == "Available":
            _round_outline(cv, occ_x1 - 1, avl_y1 - 1, occ_x1 + chip_w + 1, avl_y1 + chip_h + 1,
                           radius=chip_r + 1, color="#A89F95", width=3, tags="status_border")
        elif self.status_filter == "Cleaning":
            _round_outline(cv, occ_x1 - 1, clean_y1 - 1, occ_x1 + chip_w + 1, clean_y1 + chip_h + 1,
                           radius=chip_r + 1, color="#A89F95", width=3, tags="status_border")

        # ── SEARCH BAR ──
        s_y1, s_y2 = 216 + y, 252 + y
        s_r = (s_y2 - s_y1) // 2
        _round_rect(cv, 300 + dx, s_y1, 1150 + dx, s_y2, radius=s_r, fill=self.C_WHITE)
        cv.create_text(338 + dx, (s_y1 + s_y2) // 2,
                       text="", font=self.F_SEARCH, anchor="w")
        # Search entry overlay
        search_x = (300 + dx + 1150 + dx) // 2
        search_y = (s_y1 + s_y2) // 2
        search_w = int(570 * self._s)
        search_h = int((s_y2 - s_y1) * self._s * 0.55)
        ic_cx, ic_cy = 1125 + dx, (s_y1 + s_y2) // 2
        ic_r = 9
        cv.create_oval(ic_cx - ic_r, ic_cy - ic_r, ic_cx + ic_r, ic_cy + ic_r,
                       outline=self.C_TEXT, width=2)
        cv.create_line(ic_cx + int(ic_r * 0.72), ic_cy + int(ic_r * 0.72),
                       ic_cx + int(ic_r * 1.65), ic_cy + int(ic_r * 1.65),
                       fill=self.C_TEXT, width=2)

        # Search entry widget
        if self._search_entry is None:
            self._search_entry = tk.Entry(cv, font=self.F_SEARCH, relief=tk.FLAT,
                                          bg=self.C_WHITE, fg="#B5B0AA",
                                          highlightthickness=0,
                                          insertbackground=self.C_TEXT)
            self._search_entry.insert(0, "Search room_id")
            self._search_entry.bind("<KeyRelease>", self._on_search_key)
            self._search_entry.bind("<FocusIn>", self._on_search_focusin)
            self._search_entry.bind("<FocusOut>", self._on_search_focusout)

        cv.create_window(search_x, search_y, window=self._search_entry,
                         anchor="center", width=search_w,
                         tags="search_entry")

        # Search results count
        if self.search_text:
            total = sum(len(v) for v in rooms.values())
            cv.create_text(1130 + dx, (s_y1 + s_y2) // 2,
                           text=f"{total} found", font=self.F_LEGEND,
                           fill=self.C_TEXT_LIGHT, anchor="e", tags="search_count")

        # ── DOG SECTION ──
        sec_y = 270 + y
        next_y = sec_y  # track vertical position

        if self.current_filter in ("all", "dog"):
            cv.create_text(300 + dx, next_y, text="Dog",
                           font=self.F_SECTION, fill=self.C_TEXT, anchor="w")
            dog_grid_y = next_y + 30
            self._draw_room_grid(cv, dx, dog_grid_y, rooms["dog"])
            next_y = dog_grid_y + self._grid_height(len(rooms["dog"])) + 30

        # ── CAT SECTION ──
        if self.current_filter in ("all", "cat"):
            cv.create_text(300 + dx, next_y, text="Cat",
                           font=self.F_SECTION, fill=self.C_TEXT, anchor="w")
            cat_grid_y = next_y + 30
            self._draw_room_grid(cv, dx, cat_grid_y, rooms["cat"])
            next_y = cat_grid_y + self._grid_height(len(rooms["cat"])) + 30

        # ── FAMILY (both species) ── only when showing all
        if self.current_filter == "all" and rooms["both"]:
            cv.create_text(300 + dx, next_y, text="Family",
                           font=self.F_SECTION, fill=self.C_TEXT, anchor="w")
            family_grid_y = next_y + 30
            self._draw_room_grid(cv, dx, family_grid_y, rooms["both"])

    def _on_search_key(self, event):
        """Handle key release in search entry."""
        if event.keysym in ("Escape", "Tab", "Up", "Down", "Left", "Right", "Return"):
            if event.keysym == "Escape":
                self._search_entry.delete(0, tk.END)
                self._search_entry.insert(0, "Search room_id")
                self._search_entry.config(fg="#B5B0AA")
                self.canvas.focus_set()
            return

        text = self._search_entry.get()
        if text == "Search room_id":
            text = ""

        if text.strip().lower() != self.search_text.lower():
            self.search_text = text.strip()
            self.canvas.delete("all")
            self.draw_content()
            self.canvas.scale("all", 0, 0, self._s, self._s)
            self.canvas.update_idletasks()
            bbox = self.canvas.bbox("all")
            if bbox:
                self.canvas.configure(scrollregion=(bbox[0], 0, bbox[2], bbox[3] + int(60 * self._s)))

    def _on_search_focusin(self, event):
        """Clear placeholder on focus."""
        if self._search_entry.get() == "Search room_id":
            self._search_entry.delete(0, tk.END)
            self._search_entry.config(fg=self.C_TEXT)

    def _on_search_focusout(self, event):
        """Restore placeholder when empty and focus lost."""
        if self._search_entry.get().strip() == "":
            self._search_entry.delete(0, tk.END)
            self._search_entry.insert(0, "Search room_id")
            self._search_entry.config(fg="#B5B0AA")

    def _grid_height(self, n_rooms):
        """Calculate the pixel height of a room grid with n_rooms."""
        card_w = 184
        card_h = 110
        gap    = 18
        cols   = 4
        rows   = max(1, (n_rooms + cols - 1) // cols)
        pad_v  = 22
        return rows * card_h + (rows - 1) * gap + pad_v * 2 + 20   # +20 for card shadow feel

    def _draw_room_grid(self, cv, dx, grid_y, rooms):
        """
        Draw a white rounded card containing a grid of room cards.
        """
        card_w  = 184
        card_h  = 110
        gap_x   = 18
        gap_y   = 18
        cols    = 4
        pad_h   = 28   # horizontal padding inside white card
        pad_v   = 22   # vertical padding

        rows = max(1, (len(rooms) + cols - 1) // cols)
        inner_w = cols * card_w + (cols - 1) * gap_x
        outer_w = inner_w + pad_h * 2
        outer_h = rows * card_h + (rows - 1) * gap_y + pad_v * 2

        ox1 = 300 + dx
        oy1 = grid_y
        ox2 = ox1 + 848   # match content width  (≈ 1150-300-2)
        oy2 = oy1 + outer_h

        _round_rect(cv, ox1, oy1, ox2, oy2, radius=24, fill=self.C_WHITE)

        # Center the grid horizontally inside the white card
        total_grid_w = cols * card_w + (cols - 1) * gap_x
        start_x = ox1 + (ox2 - ox1 - total_grid_w) // 2
        start_y = oy1 + pad_v

        if not rooms:
            cv.create_text((ox1 + ox2) // 2, oy1 + outer_h // 2,
                           text="No rooms found",
                           font=self.F_CARD_INFO, fill=self.C_TEXT_LIGHT)
            return

        for i, room in enumerate(rooms):
            col = i % cols
            row = i // cols
            cx  = start_x + col * (card_w + gap_x)
            cy  = start_y + row * (card_h + gap_y)
            self._draw_room_card(cv, cx, cy, card_w, card_h, room)


if __name__ == "__main__":
    app = RoomsDashboard()
    app.mainloop()
