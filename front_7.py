import tkinter as tk
from PIL import Image, ImageTk, ImageDraw
import os
import sys
from decimal import Decimal

from app_window import AppWindow
from database import DatabaseConnection

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


class PetDetailsBackend:
    """Data layer for the Pet Details popup."""

    def __init__(self, db=None):
        self.db = db or DatabaseConnection()

    @staticmethod
    def _bit_to_yes_no(value):
        if isinstance(value, (bytes, bytearray)):
            value = value != b"\x00"
        return "Yes" if bool(value) else "No"

    @staticmethod
    def _format_weight(value):
        if value is None:
            return "-"
        if isinstance(value, Decimal):
            value = float(value)
        return f"{value:g}kg"

    @staticmethod
    def _title(value, default="-"):
        if value in (None, ""):
            return default
        return str(value).replace("_", " ").title()

    @staticmethod
    def _note(value, default="None"):
        if value in (None, ""):
            return default
        return str(value)

    def get_pet(self, pet_id=None):
        params = []
        pet_filter = ""
        if pet_id is not None:
            pet_filter = "WHERE p.pet_id = %s"
            params.append(pet_id)

        rows = self.db.fetch_all(
            f"""
            SELECT
                p.pet_id,
                p.pet_name,
                p.species,
                p.breed,
                p.weight,
                p.age,
                p.gender,
                p.sterilized,
                p.vaccinated,
                p.health_condition,
                p.behaviour_note,
                p.special_requirement,
                c.full_name AS owner_name,
                c.phone AS owner_phone,
                active_booking.room_id,
                active_booking.camera_url,
                GROUP_CONCAT(DISTINCT sc.service_type ORDER BY sc.service_type SEPARATOR ', ') AS services
            FROM pets p
            JOIN customers c ON c.customer_id = p.customer_id
            LEFT JOIN (
                SELECT b.pet_id, r.room_id, r.camera_url
                FROM bookings b
                JOIN rooms r ON r.room_id = b.room_id
                JOIN booking_statuses bs ON bs.status_id = b.booking_status_id
                WHERE bs.status_name IN ('booked', 'checked_in')
                  AND b.check_in <= NOW()
                  AND b.check_out >= NOW()
            ) active_booking ON active_booking.pet_id = p.pet_id
            LEFT JOIN services s ON s.pet_id = p.pet_id
            LEFT JOIN service_catalog sc ON sc.service_type_id = s.service_type_id
            {pet_filter}
            GROUP BY
                p.pet_id, p.pet_name, p.species, p.breed, p.weight, p.age,
                p.gender, p.sterilized, p.vaccinated, p.health_condition,
                p.behaviour_note, p.special_requirement, c.full_name,
                c.phone, active_booking.room_id, active_booking.camera_url
            ORDER BY active_booking.room_id IS NULL, p.pet_id
            LIMIT 1
            """,
            tuple(params),
        )
        if not rows:
            return None

        row = rows[0]
        return {
            "pet_id": row.get("pet_id"),
            "name": row.get("pet_name") or "-",
            "species": self._title(row.get("species"), "Pet"),
            "breed": row.get("breed") or "-",
            "weight": self._format_weight(row.get("weight")),
            "age": f"{row.get('age')}y" if row.get("age") is not None else "-",
            "gender": self._title(row.get("gender")),
            "sterilized": self._bit_to_yes_no(row.get("sterilized")),
            "vaccinated": self._bit_to_yes_no(row.get("vaccinated")),
            "health": self._note(row.get("health_condition"), "Healthy"),
            "behaviour": self._note(row.get("behaviour_note")),
            "special": self._note(row.get("special_requirement")),
            "owner": row.get("owner_name") or "-",
            "phone": row.get("owner_phone") or "-",
            "room": f"R-{int(row['room_id']):02d}" if row.get("room_id") is not None else "No active room",
            "camera": row.get("camera_url") or "",
            "services": (row.get("services") or "No services").replace("_", " ").title(),
        }


