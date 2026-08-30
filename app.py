import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime

# ----------------------------- PAGE CONFIG -----------------------------
st.set_page_config(page_title="M.H.M 786 POS", page_icon="🛒", layout="wide")

# ----------------------------- SESSION STATE -----------------------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "username" not in st.session_state:
    st.session_state.username = ""
if "cart" not in st.session_state:
    st.session_state.cart = []

# ----------------------------- DATABASE RESET (FIXED) -----------------------------
def reset_database():
    conn = sqlite3.connect('pos_system.db')
    c = conn.cursor()
    
    # Drop all existing tables
    c.execute("DROP TABLE IF EXISTS products")
    c.execute("DROP TABLE IF EXISTS sales")
    c.execute("DROP TABLE IF EXISTS users")
    c.execute("DROP TABLE IF EXISTS categories")
    c.execute("DROP TABLE IF EXISTS customers")
    c.execute("DROP TABLE IF EXISTS suppliers")
    c.execute("DROP TABLE IF EXISTS expenses")
    c.execute("DROP TABLE IF EXISTS returns")
    c.execute("DROP TABLE IF EXISTS purchases")
    c.execute("DROP TABLE IF EXISTS settings")
    
    # --- Products ---
    c.execute('''CREATE TABLE products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE,
        category TEXT,
        price REAL,
        stock INTEGER
    )''')
    
    # --- Sales (with all required columns) ---
    c.execute('''CREATE TABLE sales (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        invoice_no TEXT,
        customer_id INTEGER,
        product_name TEXT,
        qty INTEGER,
        price REAL,
        total REAL,
        payment_method TEXT DEFAULT 'Cash',
        date TEXT,
        return_status TEXT DEFAULT 'active'
    )''')
    
    # --- Users ---
    c.execute('''CREATE TABLE users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password TEXT,
        role TEXT
    )''')
    
    # --- Categories ---
    c.execute('''CREATE TABLE categories (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE
    )''')
    
    # --- Customers ---
    c.execute('''CREATE TABLE customers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        phone TEXT,
        email TEXT,
        address TEXT
    )''')
    
    # --- Suppliers ---
    c.execute('''CREATE TABLE suppliers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        phone TEXT,
        email TEXT,
        address TEXT
    )''')
    
    # --- Expenses ---
    c.execute('''CREATE TABLE expenses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        description TEXT,
        amount REAL,
        category TEXT,
        date TEXT
    )''')
    
    # --- Returns ---
    c.execute('''CREATE TABLE returns (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        sale_id INTEGER,
        product_name TEXT,
        qty INTEGER,
        refund_amount REAL,
        date TEXT
    )''')
    
    # --- Purchases ---
    c.execute('''CREATE TABLE purchases (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        supplier_id INTEGER,
        product_name TEXT,
        qty INTEGER,
        cost_price REAL,
        total REAL,
        date TEXT
    )''')
    
    # --- Settings ---
    c.execute('''CREATE TABLE settings (
        key TEXT PRIMARY KEY,
        value TEXT
    )''')
    
    # --- Default Admin ---
    c.execute("INSERT INTO users (username, password, role) VALUES ('admin', '786', 'Admin')")
    
    # --- Default Settings ---
    c.execute("INSERT INTO settings (key, value) VALUES ('tax_rate', '0.17')")
    c.execute("INSERT INTO settings (key, value) VALUES ('store_name', 'M.H.M 786 Store')")
    
    # --- Sample Categories ---
    sample_cats = ['Grocery', 'Beverages', 'Dairy', 'Bakery', 'Meat', 'Vegetables']
    for cat in sample_cats:
        c.execute("INSERT INTO categories (name) VALUES (?)", (cat,))
    
    # --- Sample Products ---
    sample_products = [
        ('Bread (Roti)', 'Bakery', 50, 10),
        ('Milk (1L)', 'Dairy', 120, 8),
        ('Sugar (1kg)', 'Grocery', 95, 20),
        ('Tea (250g)', 'Beverages', 220, 15),
        ('Cooking Oil (1L)', 'Grocery', 180, 6),
        ('Eggs (Dozen)', 'Dairy', 150, 12)
    ]
    for name, cat, price, stock in sample_products:
        c.execute("INSERT INTO products (name, category, price, stock) VALUES (?,?,?,?)", (name, cat, price, stock))
    
    # --- Sample Sales (for testing Today's Sales card) ---
    today = datetime.now().strftime("%Y-%m-%d")
    sample_sales = [
        ('INV-001', 0, 'Bread (Roti)', 2, 50, 100, 'Cash', today + ' 10:00:00', 'active'),
        ('INV-001', 0, 'Milk (1L)', 1, 120, 120, 'Cash', today + ' 10:00:00', 'active'),
        ('INV-002', 0, 'Sugar (1kg)', 3, 95, 285, 'Card', today + ' 11:30:00', 'active'),
        ('INV-003', 0, 'Tea (250g)', 1, 220, 220, 'Online', today + ' 12:15:00', 'active'),
        ('INV-004', 0, 'Cooking Oil (1L)', 2, 180, 360, 'Credit', today + ' 14:00:00', 'active'),
        ('INV-005', 0, 'Eggs (Dozen)', 1, 150, 150, 'Cash', today + ' 15:45:00', 'returned'),
    ]
    for inv, cust, name, qty, price, total, method, date, status in sample_sales:
        c.execute("""INSERT INTO sales 
                     (invoice_no, customer_id, product_name, qty, price, total, payment_method, date, return_status) 
                     VALUES (?,?,?,?,?,?,?,?,?)""", 
                  (inv, cust, name, qty, price, total, method, date, status))
    
    conn.commit()
    conn.close()
    return True

