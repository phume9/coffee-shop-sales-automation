performance_schemainformation_schemaperformance_schemaViews-- =====================================================
-- Campus Coffee Shop Database
-- Part 1: Schema + starter data
-- Run this whole file in MySQL Workbench (lightning bolt icon)
-- =====================================================

DROP DATABASE IF EXISTS coffee_shop;
CREATE DATABASE coffee_shop;
USE coffee_shop;

-- ---------- Customers ----------
CREATE TABLE customers (
    customer_id   INT AUTO_INCREMENT PRIMARY KEY,
    first_name    VARCHAR(50)  NOT NULL,
    last_name     VARCHAR(50)  NOT NULL,
    email         VARCHAR(100) UNIQUE,
    joined_date   DATE         NOT NULL
);

-- ---------- Employees ----------
CREATE TABLE employees (
    employee_id   INT AUTO_INCREMENT PRIMARY KEY,
    first_name    VARCHAR(50)  NOT NULL,
    last_name     VARCHAR(50)  NOT NULL,
    role          VARCHAR(30)  NOT NULL,   -- Barista, Shift Lead, Manager
    hire_date     DATE         NOT NULL
);

-- ---------- Products ----------
CREATE TABLE products (
    product_id    INT AUTO_INCREMENT PRIMARY KEY,
    product_name  VARCHAR(100) NOT NULL,
    category      VARCHAR(30)  NOT NULL,   -- Coffee, Tea, Pastry, Snack
    price         DECIMAL(6,2) NOT NULL,
    cost          DECIMAL(6,2) NOT NULL    -- what it costs the shop to make
);

-- ---------- Inventory (one row per product) ----------
CREATE TABLE inventory (
    product_id        INT PRIMARY KEY,
    quantity_on_hand  INT NOT NULL DEFAULT 0,
    reorder_level     INT NOT NULL DEFAULT 10,  -- alert when stock falls below this
    FOREIGN KEY (product_id) REFERENCES products(product_id)
);

-- ---------- Orders (one row per receipt) ----------
CREATE TABLE orders (
    order_id        INT AUTO_INCREMENT PRIMARY KEY,
    customer_id     INT NULL,                 -- NULL = walk-in, not a member
    employee_id     INT NOT NULL,
    order_datetime  DATETIME NOT NULL,
    payment_method  VARCHAR(20) NOT NULL,     -- Card, Cash, Mobile
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id),
    FOREIGN KEY (employee_id) REFERENCES employees(employee_id)
);

-- ---------- Order Items (one row per item on a receipt) ----------
CREATE TABLE order_items (
    order_item_id  INT AUTO_INCREMENT PRIMARY KEY,
    order_id       INT NOT NULL,
    product_id     INT NOT NULL,
    quantity       INT NOT NULL,
    unit_price     DECIMAL(6,2) NOT NULL,     -- price at time of sale
    FOREIGN KEY (order_id)   REFERENCES orders(order_id),
    FOREIGN KEY (product_id) REFERENCES products(product_id)
);

-- =====================================================
-- Starter data (orders will be generated later with Python)
-- =====================================================

INSERT INTO employees (first_name, last_name, role, hire_date) VALUES
('Maya',   'Lopez',   'Manager',    '2023-01-15'),
('Jordan', 'Kim',     'Shift Lead', '2023-08-01'),
('Ava',    'Patel',   'Barista',    '2024-02-10'),
('Liam',   'Nguyen',  'Barista',    '2024-09-05'),
('Sofia',  'Garcia',  'Barista',    '2025-01-20');

INSERT INTO products (product_name, category, price, cost) VALUES
('Espresso',            'Coffee', 2.75, 0.60),
('Latte',               'Coffee', 4.50, 1.10),
('Cappuccino',          'Coffee', 4.25, 1.00),
('Cold Brew',           'Coffee', 4.00, 0.80),
('Caramel Macchiato',   'Coffee', 5.25, 1.40),
('Chai Latte',          'Tea',    4.25, 1.05),
('Green Tea',           'Tea',    2.95, 0.45),
('Blueberry Muffin',    'Pastry', 3.25, 1.10),
('Croissant',           'Pastry', 3.00, 0.95),
('Cinnamon Roll',       'Pastry', 3.75, 1.20),
('Bagel w/ Cream Cheese','Snack', 3.50, 1.00),
('Granola Bar',         'Snack',  2.25, 0.70);

INSERT INTO inventory (product_id, quantity_on_hand, reorder_level) VALUES
(1, 200, 50), (2, 150, 40), (3, 120, 40), (4, 80, 30),
(5, 60, 25),  (6, 90, 30),  (7, 100, 25), (8, 18, 20),
(9, 25, 20),  (10, 12, 15), (11, 40, 15), (12, 70, 20);

INSERT INTO customers (first_name, last_name, email, joined_date) VALUES
('Emma',    'Johnson',  'emma.j@example.com',    '2025-08-25'),
('Noah',    'Williams', 'noah.w@example.com',    '2025-08-28'),
('Olivia',  'Brown',    'olivia.b@example.com',  '2025-09-02'),
('Ethan',   'Davis',    'ethan.d@example.com',   '2025-09-10'),
('Isabella','Miller',   'isabella.m@example.com','2025-09-15'),
('Lucas',   'Wilson',   'lucas.w@example.com',   '2025-10-01'),
('Mia',     'Moore',    'mia.m@example.com',     '2025-10-12'),
('Aiden',   'Taylor',   'aiden.t@example.com',   '2025-11-03'),
('Harper',  'Anderson', 'harper.a@example.com',  '2026-01-14'),
('Elijah',  'Thomas',   'elijah.t@example.com',  '2026-02-20');
