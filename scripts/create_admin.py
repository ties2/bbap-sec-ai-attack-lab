"""
Create initial BBAP-Sec admin user.

Usage:
  python scripts/create_admin.py --name Admin --email admin@bbap-sec.com --password ChangeMeNow123!
"""

import argparse
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from webapp.auth import hash_password
from webapp.database import create_user, get_user_by_email, init_db


def main():
    parser = argparse.ArgumentParser(description="Create initial admin user")
    parser.add_argument("--name", required=True)
    parser.add_argument("--email", required=True)
    parser.add_argument("--password", required=True)
    parser.add_argument("--group", default="BBAP-Sec")
    args = parser.parse_args()

    if len(args.password) < 8:
        raise SystemExit("Password must be at least 8 characters")

    init_db()

    existing = get_user_by_email(args.email)
    if existing:
        raise SystemExit(f"User already exists: {args.email}")

    uid = create_user(
        name=args.name,
        email=args.email,
        password_hash=hash_password(args.password),
        role="bbap_admin",
        group_name=args.group,
    )

    print(f"Created bbap_admin user id={uid} email={args.email}")


if __name__ == "__main__":
    main()