reset_database()

# ----------------------------- DB HELPER -----------------------------
def get_conn():
    return sqlite3.connect('pos_system.db')

# ----------------------------- LOGIN -----------------------------
def login_page():
    st.markdown("<h1 style='text-align:center;'>🛒 M.H.M 786 POS</h1>", unsafe_allow_html=True)
    st.markdown("<h4 style='text-align:center;'>Secure Login</h4>", unsafe_allow_html=True)
    st.divider()
    
    col1, col2, col3 = st.columns([1, 1.5, 1])
    with col2:
        st.image("https://img.icons8.com/fluency/96/000000/lock.png", width=100)
        username = st.text_input("Username", placeholder="admin")
        password = st.text_input("Password", type="password", placeholder="Enter 786")
        
        if st.button("🔓 Login", use_container_width=True):
            conn = get_conn()
            c = conn.cursor()
            c.execute("SELECT password, role FROM users WHERE username=?", (username,))
            row = c.fetchone()
            conn.close()
            if row and row[0] == password:
                st.session_state.logged_in = True
                st.session_state.username = username
                st.rerun()
            else:
                st.error("Invalid credentials. Try admin / 786")

# ============================================================================
# ======================== TODAY'S SALES CARD ===============================
# ============================================================================

def today_sales_card():
    """Complete Today's Sales Card with all metrics"""
    
    st.markdown("### 💰 Today's Sales")
    
    conn = get_conn()
    c = conn.cursor()
    today = datetime.now().strftime("%Y-%m-%d")
    
    # --- 1. Total Sales (Active only) ---
    c.execute("""
        SELECT COALESCE(SUM(total), 0) 
        FROM sales 
        WHERE date LIKE ? AND return_status = 'active'
    """, (today+'%',))
    total_sales = c.fetchone()[0]
    
    # --- 2. Total Invoices ---
    c.execute("""
        SELECT COUNT(DISTINCT invoice_no) 
        FROM sales 
        WHERE date LIKE ? AND return_status = 'active'
    """, (today+'%',))
    total_invoices = c.fetchone()[0]
    
    # --- 3. Total Items Sold ---
    c.execute("""
        SELECT COALESCE(SUM(qty), 0) 
        FROM sales 
        WHERE date LIKE ? AND return_status = 'active'
    """, (today+'%',))
    total_items = c.fetchone()[0]
    
    # --- 4. Average Invoice Value ---
    avg_invoice = total_sales / total_invoices if total_invoices > 0 else 0.0
    
    # --- 5. Payment Methods ---
    # Cash
    c.execute("""
        SELECT COALESCE(SUM(total), 0) 
        FROM sales 
        WHERE date LIKE ? AND payment_method = 'Cash' AND return_status = 'active'
    """, (today+'%',))
    cash_sales = c.fetchone()[0]
    
    # Card
    c.execute("""
        SELECT COALESCE(SUM(total), 0) 
        FROM sales 
        WHERE date LIKE ? AND payment_method = 'Card' AND return_status = 'active'
    """, (today+'%',))
    card_sales = c.fetchone()[0]
    
    # Online
    c.execute("""
        SELECT COALESCE(SUM(total), 0) 
        FROM sales 
        WHERE date LIKE ? AND payment_method = 'Online' AND return_status = 'active'
    """, (today+'%',))
    online_sales = c.fetchone()[0]
    
    # Credit
    c.execute("""
        SELECT COALESCE(SUM(total), 0) 
        FROM sales 
        WHERE date LIKE ? AND payment_method = 'Credit' AND return_status = 'active'
    """, (today+'%',))
    credit_sales = c.fetchone()[0]
    
    # --- 6. Returned Sales ---
    c.execute("""
        SELECT COALESCE(SUM(total), 0), COUNT(*) 
        FROM sales 
        WHERE date LIKE ? AND return_status = 'returned'
    """, (today+'%',))
    returned_amount, returned_count = c.fetchone()
    
    # --- 7. Cancelled Sales (placeholder) ---
    # We don't have cancelled status yet, so using 0
    cancelled_sales = 0.0
    cancelled_count = 0
    
    conn.close()
    
    # --- Display Top Row (4 main metrics) ---
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("💰 Total Sales", f"Rs. {total_sales:,.2f}")
    col2.metric("🧾 Invoices", total_invoices)
    col3.metric("📦 Items Sold", total_items)
    col4.metric("📊 Avg Invoice", f"Rs. {avg_invoice:,.2f}")
    
    # --- Display Payment Methods ---
    st.markdown("#### 💳 Payment Methods")
    col_cash, col_card, col_online, col_credit = st.columns(4)
    col_cash.metric("Cash", f"Rs. {cash_sales:,.2f}")
    col_card.metric("Card", f"Rs. {card_sales:,.2f}")
    col_online.metric("Online", f"Rs. {online_sales:,.2f}")
    col_credit.metric("Credit", f"Rs. {credit_sales:,.2f}")
    
    # --- Display Returned & Cancelled ---
    col_ret, col_can = st.columns(2)
    col_ret.metric("🔄 Returned", f"Rs. {returned_amount:,.2f} ({returned_count} items)")
    col_can.metric("❌ Cancelled", f"Rs. {cancelled_sales:,.2f} ({cancelled_count} items)")
    
    # --- Button to show today's sales list ---
    if st.button("📋 View Today's Sales List"):
        with st.expander("📋 Today's Sales Details", expanded=True):
            conn = get_conn()
            df_today = pd.read_sql_query("""
                SELECT invoice_no, product_name, qty, total, payment_method, date, return_status 
                FROM sales 
                WHERE date LIKE ? 
                ORDER BY id DESC
            """, (today+'%',), conn)
            conn.close()
            if not df_today.empty:
                df_today['date'] = pd.to_datetime(df_today['date']).dt.strftime('%I:%M %p')
                st.dataframe(df_today, use_container_width=True, hide_index=True)
            else:
                st.info("No sales today yet.")
    
    st.divider()

