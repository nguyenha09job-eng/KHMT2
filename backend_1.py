from database import DatabaseConnection
from datetime import date, timedelta


def format_large_number(num):
    """Format số lớn: >= 1B → B, >= 1M → M, >= 1K → K, còn lại giữ nguyên."""
    if num >= 1_000_000_000:
        s = f"{num / 1_000_000_000:.1f}".rstrip("0").rstrip(".")
        return f"{s}B"
    if num >= 1_000_000:
        s = f"{num / 1_000_000:.1f}".rstrip("0").rstrip(".")
        return f"{s}M"
    if num >= 1_000:
        s = f"{num / 1_000:.1f}".rstrip("0").rstrip(".")
        return f"{s}K"
    return f"{num:,.0f}"


class DashboardBackend:
    """Backend xử lý dữ liệu cho màn hình Dashboard."""

    def __init__(self):
        self.db = DatabaseConnection()

    # ------------------------------------------------------------------
    # 1. Currently Staying – tổng pet đang lưu trú, tách riêng chó / mèo
    # ------------------------------------------------------------------
    def get_currently_staying(self):
        total = self.db.fetch_one("""
            SELECT COUNT(*) AS cnt
            FROM bookings b
            JOIN booking_statuses bs ON bs.status_id = b.booking_status_id
            WHERE bs.status_name = 'Staying'
              AND DATE(b.check_in) <= CURDATE()
              AND DATE(b.check_out) >= CURDATE()
        """)
        dogs = self.db.fetch_one("""
            SELECT COUNT(*) AS cnt
            FROM bookings b
            JOIN booking_statuses bs ON bs.status_id = b.booking_status_id
            JOIN pets p ON p.pet_id = b.pet_id
            WHERE bs.status_name = 'Staying'
              AND DATE(b.check_in) <= CURDATE()
              AND DATE(b.check_out) >= CURDATE()
              AND LOWER(p.species) = 'dog'
        """)
        cats = self.db.fetch_one("""
            SELECT COUNT(*) AS cnt
            FROM bookings b
            JOIN booking_statuses bs ON bs.status_id = b.booking_status_id
            JOIN pets p ON p.pet_id = b.pet_id
            WHERE bs.status_name = 'Staying'
              AND DATE(b.check_in) <= CURDATE()
              AND DATE(b.check_out) >= CURDATE()
              AND LOWER(p.species) = 'cat'
        """)
        t = total["cnt"] if total else 0
        d = dogs["cnt"] if dogs else 0
        c = cats["cnt"] if cats else 0
        return {
            "total": t,
            "dogs": d,
            "cats": c,
            "display": format_large_number(t),
            "subtext": f"{d} dogs - {c} cats",
        }

    # ------------------------------------------------------------------
    # 2. Available Rooms – phòng còn trống / tổng phòng
    # ------------------------------------------------------------------
    def get_available_rooms(self):
        total = self.db.fetch_one("""
            SELECT COUNT(*) AS cnt
            FROM rooms
            WHERE is_active = 1
        """)
        occupied = self.db.fetch_one("""
            SELECT COUNT(DISTINCT b.room_id) AS cnt
            FROM bookings b
            JOIN booking_statuses bs ON bs.status_id = b.booking_status_id
            WHERE bs.status_name = 'Staying'
              AND DATE(b.check_in) <= CURDATE()
              AND DATE(b.check_out) >= CURDATE()
        """)
        t = total["cnt"] if total else 0
        o = occupied["cnt"] if occupied else 0
        a = t - o
        return {
            "available": a,
            "total": t,
            "display": format_large_number(a),
            "subtext": f"out of {t} rooms",
        }

    # ------------------------------------------------------------------
    # 3. Monthly Revenue – doanh thu tháng hiện tại + % so với tháng trước
    # ------------------------------------------------------------------
    def get_monthly_revenue(self):
        today = date.today()
        first_this_month = today.replace(day=1)
        last_prev_month = first_this_month - timedelta(days=1)
        first_prev_month = last_prev_month.replace(day=1)

        this_month = self.db.fetch_one("""
            SELECT COALESCE(SUM(total_amount), 0) AS total
            FROM billing
            WHERE payment_date >= %s AND payment_date < %s
        """, (
            first_this_month.strftime("%Y-%m-%d"),
            today.strftime("%Y-%m-%d") + " 23:59:59",
        ))

        prev_month = self.db.fetch_one("""
            SELECT COALESCE(SUM(total_amount), 0) AS total
            FROM billing
            WHERE payment_date >= %s AND payment_date < %s
        """, (
            first_prev_month.strftime("%Y-%m-%d"),
            first_this_month.strftime("%Y-%m-%d"),
        ))

        cur = float(this_month["total"]) if this_month else 0.0
        prev = float(prev_month["total"]) if prev_month else 0.0

        if prev > 0:
            pct = round((cur - prev) / prev * 100)
            sign = "+" if pct >= 0 else ""
            subtext = f"{sign}{pct}% vs last month"
        else:
            subtext = "0% vs last month"

        display = format_large_number(cur)

        return {
            "current": cur,
            "previous": prev,
            "display": display,
            "subtext": subtext,
        }

    # ------------------------------------------------------------------
    # 4. Check-outs Today – pet dự kiến check-out hôm nay
    # ------------------------------------------------------------------
    def get_checkouts_today(self):
        total = self.db.fetch_one("""
            SELECT COUNT(*) AS cnt
            FROM bookings b
            JOIN booking_statuses bs ON bs.status_id = b.booking_status_id
            WHERE DATE(b.check_out) = CURDATE()
              AND bs.status_name IN ('Staying', 'Pending')
        """)
        pending = self.db.fetch_one("""
            SELECT COUNT(*) AS cnt
            FROM bookings b
            JOIN booking_statuses bs ON bs.status_id = b.booking_status_id
            LEFT JOIN billing bl ON bl.booking_id = b.booking_id
            WHERE DATE(b.check_out) = CURDATE()
              AND bs.status_name IN ('Staying', 'Pending')
              AND bl.payment_id IS NULL
        """)
        t = total["cnt"] if total else 0
        p = pending["cnt"] if pending else 0
        return {
            "total": t,
            "pending_billing": p,
            "display": format_large_number(t),
            "subtext": "Pending billing" if p > 0 else "All billed",
        }

    # ------------------------------------------------------------------
    # 5. Active Bookings – danh sách booking đang hoạt động
    # ------------------------------------------------------------------
    def get_active_bookings(self):
        rows = self.db.fetch_all("""
            SELECT
                p.pet_name                AS pet,
                c.full_name               AS owner,
                DATE_FORMAT(b.check_in, '%d/%m')  AS check_in,
                DATE_FORMAT(b.check_out, '%d/%m') AS check_out,
                bs.status_name            AS status,
                CONCAT('R-', LPAD(r.room_id, 2, '0')) AS room
            FROM bookings b
            JOIN pets p             ON p.pet_id = b.pet_id
            JOIN customers c        ON c.customer_id = b.customer_id
            JOIN booking_statuses bs ON bs.status_id = b.booking_status_id
            JOIN rooms r            ON r.room_id = b.room_id
            WHERE bs.status_name IN ('Staying', 'Pending')
            ORDER BY b.check_in DESC
        """)
        return rows if rows else []

    # ------------------------------------------------------------------
    # 6. Today's Services – dịch vụ cần thực hiện trong ngày
    # ------------------------------------------------------------------
    def get_today_services(self):
        rows = self.db.fetch_all("""
            SELECT
                p.pet_name          AS pet,
                sc.service_type     AS service,
                CONCAT('R-', LPAD(r.room_id, 2, '0')) AS room,
                s.status            AS status,
                s.frequency_tag     AS frequency
            FROM services s
            JOIN bookings b ON b.booking_id = s.booking_id
            JOIN booking_statuses bs ON bs.status_id = b.booking_status_id
            JOIN pets p      ON p.pet_id = s.pet_id
            JOIN service_catalog sc ON sc.service_type_id = s.service_type_id
            JOIN rooms r     ON r.room_id = b.room_id
            WHERE s.service_date = CURDATE()
              AND bs.status_name = 'Staying'
            ORDER BY s.status, p.pet_name
        """)
        return rows if rows else []

    # ------------------------------------------------------------------
    # 7. Tổng hợp toàn bộ dữ liệu Dashboard trong 1 lần gọi
    # ------------------------------------------------------------------
    def get_all_dashboard_data(self):
        return {
            "currently_staying": self.get_currently_staying(),
            "available_rooms": self.get_available_rooms(),
            "monthly_revenue": self.get_monthly_revenue(),
            "checkouts_today": self.get_checkouts_today(),
            "active_bookings": self.get_active_bookings(),
            "today_services": self.get_today_services(),
        }


