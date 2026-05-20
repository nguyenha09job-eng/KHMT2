import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk, ImageDraw
import os
import sys
from datetime import datetime
from decimal import Decimal
import unicodedata

from database import DatabaseConnection
from navigation import bind_click, bind_nav_item, logout_to_login, switch_to


_HCMC_DISTRICTS = [
    "Quận 1", "Quận 2", "Quận 3", "Quận 4", "Quận 5", "Quận 6",
    "Quận 7", "Quận 8", "Quận 9", "Quận 10", "Quận 11", "Quận 12",
    "Quận Bình Tân", "Quận Tân Phú", "Quận Tân Bình", "Quận Gò Vấp",
    "Quận Bình Thạnh", "Quận Phú Nhuận",
    "Thành phố Thủ Đức",
    "Huyện Bình Chánh", "Huyện Hóc Môn", "Huyện Củ Chi",
    "Huyện Nhà Bè", "Huyện Cần Giờ",
]

_HCMC_STREETS = [
    "Nguyễn Huệ", "Lê Lợi", "Đồng Khởi", "Hai Bà Trưng", "Lý Tự Trọng",
    "Nguyễn Đình Chiểu", "Nam Kỳ Khởi Nghĩa", "Điện Biên Phủ", "Võ Văn Tần",
    "Phạm Ngọc Thạch", "Nguyễn Thị Minh Khai", "Phan Đình Phùng",
    "Nguyễn Văn Cừ", "Trần Hưng Đạo", "Trần Quang Khải", "Nguyễn Thái Học",
    "Lê Duẩn", "Lý Thường Kiệt", "Nguyễn Thượng Hiền", "Nguyễn Thông",
    "Nguyễn Công Trứ", "Lê Lai", "Trần Bình Trọng", "Bùi Viện", "Đề Thám",
    "Cô Bắc", "Cô Giang", "Phạm Hồng Thái", "Tôn Thất Tùng",
    "Nguyễn Cư Trinh", "Nguyễn Thị Nghĩa", "Lê Thạch",
    "Cách Mạng Tháng Tám", "Trường Chinh", "Hoàng Văn Thụ",
    "Nguyễn Thái Sơn", "Phạm Ngũ Lão", "Nguyễn Trãi",
    "Nguyễn Văn Trỗi", "Ngô Gia Tự", "Lê Văn Sỹ",
    "Nguyễn Trọng Tuyển", "Phạm Văn Bạch", "Nguyễn Chí Thanh",
    "Trần Duy Hưng", "Nguyễn Khánh Toàn",
    "Xa Lộ Hà Nội", "Phạm Văn Đồng", "Nguyễn Văn Linh",
    "Võ Duy Ninh", "Nguyễn Duy Trinh", "Lê Văn Việt", "Đỗ Xuân Hợp",
    "Lê Quang Định", "Phan Đăng Lưu", "Lương Định Của",
    "Nguyễn Thị Định", "Nguyễn Cơ Thạch",
    "Trường Sơn", "Trần Quốc Hoàn", "Cộng Hòa", "Hoàng Hoa Thám",
    "Tân Kỳ Tân Quý", "Âu Cơ", "Lạc Long Quân", "An Dương Vương",
    "Nguyễn Lương Bằng", "Phạm Hữu Lầu", "Nguyễn Bình",
    "Huỳnh Tấn Phát", "Nguyễn Hữu Thọ", "Tạ Quang Bửu",
    "Võ Chí Công", "Kha Vạn Cân", "Tô Ngọc Vân", "Trần Não",
    "Hồng Bàng", "Hùng Vương", "Nguyễn Tri Phương", "Trần Phú",
    "Trần Quang Diệu", "Nguyễn Văn Đậu", "Phan Văn Hớn",
    "Phùng Hưng", "Bùi Thị Xuân", "Nguyễn Văn Tố", "Lò Gốm",
    "Võ Văn Kiệt", "Nguyễn Tất Thành", "Kinh Dương Vương",
    "Quốc Lộ 1", "Quốc Lộ 13", "Quốc Lộ 22", "Quốc Lộ 50",
    "Quang Trung", "Nguyễn Thái Sơn",
]

# District → streets mapping for address validation
_HCMC_STREETS_BY_DISTRICT = {
    "Quận 1": [
        "Nguyễn Huệ", "Lê Lợi", "Đồng Khởi", "Hai Bà Trưng", "Lý Tự Trọng",
        "Nguyễn Đình Chiểu", "Nam Kỳ Khởi Nghĩa", "Võ Văn Tần", "Phạm Ngọc Thạch",
        "Nguyễn Thị Minh Khai", "Phan Đình Phùng", "Nguyễn Văn Cừ", "Trần Hưng Đạo",
        "Trần Quang Khải", "Nguyễn Thái Học", "Lê Duẩn", "Lý Thường Kiệt",
        "Nguyễn Thượng Hiền", "Nguyễn Thông", "Nguyễn Công Trứ", "Lê Lai",
        "Trần Bình Trọng", "Bùi Viện", "Đề Thám", "Cô Bắc", "Cô Giang",
        "Phạm Hồng Thái", "Tôn Thất Tùng", "Nguyễn Cư Trinh", "Nguyễn Thị Nghĩa",
        "Lê Thạch", "Phạm Phú Thứ", "Tôn Thất Thuyết", "Yersin", "Ký Con",
        "Nguyễn Văn Ngọc", "Điện Biên Phủ", "Phạm Ngũ Lão",
    ],
    "Quận 3": [
        "Cách Mạng Tháng Tám", "Trường Chinh", "Hoàng Văn Thụ", "Nguyễn Thái Sơn",
        "Phạm Ngũ Lão", "Nguyễn Trãi", "Nguyễn Văn Trỗi", "Ngô Gia Tự",
        "Lê Văn Sỹ", "Trần Văn Đang", "Nguyễn Trọng Tuyển", "Phạm Văn Bạch",
        "Phan Huy Chú", "Văn Cao", "Tô Hiệu", "Nguyễn Sơn", "Nguyễn Kiệm",
        "Phan Văn Trị", "Trần Quốc Hoàn", "Nguyễn Phúc Nguyên",
        "Nguyễn Chí Thanh", "Hoàng Minh Giám", "Nguyễn Khánh Toàn",
        "Trần Duy Hưng", "Điện Biên Phủ", "Nguyễn Đình Chiểu",
    ],
    "Quận 5": [
        "Trần Hưng Đạo", "Hồng Bàng", "Hùng Vương", "Nguyễn Tri Phương",
        "Trần Phú", "Nguyễn Trãi", "Châu Văn Liêm", "Phan Huy Ích",
        "Phùng Hưng", "Bùi Thị Xuân", "Nguyễn Văn Tố", "Lò Gốm",
        "Ngô Văn Năm", "Lê Quang Sung",
    ],
    "Quận 6": [
        "Hồng Bàng", "Hùng Vương", "Kinh Dương Vương", "Lạc Long Quân",
        "Phạm Văn Chí", "Nguyễn Văn Luông",
    ],
    "Quận 10": [
        "Cách Mạng Tháng Tám", "Lý Thường Kiệt", "Nguyễn Tri Phương",
        "Trần Phú", "Nguyễn Chí Thanh", "Lê Hồng Phong", "Sư Vạn Hạnh",
        "Ngô Gia Tự", "Lý Thái Tổ",
    ],
    "Quận 11": [
        "Trần Hưng Đạo", "Hồng Bàng", "Lạc Long Quân", "Âu Cơ",
        "Nguyễn Thị Nhỏ", "Bình Thới", "Hàn Hải Nguyên",
    ],
    "Quận 7": [
        "Nguyễn Văn Linh", "Nguyễn Lương Bằng", "Phạm Hữu Lầu",
        "Nguyễn Bình", "Lê Văn Lương", "Nguyễn Thị Thập",
        "Huỳnh Tấn Phát", "Nguyễn Văn Tạo", "Nguyễn Hữu Thọ",
        "Tạ Quang Bửu", "Phan Văn Đáng", "Ca Văn Thỉnh",
        "Trần Xuân Soạn", "Nguyễn Cơ Thạch",
    ],
    "Bình Thạnh": [
        "Điện Biên Phủ", "Xa Lộ Hà Nội", "Phạm Văn Đồng", "Nguyễn Văn Linh",
        "Võ Duy Ninh", "Nguyễn Duy Trinh", "Lê Văn Việt", "Đỗ Xuân Hợp",
        "Nguyễn Xí", "Ngô Tất Tố", "Lê Quang Định", "Phan Đăng Lưu",
        "Phan Chu Trinh", "Lương Định Của", "Huyền Trân Công Chúa",
        "Nguyễn Thị Định", "Nguyễn Cơ Thạch", "Trần Quang Diệu",
        "Nguyễn Văn Đậu", "Phan Văn Hớn",
    ],
    "Tân Bình": [
        "Trường Sơn", "Trần Quốc Hoàn", "Cộng Hòa", "Hoàng Hoa Thám",
        "Tân Kỳ Tân Quý", "Âu Cơ", "Lạc Long Quân", "An Dương Vương",
        "Thụy Khuê", "Lê Văn Sỹ", "Phạm Văn Bạch", "Trần Văn Đang",
        "Nguyễn Trọng Tuyển",
    ],
    "Tân Phú": [
        "Tân Kỳ Tân Quý", "Lạc Long Quân", "Âu Cơ", "Kinh Dương Vương",
        "Lũy Bán Bích", "Trương Vĩnh Ký", "Thoại Ngọc Hầu",
    ],
    "Bình Tân": [
        "Kinh Dương Vương", "Hồ Học Lãm", "Tên Lửa", "Trần Văn Kiểu",
        "Lê Văn Quới", "Mã Lò", "Bình Trị Đông",
    ],
    "Gò Vấp": [
        "Quang Trung", "Nguyễn Thái Sơn", "Phan Văn Trị", "Nguyễn Kiệm",
        "Lê Đức Thọ", "Nguyễn Văn Lượng", "Dương Quảng Hàm",
    ],
    "Phú Nhuận": [
        "Phan Đăng Lưu", "Nguyễn Văn Trỗi", "Nguyễn Đình Chiểu",
        "Trần Huy Liệu", "Hoàng Văn Thụ", "Huỳnh Văn Bánh",
        "Lê Văn Sỹ", "Trần Văn Đang",
    ],
    "Thủ Đức": [
        "Xa Lộ Hà Nội", "Võ Chí Công", "Phạm Văn Đồng", "Đỗ Xuân Hợp",
        "Nguyễn Duy Trinh", "Lê Văn Việt", "Kha Vạn Cân", "Tô Ngọc Vân",
        "Trần Não", "Nguyễn Văn Hưởng", "Nguyễn Thị Định",
        "Hoàng Diệu", "Đặng Văn Bi", "Linh Trung",
    ],
    "Bình Chánh": [
        "Quốc Lộ 1", "Nguyễn Văn Linh", "Võ Văn Kiệt", "Kinh Dương Vương",
        "Trần Đại Nghĩa", "Đoàn Nguyễn Tuân",
    ],
    "Hóc Môn": [
        "Quốc Lộ 22", "Nguyễn Ảnh Thủ", "Lê Lợi", "Lý Thường Kiệt",
        "Đặng Thúc Vịnh", "Trần Văn Mười",
    ],
    "Quận 2": [
        "Mai Chí Thọ", "Trần Não", "Lương Định Của", "Huyền Trân Công Chúa",
        "Nguyễn Thị Định", "Nguyễn Cơ Thạch",
    ],
    "Quận 4": [
        "Võ Văn Kiệt", "Nguyễn Tất Thành", "Tôn Thất Thuyết",
        "Trần Văn Khéo", "Khánh Hội",
    ],
    "Quận 8": [
        "Nguyễn Văn Linh", "Phạm Thế Hiển", "Hưng Phú", "Bến Bình Đông",
        "Tùng Thiện Vương", "Cao Lỗ",
    ],
    "Quận 9": [
        "Lê Văn Việt", "Đỗ Xuân Hợp", "Kha Vạn Cân", "Nguyễn Duy Trinh",
        "Võ Văn Hát", "Lã Xuân Oai",
    ],
    "Quận 12": [
        "Quốc Lộ 1", "Trường Chinh", "Hà Huy Giáp", "Lê Văn Khương",
        "Nguyễn Ảnh Thủ", "Tô Ký",
    ],
    "Nhà Bè": [
        "Nguyễn Văn Tạo", "Huỳnh Tấn Phát", "Lê Văn Lương",
        "Nguyễn Thị Thập", "Phạm Hữu Lầu",
    ],
    "Củ Chi": [
        "Quốc Lộ 22", "Tỉnh Lộ 8", "Nguyễn Văn Khạ",
        "Quốc Lộ 1", "Hà Huy Giáp",
    ],
    "Cần Giờ": [
        "Đồng Đình", "Duyên Hải", "Lương Văn Nho",
        "Trần Quang Diệu",
    ],
}


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


