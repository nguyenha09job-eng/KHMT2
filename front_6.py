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


class CustomerPetDashboard(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Pet&Bed - Customer & Pet")
        self.attributes("-fullscreen", True)
        self.configure(bg="#F2D5D5")
        self.update_idletasks()

        self.W = self.winfo_width()
        self.H = self.winfo_height()
        self.BASE_W = 1200.0
        self.BASE_H = 850.0
        self._s = self.W / self.BASE_W
        s = self._s
        self.Y_OFF = 20

        # Colors
        self.C_BG         = "#F2D5D5"
        self.C_SIDEBAR    = "#FFFFFF"
        self.C_TEXT       = "#4A3525"
        self.C_TEXT_LIGHT = "#7A685F"
        self.C_WHITE      = "#FFFFFF"
        self.C_ACTIVE     = "#E6B8B8"   # pink active nav
        self.C_DIVIDER    = "#ECD8D8"

        # Pet chip colors
        self.C_DOG_CHIP   = "#F5E0C0"   # warm peach for dog
        self.C_CAT_CHIP   = "#F5D0C8"   # soft salmon for cat

        # Profile button
        self.C_PROFILE_BG = "#B8D8D5"   # teal-ish
        self.C_PROFILE_FG = "#FFFFFF"

        # Fonts
        self.F_LOGO       = ("Arial Rounded MT Bold", max(16, int(40 * s)), "bold")
        self.F_NAV        = ("Baghdad", max(10, int(18 * s)))
        self.F_TITLE      = ("Arial Rounded MT Bold", max(10, int(18 * s)), "bold")
        self.F_TABLE_HEAD = ("Baghdad", max(10, int(16 * s)), "bold")
        self.F_TABLE_BODY = ("Baghdad", max(10, int(15 * s)))
        self.F_CHIP       = ("Baghdad", max(9,  int(14 * s)), "bold")
        self.F_PROFILE    = ("Baghdad", max(9,  int(14 * s)), "bold")
        self.F_SEARCH     = ("Baghdad", max(10, int(16 * s)))

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
            fill = self.C_ACTIVE if i == 4 else "#efefef"
            _round_rect(cv, pad_x, y, right_x, y + item_h, radius=item_r, fill=fill, outline="")
            cv.create_text(pad_x + 20, y + 20, text=item, font=self.F_NAV,
                           fill=self.C_TEXT, anchor="w")
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
            img = Image.new("RGB", (sw, sh), color="#D4A0A0")
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

    # ─────────────────────────── PET CHIP ───────────────────────────
    def _draw_pet_chip(self, cv, cx, cy, emoji, name, bg):
        """Draw a pill chip with emoji + name."""
        chip_w = len(name) * 10 + 52
        chip_h = 30
        x1 = cx - chip_w // 2
        y1 = cy - chip_h // 2
        x2 = x1 + chip_w
        y2 = y1 + chip_h
        _round_rect(cv, x1, y1, x2, y2, radius=chip_h // 2, fill=bg)
        cv.create_text(cx - len(name) * 3, cy, text=f"{emoji} {name}",
                       font=self.F_CHIP, fill=self.C_TEXT)

    # ─────────────────────────── MAIN CONTENT ───────────────────────
    def draw_content(self):
        cv = self.canvas
        dx = -self.BASE_SIDE_W
        y  = self.Y_OFF

        # ── HEADER BAR ──
        _round_rect(cv, 300 + dx, 30 + y, 1150 + dx, 68 + y, radius=20, fill=self.C_WHITE)
        cv.create_text(330 + dx, 49 + y, text="Customer & Pet",
                       font=self.F_TITLE, fill=self.C_TEXT, anchor="w")

        # ── BANNER IMAGE ──
        _dir = os.path.dirname(__file__)
        banner_path = os.path.join(_dir, "image", "customer.jpg")
        banner_w, banner_h = 848, 172
        banner_tk = self.create_rounded_image(banner_path, banner_w, banner_h, radius=20)
        self.images.append(banner_tk)
        cv.create_image(300 + dx, 82 + y, image=banner_tk, anchor="nw")

        # ── SEARCH BAR ──
        s_y1, s_y2 = 268 + y, 304 + y
        s_r = (s_y2 - s_y1) // 2
        _round_rect(cv, 300 + dx, s_y1, 1150 + dx, s_y2, radius=s_r, fill=self.C_WHITE)
        cv.create_text(338 + dx, (s_y1 + s_y2) // 2,
                       text="Search by name, phone number, or pet name",
                       font=self.F_SEARCH, fill="#B5B0AA", anchor="w")
        # Magnifier icon
        ic_cx, ic_cy = 1125 + dx, (s_y1 + s_y2) // 2
        ic_r = 9
        cv.create_oval(ic_cx - ic_r, ic_cy - ic_r, ic_cx + ic_r, ic_cy + ic_r,
                       outline=self.C_TEXT, width=2)
        cv.create_line(ic_cx + int(ic_r * 0.72), ic_cy + int(ic_r * 0.72),
                       ic_cx + int(ic_r * 1.65), ic_cy + int(ic_r * 1.65),
                       fill=self.C_TEXT, width=2)

        # ── TABLE CARD ──
        tbl_y1 = 318 + y
        tbl_y2 = 900 + y
        _round_rect(cv, 300 + dx, tbl_y1, 1150 + dx, tbl_y2, radius=25, fill=self.C_WHITE)

        # Column headers
        hdr_y = tbl_y1 + 35
        cols    = ["Customer", "Phone", "Pets", "Points", "Membership"]
        col_xs  = [330 + dx, 460 + dx, 570 + dx, 680 + dx, 790 + dx]

        for col, cx in zip(cols, col_xs):
            cv.create_text(cx, hdr_y, text=col, font=self.F_TABLE_HEAD,
                           fill=self.C_TEXT, anchor="w")

        # Divider under header
        cv.create_line(325 + dx, hdr_y + 22, 1130 + dx, hdr_y + 22,
                       fill=self.C_DIVIDER, width=1)

        # Table data
        table_data = [
            {
                "customer": "Nguyễn Lan",
                "phone":    "012345678",
                "pet_name": "Milo",
                "pet_emoji":"🐶",
                "pet_chip": self.C_DOG_CHIP,
                "points":   "1.230P",
                "membership":"VIP",
            },
            {
                "customer": "Nguyễn Lan",
                "phone":    "012345678",
                "pet_name": "Moa",
                "pet_emoji":"🐱",
                "pet_chip": self.C_CAT_CHIP,
                "points":   "1.230P",
                "membership":"VIP",
            },
        ]

        row_h = 58
        for ri, row in enumerate(table_data):
            ry  = hdr_y + 30 + ri * row_h
            rcy = ry + row_h // 2

            cv.create_text(col_xs[0], rcy, text=row["customer"],
                           font=self.F_TABLE_BODY, fill=self.C_TEXT, anchor="w")
            cv.create_text(col_xs[1], rcy, text=row["phone"],
                           font=self.F_TABLE_BODY, fill=self.C_TEXT, anchor="w")

            # Pet chip centred in the Pets column
            chip_cx = col_xs[2] + 42
            self._draw_pet_chip(cv, chip_cx, rcy,
                                row["pet_emoji"], row["pet_name"], row["pet_chip"])

            cv.create_text(col_xs[3], rcy, text=row["points"],
                           font=self.F_TABLE_BODY, fill=self.C_TEXT, anchor="w")
            cv.create_text(col_xs[4], rcy, text=row["membership"],
                           font=self.F_TABLE_BODY, fill=self.C_TEXT, anchor="w")

            # Profile button
            pbw, pbh = 90, 30
            pbx = 1130 + dx - pbw
            pby = rcy - pbh // 2
            _round_rect(cv, pbx, pby, pbx + pbw, pby + pbh,
                        radius=pbh // 2, fill=self.C_PROFILE_BG)
            cv.create_text(pbx + pbw // 2, rcy,
                           text="Profile", font=self.F_PROFILE,
                           fill=self.C_WHITE)

            # Row divider (not after last)
            if ri < len(table_data) - 1:
                cv.create_line(325 + dx, ry + row_h - 1, 1130 + dx, ry + row_h - 1,
                               fill=self.C_DIVIDER, width=1)


if __name__ == "__main__":
    app = CustomerPetDashboard()
    app.mainloop()