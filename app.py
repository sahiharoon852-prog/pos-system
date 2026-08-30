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

# ----------------------------- DATABASE SETUP -----------------------------
def reset_database():
    conn = sqlite3.connect('pos_system.db')
    c = conn.cursor()
    
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
    
    c.execute('''CREATE TABLE products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE,
        category TEXT,
        price REAL,
        stock INTEGER
    )''')
    
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
    
    c.execute('''CREATE TABLE users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password TEXT,
        role TEXT
    )''')
    
    c.execute('''CREATE TABLE categories (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE
    )''')
    
    c.execute('''CREATE TABLE customers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        phone TEXT,
        email TEXT,
        address TEXT
    )''')
    
    c.execute('''CREATE TABLE suppliers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        phone TEXT,
        email TEXT,
        address TEXT
    )''')
    
    c.execute('''CREATE TABLE expenses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        description TEXT,
        amount REAL,
        category TEXT,
        date TEXT
    )''')
    
    c.execute('''CREATE TABLE returns (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        sale_id INTEGER,
        product_name TEXT,
        qty INTEGER,
        refund_amount REAL,
        date TEXT
    )''')
    
    c.execute('''CREATE TABLE purchases (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        supplier_id INTEGER,
        product_name TEXT,
        qty INTEGER,
        cost_price REAL,
        total REAL,
        date TEXT
    )''')
    
    c.execute('''CREATE TABLE settings (
        key TEXT PRIMARY KEY,
        value TEXT
    )''')
    
    c.execute("INSERT INTO users (username, password, role) VALUES ('admin', '786', 'Admin')")
    c.execute("INSERT INTO settings (key, value) VALUES ('tax_rate', '0.17')")
    c.execute("INSERT INTO settings (key, value) VALUES ('store_name', 'M.H.M 786 Store')")
    
    sample_cats = ['Grocery', 'Beverages', 'Dairy', 'Bakery', 'Meat', 'Vegetables']
    for cat in sample_cats:
        c.execute("INSERT INTO categories (name) VALUES (?)", (cat,))
    
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

def get_conn():
    return sqlite3.connect('pos_system.db')

