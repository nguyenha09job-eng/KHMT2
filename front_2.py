import tkinter as tk
from PIL import Image, ImageTk, ImageDraw
import os
import sys
from datetime import datetime

def _round_rect(cv, x1, y1, x2, y2, radius=25, **kwargs):
    """Draw a rounded rectangle using arcs for true rounded corners."""
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

# =========================================================
# DATA
# =========================================================
PETS = [
    {"name": "Milo",  "type": "Dog", "room": "R-03", "room_type": "Standard",
     "weight": "15kg", "sex": "Male",   "breed": "Corgi",    "sterilized": True,
     "service": "Grooming", "status": "Done", "health": "Good", "special": "None", "need": False},
    {"name": "Luna",  "type": "Cat", "room": "R-08", "room_type": "VIP",
     "weight": "5kg",  "sex": "Female", "breed": "British",  "sterilized": False,
     "service": "Bathing",  "status": "Pending", "health": "Allergy", "special": "Diet food", "need": True},
    {"name": "Rocky", "type": "Dog", "room": "R-01", "room_type": "Standard",
     "weight": "18kg", "sex": "Male",   "breed": "Husky",    "sterilized": True,
     "service": "Daycare",  "status": "Done", "health": "Good", "special": "None", "need": False},
    {"name": "Kitty", "type": "Cat", "room": "R-11", "room_type": "Standard",
     "weight": "4kg",  "sex": "Female", "breed": "Persian",  "sterilized": False,
     "service": "Grooming", "status": "Not done", "health": "Skin issue", "special": "Medication", "need": True},
    {"name": "Mochi", "type": "Dog", "room": "R-05", "room_type": "VIP",
     "weight": "10kg", "sex": "Male",   "breed": "Poodle",   "sterilized": False,
     "service": "Nail Trim","status": "Done", "health": "Good", "special": "None", "need": False},
]


