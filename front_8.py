import tkinter as tk
from PIL import Image, ImageTk, ImageDraw
import os
import sys
from datetime import date
from decimal import Decimal

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


class CustomerProfileBackend:
    """Data layer for the Customer Profile popup."""

    def __init__(self, db=None):
        self.db = db or DatabaseConnection()

    @staticmethod
    def _bit_to_yes_no(value):
        if isinstance(value, (bytes, bytearray)):
            value = value != b"\x00"
        return "Yes" if bool(value) else "No"

    @staticmethod
    def _format_money(value):
        if value is None:
            value = 0
        if isinstance(value, Decimal):
            value = int(value)
        return f"{int(value):,}".replace(",", ".") + "đ"

    @staticmethod
    def _format_date(value):
        if not value:
            return "-"
        return value.strftime("%d/%m/%Y")

    @staticmethod
    def _format_short_date(value):
        if not value:
            return "-"
        return value.strftime("%d/%m")

    @staticmethod
    def _title(value, default="-"):
        if value in (None, ""):
            return default
        return str(value).replace("_", " ").title()

    def _get_customer(self, customer_id):
        params = []
        where_clause = ""
        if customer_id is not None:
            where_clause = "WHERE c.customer_id = %s"
            params.append(customer_id)

        rows = self.db.fetch_all(
            f"""
            SELECT
                c.customer_id,
                c.full_name,
                c.phone,
                c.address,
                c.district,
                c.join_date,
                c.total_spent,
                c.historical_flag,
                COALESCE(v.current_points, cp.total_point, 0) AS points,
                COALESCE(v.current_membership, cp.membership_type, 'Standard') AS membership
            FROM customers c
            LEFT JOIN vw_customer_lifetime_value v ON v.customer_id = c.customer_id
            LEFT JOIN customer_points cp ON cp.customer_id = c.customer_id
            {where_clause}
            ORDER BY c.last_active_date DESC, c.customer_id
            LIMIT 1
            """,
            tuple(params),
        )
        return rows[0] if rows else None

    def _get_subscription(self, customer_id):
        return self.db.fetch_one(
            """
            SELECT
                cs.start_date,
                cs.end_date,
                pt.plan_name,
                pt.max_points
            FROM customer_subscriptions cs
            JOIN plan_types pt ON pt.plan_type_id = cs.plan_type_id
            JOIN subscription_statuses ss ON ss.status_id = cs.status_id
            WHERE cs.customer_id = %s
            ORDER BY
                ss.status_name = 'active' DESC,
                cs.end_date DESC
            LIMIT 1
            """,
            (customer_id,),
        )

    def _get_pets(self, customer_id):
        rows = self.db.fetch_all(
            """
            SELECT pet_name, species
            FROM pets
            WHERE customer_id = %s
            ORDER BY pet_name
            LIMIT 8
            """,
            (customer_id,),
        )
        pets = []
        for row in rows or []:
            species = self._title(row.get("species"), "Pet")
            pets.append(f"{species} {row.get('pet_name') or '-'}")
        return pets

    def _get_history(self, customer_id):
        rows = self.db.fetch_all(
            """
            SELECT
                b.booking_id,
                p.pet_name,
                p.species,
                b.check_in,
                b.check_out,
                COALESCE(bl.total_amount, b.room_price, 0) AS amount
            FROM bookings b
            JOIN pets p ON p.pet_id = b.pet_id
            LEFT JOIN billing bl ON bl.booking_id = b.booking_id
            WHERE b.customer_id = %s
            ORDER BY b.check_in DESC, b.booking_id DESC
            LIMIT 3
            """,
            (customer_id,),
        )
        history = []
        for row in rows or []:
            pet_label = f"{self._title(row.get('species'), 'Pet')} {row.get('pet_name') or '-'}"
            history.append({
                "booking": f"#{row.get('booking_id')}",
                "pet": pet_label,
                "dates": f"{self._format_short_date(row.get('check_in'))} -> {self._format_short_date(row.get('check_out'))}",
                "amount": self._format_money(row.get("amount")),
            })
        return history

    def get_profile(self, customer_id=None):
        customer = self._get_customer(customer_id)
        if not customer:
            return None

        subscription = self._get_subscription(customer["customer_id"]) or {}
        points = int(customer.get("points") or 0)
        point_goal = int(subscription.get("max_points") or 1000)
        if point_goal <= 0:
            point_goal = 1000
        join_date = customer.get("join_date")
        days_ago = (date.today() - join_date).days if join_date else 0

        validity = "-"
        if subscription.get("start_date") and subscription.get("end_date"):
            validity = f"{self._format_short_date(subscription['start_date'])} -> {self._format_short_date(subscription['end_date'])}"

        return {
            "customer_id": customer["customer_id"],
            "full_name": customer.get("full_name") or "-",
            "phone": customer.get("phone") or "-",
            "address": customer.get("address") or "-",
            "district": customer.get("district") or "-",
            "member_since": f"{self._format_date(join_date)} ({days_ago} days ago)",
            "historical_flag": self._bit_to_yes_no(customer.get("historical_flag")),
            "membership": subscription.get("plan_name") or self._title(customer.get("membership"), "Standard"),
            "validity": validity,
            "points": points,
            "point_goal": point_goal,
            "point_text": f"{points}/{point_goal}p",
            "point_ratio": min(points / point_goal, 1.0),
            "total_spend": self._format_money(customer.get("total_spent")),
            "pets": self._get_pets(customer["customer_id"]),
            "history": self._get_history(customer["customer_id"]),
        }