# ----------------------------- LOGIN -----------------------------
def login_page():
    st.markdown("""
    <div style='text-align:center; padding:50px 0;'>
        <h1 style='color:#2E8B57;'>🛒 M.H.M 786 POS</h1>
        <h4>Secure Point of Sale System</h4>
    </div>
    """, unsafe_allow_html=True)
    st.divider()
    
    col1, col2, col3 = st.columns([1, 1.5, 1])
    with col2:
        st.image("https://img.icons8.com/fluency/96/000000/lock.png", width=100)
        username = st.text_input("Username", placeholder="admin")
        password = st.text_input("Password", type="password", placeholder="Enter 786")
        
        if st.button("🔓 Login", use_container_width=True, type="primary"):
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
    """Complete Today's Sales Card with all metrics - Enhanced Design"""
    
    # --- Custom CSS for Beautiful Cards ---
    st.markdown("""
    <style>
    .sales-card {
        background: linear-gradient(145deg, #ffffff, #f8f9fa);
        border-radius: 15px;
        padding: 18px 12px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.06);
        text-align: center;
        border-left: 5px solid #2E8B57;
        margin-bottom: 8px;
        transition: transform 0.2s;
    }
    .sales-card:hover {
        transform: translateY(-3px);
        box-shadow: 0 6px 20px rgba(0,0,0,0.1);
    }
    .sales-card-red { border-left-color: #dc3545; }
    .sales-card-blue { border-left-color: #007bff; }
    .sales-card-gold { border-left-color: #ffc107; }
    .sales-card-purple { border-left-color: #6f42c1; }
    .sales-card-orange { border-left-color: #fd7e14; }
    .sales-card-teal { border-left-color: #20c997; }
    
    .sales-value {
        font-size: 1.8rem;
        font-weight: 700;
        color: #1a1a2e;
        margin: 3px 0;
    }
    .sales-label {
        font-size: 0.85rem;
        color: #6c757d;
        font-weight: 600;
        letter-spacing: 0.3px;
        text-transform: uppercase;
    }
    .sales-sub {
        font-size: 0.75rem;
        color: #adb5bd;
    }
    .dashboard-title {
        font-size: 1.5rem;
        font-weight: 700;
        color: #2E8B57;
        margin-bottom: 15px;
    }
    .payment-card {
        background: #f8f9fa;
        border-radius: 10px;
        padding: 12px;
        text-align: center;
        border: 1px solid #e9ecef;
    }
    </style>
    """, unsafe_allow_html=True)
    
    st.markdown("<div class='dashboard-title'>💰 Today's Sales</div>", unsafe_allow_html=True)
    
    conn = get_conn()
    c = conn.cursor()
    today = datetime.now().strftime("%Y-%m-%d")
    
    # --- All queries with safe COALESCE ---
    c.execute("SELECT COALESCE(SUM(total), 0) FROM sales WHERE date LIKE ? AND return_status = 'active'", (today+'%',))
    total_sales = c.fetchone()[0]
    
    c.execute("SELECT COUNT(DISTINCT invoice_no) FROM sales WHERE date LIKE ? AND return_status = 'active'", (today+'%',))
    total_invoices = c.fetchone()[0]
    
    c.execute("SELECT COALESCE(SUM(qty), 0) FROM sales WHERE date LIKE ? AND return_status = 'active'", (today+'%',))
    total_items = c.fetchone()[0]
    
    avg_invoice = total_sales / total_invoices if total_invoices > 0 else 0.0
    
    c.execute("SELECT COALESCE(SUM(total), 0) FROM sales WHERE date LIKE ? AND payment_method = 'Cash' AND return_status = 'active'", (today+'%',))
    cash_sales = c.fetchone()[0]
    
    c.execute("SELECT COALESCE(SUM(total), 0) FROM sales WHERE date LIKE ? AND payment_method = 'Card' AND return_status = 'active'", (today+'%',))
    card_sales = c.fetchone()[0]
    
    c.execute("SELECT COALESCE(SUM(total), 0) FROM sales WHERE date LIKE ? AND payment_method = 'Online' AND return_status = 'active'", (today+'%',))
    online_sales = c.fetchone()[0]
    
    c.execute("SELECT COALESCE(SUM(total), 0) FROM sales WHERE date LIKE ? AND payment_method = 'Credit' AND return_status = 'active'", (today+'%',))
    credit_sales = c.fetchone()[0]
    
    c.execute("SELECT COALESCE(SUM(total), 0), COUNT(*) FROM sales WHERE date LIKE ? AND return_status = 'returned'", (today+'%',))
    returned_amount, returned_count = c.fetchone()
    
    conn.close()
    
    # --- Row 1: 4 Main Metrics ---
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f"""
        <div class='sales-card'>
            <div class='sales-label'>Total Sales</div>
            <div class='sales-value'>Rs. {total_sales:,.2f}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class='sales-card sales-card-blue'>
            <div class='sales-label'>Invoices</div>
            <div class='sales-value'>{total_invoices}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class='sales-card sales-card-gold'>
            <div class='sales-label'>Items Sold</div>
            <div class='sales-value'>{total_items}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown(f"""
        <div class='sales-card sales-card-purple'>
            <div class='sales-label'>Avg Invoice</div>
            <div class='sales-value'>Rs. {avg_invoice:,.2f}</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # --- Row 2: Payment Methods ---
    st.markdown("<div class='dashboard-title' style='font-size:1.1rem;'>💳 Payment Methods</div>", unsafe_allow_html=True)
    
    col_c1, col_c2, col_c3, col_c4 = st.columns(4)
    
    with col_c1:
        st.markdown(f"""
        <div class='payment-card'>
            <div style='font-weight:600; color:#28a745;'>Cash</div>
            <div style='font-size:1.3rem; font-weight:700;'>Rs. {cash_sales:,.2f}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col_c2:
        st.markdown(f"""
        <div class='payment-card'>
            <div style='font-weight:600; color:#007bff;'>Card</div>
            <div style='font-size:1.3rem; font-weight:700;'>Rs. {card_sales:,.2f}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col_c3:
        st.markdown(f"""
        <div class='payment-card'>
            <div style='font-weight:600; color:#17a2b8;'>Online</div>
            <div style='font-size:1.3rem; font-weight:700;'>Rs. {online_sales:,.2f}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col_c4:
        st.markdown(f"""
        <div class='payment-card'>
            <div style='font-weight:600; color:#fd7e14;'>Credit</div>
            <div style='font-size:1.3rem; font-weight:700;'>Rs. {credit_sales:,.2f}</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # --- Row 3: Returned & Cancelled ---
    col_r1, col_r2 = st.columns(2)
    
    with col_r1:
        st.markdown(f"""
        <div class='sales-card sales-card-red'>
            <div class='sales-label'>🔄 Returned</div>
            <div class='sales-value' style='font-size:1.4rem;'>Rs. {returned_amount:,.2f}</div>
            <div class='sales-sub'>({returned_count} items returned)</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col_r2:
        st.markdown(f"""
        <div class='sales-card sales-card-orange'>
            <div class='sales-label'>❌ Cancelled</div>
            <div class='sales-value' style='font-size:1.4rem;'>Rs. 0.00</div>
            <div class='sales-sub'>(0 items cancelled)</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # --- View List Button ---
    if st.button("📋 View Today's Sales List", use_container_width=False, type="primary"):
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
                df_today['return_status'] = df_today['return_status'].apply(lambda x: '🔄 Returned' if x == 'returned' else '✅ Active')
                st.dataframe(df_today, use_container_width=True, hide_index=True)
            else:
                st.info("No sales today yet.")

# ============================================================================
# ============================= MAIN APP =====================================
# ============================================================================

def main_app():
    # --- Sidebar ---
    with st.sidebar:
        st.image("https://img.icons8.com/color/96/000000/grocery-store.png", width=80)
        st.markdown("### M.H.M 786 Store")
        st.caption(f"👤 {st.session_state.username}")
        st.divider()
        
        if st.button("🚪 Logout", use_container_width=True):
            st.session_state.logged_in = False
            st.session_state.cart = []
            st.rerun()
        
        st.markdown("---")
        st.markdown("### 📋 Menu")
        menu_items = [
            "🏠 Dashboard",
            "💰 POS / New Sale",
            "📦 Products",
            "📂 Categories",
            "👤 Customers",
            "🏭 Suppliers",
            "💸 Expenses",
            "⚙️ Settings"
        ]
        for item in menu_items:
            st.caption(item)
        
        st.markdown("---")
        st.caption("© 2026 M.H.M 786")
    
    # --- Main Content ---
    st.header("📊 Executive Dashboard")
    
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
    
    # ---- CALL TODAY'S SALES CARD ----
    today_sales_card()
    
    # --- Quick Stats Footer ---
    st.divider()
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
    col1.metric("💸 Today's Expenses", f"Rs. {today_expenses:,.2f}")
    col2.metric("📦 Total Products", total_products)
    col3.metric("⚠️ Low Stock Alert", low_stock, delta="Need restock" if low_stock > 0 else "✅ OK")
    
    st.divider()
    st.caption("✅ M.H.M 786 POS - Fully Functional | InshaAllah!")

# ============================================================================
# ============================= RUN ==========================================
# ============================================================================

if not st.session_state.logged_in:
    login_page()
else:
    main_app()