class PetPopup(AppWindow):
    def __init__(self, pet_id=None):
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
        self.F_HEADER  = ("Arial Rounded MT Bold", 18, "bold")
        self.F_BODY    = ("Baghdad", 18)
        self.F_LINK    = ("Baghdad", 18, "underline")

        # Canvas cho Pop-up
        self.cv = tk.Canvas(self, width=520, height=680, bg="#E5E5E5", highlightthickness=0)
        self.cv.place(relx=0.5, rely=0.5, anchor="center")
        
        self.images = [] # Tránh garbage collection
        self.backend = PetDetailsBackend()
        self.pet = self.load_pet(pet_id)
        
        self.draw_popup()

    def load_pet(self, pet_id=None):
        try:
            return self.backend.get_pet(pet_id)
        except Exception as exc:
            print(f"Khong the tai du lieu Pet Details: {exc}")
            return None

    def draw_popup(self):
        cv = self.cv
        pet = self.pet or {
            "pet_id": "-",
            "name": "No pet",
            "species": "Pet",
            "breed": "-",
            "weight": "-",
            "age": "-",
            "gender": "-",
            "sterilized": "-",
            "vaccinated": "-",
            "health": "No data",
            "behaviour": "No data",
            "special": "No data",
            "owner": "-",
            "phone": "-",
            "room": "No active room",
            "camera": "",
            "services": "No services",
        }
        
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
        avatar_fill = "#F9D5E2" if pet["species"].lower() == "cat" else "#D2B48C"
        cv.create_oval(ava_x, ava_y, ava_x + ava_r*2, ava_y + ava_r*2, fill=avatar_fill, outline="")
        cv.create_text(ava_x + ava_r, ava_y + ava_r, text=pet["species"][:3], font=("Arial", 12, "bold"))
        
        # 4. Title & Subtitle
        cv.create_text(110, 45, text=f"{pet['name']} - {pet['owner']}'s pet",
                       font=self.F_TITLE, fill=self.C_TEXT_DARK, anchor="w", width=350)
        cv.create_text(110, 75, text=f"pet_id: {pet['pet_id']} - {pet['services']}",
                       font=self.F_SUB, fill=self.C_TEXT_LIGHT, anchor="w", width=350)

        # 5. Các Tag (Chips)
        next_x = self.draw_chip(cv, 40, 110, pet["breed"], self.C_CHIP_BREED) + 8
        next_x = self.draw_chip(cv, next_x, 110, pet["weight"], self.C_CHIP_WEIGHT) + 8
        next_x = self.draw_chip(cv, next_x, 110, pet["age"], self.C_CHIP_AGE) + 8
        self.draw_chip(cv, next_x, 110, pet["gender"], self.C_CHIP_GENDER)

        # ─── THÔNG TIN CHI TIẾT ───
        start_x = 40
        y = 155
        spacing = 28
        section_gap = 16

        # Current room
        cv.create_text(start_x, y, text="Current room", font=self.F_HEADER, fill=self.C_TEXT_DARK, anchor="w")
        y += spacing
        cv.create_text(start_x, y, text=pet["room"], font=self.F_BODY, fill=self.C_TEXT_DARK, anchor="w")
        if pet["camera"]:
            cv.create_text(start_x + 120, y, text="Link cam", font=self.F_LINK, fill=self.C_TEXT_DARK, anchor="w")
        y += spacing + section_gap

        # Owner Information
        cv.create_text(start_x, y, text="Owner Information", font=self.F_HEADER, fill=self.C_TEXT_DARK, anchor="w")
        y += spacing
        cv.create_text(start_x, y, text="Owner", font=self.F_BODY, fill=self.C_TEXT_DARK, anchor="w")
        cv.create_text(start_x + 100, y, text=pet["owner"], font=self.F_BODY, fill=self.C_TEXT_DARK, anchor="w", width=330)
        y += spacing
        cv.create_text(start_x, y, text="Phone", font=self.F_BODY, fill=self.C_TEXT_DARK, anchor="w")
        cv.create_text(start_x + 100, y, text=pet["phone"], font=self.F_BODY, fill=self.C_TEXT_DARK, anchor="w")
        y += spacing + section_gap

        # Health
        cv.create_text(start_x, y, text="Health", font=self.F_HEADER, fill=self.C_TEXT_DARK, anchor="w")
        y += spacing
        cv.create_text(start_x, y, text="Sterilization", font=self.F_BODY, fill=self.C_TEXT_DARK, anchor="w")
        cv.create_text(start_x + 200, y, text=pet["sterilized"], font=self.F_BODY, fill=self.C_TEXT_DARK, anchor="w")
        y += spacing
        cv.create_text(start_x, y, text="Vaccination", font=self.F_BODY, fill=self.C_TEXT_DARK, anchor="w")
        cv.create_text(start_x + 200, y, text=pet["vaccinated"], font=self.F_BODY, fill=self.C_TEXT_DARK, anchor="w")
        y += spacing + section_gap

        # Health condition
        cv.create_text(start_x, y, text="Health condition", font=self.F_HEADER, fill=self.C_TEXT_DARK, anchor="w")
        y += spacing
        cv.create_text(start_x, y, text=pet["health"], font=self.F_BODY, fill=self.C_TEXT_DARK, anchor="w", width=430)
        y += spacing + section_gap

        # Behaviour note
        cv.create_text(start_x, y, text="Behaviour note", font=self.F_HEADER, fill=self.C_TEXT_DARK, anchor="w")
        y += spacing
        cv.create_text(start_x, y, text=pet["behaviour"], font=self.F_BODY, fill=self.C_TEXT_DARK, anchor="w", width=430)
        y += spacing + section_gap

        # Special requirement
        cv.create_text(start_x, y, text="Special requirement", font=self.F_HEADER, fill=self.C_TEXT_DARK, anchor="w")
        y += spacing
        cv.create_text(start_x, y, text=pet["special"], font=self.F_BODY, fill=self.C_TEXT_DARK, anchor="w", width=430)

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
        return x + text_w + padding_x * 2

if __name__ == "__main__":
    pet_id = int(sys.argv[1]) if len(sys.argv) > 1 and sys.argv[1].isdigit() else None
    app = PetPopup(pet_id=pet_id)
    app.mainloop()
