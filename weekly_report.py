"""
Campus Coffee Shop - Step 4: Automated Weekly Report

What this script does:
  1. Reads your settings from config.ini (database + email)
  2. Runs the key business queries for the most recent 7 days
  3. Compares this week with the week before (% change)
  4. Builds a clean HTML report and saves it in the "reports" folder
  5. Emails the report (only if send_email = yes in config.ini)

Run it with:   python weekly_report.py
"""

import configparser
import smtplib
from datetime import timedelta
from email.message import EmailMessage
from pathlib import Path

import mysql.connector

BASE_DIR = Path(__file__).resolve().parent     # the folder this script is in
CONFIG_FILE = BASE_DIR / "config.ini"
REPORTS_DIR = BASE_DIR / "reports"


# =====================================================
# 1. Settings
# =====================================================
def load_config():
    """Read database and email settings from config.ini."""
    if not CONFIG_FILE.exists():
        raise SystemExit(
            "config.ini not found. Make a copy of config_example.ini, "
            "rename it to config.ini, and fill in your details."
        )
    config = configparser.ConfigParser()
    config.read(CONFIG_FILE)
    return config


# =====================================================
# 2. Get the data
# =====================================================
def run_query(cursor, sql, params=()):
    cursor.execute(sql, params)
    return cursor.fetchall()


def totals_for(cursor, start, end):
    """Orders and revenue between two dates (inclusive)."""
    row = run_query(cursor, """
        SELECT COUNT(DISTINCT o.order_id),
               COALESCE(SUM(oi.quantity * oi.unit_price), 0)
        FROM orders o
        JOIN order_items oi ON o.order_id = oi.order_id
        WHERE DATE(o.order_datetime) BETWEEN %s AND %s
    """, (start, end))[0]
    orders, revenue = int(row[0]), float(row[1])
    avg_order = revenue / orders if orders else 0
    return {"orders": orders, "revenue": revenue, "avg_order": avg_order}


def get_report_data(cursor):
    # The report covers the 7 most recent days that have sales
    latest = run_query(cursor, "SELECT DATE(MAX(order_datetime)) FROM orders")[0][0]
    if latest is None:
        raise SystemExit("No orders found. Run generate_orders.py first.")

    week_end = latest
    week_start = week_end - timedelta(days=6)
    prev_end = week_start - timedelta(days=1)
    prev_start = prev_end - timedelta(days=6)

    this_week = totals_for(cursor, week_start, week_end)
    last_week = totals_for(cursor, prev_start, prev_end)

    # Revenue per day this week (reuses the daily_sales view from Step 3)
    daily = run_query(cursor, """
        SELECT sale_date, orders, revenue
        FROM daily_sales
        WHERE sale_date BETWEEN %s AND %s
        ORDER BY sale_date
    """, (week_start, week_end))

    top_products = run_query(cursor, """
        SELECT p.product_name,
               SUM(oi.quantity),
               SUM(oi.quantity * oi.unit_price) AS revenue
        FROM orders o
        JOIN order_items oi ON o.order_id = oi.order_id
        JOIN products p     ON oi.product_id = p.product_id
        WHERE DATE(o.order_datetime) BETWEEN %s AND %s
        GROUP BY p.product_id, p.product_name
        ORDER BY revenue DESC
        LIMIT 5
    """, (week_start, week_end))

    busiest_hour = run_query(cursor, """
        SELECT HOUR(order_datetime) AS hr, COUNT(*) AS cnt
        FROM orders
        WHERE DATE(order_datetime) BETWEEN %s AND %s
        GROUP BY hr
        ORDER BY cnt DESC
        LIMIT 1
    """, (week_start, week_end))

    low_stock = run_query(cursor, """
        SELECT p.product_name, i.quantity_on_hand, i.reorder_level
        FROM inventory i
        JOIN products p ON i.product_id = p.product_id
        WHERE i.quantity_on_hand < i.reorder_level
        ORDER BY i.reorder_level - i.quantity_on_hand DESC
    """)

    return {
        "week_start": week_start,
        "week_end": week_end,
        "this_week": this_week,
        "last_week": last_week,
        "daily": daily,
        "top_products": top_products,
        "busiest_hour": busiest_hour[0] if busiest_hour else None,
        "low_stock": low_stock,
    }


# =====================================================
# 3. Build the report
# =====================================================
def pct_change(new, old):
    """Return a colored '+5.2%' style label comparing two numbers."""
    if not old:
        return '<span style="color:#888">n/a</span>'
    change = (new - old) / old * 100
    color = "#1a7f37" if change >= 0 else "#c62828"   # green up, red down
    arrow = "&#9650;" if change >= 0 else "&#9660;"
    return f'<span style="color:{color}">{arrow} {change:+.1f}%</span>'


def format_hour(hour):
    """Turn 8 into '8:00 AM', 14 into '2:00 PM'."""
    suffix = "AM" if hour < 12 else "PM"
    return f"{(hour % 12) or 12}:00 {suffix}"


