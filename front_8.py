import tkinter as tk
from PIL import Image, ImageTk, ImageDraw
import os

def _round_rect(cv, x1, y1, x2, y2, radius=25, **kwargs):
    """Hàm vẽ hình chữ nhật bo góc trên Canvas"""
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

class CustomerProfilePopup(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Customer Profile Pop-up")
        
        # Tăng chiều cao để chứa đủ bảng lịch sử phía dưới
        self.W = 600
        self.H = 880 
        
        # Căn giữa màn hình
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x = (screen_width - self.W) // 2
        y = (screen_height - self.H) // 2
        self.geometry(f"{self.W}x{self.H}+{x}+{y}")
        self.configure(bg="#E5E5E5") # Nền xám ngoài cùng
        
        # --- BẢNG MÀU TỪ THIẾT KẾ ---
        self.C_POPUP_TOP_BG = "#FFFFFF" # Trắng tinh ở nửa trên
        self.C_POPUP_BOT_BG = "#FAFAFA" # Hơi xám rất nhẹ ở nửa dưới
        self.C_DIVIDER      = "#E8E8E8" # Màu đường kẻ ngang
        
        self.C_TEXT_DARK  = "#4A3525"
        self.C_TEXT_LIGHT = "#7A685F"
        self.C_TEXT_GREEN = "#6CB059" # Xanh lá cho tiền tệ
        
        self.C_CHIP_PET   = "#F9E1B7" # Cam nhạt (Milo, Moa)
        self.C_CHIP_FLAG  = "#E0F2CB" # Xanh lá nhạt (No flag)
        
        self.C_PROG_BG    = "#EFEFEF" # Thanh xám
        self.C_PROG_FG    = "#F5A623" # Thanh cam

        # --- FONTS ---
        self.F_TITLE   = ("Arial Rounded MT Bold", 20, "bold")
        self.F_SUB     = ("Baghdad", 14)
        self.F_CHIP    = ("Baghdad", 12, "bold")
        self.F_HEADER  = ("Arial Rounded MT Bold", 16, "bold")
        self.F_BODY    = ("Baghdad", 15)
        self.F_TBL_HDR = ("Baghdad", 15)

        self.cv = tk.Canvas(self, width=self.W, height=self.H, bg="#E5E5E5", highlightthickness=0)
        self.cv.pack(fill=tk.BOTH, expand=True)
        
        self.draw_popup()

    def draw_popup(self):
        cv = self.cv
        margin = 10
        
        # 1. VẼ NỀN POP-UP (Nửa trên trắng, nửa dưới hơi xám)
        # Nền tổng (màu nửa dưới)
        _round_rect(cv, margin, margin, self.W - margin, self.H - margin, radius=25, fill=self.C_POPUP_BOT_BG)
        # Nền nửa trên (Màu trắng tinh) tới toạ độ y=500
        _round_rect(cv, margin, margin, self.W - margin, 500, radius=25, fill=self.C_POPUP_TOP_BG)
        # Vá khúc giữa để không bị bo tròn lộ phần nối
        cv.create_rectangle(margin, 460, self.W - margin, 500, fill=self.C_POPUP_TOP_BG, outline="")
        
        # Đường kẻ ranh giới mờ (Đã ẩn theo yêu cầu)
        # cv.create_line(margin, 500, self.W - margin, 500, fill=self.C_DIVIDER, width=1)
        
        # 2. NÚT CLOSE 'X'
        close_x, close_y = self.W - 35, 40
        cv.create_line(close_x-8, close_y-8, close_x+8, close_y+8, width=3, fill=self.C_TEXT_DARK, capstyle="round")
        cv.create_line(close_x-8, close_y+8, close_x+8, close_y-8, width=3, fill=self.C_TEXT_DARK, capstyle="round")
        close_btn = cv.create_rectangle(close_x-15, close_y-15, close_x+15, close_y+15, fill="", outline="")
        cv.tag_bind(close_btn, "<Button-1>", lambda e: self.destroy())

        # 3. HEADER (Tên + Pet Chips)
        cv.create_text(40, 45, text="Customer Profile - Nguyễn Lan", font=self.F_TITLE, fill=self.C_TEXT_DARK, anchor="w")
        cv.create_text(40, 75, text="0901234567 - address", font=self.F_SUB, fill=self.C_TEXT_LIGHT, anchor="w")
        
        nxt_x = 40
        nxt_x = self.draw_chip(cv, nxt_x, 100, "🐶 Milo", self.C_CHIP_PET) + 12
        self.draw_chip(cv, nxt_x, 100, "🐱 Moa", self.C_CHIP_PET)

        # 4. CUSTOMER DETAILS
        start_x = 40
        col2_x = 230
        y = 175
        spacing = 30
        
        cv.create_text(start_x, y, text="Customer Details", font=self.F_HEADER, fill=self.C_TEXT_DARK, anchor="w")
        y += 35
        
        details = [
            ("Full name", "Nguyễn Lan"),
            ("Phone Number", "0901234567"),
            ("Street Address", "45 Nguyễn Thị Minh Khai"),
            ("District", "Quận 3"),
            ("Member Since", "2/08/2023 (634 days ago)")
        ]
        
        for title, val in details:
            cv.create_text(start_x, y, text=title, font=self.F_BODY, fill=self.C_TEXT_DARK, anchor="w")
            cv.create_text(col2_x, y, text=val, font=self.F_BODY, fill=self.C_TEXT_DARK, anchor="w")
            y += spacing
            
        # Dòng Historical flag (có chip)
        cv.create_text(start_x, y, text="Historical flag", font=self.F_BODY, fill=self.C_TEXT_DARK, anchor="w")
        self.draw_chip(cv, col2_x, y - 12, "No", self.C_CHIP_FLAG)

        # 5. MEMBERSHIP & POINT
        y += 45
        cv.create_text(start_x, y, text="Membership & Point", font=self.F_HEADER, fill=self.C_TEXT_DARK, anchor="w")
        y += 35
        
        cv.create_text(start_x, y, text="Current Membership", font=self.F_BODY, fill=self.C_TEXT_DARK, anchor="w")
        cv.create_text(col2_x, y, text="VIP", font=self.F_BODY, fill=self.C_TEXT_DARK, anchor="w")
        y += spacing
        
        cv.create_text(start_x, y, text="Validity Period", font=self.F_BODY, fill=self.C_TEXT_DARK, anchor="w")
        cv.create_text(col2_x, y, text="01/03 → 20/06/2025", font=self.F_BODY, fill=self.C_TEXT_DARK, anchor="w")
        y += spacing
        
        cv.create_text(start_x, y, text="Current Points", font=self.F_BODY, fill=self.C_TEXT_DARK, anchor="w")
        # Vẽ Progress Bar (Thanh cam/xám)
        bar_w = 200
        bar_h = 12
        bar_y = y - 6
        _round_rect(cv, col2_x, bar_y, col2_x + bar_w, bar_y + bar_h, radius=6, fill=self.C_PROG_BG)
        _round_rect(cv, col2_x, bar_y, col2_x + bar_w * 0.9, bar_y + bar_h, radius=6, fill=self.C_PROG_FG)
        cv.create_text(col2_x + bar_w + 15, y, text="900/1000p", font=self.F_BODY, fill=self.C_TEXT_DARK, anchor="w")

        # 6. TOTAL SPEND (Nằm dưới đường line xám)
        y = 530
        cv.create_text(start_x, y, text="Total spend", font=self.F_HEADER, fill=self.C_TEXT_DARK, anchor="w")
        y += 30
        cv.create_text(start_x, y, text="8.400.000đ", font=self.F_HEADER, fill=self.C_TEXT_GREEN, anchor="w")

        # 7. RECENT BOOKING HISTORY
        y += 45
        cv.create_text(start_x, y, text="Recent Booking History", font=self.F_HEADER, fill=self.C_TEXT_DARK, anchor="w")
        
        # Table Headers
        y += 40
        col_x = [45, 120, 240, 460]
        headers = ["#", "Pet", "Dates", "Amount"]
        for i, h in enumerate(headers):
            cv.create_text(col_x[i], y, text=h, font=self.F_TBL_HDR, fill=self.C_TEXT_LIGHT, anchor="w")
        
        # Đường gạch dưới Header table
        y += 20
        cv.create_line(start_x, y, self.W - 30, y, fill=self.C_DIVIDER, width=1)
        
        # Các dòng dữ liệu trong bảng
        y += 25
        row_gap = 55
        for _ in range(3):
            # Cột #
            cv.create_text(col_x[0], y, text="#1042", font=self.F_BODY, fill=self.C_TEXT_DARK, anchor="w")
            # Cột Pet (Chip)
            self.draw_chip(cv, col_x[1], y - 12, "🐱 Moa", self.C_CHIP_PET)
            # Cột Dates (2 dòng)
            cv.create_text(col_x[2], y, text="04/05/2025 →\n07/05/2025", font=self.F_BODY, fill=self.C_TEXT_DARK, anchor="w", justify="left")
            # Cột Amount
            cv.create_text(col_x[3], y, text="875,000đ", font=self.F_HEADER, fill=self.C_TEXT_GREEN, anchor="w")
            
            y += row_gap - 10
            # Gạch dưới dòng (line)
            cv.create_line(start_x, y, self.W - 30, y, fill=self.C_DIVIDER, width=1)
            y += 20

    def draw_chip(self, cv, x, y, text, bg_color):
        """Hàm vẽ pill chip có khả năng tự co giãn theo chiều rộng text"""
        padding_x = 12
        padding_y = 6
        
        # Lấy bounding box để tính độ rộng text
        temp_text = cv.create_text(0, 0, text=text, font=self.F_CHIP)
        bbox = cv.bbox(temp_text)
        cv.delete(temp_text)
        
        text_w = bbox[2] - bbox[0]
        text_h = bbox[3] - bbox[1]
        
        end_x = x + text_w + padding_x * 2
        end_y = y + text_h + padding_y * 2
        
        # Vẽ background
        _round_rect(cv, x, y, end_x, end_y, radius=(end_y - y)//2, fill=bg_color, outline="")
        # Vẽ text
        cv.create_text(x + padding_x + text_w/2, y + padding_y + text_h/2, text=text, font=self.F_CHIP, fill=self.C_TEXT_DARK)
        
        return end_x

if __name__ == "__main__":
    app = CustomerProfilePopup()
    app.mainloop()