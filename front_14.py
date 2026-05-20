import tkinter as tk
from PIL import Image, ImageTk, ImageDraw
import os
import sys
import math
from datetime import datetime
from decimal import Decimal

from app_window import AppWindow
from database import DatabaseConnection
from navigation import bind_click, bind_nav_item, logout_to_login


class FuzzyInsightEngine:
    """Small rule-based fuzzy engine that turns report data into guidance."""

    def __init__(self, report_data):
        self.data = report_data

    @staticmethod
    def _clamp(value, low=0.0, high=1.0):
        return max(low, min(high, float(value)))

    @staticmethod
    def _tri(x, a, b, c):
        x = float(x)
        if x <= a or x >= c:
            return 0.0
        if x == b:
            return 1.0
        if x < b:
            return (x - a) / (b - a)
        return (c - x) / (c - b)

    @staticmethod
    def _trap(x, a, b, c, d):
        x = float(x)
        if a == b and x <= b:
            return 1.0
        if c == d and x >= c:
            return 1.0
        if x <= a or x >= d:
            return 0.0
        if b <= x <= c:
            return 1.0
        if x < b:
            return (x - a) / (b - a)
        return (d - x) / (d - c)

    @staticmethod
    def _defuzzify(rules, default=50):
        total_weight = sum(weight for weight, _value in rules)
        if total_weight <= 0:
            return default
        return round(sum(weight * value for weight, value in rules) / total_weight)

    @staticmethod
    def _parse_number(value):
        text = str(value or "").replace(",", "").strip()
        digits = []
        for char in text:
            if char.isdigit() or char in ".-":
                digits.append(char)
        try:
            return float("".join(digits)) if digits else 0.0
        except ValueError:
            return 0.0

    @classmethod
    def _parse_money(cls, value):
        text = str(value or "").replace(",", "").strip().upper()
        amount = cls._parse_number(text)
        if text.endswith("B"):
            return amount * 1_000_000_000
        if text.endswith("M"):
            return amount * 1_000_000
        if text.endswith("K"):
            return amount * 1_000
        return amount

    def _stat_value(self, label):
        for stat_label, value, _sub in self.data.get("stats", []):
            if stat_label == label:
                return value
        return 0

    def _trend_change(self):
        values = [
            float(value or 0)
            for label, value in self.data.get("bar_data", [])
            if label != "-"
        ]
        if len(values) < 2 or max(values) <= 0:
            return 0.0

        half = max(1, len(values) // 2)
        early = sum(values[:half]) / half
        late = sum(values[-half:]) / half
        baseline = max(early, late, 1.0)
        return (late - early) / baseline * 100

    @staticmethod
    def _top_segment(segments):
        valid = []
        for pct, _color, label in segments or []:
            name = str(label or "Unknown").split("\n")[0]
            if name.lower() == "no data":
                continue
            valid.append((float(pct or 0), name))
        if not valid:
            return "No data", 0.0
        pct, name = max(valid, key=lambda item: item[0])
        return name, pct

    @staticmethod
    def _top_payment(methods):
        valid = [(str(label or "Unknown"), float(pct or 0) * 100) for label, pct, _color in methods or []]
        if not valid:
            return "No data", 0.0
        return max(valid, key=lambda item: item[1])

    @staticmethod
    def _confidence(*memberships):
        return max(45, min(96, round(max(memberships or [0]) * 100)))

    @staticmethod
    def _insight(title, label, text, score, confidence, color, bg):
        return {
            "title": title,
            "label": label,
            "text": text,
            "score": int(score),
            "confidence": int(confidence),
            "color": color,
            "bg": bg,
        }

    def _revenue_momentum(self):
        change = self._trend_change()
        falling = self._trap(change, -100, -100, -28, -8)
        stable = self._tri(change, -18, 0, 18)
        rising = self._trap(change, 8, 28, 100, 100)
        score = self._defuzzify([(falling, 32), (stable, 62), (rising, 88)])
        confidence = self._confidence(falling, stable, rising)

        if rising >= stable and rising >= falling:
            return self._insight(
                "Revenue Momentum",
                "Rising",
                f"Late-period revenue is about {abs(change):.0f}% stronger than the early period. Keep staffing and add-on services ready for peaks.",
                score,
                confidence,
                "#5A8A1A",
                "#D4EDBA",
            )
        if falling >= stable:
            return self._insight(
                "Revenue Momentum",
                "Cooling",
                f"Revenue is about {abs(change):.0f}% softer near the end of this range. Check low days and test room-plus-service bundles.",
                score,
                confidence,
                "#C05070",
                "#F9D0D8",
            )
        return self._insight(
            "Revenue Momentum",
            "Stable",
            f"Revenue movement stays within about {abs(change):.0f}% across the period, so demand looks predictable.",
            score,
            confidence,
            "#8A6A1A",
            "#F7E4B5",
        )

    def _capacity_signal(self):
        occupancy = self._parse_number(self._stat_value("Room Occupancy"))
        low = self._trap(occupancy, 0, 0, 35, 52)
        healthy = self._tri(occupancy, 42, 68, 86)
        high = self._trap(occupancy, 76, 90, 100, 100)
        score = self._defuzzify([(low, 35), (healthy, 74), (high, 90)])
        confidence = self._confidence(low, healthy, high)
        rising = self._trap(self._trend_change(), 8, 28, 100, 100)
        tight_and_rising = min(high, rising)

        if tight_and_rising >= 0.4:
            text = f"Occupancy is tight at {occupancy:.0f}% while revenue is improving. Prioritize premium rooms and high-margin add-ons."
            label = "Premium Window"
            color, bg = "#5A8A1A", "#D4EDBA"
        elif high >= healthy and high >= low:
            text = f"Occupancy is high at {occupancy:.0f}%. Protect room availability and avoid over-discounting limited capacity."
            label = "Tight"
            color, bg = "#8A6A1A", "#F7E4B5"
        elif low >= healthy:
            text = f"Occupancy is only {occupancy:.0f}%. Use targeted offers to pull bookings into underused rooms."
            label = "Open Capacity"
            color, bg = "#C05070", "#F9D0D8"
        else:
            text = f"Occupancy sits around {occupancy:.0f}%, a healthy zone for balancing walk-ins, bookings, and service capacity."
            label = "Balanced"
            color, bg = "#4A7E78", "#D5F1EE"

        return self._insight("Capacity Signal", label, text, score, confidence, color, bg)

    def _mix_signal(self):
        service_name, service_pct = self._top_segment(self.data.get("service_segments", []))
        member_name, member_pct = self._top_segment(self.data.get("membership_segments", []))
        payment_name, payment_pct = self._top_payment(self.data.get("payment_methods", []))
        focus_candidates = [
            ("service", service_name, service_pct),
            ("membership", member_name, member_pct),
            ("payment", payment_name, payment_pct),
        ]
        focus_type, focus_name, focus_pct = max(focus_candidates, key=lambda item: item[2])
        diverse = self._trap(focus_pct, 0, 0, 38, 55)
        focused = self._trap(focus_pct, 50, 68, 100, 100)
        score = self._defuzzify([(diverse, 82), (focused, 55)], default=68)
        confidence = self._confidence(diverse, focused)

        if focused >= diverse:
            if focus_type == "service":
                text = f"Revenue mix leans toward {focus_name} at {focus_pct:.0f}%. Push one complementary service to reduce dependency."
            elif focus_type == "membership":
                text = f"{focus_name} customers drive {focus_pct:.0f}% of revenue. Build a next-best offer for the smaller tiers."
            else:
                text = f"{payment_name} covers {focus_pct:.0f}% of payments. Keep that flow smooth, but maintain backup payment options."
            label = "Concentrated"
            color, bg = "#8A6A1A", "#F7E4B5"
        else:
            text = "Revenue, membership, and payment mix are reasonably distributed, giving the period lower concentration risk."
            label = "Diversified"
            color, bg = "#4A7E78", "#D5F1EE"

        return self._insight("Mix Quality", label, text, score, confidence, color, bg)

    def _promotion_signal(self):
        discounts = self.data.get("discounts", [])
        discount_total = sum(float(row[8] or 0) for row in discounts) if discounts else 0.0
        revenue = self._parse_money(self._stat_value("Total Revenue"))
        discount_ratio = (discount_total / max(revenue + discount_total, 1)) * 100

        low = self._trap(discount_ratio, 0, 0, 2, 5)
        medium = self._tri(discount_ratio, 3, 8, 14)
        high = self._trap(discount_ratio, 10, 18, 40, 40)
        score = self._defuzzify([(low, 82), (medium, 66), (high, 38)], default=74)
        confidence = self._confidence(low, medium, high)

        if not discounts:
            return self._insight(
                "Promotion Guardrail",
                "Clean",
                "No discount rows appear in this range, so margin leakage from listed promotions looks low.",
                82,
                80,
                "#4A7E78",
                "#D5F1EE",
            )
        if high >= medium and high >= low:
            label = "High Discount"
            text = f"Listed discounts equal roughly {discount_ratio:.1f}% of visible revenue. Review whether they are lifting repeat bookings."
            color, bg = "#C05070", "#F9D0D8"
        elif medium >= low:
            label = "Watch"
            text = f"Discount usage is moderate at about {discount_ratio:.1f}% of visible revenue. Keep it tied to VIP or repeat behavior."
            color, bg = "#8A6A1A", "#F7E4B5"
        else:
            label = "Controlled"
            text = f"Discount impact is low at about {discount_ratio:.1f}% of visible revenue, so promotions look margin-friendly."
            color, bg = "#5A8A1A", "#D4EDBA"

        return self._insight("Promotion Guardrail", label, text, score, confidence, color, bg)

    def build(self):
        has_revenue = self._parse_money(self._stat_value("Total Revenue")) > 0
        has_transactions = self._parse_number(self._stat_value("Transactions")) > 0
        if not has_revenue and not has_transactions:
            return [
                self._insight(
                    "Data Readiness",
                    "Waiting",
                    "There is not enough paid activity in this range yet. Switch range or wait for billing data to generate stronger insights.",
                    45,
                    70,
                    "#7A685F",
                    "#EFE6DD",
                )
            ]

        insights = [
            self._revenue_momentum(),
            self._capacity_signal(),
            self._mix_signal(),
            self._promotion_signal(),
        ]
        return insights[:4]


class ReportBackend:
    def __init__(self, db=None):
        self.db = db or DatabaseConnection()
        self.custom_start = None
        self.custom_end = None

    @staticmethod
    def _money(value):
        if value is None:
            value = 0
        if isinstance(value, Decimal):
            value = int(value)
        return f"{int(value):,}đ"

    @staticmethod
    def _money_million(value):
        if value is None:
            value = 0
        amount = float(value)
        million = amount / 1_000_000
        return f"{million:.1f}".rstrip("0").rstrip(".") + "M"

    @staticmethod
    def _pct(value):
        return f"{float(value or 0):.0f}%"

    def _period_condition(self):
        if self.active_tab == "Custom":
            start = self.custom_start
            end = self.custom_end
            if start and end:
                try:
                    from datetime import datetime
                    datetime.strptime(start, "%Y-%m-%d")
                    datetime.strptime(end, "%Y-%m-%d")
                    return (
                        f"DATE(COALESCE(bl.payment_date, b.check_out)) >= '{start}' "
                        f"AND DATE(COALESCE(bl.payment_date, b.check_out)) <= '{end}'"
                    )
                except ValueError:
                    pass
        filters = {
            "Today": "DATE(COALESCE(bl.payment_date, b.check_out)) = CURDATE()",
            "This week": "YEARWEEK(COALESCE(bl.payment_date, b.check_out), 1) = YEARWEEK(CURDATE(), 1)",
            "This month": "YEAR(COALESCE(bl.payment_date, b.check_out)) = YEAR(CURDATE()) "
                          "AND MONTH(COALESCE(bl.payment_date, b.check_out)) = MONTH(CURDATE())",
            "Last month": "YEAR(COALESCE(bl.payment_date, b.check_out)) = YEAR(DATE_SUB(CURDATE(), INTERVAL 1 MONTH)) "
                          "AND MONTH(COALESCE(bl.payment_date, b.check_out)) = MONTH(DATE_SUB(CURDATE(), INTERVAL 1 MONTH))",
        }
        return filters.get(self.active_tab, filters["This week"])

    def get_data(self, active_tab="This week", custom_start=None, custom_end=None):
        self.active_tab = active_tab
        self.custom_start = custom_start
        self.custom_end = custom_end
        try:
            data = {
                "today": datetime.now().strftime("%d/%m/%Y"),
                "range": self.get_range_label(),
                "bar_title": f"Revenue Trend - {active_tab}",
                "bar_data": self.get_revenue_trend(),
                "stats": self.get_stats(),
                "service_segments": self.get_service_segments(),
                "membership_segments": self.get_membership_segments(),
                "payment_methods": self.get_payment_methods(),
                "discounts": self.get_discounts(),
            }
            data["ai_insights"] = FuzzyInsightEngine(data).build()
            return data
        except Exception as exc:
            print(f"Report backend error: {exc}")
            return self.fallback_data(active_tab)

    def get_range_label(self):
        if self.active_tab == "Custom" and self.custom_start and self.custom_end:
            from datetime import datetime
            try:
                s = datetime.strptime(self.custom_start, "%Y-%m-%d").strftime("%d/%m/%Y")
                e = datetime.strptime(self.custom_end, "%Y-%m-%d").strftime("%d/%m/%Y")
                return {"start": s, "end": e}
            except ValueError:
                pass
        row = self.db.fetch_one(
            f"""
            SELECT
                MIN(DATE(COALESCE(bl.payment_date, b.check_out))) AS start_date,
                MAX(DATE(COALESCE(bl.payment_date, b.check_out))) AS end_date
            FROM bookings b
            LEFT JOIN billing bl ON bl.booking_id = b.booking_id
            WHERE {self._period_condition()}
            """
        ) or {}
        start = row.get("start_date")
        end = row.get("end_date")
        return {
            "start": start.strftime("%d/%m/%Y") if start else "-",
            "end": end.strftime("%d/%m/%Y") if end else "-",
        }

    def get_revenue_trend(self):
        if self.active_tab == "Today":
            return self._revenue_by_hour()
        rows = self.db.fetch_all(
            f"""
            SELECT
                DATE(COALESCE(bl.payment_date, b.check_out)) AS report_date,
                COALESCE(SUM(bl.total_amount), 0) AS revenue
            FROM bookings b
            LEFT JOIN billing bl ON bl.booking_id = b.booking_id
            WHERE {self._period_condition()}
            GROUP BY DATE(COALESCE(bl.payment_date, b.check_out))
            ORDER BY report_date
            """
        )
        data = []
        for row in rows or []:
            label = row["report_date"].strftime("%d/%m")
            data.append((label, round(float(row.get("revenue") or 0) / 1_000_000, 1)))
        return data or [("-", 0)]

    def _revenue_by_hour(self):
        rows = self.db.fetch_all(
            """
            SELECT HOUR(COALESCE(bl.payment_date, b.check_out)) AS hour,
                   COALESCE(SUM(bl.total_amount), 0) AS revenue
            FROM bookings b
            LEFT JOIN billing bl ON bl.booking_id = b.booking_id
            WHERE DATE(COALESCE(bl.payment_date, b.check_out)) = CURDATE()
            GROUP BY HOUR(COALESCE(bl.payment_date, b.check_out))
            ORDER BY hour
            """
        )
        return [(f"{int(row['hour']):02d}h", round(float(row.get("revenue") or 0) / 1_000_000, 1))
                for row in rows or []] or [("-", 0)]

    def get_stats(self):
        row = self.db.fetch_one(
            f"""
            SELECT
                COALESCE(SUM(bl.total_amount), 0) AS total_revenue,
                COUNT(bl.payment_id) AS transactions,
                COALESCE(AVG(bl.total_amount), 0) AS avg_order
            FROM bookings b
            LEFT JOIN billing bl ON bl.booking_id = b.booking_id
            WHERE {self._period_condition()}
            """
        ) or {}
        occupancy = self.db.fetch_one(
            f"""
            SELECT
                COUNT(DISTINCT b.room_id) AS occupied_rooms,
                (SELECT COUNT(*) FROM rooms WHERE is_active = 1 OR is_active = b'1') AS total_rooms
            FROM bookings b
            LEFT JOIN billing bl ON bl.booking_id = b.booking_id
            WHERE {self._period_condition()}
            """
        ) or {}
        total_rooms = int(occupancy.get("total_rooms") or 0)
        occupied = int(occupancy.get("occupied_rooms") or 0)
        occ_pct = round((occupied / total_rooms) * 100) if total_rooms else 0
        return [
            ("Total Revenue", self._money_million(row.get("total_revenue")), "current period"),
            ("Transactions", str(int(row.get("transactions") or 0)), f"avg {self._money(row.get('avg_order'))} / order"),
            ("Room Occupancy", f"{occ_pct}%", f"{occupied}/{total_rooms} rooms"),
        ]

    def _segments_from_rows(self, rows, label_key, value_key, palette):
        total = sum(float(row.get(value_key) or 0) for row in rows or [])
        if total <= 0:
            return [(100, "#C8C8C8", "No data\n100%")]
        segments = []
        for idx, row in enumerate(rows or []):
            value = float(row.get(value_key) or 0)
            pct = round(value / total * 100)
            label = str(row.get(label_key) or "Other").title()
            segments.append((pct, palette[idx % len(palette)], f"{label}\n{pct}%"))
        return segments

    def get_service_segments(self):
        rows = self.db.fetch_all(
            f"""
            SELECT service_type, SUM(revenue) AS revenue
            FROM (
                SELECT 'Room Stay' AS service_type, COALESCE(SUM(b.room_price), 0) AS revenue
                FROM bookings b
                LEFT JOIN billing bl ON bl.booking_id = b.booking_id
                WHERE {self._period_condition()}
                UNION ALL
                SELECT sc.service_type, COALESCE(SUM(s.total_price), 0) AS revenue
                FROM services s
                JOIN service_catalog sc ON sc.service_type_id = s.service_type_id
                JOIN bookings b ON b.booking_id = s.booking_id
                LEFT JOIN billing bl ON bl.booking_id = b.booking_id
                WHERE {self._period_condition()}
                GROUP BY sc.service_type
            ) revenue_parts
            GROUP BY service_type
            ORDER BY revenue DESC
            LIMIT 4
            """
        )
        return self._segments_from_rows(rows, "service_type", "revenue",
                                        ["#C8E066", "#F4A0B0", "#60C0B8", "#E8A040"])

    def get_membership_segments(self):
        rows = self.db.fetch_all(
            f"""
            SELECT COALESCE(cp.membership_type, 'Non - VIP') AS membership, COALESCE(SUM(bl.total_amount), 0) AS revenue
            FROM bookings b
            JOIN customers c ON c.customer_id = b.customer_id
            LEFT JOIN customer_points cp ON cp.customer_id = c.customer_id
            LEFT JOIN billing bl ON bl.booking_id = b.booking_id
            WHERE {self._period_condition()}
            GROUP BY COALESCE(cp.membership_type, 'Non - VIP')
            ORDER BY revenue DESC
            """
        )
        return self._segments_from_rows(rows, "membership", "revenue", ["#C8E066", "#C8C8C8", "#F4A0B0"])

    def get_payment_methods(self):
        rows = self.db.fetch_all(
            f"""
            SELECT COALESCE(pm.method_name, 'Unknown') AS method, COUNT(*) AS count
            FROM bookings b
            LEFT JOIN billing bl ON bl.booking_id = b.booking_id
            LEFT JOIN payment_methods pm ON pm.method_id = bl.payment_method_id
            WHERE {self._period_condition()} AND bl.payment_id IS NOT NULL
            GROUP BY COALESCE(pm.method_name, 'Unknown')
            ORDER BY count DESC
            """
        )
        total = sum(int(row.get("count") or 0) for row in rows or [])
        if not total:
            return [("No data", 1.0, "#C8C8C8")]
        colors = ["#F4A0B0", "#60C0B8", "#E8A040", "#C8E066"]
        return [
            (str(row.get("method") or "Unknown").title(), int(row.get("count") or 0) / total, colors[idx % len(colors)])
            for idx, row in enumerate(rows)
        ]

    def get_discounts(self, limit=3):
        rows = self.db.fetch_all(
            f"""
            SELECT
                b.booking_id,
                c.full_name,
                bl.total_amount,
                COALESCE(bl.discount_amount, 0) AS discount_amount,
                COALESCE(cp.membership_type, 'Standard') AS membership
            FROM billing bl
            JOIN bookings b ON b.booking_id = bl.booking_id
            JOIN customers c ON c.customer_id = b.customer_id
            LEFT JOIN customer_points cp ON cp.customer_id = c.customer_id
            WHERE COALESCE(bl.discount_amount, 0) > 0
              AND {self._period_condition()}
            ORDER BY bl.discount_amount DESC, bl.payment_date DESC
            LIMIT %s
            """,
            (limit,),
        )
        data = []
        for row in rows or []:
            final_paid = int(row.get("total_amount") or 0)
            discount = int(row.get("discount_amount") or 0)
            original = final_paid + discount
            membership = str(row.get("membership") or "Standard").title()
            is_vip = "vip" in membership.lower() or "premium" in membership.lower()
            data.append((
                f"#{row.get('booking_id')}",
                row.get("full_name") or "-",
                self._money(original),
                f"-{self._money(discount)}",
                membership,
                self._money(final_paid),
                "#D4EDBA" if is_vip else "#F9D0D8",
                "#5A8A1A" if is_vip else "#C05070",
                discount,
            ))
        return data

    def fallback_data(self, active_tab):
        start_display = "-"
        end_display = "-"
        if active_tab == "Custom" and self.custom_start and self.custom_end:
            from datetime import datetime
            try:
                start_display = datetime.strptime(self.custom_start, "%Y-%m-%d").strftime("%d/%m/%Y")
                end_display = datetime.strptime(self.custom_end, "%Y-%m-%d").strftime("%d/%m/%Y")
            except ValueError:
                pass
        data = {
            "today": datetime.now().strftime("%d/%m/%Y"),
            "range": {"start": start_display, "end": end_display},
            "bar_title": f"Revenue Trend - {active_tab}",
            "bar_data": [("-", 0)],
            "stats": [("Total Revenue", "0M", ""), ("Transactions", "0", ""), ("Room Occupancy", "0%", "")],
            "service_segments": [(100, "#C8C8C8", "No data\n100%")],
            "membership_segments": [(100, "#C8C8C8", "No data\n100%")],
            "payment_methods": [("No data", 1.0, "#C8C8C8")],
            "discounts": [],
        }
        data["ai_insights"] = FuzzyInsightEngine(data).build()
        return data


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


def _round_rect_outline(cv, x1, y1, x2, y2, radius=25, fill="", outline="", width=1, tags=""):
    _round_rect(cv, x1, y1, x2, y2, radius=radius, fill=fill)
    d = 2 * radius
    items = []
    items.append(cv.create_arc(x1, y1, x1 + d, y1 + d, start=90, extent=90, style='arc', outline=outline, width=width, tags=tags))
    items.append(cv.create_arc(x2 - d, y1, x2, y1 + d, start=0, extent=90, style='arc', outline=outline, width=width, tags=tags))
    items.append(cv.create_arc(x2 - d, y2 - d, x2, y2, start=270, extent=90, style='arc', outline=outline, width=width, tags=tags))
    items.append(cv.create_arc(x1, y2 - d, x1 + d, y2, start=180, extent=90, style='arc', outline=outline, width=width, tags=tags))
    items.append(cv.create_line(x1 + radius, y1, x2 - radius, y1, fill=outline, width=width, tags=tags))
    items.append(cv.create_line(x1 + radius, y2, x2 - radius, y2, fill=outline, width=width, tags=tags))
    items.append(cv.create_line(x1, y1 + radius, x1, y2 - radius, fill=outline, width=width, tags=tags))
    items.append(cv.create_line(x2, y1 + radius, x2, y2 - radius, fill=outline, width=width, tags=tags))
    return tuple(items)


class ReportDashboard(AppWindow):
    def __init__(self):
        super().__init__()
        self.title("Pet&Bed - Report")
        self.attributes("-fullscreen", True)
        self.configure(bg="#F5C97A")
        self.update_idletasks()
        # Obtain window size; fall back to screen size if values look invalid
        self.W = self.winfo_width()
        self.H = self.winfo_height()
        if (not isinstance(self.W, (int, float))) or self.W < 200:
            self.W = self.winfo_screenwidth()
        if (not isinstance(self.H, (int, float))) or self.H < 200:
            self.H = self.winfo_screenheight()
        self.BASE_W = 1200.0
        self.BASE_H = 850.0
        self._s = self.W / self.BASE_W
        s = self._s
        self.Y_OFF = 20

        # Colors
        self.C_BG          = "#F5C97A"
        self.C_SIDEBAR     = "#FFFFFF"
        self.C_TEXT        = "#4A3525"
        self.C_TEXT_LIGHT  = "#7A685F"
        self.C_WHITE       = "#FFFFFF"
        self.C_ACTIVE      = "#F5A623"
        self.C_DIVIDER     = "#ECD8C0"
        self.C_CARD_BG     = "#FFFFFF"
        self.C_BAR         = "#C8E066"   # yellow-green bars
        self.C_GREEN_LIGHT = "#C8E066"
        self.C_PINK        = "#F4A0B0"
        self.C_TEAL        = "#60C0B8"
        self.C_ORANGE_PIE  = "#E8A040"
        self.C_GREY_PIE    = "#C8C8C8"

        # Quick-filter tab active bg
        self.C_TAB_ACTIVE  = "#C8E066"
        self._active_tab   = "This week"

        # Fonts
        self.F_LOGO        = ("Arial Rounded MT Bold", max(16, int(40 * s)), "bold")
        self.F_NAV         = ("Baghdad", max(10, int(18 * s)))
        self.F_TITLE       = ("Arial Rounded MT Bold", max(10, int(18 * s)), "bold")
        self.F_DATE        = ("Baghdad", max(10, int(15 * s)))
        self.F_SECTION     = ("Arial Rounded MT Bold", max(12, int(18 * s)), "bold")
        self.F_CARD_LBL    = ("Baghdad", max(10, int(15 * s)), "bold")
        self.F_CARD_VAL    = ("Arial Rounded MT Bold", max(20, int(52 * s)), "bold")
        self.F_CARD_SUB    = ("Baghdad", max(9,  int(13 * s)))
        self.F_AXIS        = ("Baghdad", max(9,  int(13 * s)))
        self.F_BAR_VAL     = ("Baghdad", max(9,  int(12 * s)), "bold")
        self.F_PIE_LBL     = ("Baghdad", max(9,  int(13 * s)))
        self.F_TAB         = ("Baghdad", max(10, int(14 * s)))
        self.F_TABLE_HEAD  = ("Baghdad", max(10, int(14 * s)), "bold")
        self.F_TABLE_BODY  = ("Baghdad", max(9,  int(13 * s)))
        self.F_CHIP        = ("Baghdad", max(9,  int(12 * s)), "bold")
        self.F_AI_TITLE    = ("Arial Rounded MT Bold", max(10, int(14 * s)), "bold")
        self.F_AI_BODY     = ("Baghdad", max(9,  int(12 * s)))
        self.F_AI_META     = ("Baghdad", max(8,  int(11 * s)), "bold")

        self.images = []
        self.backend = ReportBackend()
        self._custom_start = ""
        self._custom_end = ""
        self.report_data = self.backend.get_data(self._active_tab)

        main = tk.Frame(self, bg=self.C_BG)
        main.pack(fill=tk.BOTH, expand=True)

        self.BASE_SIDE_W = 260
        side_w = int(self.BASE_SIDE_W * s)

        self.side_frame = tk.Frame(main, width=side_w, bg=self.C_BG)
        self.side_frame.pack(side=tk.LEFT, fill=tk.Y)
        self.side_frame.pack_propagate(False)
        self.sidebar_canvas = tk.Canvas(self.side_frame, width=side_w, height=self.H,
                                        bg=self.C_BG, highlightthickness=0)
        self.sidebar_canvas.pack(fill=tk.BOTH, expand=True)

        self.content_container = tk.Frame(main, bg=self.C_BG)
        self.content_container.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        scrollbar = tk.Scrollbar(self.content_container, orient=tk.VERTICAL)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.canvas = tk.Canvas(self.content_container, bg=self.C_BG, highlightthickness=0)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.configure(command=self.canvas.yview)

        self.draw_sidebar()
        self.sidebar_canvas.scale("all", 0, 0, s, s)
        self.draw_content()
        self.canvas.scale("all", 0, 0, s, s)

        self.canvas.update_idletasks()
        bbox = self.canvas.bbox("all")
        if bbox:
            self.canvas.configure(scrollregion=(bbox[0], 0, bbox[2], bbox[3] + int(80 * s)))

        def _on_mw(event):
            if sys.platform == "darwin":
                self.canvas.yview_scroll(int(-event.delta), "units")
            else:
                self.canvas.yview_scroll(int(-event.delta / 120), "units")

        self.canvas.bind("<MouseWheel>", _on_mw, add="+")
        self.canvas.bind("<Button-4>", lambda e: self.canvas.yview_scroll(-1, "units"), add="+")
        self.canvas.bind("<Button-5>", lambda e: self.canvas.yview_scroll(1, "units"), add="+")
        self.bind("<Escape>", lambda e: self.destroy())

    # ─────────────────────────── SIDEBAR ───────────────────────────
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
            fill = self.C_ACTIVE if i == 7 else "#efefef"
            _round_rect(cv, pad_x, y, right_x, y + item_h, radius=item_r,
                        fill=fill, outline="", tags=nav_tag)
            cv.create_text(pad_x + 20, y + 20, text=item, font=self.F_NAV,
                           fill=self.C_WHITE if i == 7 else self.C_TEXT,
                           anchor="w", tags=nav_tag)
            bind_nav_item(cv, nav_tag, self, item, "Report")
            y += item_h + gap

        # Hedgehog / porcupine icon
        _dir = os.path.dirname(__file__)
        icon_path = os.path.join(_dir, "image", "hedgehog.png")
        s = self._s
        iw, ih = int(130 * s), int(90 * s)
        sr = int(16 * s)
        if os.path.exists(icon_path):
            img = Image.open(icon_path).convert("RGBA")
            img = img.resize((iw, ih), Image.Resampling.LANCZOS)
            mask = Image.new("L", (iw, ih), 0)
            ImageDraw.Draw(mask).rounded_rectangle((0, 0, iw, ih), radius=sr, fill=255)
            result = Image.new("RGBA", (iw, ih), (0, 0, 0, 0))
            result.paste(img, (0, 0), mask=mask)
            icon_tk = ImageTk.PhotoImage(result)
            self.images.append(icon_tk)
            cv.create_image(125 - iw // 2, 570, image=icon_tk, anchor="nw")

        base_bottom = self.H / self._s
        btn_h, btn_pad = 42, 25
        btn_y2 = base_bottom - btn_pad
        btn_y1 = btn_y2 - btn_h
        _round_rect(cv, 30, btn_y1, 220, btn_y2, radius=btn_h // 2,
                    fill=self.C_TEXT, outline="", tags="logout_btn")
        cv.create_text(125, (btn_y1 + btn_y2) / 2, text="Log out",
                       font=self.F_NAV, fill="#FFFFFF", tags="logout_btn")
        bind_click(cv, "logout_btn", lambda e: logout_to_login(self))

    # ─────────────────────────── IMAGE HELPER ───────────────────────
    def create_rounded_image(self, image_path, width, height, radius, crop_align="center"):
        s = self._s
        sw, sh, sr = int(width * s), int(height * s), int(radius * s)
        if not os.path.exists(image_path):
            img = Image.new("RGB", (sw, sh), color="#C8A860")
        else:
            img = Image.open(image_path).convert("RGB")
        img_ratio = img.width / img.height
        target_ratio = sw / sh
        if img_ratio > target_ratio:
            nw = int(sh * img_ratio)
            img = img.resize((nw, sh), Image.Resampling.LANCZOS)
            if isinstance(crop_align, (float, int)):
                left = int((nw - sw) * crop_align)
            elif crop_align == "left":
                left = 0
            elif crop_align == "right":
                left = nw - sw
            else:
                left = (nw - sw) // 2
            img = img.crop((left, 0, left + sw, sh))
        else:
            nh = int(sw / img_ratio)
            img = img.resize((sw, nh), Image.Resampling.LANCZOS)
            if isinstance(crop_align, (float, int)):
                top = int((nh - sh) * crop_align)
            elif crop_align == "bottom":
                top = nh - sh
            elif crop_align == "top":
                top = 0
            else:
                top = (nh - sh) // 2
            img = img.crop((0, top, sw, top + sh))
        mask = Image.new("L", (sw, sh), 0)
        ImageDraw.Draw(mask).rounded_rectangle((0, 0, sw, sh), radius=sr, fill=255)
        result = Image.new("RGBA", (sw, sh), (0, 0, 0, 0))
        result.paste(img, (0, 0), mask=mask)
        return ImageTk.PhotoImage(result)

    # ─────────────────────────── BAR CHART ──────────────────────────
    def _draw_bar_chart(self, cv, x1, y1, x2, y2, title, data):
        """Draw a bar chart inside the given bounding box."""
        _round_rect(cv, x1, y1, x2, y2, radius=20, fill=self.C_WHITE)
        cx = (x1 + x2) // 2

        cv.create_text(cx, y1 + 22, text=title, font=self.F_SECTION, fill=self.C_TEXT)

        pad_l, pad_r, pad_t, pad_b = 52, 20, 50, 50
        chart_x1 = x1 + pad_l
        chart_x2 = x2 - pad_r
        chart_y1 = y1 + pad_t
        chart_y2 = y2 - pad_b

        max_val   = max(max(v for _, v in data), 1)
        n         = len(data)
        bar_gap   = 14
        bar_w     = (chart_x2 - chart_x1 - bar_gap * (n - 1)) / n
        chart_h   = chart_y2 - chart_y1

        # Y-axis label "Million"
        cv.create_text(x1 + 14, (chart_y1 + chart_y2) // 2,
                       text="Million", font=self.F_AXIS, fill=self.C_TEXT_LIGHT,
                       angle=90)

        # Y grid lines and labels
        step = max_val / 4
        for val in [0, step, step * 2, step * 3, max_val]:
            gy = chart_y2 - (val / max_val) * chart_h
            cv.create_line(chart_x1, gy, chart_x2, gy,
                           fill="#E8E0D8", dash=(4, 4))
            cv.create_text(chart_x1 - 6, gy, text=f"{val:g}",
                           font=self.F_AXIS, fill=self.C_TEXT_LIGHT, anchor="e")

        # Bars
        for i, (label, val) in enumerate(data):
            bx1 = chart_x1 + i * (bar_w + bar_gap)
            bx2 = bx1 + bar_w
            bh  = (val / max_val) * chart_h
            by1 = chart_y2 - bh
            by2 = chart_y2
            br  = 8
            _round_rect(cv, bx1, by1, bx2, by2, radius=br, fill=self.C_BAR)
            # Value label above bar
            cv.create_text((bx1 + bx2) / 2, by1 - 8, text=str(val),
                           font=self.F_BAR_VAL, fill=self.C_TEXT)
            # X label
            cv.create_text((bx1 + bx2) / 2, chart_y2 + 16, text=label,
                           font=self.F_AXIS, fill=self.C_TEXT)

        # X axis line
        cv.create_line(chart_x1, chart_y2, chart_x2, chart_y2,
                       fill=self.C_TEXT_LIGHT)

    # ─────────────────────────── DONUT CHART ────────────────────────
    def _draw_donut(self, cv, cx, cy, r_out, r_in, segments, title, x1, y1, x2, y2):
        """Draw a donut chart. segments = [(pct, color, label_str), ...]"""
        _round_rect(cv, x1, y1, x2, y2, radius=20, fill=self.C_WHITE)
        cv.create_text((x1 + x2) // 2, y1 + 20,
                       text=title, font=self.F_SECTION, fill=self.C_TEXT)

        # Card inner padding for label clamping
        pad_x, pad_top, pad_bot = 14, 42, 14

        start_angle = 90
        for pct, color, label in segments:
            extent = pct / 100 * 360
            cv.create_arc(cx - r_out, cy - r_out, cx + r_out, cy + r_out,
                          start=start_angle, extent=-extent,
                          fill=color, outline="")
            # Label placement — clamped inside card boundaries
            mid_angle = math.radians(start_angle - extent / 2)
            lx = cx + (r_out + 22) * math.cos(mid_angle)
            ly = cy - (r_out + 22) * math.sin(mid_angle)
            # Clamp to stay inside the card
            lx = max(x1 + pad_x + 30, min(lx, x2 - pad_x - 30))
            ly = max(y1 + pad_top + 8, min(ly, y2 - pad_bot - 8))
            cv.create_text(lx, ly, text=label, font=self.F_PIE_LBL, fill=self.C_TEXT)
            start_angle -= extent

        # White hole for donut
        cv.create_oval(cx - r_in, cy - r_in, cx + r_in, cy + r_in,
                       fill=self.C_WHITE, outline="")

    # ─────────────────────────── FUZZY AI INSIGHTS ──────────────────
    @staticmethod
    def _wrap_text(text, max_chars=44, max_lines=2):
        words = str(text or "").split()
        lines = []
        current = ""
        for word in words:
            candidate = f"{current} {word}".strip()
            if len(candidate) <= max_chars:
                current = candidate
            else:
                if current:
                    lines.append(current)
                current = word
            if len(lines) == max_lines:
                break
        if current and len(lines) < max_lines:
            lines.append(current)
        if len(lines) == max_lines and len(words) > len(" ".join(lines).split()):
            lines[-1] = lines[-1].rstrip(".") + "..."
        return "\n".join(lines)

    def _draw_ai_insights(self, cv, x1, y1, x2, y2, insights):
        _round_rect(cv, x1, y1, x2, y2, radius=20, fill=self.C_WHITE)
        cv.create_text(x1 + 24, y1 + 24, text="Fuzzy AI Insights",
                       font=self.F_SECTION, fill=self.C_TEXT, anchor="w")
        cv.create_text(x1 + 24, y1 + 48,
                       text="Rule-based signals from the current report data",
                       font=self.F_CARD_SUB, fill=self.C_TEXT_LIGHT, anchor="w")

        chip_w, chip_h = 118, 26
        chip_x2 = x2 - 24
        chip_x1 = chip_x2 - chip_w
        chip_y1 = y1 + 17
        _round_rect(cv, chip_x1, chip_y1, chip_x2, chip_y1 + chip_h,
                    radius=chip_h // 2, fill="#F7E4B5")
        cv.create_text((chip_x1 + chip_x2) // 2, chip_y1 + chip_h // 2,
                       text="Fuzzy logic", font=self.F_AI_META, fill="#8A6A1A")

        items = (insights or [])[:4]
        if not items:
            cv.create_text((x1 + x2) // 2, (y1 + y2) // 2,
                           text="No insight data available",
                           font=self.F_TABLE_BODY, fill=self.C_TEXT_LIGHT)
            return

        grid_x1, grid_x2 = x1 + 24, x2 - 24
        grid_y1, grid_y2 = y1 + 70, y2 - 18

        if len(items) == 1:
            self._draw_ai_insight_cell(cv, grid_x1, grid_y1, grid_x2, grid_y2,
                                       items[0], max_chars=92)
            return

        mid_x = (grid_x1 + grid_x2) // 2
        mid_y = (grid_y1 + grid_y2) // 2
        cv.create_line(mid_x, grid_y1, mid_x, grid_y2, fill=self.C_DIVIDER, width=1)
        cv.create_line(grid_x1, mid_y, grid_x2, mid_y, fill=self.C_DIVIDER, width=1)

        cell_w = (grid_x2 - grid_x1) / 2
        cell_h = (grid_y2 - grid_y1) / 2
        for idx, item in enumerate(items):
            col = idx % 2
            row = idx // 2
            cx1 = grid_x1 + col * cell_w + (16 if col else 0)
            cx2 = grid_x1 + (col + 1) * cell_w - (16 if not col else 0)
            cy1 = grid_y1 + row * cell_h + (12 if row else 0)
            cy2 = grid_y1 + (row + 1) * cell_h - (12 if not row else 0)
            self._draw_ai_insight_cell(cv, cx1, cy1, cx2, cy2, item)

    def _draw_ai_insight_cell(self, cv, x1, y1, x2, y2, insight, max_chars=42):
        color = insight.get("color", self.C_TEXT)
        bg = insight.get("bg", "#EFE6DD")
        label = str(insight.get("label", "Signal"))
        score = int(insight.get("score", 0))
        confidence = int(insight.get("confidence", 0))

        cv.create_text(x1, y1 + 10, text=insight.get("title", "Insight"),
                       font=self.F_AI_TITLE, fill=self.C_TEXT, anchor="w")

        chip_w = min(112, max(76, 8 * len(label) + 22))
        chip_h = 22
        chip_x1 = x2 - chip_w
        _round_rect(cv, chip_x1, y1, x2, y1 + chip_h,
                    radius=chip_h // 2, fill=bg)
        cv.create_text((chip_x1 + x2) // 2, y1 + chip_h // 2,
                       text=label[:18], font=self.F_CHIP, fill=color)

        body = self._wrap_text(insight.get("text", ""), max_chars=max_chars, max_lines=2)
        cv.create_text(x1, y1 + 36, text=body,
                       font=self.F_AI_BODY, fill=self.C_TEXT_LIGHT, anchor="w")

        bar_x1 = x1
        bar_x2 = x2 - 92
        bar_y1 = y2 - 13
        bar_y2 = bar_y1 + 8
        _round_rect(cv, bar_x1, bar_y1, bar_x2, bar_y2, radius=4, fill="#EFE6DD")
        fill_x2 = bar_x1 + (bar_x2 - bar_x1) * max(0, min(score, 100)) / 100
        _round_rect(cv, bar_x1, bar_y1, fill_x2, bar_y2, radius=4, fill=color)
        cv.create_text(x2, bar_y1 + 4, text=f"{score}/100 - {confidence}%",
                       font=self.F_AI_META, fill=self.C_TEXT, anchor="e")

    # ─────────────────────────── MAIN CONTENT ───────────────────────
    def draw_content(self):
        cv   = self.canvas
        dx   = -self.BASE_SIDE_W
        y    = self.Y_OFF
        cw   = 848        # content width (1150-300-2)
        cx0  = 300 + dx   # left edge of content
        cx1  = cx0 + cw   # right edge
        _dir = os.path.dirname(__file__)

        # ── HEADER BAR ──
        header_y1 = 30 + y
        header_y2 = 70 + y
        header_cy = (header_y1 + header_y2) // 2
        _round_rect(cv, cx0, header_y1, cx1, header_y2,
                    radius=20, fill=self.C_WHITE)
        cv.create_text(cx0 + 30, header_cy, text="Report",
                       font=self.F_TITLE, fill=self.C_TEXT, anchor="w")
        cv.create_text(cx0 + 115, header_cy,
                       text=self.report_data["today"],
                       font=self.F_DATE, fill=self.C_TEXT_LIGHT, anchor="w")

        # ── DATE RANGE + QUICK TABS ──
        dr_y1, dr_y2 = 82 + y, 118 + y
        dr_r = (dr_y2 - dr_y1) // 2
        _round_rect(cv, cx0, dr_y1, cx0 + 550, dr_y2, radius=dr_r, fill=self.C_WHITE,
                    tags="date_bar")
        cv.create_text(cx0 + 18, (dr_y1 + dr_y2) // 2,
                       text="Custom", font=self.F_TAB, fill=self.C_TEXT, anchor="w",
                       tags="date_bar")

        is_custom = self._active_tab == "Custom"
        date_fill = self.C_ACTIVE if is_custom else self.C_TEXT
        cv.create_text(cx0 + 90, (dr_y1 + dr_y2) // 2,
                       text=self.report_data["range"]["start"], font=self.F_DATE,
                       fill=date_fill, anchor="w", tags="date_bar")
        cv.create_text(cx0 + 185, (dr_y1 + dr_y2) // 2,
                       text="🗓", font=("Segoe UI Emoji", 14), anchor="w", tags="date_bar")
        cv.create_text(cx0 + 210, (dr_y1 + dr_y2) // 2,
                       text="→", font=self.F_DATE, fill=self.C_TEXT, anchor="w",
                       tags="date_bar")
        cv.create_text(cx0 + 238, (dr_y1 + dr_y2) // 2,
                       text=self.report_data["range"]["end"], font=self.F_DATE,
                       fill=date_fill, anchor="w", tags="date_bar")
        cv.create_text(cx0 + 343, (dr_y1 + dr_y2) // 2,
                       text="🗓", font=("Segoe UI Emoji", 14), anchor="w", tags="date_bar")

        # Always clickable — opens date editor and switches to Custom tab
        cv.tag_bind("date_bar", "<Button-1>", lambda e: self._edit_custom_date())
        cv.tag_bind("date_bar", "<Enter>", lambda e: cv.config(cursor="hand2"))
        cv.tag_bind("date_bar", "<Leave>", lambda e: cv.config(cursor=""))

        # ── CAT BANNER IMAGE ──
        img_path = os.path.join(_dir, "image", "report.jpg")
        img_tk   = self.create_rounded_image(img_path, 550, 180, radius=18, crop_align=0.65)
        self.images.append(img_tk)
        cv.create_image(cx0, 130 + y, image=img_tk, anchor="nw")

        # ── QUICK FILTER CONTAINER CARD & TABS ──
        card_x1 = cx0 + 568
        card_y1 = 82 + y
        card_x2 = cx1
        card_y2 = 130 + y + 180  # Ends at 310 + y, perfectly aligned with the cat banner's bottom
        _round_rect(cv, card_x1, card_y1, card_x2, card_y2, radius=26, fill=self.C_WHITE)

        tabs = ["Today", "This week", "This month", "Last month", "Custom"]
        tab_w, tab_h = 240, 32
        tab_gap = 8
        tab_y_start = card_y1 + 12

        for tab in tabs:
            ty1 = tab_y_start
            ty2 = ty1 + tab_h
            active = (tab == self._active_tab)
            tx1 = card_x1 + 20
            tx2 = card_x2 - 20
            tag = f"qtab_{tab.replace(' ', '_')}"
            
            if active:
                _round_rect(cv, tx1, ty1, tx2, ty2, radius=tab_h // 2, fill=self.C_TAB_ACTIVE, tags=tag)
            else:
                _round_rect_outline(cv, tx1, ty1, tx2, ty2, radius=tab_h // 2, fill=self.C_WHITE, outline="#C8C2BC", width=1, tags=tag)
                
            cv.create_text((tx1 + tx2) // 2, (ty1 + ty2) // 2,
                           text=tab, font=self.F_TAB, fill=self.C_TEXT, tags=tag)
            cv.tag_bind(tag, "<Button-1>", lambda e, t=tab: self._switch_report_tab(t))
            cv.tag_bind(tag, "<Enter>", lambda e: cv.config(cursor="hand2"))
            cv.tag_bind(tag, "<Leave>", lambda e: cv.config(cursor=""))
            tab_y_start += tab_h + tab_gap

        # ── BAR CHART: Revenue Trend ──
        bar_data = self.report_data["bar_data"]
        bar_y1 = 328 + y
        bar_y2 = bar_y1 + 240
        self._draw_bar_chart(cv, cx0, bar_y1, cx1, bar_y2,
                             self.report_data["bar_title"], bar_data)

        # ── STAT CARDS ──
        sc_y1 = bar_y2 + 18
        sc_y2 = sc_y1 + 130
        sc_w  = (cw - 20) // 3

        stats = self.report_data["stats"]
        for i, (lbl, val, sub) in enumerate(stats):
            sx1 = cx0 + i * (sc_w + 10)
            sx2 = sx1 + sc_w
            _round_rect(cv, sx1, sc_y1, sx2, sc_y2, radius=20, fill=self.C_WHITE)
            scx = (sx1 + sx2) // 2
            cv.create_text(scx, sc_y1 + 22, text=lbl,
                           font=self.F_CARD_LBL, fill=self.C_TEXT)
            cv.create_text(scx, sc_y1 + 72, text=val,
                           font=self.F_CARD_VAL, fill=self.C_TEXT)
            if sub:
                cv.create_text(scx, sc_y2 - 18, text=sub,
                               font=self.F_CARD_SUB, fill=self.C_TEXT_LIGHT)

        # ── FUZZY AI INSIGHTS ──
        ai_y1 = sc_y2 + 18
        ai_y2 = ai_y1 + 280
        self._draw_ai_insights(cv, cx0, ai_y1, cx1, ai_y2,
                               self.report_data.get("ai_insights", []))

        # ── DONUT CHARTS ──
        donut_y1 = ai_y2 + 18
        donut_y2 = donut_y1 + 230
        donut_w  = (cw - 16) // 2

        # Revenue by Service
        d1x1, d1x2 = cx0, cx0 + donut_w
        d1cx = d1x1 + donut_w // 2
        d1cy = (donut_y1 + donut_y2) // 2 + 12
        self._draw_donut(cv, d1cx, d1cy, 62, 34,
                         self.report_data["service_segments"],
                         "Revenue by Service",
                         d1x1, donut_y1, d1x2, donut_y2)

        # Revenue by Memberships
        d2x1, d2x2 = cx0 + donut_w + 16, cx1
        d2cx = d2x1 + (d2x2 - d2x1) // 2
        d2cy = (donut_y1 + donut_y2) // 2 + 12
        self._draw_donut(cv, d2cx, d2cy, 62, 34,
                         self.report_data["membership_segments"],
                         "Revenue by Memberships",
                         d2x1, donut_y1, d2x2, donut_y2)

        # ── PAYMENT METHODS STACKED BAR ──
        pm_y1 = donut_y2 + 18
        pm_y2 = pm_y1 + 150
        _round_rect(cv, cx0, pm_y1, cx1, pm_y2, radius=20, fill=self.C_WHITE)
        pmcx = (cx0 + cx1) // 2
        cv.create_text(pmcx, pm_y1 + 20, text="Payment Methods",
                       font=self.F_SECTION, fill=self.C_TEXT)

        # Legend
        payment_methods = self.report_data["payment_methods"]
        legend_items = [(label, color) for label, _pct, color in payment_methods]
        lx = pmcx - 160
        for lbl, col in legend_items:
            cv.create_oval(lx - 6, pm_y1 + 40, lx + 6, pm_y1 + 52, fill=col, outline="")
            cv.create_text(lx + 12, pm_y1 + 46, text=lbl,
                           font=self.F_PIE_LBL, fill=self.C_TEXT, anchor="w")
            lx += 130

        # Stacked bar
        bar_x1  = cx0 + 20
        bar_x2  = cx1 - 20
        bbar_y1 = pm_y1 + 65
        bbar_y2 = bbar_y1 + 30
        bar_r   = (bbar_y2 - bbar_y1) // 2
        total_w = bar_x2 - bar_x1
        segments = [(pct, color) for _label, pct, color in payment_methods]
        cur_x = bar_x1
        for i, (pct, col) in enumerate(segments):
            seg_w = int(pct * total_w) if i < len(segments) - 1 else bar_x2 - cur_x
            if i == 0:
                cv.create_arc(cur_x, bbar_y1, cur_x + bar_r * 2, bbar_y2,
                              start=90, extent=180, fill=col, outline=col)
                cv.create_rectangle(cur_x + bar_r, bbar_y1, cur_x + seg_w, bbar_y2, fill=col, outline=col)
            elif i == len(segments) - 1:
                cv.create_rectangle(cur_x, bbar_y1, cur_x + seg_w - bar_r, bbar_y2, fill=col, outline=col)
                cv.create_arc(cur_x + seg_w - bar_r * 2, bbar_y1, cur_x + seg_w, bbar_y2,
                              start=270, extent=180, fill=col, outline=col)
            else:
                cv.create_rectangle(cur_x, bbar_y1, cur_x + seg_w, bbar_y2, fill=col, outline=col)
            cur_x += seg_w

        # X-axis labels
        x_labels = ["0%", "20%", "40%", "60%", "80%", "100%"]
        for i, lbl in enumerate(x_labels):
            lx = bar_x1 + int(i / 5 * total_w)
            cv.create_text(lx, bbar_y2 + 14, text=lbl,
                           font=self.F_AXIS, fill=self.C_TEXT_LIGHT)

        # ── DISCOUNTS & PROMOTIONS TABLE ──
        disc_y = pm_y2 + 30
        cv.create_text(cx0, disc_y, text="Discounts & Promotions Applied",
                       font=self.F_SECTION, fill=self.C_TEXT, anchor="w")

        tbl_y1 = disc_y + 24
        # Compute table height dynamically based on number of discount rows to avoid overflow
        disc_data = self.report_data["discounts"]
        row_h = 36
        min_table_h = 130
        # header area + at least one row + bottom padding
        computed_h = 24 + (len(disc_data) if disc_data else 1) * row_h + 24
        tbl_y2 = tbl_y1 + max(min_table_h, computed_h)
        _round_rect(cv, cx0, tbl_y1, cx1, tbl_y2, radius=18, fill=self.C_WHITE)

        cols   = ["Booking", "Customer", "Original", "Discount", "Type", "Final Paid"]
        col_xs = [cx0 + 30, cx0 + 130, cx0 + 270, cx0 + 400, cx0 + 520, cx0 + 660]
        hdr_y  = tbl_y1 + 24

        for col, lcx in zip(cols, col_xs):
            cv.create_text(lcx, hdr_y, text=col, font=self.F_TABLE_HEAD,
                           fill=self.C_TEXT, anchor="w")
        cv.create_line(cx0 + 15, hdr_y + 18, cx1 - 15, hdr_y + 18,
                       fill=self.C_DIVIDER, width=1)

        # disc_data and row_h already defined above
        if not disc_data:
            cv.create_text((cx0 + cx1) // 2, hdr_y + 48,
                           text="No discounts in this period",
                           font=self.F_TABLE_BODY, fill=self.C_TEXT_LIGHT)
        for ri, row in enumerate(disc_data):
            ry  = hdr_y + 22 + ri * row_h
            rcy = ry + row_h // 2

            for ci, (val, lcx) in enumerate(zip(row[:6], col_xs)):
                if ci == 4:   # Type chip
                    chip_bg, chip_fg = row[6], row[7]
                    cw2 = 72
                    _round_rect(cv, lcx, rcy - 12, lcx + cw2, rcy + 12,
                                radius=12, fill=chip_bg)
                    cv.create_text(lcx + cw2 // 2, rcy, text=val,
                                   font=self.F_CHIP, fill=chip_fg)
                else:
                    cv.create_text(lcx, rcy, text=val,
                                   font=self.F_TABLE_BODY, fill=self.C_TEXT, anchor="w")

            if ri < len(disc_data) - 1:
                cv.create_line(cx0 + 15, ry + row_h - 1, cx1 - 15, ry + row_h - 1,
                               fill=self.C_DIVIDER, width=1)

        # ── TOTAL VALUE GIVEN AWAY ──
        tot_y = tbl_y2 + 18
        cv.create_text(cx1 - 180, tot_y,
                       text="Total value given away this period",
                       font=self.F_CARD_SUB, fill=self.C_TEXT, anchor="e")
        cv.create_text(cx1 - 15, tot_y,
                       text=f"-{self.backend._money(sum(row[8] for row in disc_data))}",
                       font=("Baghdad", max(10, int(16 * self._s)), "bold"),
                       fill="#C83040", anchor="e")

    def _edit_custom_date(self):
        """Open a premium Canvas-based dialog to pick custom start/end dates."""
        dialog = tk.Toplevel(self)
        dialog.title("Custom Date Range")
        dialog.transient(self)
        dialog.grab_set()

        # ===== WINDOW =====
        WIDTH  = 540
        HEIGHT = 420
        dialog.geometry(f"{WIDTH}x{HEIGHT}")
        dialog.configure(bg="#F5C97A")
        dialog.resizable(False, False)

        # Center on screen relative to parent
        px = self.winfo_x() + (self.winfo_width() - WIDTH) // 2
        py = self.winfo_y() + (self.winfo_height() - HEIGHT) // 2
        dialog.geometry(f"{WIDTH}x{HEIGHT}+{px}+{py}")

        # ===== COLORS =====
        C_BG     = "#F5C97A"
        C_WHITE  = "#FFFFFF"
        C_TEXT   = "#4A3525"
        C_BORDER = "#D7D0CB"
        C_PLACE  = "#B6AEA9"
        C_BTN    = "#F5A623"

        # ===== CANVAS =====
        cv = tk.Canvas(dialog, width=WIDTH, height=HEIGHT,
                       bg=C_BG, highlightthickness=0)
        cv.pack(fill="both", expand=True)

        # ===== CARD =====
        PAD = 15
        CX1, CY1 = PAD, PAD
        CX2, CY2 = WIDTH - PAD, HEIGHT - PAD

        _round_rect(cv, CX1, CY1, CX2, CY2, radius=28,
                    fill=C_WHITE, outline="")

        IP = 35  # inner padding

        # ───── TITLE ─────
        title_y = CY1 + 38
        cv.create_text(CX1 + IP, title_y,
                       text="Custom Date Range", anchor="w",
                       fill=C_TEXT,
                       font=("Arial Rounded MT Bold", 18, "bold"))

        # Divider
        div_y = title_y + 24
        cv.create_line(CX1 + IP, div_y, CX2 - IP, div_y,
                       fill="#DCD6D2", width=1)

        # ───── START DATE LABEL ─────
        lbl1_y = div_y + 28
        cv.create_text(CX1 + IP, lbl1_y,
                       text="Start Date (DD/MM/YYYY)", anchor="w",
                       fill=C_TEXT,
                       font=("Baghdad", 18, "bold"))

        # Start date input box
        box1_y1 = lbl1_y + 12
        box1_y2 = box1_y1 + 44
        box1_x1 = CX1 + IP - 4
        box1_x2 = CX2 - IP + 4

        _round_rect(cv, box1_x1, box1_y1, box1_x2, box1_y2,
                    radius=22, fill=C_WHITE, outline="")
        _round_rect_outline(cv, box1_x1, box1_y1, box1_x2, box1_y2,
                            radius=22, fill=C_WHITE, outline=C_BORDER, width=1)

        start_entry = tk.Entry(
            dialog, bd=0, relief="flat",
            bg=C_WHITE, fg=C_TEXT,
            font=("Baghdad", 18),
            insertbackground=C_TEXT,
            highlightthickness=0
        )
        default_start = self._custom_start or datetime.now().strftime("01/%m/%Y")
        start_entry.insert(0, default_start)
        start_entry.place(
            x=box1_x1 + 20,
            y=(box1_y1 + box1_y2) // 2 - 12,
            width=box1_x2 - box1_x1 - 40,
            height=24
        )

        # ───── END DATE LABEL ─────
        lbl2_y = box1_y2 + 22
        cv.create_text(CX1 + IP, lbl2_y,
                       text="End Date (DD/MM/YYYY)", anchor="w",
                       fill=C_TEXT,
                       font=("Baghdad", 18, "bold"))

        # End date input box
        box2_y1 = lbl2_y + 12
        box2_y2 = box2_y1 + 44
        box2_x1 = box1_x1
        box2_x2 = box1_x2

        _round_rect(cv, box2_x1, box2_y1, box2_x2, box2_y2,
                    radius=22, fill=C_WHITE, outline="")
        _round_rect_outline(cv, box2_x1, box2_y1, box2_x2, box2_y2,
                            radius=22, fill=C_WHITE, outline=C_BORDER, width=1)

        end_entry = tk.Entry(
            dialog, bd=0, relief="flat",
            bg=C_WHITE, fg=C_TEXT,
            font=("Baghdad", 18),
            insertbackground=C_TEXT,
            highlightthickness=0
        )
        default_end = self._custom_end or datetime.now().strftime("%d/%m/%Y")
        end_entry.insert(0, default_end)
        end_entry.place(
            x=box2_x1 + 20,
            y=(box2_y1 + box2_y2) // 2 - 12,
            width=box2_x2 - box2_x1 - 40,
            height=24
        )

        # ───── APPLY BUTTON ─────
        btn_w  = 180
        btn_h  = 44
        btn_cx = WIDTH // 2
        btn_y1 = box2_y2 + 24
        btn_y2 = btn_y1 + btn_h
        btn_x1 = btn_cx - btn_w // 2
        btn_x2 = btn_cx + btn_w // 2

        _round_rect(cv, btn_x1, btn_y1, btn_x2, btn_y2,
                    radius=btn_h // 2, fill=C_BTN, outline="",
                    tags="apply_btn")

        cv.create_text(btn_cx, (btn_y1 + btn_y2) // 2,
                       text="Apply", fill=C_WHITE,
                       font=("Arial Rounded MT Bold", 18, "bold"),
                       tags="apply_btn")

        def apply(event=None):
            s = start_entry.get().strip()
            e = end_entry.get().strip()
            try:
                if s:
                    datetime.strptime(s, "%d/%m/%Y")
                if e:
                    datetime.strptime(e, "%d/%m/%Y")
            except ValueError:
                from tkinter import messagebox
                messagebox.showerror("Error", "Invalid date format. Use DD/MM/YYYY.", parent=dialog)
                return
            if not s or not e:
                from tkinter import messagebox
                messagebox.showerror("Error", "Please enter both start and end dates.", parent=dialog)
                return
            self._custom_start = s
            self._custom_end = e
            dialog.destroy()
            self._switch_report_tab("Custom")

        cv.tag_bind("apply_btn", "<Button-1>", apply)
        cv.tag_bind("apply_btn", "<Enter>", lambda e: cv.config(cursor="hand2"))
        cv.tag_bind("apply_btn", "<Leave>", lambda e: cv.config(cursor=""))
        dialog.bind("<Escape>", lambda e: dialog.destroy())

        start_entry.focus_set()
        start_entry.bind("<Return>", lambda e: end_entry.focus_set())
        end_entry.bind("<Return>", apply)

    def _switch_report_tab(self, tab_name):
        self._active_tab = tab_name
        if tab_name == "Custom":
            from datetime import datetime
            if not self._custom_start or not self._custom_end:
                now = datetime.now()
                self._custom_start = f"01/{now.month:02d}/{now.year}"
                self._custom_end = now.strftime("%d/%m/%Y")
            try:
                s = datetime.strptime(self._custom_start, "%d/%m/%Y").strftime("%Y-%m-%d")
                e = datetime.strptime(self._custom_end, "%d/%m/%Y").strftime("%Y-%m-%d")
            except ValueError:
                s = e = None
            self.report_data = self.backend.get_data(tab_name, custom_start=s, custom_end=e)
        else:
            self.report_data = self.backend.get_data(tab_name)
        self.canvas.delete("all")
        self.images = self.images[:1]
        self.draw_content()
        self.canvas.scale("all", 0, 0, self._s, self._s)
        self.canvas.update_idletasks()
        bbox = self.canvas.bbox("all")
        if bbox:
            self.canvas.configure(scrollregion=(bbox[0], 0, bbox[2], bbox[3] + int(80 * self._s)))


if __name__ == "__main__":
    app = ReportDashboard()
    app.mainloop()
