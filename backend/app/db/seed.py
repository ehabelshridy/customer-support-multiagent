"""
Seeds the SQLite database with realistic mock data using Faker.

Run directly:
    python -m app.db.seed

The random seed is fixed so the generated data (and therefore every demo
scenario, including edge cases like non-refund-eligible orders) is
reproducible across runs.
"""

import os
import random
import sqlite3
from datetime import timedelta

from faker import Faker

# Support both `python -m app.db.seed` and running this file directly
try:
    from app.config import DB_PATH, SCHEMA_PATH
except ImportError:  # pragma: no cover
    import sys

    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
    from app.config import DB_PATH, SCHEMA_PATH

fake = Faker()
random.seed(42)
Faker.seed(42)

N_CUSTOMERS = 50
N_ORDERS = 80
N_INVOICES = 100


def build_connection() -> sqlite3.Connection:
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        conn.executescript(f.read())
    return conn


def seed_customers(cursor: sqlite3.Cursor) -> list[tuple]:
    customers = []
    for i in range(1, N_CUSTOMERS + 1):
        customers.append(
            (
                f"CUST-{1000 + i}",
                fake.name(),
                fake.email(),
                random.choice(["Basic", "Pro", "Enterprise"]),
                fake.date_between(start_date="-3y", end_date="-1m").isoformat(),
                random.choices(["active", "suspended", "closed"], weights=[85, 10, 5])[0],
            )
        )
    cursor.executemany("INSERT INTO customers VALUES (?, ?, ?, ?, ?, ?)", customers)
    return customers


def seed_orders(cursor: sqlite3.Cursor, customers: list[tuple]) -> list[tuple]:
    orders = []
    for i in range(1, N_ORDERS + 1):
        cust = random.choice(customers)
        status = random.choices(
            ["delivered", "shipped", "processing", "cancelled", "refunded"],
            weights=[50, 20, 10, 10, 10],
        )[0]
        amount = round(random.uniform(15, 450), 2)
        # ~15% of products are deliberately non-refund-eligible (e.g. digital
        # goods) so the refund agent's eligibility tool has a real edge case
        # to catch before the request ever reaches a human.
        refund_eligible = 0 if random.random() < 0.15 else 1

        orders.append(
            (
                f"ORD-{2000 + i}",
                cust[0],
                fake.word().capitalize() + " " + random.choice(["Plan", "Package", "Kit", "License"]),
                amount,
                status,
                fake.date_between(start_date="-6m", end_date="today").isoformat(),
                refund_eligible,
            )
        )
    cursor.executemany("INSERT INTO orders VALUES (?, ?, ?, ?, ?, ?, ?)", orders)
    return orders


def seed_invoices(cursor: sqlite3.Cursor, customers: list[tuple]) -> None:
    invoices = []
    for i in range(1, N_INVOICES + 1):
        cust = random.choice(customers)
        billing_date = fake.date_between(start_date="-1y", end_date="today")
        due_date = billing_date + timedelta(days=30)
        invoices.append(
            (
                f"INV-{3000 + i}",
                cust[0],
                round(random.uniform(9.99, 299.99), 2),
                random.choices(["paid", "pending", "overdue", "failed"], weights=[70, 15, 10, 5])[0],
                billing_date.isoformat(),
                due_date.isoformat(),
                fake.sentence(nb_words=6),
            )
        )
    cursor.executemany("INSERT INTO invoices VALUES (?, ?, ?, ?, ?, ?, ?)", invoices)


def seed_known_demo_records(cursor: sqlite3.Cursor) -> None:
    """
    Insert a handful of hand-picked records with predictable IDs so the
    README walkthrough / frontend demo can reference concrete, reliable
    scenarios (auto-approved refund, human-approval-required refund,
    ineligible refund, overdue invoice).
    """
    cursor.execute(
        "INSERT OR REPLACE INTO customers VALUES (?, ?, ?, ?, ?, ?)",
        ("CUST-DEMO1", "Amina Fathy", "amina.demo@example.com", "Pro", "2023-01-15", "active"),
    )
    cursor.executemany(
        "INSERT OR REPLACE INTO orders VALUES (?, ?, ?, ?, ?, ?, ?)",
        [
            ("ORD-DEMO-SMALL", "CUST-DEMO1", "Starter Kit", 45.00, "delivered", "2026-06-01", 1),
            ("ORD-DEMO-LARGE", "CUST-DEMO1", "Enterprise License", 350.00, "delivered", "2026-06-15", 1),
            ("ORD-DEMO-INELIGIBLE", "CUST-DEMO1", "Digital Course Bundle", 80.00, "delivered", "2026-05-20", 0),
        ],
    )
    cursor.executemany(
        "INSERT OR REPLACE INTO invoices VALUES (?, ?, ?, ?, ?, ?, ?)",
        [
            ("INV-DEMO-OVERDUE", "CUST-DEMO1", 129.99, "overdue", "2026-05-01", "2026-05-31", "Monthly Pro subscription"),
        ],
    )


def main() -> None:
    conn = build_connection()
    cursor = conn.cursor()
    customers = seed_customers(cursor)
    seed_orders(cursor, customers)
    seed_invoices(cursor, customers)
    seed_known_demo_records(cursor)
    conn.commit()
    conn.close()
    print(f"Database seeded at {DB_PATH}")
    print(f"  customers: {N_CUSTOMERS} (+1 demo)")
    print(f"  orders:    {N_ORDERS} (+3 demo)")
    print(f"  invoices:  {N_INVOICES} (+1 demo)")
    print("Demo customer_id: CUST-DEMO1")
    print("Demo orders: ORD-DEMO-SMALL (auto-approve), ORD-DEMO-LARGE (needs approval), "
          "ORD-DEMO-INELIGIBLE (not refundable)")


if __name__ == "__main__":
    main()
