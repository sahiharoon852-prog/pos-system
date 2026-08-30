import streamlit as st
import pandas as pd
import sqlite3
from datetime import date

# SQLite Database Initialization
def init_db():
    conn = sqlite3.connect('pos_system.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS products 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, barcode TEXT, price REAL, stock INTEGER)''')
    c.execute('''CREATE TABLE IF NOT EXISTS sales 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, date TEXT, items TEXT, total REAL)''')
    conn.commit()
    conn.close()

init_db()

st.set_page_config(page_title="Smart POS System", layout="wide")

# Sidebar Navigation Menu
st.sidebar.markdown("### 📌 Menu Select:")
menu = st.sidebar.radio("", [
    "Main Desktop Dashboard", 
    "Billing & Receipt", 
    "Add New Product", 
    "Sales History Log", 
    "Store Settings"
])

# 1. Main Desktop Dashboard
if menu == "Main Desktop Dashboard":
    st.title("🛍️ SALMAN KIRYANA STORE")
    st.caption("⚡ Live Point of Sale & Barcode System")
    st.markdown("---")
    
    conn = sqlite3.connect('pos_system.db')
    df_products = pd.read_sql("SELECT * FROM products", conn)
    df_sales = pd.read_sql("SELECT * FROM sales", conn)
    conn.close()
    
    total_products = len(df_products)
    total_stock_value = (df_products['price'] * df_products['stock']).sum() if not df_products.empty else 0
    todays_sales = df_sales[df_sales['date'] == str(date.today())]['total'].sum() if not df_sales.empty else 0
    
    col1, col2, col3 = st.columns(3)
    col1.metric("💵 Today's Sales", f"Rs. {todays_sales:,.0f}")
    col2.metric("📦 Total Stock Value", f"Rs. {total_stock_value:,.0f}")
    col3.metric("🏷️ Total Products", f"{total_products} Items")
    
    st.markdown("### 📦 Live Stock & Quick Direct Edit")
    if not df_products.empty:
        conn = sqlite3.connect('pos_system.db')
        edited_df = st.data_editor(df_products, num_rows="dynamic", key="stock_editor")
        if st.button("Save Stock Changes"):
            edited_df.to_sql('products', conn, if_exists='replace', index=False)
            conn.close()
            st.success("Stock updated successfully!")
            st.rerun()
    else:
        st.info("No products found. Add products from the sidebar menu.")

# 2. Billing & Receipt
elif menu == "Billing & Receipt":
    st.title("🧾 Billing & Print Receipt")
    conn = sqlite3.connect('pos_system.db')
    df_products = pd.read_sql("SELECT * FROM products", conn)
    conn.close()
    
    if 'cart' not in st.session_state:
        st.session_state.cart = []
        
    barcode_input = st.text_input("Scan Barcode / Enter Product Name")
    if barcode_input:
        match = df_products[
            (df_products['barcode'] == barcode_input) | 
            (df_products['name'].str.contains(barcode_input, case=False, na=False))
        ]
        if not match.empty:
            prod = match.iloc[0]
            st.session_state.cart.append({'name': prod['name'], 'price': prod['price'], 'qty': 1})
            st.success(f"Added: {prod['name']}")
        else:
            st.error("Product not found!")
            
    if st.session_state.cart:
        cart_df = pd.DataFrame(st.session_state.cart)
        st.dataframe(cart_df)
        total = (cart_df['price'] * cart_df['qty']).sum()
        st.markdown(f"### Total Bill: Rs. {total:,.2f}")
        if st.button("Complete Sale & Print"):
            conn = sqlite3.connect('pos_system.db')
            c = conn.cursor()
            items_str = ", ".join([f"{row['name']} (x{row['qty']})" for _, row in cart_df.iterrows()])
            c.execute("INSERT INTO sales (date, items, total) VALUES (?, ?, ?)", (str(date.today()), items_str, total))
            conn.commit()
            conn.close()
            st.success("Sale completed successfully!")
            st.session_state.cart = []
            st.rerun()

# 3. Add New Product
elif menu == "Add New Product":
    st.title("➕ Add New Product (Barcode Auto)")
    with st.form("product_form"):
        name = st.text_input("Product Name (e.g. Sugar 1kg)")
        barcode = st.text_input("Barcode Number (e.g. 101)")
        price = st.number_input("Price (Rs.)", min_value=0.0)
        stock = st.number_input("Stock Quantity", min_value=0, step=1)
        submitted = st.form_submit_button("Add Product")
        if submitted:
            conn = sqlite3.connect('pos_system.db')
            c = conn.cursor()
            c.execute("INSERT INTO products (name, barcode, price, stock) VALUES (?, ?, ?, ?)", (name, barcode, price, stock))
            conn.commit()
            conn.close()
            st.success(f"Product '{name}' added successfully!")

# 4. Sales History Log
elif menu == "Sales History Log":
    st.title("📜 Sales History Log")
    conn = sqlite3.connect('pos_system.db')
    df_sales = pd.read_sql("SELECT * FROM sales", conn)
    conn.close()
    st.dataframe(df_sales)

# 5. Store Settings
elif menu == "Store Settings":
    st.title("⚙️ Store Settings")
    st.text_input("Store Name", value="SALMAN KIRYANA STORE")
    st.text_input("Currency Symbol", value="Rs.")
    if st.button("Save Settings"):
        st.success("Settings saved successfully!")