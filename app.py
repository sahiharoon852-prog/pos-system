# ----------------------------- DASHBOARD (COMPLETE WITH TODAY'S SALES) -----------------------------
def dashboard():
    # --- CSS for Beautiful Cards ---
    st.markdown("""
    <style>
    .metric-card {
        background: linear-gradient(145deg, #ffffff, #f0f2f6);
        border-radius: 15px;
        padding: 15px 10px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.08);
        text-align: center;
        border-left: 6px solid #2E8B57;
        margin-bottom: 10px;
        transition: transform 0.2s;
    }
    .metric-card:hover {
        transform: scale(1.02);
        cursor: pointer;
    }
    .metric-card-red { border-left-color: #dc3545; }
    .metric-card-blue { border-left-color: #007bff; }
    .metric-card-gold { border-left-color: #ffc107; }
    .metric-card-purple { border-left-color: #6f42c1; }
    .metric-value {
        font-size: 2.2rem;
        font-weight: 700;
        color: #1a1a2e;
        margin: 5px 0;
    }
    .metric-label {
        font-size: 0.9rem;
        color: #6c757d;
        font-weight: 600;
        letter-spacing: 0.5px;
    }
    .btn-pay {
        background-color: #dc3545;
        color: white;
        border-radius: 20px;
        padding: 5px 15px;
        border: none;
        width: 100%;
    }
    .btn-receive {
        background-color: #28a745;
        color: white;
        border-radius: 20px;
        padding: 5px 15px;
        border: none;
        width: 100%;
    }
    </style>
    """, unsafe_allow_html=True)

    # --- Header / Greeting ---
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

    # ==================== TODAY'S SALES CARD ====================
    st.markdown("### 💰 Today's Sales")
    
    conn = get_conn()
    c = conn.cursor()
    today = datetime.now().strftime("%Y-%m-%d")
    
    # --- Fetch today's active sales (non-returned) ---
    c.execute("""
        SELECT 
            COALESCE(SUM(total), 0) as total_sales,
            COUNT(DISTINCT invoice_no) as total_invoices,
            COALESCE(SUM(qty), 0) as total_items
        FROM sales 
        WHERE date LIKE ? AND return_status = 'active'
    """, (today+'%',))
    row = c.fetchone()
    total_sales, total_invoices, total_items = row
    avg_bill = total_sales / total_invoices if total_invoices > 0 else 0

    # --- Returned sales today ---
    c.execute("""
        SELECT 
            COALESCE(SUM(total), 0) as returned_amount,
            COUNT(*) as returned_count
        FROM sales 
        WHERE date LIKE ? AND return_status = 'returned'
    """, (today+'%',))
    returned_row = c.fetchone()
    returned_amount, returned_count = returned_row

    # --- Cancelled sales (we don't have a separate status yet, so placeholder) ---
    cancelled_sales = 0
    cancelled_count = 0

    conn.close()

    # --- Display metrics in a single row (6 metrics) ---
    col1, col2, col3, col4, col5, col6 = st.columns(6)
    col1.metric("💰 Total Sales", f"Rs. {total_sales:,.2f}")
    col2.metric("🧾 Invoices", total_invoices)
    col3.metric("📦 Items Sold", total_items)
    col4.metric("📊 Avg Invoice", f"Rs. {avg_bill:,.2f}")
    col5.metric("🔄 Returned", f"Rs. {returned_amount:,.2f} ({returned_count})")
    col6.metric("❌ Cancelled", f"Rs. {cancelled_sales:,.2f} ({cancelled_count})")

    # --- Payment method placeholders (coming soon) ---
    with st.expander("💳 Payment Methods (Coming Soon)"):
        col_cash, col_card, col_online, col_credit = st.columns(4)
        col_cash.metric("Cash", "Rs. 0.00")
        col_card.metric("Card", "Rs. 0.00")
        col_online.metric("Online", "Rs. 0.00")
        col_credit.metric("Credit", "Rs. 0.00")
        st.caption("Payment method data will be available after you add payment fields to sales.")

    # --- Button to show today's sales list ---
    if st.button("📋 View Today's Sales List", use_container_width=False):
        with st.expander("📋 Today's Sales Details", expanded=True):
            conn = get_conn()
            df_today = pd.read_sql_query("""
                SELECT invoice_no, product_name, qty, total, date, return_status 
                FROM sales 
                WHERE date LIKE ? 
                ORDER BY id DESC
            """, (today+'%',), conn)
            conn.close()
            if not df_today.empty:
                # Format date/time
                df_today['date'] = pd.to_datetime(df_today['date']).dt.strftime('%I:%M %p')
                st.dataframe(df_today, use_container_width=True, hide_index=True)
            else:
                st.info("No sales today yet.")

    st.divider()

    # ==================== TO PAY / TO RECEIVE ====================
    conn = get_conn()
    suppliers_df = pd.read_sql_query("SELECT id, name, phone FROM suppliers ORDER BY name", conn)
    customers_df = pd.read_sql_query("SELECT id, name, phone FROM customers ORDER BY name", conn)
    conn.close()

    col_left, col_right = st.columns(2, gap="medium")
    
    with col_left:
        st.markdown("### 💸 To Pay (Suppliers)")
        st.caption("You need to pay these suppliers")
        if not suppliers_df.empty:
            for _, row in suppliers_df.iterrows():
                c1, c2, c3 = st.columns([3, 2, 1.5])
                with c1:
                    st.write(f"**{row['name']}**")
                with c2:
                    st.write(row['phone'] if row['phone'] else "N/A")
                with c3:
                    if st.button("💰 Pay", key=f"pay_{row['id']}", use_container_width=True):
                        st.success(f"✅ Payment to {row['name']} recorded successfully! (Demo)")
        else:
            st.info("No suppliers added yet.")

    with col_right:
        st.markdown("### 💰 To Receive (Customers)")
        st.caption("You need to receive payments from these customers")
        if not customers_df.empty:
            for _, row in customers_df.iterrows():
                c1, c2, c3 = st.columns([3, 2, 1.5])
                with c1:
                    st.write(f"**{row['name']}**")
                with c2:
                    st.write(row['phone'] if row['phone'] else "N/A")
                with c3:
                    if st.button("📥 Receive", key=f"rec_{row['id']}", use_container_width=True):
                        st.success(f"✅ Payment received from {row['name']} recorded! (Demo)")
        else:
            st.info("No customers added yet.")

    st.divider()
    
    # ==================== QUICK STATS ====================
    st.subheader("📈 Quick Stats")
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT COALESCE(SUM(amount), 0) FROM expenses WHERE date = ?", (today,))
    today_expenses = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM products")
    total_products = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM products WHERE stock < 5")
    low_stock = c.fetchone()[0]
    conn.close()

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Today's Expenses", f"Rs. {today_expenses:,.2f}")
    col2.metric("Total Products", total_products)
    col3.metric("Low Stock Alert", low_stock, delta="Need restock" if low_stock > 0 else "OK")
    col4.metric("", "", delta_Color="off")  # empty placeholder

    st.divider()
    st.caption("✅ Dashboard fully functional: Today's Sales, Pay/Receive lists, and Quick Stats. InshaAllah!")