# ------------------------------------------------------------------
# TEST – chạy độc lập để kiểm tra dữ liệu trả về
# ------------------------------------------------------------------
if __name__ == "__main__":
    backend = DashboardBackend()

    print("=" * 60)
    print(" DASHBOARD DATA")
    print("=" * 60)

    data = backend.get_all_dashboard_data()

    cs = data["currently_staying"]
    print(f"\n[1] Currently Staying:  {cs['total']}  ({cs['subtext']})")

    ar = data["available_rooms"]
    print(f"[2] Available Rooms:    {ar['available']}  ({ar['subtext']})")

    mr = data["monthly_revenue"]
    print(f"[3] Monthly Revenue:    {mr['display']}  ({mr['subtext']})")

    co = data["checkouts_today"]
    print(f"[4] Check-outs Today:   {co['total']}  ({co['subtext']})")

    print("\n--- Active Bookings ---")
    for b in data["active_bookings"]:
        print(f"  {b['pet']:<10s} | {b['owner']:<12s} | "
              f"{b['check_in']} -> {b['check_out']} | {b['status']:<10s} | {b['room']}")

    print("\n--- Today's Services ---")
    for s in data["today_services"]:
        print(f"  {s['pet']:<10s} | {s['service']:<12s} | "
              f"{s['room']} | {s['status']:<10s} | {s['frequency']}")

