import tkinter as tk
from PIL import Image, ImageTk, ImageDraw
import os
import sys
from datetime import datetime

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
        title_y = 95 + y_off
        cv.create_text(L_PAD, title_y + 15, text="DUE TODAY\n(Check-outs)", font=self.F_TITLE_LARGE, fill=self.C_TEXT, anchor="nw")
        cv.create_text(L_PAD, title_y + 90, text="Tuesday, 06/05/2025", font=self.F_DATE, fill=self.C_TEXT, anchor="nw")

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
        card_y2 = 625 + y_off
        _round_rect(cv, L_PAD, card_y1, R_PAD, card_y2, radius=25, fill=self.C_WHITE, outline="")

        # Title
        cv.create_text(L_PAD + 25, card_y1 + 28, text="Booking #1041", font=self.F_TITLE_MED, fill=self.C_TEXT, anchor="w")
        
        # Tag Milo
        _round_rect(cv, L_PAD + 190, card_y1 + 16, L_PAD + 265, card_y1 + 41, radius=12, fill=self.C_UNPAID_BG)
        cv.create_text(L_PAD + 227, card_y1 + 28, text="🐶 Milo", font=self.F_BOLD, fill=self.C_TEXT)

        # Tag Unpaid
        _round_rect(cv, R_PAD - 110, card_y1 + 16, R_PAD - 25, card_y1 + 41, radius=12, fill=self.C_UNPAID_BG)
        cv.create_text(R_PAD - 67, card_y1 + 28, text="Unpaid", font=self.F_BOLD, fill=self.C_TEXT)

        # Subtitle
        cv.create_text(L_PAD + 25, card_y1 + 58, text="Trần Minh  -  room_id  -  03/05 ➔ 06/05", font=self.F_REGULAR, fill=self.C_TEXT_LIGHT, anchor="w")
        cv.create_line(L_PAD + 25, card_y1 + 78, R_PAD - 25, card_y1 + 78, fill=self.C_LINE)

        # Items list
        y_item = card_y1 + 105
        cv.create_text(L_PAD + 25, y_item, text="Room ( type_name × 3 nights )", font=self.F_REGULAR, fill=self.C_TEXT, anchor="w")
        cv.create_text(R_PAD - 25, y_item, text="900,000đ", font=self.F_PRICE, fill=self.C_TEXT, anchor="e")

        y_item += 35
        # Service Tags under room
        _round_rect(cv, L_PAD + 25, y_item - 12, L_PAD + 125, y_item + 12, radius=12, fill=self.C_TAG_GREEN)
        cv.create_text(L_PAD + 75, y_item, text="Grooming x2", font=self.F_BOLD, fill=self.C_TEXT)

        _round_rect(cv, L_PAD + 135, y_item - 12, L_PAD + 235, y_item + 12, radius=12, fill=self.C_TAG_PINK)
        cv.create_text(L_PAD + 185, y_item, text="Daycare x2", font=self.F_BOLD, fill=self.C_TEXT)
        cv.create_text(R_PAD - 25, y_item, text="550,000đ", font=self.F_PRICE, fill=self.C_TEXT, anchor="e")

        y_item += 35
        cv.create_text(L_PAD + 25, y_item, text="Transport (District 7)", font=self.F_REGULAR, fill=self.C_TEXT, anchor="w")
        cv.create_text(R_PAD - 25, y_item, text="200,000đ", font=self.F_PRICE, fill=self.C_TEXT, anchor="e")

        y_item += 35
        cv.create_text(L_PAD + 25, y_item, text="VIP Discount (10%)", font=self.F_REGULAR, fill=self.C_TEXT, anchor="w")
        cv.create_text(R_PAD - 25, y_item, text="-190,000đ", font=self.F_PRICE, fill=self.C_TEXT, anchor="e")

        # Divider
        y_line = y_item + 25
        cv.create_line(L_PAD + 25, y_line, R_PAD - 25, y_line, fill=self.C_LINE)

        # Total amount
        y_total = y_line + 30
        cv.create_text(L_PAD + 25, y_total, text="Total amount", font=self.F_TITLE_MED, fill=self.C_TEXT, anchor="w")
        cv.create_text(R_PAD - 25, y_total, text="2,300,000đ", font=("Arial Rounded MT Bold", max(15, int(21*self._s)), "bold"), fill=self.C_TEXT, anchor="e")

        cv.create_text(R_PAD - 25, y_total + 25, text="Add 1,130 pts to account", font=self.F_REGULAR, fill=self.C_TEXT_LIGHT, anchor="e")

        # Payment options & Done
        y_btn = y_total + 30
        # Cash Outline
        _round_rect_outline(cv, L_PAD + 25, y_btn, L_PAD + 115, y_btn + 34, radius=15, color="#A89F95", width=1)
        cv.create_text(L_PAD + 70, y_btn + 17, text="Cash", font=self.F_REGULAR, fill=self.C_TEXT)

        # Bank Transfer Outline
        _round_rect_outline(cv, L_PAD + 130, y_btn, L_PAD + 280, y_btn + 34, radius=15, color="#A89F95", width=1)
        cv.create_text(L_PAD + 205, y_btn + 17, text="Bank Transfer", font=self.F_REGULAR, fill=self.C_TEXT)

        # Card Solid active
        _round_rect(cv, L_PAD + 295, y_btn, L_PAD + 385, y_btn + 34, radius=15, fill=self.C_ACTIVE)
        cv.create_text(L_PAD + 340, y_btn + 17, text="Card", font=self.F_REGULAR, fill=self.C_TEXT)

        # Date at footer
        cv.create_text(L_PAD + 25, y_btn + 58, text="06/05/2025", font=self.F_REGULAR, fill=self.C_TEXT_LIGHT, anchor="w")

        # Nút Done
        _round_rect(cv, R_PAD - 125, y_btn + 22, R_PAD - 25, y_btn + 62, radius=20, fill=self.C_BTN_GREEN)
        cv.create_text(R_PAD - 75, y_btn + 42, text="Done", font=self.F_BOLD, fill=self.C_WHITE)

        # -------------------------------------------------
        # 5. BOOKING HISTORY
        # -------------------------------------------------
        hist_y = card_y2 + 40
        cv.create_text(L_PAD, hist_y, text="Booking History", font=self.F_TITLE_MED, fill=self.C_TEXT, anchor="w")

        tbl_y1 = hist_y + 20
        tbl_y2 = tbl_y1 + 185
        _round_rect(cv, L_PAD, tbl_y1, R_PAD, tbl_y2, radius=25, fill=self.C_WHITE, outline="")

        # Table Header
        h_y = tbl_y1 + 25
        cols_x = [L_PAD + 30, L_PAD + 80, L_PAD + 280, L_PAD + 420, L_PAD + 560, L_PAD + 700]
        headers = ["#", "Customer / Pet", "Date", "Amount", "Method", "Status"]
        for x_pos, text in zip(cols_x, headers):
            cv.create_text(x_pos, h_y, text=text, font=self.F_BOLD, fill=self.C_TEXT, anchor="w")
        
        cv.create_line(L_PAD + 20, h_y + 15, R_PAD - 20, h_y + 15, fill=self.C_LINE)

        # Rows
        row_y = h_y + 40
        for i in range(2):
            cv.create_text(cols_x[0], row_y, text="1042", font=self.F_REGULAR, fill=self.C_TEXT, anchor="w")
            cv.create_text(cols_x[1], row_y, text="Nguyễn Lan · Milo", font=self.F_REGULAR, fill=self.C_TEXT, anchor="w")
            cv.create_text(cols_x[2], row_y, text="04/05/2025", font=self.F_REGULAR, fill=self.C_TEXT, anchor="w")
            cv.create_text(cols_x[3], row_y, text="1,130,000đ", font=self.F_BOLD, fill=self.C_TEXT, anchor="w")
            cv.create_text(cols_x[4], row_y, text="Transfer", font=self.F_REGULAR, fill=self.C_TEXT, anchor="w")
            
            # Tag Paid
            _round_rect(cv, cols_x[5]-10, row_y - 12, cols_x[5] + 80, row_y + 12, radius=12, fill=self.C_PAID_BG)
            cv.create_text(cols_x[5] + 35, row_y, text="Paid", font=self.F_BOLD, fill=self.C_TEXT)

            if i == 0:
                cv.create_line(L_PAD + 20, row_y + 20, R_PAD - 20, row_y + 20, fill=self.C_LINE)
            row_y += 45

if __name__ == "__main__":
    app = BillingDashboard()
    app.mainloop()