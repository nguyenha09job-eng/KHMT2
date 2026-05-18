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

class PetPopup(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Pet Details Pop-up")
        width = 600
        height = 750
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x = (screen_width - width) // 2
        y = (screen_height - height) // 2
        self.geometry(f"{width}x{height}+{x}+{y}")
        self.configure(bg="#E5E5E5") # Nền xám mờ giả lập overlay
        
        # Colors (Lấy mã màu chuẩn từ ảnh)
        self.C_POPUP_BG   = "#FFFFFF"
        self.C_TEXT_DARK  = "#4A3525"
        self.C_TEXT_LIGHT = "#7A685F"
        
        self.C_CHIP_BREED = "#F9E1B7" # Cam nhạt
        self.C_CHIP_WEIGHT= "#F9D5E2" # Hồng nhạt
        self.C_CHIP_AGE   = "#BDE2DF" # Xanh lơ
        self.C_CHIP_GENDER= "#E0F2CB" # Xanh lá nhạt

        # Fonts
        self.F_TITLE   = ("Arial Rounded MT Bold", 22, "bold")
        self.F_SUB     = ("Baghdad", 14)
        self.F_CHIP    = ("Baghdad", 12, "bold")
        self.F_HEADER  = ("Arial Rounded MT Bold", 16, "bold")
        self.F_BODY    = ("Baghdad", 16)
        self.F_LINK    = ("Baghdad", 16, "underline")

        # Canvas cho Pop-up
        self.cv = tk.Canvas(self, width=520, height=680, bg="#E5E5E5", highlightthickness=0)
        self.cv.place(relx=0.5, rely=0.5, anchor="center")
        
        self.images = [] # Tránh garbage collection
        
        self.draw_popup()

    def draw_popup(self):
        cv = self.cv
        
        # 1. Vẽ khung Pop-up bo tròn nền trắng
        _round_rect(cv, 10, 10, 510, 670, radius=25, fill=self.C_POPUP_BG)
        
        # 2. Nút Tắt (Close 'X')
        close_x, close_y = 480, 40
        cv.create_line(close_x-7, close_y-7, close_x+7, close_y+7, width=3, fill=self.C_TEXT_DARK, capstyle="round")
        cv.create_line(close_x-7, close_y+7, close_x+7, close_y-7, width=3, fill=self.C_TEXT_DARK, capstyle="round")
        
        # Để nút X có thể click đóng (Giả lập vùng click)
        close_btn = cv.create_rectangle(close_x-15, close_y-15, close_x+15, close_y+15, fill="", outline="")
        cv.tag_bind(close_btn, "<Button-1>", lambda e: self.destroy())

        # 3. Avatar Chó (Vẽ hình tròn thay thế nếu không có file ảnh thật)
        ava_x, ava_y, ava_r = 40, 30, 30
        cv.create_oval(ava_x, ava_y, ava_x + ava_r*2, ava_y + ava_r*2, fill="#D2B48C", outline="")
        cv.create_text(ava_x + ava_r, ava_y + ava_r, text="🐶", font=("Arial", 25))
        
        # 4. Title & Subtitle
        cv.create_text(110, 45, text="Milo - Nguyễn Lan's pet", font=self.F_TITLE, fill=self.C_TEXT_DARK, anchor="w")
        cv.create_text(110, 75, text="pet_id", font=self.F_SUB, fill=self.C_TEXT_LIGHT, anchor="w")

        # 5. Các Tag (Chips)
        self.draw_chip(cv, 40, 110, "breed", self.C_CHIP_BREED)
        self.draw_chip(cv, 110, 110, "weight", self.C_CHIP_WEIGHT)
        self.draw_chip(cv, 185, 110, "age", self.C_CHIP_AGE)
        self.draw_chip(cv, 240, 110, "gender", self.C_CHIP_GENDER)

        # ─── THÔNG TIN CHI TIẾT ───
        start_x = 40
        y = 155
        spacing = 28
        section_gap = 16

        # Current room
        cv.create_text(start_x, y, text="Current room", font=self.F_HEADER, fill=self.C_TEXT_DARK, anchor="w")
        y += spacing
        cv.create_text(start_x, y, text="R - 03", font=self.F_BODY, fill=self.C_TEXT_DARK, anchor="w")
        cv.create_text(start_x + 90, y, text="Link cam", font=self.F_LINK, fill=self.C_TEXT_DARK, anchor="w")
        y += spacing + section_gap

        # Owner Information
        cv.create_text(start_x, y, text="Owner Information", font=self.F_HEADER, fill=self.C_TEXT_DARK, anchor="w")
        y += spacing
        cv.create_text(start_x, y, text="Owner", font=self.F_BODY, fill=self.C_TEXT_DARK, anchor="w")
        cv.create_text(start_x + 100, y, text="Nguyễn Lan", font=self.F_BODY, fill=self.C_TEXT_DARK, anchor="w")
        y += spacing
        cv.create_text(start_x, y, text="Phone", font=self.F_BODY, fill=self.C_TEXT_DARK, anchor="w")
        cv.create_text(start_x + 100, y, text="0901234567", font=self.F_BODY, fill=self.C_TEXT_DARK, anchor="w")
        y += spacing + section_gap

        # Health
        cv.create_text(start_x, y, text="Health", font=self.F_HEADER, fill=self.C_TEXT_DARK, anchor="w")
        y += spacing
        cv.create_text(start_x, y, text="Sterilization", font=self.F_BODY, fill=self.C_TEXT_DARK, anchor="w")
        cv.create_text(start_x + 200, y, text="Yes", font=self.F_BODY, fill=self.C_TEXT_DARK, anchor="w")
        y += spacing
        cv.create_text(start_x, y, text="Vaccination", font=self.F_BODY, fill=self.C_TEXT_DARK, anchor="w")
        cv.create_text(start_x + 200, y, text="Yes", font=self.F_BODY, fill=self.C_TEXT_DARK, anchor="w")
        y += spacing + section_gap

        # Health condition
        cv.create_text(start_x, y, text="Health condition", font=self.F_HEADER, fill=self.C_TEXT_DARK, anchor="w")
        y += spacing
        cv.create_text(start_x, y, text="Healthy", font=self.F_BODY, fill=self.C_TEXT_DARK, anchor="w")
        y += spacing + section_gap

        # Behaviour note
        cv.create_text(start_x, y, text="Behaviour note", font=self.F_HEADER, fill=self.C_TEXT_DARK, anchor="w")
        y += spacing
        cv.create_text(start_x, y, text="Bites strangers – warn staff before entering room", font=self.F_BODY, fill=self.C_TEXT_DARK, anchor="w")
        y += spacing + section_gap

        # Special requirement
        cv.create_text(start_x, y, text="Special requirement", font=self.F_HEADER, fill=self.C_TEXT_DARK, anchor="w")
        y += spacing
        cv.create_text(start_x, y, text="No fish in food", font=self.F_BODY, fill=self.C_TEXT_DARK, anchor="w")

    def draw_chip(self, cv, x, y, text, bg_color):
        """Hàm phụ trợ vẽ các tag màu (pill chips)"""
        font = self.F_CHIP
        padding_x = 12
        padding_y = 6
        text_w = len(text) * 8.5  # Ước lượng chiều dài chữ phù hợp với font Baghdad mới
        text_h = 16
        
        # Vẽ background bo tròn của chip
        _round_rect(cv, x, y, x + text_w + padding_x*2, y + text_h + padding_y*2, radius=14, fill=bg_color, outline="")
        # Vẽ chữ ở giữa chip
        cv.create_text(x + padding_x + text_w/2, y + padding_y + text_h/2, text=text, font=font, fill=self.C_TEXT_DARK)

if __name__ == "__main__":
    app = PetPopup()
    app.mainloop()