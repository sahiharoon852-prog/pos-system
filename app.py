import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime, timedelta
import io
import base64

# ----------------------------- CONFIG -----------------------------
APP_NAME = "M.H.M 786 POS"
APP_ICON = "🛒"
ADMIN_PIN = "786"  # Default admin PIN
TAX_RATE = 0.17    # 17% GST (can be changed in Settings)

# ----------------------------- DB SETUP -----------------------------
def init_db():
    conn = sqlite3.connect('pos_system.db')
    c = conn.cursor()
    # Products
    c.execute('''CREATE TABLE IF NOT EXISTS products
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT UNIQUE, 
                  category TEXT, price REAL, stock INTEGER)''')
    # Categories
    c.execute('''CREATE TABLE IF NOT EXISTS categories
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT UNIQUE)''')
    # Customers
    c.execute('''CREATE TABLE IF NOT EXISTS customers
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, phone TEXT, email TEXT, address TEXT)''')
    # Suppliers
    c.execute('''CREATE TABLE IF NOT EXISTS suppliers
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, phone TEXT, email TEXT, address TEXT)''')
    # Sales
    c.execute('''CREATE TABLE IF NOT EXISTS sales
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  invoice_no TEXT, customer_id INTEGER, 
                  product_name TEXT, qty INTEGER, price REAL, total REAL, 
                  date TEXT, return_status TEXT DEFAULT 'active')''')
    # Purchases
    c.execute('''CREATE TABLE IF NOT EXISTS purchases
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  supplier_id INTEGER, product_name TEXT, qty INTEGER, 
                  cost_price REAL, total REAL, date TEXT)''')
    # Expenses
    c.execute('''CREATE TABLE IF NOT EXISTS expenses
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  description TEXT, amount REAL, category TEXT, date TEXT)''')
    # Returns
    c.execute('''CREATE TABLE IF NOT EXISTS returns
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  sale_id INTEGER, product_name TEXT, qty INTEGER, 
                  refund_amount REAL, date TEXT)''')
    # Users
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  username TEXT UNIQUE, password TEXT, role TEXT)''')
    # Settings
    c.execute('''CREATE TABLE IF NOT EXISTS settings
                 (key TEXT PRIMARY KEY, value TEXT)''')
    # Insert default admin user if not exists
    c.execute("SELECT COUNT(*) FROM users WHERE username='admin'")
    if c.fetchone()[0] == 0:
        c.execute("INSERT INTO users (username, password, role) VALUES ('admin', '786', 'Admin')")
    # Insert default settings
    c.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('tax_rate', '0.17')")
    c.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('store_name', 'M.H.M 786 Store')")
    # Insert sample categories if empty
    c.execute("SELECT COUNT(*) FROM categories")
    if c.fetchone()[0] == 0:
        sample_cats = ['Grocery', 'Beverages', 'Dairy', 'Bakery', 'Meat', 'Vegetables']
        c.executemany("INSERT INTO categories (name) VALUES (?)", [(cat,) for cat in sample_cats])
    # Insert sample products if empty
    c.execute("SELECT COUNT(*) FROM products")
    if c.fetchone()[0] == 0:
        sample_products = [
            ('Bread (Roti)', 'Bakery', 50, 10),
            ('Milk (1L)', 'Dairy', 120, 8),
            ('Sugar (1kg)', 'Grocery', 95, 20),
            ('Tea (250g)', 'Beverages', 220, 15),
            ('Cooking Oil (1L)', 'Grocery', 180, 6),
            ('Eggs (Dozen)', 'Dairy', 150, 12)
        ]
        c.executemany("INSERT INTO products (name, category, price, stock) VALUES (?,?,?,?)", sample_products)
    conn.commit()
    conn.close()

init_db()

# ----------------------------- DB HELPER -----------------------------
def get_conn():
    return sqlite3.connect('pos_system.db')

def get_setting(key):
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT value FROM settings WHERE key=?", (key,))
    row = c.fetchone()
    conn.close()
    return row[0] if row else None

def update_setting(key, value):
    conn = get_conn()
    c = conn.cursor()
    c.execute("REPLACE INTO settings (key, value) VALUES (?,?)", (key, value))
    conn.commit()
    conn.close()

def get_tax_rate():
    rate = get_setting('tax_rate')
    return float(rate) if rate else 0.17

def get_store_name():
    name = get_setting('store_name')
    return name if name else "M.H.M 786 Store"

# ----------------------------- SESSION STATE -----------------------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "username" not in st.session_state:
    st.session_state.username = ""
if "role" not in st.session_state:
    st.session_state.role = "Admin"
if "cart" not in st.session_state:
    st.session_state.cart = []
if "page" not in st.session_state:
    st.session_state.page = "Dashboard"

# ----------------------------- PAGE CONFIG -----------------------------
st.set_page_config(page_title=APP_NAME, page_icon=APP_ICON, layout="wide")

# ----------------------------- LOGIN -----------------------------
def login_page():
    st.markdown(f"<h1 style='text-align:center;'>{APP_ICON} {get_store_name()}</h1>", unsafe_allow_html=True)
    st.markdown("<h4 style='text-align:center;'>Secure Point of Sale System</h4>", unsafe_allow_html=True)
    st.divider()
    col1, col2, col3 = st.columns([1, 1.5, 1])
    with col2:
        st.image("https://img.icons8.com/fluency/96/000000/lock.png", width=100)
        username = st.text_input("Username", placeholder="admin")
        password = st.text_input("Password", type="password", placeholder="Enter PIN")
        if st.button("🔓 Login", use_container_width=True):
            conn = get_conn()
            c = conn.cursor()
            c.execute("SELECT password, role FROM users WHERE username=?", (username,))
            row = c.fetchone()
            conn.close()
            if row and row[0] == password:
                st.session_state.logged_in = True
                st.session_state.username = username
                st.session_state.role = row[1]
                st.rerun()
            else:
                st.error("Invalid credentials. Try admin/786.")

# ----------------------------- SIDEBAR NAVIGATION -----------------------------
def show_sidebar():
    with st.sidebar:
        st.image("https://img.icons8.com/color/96/000000/grocery-store.png", width=80)
        st.markdown(f"### {get_store_name()}")
        st.caption(f"User: {st.session_state.username} ({st.session_state.role})")
        st.divider()
        pages = [
            "🏠 Dashboard",
            "💰 POS / New Sale",
            "📦 Products",
            "📂 Categories",
            "📊 Inventory",
            "🛒 Purchases",
            "📈 Sales History",
            "🔄 Returns",
            "👤 Customers",
            "🏭 Suppliers",
            "💸 Expenses",
            "🧾 Invoices",
            "📉 Reports",
            "👥 Users & Permissions",
            "⚙️ Settings",
            "💾 Backup & Restore",
            "🚪 Logout"
        ]
        selected = st.radio("Navigation", pages, index=0)
        if selected == "🚪 Logout":
            st.session_state.logged_in = False
            st.session_state.cart = []
            st.rerun()
        return selected

# ----------------------------- DASHBOARD -----------------------------
def dashboard():
    st.header("📊 Dashboard")
    conn = get_conn()
    c = conn.cursor()
    # Total products
    c.execute("SELECT COUNT(*) FROM products")
    total_products = c.fetchone()[0]
    # Total customers
    c.execute("SELECT COUNT(*) FROM customers")
    total_customers = c.fetchone()[0]
    # Total suppliers
    c.execute("SELECT COUNT(*) FROM suppliers")
    total_suppliers = c.fetchone()[0]
    # Today's sales
    today = datetime.now().strftime("%Y-%m-%d")
    c.execute("SELECT SUM(total) FROM sales WHERE date LIKE ?", (today+'%',))
    today_sales = c.fetchone()[0] or 0.0
    # Total sales (all time)
    c.execute("SELECT SUM(total) FROM sales")
    total_sales = c.fetchone()[0] or 0.0
    conn.close()
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Products", total_products)
    col2.metric("Customers", total_customers)
    col3.metric("Suppliers", total_suppliers)
    col4.metric("Today's Sales", f"Rs. {today_sales:.2f}")
    
    col5, col6 = st.columns(2)
    col5.metric("Total Sales (All Time)", f"Rs. {total_sales:.2f}")
    # Show recent sales
    st.subheader("Recent Sales")
    conn = get_conn()
    df_recent = pd.read_sql_query("SELECT id, invoice_no, customer_id, product_name, qty, total, date FROM sales ORDER BY id DESC LIMIT 10", conn)
    conn.close()
    if not df_recent.empty:
        st.dataframe(df_recent, use_container_width=True)
    else:
        st.info("No sales recorded yet.")

# ----------------------------- POS / NEW SALE -----------------------------
def pos_sale():
    st.header("💰 POS / New Sale")
    # Sidebar already has add to cart; we use the existing cart system.
    # We'll use the same as before but also allow customer selection.
    conn = get_conn()
    df_customers = pd.read_sql_query("SELECT id, name FROM customers", conn)
    conn.close()
    customer_options = ["Walk-in Customer"] + df_customers['name'].tolist() if not df_customers.empty else ["Walk-in Customer"]
    selected_customer = st.selectbox("Select Customer", customer_options)
    # (We'll store customer ID if not walk-in)
    customer_id = 0
    if selected_customer != "Walk-in Customer":
        customer_id = df_customers[df_customers['name']==selected_customer]['id'].values[0]
    
    # Cart display (reuse existing)
    st.subheader("🛒 Current Cart")
    if st.session_state.cart:
        df_cart = pd.DataFrame(st.session_state.cart)
        df_cart['Total'] = df_cart['qty'] * df_cart['price']
        st.dataframe(df_cart[['name','qty','price','Total']], use_container_width=True)
        total_bill = df_cart['Total'].sum()
        tax = total_bill * get_tax_rate()
        grand_total = total_bill + tax
        st.metric("Subtotal", f"Rs. {total_bill:.2f}")
        st.metric("Tax (GST)", f"Rs. {tax:.2f}")
        st.metric("Grand Total", f"Rs. {grand_total:.2f}")
        
        if st.button("✅ Generate Invoice & Save"):
            conn = get_conn()
            c = conn.cursor()
            today = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            invoice_no = "INV-" + datetime.now().strftime("%Y%m%d%H%M%S")
            for _, row in df_cart.iterrows():
                c.execute("INSERT INTO sales (invoice_no, customer_id, product_name, qty, price, total, date) VALUES (?,?,?,?,?,?,?)",
                          (invoice_no, customer_id, row['name'], row['qty'], row['price'], row['Total'], today))
                c.execute("UPDATE products SET stock = stock - ? WHERE name = ?", (row['qty'], row['name']))
            conn.commit()
            conn.close()
            st.success(f"Invoice {invoice_no} saved successfully!")
            st.balloons()
            st.session_state.cart = []
            st.rerun()
    else:
        st.info("Cart is empty. Add items from sidebar.")

# ----------------------------- PRODUCTS -----------------------------
def products():
    st.header("📦 Products")
    conn = get_conn()
    df = pd.read_sql_query("SELECT * FROM products ORDER BY name", conn)
    conn.close()
    st.dataframe(df, use_container_width=True)
    
    with st.expander("➕ Add / Edit Product"):
        conn = get_conn()
        df_cats = pd.read_sql_query("SELECT name FROM categories", conn)
        conn.close()
        cat_list = df_cats['name'].tolist() if not df_cats.empty else []
        name = st.text_input("Product Name")
        category = st.selectbox("Category", cat_list) if cat_list else st.text_input("Category (new)")
        price = st.number_input("Price (Rs.)", min_value=0.0, step=1.0)
        stock = st.number_input("Stock", min_value=0, step=1)
        if st.button("Add Product"):
            if name and price >= 0 and stock >= 0:
                conn = get_conn()
                c = conn.cursor()
                try:
                    c.execute("INSERT INTO products (name, category, price, stock) VALUES (?,?,?,?)", (name, category, price, stock))
                    conn.commit()
                    st.success("Product added!")
                    st.rerun()
                except:
                    st.error("Product name already exists.")
                conn.close()
    
    # Delete product
    st.subheader("🗑️ Delete Product")
    conn = get_conn()
    df_names = pd.read_sql_query("SELECT name FROM products", conn)
    conn.close()
    if not df_names.empty:
        prod_to_del = st.selectbox("Select product to delete", df_names['name'].tolist())
        if st.button("Delete Selected Product"):
            conn = get_conn()
            c = conn.cursor()
            c.execute("DELETE FROM products WHERE name=?", (prod_to_del,))
            conn.commit()
            conn.close()
            st.success(f"{prod_to_del} deleted.")
            st.rerun()

# ----------------------------- CATEGORIES -----------------------------
def categories():
    st.header("📂 Categories")
    conn = get_conn()
    df = pd.read_sql_query("SELECT * FROM categories ORDER BY name", conn)
    conn.close()
    st.dataframe(df, use_container_width=True)
    with st.expander("➕ Add Category"):
        cat_name = st.text_input("Category Name")
        if st.button("Add Category"):
            if cat_name:
                conn = get_conn()
                c = conn.cursor()
                try:
                    c.execute("INSERT INTO categories (name) VALUES (?)", (cat_name,))
                    conn.commit()
                    st.success("Category added!")
                    st.rerun()
                except:
                    st.error("Category already exists.")
                conn.close()
    # Delete category
    conn = get_conn()
    df_cats = pd.read_sql_query("SELECT name FROM categories", conn)
    conn.close()
    if not df_cats.empty:
        del_cat = st.selectbox("Delete category", df_cats['name'].tolist())
        if st.button("Delete Category"):
            conn = get_conn()
            c = conn.cursor()
            c.execute("DELETE FROM categories WHERE name=?", (del_cat,))
            conn.commit()
            conn.close()
            st.success(f"{del_cat} deleted.")
            st.rerun()

# ----------------------------- INVENTORY -----------------------------
def inventory():
    st.header("📊 Inventory")
    conn = get_conn()
    df = pd.read_sql_query("SELECT name, category, price, stock FROM products ORDER BY name", conn)
    conn.close()
    st.dataframe(df, use_container_width=True)
    st.subheader("Adjust Stock")
    conn = get_conn()
    df_names = pd.read_sql_query("SELECT name FROM products", conn)
    conn.close()
    if not df_names.empty:
        prod = st.selectbox("Product", df_names['name'].tolist())
        new_stock = st.number_input("New Stock Quantity", min_value=0, step=1)
        if st.button("Update Stock"):
            if prod and new_stock >= 0:
                conn = get_conn()
                c = conn.cursor()
                c.execute("UPDATE products SET stock = ? WHERE name = ?", (new_stock, prod))
                conn.commit()
                conn.close()
                st.success(f"Stock of {prod} updated to {new_stock}.")
                st.rerun()

# ----------------------------- PURCHASES -----------------------------
def purchases():
    st.header("🛒 Purchases")
    conn = get_conn()
    df = pd.read_sql_query("SELECT * FROM purchases ORDER BY id DESC", conn)
    conn.close()
    st.dataframe(df, use_container_width=True)
    with st.expander("➕ Record Purchase"):
        conn = get_conn()
        df_supp = pd.read_sql_query("SELECT id, name FROM suppliers", conn)
        conn.close()
        supp_list = df_supp['name'].tolist() if not df_supp.empty else []
        supplier = st.selectbox("Supplier", supp_list) if supp_list else st.text_input("Supplier (new)")
        product = st.text_input("Product Name")
        qty = st.number_input("Quantity", min_value=1, step=1)
        cost = st.number_input("Cost per unit (Rs.)", min_value=0.0, step=1.0)
        if st.button("Record Purchase"):
            if product and qty > 0 and cost >= 0:
                conn = get_conn()
                c = conn.cursor()
                total = qty * cost
                # Get supplier id
                if supplier in supp_list:
                    supp_id = df_supp[df_supp['name']==supplier]['id'].values[0]
                else:
                    # Insert new supplier
                    c.execute("INSERT INTO suppliers (name) VALUES (?)", (supplier,))
                    supp_id = c.lastrowid
                today = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                c.execute("INSERT INTO purchases (supplier_id, product_name, qty, cost_price, total, date) VALUES (?,?,?,?,?,?)",
                          (supp_id, product, qty, cost, total, today))
                # Also update product stock? (maybe not, purchases are separate)
                conn.commit()
                conn.close()
                st.success("Purchase recorded.")
                st.rerun()

# ----------------------------- SALES HISTORY -----------------------------
def sales_history():
    st.header("📈 Sales History")
    conn = get_conn()
    df = pd.read_sql_query("SELECT * FROM sales ORDER BY id DESC", conn)
    conn.close()
    st.dataframe(df, use_container_width=True)
    # Filter by date
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input("Start Date", datetime.now() - timedelta(days=30))
    with col2:
        end_date = st.date_input("End Date", datetime.now())
    if st.button("Filter"):
        conn = get_conn()
        df_f = pd.read_sql_query("SELECT * FROM sales WHERE date BETWEEN ? AND ?", (start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d')), conn)
        conn.close()
        st.dataframe(df_f, use_container_width=True)

# ----------------------------- RETURNS -----------------------------
def returns():
    st.header("🔄 Returns")
    conn = get_conn()
    # Show sales that are not returned
    df_sales = pd.read_sql_query("SELECT id, invoice_no, product_name, qty, total FROM sales WHERE return_status='active'", conn)
    conn.close()
    if not df_sales.empty:
        st.subheader("Select a sale to return")
        sale_id = st.selectbox("Sale ID", df_sales['id'].tolist())
        if sale_id:
            sale_row = df_sales[df_sales['id']==sale_id].iloc[0]
            st.write(f"Invoice: {sale_row['invoice_no']}, Product: {sale_row['product_name']}, Qty: {sale_row['qty']}, Total: {sale_row['total']}")
            refund_qty = st.number_input("Quantity to return", min_value=1, max_value=int(sale_row['qty']), value=1)
            if st.button("Process Return"):
                refund_amount = (sale_row['total'] / sale_row['qty']) * refund_qty
                conn = get_conn()
                c = conn.cursor()
                today = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                c.execute("INSERT INTO returns (sale_id, product_name, qty, refund_amount, date) VALUES (?,?,?,?,?)",
                          (sale_id, sale_row['product_name'], refund_qty, refund_amount, today))
                # Update sale return_status
                if refund_qty == sale_row['qty']:
                    c.execute("UPDATE sales SET return_status='returned' WHERE id=?", (sale_id,))
                else:
                    # Partial return: not changing status, but we could adjust stock.
                    pass
                # Increase stock
                c.execute("UPDATE products SET stock = stock + ? WHERE name = ?", (refund_qty, sale_row['product_name']))
                conn.commit()
                conn.close()
                st.success(f"Return processed. Refund: Rs. {refund_amount:.2f}")
                st.rerun()
    else:
        st.info("No sales available for return.")

# ----------------------------- CUSTOMERS -----------------------------
def customers():
    st.header("👤 Customers")
    conn = get_conn()
    df = pd.read_sql_query("SELECT * FROM customers ORDER BY name", conn)
    conn.close()
    st.dataframe(df, use_container_width=True)
    with st.expander("➕ Add Customer"):
        name = st.text_input("Name")
        phone = st.text_input("Phone")
        email = st.text_input("Email")
        address = st.text_area("Address")
        if st.button("Add Customer"):
            if name:
                conn = get_conn()
                c = conn.cursor()
                c.execute("INSERT INTO customers (name, phone, email, address) VALUES (?,?,?,?)", (name, phone, email, address))
                conn.commit()
                conn.close()
                st.success("Customer added.")
                st.rerun()
    # Delete customer
    conn = get_conn()
    df_names = pd.read_sql_query("SELECT name FROM customers", conn)
    conn.close()
    if not df_names.empty:
        del_cust = st.selectbox("Delete Customer", df_names['name'].tolist())
        if st.button("Delete Customer"):
            conn = get_conn()
            c = conn.cursor()
            c.execute("DELETE FROM customers WHERE name=?", (del_cust,))
            conn.commit()
            conn.close()
            st.success(f"{del_cust} deleted.")
            st.rerun()

# ----------------------------- SUPPLIERS -----------------------------
def suppliers():
    st.header("🏭 Suppliers")
    conn = get_conn()
    df = pd.read_sql_query("SELECT * FROM suppliers ORDER BY name", conn)
    conn.close()
    st.dataframe(df, use_container_width=True)
    with st.expander("➕ Add Supplier"):
        name = st.text_input("Name")
        phone = st.text_input("Phone")
        email = st.text_input("Email")
        address = st.text_area("Address")
        if st.button("Add Supplier"):
            if name:
                conn = get_conn()
                c = conn.cursor()
                c.execute("INSERT INTO suppliers (name, phone, email, address) VALUES (?,?,?,?)", (name, phone, email, address))
                conn.commit()
                conn.close()
                st.success("Supplier added.")
                st.rerun()
    # Delete supplier
    conn = get_conn()
    df_names = pd.read_sql_query("SELECT name FROM suppliers", conn)
    conn.close()
    if not df_names.empty:
        del_supp = st.selectbox("Delete Supplier", df_names['name'].tolist())
        if st.button("Delete Supplier"):
            conn = get_conn()
            c = conn.cursor()
            c.execute("DELETE FROM suppliers WHERE name=?", (del_supp,))
            conn.commit()
            conn.close()
            st.success(f"{del_supp} deleted.")
            st.rerun()

# ----------------------------- EXPENSES -----------------------------
def expenses():
    st.header("💸 Expenses")
    conn = get_conn()
    df = pd.read_sql_query("SELECT * FROM expenses ORDER BY id DESC", conn)
    conn.close()
    st.dataframe(df, use_container_width=True)
    with st.expander("➕ Add Expense"):
        desc = st.text_input("Description")
        amount = st.number_input("Amount (Rs.)", min_value=0.0, step=1.0)
        category = st.selectbox("Category", ["Rent", "Utilities", "Salaries", "Transport", "Other"])
        date = st.date_input("Date", datetime.now())
        if st.button("Add Expense"):
            if desc and amount > 0:
                conn = get_conn()
                c = conn.cursor()
                c.execute("INSERT INTO expenses (description, amount, category, date) VALUES (?,?,?,?)",
                          (desc, amount, category, date.strftime('%Y-%m-%d')))
                conn.commit()
                conn.close()
                st.success("Expense added.")
                st.rerun()
    # Delete expense
    conn = get_conn()
    df_ids = pd.read_sql_query("SELECT id FROM expenses", conn)
    conn.close()
    if not df_ids.empty:
        del_id = st.selectbox("Delete Expense (select ID)", df_ids['id'].tolist())
        if st.button("Delete Expense"):
            conn = get_conn()
            c = conn.cursor()
            c.execute("DELETE FROM expenses WHERE id=?", (del_id,))
            conn.commit()
            conn.close()
            st.success(f"Expense ID {del_id} deleted.")
            st.rerun()

# ----------------------------- INVOICES -----------------------------
def invoices():
    st.header("🧾 Invoices")
    conn = get_conn()
    df_sales = pd.read_sql_query("SELECT DISTINCT invoice_no, date FROM sales ORDER BY id DESC", conn)
    conn.close()
    if not df_sales.empty:
        inv = st.selectbox("Select Invoice", df_sales['invoice_no'].tolist())
        if inv:
            conn = get_conn()
            df_details = pd.read_sql_query("SELECT product_name, qty, price, total FROM sales WHERE invoice_no=?", (inv,), conn)
            conn.close()
            st.dataframe(df_details, use_container_width=True)
            total = df_details['total'].sum()
            tax = total * get_tax_rate()
            grand = total + tax
            st.metric("Subtotal", f"Rs. {total:.2f}")
            st.metric("Tax", f"Rs. {tax:.2f}")
            st.metric("Grand Total", f"Rs. {grand:.2f}")
            # Option to generate PDF (placeholder)
            if st.button("Download Invoice (PDF) - Coming Soon"):
                st.info("PDF generation will be added later.")
    else:
        st.info("No invoices found.")

# ----------------------------- REPORTS -----------------------------
def reports():
    st.header("📉 Reports")
    conn = get_conn()
    # Sales summary by period
    st.subheader("Sales Summary")
    period = st.selectbox("Period", ["Today", "This Week", "This Month", "All Time"])
    now = datetime.now()
    if period == "Today":
        start = now.strftime('%Y-%m-%d')
        end = now.strftime('%Y-%m-%d')
    elif period == "This Week":
        start = (now - timedelta(days=now.weekday())).strftime('%Y-%m-%d')
        end = now.strftime('%Y-%m-%d')
    elif period == "This Month":
        start = now.replace(day=1).strftime('%Y-%m-%d')
        end = now.strftime('%Y-%m-%d')
    else:
        start = "1970-01-01"
        end = now.strftime('%Y-%m-%d')
    df_sales = pd.read_sql_query("SELECT date, total FROM sales WHERE date BETWEEN ? AND ?", (start, end), conn)
    conn.close()
    if not df_sales.empty:
        total_sales = df_sales['total'].sum()
        st.metric("Total Sales", f"Rs. {total_sales:.2f}")
        st.line_chart(df_sales.set_index('date')['total'])
    else:
        st.info("No sales data for this period.")
    
    # Profit calculation (simple: assume cost is 70% of sales - just placeholder)
    st.subheader("Profit Estimation")
    if not df_sales.empty:
        profit = total_sales * 0.3  # dummy
        st.metric("Estimated Profit (30% margin)", f"Rs. {profit:.2f}")
    else:
        st.info("No data.")

# ----------------------------- USERS & PERMISSIONS -----------------------------
def users():
    st.header("👥 Users & Permissions")
    # Only admin can manage users
    if st.session_state.role != "Admin":
        st.warning("Access restricted to Admin only.")
        return
    conn = get_conn()
    df = pd.read_sql_query("SELECT id, username, role FROM users", conn)
    conn.close()
    st.dataframe(df, use_container_width=True)
    with st.expander("➕ Add New User"):
        new_user = st.text_input("Username")
        new_pass = st.text_input("Password", type="password")
        new_role = st.selectbox("Role", ["Admin", "Cashier"])
        if st.button("Add User"):
            if new_user and new_pass:
                conn = get_conn()
                c = conn.cursor()
                try:
                    c.execute("INSERT INTO users (username, password, role) VALUES (?,?,?)", (new_user, new_pass, new_role))
                    conn.commit()
                    st.success("User added.")
                    st.rerun()
                except:
                    st.error("Username already exists.")
                conn.close()
    # Delete user
    conn = get_conn()
    df_users = pd.read_sql_query("SELECT username FROM users WHERE username!='admin'", conn)
    conn.close()
    if not df_users.empty:
        del_user = st.selectbox("Delete User (except admin)", df_users['username'].tolist())
        if st.button("Delete User"):
            conn = get_conn()
            c = conn.cursor()
            c.execute("DELETE FROM users WHERE username=?", (del_user,))
            conn.commit()
            conn.close()
            st.success(f"{del_user} deleted.")
            st.rerun()

# ----------------------------- SETTINGS -----------------------------
def settings():
    st.header("⚙️ Settings")
    store_name = get_store_name()
    tax_rate = get_tax_rate()
    new_name = st.text_input("Store Name", store_name)
    new_tax = st.number_input("Tax Rate (as decimal, e.g., 0.17 for 17%)", min_value=0.0, max_value=1.0, value=tax_rate, step=0.01)
    if st.button("Save Settings"):
        update_setting('store_name', new_name)
        update_setting('tax_rate', str(new_tax))
        st.success("Settings updated.")
        st.rerun()

# ----------------------------- BACKUP & RESTORE -----------------------------
def backup_restore():
    st.header("💾 Backup & Restore")
    # Backup: download database
    with open('pos_system.db', 'rb') as f:
        data = f.read()
    b64 = base64.b64encode(data).decode()
    href = f'<a href="data:application/octet-stream;base64,{b64}" download="pos_backup.db">Download Backup</a>'
    st.markdown(href, unsafe_allow_html=True)
    
    # Restore: upload database
    uploaded_file = st.file_uploader("Upload backup .db file", type=['db'])
    if uploaded_file:
        if st.button("Restore Database (will overwrite current)"):
            with open('pos_system.db', 'wb') as f:
                f.write(uploaded_file.getbuffer())
            st.success("Database restored. Restart app to apply changes.")
            st.rerun()

# ----------------------------- MAIN APP -----------------------------
def main():
    if not st.session_state.logged_in:
        login_page()
        return
    
    selected = show_sidebar()
    # Map selection to page functions
    if selected == "🏠 Dashboard":
        dashboard()
    elif selected == "💰 POS / New Sale":
        pos_sale()
    elif selected == "📦 Products":
        products()
    elif selected == "📂 Categories":
        categories()
    elif selected == "📊 Inventory":
        inventory()
    elif selected == "🛒 Purchases":
        purchases()
    elif selected == "📈 Sales History":
        sales_history()
    elif selected == "🔄 Returns":
        returns()
    elif selected == "👤 Customers":
        customers()
    elif selected == "🏭 Suppliers":
        suppliers()
    elif selected == "💸 Expenses":
        expenses()
    elif selected == "🧾 Invoices":
        invoices()
    elif selected == "📉 Reports":
        reports()
    elif selected == "👥 Users & Permissions":
        users()
    elif selected == "⚙️ Settings":
        settings()
    elif selected == "💾 Backup & Restore":
        backup_restore()
    else:
        st.error("Page not found.")

if __name__ == "__main__":
    main()
