import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime

# --- صفحے کی ترتیب (Page Config) ---
st.set_page_config(page_title="M.H.M 786 Store", page_icon="🛒", layout="wide")

# --- سیشن (Session) کو یاد رکھنا ---
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "cart" not in st.session_state:
    st.session_state.cart = []

# --- ڈیٹا بیس سیٹ اپ (پہلی بار چلے گا تو خود بخود ڈیٹا ڈال دے گا) ---
def init_db():
    conn = sqlite3.connect('pos_system.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS products
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT UNIQUE, price REAL, stock INTEGER)''')
    c.execute('''CREATE TABLE IF NOT EXISTS sales
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, product_name TEXT, qty INTEGER, total REAL, date TEXT)''')
    
    # اگر پہلی بار چل رہا ہے تو کچہری سامان ڈال دو (اب تھوڑا سا زیادہ)
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

# ڈیٹا بیس کو ایک بار آرڈر کرو
init_db()

# --------------------- لاگ ان (Login) پیج ---------------------
def login_page():
    # خوبصورت عنوان
    st.markdown("<h1 style='text-align: center; color: #2E8B57;'>🛒 M.H.M 786 STORE</h1>", unsafe_allow_html=True)
    st.markdown("<h4 style='text-align: center;'>محفوظ پوائنٹ آف سیل سسٹم</h4>", unsafe_allow_html=True)
    st.markdown("---")
    
    # درمیان میں باکس بنائیں
    col1, col2, col3 = st.columns([1, 1.5, 1])
    with col2:
        st.image("https://img.icons8.com/fluency/96/000000/lock.png", width=100)
        st.markdown("### 🔑 ایڈمن لاگ ان")
        password = st.text_input("پن / پاس ورڈ درج کریں", type="password", placeholder="یہاں 786 لکھیں")
        
        if st.button("🚪 لاگ ان کریں", use_container_width=True, type="primary"):
            if password == "786":  # خفیہ پن
                st.session_state.logged_in = True
                st.rerun()
            else:
                st.error("❌ غلط پن! براہ کرم 786 درج کریں۔")
        
        st.caption("📌 ڈیفالٹ پن: **786** (یہ صرف آپ کو معلوم ہو)")

# --------------------- اصل POS ایپ ---------------------
def main_app():
    # --- سائیڈ بار (بائیں جانب) ---
    with st.sidebar:
        st.image("https://img.icons8.com/color/96/000000/grocery-store.png", width=80)
        st.markdown("### 🏪 M.H.M 786 Store")
        
        # لاگ آؤٹ بٹن
        if st.button("🚪 لاگ آؤٹ کریں", use_container_width=True):
            st.session_state.logged_in = False
            st.session_state.cart = []  # کارٹ بھی خالی کر دو
            st.rerun()
        
        st.markdown("---")
        st.header("🛍️ کارٹ میں شامل کریں")
        
        # ڈیٹا بیس سے پراڈکٹس لوڈ کریں
        conn = sqlite3.connect('pos_system.db')
        df_products = pd.read_sql_query("SELECT * FROM products", conn)
        conn.close()
        
        if df_products.empty:
            st.warning("کوئی پراڈکٹ دستیاب نہیں!")
            return
        
        # پراڈکٹ سلیکٹ کریں
        product_names = df_products['name'].tolist()
        selected_product = st.selectbox("پراڈکٹ چنیں", product_names)
        
        # اس پراڈکٹ کی معلومات
        product_row = df_products[df_products['name'] == selected_product]
        price = product_row['price'].values[0]
        max_stock = int(product_row['stock'].values[0])
        
        # اگر اسٹاک موجود ہے تو مقدار ڈالیں
        if max_stock > 0:
            qty = st.number_input("مقدار (Quantity)", min_value=1, max_value=max_stock, value=1, step=1)
            if st.button("➕ کارٹ میں ڈالیں", use_container_width=True, type="primary"):
                st.session_state.cart.append({"name": selected_product, "qty": qty, "price": price})
                st.success(f"✅ {qty} عدد {selected_product} کارٹ میں ڈال دیا!")
        else:
            st.error(f"❌ یہ پراڈکٹ اسٹور میں ختم ہو چکی ہے!")
            st.number_input("مقدار", min_value=1, max_value=1, value=1, step=1, disabled=True)
        
        # چھوٹا سا شماریات (Stats)
        st.markdown("---")
        total_products = df_products.shape[0]
        st.metric("📦 کل پراڈکٹس", total_products)
        st.caption("🇵🇰 ورژن 2.0 - M.H.M 786")

    # --- مین ایریا (درمیان میں بل کا حصہ) ---
    st.title("🧾 M.H.M 786 - بلنگ کاؤنٹر")
    st.caption(f"✅ ایڈمن لاگ ان | آج کی تاریخ: {datetime.now().strftime('%d-%B-%Y %I:%M %p')}")
    
    col_left, col_right = st.columns([2, 1])
    
    with col_left:
        st.subheader("🛒 موجودہ کارٹ")
        if st.session_state.cart:
            df_cart = pd.DataFrame(st.session_state.cart)
            df_cart['کل رقم (Rs.)'] = df_cart['qty'] * df_cart['price']
            st.dataframe(df_cart[['name', 'qty', 'price', 'کل رقم (Rs.)']], use_container_width=True, hide_index=True)
            
            total_bill = df_cart['کل رقم (Rs.)'].sum()
            st.metric("💰 کل بل", f"Rs. {total_bill}")
        else:
            st.info("🛒 کارٹ خالی ہے۔ براہ کرم بائیں جانب سے سامان شامل کریں۔")
    
    with col_right:
        st.subheader("📋 چیک آؤٹ")
        if st.session_state.cart:
            # بل بنانے کا بٹن
            if st.button("✅ بل بنائیں اور سیو کریں", use_container_width=True, type="primary"):
                conn = sqlite3.connect('pos_system.db')
                c = conn.cursor()
                today = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                
                for _, row in df_cart.iterrows():
                    # سیلز ٹیبل میں ڈالیں
                    c.execute("INSERT INTO sales (product_name, qty, total, date) VALUES (?, ?, ?, ?)",
                              (row['name'], row['qty'], row['کل رقم (Rs.)'], today))
                    # اسٹور سے مقدار گھٹائیں
                    c.execute("UPDATE products SET stock = stock - ? WHERE name = ?", (row['qty'], row['name']))
                
                conn.commit()
                conn.close()
                
                st.success("🎉 بل کامیابی سے سیو ہو گیا! اللہ برکت ڈالے۔")
                st.balloons()
                st.session_state.cart = []  # کارٹ خالی کرو
                st.rerun()
            
            # کارٹ خالی کرنے کا بٹن
            if st.button("🗑️ کارٹ خالی کریں", use_container_width=True):
                st.session_state.cart = []
                st.rerun()
        else:
            # اگر کارٹ خالی ہے تو بٹن غیر فعال (Disabled) کر دیں
            st.button("✅ بل بنائیں", disabled=True, use_container_width=True)
            st.button("🗑️ کارٹ خالی کریں", disabled=True, use_container_width=True)
        
        st.divider()
        st.caption("© 2026 M.H.M 786 - جملہ حقوق محفوظ ہیں")

# --------------------- یہ فیصلہ کرتا ہے کہ کون سا صفحہ دکھانا ہے ---------------------
if st.session_state.logged_in:
    main_app()
else:
    login_page()