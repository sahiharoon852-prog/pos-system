import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime

# --- Page Config ---
st.set_page_config(page_title="M.H.M 786 Store", page_icon="🛒", layout="wide")

# --- Session State ---
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "cart" not in st.session_state:
    st.session_state.cart = []
st.set_page_config(page_title="Usman General Store", page_icon="🛒", layout="wide")
# --- Database Setup ---
def init_db():
    conn = sqlite3.connect('pos_system.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS products
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT UNIQUE, price REAL, stock INTEGER)''')
    c.execute('''CREATE TABLE IF NOT EXISTS sales
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, product_name TEXT, qty INTEGER, total REAL, date TEXT)''')
    
    c.execute("SELECT COUNT(*) FROM products")
    if c.fetchone()[0] == 0:
        items = [
            ('Bread (Roti)', 50, 10), 
            ('Milk (1L)', 120, 8), 
            ('Sugar (1kg)', 95, 20), 
            ('Tea (250g)', 220, 15),
            ('Cooking Oil (1L)', 180, 6),
            ('Eggs (Dozen)', 150, 12)
        ]
        c.executemany("INSERT INTO products (name, price, stock) VALUES (?, ?, ?)", items)
    conn.commit()
    conn.close()

init_db()

# --------------------- LOGIN PAGE ---------------------
def login_page():
    st.markdown("<h1 style='text-align: center; color: #2E8B57;'>🛒 M.H.M 786 STORE</h1>", unsafe_allow_html=True)
 st.markdown("<h1 style='text-align: center; color: #2E8B57;'>🛒 USMAN GENERAL STORE</h1>", unsafe_allow_html=True)
    st.markdown("---")
    
    col1, col2, col3 = st.columns([1, 1.5, 1])
    with col2:
        st.image("https://img.icons8.com/fluency/96/000000/lock.png", width=100)
        st.markdown("### 🔑 Admin Login")
        password = st.text_input("Enter PIN / Password", type="password", placeholder="Enter 786 here")
        
        if st.button("🔓 Login", use_container_width=True, type="primary"):
            if password == "786":
                st.session_state.logged_in = True
                st.rerun()
            else:
                st.error("❌ Wrong PIN! Please enter 786.")
        
        st.caption("📌 Default PIN: **786** (Keep this secret)")

# --------------------- MAIN POS APP (ENGLISH) ---------------------
def main_app():
    with st.sidebar:
        st.image("https://img.icons8.com/color/96/000000/grocery-store.png", width=80)
        st.markdown("### 🏪 M.H.M 786 Store")
        
        if st.button("🚪 Logout", use_container_width=True):
            st.session_state.logged_in = False
            st.session_state.cart = []
            st.rerun()
        
        st.markdown("---")
        st.header("🛍️ Add to Cart")
        
        conn = sqlite3.connect('pos_system.db')
        df_products = pd.read_sql_query("SELECT * FROM products", conn)
        conn.close()
        
        if df_products.empty:
            st.warning("No products available!")
            return
        
        product_names = df_products['name'].tolist()
        selected_product = st.selectbox("Select Product", product_names)
        
        product_row = df_products[df_products['name'] == selected_product]
        price = product_row['price'].values[0]
        max_stock = int(product_row['stock'].values[0])
        
        if max_stock > 0:
            qty = st.number_input("Quantity", min_value=1, max_value=max_stock, value=1, step=1)
            if st.button("➕ Add to Cart", use_container_width=True, type="primary"):
                st.session_state.cart.append({"name": selected_product, "qty": qty, "price": price})
  st.markdown("### 🏪 Usman General Store")
        else:
            st.error(f"❌ {selected_product} is out of stock!")
            st.number_input("Quantity", min_value=1, max_value=1, value=1, step=1, disabled=True)
        
        st.markdown("---")
        total_products = df_products.shape[0]
        st.metric("📦 Total Products", total_products)
        st.caption("🇵🇰 Version 2.0 - M.H.M 786")

    # --- Main Area ---
    st.title("🧾 M.H.M 786 - Billing Counter")
    st.caption(f"✅ Admin Logged In | Today: {datetime.now().strftime('%d-%B-%Y %I:%M %p')}")
    
    col_left, col_right = st.columns([2, 1])
    
    with col_left:
        st.subheader("🛒 Current Cart")
        if st.session_state.cart:
            df_cart = pd.DataFrame(st.session_state.cart)
            df_cart['Total (Rs.)'] = df_cart['qty'] * df_cart['price']
            st.dataframe(df_cart[['name', 'qty', 'price', 'Total (Rs.)']], use_container_width=True, hide_index=True)
            
            total_bill = df_cart['Total (Rs.)'].sum()
            st.metric("💰 Total Bill", f"Rs. {total_bill}")
        else:
            st.info("🛒 Cart is empty. Add items from the sidebar.")
    
    with col_right:
        st.subheader("📋 Checkout")
        st.title("🧾 Usman General - Billing Counter")
            if st.button("✅ Generate & Save Bill", use_container_width=True, type="primary"):
                conn = sqlite3.connect('pos_system.db')
                c = conn.cursor()
                today = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                
                for _, row in df_cart.iterrows():
                    c.execute("INSERT INTO sales (product_name, qty, total, date) VALUES (?, ?, ?, ?)",
                              (row['name'], row['qty'], row['Total (Rs.)'], today))
                    c.execute("UPDATE products SET stock = stock - ? WHERE name = ?", (row['qty'], row['name']))
                
                conn.commit()
                conn.close()
                
                st.success("🎉 Bill saved successfully! May Allah bless your business.")
                st.balloons()
                st.session_state.cart = []
                st.rerun()
            
            if st.button("🗑️ Clear Cart", use_container_width=True):
                st.session_state.cart = []
                st.rerun()
        else:
            st.button("✅ Generate Bill", disabled=True, use_container_width=True)
            st.button("🗑️ Clear Cart", disabled=True, use_container_width=True)
        
        st.divider()
        st.caption("© 2026 M.H.M 786 - All Rights Reserved")

# --------------------- RUN ---------------------
if st.session_state.logged_in:
    main_app()
else:
    login_page()
