import sqlite3
import os
import sys


# -----------------------------------------
# Find application folder
# -----------------------------------------

if getattr(sys, 'frozen', False):
    # When running as .exe
    BASE_DIR = os.path.dirname(sys.executable)
else:
    # When running normally with Python
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))


# -----------------------------------------
# Database location
# -----------------------------------------

DB_PATH = os.path.join(BASE_DIR, "shetisathi.db")


# -----------------------------------------
# Create Database
# -----------------------------------------

def create_database():

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # -----------------------------------------
    # WORKS TABLE
    # -----------------------------------------

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS works (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_name TEXT,
            village TEXT,
            mobile TEXT,
            service TEXT,
            calculation_type TEXT,
            quantity REAL,
            rate REAL,
            total REAL,
            paid REAL,
            remaining REAL,
            work_date TEXT
        )
    """)

    # -----------------------------------------
    # RATES TABLE
    # -----------------------------------------

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS rates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            service TEXT,
            calculation_type TEXT,
            rate REAL
        )
    """)

    # -----------------------------------------
    # DEFAULT RATES
    # -----------------------------------------

    cursor.execute("SELECT COUNT(*) FROM rates")
    count = cursor.fetchone()[0]

    if count == 0:

        default_rates = [

            ("नांगरणी", "प्रति एकर", 800),
            ("नांगरणी", "प्रति तास", 3500),

            ("पेरणी BBF", "प्रति एकर", 2000),
            ("पेरणी सारा", "प्रति एकर", 2000),

            ("रोटाव्हेटर", "प्रति एकर", 3500),

            ("ट्रॉली", "प्रति फेरा", 500),

            ("फणपाळी", "प्रति एकर", 2000),
            ("फणपाळी", "प्रति तास", 1000),

            ("सरी सोडणे", "प्रति एकर", 2000),

            ("सोयाबीन मळणी", "प्रति पोते", 500),
            ("गहू मळणी", "प्रति पोते", 500),
            ("हरभरा मळणी", "प्रति पोते", 500),
            ("ज्वारी मळणी", "प्रति पोते", 250)
        ]

        cursor.executemany("""
            INSERT INTO rates (
                service,
                calculation_type,
                rate
            )
            VALUES (?, ?, ?)
        """, default_rates)

    # -----------------------------------------
    # PAYMENT HISTORY TABLE
    # -----------------------------------------

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS payments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            work_id INTEGER,
            customer_name TEXT,
            amount REAL,
            payment_date TEXT,
            payment_time TEXT
        )
    """)

    # -----------------------------------------
    # EXPENSES TABLE
    # -----------------------------------------

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            expense_type TEXT,
            amount REAL,
            expense_date TEXT,
            description TEXT
        )
    """)

    # -----------------------------------------
    # Add payment_time if old database
    # -----------------------------------------

    try:
        cursor.execute(
            "ALTER TABLE payments ADD COLUMN payment_time TEXT"
        )
    except sqlite3.OperationalError:
        pass

    # -----------------------------------------
    # Save
    # -----------------------------------------

    conn.commit()
    conn.close()

    print("Database created successfully!")
    print("Database location:", DB_PATH)


# -----------------------------------------
# Add Missing Rates
# -----------------------------------------

def add_missing_rates():

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT COUNT(*)
        FROM rates
        WHERE service = ? AND calculation_type = ?
    """, ("पेरणी सारा", "प्रति एकर"))

    count = cursor.fetchone()[0]

    if count == 0:

        cursor.execute("""
            INSERT INTO rates (
                service,
                calculation_type,
                rate
            )
            VALUES (?, ?, ?)
        """, ("पेरणी सारा", "प्रति एकर", 2000))

        print("पेरणी सारा rate added successfully!")

    conn.commit()
    conn.close()


# -----------------------------------------
# Run database directly
# -----------------------------------------

if __name__ == "__main__":
    create_database()
    add_missing_rates()