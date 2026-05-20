from __future__ import annotations

import argparse
import importlib

from navigation import PAGE_SPECS, resolve_page


def run_page(page_name: str, args: argparse.Namespace) -> None:
    page_name = resolve_page(page_name)
    spec = PAGE_SPECS[page_name]
    module = importlib.import_module(spec.module)
    page_class = getattr(module, spec.class_name)

    if page_name == "Login":
        page_class().run()
        return
    if page_name == "Pet Details":
        app = page_class(pet_id=args.pet_id)
    elif page_name == "Customer Profile":
        app = page_class(customer_id=args.customer_id)
    else:
        app = page_class()
    app.mainloop()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Pet&Bed application launcher")
    parser.add_argument("--page", default="Login")
    parser.add_argument("--pet-id", type=int, default=None)
    parser.add_argument("--customer-id", type=int, default=None)
    return parser.parse_args()


if __name__ == "__main__":
    parsed = parse_args()
    run_page(parsed.page, parsed)
