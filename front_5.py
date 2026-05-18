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


class RoomsDashboard(tk.Tk):
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
        self.C_PINK_BTN   = "#F4A7B5"   # status button on pink card
        self.C_GREEN_BTN  = "#A8D878"   # status button on green card

        # Legend chips
        self.C_OCC_CHIP   = "#F9D0D8"
        self.C_AVL_CHIP   = "#D6EDBB"

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
            fill = self.C_ACTIVE if i == 3 else "#efefef"
            _round_rect(cv, pad_x, y, right_x, y + item_h, radius=item_r, fill=fill, outline="")
            cv.create_text(pad_x + 20, y + 20, text=item, font=self.F_NAV,
                           fill=self.C_WHITE if i == 3 else self.C_TEXT, anchor="w")
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
        cv.tag_bind("logout_btn", "<Button-1>", lambda e: self.destroy())

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
    def _draw_room_card(self, cv, x, y, card_w, card_h, available=False):
        """Draw a single room card at (x,y). Green if available, pink otherwise."""
        r = 14
        card_bg  = self.C_GREEN_CARD if available else self.C_PINK_CARD
        btn_bg   = self.C_GREEN_BTN  if available else self.C_PINK_BTN

        _round_rect(cv, x, y, x + card_w, y + card_h, radius=r, fill=card_bg)

        # Text content
        mid_x = x + card_w // 2
        cv.create_text(mid_x, y + 22, text="Room_ID",   font=self.F_CARD_ID,   fill=self.C_TEXT)
        cv.create_text(mid_x, y + 40, text="Type_name", font=self.F_CARD_INFO,  fill=self.C_TEXT)
        cv.create_text(mid_x, y + 56, text="Species",   font=self.F_CARD_INFO,  fill=self.C_TEXT)

        # Status button
        bw, bh = card_w - 24, 26
        bx1 = x + 12
        by1 = y + card_h - bh - 10
        bx2 = bx1 + bw
        by2 = by1 + bh
        _round_rect(cv, bx1, by1, bx2, by2, radius=bh // 2, fill=btn_bg)
        cv.create_text(mid_x, by1 + bh // 2, text="Status",
                       font=self.F_CARD_BTN, fill=self.C_TEXT)

    # ─────────────────────────── MAIN CONTENT ───────────────────────
    def draw_content(self):
        cv = self.canvas
        dx = -self.BASE_SIDE_W
        y  = self.Y_OFF
        _dir = os.path.dirname(__file__)

        # ── HEADER BAR ──
        _round_rect(cv, 300 + dx, 30 + y, 1150 + dx, 68 + y, radius=20, fill=self.C_WHITE)
        cv.create_text(330 + dx, 49 + y, text="Rooms",
                       font=self.F_TITLE, fill=self.C_TEXT, anchor="w")
        cv.create_text(420 + dx, 49 + y,
                       text="7 occupied  -  8 available  -  1 cleaning",
                       font=self.F_HEADER_SUB, fill=self.C_TEXT_LIGHT, anchor="w")

        # ── TOP IMAGE STRIP  (Dog | Cat | Legend) ──
        img_y = 82 + y
        img_h = 120

        # Dog image
        dog_path = os.path.join(_dir, "image", "dog_room.jpg")
        dog_tk = self.create_rounded_image(dog_path, 265, img_h, radius=16)
        self.images.append(dog_tk)
        cv.create_image(300 + dx, img_y, image=dog_tk, anchor="nw")
        # Label overlay
        cv.create_text(330 + dx, img_y + img_h - 22,
                       text="Dog", font=self.F_IMG_LABEL, fill=self.C_WHITE, anchor="w")

        # Cat image
        cat_path = os.path.join(_dir, "image", "cat_room.jpg")
        cat_tk = self.create_rounded_image(cat_path, 265, img_h, radius=16)
        self.images.append(cat_tk)
        cv.create_image(578 + dx, img_y, image=cat_tk, anchor="nw")
        cv.create_text(608 + dx, img_y + img_h - 22,
                       text="Cat", font=self.F_IMG_LABEL, fill=self.C_WHITE, anchor="w")

        # Legend box
        leg_x1, leg_y1 = 856 + dx, img_y
        leg_x2, leg_y2 = 1148 + dx, img_y + img_h
        _round_rect(cv, leg_x1, leg_y1, leg_x2, leg_y2, radius=16, fill=self.C_WHITE)

        chip_w, chip_h = 252, 36
        chip_r = chip_h // 2
        chip_cx = (leg_x1 + leg_x2) // 2

        # Occupied chip
        occ_y1 = leg_y1 + 18
        occ_x1 = chip_cx - chip_w // 2
        _round_rect(cv, occ_x1, occ_y1, occ_x1 + chip_w, occ_y1 + chip_h,
                    radius=chip_r, fill=self.C_OCC_CHIP)
        cv.create_text(chip_cx, occ_y1 + chip_h // 2,
                       text="Occupied", font=self.F_LEGEND, fill=self.C_TEXT)

        # Available chip
        avl_y1 = occ_y1 + chip_h + 12
        _round_rect(cv, occ_x1, avl_y1, occ_x1 + chip_w, avl_y1 + chip_h,
                    radius=chip_r, fill=self.C_AVL_CHIP)
        cv.create_text(chip_cx, avl_y1 + chip_h // 2,
                       text="Available", font=self.F_LEGEND, fill=self.C_TEXT)

        # ── SEARCH BAR ──
        s_y1, s_y2 = 216 + y, 252 + y
        s_r = (s_y2 - s_y1) // 2
        _round_rect(cv, 300 + dx, s_y1, 1150 + dx, s_y2, radius=s_r, fill=self.C_WHITE)
        cv.create_text(338 + dx, (s_y1 + s_y2) // 2,
                       text="Search room_id", font=self.F_SEARCH,
                       fill="#B5B0AA", anchor="w")
        ic_cx, ic_cy = 1125 + dx, (s_y1 + s_y2) // 2
        ic_r = 9
        cv.create_oval(ic_cx - ic_r, ic_cy - ic_r, ic_cx + ic_r, ic_cy + ic_r,
                       outline=self.C_TEXT, width=2)
        cv.create_line(ic_cx + int(ic_r * 0.72), ic_cy + int(ic_r * 0.72),
                       ic_cx + int(ic_r * 1.65), ic_cy + int(ic_r * 1.65),
                       fill=self.C_TEXT, width=2)

        # ── DOG SECTION ──
        sec_y = 270 + y
        cv.create_text(300 + dx, sec_y, text="Dog",
                       font=self.F_SECTION, fill=self.C_TEXT, anchor="w")

        dog_grid_y = sec_y + 30
        self._draw_room_grid(cv, dx, dog_grid_y,
                             n_rooms=7, n_available_last=1)

        # ── CAT SECTION ──
        cat_sec_y = dog_grid_y + self._grid_height(7) + 30
        cv.create_text(300 + dx, cat_sec_y, text="Cat",
                       font=self.F_SECTION, fill=self.C_TEXT, anchor="w")

        cat_grid_y = cat_sec_y + 30
        self._draw_room_grid(cv, dx, cat_grid_y,
                             n_rooms=7, n_available_last=1)

    def _grid_height(self, n_rooms):
        """Calculate the pixel height of a room grid with n_rooms."""
        card_w = 184
        card_h = 110
        gap    = 18
        cols   = 4
        rows   = (n_rooms + cols - 1) // cols
        pad_v  = 22
        return rows * card_h + (rows - 1) * gap + pad_v * 2 + 20   # +20 for card shadow feel

    def _draw_room_grid(self, cv, dx, grid_y, n_rooms=7, n_available_last=1):
        """
        Draw a white rounded card containing a grid of room cards.
        The last n_available_last cards are rendered as 'available' (green).
        """
        card_w  = 184
        card_h  = 110
        gap_x   = 18
        gap_y   = 18
        cols    = 4
        pad_h   = 28   # horizontal padding inside white card
        pad_v   = 22   # vertical padding

        rows = (n_rooms + cols - 1) // cols
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

        for i in range(n_rooms):
            col = i % cols
            row = i // cols
            cx  = start_x + col * (card_w + gap_x)
            cy  = start_y + row * (card_h + gap_y)
            available = (i >= n_rooms - n_available_last)
            self._draw_room_card(cv, cx, cy, card_w, card_h, available=available)


if __name__ == "__main__":
    app = RoomsDashboard()
    app.mainloop()