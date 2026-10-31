# ☕ Campus Coffee Shop: Sales Database & Automated Weekly Report

A small-business data project: I designed a MySQL database for a coffee shop, filled it with realistic sales data using Python, wrote SQL queries that answer real business questions, and automated a weekly KPI report that arrives by email every Monday morning without anyone touching it.

**Tools:** MySQL · SQL · Python · Windows Task Scheduler · Gmail SMTP

---

## The business problem

A small coffee shop owner has sales data but no time to dig through it. They want to know every week:

- How did sales do compared with last week?
- What are the best-selling products?
- When is the shop busiest, so shifts can be staffed properly?
- Which items are running low and need to be reordered?

This project answers those questions automatically.

---

## How it works

```
 MySQL database  →  SQL business queries  →  Python report script  →  Email every Monday 8 AM
 (6 tables)         (13 queries + a view)    (HTML KPI report)        (Windows Task Scheduler)
```

---

## 1. Database design

![ER diagram](images/er_diagram.png)

Six normalized tables: **customers**, **employees**, **products**, **inventory**, **orders**, and **order_items**.

Design decisions:
- **orders vs. order_items:** one receipt can contain many products, so line items live in their own table.
- **unit_price stored on each sale:** past sales stay accurate even if a menu price changes later.
- **customer_id can be NULL:** walk-in customers aren't loyalty members.
- **reorder_level in inventory:** powers the automatic low-stock alerts.

📄 [`coffee_shop_schema.sql`](coffee_shop_schema.sql)

---

## 2. Sample data

[`generate_orders.py`](generate_orders.py) creates about 60 days of orders (around 1,800) with realistic patterns:
- A morning rush from 7–9 AM
- Busier weekdays than weekends
- Coffee selling more than tea, pastries, and snacks
- About 40% of orders from loyalty members

---

## 3. Business questions answered with SQL

📄 [`business_queries.sql`](business_queries.sql)

| Area | Questions |
|---|---|
| **Sales** | Overall revenue and average order value · Top 5 products · Profit margin by category · Weekly trend |
| **Operations** | Busiest hours · Busiest days · Employee performance · Low-stock items |
| **Customers** | Do loyalty members spend more than walk-ins? · Top customers · Payment preferences · Products bought together |

**SQL techniques used:** multi-table JOINs, GROUP BY aggregation, CTEs, subqueries, a self-join (for product pairs), a reusable view, and date functions.

![Query results](images/query_results.png)

---

## 4. Automated weekly report

[`weekly_report.py`](weekly_report.py) connects to the database, runs the key queries for the latest week, and emails an HTML report that includes:

- Revenue, orders, and average order value, with **% change vs. last week**
- The busiest hour (for staffing)
- Top 5 products
- Sales by day
- **Low-stock alerts**

![Weekly report email](images/weekly_report_email.png)

Windows Task Scheduler runs it every **Monday at 8:00 AM**.

**Security:** database and email passwords live in a separate `config.ini` file that is excluded from this repository with `.gitignore`. A safe template is provided in [`config_example.ini`](config_example.ini).

---

## How to run it yourself

1. Run `coffee_shop_schema.sql` in MySQL Workbench.
2. Install the MySQL connector: `pip install mysql-connector-python`
3. Generate orders: `python generate_orders.py`
4. Run `business_queries.sql` in Workbench (this also creates the `daily_sales` view the report needs).
5. Copy `config_example.ini` to `config.ini` and fill in your details.
6. Create the report: `python weekly_report.py`

---

## Limitations and next steps

- The data is generated, so patterns like "products bought together" reflect the random weights rather than real customer behavior. With real point-of-sale data, the same queries would reveal genuine combo-deal opportunities.
- In a real shop, new orders would flow in from the register system every day. Here the dataset is fixed, so each weekly report shows the same week.
- Possible next steps: a Power BI dashboard on top of the same database, and updating inventory automatically as items sell.