def build_html(d):
    tw, lw = d["this_week"], d["last_week"]
    period = f'{d["week_start"]:%b %d} &ndash; {d["week_end"]:%b %d, %Y}'

    cell = 'style="padding:8px 12px;border-bottom:1px solid #eee"'
    head = 'style="padding:8px 12px;text-align:left;background:#f4efe9;color:#4e342e"'

    def kpi(label, value, change):
        return f"""
        <td style="padding:12px;background:#faf7f4;border-radius:8px;text-align:center">
          <div style="font-size:12px;color:#777">{label}</div>
          <div style="font-size:22px;font-weight:bold;color:#3e2723;margin:4px 0">{value}</div>
          <div style="font-size:12px">{change} vs last week</div>
        </td>"""

    kpis = (
        kpi("Revenue", f'${tw["revenue"]:,.2f}', pct_change(tw["revenue"], lw["revenue"]))
        + '<td style="width:8px"></td>'
        + kpi("Orders", f'{tw["orders"]:,}', pct_change(tw["orders"], lw["orders"]))
        + '<td style="width:8px"></td>'
        + kpi("Avg order", f'${tw["avg_order"]:.2f}', pct_change(tw["avg_order"], lw["avg_order"]))
    )

    product_rows = "".join(
        f"<tr><td {cell}>{i}. {name}</td><td {cell}>{int(units)}</td>"
        f"<td {cell}>${float(rev):,.2f}</td></tr>"
        for i, (name, units, rev) in enumerate(d["top_products"], start=1)
    )

    daily_rows = "".join(
        f"<tr><td {cell}>{day:%a %b %d}</td><td {cell}>{orders}</td>"
        f"<td {cell}>${float(rev):,.2f}</td></tr>"
        for day, orders, rev in d["daily"]
    )

    if d["low_stock"]:
        stock_rows = "".join(
            f"<tr><td {cell}>&#9888; {name}</td><td {cell}>{qty}</td><td {cell}>{level}</td></tr>"
            for name, qty, level in d["low_stock"]
        )
        stock_section = f"""
        <h3 style="color:#c62828">Low stock &ndash; reorder soon</h3>
        <table style="border-collapse:collapse;width:100%">
          <tr><th {head}>Product</th><th {head}>On hand</th><th {head}>Reorder level</th></tr>
          {stock_rows}
        </table>"""
    else:
        stock_section = '<p style="color:#1a7f37">&#10004; All products are above reorder level.</p>'

    if d["busiest_hour"]:
        hr, cnt = d["busiest_hour"]
        busiest = f"Busiest hour this week: <b>{format_hour(hr)}</b> ({cnt} orders). Make sure it's fully staffed."
    else:
        busiest = ""

    return f"""<!DOCTYPE html>
<html><body style="margin:0;padding:24px;background:#ffffff;font-family:Arial,sans-serif;color:#333">
<div style="max-width:640px;margin:0 auto">
  <h2 style="color:#3e2723;margin-bottom:4px">&#9749; Campus Coffee Shop &ndash; Weekly Report</h2>
  <div style="color:#777;margin-bottom:20px">{period}</div>

  <table style="width:100%;border-collapse:separate"><tr>{kpis}</tr></table>

  <p style="margin:20px 0">{busiest}</p>

  <h3 style="color:#4e342e">Top 5 products</h3>
  <table style="border-collapse:collapse;width:100%">
    <tr><th {head}>Product</th><th {head}>Units</th><th {head}>Revenue</th></tr>
    {product_rows}
  </table>

  <h3 style="color:#4e342e">Sales by day</h3>
  <table style="border-collapse:collapse;width:100%">
    <tr><th {head}>Day</th><th {head}>Orders</th><th {head}>Revenue</th></tr>
    {daily_rows}
  </table>

  {stock_section}

  <p style="color:#aaa;font-size:11px;margin-top:30px">
    Generated automatically by weekly_report.py from the coffee_shop MySQL database.
  </p>
</div>
</body></html>"""


# =====================================================
# 4. Send the email
# =====================================================
def send_email(config, html, subject):
    sender = config["email"]["sender"]
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = sender
    msg["To"] = config["email"]["recipient"]
    msg.set_content("This report is best viewed in an email app that shows HTML.")
    msg.add_alternative(html, subtype="html")

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(sender, config["email"]["app_password"].replace(" ", ""))
        server.send_message(msg)


# =====================================================
# Main program
# =====================================================
def main():
    config = load_config()
    db = config["mysql"]

    conn = mysql.connector.connect(
        host=db["host"],
        port=int(db["port"]),
        user=db["user"],
        password=db["password"],
        database=db["database"],
    )
    cursor = conn.cursor()
    data = get_report_data(cursor)
    cursor.close()
    conn.close()

    html = build_html(data)

    REPORTS_DIR.mkdir(exist_ok=True)
    report_file = REPORTS_DIR / f'weekly_report_{data["week_end"]}.html'
    report_file.write_text(html, encoding="utf-8")
    print(f"Report saved: {report_file}")

    if config.getboolean("email", "send_email", fallback=False):
        subject = f'Coffee Shop Weekly Report: week ending {data["week_end"]:%b %d}'
        send_email(config, html, subject)
        print(f'Email sent to {config["email"]["recipient"]}')
    else:
        print("Email is turned off (send_email = no in config.ini).")


if __name__ == "__main__":
    main()