import random
from datetime import datetime, timedelta

start_date = datetime(2025, 1, 15)
end_date = datetime(2025, 5, 19)


def rand_date():
    delta = (end_date - start_date).days
    d = start_date + timedelta(days=random.randint(0, delta))
    return d.strftime('%Y-%m-%d')


# =====================================================
# GENERATE CUSTOMERS
# =====================================================

with open('customers.sql', 'w', encoding='utf-8') as f:

    f.write("INSERT INTO customers(full_name, phone, address, district, join_date, last_active_date, total_spent) VALUES\n")

    rows = []

    for i in range(1, 2001):

        full_name = f"Customer {i}"
        phone = f"09{str(i).zfill(8)}"
        address = f"{i} Nguyen Trai"
        district = f"District {random.randint(1,12)}"
        join_date = rand_date()
        active_date = rand_date()
        spent = random.randint(500000, 12000000)

        row = f"('{full_name}','{phone}','{address}','{district}','{join_date}','{active_date}',{spent})"

        rows.append(row)

    f.write(',\n'.join(rows))
    f.write(';')


# =====================================================
# GENERATE PETS
# =====================================================

with open('pets.sql', 'w', encoding='utf-8') as f:

    f.write("INSERT INTO pets(customer_id, pet_name, species, breed, weight, age, gender, sterilized, health_condition, vaccinated, behaviour_note, special_requirement) VALUES\n")

    rows = []

    for i in range(1, 2501):

        customer_id = random.randint(1, 2000)

        if i % 3 == 0:
            species = 'cat'
            breed = 'British Shorthair'
            weight = round(random.uniform(2, 7), 2)
            pet_name = f'Cat_{i}'
        else:
            species = 'dog'
            breed = 'Poodle'
            weight = round(random.uniform(2, 30), 2)
            pet_name = f'Dog_{i}'

        age = random.randint(1, 12)
        gender = random.choice(['male', 'female'])
        sterilized = random.randint(0, 1)

        row = f"({customer_id},'{pet_name}','{species}','{breed}',{weight},{age},'{gender}',{sterilized},'Healthy',1,'Friendly','None')"

        rows.append(row)

    f.write(',\n'.join(rows))
    f.write(';')


