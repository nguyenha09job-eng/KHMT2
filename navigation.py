from __future__ import annotations

import sys
import os
import importlib
from dataclasses import dataclass
from pathlib import Path
from typing import Callable


APP_ENTRY = Path(__file__).with_name("main.py")


@dataclass(frozen=True)
class PageSpec:
    module: str
    class_name: str


NAV_ITEMS = [
    "Dashboard",
    "Care View",
    "Booking",
    "Rooms",
    "Customer & Pet",
    "Billing",
    "Staff",
    "Report",
]


PAGE_SPECS = {
    "Dashboard": PageSpec("front_1", "PetDashboard"),
    "Care View": PageSpec("front_2", "CareViewDashboard"),
    "Booking": PageSpec("front_3", "BookingDashboard"),
    "Booking History": PageSpec("front_4", "BookingHistory"),
    "Rooms": PageSpec("front_5", "RoomsDashboard"),
    "Customer & Pet": PageSpec("front_6", "CustomerPetDashboard"),
    "Billing": PageSpec("front_10", "BillingDashboard"),
    "Staff": PageSpec("front_11", "StaffPage"),
    "Staff Dashboard": PageSpec("front_13", "StaffDashboard"),
    "Report": PageSpec("front_14", "ReportDashboard"),
    "Login": PageSpec("login", "LoginApp"),
    "Pet Details": PageSpec("front_7", "PetPopup"),
    "Customer Profile": PageSpec("front_8", "CustomerProfilePopup"),
    "New Staff": PageSpec("front_12", "NewStaffPopup"),
}


ALIASES = {
    "dashboard": "Dashboard",
    "home": "Dashboard",
    "care": "Care View",
    "care-view": "Care View",
    "booking": "Booking",
    "bookings": "Booking",
    "history": "Booking History",
    "booking-history": "Booking History",
    "rooms": "Rooms",
    "customer": "Customer & Pet",
    "customers": "Customer & Pet",
    "customer-pet": "Customer & Pet",
    "billing": "Billing",
    "staff": "Staff",
    "staff-dashboard": "Staff Dashboard",
    "employee": "Staff Dashboard",
    "report": "Report",
    "reports": "Report",
    "login": "Login",
    "pet": "Pet Details",
    "pet-details": "Pet Details",
    "profile": "Customer Profile",
    "customer-profile": "Customer Profile",
    "new-staff": "New Staff",
}


def resolve_page(page: str | None) -> str:
    if not page:
        return "Dashboard"
    if page == "Staff":
        return staff_page_for_current_user()
    if page in PAGE_SPECS:
        return page
    normalized = page.strip().lower().replace("_", "-")
    target = ALIASES.get(normalized, "Dashboard")
    if target == "Staff":
        return staff_page_for_current_user()
    return target


def staff_page_for_current_user() -> str:
    role = os.environ.get("PETBED_ROLE", "").strip().lower()
    return "Staff" if role == "manager" else "Staff Dashboard"


def build_command(page: str, *extra_args: str) -> list[str]:
    return [sys.executable, str(APP_ENTRY), "--page", resolve_page(page), *extra_args]


def launch_page(page: str, *extra_args: str) -> None:
    window = create_page(page, *extra_args)
    try:
        window.lift()
        window.focus_force()
    except Exception:
        pass


def _arg_value(args: tuple[str, ...], name: str) -> str | None:
    try:
        index = args.index(name)
    except ValueError:
        return None
    if index + 1 >= len(args):
        return None
    return args[index + 1]


def create_page(page: str, *extra_args: str):
    page_name = resolve_page(page)
    spec = PAGE_SPECS[page_name]
    module = importlib.import_module(spec.module)
    page_class = getattr(module, spec.class_name)

    if page_name == "Login":
        controller = page_class()
        controller.root.protocol("WM_DELETE_WINDOW", controller._on_close)
        controller.root._controller = controller
        return controller.root

    if page_name == "Pet Details":
        pet_id = _arg_value(extra_args, "--pet-id")
        return page_class(pet_id=int(pet_id) if pet_id else None)

    if page_name == "Customer Profile":
        customer_id = _arg_value(extra_args, "--customer-id")
        return page_class(customer_id=int(customer_id) if customer_id else None)

    return page_class()


def _destroy(window) -> None:
    try:
        window.destroy()
    except Exception:
        pass


def switch_to(window, page: str, current_page: str | None = None) -> None:
    target = resolve_page(page)
    if current_page and resolve_page(current_page) == target:
        return
    new_window = create_page(target)
    try:
        new_window.lift()
        new_window.focus_force()
    except Exception:
        pass
    try:
        window.after(60, lambda: _destroy(window))
    except Exception:
        _destroy(window)


def open_popup(page: str, *extra_args: str) -> None:
    launch_page(page, *extra_args)


def logout_to_login(window) -> None:
    switch_to(window, "Login")


def bind_click(canvas, tag_or_id, callback: Callable) -> None:
    canvas.tag_bind(tag_or_id, "<Button-1>", callback)
    canvas.tag_bind(tag_or_id, "<Enter>", lambda _e: canvas.config(cursor="hand2"))
    canvas.tag_bind(tag_or_id, "<Leave>", lambda _e: canvas.config(cursor=""))


def bind_nav_item(canvas, tag: str, window, target_page: str, current_page: str) -> None:
    bind_click(canvas, tag, lambda _e: switch_to(window, target_page, current_page))