class CustomerProfilePopup(tk.Tk):
    def __init__(self, customer_id=None):
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
        self.F_HEADER  = ("Arial Rounded MT Bold", 18, "bold")
        self.F_BODY    = ("Baghdad", 18)
        self.F_TBL_HDR = ("Baghdad", 18)

        self.cv = tk.Canvas(self, width=self.W, height=self.H, bg="#E5E5E5", highlightthickness=0)
        self.cv.pack(fill=tk.BOTH, expand=True)
        self.backend = CustomerProfileBackend()
        self.profile = self.load_profile(customer_id)
        
        self.draw_popup()

    def load_profile(self, customer_id=None):
        try:
            return self.backend.get_profile(customer_id)
        except Exception as exc:
            print(f"Khong the tai du lieu Customer Profile: {exc}")
            return None

    def draw_popup(self):
        cv = self.cv
        margin = 10
        profile = self.profile or {
            "full_name": "No customer",
            "phone": "-",
            "address": "-",
            "district": "-",
            "member_since": "-",
            "historical_flag": "No",
            "membership": "-",
            "validity": "-",
            "point_text": "0/1000p",
            "point_ratio": 0,
            "total_spend": "0d",
            "pets": [],
            "history": [],
        }
        
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
        cv.create_text(40, 45, text=f"Customer Profile - {profile['full_name']}",
                       font=self.F_TITLE, fill=self.C_TEXT_DARK, anchor="w", width=500)
        cv.create_text(40, 75, text=f"{profile['phone']} - {profile['address']}",
                       font=self.F_SUB, fill=self.C_TEXT_LIGHT, anchor="w", width=500)
        
        nxt_x = 40
        for pet in (profile["pets"][:3] or ["No pet"]):
            nxt_x = self.draw_chip(cv, nxt_x, 100, pet, self.C_CHIP_PET) + 12

        # 4. CUSTOMER DETAILS
        start_x = 40
        col2_x = 230
        y = 175
        spacing = 30
        
        cv.create_text(start_x, y, text="Customer Details", font=self.F_HEADER, fill=self.C_TEXT_DARK, anchor="w")
        y += 35
        
        details = [
            ("Full name", profile["full_name"]),
            ("Phone Number", profile["phone"]),
            ("Street Address", profile["address"]),
            ("District", profile["district"]),
            ("Member Since", profile["member_since"]),
        ]
        
        for title, val in details:
            cv.create_text(start_x, y, text=title, font=self.F_BODY, fill=self.C_TEXT_DARK, anchor="w")
            cv.create_text(col2_x, y, text=val, font=self.F_BODY, fill=self.C_TEXT_DARK, anchor="w", width=320)
            y += spacing
            
        # Dòng Historical flag (có chip)
        cv.create_text(start_x, y, text="Historical flag", font=self.F_BODY, fill=self.C_TEXT_DARK, anchor="w")
        self.draw_chip(cv, col2_x, y - 12, profile["historical_flag"], self.C_CHIP_FLAG)

        # 5. MEMBERSHIP & POINT
        y += 45
        cv.create_text(start_x, y, text="Membership & Point", font=self.F_HEADER, fill=self.C_TEXT_DARK, anchor="w")
        y += 35
        
        cv.create_text(start_x, y, text="Current Membership", font=self.F_BODY, fill=self.C_TEXT_DARK, anchor="w")
        cv.create_text(col2_x, y, text=profile["membership"], font=self.F_BODY, fill=self.C_TEXT_DARK, anchor="w")
        y += spacing
        
        cv.create_text(start_x, y, text="Validity Period", font=self.F_BODY, fill=self.C_TEXT_DARK, anchor="w")
        cv.create_text(col2_x, y, text=profile["validity"], font=self.F_BODY, fill=self.C_TEXT_DARK, anchor="w")
        y += spacing
        
        cv.create_text(start_x, y, text="Current Points", font=self.F_BODY, fill=self.C_TEXT_DARK, anchor="w")
        # Vẽ Progress Bar (Thanh cam/xám)
        bar_w = 200
        bar_h = 12
        bar_y = y - 6
        _round_rect(cv, col2_x, bar_y, col2_x + bar_w, bar_y + bar_h, radius=6, fill=self.C_PROG_BG)
        _round_rect(cv, col2_x, bar_y, col2_x + bar_w * profile["point_ratio"], bar_y + bar_h,
                    radius=6, fill=self.C_PROG_FG)
        cv.create_text(col2_x + bar_w + 15, y, text=profile["point_text"], font=self.F_BODY, fill=self.C_TEXT_DARK, anchor="w")

        # 6. TOTAL SPEND (Nằm dưới đường line xám)
        y = 530
        cv.create_text(start_x, y, text="Total spend", font=self.F_HEADER, fill=self.C_TEXT_DARK, anchor="w")
        y += 30
        cv.create_text(start_x, y, text=profile["total_spend"], font=self.F_HEADER, fill=self.C_TEXT_GREEN, anchor="w")

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
        if not profile["history"]:
            cv.create_text(col_x[0], y, text="No booking history", font=self.F_BODY,
                           fill=self.C_TEXT_LIGHT, anchor="w")
            return

        for row in profile["history"]:
            # Cột #
            cv.create_text(col_x[0], y, text=row["booking"], font=self.F_BODY, fill=self.C_TEXT_DARK, anchor="w")
            # Cột Pet (Chip)
            self.draw_chip(cv, col_x[1], y - 12, row["pet"], self.C_CHIP_PET)
            # Cột Dates (2 dòng)
            cv.create_text(col_x[2], y, text=row["dates"], font=self.F_BODY, fill=self.C_TEXT_DARK, anchor="w", justify="left")
            # Cột Amount
            cv.create_text(col_x[3], y, text=row["amount"], font=self.F_HEADER, fill=self.C_TEXT_GREEN, anchor="w")
            
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
    customer_id = int(sys.argv[1]) if len(sys.argv) > 1 and sys.argv[1].isdigit() else None
    app = CustomerProfilePopup(customer_id=customer_id)
    app.mainloop()