def _addr_extract(text):
    """Split address text into (number_prefix, street_name) for autocomplete."""
    tokens = text.split()
    for i, tok in enumerate(tokens):
        if not any(c.isdigit() for c in tok):
            prefix = " ".join(tokens[:i])
            search = " ".join(tokens[i:])
            return (prefix + " " if prefix else "", search)
    # All tokens contain digits or empty → no street name yet
    return (text + " " if text.strip() else "", "")


class BookingBackend:
    """Data layer for Quick Booking, kept directly in front_3.py."""

    def __init__(self, db=None):
        self.db = db or DatabaseConnection()

    @staticmethod
    def _clean(value):
        value = (value or "").strip()
        return value or None

    @staticmethod
    def _parse_bool(value):
        return 1 if bool(value) else 0

    @staticmethod
    def _parse_weight(value):
        text = (value or "").strip().lower().replace("kg", "").replace(",", ".")
        try:
            weight = Decimal(text)
        except Exception as exc:
            raise ValueError("Weight must be a number, for example 4.5") from exc
        if weight <= 0:
            raise ValueError("Weight must be greater than 0")
        return weight

    @staticmethod
    def _parse_datetime(value, end=False):
        text = (value or "").strip()
        formats = [
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%d %H:%M",
            "%Y-%m-%d",
            "%m/%d/%Y",
            "%m/%d/%y",
            "%d/%m/%Y",
            "%d/%m/%y",
        ]
        for fmt in formats:
            try:
                parsed = datetime.strptime(text, fmt)
                if "%H" not in fmt:
                    parsed = parsed.replace(hour=8, minute=0, second=0)
                return parsed
            except ValueError:
                pass
        raise ValueError("Date must be like 2026-05-20 or 05/20/26")

    @staticmethod
    def _room_id_from_text(value):
        text = (value or "").strip().upper().replace("R-", "").replace("ROOM", "").strip()
        return int(text) if text.isdigit() else None

    def create_booking(self, data):
        phone = self._clean(data.get("phone"))
        full_name = self._clean(data.get("full_name"))
        pet_name = self._clean(data.get("pet_name"))
        species = (data.get("species") or "Dog").strip().lower()
        gender = (data.get("gender") or "Male").strip().lower()
        weight = self._parse_weight(data.get("weight"))
        check_in = self._parse_datetime(data.get("check_in"))
        check_out = self._parse_datetime(data.get("check_out"), end=True)

        if not phone or not full_name or not pet_name:
            raise ValueError("Phone number, full name, and pet name are required")
        if species not in ("dog", "cat"):
            raise ValueError("Species must be Dog or Cat")
        if gender not in ("male", "female"):
            raise ValueError("Gender must be Male or Female")
        if check_out <= check_in:
            raise ValueError("Check out must be after check in")

        conn = self.db.connect()
        cursor = conn.cursor(dictionary=True)
        try:
            cursor.execute("SELECT customer_id FROM customers WHERE phone = %s LIMIT 1", (phone,))
            customer = cursor.fetchone()
            if customer:
                customer_id = customer["customer_id"]
                cursor.execute(
                    """
                    UPDATE customers
                    SET full_name = %s, address = %s, district = %s, last_active_date = CURDATE()
                    WHERE customer_id = %s
                    """,
                    (
                        full_name,
                        self._clean(data.get("address")),
                        self._clean(data.get("district")),
                        customer_id,
                    ),
                )
            else:
                cursor.execute(
                    """
                    INSERT INTO customers (full_name, phone, address, district, last_active_date)
                    VALUES (%s, %s, %s, %s, CURDATE())
                    """,
                    (
                        full_name,
                        phone,
                        self._clean(data.get("address")),
                        self._clean(data.get("district")),
                    ),
                )
                customer_id = cursor.lastrowid

            cursor.execute(
                """
                SELECT pet_id
                FROM pets
                WHERE customer_id = %s AND LOWER(pet_name) = LOWER(%s)
                LIMIT 1
                """,
                (customer_id, pet_name),
            )
            pet = cursor.fetchone()
            pet_values = (
                species,
                self._clean(data.get("breed")),
                weight,
                gender,
                self._parse_bool(data.get("sterilized")),
                self._clean(data.get("health_condition")),
                self._parse_bool(data.get("vaccinated")),
                self._clean(data.get("behaviour_note")),
                self._clean(data.get("special_requirement")),
            )
            if pet:
                pet_id = pet["pet_id"]
                cursor.execute(
                    """
                    UPDATE pets
                    SET species = %s, breed = %s, weight = %s, gender = %s,
                        sterilized = %s, health_condition = %s, vaccinated = %s,
                        behaviour_note = %s, special_requirement = %s
                    WHERE pet_id = %s
                    """,
                    (*pet_values, pet_id),
                )
            else:
                cursor.execute(
                    """
                    INSERT INTO pets (
                        customer_id, pet_name, species, breed, weight, gender,
                        sterilized, health_condition, vaccinated, behaviour_note,
                        special_requirement
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    (customer_id, pet_name, *pet_values),
                )
                pet_id = cursor.lastrowid

            room_type_text = self._clean(data.get("room_type"))
            if room_type_text:
                cursor.execute(
                    """
                    SELECT *
                    FROM room_types
                    WHERE (LOWER(type_name) LIKE LOWER(%s) OR room_type_id = %s)
                      AND species IN (%s, 'both')
                      AND min_weight <= %s
                      AND max_weight >= %s
                    ORDER BY species = %s DESC, price_per_night
                    LIMIT 1
                    """,
                    (
                        f"%{room_type_text}%",
                        int(room_type_text) if room_type_text.isdigit() else -1,
                        species,
                        weight,
                        weight,
                        species,
                    ),
                )
            else:
                cursor.execute(
                    """
                    SELECT *
                    FROM room_types
                    WHERE species IN (%s, 'both')
                      AND min_weight <= %s
                      AND max_weight >= %s
                    ORDER BY species = %s DESC, price_per_night
                    LIMIT 1
                    """,
                    (species, weight, weight, species),
                )
            room_type = cursor.fetchone()
            if not room_type:
                raise ValueError("No matching room type for this species and weight")

            requested_room_id = self._room_id_from_text(data.get("room"))
            room_params = [
                room_type["room_type_id"],
                check_out,
                check_in,
            ]
            room_filter = ""
            if requested_room_id is not None:
                room_filter = "AND r.room_id = %s"
                room_params.append(requested_room_id)
            cursor.execute(
                f"""
                SELECT r.room_id
                FROM rooms r
                WHERE r.room_type_id = %s
                  AND r.is_active = 1
                  AND NOT EXISTS (
                      SELECT 1
                      FROM bookings b
                      WHERE b.room_id = r.room_id
                        AND b.booking_status_id IN (1, 2)
                        AND b.check_in < %s
                        AND b.check_out > %s
                  )
                  {room_filter}
                ORDER BY r.room_id
                LIMIT 1
                """,
                tuple(room_params),
            )
            room = cursor.fetchone()
            if not room:
                raise ValueError("No available room for the selected dates")

            cursor.execute(
                """
                INSERT INTO bookings (
                    customer_id, pet_id, room_id, check_in, check_out,
                    booking_status_id, room_price, notes
                )
                VALUES (%s, %s, %s, %s, %s, 1, %s, %s)
                """,
                (
                    customer_id,
                    pet_id,
                    room["room_id"],
                    check_in,
                    check_out,
                    room_type["price_per_night"],
                    self._clean(data.get("booking_notes")),
                ),
            )
            booking_id = cursor.lastrowid

            service_text = self._clean(data.get("service"))
            if service_text:
                cursor.execute(
                    """
                    SELECT service_type_id, base_price
                    FROM service_catalog
                    WHERE is_active = 1
                      AND (LOWER(service_type) LIKE LOWER(%s) OR service_type_id = %s)
                    ORDER BY service_type_id
                    LIMIT 1
                    """,
                    (
                        f"%{service_text}%",
                        int(service_text) if service_text.isdigit() else -1,
                    ),
                )
                service = cursor.fetchone()
                if not service:
                    raise ValueError("Service not found in service catalog")
                quantity = int(data.get("service_quantity", 1))
                cursor.execute(
                    """
                    INSERT INTO services (
                        booking_id, pet_id, service_type_id, unit_price,
                        quantity, total_price, service_date, status
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, DATE(%s), 'pending')
                    """,
                    (
                        booking_id,
                        pet_id,
                        service["service_type_id"],
                        service["base_price"],
                        quantity,
                        service["base_price"] * quantity,
                        check_in,
                    ),
                )

            conn.commit()
            return {
                "booking_id": booking_id,
                "customer_id": customer_id,
                "pet_id": pet_id,
                "room_id": room["room_id"],
                "room_type": room_type["type_name"],
                "price": room_type["price_per_night"],
            }
        except Exception:
            conn.rollback()
            raise
        finally:
            cursor.close()
            conn.close()

    def get_room_type_price(self, room_type_name):
        row = self.db.fetch_one(
            "SELECT price_per_night FROM room_types WHERE LOWER(type_name) = LOWER(%s) LIMIT 1",
            (room_type_name,),
        )
        return int(row["price_per_night"]) if row else None

    def get_service_price(self, service_type_name):
        row = self.db.fetch_one(
            "SELECT base_price FROM service_catalog WHERE LOWER(service_type) = LOWER(%s) AND is_active = 1 LIMIT 1",
            (service_type_name,),
        )
        return int(row["base_price"]) if row else None

    def get_available_rooms(self, room_type_name):
        rows = self.db.fetch_all(
            """
            SELECT r.room_id
            FROM rooms r
            JOIN room_types rt ON rt.room_type_id = r.room_type_id
            WHERE LOWER(rt.type_name) = LOWER(%s)
              AND r.is_active = 1
            ORDER BY r.room_id
            """,
            (room_type_name,),
        )
        return [f"R-{int(row['room_id']):02d}" for row in rows] if rows else []


class BookingDashboard(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Pet&Bed - Booking")
        self.attributes("-fullscreen", True)
        self.configure(bg="#A8D3CF")
        self.update_idletasks()

        self.W = self.winfo_width()
        self.H = self.winfo_height()
        self.BASE_W = 1200.0
        self.BASE_H = 850.0
        self._s = self.W / self.BASE_W
        s = self._s
        self.Y_OFF = 20

        # Colors
        self.C_BG = "#A8D3CF"
        self.C_SIDEBAR = "#FFFFFF"
        self.C_TEXT = "#4A3525"
        self.C_TEXT_LIGHT = "#7A685F"
        self.C_WHITE = "#FFFFFF"
        self.C_ACTIVE = "#68BBB2"
        self.C_CARD_BG = "#FFFFFF"
        self.C_BORDER = "#CFC9C3"
        self.C_DIVIDER = "#DDD8D2"
        self.C_CONFIRM = "#68BBB2"
        self.C_CHIP_BORDER = "#D8D4CF"
        self.C_TOGGLE_OFF = "#D8D4D0"
        self.C_PLACEHOLDER = "#B5B0AA"

        # Fonts
        self.F_LOGO = ("Arial Rounded MT Bold", max(16, int(40 * s)), "bold")
        self.F_NAV = ("Baghdad", max(10, int(18 * s)))
        self.F_TITLE = ("Arial Rounded MT Bold", max(10, int(18 * s)), "bold")
        self.F_DATE = ("Baghdad", max(10, int(18 * s)))
        self.F_SECTION = ("Arial Rounded MT Bold", max(10, int(20 * s)), "bold")
        self.F_QUICK = ("Arial Rounded MT Bold", max(18, int(36 * s)), "bold")
        self.F_LABEL = ("Baghdad", max(10, int(16 * s)), "bold")
        self.F_INPUT = ("Baghdad", max(10, int(18 * s)))
        self.F_BTN = ("Baghdad", max(10, int(16 * s)))
        self.F_PRICE = ("Baghdad", max(10, int(18 * s)), "bold")
        self.F_QUOTE = ("Arial Rounded MT Bold", max(10, int(16 * s)), "bold")
        self.F_TOGGLE_BTN = ("Baghdad", max(9, int(14 * s)), "bold")

        self.images = []
        self.backend = BookingBackend()
        self.entries = {}
        self.placeholders = {}
        self.choice_vars = {
            "membership": tk.StringVar(value="No"),
            "species": tk.StringVar(value="Dog"),
            "gender": tk.StringVar(value="Male"),
            "room_type": tk.StringVar(value="Small Dog Room"),
            "service": tk.StringVar(value="grooming"),
        }
        self.chip_groups = {}
        self.toggle_vars = {}
        self._price_label = None
        self._room_chips = []
        self._selected_room_var = tk.StringVar(value="")
        self._room_chips_container = None

        # Layout
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

        # Content - scrollable frame approach
        self.content_container = tk.Frame(main, bg=self.C_BG)
        self.content_container.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        content_canvas = tk.Canvas(self.content_container, bg=self.C_BG, highlightthickness=0)
        scrollbar = tk.Scrollbar(self.content_container, orient=tk.VERTICAL, command=content_canvas.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        content_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        content_canvas.configure(yscrollcommand=scrollbar.set)
        self.content_canvas = content_canvas

        # Scrollable inner frame
        self.inner = tk.Frame(content_canvas, bg=self.C_BG)
        self.inner_window = content_canvas.create_window(0, 0, window=self.inner, anchor="nw")

        # Draw
        self.draw_sidebar()
        self.sidebar_canvas.scale("all", 0, 0, s, s)
        self.build_content()

        # Scroll bindings - global capture to work over all child widgets
        def _on_mw_global(event):
            # Only scroll when cursor is in the content area (right of sidebar)
            sidebar_right = self.side_frame.winfo_rootx() + self.side_frame.winfo_width()
            if event.x_root >= sidebar_right:
                if sys.platform == "darwin":
                    content_canvas.yview_scroll(int(-event.delta), "units")
                else:
                    content_canvas.yview_scroll(int(-event.delta / 120), "units")

        self.bind_all("<MouseWheel>", _on_mw_global, add="+")
        self.bind_all("<Button-4>", lambda e: content_canvas.yview_scroll(-1, "units"), add="+")
        self.bind_all("<Button-5>", lambda e: content_canvas.yview_scroll(1, "units"), add="+")

        # Also bind on content_canvas itself for when it has focus
        content_canvas.bind("<MouseWheel>", _on_mw_global, add="+")

        def _on_configure(e):
            content_canvas.itemconfig(self.inner_window, width=e.width)
            content_canvas.configure(scrollregion=content_canvas.bbox("all"))
        content_canvas.bind("<Configure>", _on_configure)
        self.inner.bind("<Configure>", lambda e: content_canvas.configure(scrollregion=content_canvas.bbox("all")))

        self.bind("<Escape>", lambda e: self.destroy())

    # =====================================================
    # SIDEBAR (same as front_1, Booking active, turtle icon)
    # =====================================================
    def draw_sidebar(self):
        cv = self.sidebar_canvas
        _round_rect(cv, -80, 0, 250, 820, radius=30, fill=self.C_SIDEBAR, outline="")
        cv.create_text(125, 70, text="Pet&Bed", font=self.F_LOGO, fill=self.C_TEXT)

        nav_items = ["Dashboard", "Care View", "Booking", "Rooms",
                     "Customer & Pet", "Billing", "Staff", "Report"]
        y = 110
        item_h, item_r, pad_x, right_x, gap = 37, 18, 36, 215, 10

        for i, item in enumerate(nav_items):
            nav_tag = f"nav_{i}"
            fill = self.C_ACTIVE if i == 2 else "#efefef"
            _round_rect(cv, pad_x, y, right_x, y + item_h, radius=item_r,
                        fill=fill, outline="", tags=nav_tag)
            cv.create_text(pad_x + 20, y + 20, text=item, font=self.F_NAV,
                           fill=self.C_TEXT, anchor="w", tags=nav_tag)
            bind_nav_item(cv, nav_tag, self, item, "Booking")
            y += item_h + gap

        # Turtle icon
        _dir = os.path.dirname(__file__)
        icon_path = os.path.join(_dir, "image", "turtle.png")
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

        # Logout
        base_bottom = self.H / self._s
        btn_h, btn_pad = 42, 25
        btn_y2 = base_bottom - btn_pad
        btn_y1 = btn_y2 - btn_h
        _round_rect(cv, 30, btn_y1, 220, btn_y2, radius=btn_h // 2,
                    fill=self.C_TEXT, outline="", tags="logout_btn")
        cv.create_text(125, (btn_y1 + btn_y2) / 2, text="Log out",
                       font=self.F_NAV, fill="#FFFFFF", tags="logout_btn")
        bind_click(cv, "logout_btn", lambda e: logout_to_login(self))

    # =====================================================
    # ROUNDED IMAGE HELPER
    # =====================================================
    def create_rounded_image(self, image_path, width, height, radius):
        s = self._s
        sw, sh, sr = int(width * s), int(height * s), int(radius * s)
        if not os.path.exists(image_path):
            img = Image.new("RGB", (sw, sh), color="#CCCCCC")
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

    # =====================================================
    # CONTENT (header + form + banner using Frame widgets)
    # =====================================================
    def build_content(self):
        s = self._s
        pad_x = int(30 * s)
        pad_y = int(45 * s)
        inner = self.inner

        # === HEADER BAR ===
        header_h = int(40 * s)
        header_cv = tk.Canvas(inner, height=header_h, bg=self.C_BG, highlightthickness=0)
        header_cv.pack(fill=tk.X, padx=pad_x, pady=(pad_y, int(5 * s)))

        def _draw_header(event=None):
            header_cv.delete("all")
            w = header_cv.winfo_width()
            h = header_cv.winfo_height()
            _round_rect(header_cv, 0, 0, w, h, radius=h//2, fill=self.C_WHITE)
            header_cv.create_text(int(30*s), h//2, text="Booking", font=self.F_TITLE, fill=self.C_TEXT, anchor="w")
            header_cv.create_text(int(135*s), h//2, text=datetime.now().strftime("%A, %d/%m/%Y"),
                                  font=self.F_DATE, fill=self.C_TEXT_LIGHT, anchor="w")
            # Toggle: Bookings | History
            tw = int(95 * s)
            tx = w - int(12 * s) - tw * 2
            tg_h = h - int(6*s)
            _round_rect(header_cv, tx, int(3*s), tx + tw, h - int(3*s),
                        radius=tg_h//2, fill=self.C_TEXT)
            header_cv.create_text(tx + tw//2, h//2, text="Bookings",
                                  font=self.F_TOGGLE_BTN, fill=self.C_WHITE)
            _round_rect(header_cv, tx + tw, int(3*s), tx + tw * 2, h - int(3*s),
                        radius=tg_h//2, fill=self.C_WHITE, tags="history_toggle")
            header_cv.create_text(tx + tw + tw//2, h//2, text="History",
                                  font=self.F_TOGGLE_BTN, fill=self.C_TEXT,
                                  tags="history_toggle")
            bind_click(header_cv, "history_toggle",
                       lambda _e: switch_to(self, "Booking History", "Booking"))
        header_cv.bind("<Configure>", _draw_header)

        # === QUICK BOOKING TITLE ===
        tk.Label(inner, text="Quick booking", font=self.F_QUICK,
                 bg=self.C_BG, fg=self.C_TEXT, anchor="w").pack(fill=tk.X, padx=pad_x, pady=(int(5*s), int(14*s)))

        # === FORM CARD (layered Canvas behind Frame for rounded corners) ===
        card_wrapper = tk.Frame(inner, bg=self.C_BG)
        card_wrapper.pack(fill=tk.X, padx=pad_x, pady=(0, int(12*s)))

        # Canvas behind everything for the rounded white background
        card_bg_cv = tk.Canvas(card_wrapper, bg=self.C_BG, highlightthickness=0)
        card_bg_cv.place(x=0, y=0, relwidth=1, relheight=1)
        tk.Misc.lower(card_bg_cv)  # send behind form_frame

        # Form frame on top, padded so its corners are inside the rounded area
        card_inset = int(16 * s)
        form_frame = tk.Frame(card_wrapper, bg=self.C_CARD_BG)
        form_frame.pack(fill=tk.X, padx=card_inset, pady=card_inset)

        def _draw_card_bg(event=None):
            card_bg_cv.delete("all")
            w = card_wrapper.winfo_width()
            h = card_wrapper.winfo_height()
            if w > 1 and h > 1:
                _round_rect(card_bg_cv, 0, 0, w, h, radius=int(30*s), fill=self.C_CARD_BG)

        card_wrapper.bind("<Configure>", _draw_card_bg)

        form_pad = int(36 * s)

        # --- Customer Section ---
        self._add_section_label(form_frame, "Customer", form_pad)
        row1 = tk.Frame(form_frame, bg=self.C_CARD_BG)
        row1.pack(fill=tk.X, padx=form_pad, pady=(0, int(10*s)))
        self._add_labeled_entry(row1, "Phone number", "ex: 012345678", side=tk.LEFT, expand=True, key="phone")
        self._add_labeled_entry(row1, "Full Name", "ex: Thuy Hang", side=tk.LEFT, expand=True, key="full_name")
        # Phone validation indicator
        phone_entry = self.entries["phone"]
        phone_err = tk.Label(phone_entry.master.master, text="SĐT không hợp lệ",
                             font=self.F_LABEL, bg=self.C_CARD_BG, fg="#E74C3C")
        def _validate_phone(_event=None):
            val = phone_entry.get()
            ph = self.placeholders.get("phone", "")
            if val == ph or not val.strip():
                phone_err.pack_forget()
            elif len(val) == 10 and val.startswith("0") and val.isdigit():
                phone_err.pack_forget()
            else:
                phone_err.pack(anchor="w")
        phone_entry.bind("<KeyRelease>", _validate_phone, add="+")
        phone_entry.bind("<<Paste>>", _validate_phone, add="+")

        row2 = tk.Frame(form_frame, bg=self.C_CARD_BG)
        row2.pack(fill=tk.X, padx=form_pad, pady=(0, int(10*s)))
        self._add_labeled_entry(row2, "Street address", "ex: 45 Nguyen Thi Minh Khai", side=tk.LEFT, expand=True, key="address")
        self._add_labeled_entry(row2, "District", "Quan 3", side=tk.LEFT, key="district")
        # Autocomplete suggestions for HCMC locations
        self._add_autocomplete("address", _HCMC_STREETS, extract=_addr_extract)
        self._add_autocomplete("district", _HCMC_DISTRICTS)
        # Address-district validation
        addr_entry = self.entries["address"]
        addr_err = tk.Label(addr_entry.master.master, text="Địa chỉ không hợp lệ",
                             font=self.F_LABEL, bg=self.C_CARD_BG, fg="#E74C3C")
        district_entry = self.entries["district"]

        def _validate_address(_event=None):
            addr_val = addr_entry.get()
            addr_ph = self.placeholders.get("address", "")
            dist_val = district_entry.get()
            dist_ph = self.placeholders.get("district", "")
            _, street = _addr_extract(addr_val)
            if (addr_val == addr_ph or not addr_val.strip() or not street.strip()
                    or dist_val == dist_ph or not dist_val.strip()):
                addr_err.pack_forget()
                return

            def _norm(t):
                return unicodedata.normalize('NFKD', t).encode('ascii', 'ignore').decode('ascii').lower()

            n_street = _norm(street)
            n_dist = _norm(dist_val)
            valid = [s for d, streets in _HCMC_STREETS_BY_DISTRICT.items()
                     if _norm(d) == n_dist for s in streets]
            if not valid:
                addr_err.pack_forget()
                return
            if n_street in [_norm(s) for s in valid]:
                addr_err.pack_forget()
            else:
                addr_err.pack(anchor="w")

        addr_entry.bind("<KeyRelease>", _validate_address, add="+")
        addr_entry.bind("<<AutocompleteConfirm>>", _validate_address, add="+")
        district_entry.bind("<KeyRelease>", _validate_address, add="+")
        district_entry.bind("<<AutocompleteConfirm>>", _validate_address, add="+")

        mem_frame = tk.Frame(form_frame, bg=self.C_CARD_BG)
        mem_frame.pack(fill=tk.X, padx=form_pad, pady=(0, int(12*s)))
        tk.Label(mem_frame, text="Membership", font=self.F_LABEL, bg=self.C_CARD_BG, fg=self.C_TEXT).pack(anchor="w")
        chip_row = tk.Frame(mem_frame, bg=self.C_CARD_BG)
        chip_row.pack(anchor="w", pady=(int(3*s), 0))
        for chip in ["No", "VIP", "Premium"]:
            self._add_chip(chip_row, chip, group="membership")

        # --- Pets Section ---
        self._add_section_label(form_frame, "Pets", form_pad)
        row3 = tk.Frame(form_frame, bg=self.C_CARD_BG)
        row3.pack(fill=tk.X, padx=form_pad, pady=(0, int(10*s)))

        # Pack rightmost widgets first from the right so they get priority space
        st_frame = tk.Frame(row3, bg=self.C_CARD_BG)
        st_frame.pack(side=tk.RIGHT, padx=(int(12*s), 0), anchor="ne")
        tk.Label(st_frame, text="Sterilization", font=self.F_LABEL, bg=self.C_CARD_BG, fg=self.C_TEXT).pack(anchor="w")
        self._add_toggle(st_frame, key="sterilized")

        sp_frame = tk.Frame(row3, bg=self.C_CARD_BG)
        sp_frame.pack(side=tk.RIGHT, padx=(int(12*s), 0), anchor="ne")
        tk.Label(sp_frame, text="Species", font=self.F_LABEL, bg=self.C_CARD_BG, fg=self.C_TEXT).pack(anchor="w")
        sp_chips = tk.Frame(sp_frame, bg=self.C_CARD_BG)
        sp_chips.pack(anchor="w")
        for c in ["Dog", "Cat"]:
            self._add_chip(sp_chips, c, group="species")

        # Pack leftmost widgets from the left
        self._add_labeled_entry(row3, "Name", "ex: Milo", side=tk.LEFT, expand=True, key="pet_name")

        row4 = tk.Frame(form_frame, bg=self.C_CARD_BG)
        row4.pack(fill=tk.X, padx=form_pad, pady=(0, int(10*s)))

        # Pack rightmost widgets first from the right so they get priority space
        vc_frame = tk.Frame(row4, bg=self.C_CARD_BG)
        vc_frame.pack(side=tk.RIGHT, padx=(int(12*s), 0), anchor="ne")
        tk.Label(vc_frame, text="Vaccinated", font=self.F_LABEL, bg=self.C_CARD_BG, fg=self.C_TEXT).pack(anchor="w")
        self._add_toggle(vc_frame, key="vaccinated")

        gd_frame = tk.Frame(row4, bg=self.C_CARD_BG)
        gd_frame.pack(side=tk.RIGHT, padx=(int(12*s), 0), anchor="ne")
        tk.Label(gd_frame, text="Gender", font=self.F_LABEL, bg=self.C_CARD_BG, fg=self.C_TEXT).pack(anchor="w")
        gd_chips = tk.Frame(gd_frame, bg=self.C_CARD_BG)
        gd_chips.pack(anchor="w")
        for c in ["Male", "Female"]:
            self._add_chip(gd_chips, c, group="gender")

        # Pack leftmost widgets from the left
        self._add_labeled_entry(row4, "Breed", "ex: Poodle", side=tk.LEFT, expand=True, key="breed")
        self._add_labeled_entry(row4, "Weight (kg)", "ex: 4.5", side=tk.LEFT, key="weight")
        # Weight validation indicator
        weight_entry = self.entries["weight"]
        weight_err = tk.Label(weight_entry.master.master, text="giá trị không hợp lệ",
                              font=self.F_LABEL, bg=self.C_CARD_BG, fg="#E74C3C")
        def _validate_weight(_event=None):
            val = weight_entry.get()
            ph = self.placeholders.get("weight", "")
            if val == ph or not val.strip():
                weight_err.pack_forget()
            else:
                try:
                    float(val.replace(",", ".").strip())
                    weight_err.pack_forget()
                except ValueError:
                    weight_err.pack(anchor="w")
        weight_entry.bind("<KeyRelease>", _validate_weight, add="+")
        weight_entry.bind("<<Paste>>", _validate_weight, add="+")

        for label, key in [
            ("Health condition", "health_condition"),
            ("Behaviour note", "behaviour_note"),
            ("Special requirement", "special_requirement"),
        ]:
            r = tk.Frame(form_frame, bg=self.C_CARD_BG)
            r.pack(fill=tk.X, padx=form_pad, pady=(0, int(10*s)))
            self._add_labeled_entry(r, label, "Note here", side=tk.TOP, expand=True, full=True, key=key)

        # --- Booking Section ---
        self._add_section_label(form_frame, "Booking", form_pad)
        row5 = tk.Frame(form_frame, bg=self.C_CARD_BG)
        row5.pack(fill=tk.X, padx=form_pad, pady=(0, int(10*s)))
        # Pack price_f first on the RIGHT so it is guaranteed full width and never cut off
        price_f = tk.Frame(row5, bg=self.C_CARD_BG)
        price_f.pack(side=tk.RIGHT, padx=(int(10*s), 0), anchor="ne")
        tk.Label(price_f, text="Price", font=self.F_LABEL, bg=self.C_CARD_BG, fg=self.C_TEXT).pack(anchor="w")
        pv = tk.Frame(price_f, bg=self.C_CARD_BG)
        pv.pack(anchor="w")
        self._price_label = tk.Label(pv, text=self._price_text(), font=self.F_PRICE,
                                     bg=self.C_CARD_BG, fg="#6BA52F")
        self._price_label.pack(side=tk.LEFT)
        tk.Label(pv, text="/night", font=self.F_LABEL, bg=self.C_CARD_BG, fg=self.C_TEXT).pack(side=tk.LEFT)

        # Pack rt_frame on the LEFT to fill remaining space
        rt_frame = tk.Frame(row5, bg=self.C_CARD_BG)
        rt_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, int(10*s)))
        tk.Label(rt_frame, text="Room type", font=self.F_LABEL, bg=self.C_CARD_BG, fg=self.C_TEXT).pack(anchor="w")
        rt_row1 = tk.Frame(rt_frame, bg=self.C_CARD_BG)
        rt_row1.pack(anchor="w")
        for chip in ["Small Dog Room", "Medium Dog Room"]:
            self._add_chip(rt_row1, chip, group="room_type")
        rt_row2 = tk.Frame(rt_frame, bg=self.C_CARD_BG)
        rt_row2.pack(anchor="w", pady=(int(3*s), 0))
        for chip in ["Large Dog Room", "Cat Room", "Family Room"]:
            self._add_chip(rt_row2, chip, group="room_type")

        row6 = tk.Frame(form_frame, bg=self.C_CARD_BG)
        row6.pack(fill=tk.X, padx=form_pad, pady=(0, int(10*s)))

        # Pack svc_price_f first on the RIGHT so it is guaranteed full width and never cut off
        svc_price_f = tk.Frame(row6, bg=self.C_CARD_BG)
        svc_price_f.pack(side=tk.RIGHT, padx=(int(10*s), 0), anchor="ne")
        tk.Label(svc_price_f, text="Price / times", font=self.F_LABEL, bg=self.C_CARD_BG, fg=self.C_TEXT).pack(anchor="w")

        # Quantity selector row: [-]  Qty  [+]
        qty_row = tk.Frame(svc_price_f, bg=self.C_CARD_BG)
        qty_row.pack(anchor="w", pady=(int(2*s), int(4*s)))

        self.service_quantity_var = tk.IntVar(value=1)

        # Helper to change quantity
        def change_qty(delta):
            new_qty = self.service_quantity_var.get() + delta
            if new_qty >= 1:
                self.service_quantity_var.set(new_qty)
                qty_val_lbl.config(text=str(new_qty))
                self._update_service_price_display()

        # Draw elegant circular buttons for - and +
        btn_dec = tk.Canvas(qty_row, width=int(24*s), height=int(24*s), bg=self.C_CARD_BG, highlightthickness=0)
        btn_dec.pack(side=tk.LEFT)
        def draw_dec(event=None):
            btn_dec.delete("all")
            _round_rect(btn_dec, 0, 0, int(24*s), int(24*s), radius=int(12*s), fill="#F2F2F2")
            btn_dec.create_text(int(12*s), int(12*s), text="-", font=("Arial", int(14*s), "bold"), fill=self.C_TEXT)
        draw_dec()
        btn_dec.bind("<Button-1>", lambda e: change_qty(-1))

        qty_val_lbl = tk.Label(qty_row, text="1", font=self.F_BTN, bg=self.C_CARD_BG, fg=self.C_TEXT, width=3)
        qty_val_lbl.pack(side=tk.LEFT, padx=int(4*s))

        btn_inc = tk.Canvas(qty_row, width=int(24*s), height=int(24*s), bg=self.C_CARD_BG, highlightthickness=0)
        btn_inc.pack(side=tk.LEFT)
        def draw_inc(event=None):
            btn_inc.delete("all")
            _round_rect(btn_inc, 0, 0, int(24*s), int(24*s), radius=int(12*s), fill="#F2F2F2")
            btn_inc.create_text(int(12*s), int(12*s), text="+", font=("Arial", int(14*s), "bold"), fill=self.C_TEXT)
        draw_inc()
        btn_inc.bind("<Button-1>", lambda e: change_qty(1))

        # Price Display row below the quantity selector
        pv_svc = tk.Frame(svc_price_f, bg=self.C_CARD_BG)
        pv_svc.pack(anchor="w")
        self._service_price_label = tk.Label(pv_svc, text="", font=self.F_PRICE,
                                             bg=self.C_CARD_BG, fg="#6BA52F")
        self._service_price_label.pack(side=tk.LEFT)
        tk.Label(pv_svc, text=" total", font=self.F_LABEL, bg=self.C_CARD_BG, fg=self.C_TEXT).pack(side=tk.LEFT)

        # Pack svc_frame on the LEFT to fill remaining space
        svc_frame = tk.Frame(row6, bg=self.C_CARD_BG)
        svc_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, int(10*s)))
        tk.Label(svc_frame, text="Service", font=self.F_LABEL, bg=self.C_CARD_BG, fg=self.C_TEXT).pack(anchor="w")
        svc_row1 = tk.Frame(svc_frame, bg=self.C_CARD_BG)
        svc_row1.pack(anchor="w", pady=(int(4*s), 0))
        for chip in ["Grooming", "Daycare", "Pickup"]:
            self._add_chip(svc_row1, chip, group="service", value=chip.lower())
        svc_row2 = tk.Frame(svc_frame, bg=self.C_CARD_BG)
        svc_row2.pack(anchor="w", pady=(int(3*s), 0))
        for chip in ["Dropoff", "Swimming", "Walk"]:
            self._add_chip(svc_row2, chip, group="service", value=chip.lower())

        # Room chips waterfall container (hidden initially, shown when room type selected)
        self._room_chips_container = tk.Frame(form_frame, bg=self.C_CARD_BG, highlightthickness=0)
        # Add Specific room header label so it hides/shows dynamically along with the chips
        tk.Label(self._room_chips_container, text="Specific room", font=self.F_LABEL,
                 bg=self.C_CARD_BG, fg=self.C_TEXT).pack(anchor="w", pady=(0, int(4*s)))
        self._room_chips_inner = tk.Frame(self._room_chips_container, bg=self.C_CARD_BG)
        self._room_chips_inner.pack(fill=tk.X, padx=0, pady=(0, int(6*s)))

        # Trace room_type changes → update price & available rooms
        self.choice_vars["room_type"].trace_add("write", self._on_room_type_changed)
        self._on_room_type_changed()

        # Trace service changes → update service price display
        self.choice_vars["service"].trace_add("write", self._on_service_changed)
        self._update_service_price_display()

        row7 = tk.Frame(form_frame, bg=self.C_CARD_BG)
        row7.pack(fill=tk.X, padx=form_pad, pady=(0, int(10*s)))
        self._add_labeled_entry(row7, "Check in", "2026-05-20", side=tk.LEFT, expand=True, key="check_in")
        self._add_labeled_entry(row7, "Check out", "2026-05-23", side=tk.LEFT, expand=True, key="check_out")
        # Date validation indicator
        ci_entry = self.entries["check_in"]
        co_entry = self.entries["check_out"]
        self._date_err = tk.Label(ci_entry.master.master, text="ngày tháng không hợp lệ",
                            font=self.F_LABEL, bg=self.C_CARD_BG, fg="#E74C3C")
        def _validate_dates(_event=None):
            ci = ci_entry.get()
            co = co_entry.get()
            ci_ph = self.placeholders.get("check_in", "")
            co_ph = self.placeholders.get("check_out", "")
            if ci == ci_ph or co == co_ph or not ci.strip() or not co.strip():
                self._date_err.pack_forget()
                return
            try:
                ci_dt = self._parse_datetime(ci)
                co_dt = self._parse_datetime(co)
                if ci_dt.date() < datetime.now().date():
                    self._date_err.pack(anchor="w")
                elif co_dt <= ci_dt:
                    self._date_err.pack(anchor="w")
                else:
                    self._date_err.pack_forget()
            except ValueError:
                self._date_err.pack(anchor="w")
        ci_entry.bind("<KeyRelease>", _validate_dates, add="+")
        ci_entry.bind("<<Paste>>", _validate_dates, add="+")
        co_entry.bind("<KeyRelease>", _validate_dates, add="+")
        co_entry.bind("<<Paste>>", _validate_dates, add="+")

        # Confirm button (rounded via Canvas)
        btn_h = int(46 * s)
        btn_cv = tk.Canvas(form_frame, height=btn_h, bg=self.C_CARD_BG, highlightthickness=0)
        btn_cv.pack(pady=(int(14*s), int(20*s)))
        def _draw_confirm_btn(event=None):
            btn_cv.delete("cbtn")
            cw = btn_cv.winfo_width()
            ch = btn_cv.winfo_height()
            if cw > 1 and ch > 1:
                bw = int(180 * s)
                bx = (cw - bw) // 2
                _round_rect(btn_cv, bx, 0, bx + bw, ch, radius=ch//2, fill=self.C_CONFIRM, tags="cbtn")
                btn_cv.create_text(cw//2, ch//2, text="Confirm", font=self.F_BTN, fill="white", tags="cbtn")
        btn_cv.bind("<Configure>", _draw_confirm_btn)
        btn_cv.bind("<Button-1>", self._on_confirm)

        # Error label (hidden by default, shows red text on validation failure)
        self._confirm_err = tk.Label(form_frame, text="", font=self.F_LABEL,
                                     bg=self.C_CARD_BG, fg="#E74C3C")
        self._confirm_err.pack(pady=(0, int(10*s)))

        # === BOTTOM BANNER (image + text overlay) ===
        _dir = os.path.dirname(__file__)
        banner_path = os.path.join(_dir, "image", "booking.jpg")
        bw_base = int(self.BASE_W - self.BASE_SIDE_W - pad_x * 2 / s)
        bh_base = 280  # larger cat image
        banner_tk = self.create_rounded_image(banner_path, bw_base, bh_base, radius=20)
        self.images.append(banner_tk)

        bh = int(bh_base * s)
        banner_cv = tk.Canvas(inner, height=bh, bg=self.C_BG, highlightthickness=0)
        banner_cv.pack(fill=tk.X, padx=pad_x, pady=(0, int(15*s)))
        quote_font = ("Arial Rounded MT Bold", max(12, int(18 * s)), "bold")

        def _draw_banner(event=None):
            banner_cv.delete("banner")
            cw = banner_cv.winfo_width()
            ch = banner_cv.winfo_height()
            if cw > 1 and ch > 1:
                banner_cv.create_image(cw // 2, ch // 2, image=banner_tk, tags="banner")
                # 2-line quote at top-left corner of the banner
                banner_cv.create_text(int(24 * s), int(22 * s),
                                      text='"Until one has loved an animal,\na part of one\'s soul remains unawakened"',
                                      font=quote_font, fill="white", anchor="nw", tags="banner")
        banner_cv.bind("<Configure>", _draw_banner)

    # =====================================================
    # PRICE HELPERS
    # =====================================================
    def _price_text(self):
        room_type = self.choice_vars["room_type"].get()
        try:
            price = self.backend.get_room_type_price(room_type)
        except Exception:
            price = None
        if price is None:
            defaults = {"Small Dog Room": 875000, "Medium Dog Room": 950000,
                        "Large Dog Room": 1050000, "Cat Room": 800000, "Family Room": 1500000}
            price = defaults.get(room_type, 875000)
        return f"{int(price):,}đ"

    def _on_room_type_changed(self, *_args):
        if self._price_label:
            self._price_label.config(text=self._price_text())
        room_type = self.choice_vars["room_type"].get()
        try:
            rooms = self.backend.get_available_rooms(room_type)
        except Exception:
            rooms = []
        self._rebuild_room_chips(rooms)

    def _service_price_text(self):
        service_name = self.choice_vars["service"].get()
        qty = getattr(self, "service_quantity_var", None)
        qty_val = qty.get() if qty else 1
        try:
            price = self.backend.get_service_price(service_name)
        except Exception:
            price = None
        if price is None:
            defaults = {"grooming": 150000, "daycare": 120000,
                        "pickup": 50000, "dropoff": 50000,
                        "swimming": 100000, "walk": 80000}
            price = defaults.get(service_name, 150000)
        total = price * qty_val
        return f"{int(total):,}đ"

    def _on_service_changed(self, *_args):
        self._update_service_price_display()

    def _update_service_price_display(self):
        if hasattr(self, "_service_price_label") and self._service_price_label:
            self._service_price_label.config(text=self._service_price_text())

    def _rebuild_room_chips(self, rooms):
        s = self._s
        for w in self._room_chips_inner.winfo_children():
            w.destroy()

        if not rooms:
            self._room_chips_container.pack_forget()
            return

        self._selected_room_var.set("")
        self._room_chips = []
        chip_frame = tk.Frame(self._room_chips_inner, bg=self.C_CARD_BG)
        chip_frame.pack(anchor="w")
        per_row = 5

        for i, rid in enumerate(rooms):
            if i > 0 and i % per_row == 0:
                chip_frame = tk.Frame(self._room_chips_inner, bg=self.C_CARD_BG)
                chip_frame.pack(anchor="w", pady=(int(4*s), 0))

            chip_h = int(36 * s)
            chip_w = int(80 * s)
            cv = tk.Canvas(chip_frame, width=chip_w, height=chip_h,
                           bg=self.C_CARD_BG, highlightthickness=0)
            cv.pack(side=tk.LEFT, padx=(0, int(8*s)))

            def draw_chip(cv=cv, rid=rid):
                cv.delete("all")
                r = chip_h // 2
                active = (self._selected_room_var.get() == rid)
                if active:
                    # Match active capsule: fill with C_ACTIVE, white text
                    _round_rect(cv, 0, 0, chip_w, chip_h, radius=r, fill=self.C_ACTIVE)
                    cv.create_text(chip_w//2, chip_h//2, text=rid,
                                   font=self.F_BTN, fill="white")
                else:
                    _round_rect(cv, 0, 0, chip_w, chip_h, radius=r,
                                fill=self.C_CHIP_BORDER)
                    _round_rect(cv, 1, 1, chip_w-1, chip_h-1, radius=max(1, r-1),
                                fill=self.C_WHITE, outline="")
                    cv.create_text(chip_w//2, chip_h//2, text=rid,
                                   font=self.F_BTN, fill=self.C_TEXT_LIGHT)

            draw_chip()
            self._room_chips.append(draw_chip)

            def on_click(_e=None, rid=rid):
                self._selected_room_var.set(rid)
                for fn in self._room_chips:
                    fn()

            cv.bind("<Button-1>", lambda e, rid=rid: on_click(rid=rid))

        self._room_chips_container.pack(fill=tk.X, padx=int(36*s),
                                        pady=(0, int(10*s)))

    # =====================================================
    # FORM HELPERS
    # =====================================================
    def _add_section_label(self, parent, text, padx):
        s = self._s
        f = tk.Frame(parent, bg=self.C_CARD_BG)
        f.pack(fill=tk.X, padx=padx, pady=(int(18*s), int(10*s)))
        tk.Label(f, text=text, font=self.F_SECTION, bg=self.C_CARD_BG, fg=self.C_TEXT).pack(anchor="w")
        sep = tk.Frame(f, bg=self.C_DIVIDER, height=2)
        sep.pack(fill=tk.X, pady=(int(8*s), 0))

    def _add_labeled_entry(self, parent, label, placeholder, side=tk.LEFT, expand=False, full=False, key=None):
        s = self._s
        f = tk.Frame(parent, bg=self.C_CARD_BG)
        if full:
            f.pack(fill=tk.X)
        else:
            f.pack(side=side, fill=tk.X, expand=expand, padx=(0, int(10*s)))
        tk.Label(f, text=label, font=self.F_LABEL, bg=self.C_CARD_BG, fg=self.C_TEXT).pack(anchor="w")
        # Capsule input: white bg canvas, draw rounded-rect border outline
        entry_h = int(48 * s)
        border_cv = tk.Canvas(f, height=entry_h, bg=self.C_CARD_BG, highlightthickness=0)
        border_cv.pack(fill=tk.X, pady=(int(5*s), 0))
        entry = tk.Entry(border_cv, font=self.F_INPUT, relief=tk.FLAT, bg="white",
                         fg=self.C_TEXT, highlightthickness=0,
                         insertbackground=self.C_TEXT)
        entry.insert(0, placeholder)
        entry.config(fg=self.C_PLACEHOLDER)
        entry.bind("<FocusIn>", lambda e, en=entry, ph=placeholder: self._clear_placeholder(en, ph))
        entry.bind("<FocusOut>", lambda e, en=entry, ph=placeholder: self._set_placeholder(en, ph))
        win_id = border_cv.create_window(int(6*s), int(8*s), window=entry, anchor="w", tags="entry_win")
        def _draw_entry_border(event=None):
            border_cv.delete("efill")
            cw = border_cv.winfo_width()
            ch = border_cv.winfo_height()
            if cw > 1 and ch > 1:
                r = ch // 2
                bw = max(1, int(1.5*s))
                _round_rect(border_cv, 0, 0, cw, ch, radius=r, fill=self.C_BORDER, tags="efill")
                _round_rect(border_cv, bw, bw, cw-bw, ch-bw, radius=max(1, r-bw), fill="white", tags="efill")
                border_cv.itemconfig(win_id, width=cw - int(26*s))
                border_cv.coords(win_id, int(10*s), ch // 2)
        border_cv.bind("<Configure>", _draw_entry_border)
        if key:
            self.entries[key] = entry
            self.placeholders[key] = placeholder
        return entry

    def _entry_value(self, key):
        entry = self.entries.get(key)
        if entry is None:
            return ""
        value = entry.get().strip()
        placeholder = self.placeholders.get(key, "")
        if value == placeholder:
            return ""
        return value

    def _add_autocomplete(self, entry_key, suggestions, extract=None):
        """Add autocomplete dropdown to an entry.

        Args:
            entry_key: key in self.entries
            suggestions: list of suggestion strings
            extract: optional callable(typed_text) -> (prefix, search_term)
                     prefix is prepended back on confirm (e.g. house number)
        """
        entry = self.entries.get(entry_key)
        if not entry:
            return

        if extract is None:
            extract = lambda t: ("", t)

        def _norm(t):
            return unicodedata.normalize('NFKD', t).encode('ascii', 'ignore').decode('ascii').lower()

        state = {"win": None, "lb": None, "sel": -1, "prefix": ""}

        def hide():
            if state["win"]:
                state["win"].destroy()
                state["win"] = None
                state["lb"] = None
            state["sel"] = -1

        def show(matches):
            hide()
            win = tk.Toplevel(self)
            win.wm_overrideredirect(True)
            win.configure(bg=self.C_BORDER)
            try:
                win.attributes("-topmost", True)
                win.attributes("-focusable", False)
            except tk.TclError:
                pass

            lb = tk.Listbox(win, font=self.F_INPUT, relief=tk.FLAT,
                            bg="white", fg=self.C_TEXT,
                            selectbackground=self.C_ACTIVE,
                            selectforeground="white",
                            highlightthickness=0, borderwidth=0,
                            activestyle="none", cursor="hand2")
            lb.pack(fill=tk.BOTH, expand=True, padx=1, pady=1)
            for m in matches:
                lb.insert(tk.END, m)

            entry.update_idletasks()
            x = entry.winfo_rootx()
            y = entry.winfo_rooty() + entry.winfo_height()
            w = max(entry.master.winfo_width(), 200)
            ih = min(len(matches), 6) * 24 + 4
            win.geometry(f"{w}x{ih}+{x}+{y}")
            win.lift()

            def on_click(_event=None):
                if lb.curselection():
                    val = lb.get(lb.curselection()[0])
                    entry.delete(0, tk.END)
                    entry.insert(0, state["prefix"] + val)
                    entry.config(fg=self.C_TEXT)
                    entry.event_generate("<<AutocompleteConfirm>>")
                    hide()
                    entry.focus_set()

            lb.bind("<ButtonRelease-1>", on_click)
            state["win"] = win
            state["lb"] = lb
            state["sel"] = -1

        def select(delta):
            if not state["lb"]:
                return
            sz = state["lb"].size()
            if sz == 0:
                return
            n = state["sel"] + delta
            n = max(0, min(n, sz - 1))
            state["lb"].selection_clear(0, sz - 1)
            state["lb"].selection_set(n)
            state["lb"].activate(n)
            state["sel"] = n

        def confirm():
            if state["lb"] and state["sel"] >= 0:
                val = state["lb"].get(state["sel"])
                entry.delete(0, tk.END)
                entry.insert(0, state["prefix"] + val)
                entry.config(fg=self.C_TEXT)
            entry.event_generate("<<AutocompleteConfirm>>")
            hide()
            entry.focus_set()

        def on_keyrelease(event):
            if event.keysym == "Down":
                if not state["lb"]:
                    typed = entry.get()
                    ph = self.placeholders.get(entry_key, "")
                    if typed.strip() and typed != ph:
                        prefix, search = extract(typed)
                        if search.strip():
                            matches = [s for s in suggestions if _norm(search) in _norm(s)]
                            if matches:
                                state["prefix"] = prefix
                                show(matches)
                                select(0)
                else:
                    select(1)
                return "break"
            elif event.keysym == "Up":
                if state["lb"]:
                    select(-1)
                return "break"
            elif event.keysym == "Return":
                confirm()
                return "break"
            elif event.keysym == "Escape":
                hide()
                return "break"
            elif event.keysym in ("Tab", "Shift_L", "Shift_R", "Control_L", "Control_R",
                                 "Alt_L", "Alt_R", "Caps_Lock", "Meta_L", "Meta_R",
                                 "Left", "Right"):
                return

            typed = entry.get()
            ph = self.placeholders.get(entry_key, "")
            if not typed.strip() or typed == ph:
                hide()
                return

            prefix, search = extract(typed)
            if not search.strip():
                hide()
                return

            matches = [s for s in suggestions if _norm(search) in _norm(s)]
            if matches:
                state["prefix"] = prefix
                show(matches)
                select(0)
            else:
                hide()

        def on_focusout(_event):
            entry.after(200, hide)

        entry.bind("<KeyRelease>", on_keyrelease, add="+")
        entry.bind("<FocusOut>", on_focusout, add="+")

    def _clear_placeholder(self, entry, placeholder):
        if entry.get() == placeholder:
            entry.delete(0, tk.END)
            entry.config(fg=self.C_TEXT)

    def _set_placeholder(self, entry, placeholder):
        if entry.get() == "":
            entry.insert(0, placeholder)
            entry.config(fg=self.C_PLACEHOLDER)

    def _add_chip(self, parent, text, active=False, group=None, value=None):
        s = self._s
        chip_value = value or text
        chip_h = int(42 * s)
        txt_len = len(text) if text else 3
        chip_w = int((txt_len * 18 + 36) * s)
        cv = tk.Canvas(parent, width=chip_w, height=chip_h,
                       bg=self.C_CARD_BG, highlightthickness=0)
        cv.pack(side=tk.LEFT, padx=(0, int(12*s)), pady=(int(4*s), 0))
        def _draw_chip(event=None):
            cv.delete("chip")
            cw = cv.winfo_width()
            ch = cv.winfo_height()
            if cw > 1 and ch > 1:
                r = ch // 2
                active_now = self.choice_vars[group].get() == chip_value if group else active
                if active_now:
                    _round_rect(cv, 0, 0, cw, ch, radius=r, fill=self.C_ACTIVE, tags="chip")
                    cv.create_text(cw//2, ch//2, text=text, font=self.F_BTN, fill="white", tags="chip")
                else:
                    # Capsule: border color outer + white inner → clean 1px border
                    _round_rect(cv, 0, 0, cw, ch, radius=r, fill=self.C_CHIP_BORDER, tags="chip")
                    _round_rect(cv, 1, 1, cw-1, ch-1, radius=max(1, r-1), fill="white", tags="chip")
                    cv.create_text(cw//2, ch//2, text=text, font=self.F_BTN, fill=self.C_TEXT_LIGHT, tags="chip")
        cv.bind("<Configure>", _draw_chip)
        if group:
            self.chip_groups.setdefault(group, []).append(_draw_chip)

            def _select(_event=None):
                self.choice_vars[group].set(chip_value)
                for redraw in self.chip_groups.get(group, []):
                    redraw()

            cv.bind("<Button-1>", _select)
        else:
            cv.bind("<Button-1>", lambda e: None)
        return cv

    def _add_toggle(self, parent, key=None):
        s = self._s
        var = tk.BooleanVar(value=False)
        tw, th = int(52*s), int(30*s)
        cv = tk.Canvas(parent, width=tw, height=th,
                       bg=self.C_CARD_BG, highlightthickness=0)
        cv.pack(anchor="w", pady=(int(4*s), 0))

        def draw_toggle():
            cv.delete("all")
            w, h = tw, th
            r = h // 2
            pad = int(2*s)
            thumb_d = h - 2*pad
            if var.get():
                _round_rect(cv, 0, 0, w, h, radius=r, fill=self.C_ACTIVE)
                cv.create_oval(w - h + pad, pad, w - pad, h - pad,
                              fill="white", outline="")
            else:
                _round_rect(cv, 0, 0, w, h, radius=r, fill=self.C_TOGGLE_OFF)
                cv.create_oval(pad, pad, h - pad, h - pad,
                              fill="white", outline="")

        draw_toggle()
        cv.bind("<Button-1>", lambda e: (var.set(not var.get()), draw_toggle()))
        if key:
            self.toggle_vars[key] = var
        return var

    def _collect_form_data(self):
        return {
            "phone": self._entry_value("phone"),
            "full_name": self._entry_value("full_name"),
            "address": self._entry_value("address"),
            "district": self._entry_value("district"),
            "membership": self.choice_vars["membership"].get(),
            "pet_name": self._entry_value("pet_name"),
            "species": self.choice_vars["species"].get(),
            "sterilized": self.toggle_vars.get("sterilized", tk.BooleanVar(value=False)).get(),
            "breed": self._entry_value("breed"),
            "weight": self._entry_value("weight"),
            "gender": self.choice_vars["gender"].get(),
            "vaccinated": self.toggle_vars.get("vaccinated", tk.BooleanVar(value=False)).get(),
            "health_condition": self._entry_value("health_condition"),
            "behaviour_note": self._entry_value("behaviour_note"),
            "special_requirement": self._entry_value("special_requirement"),
            "room_type": self.choice_vars["room_type"].get(),
            "room": self._selected_room_var.get().replace("R-", "").strip(),
            "service": self.choice_vars["service"].get(),
            "service_quantity": self.service_quantity_var.get() if hasattr(self, "service_quantity_var") else 1,
            "check_in": self._entry_value("check_in"),
            "check_out": self._entry_value("check_out"),
        }

    def _on_confirm(self, _event=None):
        self._confirm_err.config(text="")
        try:
            result = self.backend.create_booking(self._collect_form_data())
            messagebox.showinfo(
                "Success",
                (
                    f"Booking #{result['booking_id']} confirmed.\n"
                    f"Room: R-{result['room_id']:02d}\n"
                    f"Type: {result['room_type']}"
                ),
                parent=self,
            )
        except Exception as exc:
            self._confirm_err.config(text="⚠ Thông tin không hợp lệ")


if __name__ == "__main__":
    app = BookingDashboard()
    app.mainloop()
