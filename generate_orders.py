"""
Campus Coffee Shop - Step 2: Generate realistic sample orders

What this script does:
  1. Connects to the coffee_shop database in MySQL
  2. Deletes any old orders (so you can safely run it again)
  3. Creates about 60 days of fake orders, ending yesterday,
     with realistic patterns (morning rush, busier weekdays,
     coffee sells more than snacks, some loyalty members)
  4. Saves everything to the orders and order_items tables

Run it from Command Prompt with:   python generate_orders.py
"""

import random
from datetime import datetime, timedelta
from getpass import getpass

import mysql.connector

# ---------- Settings you can change ----------
DAYS_OF_HISTORY = 60          # how many days of orders to create
ORDERS_PER_WEEKDAY = (25, 45) # random number of orders on Mon-Fri
ORDERS_PER_WEEKEND = (12, 25) # random number of orders on Sat-Sun
MEMBER_CHANCE = 0.40          # 40% of orders come from loyalty members

# Hours the shop is open (7am to 7pm) and how busy each hour is.
# Bigger number = busier. Notice the 7-9am morning rush.
HOUR_WEIGHTS = {
    7: 10, 8: 14, 9: 11, 10: 7, 11: 6, 12: 8,
    13: 7, 14: 5, 15: 6, 16: 5, 17: 4, 18: 3,
}

# How popular each category is (coffee sells the most)
CATEGORY_WEIGHTS = {"Coffee": 6, "Tea": 2, "Pastry": 3, "Snack": 1}

PAYMENT_METHODS = ["Card", "Card", "Card", "Mobile", "Mobile", "Cash"]


def main():
    # ---------- 1. Connect to MySQL ----------
    # getpass hides your password while you type it,
    # so it never gets saved inside this file.
    password = getpass("Enter your MySQL root password: ")

    conn = mysql.connector.connect(
        host="127.0.0.1",
        port=3306,
        user="root",
        password=password,
        database="coffee_shop",
    )
    cursor = conn.cursor()
    print("Connected to coffee_shop!")

    # ---------- 2. Clear out old orders ----------
    cursor.execute("DELETE FROM order_items")
    cursor.execute("DELETE FROM orders")
    cursor.execute("ALTER TABLE order_items AUTO_INCREMENT = 1")
    cursor.execute("ALTER TABLE orders AUTO_INCREMENT = 1")

    # ---------- 3. Load existing products, customers, employees ----------
    cursor.execute("SELECT product_id, category, price FROM products")
    products = cursor.fetchall()   # list of (id, category, price)

    cursor.execute("SELECT customer_id FROM customers")
    customer_ids = [row[0] for row in cursor.fetchall()]

    cursor.execute("SELECT employee_id FROM employees")
    employee_ids = [row[0] for row in cursor.fetchall()]

    # Each product's chance of being picked depends on its category
    product_weights = [CATEGORY_WEIGHTS[p[1]] for p in products]

    hours = list(HOUR_WEIGHTS.keys())
    hour_weights = list(HOUR_WEIGHTS.values())

    # ---------- 4. Create the orders, one day at a time ----------
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    start_day = today - timedelta(days=DAYS_OF_HISTORY)

    total_orders = 0
    total_items = 0

    for day_number in range(DAYS_OF_HISTORY):
        day = start_day + timedelta(days=day_number)
        is_weekend = day.weekday() >= 5   # 5 = Saturday, 6 = Sunday

        low, high = ORDERS_PER_WEEKEND if is_weekend else ORDERS_PER_WEEKDAY
        orders_today = random.randint(low, high)

        for _ in range(orders_today):
            # Pick a time, weighted toward the morning rush
            hour = random.choices(hours, weights=hour_weights)[0]
            order_time = day.replace(hour=hour, minute=random.randint(0, 59))

            # Loyalty member or walk-in (NULL)?
            if random.random() < MEMBER_CHANCE:
                customer_id = random.choice(customer_ids)
            else:
                customer_id = None

            employee_id = random.choice(employee_ids)
            payment = random.choice(PAYMENT_METHODS)

            cursor.execute(
                """INSERT INTO orders
                   (customer_id, employee_id, order_datetime, payment_method)
                   VALUES (%s, %s, %s, %s)""",
                (customer_id, employee_id, order_time, payment),
            )
            order_id = cursor.lastrowid   # the ID MySQL just created

            # Each order has 1 to 3 different products
            num_items = random.choices([1, 2, 3], weights=[55, 35, 10])[0]
            chosen = set()
            while len(chosen) < num_items:
                chosen.add(random.choices(products, weights=product_weights)[0])

            for product_id, _category, price in chosen:
                quantity = random.choices([1, 2], weights=[85, 15])[0]
                cursor.execute(
                    """INSERT INTO order_items
                       (order_id, product_id, quantity, unit_price)
                       VALUES (%s, %s, %s, %s)""",
                    (order_id, product_id, quantity, price),
                )
                total_items += 1

            total_orders += 1

    # ---------- 5. Save everything ----------
    conn.commit()   # nothing is saved until you commit!
    cursor.close()
    conn.close()

    print(f"Done! Created {total_orders} orders with {total_items} order items.")
    print(f"Dates: {start_day.date()} to {(today - timedelta(days=1)).date()}")


if __name__ == "__main__":
    main()
