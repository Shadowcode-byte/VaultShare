"""
Promotes an already-registered user to admin. Run locally, directly
against the database:

    python3 scripts/promote_admin.py kamal@upes.ac.in

Deliberately a command-line script, not an HTTP endpoint. An admin
role has to come from SOMEWHERE for the very first admin account
(before any admin exists to grant it through the app), but exposing
that as an API route -- even one gated by some other check -- is
exactly the kind of privilege-escalation surface Section 30's rule
against assuming a control is safe just because it exists warns
about. Requiring shell access to the server for this action means the
attack surface for "become an admin" is the server's own access
control, not one more HTTP route to defend.
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.session import SessionLocal  # noqa: E402
from app.models.user import User  # noqa: E402
from app.models.enums import UserRole  # noqa: E402


def main():
    parser = argparse.ArgumentParser(description="Promote a registered user to admin.")
    parser.add_argument("email", help="Email of an already-registered user")
    args = parser.parse_args()

    with SessionLocal() as db:
        user = db.query(User).filter(User.email == args.email.lower()).first()
        if user is None:
            print(f"No user found with email '{args.email}'. They must register first.")
            sys.exit(1)

        if user.role == UserRole.ADMIN:
            print(f"{user.email} is already an admin.")
            return

        user.role = UserRole.ADMIN
        db.commit()
        print(f"{user.email} is now an admin.")


if __name__ == "__main__":
    main()
