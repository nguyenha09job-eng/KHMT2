import tkinter as tk
from PIL import Image, ImageTk, ImageDraw
import os
import sys
from datetime import datetime
from backend_1 import DashboardBackend

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
        cv = self.canvas
        dx = -self.BASE_SIDE_W
        y_off = self.Y_OFF
        row_h = 35

        # =========================
        # ACTIVE BOOKINGS (y: 380 → 670)
        # =========================
        cv.create_text(315+dx, 380+y_off, text="Active Bookings", font=self.F_SECTION, fill=self.C_TEXT, anchor="w")
        _round_rect(cv, 300+dx, 400+y_off, 1150+dx, 620+y_off, radius=30, fill=self.C_WHITE, outline="")

        cols1 = ["Pet", "Owner", "Check in", "Check out", "Status", "Room"]
        xs1 = [365+dx, 475+dx, 605+dx, 745+dx, 880+dx, 1005+dx]
        for i, col in enumerate(cols1):
            cv.create_text(xs1[i], 425+y_off, text=col, font=self.F_TABLE_HEAD, fill=self.C_TEXT, anchor="w")
        cv.create_line(320+dx, 450+y_off, 1130+dx, 450+y_off, fill=self.C_TEXT_LIGHT)

        data1 = [
            (b["pet"], b["owner"], b["check_in"], b["check_out"], b["status"], b["room"])
            for b in self.data["active_bookings"]
        ]
        data1 = data1[:5] 
        y = 475 + y_off
        for ri, row in enumerate(data1):
            for i, val in enumerate(row):
                cv.create_text(xs1[i], y, text=val, font=self.F_TABLE_ROW, fill=self.C_TEXT, anchor="w")
            if ri < len(data1) - 1:
                cv.create_line(320+dx, y+17, 1130+dx, y+17, fill=self.C_TEXT_LIGHT)
            y += row_h

        # =========================
        # TODAY'S SERVICES (y: 695 → 955)
        # =========================
        # =========================
# TODAY'S SERVICES
# =========================
        cv.create_text(315+dx, 645+y_off,
                    text="Today's Services",
                    font=self.F_SECTION,
                    fill=self.C_TEXT,
                    anchor="w")

        _round_rect(cv,
                    300+dx, 665+y_off,
                    1150+dx, 940+y_off,
                    radius=30,
                    fill=self.C_WHITE,
                    outline="")

        cols2 = ["Pet", "Service", "Room", "Status", "Frequency"]
        xs2 = [365+dx, 475+dx, 605+dx, 765+dx, 905+dx]

        for i, col in enumerate(cols2):
            cv.create_text(xs2[i],
                        695+y_off,
                        text=col,
                        font=self.F_TABLE_HEAD,
                        fill=self.C_TEXT,
                        anchor="w")

        cv.create_line(
            320+dx,
            720+y_off,
            1130+dx,
            720+y_off,
            fill=self.C_TEXT_LIGHT
        )

        data2 = [
            (s["pet"], s["service"], s["room"], s["status"], s["frequency"])
            for s in self.data["today_services"]
        ]

        data2 = data2[:5]

        y = 750 + y_off

        for ri, row in enumerate(data2):
            for i, val in enumerate(row):
                cv.create_text(xs2[i],
                            y,
                            text=val,
                            font=self.F_TABLE_ROW,
                            fill=self.C_TEXT,
                            anchor="w")

            if ri < len(data2) - 1:
                cv.create_line(
                    320+dx,
                    y + 17,
                    1130+dx,
                    y + 17,
                    fill=self.C_TEXT_LIGHT
                )

            y += row_h


if __name__ == "__main__":
    app = PetDashboard()
    app.mainloop()
