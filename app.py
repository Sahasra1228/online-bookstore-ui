from flask import Flask, render_template, request, jsonify, redirect, url_for, session, flash
import psycopg2
import os

app = Flask(__name__)
app.secret_key = "bookstore_secret"

# -----------------------------
# LOGIN CHECK
# -----------------------------
def check_login():
    return 'user' in session


# -----------------------------
# DATABASE CONNECTION
# -----------------------------
def get_db_connection():
    try:
        return psycopg2.connect(
            host=os.getenv("DB_HOST"),
            database=os.getenv("DB_NAME"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            port=5432,
            sslmode="require"
        )
    except Exception as e:
        print("DB CONNECTION ERROR:", e)
        return None


# -----------------------------
# HOME
# -----------------------------
@app.route('/')
def home():
    return redirect(url_for('admin_login'))


# -----------------------------
# LOGIN
# -----------------------------
@app.route('/admin_login', methods=['GET', 'POST'])
def admin_login():

    if request.method == 'POST':

        username = request.form['username']
        password = request.form['password']

        if username == "admin" and password == "admin123":
            session['user'] = username
            session['message'] = "Logged in successfully!"
            return redirect(url_for('dashboard'))
        else:
            flash("Invalid credentials")

    return render_template('admin_login.html')


# -----------------------------
# LOGOUT
# -----------------------------
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('admin_login'))


# -----------------------------
# DASHBOARD (FIXED)
# -----------------------------
@app.route('/dashboard')
def dashboard():

    if not check_login():
        return redirect(url_for('admin_login'))

    conn = get_db_connection()

    if conn is None:
        return "Database connection failed. Check Render environment variables."

    cur = conn.cursor()

    cur.execute("SELECT COUNT(*) FROM books")
    total_books = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM customers")
    total_customers = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM orders")
    total_orders = cur.fetchone()[0]

    cur.execute("SELECT COALESCE(SUM(total_amount), 0) FROM orders")
    total_revenue = cur.fetchone()[0] or 0

    cur.close()
    conn.close()

    data = {
        "books": total_books,
        "customers": total_customers,
        "orders": total_orders,
        "revenue": float(total_revenue)
    }

    return render_template("index.html", data=data)


# -----------------------------
# BOOKS
# -----------------------------
@app.route('/books')
def books():

    if not check_login():
        return redirect(url_for('admin_login'))

    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("SELECT * FROM books ORDER BY book_id ASC")
    rows = cur.fetchall()

    cur.close()
    conn.close()

    books = []
    for row in rows:
        books.append({
            "id": row[0],
            "title": row[1],
            "author": row[2],
            "genre": row[3],
            "published_year": row[4],
            "price": row[5],
            "stock": row[6]
        })

    return render_template('books.html', books=books)


# -----------------------------
# ADD BOOK
# -----------------------------
@app.route('/add_book', methods=['POST'])
def add_book():

    data = request.json

    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO books (title, author, genre, published_year, price, stock)
        VALUES (%s, %s, %s, %s, %s, %s)
    """, (
        data['title'],
        data['author'],
        data['genre'],
        data['published_year'],
        data['price'],
        data['stock']
    ))

    conn.commit()
    cur.close()
    conn.close()

    return jsonify({"message": "success"})

# -----------------------------
# EDIT BOOK
# -----------------------------
@app.route('/edit_book/<int:book_id>', methods=['PUT'])
def edit_book(book_id):

    data = request.get_json()

    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("""
        UPDATE books
        SET title=%s,
            author=%s,
            genre=%s,
            published_year=%s,
            price=%s,
            stock=%s
        WHERE book_id=%s
    """, (
        data['title'],
        data['author'],
        data['genre'],
        data['published_year'],
        data['price'],
        data['stock'],
        book_id
    ))

    conn.commit()
    cur.close()
    conn.close()

    return jsonify({"status": "success"})


# -----------------------------
# DELETE BOOK
# -----------------------------
@app.route('/delete_book/<int:book_id>', methods=['DELETE'])
def delete_book(book_id):

    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute(
        "DELETE FROM books WHERE book_id=%s",
        (book_id,)
    )

    conn.commit()
    cur.close()
    conn.close()

    return jsonify({"status": "success"})

# -----------------------------
# CUSTOMERS
# -----------------------------
@app.route('/customers')
def customers():

    if not check_login():
        return redirect(url_for('admin_login'))

    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("SELECT * FROM customers ORDER BY customer_id ASC")
    rows = cur.fetchall()

    cur.close()
    conn.close()

    customers = []
    for row in rows:
        customers.append({
            "id": row[0],
            "name": row[1],
            "email": row[2],
            "phone": row[3],
            "city": row[4],
            "country": row[5]
        })

    return render_template("customers.html", customers=customers)


# -----------------------------
# ADD CUSTOMER
# -----------------------------
@app.route('/add_customer', methods=['POST'])
def add_customer():

    data = request.get_json(force=True)

    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO customers (name, email, phone, city, country)
        VALUES (%s, %s, %s, %s, %s)
    """, (
        data['name'],
        data['email'],
        data['phone'],
        data['city'],
        data['country']
    ))

    conn.commit()
    cur.close()
    conn.close()

    return jsonify({"status": "success"})