class CareViewDashboard(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("Pet&Bed - Care View")
        self.attributes("-fullscreen", True)
        self.configure(bg="#DDE89D")
        self.update_idletasks()

        self.W = self.winfo_width()
        self.H = self.winfo_height()

        self.BASE_W = 1200.0
        self.BASE_H = 850.0
        self._s = self.W / self.BASE_W
        s = self._s
        self.Y_OFF = 20

        # Colors
        self.C_BG = "#DDE89D"
        self.C_SIDEBAR = "#FFFFFF"
        self.C_TEXT = "#4A3525"
        self.C_TEXT_LIGHT = "#7A685F"
        self.C_WHITE = "#FFFFFF"
        self.C_ACTIVE = "#C8DB6D"
        self.C_TAG = "#EFE5DD"
        self.C_TEAL = "#C9E7E5"
        self.C_CARD = "#F8F8F6"
        self.C_LINE = "#DDD4CB"

        # Fonts
        self.F_LOGO = ("Arial Rounded MT Bold", max(16, int(40 * s)), "bold")
        self.F_NAV = ("Baghdad", max(10, int(18 * s)))
        self.F_TITLE = ("Arial Rounded MT Bold", max(10, int(18 * s)), "bold")
        self.F_DATE = ("Baghdad", max(10, int(18 * s)))
        self.F_FILTER = ("Baghdad", max(9, int(14 * s)), "bold")
        self.F_CARD_NAME = ("Arial Rounded MT Bold", max(12, int(22 * s)), "bold")
        self.F_CARD_INFO = ("Baghdad", max(9, int(14 * s)))
        self.F_CARD_TAG = ("Baghdad", max(9, int(13 * s)))
        self.F_CARD_BTN = ("Baghdad", max(9, int(13 * s)), "bold")
        self.F_QUOTE = ("Arial Rounded MT Bold", max(10, int(16 * s)), "bold")

        self.images = []
        self.current_filter = "All"

        # -- Layout --
        main = tk.Frame(self, bg=self.C_BG)
        main.pack(fill=tk.BOTH, expand=True)

        self.BASE_SIDE_W = 260
        side_w = int(self.BASE_SIDE_W * s)

        # Sidebar
        self.side_frame = tk.Frame(main, width=side_w, bg=self.C_BG)
        self.side_frame.pack(side=tk.LEFT, fill=tk.Y)
        self.side_frame.pack_propagate(False)

        self.sidebar_canvas = tk.Canvas(self.side_frame, width=side_w, height=self.H,
                                        bg=self.C_BG, highlightthickness=0)
        self.sidebar_canvas.pack(fill=tk.BOTH, expand=True)

        # Content
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
        self.draw_header()
        self.draw_banner()
        self.draw_pet_cards(PETS)

        # Scale
        self.sidebar_canvas.scale("all", 0, 0, s, s)
        self.canvas.scale("all", 0, 0, s, s)

        # Scrollregion
        self.canvas.update_idletasks()
        bbox = self.canvas.bbox("all")
        if bbox:
            self.canvas.configure(scrollregion=(bbox[0], 0, bbox[2], bbox[3] + 50 * s))
        else:
            self.canvas.configure(scrollregion=self.canvas.bbox("all"))

        # Scroll bindings
        def _on_mw(event):
            delta = event.delta
            if sys.platform == "darwin":
                self.canvas.yview_scroll(int(-delta), "units")
            else:
                self.canvas.yview_scroll(int(-delta / 120), "units")

        self.canvas.bind("<MouseWheel>", _on_mw, add="+")
        self.canvas.bind("<Button-4>", lambda e: self.canvas.yview_scroll(-1, "units"), add="+")
        self.canvas.bind("<Button-5>", lambda e: self.canvas.yview_scroll(1, "units"), add="+")

        def _update_scrollregion(_e=None):
            bbox = self.canvas.bbox("all")
            if bbox:
                self.canvas.configure(scrollregion=(bbox[0], 0, bbox[2], bbox[3] + 50 * self._s))
        self.canvas.bind("<Configure>", _update_scrollregion)

        self.bind("<Escape>", lambda e: self.destroy())

    # =====================================================
    # SIDEBAR (identical to front_1 but Care View active)
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
            if i == 1:  # Care View active
                _round_rect(cv, pad_x, y, right_x, y + item_h,
                            radius=item_r, fill=self.C_ACTIVE, outline="")
            else:
                _round_rect(cv, pad_x, y, right_x, y + item_h,
                            radius=item_r, fill="#efefef", outline="")
            cv.create_text(pad_x + 20, y + 20, text=item,
                           font=self.F_NAV, fill=self.C_TEXT, anchor="w")
            y += item_h + gap

        # Rabbit image
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

    # =====================================================
    # HEADER with filter buttons
    # =====================================================
    def draw_header(self):
        cv = self.canvas
        dx = -self.BASE_SIDE_W
        y_off = self.Y_OFF

        # Header bar
        _round_rect(cv, 300+dx, 30+y_off, 1150+dx, 70+y_off, radius=20,
                    fill=self.C_WHITE, outline="")
        cv.create_text(330+dx, 50+y_off, text="Care View",
                       font=self.F_TITLE, fill=self.C_TEXT, anchor="w")
        cv.create_text(460+dx, 52+y_off, text=datetime.now().strftime("%A, %d/%m/%Y"),
                       font=self.F_DATE, fill=self.C_TEXT_LIGHT, anchor="w")

        # Filter buttons: All (active), Dog, Cat, Needs Attention
        filters = [("All", 80), ("Dog", 70), ("Cat", 70), ("Needs Attention", 140)]
        fx = 740 + dx
        for label, fw in filters:
            if label == "All":
                _round_rect(cv, fx, 30+y_off, fx+fw, 70+y_off, radius=20,
                            fill=self.C_TEXT, outline="")
                cv.create_text(fx + fw/2, 50+y_off, text=label,
                               font=("Baghdad", max(10, int(17 * self._s)), "bold"), fill=self.C_WHITE)
            else:
                cv.create_text(fx + fw/2, 50+y_off, text=label,
                               font=("Baghdad", max(10, int(17 * self._s)), "bold"), fill=self.C_TEXT)
            fx += fw + 12

    # =====================================================
    # BANNER IMAGE with quote
    # =====================================================
    def draw_banner(self):
        cv = self.canvas
        dx = -self.BASE_SIDE_W
        y_off = self.Y_OFF

        _dir = os.path.dirname(__file__)
        banner_path = os.path.join(_dir, "image", "careview.jpg")
        banner_w, banner_h = 850, 200
        banner_tk = self.create_rounded_image(banner_path, banner_w, banner_h, radius=24, crop_y=0.0)
        self.images.append(banner_tk)
        cv.create_image(300+dx, 75+y_off, image=banner_tk, anchor="nw")

        # Quote overlay
        cv.create_text(330+dx, 150+y_off,
                       text='"Sometimes the smallest things take up the\nmost room in your heart."',
                       font=self.F_QUOTE, fill=self.C_WHITE, anchor="w", justify="left")

    # =====================================================
    # PET CARDS GRID (3 columns)
    # =====================================================
    def draw_pet_cards(self, pets):
        cv = self.canvas
        dx = -self.BASE_SIDE_W
        y_off = self.Y_OFF

        # Card dimensions
        card_w = 260
        card_h = 280
        card_r = 24
        cols = 3
        gap_x = 15
        gap_y = 20
        start_x = 300 + dx
        start_y = 300 + y_off

        for idx, pet in enumerate(pets):
            col = idx % cols
            row = idx // cols
            x1 = start_x + col * (card_w + gap_x)
            y1 = start_y + row * (card_h + gap_y)
            x2 = x1 + card_w
            y2 = y1 + card_h

            self._draw_one_card(cv, x1, y1, x2, y2, card_r, pet)

    def _draw_one_card(self, cv, x1, y1, x2, y2, radius, pet):
        # Card background
        _round_rect(cv, x1, y1, x2, y2, radius=radius, fill=self.C_CARD, outline="")

        cx = (x1 + x2) / 2
        pad = 18
        lx = x1 + pad  # left text x

        # Pet name (centered, bold)
        cv.create_text(cx, y1 + 22, text=pet["name"],
                       font=self.F_CARD_NAME, fill=self.C_TEXT)

        # Room + Link cam button
        cv.create_text(lx, y1 + 48, text=f"Room {pet['room']}",
                       font=self.F_CARD_INFO, fill=self.C_TEXT, anchor="w")
        cv.create_text(lx, y1 + 65, text=pet["room_type"],
                       font=self.F_CARD_INFO, fill=self.C_TEXT, anchor="w")

        # Link cam button (right side)
        btn_x1 = x2 - pad - 75
        btn_y1 = y1 + 42
        btn_x2 = x2 - pad
        btn_y2 = y1 + 65
        _round_rect(cv, btn_x1, btn_y1, btn_x2, btn_y2, radius=10,
                    fill=self.C_TEAL, outline="")
        cv.create_text((btn_x1+btn_x2)/2, (btn_y1+btn_y2)/2, text="Link cam",
                       font=self.F_CARD_BTN, fill=self.C_TEXT)

        # Tag: weight - sex - breed
        tag_text = f"  {pet['weight']} - {pet['sex']} - {pet['breed']}  "
        tag_y1 = y1 + 80
        tag_y2 = y1 + 100
        tag_x2 = lx + 170
        _round_rect(cv, lx, tag_y1, tag_x2, tag_y2, radius=10,
                    fill=self.C_TAG, outline="")
        cv.create_text(lx + 85, (tag_y1+tag_y2)/2, text=tag_text,
                       font=self.F_CARD_TAG, fill=self.C_TEXT)

        # Tag: Sterilized
        ster_text = f"  Sterilized: {'Yes' if pet['sterilized'] else 'No'}  "
        ster_y1 = y1 + 108
        ster_y2 = y1 + 128
        ster_x2 = lx + 130
        _round_rect(cv, lx, ster_y1, ster_x2, ster_y2, radius=10,
                    fill=self.C_TAG, outline="")
        cv.create_text(lx + 65, (ster_y1+ster_y2)/2, text=ster_text,
                       font=self.F_CARD_TAG, fill=self.C_TEXT)

        # Divider line
        cv.create_line(lx, y1 + 140, x2 - pad, y1 + 140, fill=self.C_LINE)

        # Service type + Status button
        cv.create_text(lx, y1 + 158, text=pet["service"],
                       font=self.F_CARD_INFO, fill=self.C_TEXT, anchor="w")

        st_x1 = x2 - pad - 70
        st_y1 = y1 + 148
        st_x2 = x2 - pad
        st_y2 = y1 + 168
        _round_rect(cv, st_x1, st_y1, st_x2, st_y2, radius=10,
                    fill=self.C_TEAL, outline="")
        cv.create_text((st_x1+st_x2)/2, (st_y1+st_y2)/2, text=pet["status"],
                       font=self.F_CARD_BTN, fill=self.C_TEXT)

        # Divider
        cv.create_line(lx, y1 + 180, x2 - pad, y1 + 180, fill=self.C_LINE)

        # Health condition
        cv.create_text(lx, y1 + 198, text=f"Health: {pet['health']}",
                       font=self.F_CARD_INFO, fill=self.C_TEXT, anchor="w")

        # Divider
        cv.create_line(lx, y1 + 215, x2 - pad, y1 + 215, fill=self.C_LINE)

        # Special requirement
        cv.create_text(lx, y1 + 233, text=f"Special: {pet['special']}",
                       font=self.F_CARD_INFO, fill=self.C_TEXT, anchor="w")


if __name__ == "__main__":
    app = CareViewDashboard()
    app.mainloop()
