from datetime import date, timedelta
from decimal import Decimal

from database import DatabaseConnection


def format_large_number(num):
    """Format large numbers for the dashboard cards."""
    if num is None:
        num = 0

    if isinstance(num, Decimal):
        num = float(num)

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
    """Data layer for front_1.py using the PetHotel schema in khmt2 (1).sql."""

    def __init__(self, db=None):
        self.db = db or DatabaseConnection()

    def get_currently_staying(self):
        total = self.db.fetch_one(
            """
            SELECT COUNT(*) AS cnt
            FROM bookings b
            JOIN booking_statuses bs ON bs.status_id = b.booking_status_id
            WHERE bs.status_name = 'checked_in'
              AND b.check_in <= NOW()
              AND b.check_out >= NOW()
            """
        )
        dogs = self.db.fetch_one(
            """
            SELECT COUNT(*) AS cnt
            FROM bookings b
            JOIN booking_statuses bs ON bs.status_id = b.booking_status_id
            JOIN pets p ON p.pet_id = b.pet_id
            WHERE bs.status_name = 'checked_in'
              AND b.check_in <= NOW()
              AND b.check_out >= NOW()
              AND LOWER(p.species) = 'dog'
            """
        )
        cats = self.db.fetch_one(
            """
            SELECT COUNT(*) AS cnt
            FROM bookings b
            JOIN booking_statuses bs ON bs.status_id = b.booking_status_id
            JOIN pets p ON p.pet_id = b.pet_id
            WHERE bs.status_name = 'checked_in'
              AND b.check_in <= NOW()
              AND b.check_out >= NOW()
              AND LOWER(p.species) = 'cat'
            """
        )

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

    def get_available_rooms(self):
        total = self.db.fetch_one(
            """
            SELECT COUNT(*) AS cnt
            FROM rooms
            WHERE is_active = 1
            """
        )
        occupied = self.db.fetch_one(
            """
            SELECT COUNT(DISTINCT b.room_id) AS cnt
            FROM bookings b
            JOIN booking_statuses bs ON bs.status_id = b.booking_status_id
            WHERE bs.status_name IN ('booked', 'checked_in')
              AND b.check_in <= NOW()
              AND b.check_out >= NOW()
            """
        )

        t = total["cnt"] if total else 0
        o = occupied["cnt"] if occupied else 0
        available = max(t - o, 0)

        return {
            "available": available,
            "total": t,
            "display": format_large_number(available),
            "subtext": f"out of {t} rooms",
        }

    def get_monthly_revenue(self):
        today = date.today()
        first_this_month = today.replace(day=1)
        last_prev_month = first_this_month - timedelta(days=1)
        first_prev_month = last_prev_month.replace(day=1)

        this_month = self.db.fetch_one(
            """
            SELECT COALESCE(SUM(total_amount), 0) AS total
            FROM billing
            WHERE payment_date >= %s
              AND payment_date < %s
            """,
            (
                first_this_month.strftime("%Y-%m-%d"),
                (today + timedelta(days=1)).strftime("%Y-%m-%d"),
            ),
        )
        prev_month = self.db.fetch_one(
            """
            SELECT COALESCE(SUM(total_amount), 0) AS total
            FROM billing
            WHERE payment_date >= %s
              AND payment_date < %s
            """,
            (
                first_prev_month.strftime("%Y-%m-%d"),
                first_this_month.strftime("%Y-%m-%d"),
            ),
        )

        cur = float(this_month["total"]) if this_month else 0.0
        prev = float(prev_month["total"]) if prev_month else 0.0

        if prev > 0:
            pct = round((cur - prev) / prev * 100)
            sign = "+" if pct >= 0 else ""
            subtext = f"{sign}{pct}% vs last month"
        else:
            subtext = "0% vs last month"

        return {
            "current": cur,
            "previous": prev,
            "display": format_large_number(cur),
            "subtext": subtext,
        }

    def get_checkouts_today(self):
        total = self.db.fetch_one(
            """
            SELECT COUNT(*) AS cnt
            FROM bookings b
            JOIN booking_statuses bs ON bs.status_id = b.booking_status_id
            WHERE DATE(b.check_out) = CURDATE()
              AND bs.status_name IN ('booked', 'checked_in')
            """
        )
        pending = self.db.fetch_one(
            """
            SELECT COUNT(*) AS cnt
            FROM bookings b
            JOIN booking_statuses bs ON bs.status_id = b.booking_status_id
            LEFT JOIN billing bl ON bl.booking_id = b.booking_id
            WHERE DATE(b.check_out) = CURDATE()
              AND bs.status_name IN ('booked', 'checked_in')
              AND (bl.payment_id IS NULL OR bl.payment_method_id IS NULL)
            """
        )

        t = total["cnt"] if total else 0
        p = pending["cnt"] if pending else 0

        return {
            "total": t,
            "pending_billing": p,
            "display": format_large_number(t),
            "subtext": "Pending billing" if p > 0 else "All billed",
        }

    def get_active_bookings(self):
        rows = self.db.fetch_all(
            """
            SELECT
                p.pet_name AS pet,
                c.full_name AS owner,
                DATE_FORMAT(b.check_in, '%d/%m') AS check_in,
                DATE_FORMAT(b.check_out, '%d/%m') AS check_out,
                bs.status_name AS status,
                CONCAT('R-', LPAD(r.room_id, 2, '0')) AS room
            FROM bookings b
            JOIN pets p ON p.pet_id = b.pet_id
            JOIN customers c ON c.customer_id = b.customer_id
            JOIN booking_statuses bs ON bs.status_id = b.booking_status_id
            JOIN rooms r ON r.room_id = b.room_id
            WHERE bs.status_name IN ('checked_in', 'booked')
            ORDER BY b.check_in DESC
            LIMIT 6
            """
        )
        return rows or []

    def get_today_services(self):
        rows = self.db.fetch_all(
            """
            SELECT
                p.pet_name AS pet,
                sc.service_type AS service,
                CONCAT('R-', LPAD(r.room_id, 2, '0')) AS room,
                s.status AS status,
                COALESCE(s.frequency_tag, CONCAT(s.quantity, 'x')) AS frequency
            FROM services s
            JOIN bookings b ON b.booking_id = s.booking_id
            JOIN booking_statuses bs ON bs.status_id = b.booking_status_id
            JOIN pets p ON p.pet_id = s.pet_id
            JOIN service_catalog sc ON sc.service_type_id = s.service_type_id
            JOIN rooms r ON r.room_id = b.room_id
            WHERE s.service_date = CURDATE()
              AND bs.status_name IN ('booked', 'checked_in', 'completed')
            ORDER BY s.status, p.pet_name
            LIMIT 6
            """
        )
        return rows or []

    def get_all_dashboard_data(self):
        return {
            "currently_staying": self.get_currently_staying(),
            "available_rooms": self.get_available_rooms(),
            "monthly_revenue": self.get_monthly_revenue(),
            "checkouts_today": self.get_checkouts_today(),
            "active_bookings": self.get_active_bookings(),
            "today_services": self.get_today_services(),
        }


if __name__ == "__main__":
    backend = DashboardBackend()
    data = backend.get_all_dashboard_data()

    print("=" * 60)
    print(" DASHBOARD DATA")
    print("=" * 60)
    print(f"Currently staying: {data['currently_staying']['display']} ({data['currently_staying']['subtext']})")
    print(f"Available rooms:   {data['available_rooms']['display']} ({data['available_rooms']['subtext']})")
    print(f"Monthly revenue:   {data['monthly_revenue']['display']} ({data['monthly_revenue']['subtext']})")
    print(f"Check-outs today:  {data['checkouts_today']['display']} ({data['checkouts_today']['subtext']})")
