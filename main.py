from __future__ import annotations

import argparse
from app_window import get_app_root
from navigation import create_page


def run_page(page_name: str, args: argparse.Namespace) -> None:
    extra_args = []
    if args.pet_id is not None:
        extra_args.extend(["--pet-id", str(args.pet_id)])
    if args.customer_id is not None:
        extra_args.extend(["--customer-id", str(args.customer_id)])
    create_page(page_name, *extra_args)
    get_app_root().mainloop()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Pet&Bed application launcher")
    parser.add_argument("--page", default="Login")
    parser.add_argument("--pet-id", type=int, default=None)
    parser.add_argument("--customer-id", type=int, default=None)
    return parser.parse_args()


if __name__ == "__main__":
    parsed = parse_args()
    run_page(parsed.page, parsed)
