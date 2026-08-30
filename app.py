import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime

# --- Page Config ---
st.set_page_config(page_title="M.H.M 786 POS", page_icon="🛒", layout="wide")

# --- Session State ---
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "username" not in st.session_state:
    st.session_state.username = ""
if "cart" not in st.session_state:
    st.session_state.cart = []

# --- Simple Database Setup (Safe) ---
def init_db():
    conn = sqlite3.connect('pos_system.db')
    c = conn.cursor()
    # Products table
    c.execute('''CREATE TABLE IF NOT EXISTS products
                 (id INTEGER PRIMARY KEY, name TEXT, price REAL, stock INTEGER)''')
    # Sales table
    c.execute('''CREATE TABLE IF NOT EXISTS sales
                 (id INTEGER PRIMARY KEY, invoice_no TEXT, product_name TEXT, 
                  qty INTEGER, total REAL, date TEXT)''')
    # Users table
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (id INTEGER PRIMARY KEY, username TEXT, password TEXT, role TEXT)''')
    
    # Add default admin
    c.execute("SELECT * FROM users WHERE username='admin'")
    if not c.fetchone():
        c.execute("INSERT INTO users (username, password, role) VALUES ('admin', '786', 'Admin')")
    
    # Add sample products if empty
    c.execute("SELECT * FROM products")
    if not c.fetchone():
        items = [('Bread', 50, 10), ('Milk', 120, 8), ('Sugar', 95, 20)]
        c.executemany("INSERT INTO products (name, price, stock) VALUES (?,?,?)", items)
    
    conn.commit()
    conn.close()

init_db()

def get_conn():
    return sqlite3.connect('pos_system.db')

# --- LOGIN ---
def login_page():
    st.title("🛒 M.H.M 786 POS")
    st.caption("Secure Login")
    col1, col2, col3 = st.columns([1, 1.5, 1])
    with col2:
        user = st.text_input("Username", placeholder="admin")
        pwd = st.text_input("Password", type="password", placeholder="Enter 786")
        if st.button("Login"):
            conn = get_conn()
            c = conn.cursor()
            c.execute("SELECT password, role FROM users WHERE username=?", (user,))
            row = c.fetchone()
            conn.close()
            if row and row[0] == pwd:
                st.session_state.logged_in = True
                st.session_state.username = user
                st.rerun()
            else:
                st.error("Invalid! Use admin / 786")

# --- MAIN APP (SAFE VERSION) ---
def main_app():
    st.sidebar.title("📋 Menu")
    st.sidebar.write(f"User: {st.session_state.username}")
    if st.sidebar.button("Logout"):
        st.session_state.logged_in = False
        st.rerun()
    
    st.header("📊 Dashboard (Safe Mode)")
    st.success("✅ App is running without errors! Alhamdulillah!")
    
    # Show Today's Sales
    conn = get_conn()
    today = datetime.now().strftime("%Y-%m-%d")
    df = pd.read_sql_query("SELECT COALESCE(SUM(total), 0) as total FROM sales WHERE date LIKE ?", (today+'%',), conn)
    today_sales = df['total'].iloc[0]
    conn.close()
    
    col1, col2 = st.columns(2)
    col1.metric("Today's Sales", f"Rs. {today_sales:.2f}")
    col2.metric("Status", "✅ Working")
    
    st.info("Now we will add the full features back one by one. InshaAllah!")

# --- RUN ---
if not st.session_state.logged_in:
    login_page()
else:
    main_app()