# ============================================================================
# ============================= MAIN APP =====================================
# ============================================================================

def main_app():
    # --- Sidebar ---
    with st.sidebar:
        st.image("https://img.icons8.com/color/96/000000/grocery-store.png", width=80)
        st.markdown("### M.H.M 786 Store")
        st.caption(f"User: {st.session_state.username}")
        st.divider()
        
        if st.button("🚪 Logout", use_container_width=True):
            st.session_state.logged_in = False
            st.session_state.cart = []
            st.rerun()
        
        st.markdown("---")
        st.markdown("### 📋 Menu")
        st.caption("🏠 Dashboard")
        st.caption("💰 POS / New Sale")
        st.caption("📦 Products")
        st.caption("📂 Categories")
        st.caption("👤 Customers")
        st.caption("🏭 Suppliers")
        st.caption("💸 Expenses")
        st.caption("⚙️ Settings")
    
    # --- Main Content ---
    st.header("📊 Dashboard")
    
    # Greeting
    hour = datetime.now().hour
    if hour < 12:
        greet = "🌅 Good Morning"
    elif hour < 18:
        greet = "☀️ Good Afternoon"
    else:
        greet = "🌙 Good Evening"
    st.markdown(f"<h3 style='color:#2E8B57;'>{greet}, {st.session_state.username}!</h3>", unsafe_allow_html=True)
    st.caption(f"📅 {datetime.now().strftime('%A, %d %B %Y')} | ⏰ {datetime.now().strftime('%I:%M %p')}")
    st.divider()
    
    # ---- CALL THE TODAY'S SALES CARD ----
    today_sales_card()
    
    # --- Quick Stats Footer ---
    st.subheader("📈 Quick Stats")
    conn = get_conn()
    c = conn.cursor()
    today = datetime.now().strftime("%Y-%m-%d")
    c.execute("SELECT COALESCE(SUM(amount), 0) FROM expenses WHERE date = ?", (today,))
    today_expenses = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM products")
    total_products = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM products WHERE stock < 5")
    low_stock = c.fetchone()[0]
    conn.close()
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Today's Expenses", f"Rs. {today_expenses:,.2f}")
    col2.metric("Total Products", total_products)
    col3.metric("Low Stock Alert", low_stock, delta="Need restock" if low_stock > 0 else "OK")
    
    st.divider()
    st.caption("✅ Today's Sales Card is fully functional. InshaAllah!")

# ============================================================================
# ============================= RUN ==========================================
# ============================================================================

if not st.session_state.logged_in:
    login_page()
else:
    main_app()