# =====================================================
# GENERATE BOOKINGS
# =====================================================

with open('bookings.sql', 'w', encoding='utf-8') as f:

    f.write("INSERT INTO bookings(customer_id, pet_id, room_id, check_in, check_out, booking_status_id, notes) VALUES\n")

    rows = []

    for i in range(1, 4001):

        customer_id = random.randint(1, 2000)
        pet_id = random.randint(1, 2500)
        room_id = random.randint(1, 20)

        checkin_date = start_date + timedelta(days=random.randint(0, 110))
        checkout_date = checkin_date + timedelta(days=random.randint(2, 7))

        status = random.choice([1,2,3])

        row = (
            f"({customer_id},{pet_id},{room_id},"
            f"'{checkin_date.strftime('%Y-%m-%d %H:%M:%S')}',"
            f"'{checkout_date.strftime('%Y-%m-%d %H:%M:%S')}',"
            f"{status},'Generated booking')"
        )

        rows.append(row)

    f.write(',\n'.join(rows))
    f.write(';')


# =====================================================
# GENERATE SERVICES
# =====================================================

with open('services.sql', 'w', encoding='utf-8') as f:

    f.write("INSERT INTO services(booking_id, pet_id, service_type_id, quantity, service_date, frequency_tag, notes, status) VALUES\n")

    rows = []

    for i in range(1, 5001):

        booking_id = random.randint(1, 4000)
        pet_id = random.randint(1, 2500)
        service_type_id = random.randint(1, 6)
        quantity = random.randint(1, 3)

        row = (
            f"({booking_id},{pet_id},{service_type_id},{quantity},"
            f"'{rand_date()}','1 time/day','Generated service','done')"
        )

        rows.append(row)

    f.write(',\n'.join(rows))
    f.write(';')


# =====================================================
# GENERATE BILLING
# =====================================================

with open('billing.sql', 'w', encoding='utf-8') as f:

    f.write("INSERT INTO billing(booking_id, employee_id, total_amount, discount_amount, payment_date, payment_method_id, notes) VALUES\n")

    rows = []

    for i in range(1, 4001):

        booking_id = i
        employee_id = random.randint(1, 8)

        total_amount = random.randint(800000, 5000000)
        discount_amount = random.randint(0, 200000)

        row = (
            f"({booking_id},{employee_id},{total_amount},{discount_amount},"
            f"'{rand_date()}',{random.randint(1,3)},'Paid')"
        )

        rows.append(row)

    f.write(',\n'.join(rows))
    f.write(';')


# =====================================================
# GENERATE ATTENDANCE
# =====================================================

with open('attendance.sql', 'w', encoding='utf-8') as f:

    f.write("INSERT INTO attendance(employee_id, work_date, check_in, check_out, working_hours, overtime_hours, penalty, note) VALUES\n")

    rows = []

    for emp in range(1, 9):

        current = start_date

        while current <= end_date:

            work_date = current.strftime('%Y-%m-%d')

            row = (
                f"({emp},'{work_date}','{work_date} 08:00:00',"
                f"'{work_date} 17:00:00',9,{random.randint(0,2)},0,'Normal shift')"
            )

            rows.append(row)

            current += timedelta(days=1)

    f.write(',\n'.join(rows))
    f.write(';')


print('DONE GENERATING FULL SQL FILES')


