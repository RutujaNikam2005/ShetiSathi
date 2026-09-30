from flask import Flask, render_template, request, redirect
import sqlite3
from database import create_database, add_missing_rates, DB_PATH

app = Flask(__name__)

create_database()
add_missing_rates()
def create_expense_table():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            expense_type TEXT NOT NULL,
            description TEXT,
            amount REAL NOT NULL,
            expense_date TEXT NOT NULL
        )
    """)

    conn.commit()
    conn.close()


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/test-db")
def test_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM works")
    count = cursor.fetchone()[0]

    conn.close()

    return f"Database connected! Total work records: {count}"

@app.route("/add-work", methods=["GET", "POST"])
def add_work():

    if request.method == "POST":

        customer_name = request.form["customer_name"]
        village = request.form["village"]
        mobile = request.form["mobile"]
        service = request.form["service"]
        calculation_type = request.form["calculation_type"]
        quantity = float(request.form["quantity"])
        paid = float(request.form["paid"])
        work_date = request.form["work_date"]

        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Get rate automatically from database
        cursor.execute("""
            SELECT rate
            FROM rates
            WHERE service = ?
            AND calculation_type = ?
        """, (service, calculation_type))

        rate_row = cursor.fetchone()

        if rate_row:
            rate = float(rate_row[0])
        else:
            conn.close()
            return "Rate not found for selected service and calculation type."

        # Calculate total and remaining
        total = quantity * rate
        remaining = total - paid

        if remaining < 0:
            remaining = 0

        cursor.execute("""
            INSERT INTO works
            (customer_name, village, mobile, service, calculation_type,
             quantity, rate, total, paid, remaining, work_date)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            customer_name,
            village,
            mobile,
            service,
            calculation_type,
            quantity,
            rate,
            total,
            paid,
            remaining,
            work_date
        ))

        conn.commit()
        conn.close()

        return "Work saved successfully! <br><br><a href='/'>Back to Dashboard</a>"

    return render_template("add_work.html")

@app.route("/get-rate")
def get_rate():

    service = request.args.get("service")
    calculation_type = request.args.get("calculation_type")

    print("SERVICE:", service)
    print("CALCULATION TYPE:", calculation_type)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT rate
        FROM rates
        WHERE service = ?
        AND calculation_type = ?
    """, (service, calculation_type))

    result = cursor.fetchone()

    print("RATE RESULT:", result)

    conn.close()

    if result:
        return {"rate": float(result[0])}

    return {"rate": 0}


@app.route("/pending-payments")
def pending_payments():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT customer_name, mobile, service, total, paid, remaining, work_date
        FROM works
        WHERE remaining > 0
        ORDER BY work_date DESC
    """)

    records = cursor.fetchall()

    total_pending = sum(record[5] for record in records)

    conn.close()

    return render_template(
        "pending_payments.html",
        records=records,
        total_pending=total_pending
    )

@app.route("/search-customer")
def search_customer():
    search = request.args.get("search", "").strip()

    records = []

    if search:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT customer_name, village, mobile, service,
                   quantity, rate, total, paid, remaining, work_date
            FROM works
            WHERE customer_name LIKE ?
               OR mobile LIKE ?
            ORDER BY work_date DESC
        """, (f"%{search}%", f"%{search}%"))

        records = cursor.fetchall()

        conn.close()

    return render_template(
        "search_customer.html",
        records=records,
        search=search,
        searched=bool(search)
    )

@app.route("/daily-report")
def daily_report():
    selected_date = request.args.get("date", "").strip()

    records = []
    total_works = 0
    total_amount = 0
    total_paid = 0
    total_remaining = 0

    if selected_date:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT customer_name, village, service,
                   quantity, rate, total, paid, remaining
            FROM works
            WHERE work_date = ?
            ORDER BY id DESC
        """, (selected_date,))

        records = cursor.fetchall()

        for record in records:
            total_amount += record[5] or 0
            total_paid += record[6] or 0
            total_remaining += record[7] or 0

        total_works = len(records)

        conn.close()

    return render_template(
        "daily_report.html",
        records=records,
        selected_date=selected_date,
        total_works=total_works,
        total_amount=total_amount,
        total_paid=total_paid,
        total_remaining=total_remaining,
        searched=bool(selected_date)
    )

