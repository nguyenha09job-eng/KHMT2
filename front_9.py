import tkinter as tk
from PIL import Image, ImageTk, ImageDraw
import os
import sys
from datetime import datetime

def _round_rect(cv, x1, y1, x2, y2, radius=25, **kwargs):
    """Hàm vẽ hình chữ nhật bo góc chuẩn trên Canvas"""
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

class BillingDashboard(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("Pet&Bed - Billing")
        self.attributes("-fullscreen", True)
        self.configure(bg="#D5E4A7") # Màu nền xanh lục nhạt chuẩn theo ảnh
        self.update_idletasks()

        self.W = self.winfo_width()
        self.H = self.winfo_height()

        self.BASE_W = 1200.0
        self.BASE_H = 950.0  # Tăng chiều cao cơ sở để cuộn xem hết lịch sử
        self._s = self.W / self.BASE_W
        s = self._s

        # --- BẢNG MÀU CHUẨN DESIGN ---
        self.C_BG = "#D5E4A7"
        self.C_SIDEBAR = "#FFFFFF"
        self.C_TEXT = "#4A3525"
        self.C_TEXT_LIGHT = "#7A685F"
        self.C_WHITE = "#FFFFFF"
        self.C_ACTIVE_MENU = "#C2DC6A" # Màu xanh neon nhẹ nút Billing active
        
        self.C_CARD_BG = "#FFFFFF"
        self.C_LINE = "#E8E8E8"
        
        # Tags & Status Colors
        self.C_TAG_MILO = "#F9E1B7"    # Cam nhạt tag Milo
        self.C_TAG_UNPAID = "#F9D5E2"  # Hồng nhạt Unpaid
        self.C_TAG_GROOM = "#E0F2CB"   # Xanh lá mạ nhạt
        self.C_TAG_DAYCARE = "#F9D5E2" # Hồng nhạt daycare
        self.C_BTN_DONE = "#6CB059"    # Xanh lá cây nút Done

        # --- FONTS RESPONSIVE ---
        self.F_LOGO = ("Arial Rounded MT Bold", max(16, int(36 * s)), "bold")
        self.F_NAV = ("Baghdad", max(10, int(16 * s)))
        self.F_TITLE = ("Arial Rounded MT Bold", max(20, int(32 * s)), "bold")
        self.F_SUBTITLE = ("Baghdad", max(10, int(15 * s)))
        self.F_CARD_HDR = ("Arial Rounded MT Bold", max(12, int(20 * s)), "bold")
        self.F_BODY = ("Baghdad", max(10, int(16 * s)))
        self.F_BODY_BOLD = ("Baghdad", max(10, int(16 * s)), "bold")
        self.F_CHIP = ("Baghdad", max(9, int(13 * s)), "bold")

        self.images = []

        # -- Main Layout Container --
        main = tk.Frame(self, bg=self.C_BG)
        main.pack(fill=tk.BOTH, expand=True)

        self.BASE_SIDE_W = 240
        side_w = int(self.BASE_SIDE_W * s)

        # Sidebar Left
        self.side_frame = tk.Frame(main, width=side_w, bg=self.C_BG)
        self.side_frame.pack(side=tk.LEFT, fill=tk.Y)
        self.side_frame.pack_propagate(False)

        self.sidebar_canvas = tk.Canvas(self.side_frame, width=side_w, height=self.H, bg=self.C_BG, highlightthickness=0)
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

        # Render UI components
        self.draw_sidebar()
        self.draw_billing_content()

        # Áp dụng tỉ lệ scale tự động
        self.sidebar_canvas.scale("all", 0, 0, s, s)
        self.canvas.scale("all", 0, 0, s, s)

        # Cấu hình vùng cuộn chuột (Scrollregion)
        self.canvas.update_idletasks()
        bbox = self.canvas.bbox("all")
        if bbox:
            self.canvas.configure(scrollregion=(bbox[0], 0, bbox[2], bbox[3] + 60 * s))

        # Khóa sự kiện cuộn chuột
        def _on_mw(event):
            delta = event.delta
            if sys.platform == "darwin":
                self.canvas.yview_scroll(int(-delta), "units")
            else:
                self.canvas.yview_scroll(int(-delta / 120), "units")

        self.canvas.bind("<MouseWheel>", _on_mw, add="+")
        self.bind("<Escape>", lambda e: self.destroy())

    def draw_sidebar(self):
        cv = self.sidebar_canvas
        # Vẽ dải nền trắng của Sidebar bo tròn cạnh phải sát lề
        _round_rect(cv, -50, -50, 225, self.H/self._s + 50, radius=40, fill=self.C_SIDEBAR)

        # App Logo
        cv.create_text(115, 65, text="Pet&Bed", font=self.F_LOGO, fill=self.C_TEXT)

        # Menu items list
        nav_items = ["Dashboard", "Care View", "Booking", "Rooms", "Customer & Pet", "Billing", "Staff", "Report"]
        y = 115
        item_h = 36
        pad_x = 25
        right_x = 205
        gap = 10

        for i, item in enumerate(nav_items):
            if i == 5:  # Menu "Billing" đang active
                _round_rect(cv, pad_x, y, right_x, y + item_h, radius=18, fill=self.C_ACTIVE_MENU)
                cv.create_text(pad_x + 20, y + 18, text=item, font=self.F_NAV, fill=self.C_TEXT, anchor="w")
            else: # Các menu thông thường có viền mảnh nhẹ
                _round_rect(cv, pad_x, y, right_x, y + item_h, radius=18, fill=self.C_WHITE)
                cv.create_rectangle(pad_x + 10, y, right_x - 10, y + item_h, fill="", outline=self.C_LINE)
                cv.create_text(pad_x + 20, y + 18, text=item, font=self.F_NAV, fill=self.C_TEXT_LIGHT, anchor="w")
            y += item_h + gap

        # Icon minh hoạ thú cưng ở góc dưới sidebar
        cv.create_text(115, 730, text="🐾", font=("Arial", 45))

        # Nút Log out dạng hình oval màu nâu trầm đặc trưng
        _round_rect(cv, 25, 790, 205, 832, radius=21, fill=self.C_TEXT)
        cv.create_text(115, 811, text="Log out", font=self.F_NAV, fill=self.C_WHITE)

    def draw_chip_pill(self, cv, x, y, text, bg_color):
        """Hàm phụ vẽ các nhãn/tag trạng thái tự động co dãn theo chữ"""
        temp_txt = cv.create_text(0, 0, text=text, font=self.F_CHIP)
        bbox = cv.bbox(temp_txt)
        cv.delete(temp_txt)
        tw = bbox[2] - bbox[0]
        th = bbox[3] - bbox[1]
        px, py = 12, 4
        ex, ey = x + tw + px*2, y + th + py*2
        _round_rect(cv, x, y, ex, ey, radius=(ey-y)//2, fill=bg_color)
        cv.create_text(x + px + tw/2, y + py + th/2, text=text, font=self.F_CHIP, fill=self.C_TEXT)
        return ex

    def draw_billing_content(self):
        cv = self.canvas
        start_x = 255
        content_w = 880
        end_x = start_x + content_w

        # 1. TAG TIÊU ĐỀ PHÍA TRÊN CÙNG
        _round_rect(cv, start_x, 25, start_x + 100, 55, radius=15, fill=self.C_WHITE)
        cv.create_text(start_x + 50, 40, text="Billing", font=self.F_SUBTITLE, fill=self.C_TEXT)

        # 2. KHU VỰC TIÊU ĐỀ CHÍNH (DUE TODAY)
        cv.create_text(start_x, 105, text="DUE TODAY\n(Check-outs)", font=self.F_TITLE, fill=self.C_TEXT, anchor="nw")
        cv.create_text(start_x, 185, text="Tuesday, 06/05/2025", font=self.F_SUBTITLE, fill=self.C_TEXT_LIGHT, anchor="nw")

        # Banner ảnh Cún bên phải tiêu đề (vẽ giả lập bằng khung bo tròn phối màu mượt mà nếu thiếu file ảnh)
        _round_rect(cv, start_x + 400, 85, end_x, 215, radius=24, fill="#B0C4DE")
        cv.create_text(start_x + 640, 150, text="🐶 [Banner Dog Image]", font=self.F_BODY, fill=self.C_WHITE)

        # 3. THANH TÌM KIẾM (SEARCH BAR)
        search_y = 235
        _round_rect(cv, start_x, search_y, end_x, search_y + 45, radius=22, fill=self.C_WHITE)
        cv.create_text(start_x + 20, search_y + 22, text="Search by name, phone number, or pet name", font=self.F_BODY, fill="#A5A5A5", anchor="w")
        cv.create_text(end_x - 30, search_y + 22, text="🔍", font=("Arial", 16), fill=self.C_TEXT)

        # 4. THÔNG TIN HOÁ ĐƠN HIỆN TẠI (BOOKING CARD)
        card_y = 300
        _round_rect(cv, start_x, card_y, end_x, card_y + 320, radius=24, fill=self.C_CARD_BG)
        
        # Header dòng 1 trong Card
        cv.create_text(start_x + 25, card_y + 28, text="Booking #1041", font=self.F_CARD_HDR, fill=self.C_TEXT, anchor="w")
        rx = self.draw_chip_pill(cv, start_x + 185, card_y + 16, "🐶 Milo", self.C_TAG_MILO)
        self.draw_chip_pill(cv, end_x - 85, card_y + 16, "Unpaid", self.C_TAG_UNPAID)

        # Header dòng 2 trong Card
        cv.create_text(start_x + 25, card_y + 58, text="Trần Minh  -  room_id  -  03/05 ➔ 06/05", font=self.F_BODY, fill=self.C_TEXT_LIGHT, anchor="w")
        cv.create_line(start_x + 25, card_y + 80, end_x - 25, card_y + 80, fill=self.C_LINE)

        # Chi tiết các dịch vụ đã dùng
        item_y = card_y + 105
        # Item 1
        cv.create_text(start_x + 25, item_y, text="Room ( type_name × 3 nights )", font=self.F_BODY, fill=self.C_TEXT, anchor="w")
        cv.create_text(end_x - 25, item_y, text="900,000đ", font=self.F_BODY, fill=self.C_TEXT, anchor="e")
        # Sub-chips dưới Room item
        cx = self.draw_chip_pill(cv, start_x + 25, item_y + 15, "Grooming x2", self.C_TAG_GROOM)
        self.draw_chip_pill(cv, cx + 10, item_y + 15, "Daycare x2", self.C_TAG_DAYCARE)

        # Item 2
        item_y += 50
        cv.create_text(start_x + 25, item_y, text="Transport (District 7)", font=self.F_BODY, fill=self.C_TEXT, anchor="w")
        cv.create_text(end_x - 25, item_y, text="200,000đ", font=self.F_BODY, fill=self.C_TEXT, anchor="e")

        # Item 3
        item_y += 30
        cv.create_text(start_x + 25, item_y, text="VIP Discount (10%)", font=self.F_BODY, fill=self.C_TEXT, anchor="w")
        cv.create_text(end_x - 25, item_y, text="-190,000đ", font=self.F_BODY, fill=self.C_TEXT, anchor="e")

        # Đường kẻ chia phần tổng tiền
        cv.create_line(start_x + 25, item_y + 25, end_x - 25, item_y + 25, fill=self.C_LINE)

        # Tổng cộng tiền mặt cần trả
        total_y = item_y + 50
        cv.create_text(start_x + 25, total_y, text="Total amount", font=self.F_BODY_BOLD, fill=self.C_TEXT, anchor="w")
        cv.create_text(end_x - 25, total_y, text="2,300,000đ", font=self.F_CARD_HDR, fill=self.C_TEXT, anchor="e")

        # Phương thức thanh toán (Nút bấm lựa chọn)
        pay_y = total_y + 25
        bx = start_x + 25
        for method in ["Cash", "Bank Transfer", "Card"]:
            is_active = (method == "Card")
            bg = self.C_ACTIVE_MENU if is_active else self.C_WHITE
            bw = 120 if method == "Bank Transfer" else 75
            _round_rect(cv, bx, pay_y, bx + bw, pay_y + 28, radius=12, fill=bg)
            if not is_active:
                cv.create_rectangle(bx + 5, pay_y, bx + bw - 5, pay_y + 28, fill="", outline=self.C_LINE)
            cv.create_text(bx + bw/2, pay_y + 14, text=method, font=self.F_CHIP, fill=self.C_TEXT)
            bx += bw + 10

        # Điểm tích lũy đi kèm
        cv.create_text(end_x - 25, pay_y + 14, text="Add 1,130 pts to account", font=self.F_BODY, fill=self.C_TEXT_LIGHT, anchor="e")

        # Footer của Card: Ngày tháng & nút hoàn thành
        foot_y = card_y + 285
        cv.create_text(start_x + 25, foot_y, text="06/05/2025", font=self.F_BODY, fill=self.C_TEXT_LIGHT, anchor="w")
        _round_rect(cv, end_x - 115, foot_y - 15, end_x - 25, foot_y + 18, radius=15, fill=self.C_BTN_DONE)
        cv.create_text(end_x - 70, foot_y, text="Done", font=self.F_CHIP, fill=self.C_WHITE)


        # 5. KHU VỰC LỊCH SỬ GIAO DỊCH (BOOKING HISTORY)
        hist_y = card_y + 350
        cv.create_text(start_x, hist_y, text="Booking History", font=self.F_CARD_HDR, fill=self.C_TEXT, anchor="w")

        # Bảng danh sách hoá đơn cũ
        tbl_y = hist_y + 20
        _round_rect(cv, start_x, tbl_y, end_x, tbl_y + 220, radius=24, fill=self.C_WHITE)

        # Cột tiêu đề Table
        headers = [("#", 45), ("Customer / Pet", 150), ("Date", 420), ("Amount", 560), ("Method", 700), ("Status", 820)]
        hdr_y = tbl_y + 25
        for title, x_offset in headers:
            cv.create_text(start_x + x_offset, hdr_y, text=title, font=self.F_BODY_BOLD, fill=self.C_TEXT, anchor="w")

        cv.create_line(start_x + 25, hdr_y + 15, end_x - 25, hdr_y + 15, fill=self.C_LINE)

        # Render các dòng dữ liệu mẫu trong lịch sử giống hệt hình
        row_y = hdr_y + 35
        for i in range(2):
            cv.create_text(start_x + 45, row_y, text="1042", font=self.F_BODY, fill=self.C_TEXT_LIGHT, anchor="w")
            cv.create_text(start_x + 150, row_y, text="Nguyễn Lan  ·  Milo", font=self.F_BODY, fill=self.C_TEXT, anchor="w")
            cv.create_text(start_x + 420, row_y, text="04/05/2025", font=self.F_BODY, fill=self.C_TEXT, anchor="w")
            cv.create_text(start_x + 560, row_y, text="1,130,000đ", font=self.F_BODY_BOLD, fill=self.C_TEXT, anchor="w")
            cv.create_text(start_x + 700, row_y, text="Transfer", font=self.F_BODY, fill=self.C_TEXT, anchor="w")
            
            # Trạng thái "Paid" dạng chip viên thuốc màu xanh
            self.draw_chip_pill(cv, start_x + 820, row_y - 11, "  Paid  ", self.C_TAG_GROOM)

            # Dòng phân cách giữa các hàng
            cv.create_line(start_x + 25, row_y + 20, end_x - 25, row_y + 20, fill=self.C_LINE)
            row_y += 45

if __name__ == "__main__":
    app = BillingDashboard()
    app.mainloop()