# -----------------------------
# ORDERS
# -----------------------------
@app.route('/orders')
def orders():

    if not check_login():
        return redirect(url_for('admin_login'))

    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("SELECT * FROM orders ORDER BY order_id ASC")
    order_rows = cur.fetchall()

    cur.execute("SELECT customer_id, name FROM customers")
    customers = cur.fetchall()

    cur.execute("SELECT book_id, title FROM books")
    books = cur.fetchall()

    cur.close()
    conn.close()

    orders = []
    for row in order_rows:
        orders.append({
            "order_id": row[0],
            "customer_id": row[1],
            "book_id": row[2],
            "order_date": row[3],
            "quantity": row[4],
            "total_amount": row[5]
        })

    return render_template("orders.html", orders=orders, customers=customers, books=books)

@app.route('/debug-db')
def debug_db():
    import os
    return {
        "DB_HOST": os.environ.get("DB_HOST"),
        "DB_NAME": os.environ.get("DB_NAME"),
        "DB_USER": os.environ.get("DB_USER"),
        "DB_PASSWORD": "SET" if os.environ.get("DB_PASSWORD") else "NOT SET"
    }

@app.route('/analytics')
def analytics():

    if not check_login():
        return redirect(url_for('admin_login'))

    selected_year = request.args.get("year")

    conn = get_db_connection()
    cur = conn.cursor()

    # Get available years for filter dropdown
    cur.execute("""
        SELECT DISTINCT EXTRACT(YEAR FROM order_date)::int
        FROM orders
        ORDER BY 1
    """)
    years = [row[0] for row in cur.fetchall()]

    # Filter condition
    where_clause = ""
    params = []

    if selected_year:
        where_clause = """
            WHERE EXTRACT(YEAR FROM order_date) = %s
        """
        params.append(selected_year)

    # Dashboard cards
    cur.execute(f"""
        SELECT
            COUNT(*),
            COALESCE(SUM(total_amount),0),
            COALESCE(AVG(total_amount),0)
        FROM orders
        {where_clause}
    """, params)

    stats = cur.fetchone()

    # Monthly sales
    cur.execute(f"""
        SELECT
            TO_CHAR(order_date, 'Mon') AS month,
            SUM(total_amount) AS sales
        FROM orders
        {where_clause}
        GROUP BY month, EXTRACT(MONTH FROM order_date)
        ORDER BY EXTRACT(MONTH FROM order_date)
    """, params)

    monthly_sales = []

    for row in cur.fetchall():
        monthly_sales.append({
            "month": row[0],
            "sales": float(row[1])
        })

    # Top books
    cur.execute("""
        SELECT b.title, SUM(o.quantity) AS total
        FROM orders o
        JOIN books b ON o.book_id = b.book_id
        GROUP BY b.title
        ORDER BY total DESC
        LIMIT 5
    """)

    top_books = cur.fetchall()

    # Top customers
    cur.execute("""
        SELECT c.name, SUM(o.total_amount) AS spent
        FROM orders o
        JOIN customers c ON o.customer_id = c.customer_id
        GROUP BY c.name
        ORDER BY spent DESC
        LIMIT 5
    """)

    top_customers = cur.fetchall()

    # Genre distribution
    cur.execute("""
        SELECT b.genre, COUNT(*) AS total
        FROM orders o
        JOIN books b ON o.book_id = b.book_id
        GROUP BY b.genre
    """)

    genre_data = cur.fetchall()

    cur.close()
    conn.close()

    return render_template(
        "analytics.html",
        stats=stats,
        monthly_sales=monthly_sales,
        top_books=top_books,
        top_customers=top_customers,
        genre_data=genre_data,
        years=years,
        selected_year=selected_year
    )

@app.route('/add_order', methods=['POST'])
def add_order():

    data = request.get_json()

    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute(
        "SELECT customer_id FROM customers WHERE name=%s",
        (data['customer_name'],)
    )
    customer = cur.fetchone()

    cur.execute(
        "SELECT book_id, price FROM books WHERE title=%s",
        (data['book_name'],)
    )
    book = cur.fetchone()

    if not customer or not book:
        return jsonify({"status": "error"})

    customer_id = customer[0]
    book_id = book[0]
    price = float(book[1])

    quantity = int(data['quantity'])
    total_amount = quantity * price

    cur.execute("""
        INSERT INTO orders
        (customer_id, book_id, order_date, quantity, total_amount)
        VALUES (%s, %s, NOW(), %s, %s)
    """, (
        customer_id,
        book_id,
        quantity,
        total_amount
    ))

    conn.commit()

    cur.close()
    conn.close()

    return jsonify({"status": "success"})

# -----------------------------
# RUN
# -----------------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
