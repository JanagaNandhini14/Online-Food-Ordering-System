from flask import Flask, render_template, request, jsonify, redirect, url_for
import sqlite3
from datetime import datetime

app = Flask(__name__)
DB_NAME = "food_ordering.db"


def get_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS menu (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            category TEXT NOT NULL,
            price REAL NOT NULL,
            description TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_name TEXT NOT NULL,
            phone TEXT NOT NULL,
            address TEXT NOT NULL,
            total_amount REAL NOT NULL,
            order_date TEXT NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS order_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER NOT NULL,
            item_name TEXT NOT NULL,
            quantity INTEGER NOT NULL,
            price REAL NOT NULL,
            subtotal REAL NOT NULL,
            FOREIGN KEY(order_id) REFERENCES orders(id)
        )
    """)

    cursor.execute("SELECT COUNT(*) FROM menu")
    count = cursor.fetchone()[0]

    if count == 0:
        sample_menu = [
            ("Veg Burger", "Fast Food", 120, "Fresh burger with veggie patty"),
            ("Chicken Burger", "Fast Food", 150, "Burger with crispy chicken patty"),
            ("Pizza Margherita", "Pizza", 250, "Classic cheese pizza"),
            ("Paneer Pizza", "Pizza", 280, "Pizza topped with paneer and cheese"),
            ("French Fries", "Snacks", 90, "Crispy golden fries"),
            ("Pasta Alfredo", "Pasta", 180, "Creamy white sauce pasta"),
            ("Fried Rice", "Rice", 160, "Veg fried rice with sauces"),
            ("Chicken Biryani", "Rice", 220, "Aromatic biryani with chicken"),
            ("Cold Coffee", "Beverages", 80, "Chilled coffee with milk"),
            ("Fresh Juice", "Beverages", 70, "Seasonal fruit juice")
        ]
        cursor.executemany(
            "INSERT INTO menu (name, category, price, description) VALUES (?, ?, ?, ?)",
            sample_menu
        )

    conn.commit()
    conn.close()


@app.route("/")
def home():
    conn = get_connection()
    menu_items = conn.execute("SELECT * FROM menu ORDER BY category, name").fetchall()
    conn.close()
    return render_template("index.html", menu_items=menu_items)


@app.route("/place_order", methods=["POST"])
def place_order():
    data = request.get_json()

    customer_name = data.get("customer_name", "").strip()
    phone = data.get("phone", "").strip()
    address = data.get("address", "").strip()
    cart = data.get("cart", [])

    if not customer_name or not phone or not address:
        return jsonify({"success": False, "message": "Please fill all customer details."}), 400

    if not cart:
        return jsonify({"success": False, "message": "Cart is empty."}), 400

    total_amount = sum(item["price"] * item["quantity"] for item in cart)
    order_date = datetime.now().strftime("%d-%m-%Y %H:%M:%S")

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO orders (customer_name, phone, address, total_amount, order_date)
        VALUES (?, ?, ?, ?, ?)
    """, (customer_name, phone, address, total_amount, order_date))

    order_id = cursor.lastrowid

    for item in cart:
        subtotal = item["price"] * item["quantity"]
        cursor.execute("""
            INSERT INTO order_items (order_id, item_name, quantity, price, subtotal)
            VALUES (?, ?, ?, ?, ?)
        """, (order_id, item["name"], item["quantity"], item["price"], subtotal))

    conn.commit()
    conn.close()

    return jsonify({
        "success": True,
        "message": "Order placed successfully.",
        "order_id": order_id
    })


@app.route("/orders")
def view_orders():
    conn = get_connection()
    orders = conn.execute("SELECT * FROM orders ORDER BY id DESC").fetchall()

    order_data = []
    for order in orders:
        items = conn.execute(
            "SELECT * FROM order_items WHERE order_id = ?",
            (order["id"],)
        ).fetchall()

        order_data.append({
            "order": order,
            "items": items
        })

    conn.close()
    return render_template("orders.html", order_data=order_data)


if __name__ == "__main__":
    init_db()
    app.run(debug=True)