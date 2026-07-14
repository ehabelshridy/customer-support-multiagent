-- ============================================================
-- Customer Support Multi-Agent System - SQLite schema
-- ============================================================

DROP TABLE IF EXISTS refund_requests;
DROP TABLE IF EXISTS orders;
DROP TABLE IF EXISTS invoices;
DROP TABLE IF EXISTS customers;

-- ============================================
-- customers
-- ============================================
CREATE TABLE customers (
    customer_id     TEXT PRIMARY KEY,
    name            TEXT NOT NULL,
    email           TEXT NOT NULL,
    plan            TEXT CHECK(plan IN ('Basic', 'Pro', 'Enterprise')),
    signup_date     DATE,
    account_status  TEXT CHECK(account_status IN ('active', 'suspended', 'closed')) DEFAULT 'active'
);

-- ============================================
-- invoices (used by the Billing agent)
-- ============================================
CREATE TABLE invoices (
    invoice_id   TEXT PRIMARY KEY,
    customer_id  TEXT NOT NULL,
    amount       REAL NOT NULL,
    status       TEXT CHECK(status IN ('paid', 'pending', 'overdue', 'failed')),
    billing_date DATE,
    due_date     DATE,
    description  TEXT,
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
);

-- ============================================
-- orders (used by the Refund agent)
-- ============================================
CREATE TABLE orders (
    order_id        TEXT PRIMARY KEY,
    customer_id     TEXT NOT NULL,
    product_name    TEXT NOT NULL,
    amount          REAL NOT NULL,
    status          TEXT CHECK(status IN ('delivered', 'shipped', 'processing', 'cancelled', 'refunded')),
    order_date      DATE,
    refund_eligible BOOLEAN DEFAULT 1,
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
);

-- ============================================
-- refund_requests (audit trail for the human-in-the-loop gate)
-- ============================================
CREATE TABLE refund_requests (
    request_id       TEXT PRIMARY KEY,
    order_id         TEXT NOT NULL,
    customer_id      TEXT NOT NULL,
    requested_amount REAL NOT NULL,
    reason           TEXT,
    status           TEXT CHECK(status IN ('pending_approval', 'approved', 'rejected', 'auto_approved')),
    requires_human   BOOLEAN,
    resolved_by      TEXT,
    created_at       TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