@app.route("/view-records")
def view_records():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id,customer_name, village, mobile, service,
               quantity, rate, total, paid, remaining, work_date
        FROM works
        ORDER BY id DESC
    """)

    records = cursor.fetchall()

    conn.close()

    return render_template(
        "view_records.html",
        records=records
    )

@app.route("/manage-rates", methods=["GET", "POST"])
def manage_rates():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    if request.method == "POST":
        rate_id = request.form["rate_id"]
        new_rate = float(request.form["rate"])

        cursor.execute("""
            UPDATE rates
            SET rate = ?
            WHERE id = ?
        """, (new_rate, rate_id))

        conn.commit()

    cursor.execute("""
        SELECT id, service, calculation_type, rate
        FROM rates
        ORDER BY service, calculation_type
    """)

    rates = cursor.fetchall()

    conn.close()

    return render_template(
        "manage_rates.html",
        rates=rates
    )

@app.route("/expenses", methods=["GET", "POST"])
def expenses():

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    if request.method == "POST":

        expense_type = request.form["expense_type"]
        description = request.form["description"]
        amount = float(request.form["amount"])
        expense_date = request.form["expense_date"]

        cursor.execute("""
            INSERT INTO expenses
            (expense_type, description, amount, expense_date)
            VALUES (?, ?, ?, ?)
        """, (
            expense_type,
            description,
            amount,
            expense_date
        ))

        conn.commit()

    # Get all expense records
    cursor.execute("""
        SELECT id, expense_type, description, amount, expense_date
        FROM expenses
        ORDER BY id DESC
    """)

    expense_records = cursor.fetchall()

    # Get overall expense
    cursor.execute("""
        SELECT COALESCE(SUM(amount), 0)
        FROM expenses
    """)

    total_expenses = cursor.fetchone()[0]

    conn.close()

    return render_template(
        "expense.html",
        expenses=expense_records,
        total_expenses=total_expenses
    )
@app.route("/profit-loss")
def profit_loss():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Total income from all work
    cursor.execute("""
        SELECT COALESCE(SUM(total), 0)
        FROM works
    """)

    total_income = cursor.fetchone()[0]

    # Total expenses
    cursor.execute("""
        SELECT COALESCE(SUM(amount), 0)
        FROM expenses
    """)

    total_expenses = cursor.fetchone()[0]

    # Profit
    profit = total_income - total_expenses

    conn.close()

    return render_template(
        "profit_loss.html",
        total_income=total_income,
        total_expenses=total_expenses,
        profit=profit
    )

@app.route("/payment-history")
def payment_history():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT customer_name, mobile, service, paid, remaining, work_date
        FROM works
        WHERE paid > 0
        ORDER BY work_date DESC, id DESC
    """)

    payments = cursor.fetchall()

    conn.close()

    return render_template(
        "payment_history.html",
        payments=payments
    )

@app.route("/edit-work/<int:work_id>", methods=["GET", "POST"])
def edit_work(work_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    if request.method == "POST":
        customer_name = request.form["customer_name"]
        village = request.form["village"]
        mobile = request.form["mobile"]
        service = request.form["service"]
        quantity = float(request.form["quantity"])
        rate = float(request.form["rate"])
        paid = float(request.form["paid"])
        work_date = request.form["work_date"]

        total = quantity * rate
        remaining = total - paid

        cursor.execute("""
            UPDATE works
            SET customer_name = ?,
                village = ?,
                mobile = ?,
                service = ?,
                quantity = ?,
                rate = ?,
                total = ?,
                paid = ?,
                remaining = ?,
                work_date = ?
            WHERE id = ?
        """, (
            customer_name,
            village,
            mobile,
            service,
            quantity,
            rate,
            total,
            paid,
            remaining,
            work_date,
            work_id
        ))

        conn.commit()
        conn.close()

        return render_template(
            "edit_work.html",
            record=(
                work_id,
                customer_name,
                village,
                mobile,
                service,
                quantity,
                rate,
                total,
                paid,
                remaining,
                work_date
            )
        )

    cursor.execute("""
        SELECT id, customer_name, village, mobile, service,
               quantity, rate, total, paid, remaining, work_date
        FROM works
        WHERE id = ?
    """, (work_id,))

    record = cursor.fetchone()

    conn.close()

    return render_template(
        "edit_work.html",
        record=record
    )

@app.route("/delete-work/<int:work_id>")
def delete_work(work_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        DELETE FROM works
        WHERE id = ?
    """, (work_id,))

    conn.commit()
    conn.close()

    return redirect("/view-records")

@app.route("/delete-expense/<int:expense_id>")
def delete_expense(expense_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        DELETE FROM expenses
        WHERE id = ?
    """, (expense_id,))

    conn.commit()
    conn.close()

    return redirect("/expenses")

if __name__ == "__main__":
    create_expense_table()
    app.run(host="0.0.0.0", port=5000, debug=True)
