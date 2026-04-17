import streamlit as st
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import sqlite3
from datetime import datetime
from fpdf import FPDF
from mlxtend.frequent_patterns import apriori, association_rules

# =========================
# DATABASE
# =========================
conn = sqlite3.connect("analytics.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    username TEXT PRIMARY KEY,
    password TEXT,
    role TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS uploads (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT,
    filename TEXT,
    total_revenue REAL,
    total_sales REAL,
    created_at TEXT
)
""")

conn.commit()

# =========================
# SESSION
# =========================
if "user" not in st.session_state:
    st.session_state.user = None

if "role" not in st.session_state:
    st.session_state.role = None

# =========================
# LOGIN SYSTEM
# =========================
def login():
    st.title("🔐 Login / Register")

    choice = st.radio("Seçim", ["Login", "Register"])

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Devam Et"):

        if choice == "Register":
            cursor.execute(
                "INSERT OR IGNORE INTO users VALUES (?,?,?)",
                (username, password, "free")
            )
            conn.commit()
            st.success("Kayıt başarılı (Free kullanıcı)")

        else:
            cursor.execute(
                "SELECT * FROM users WHERE username=? AND password=?",
                (username, password)
            )
            user = cursor.fetchone()

            if user:
                st.session_state.user = user[0]
                st.session_state.role = user[2]
                st.rerun()
            else:
                st.error("Hatalı giriş")

# =========================
# PDF REPORT
# =========================
def create_pdf(username, revenue, sales, top_product):

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)

    pdf.cell(200, 10, "Business Analytics Report", ln=True)
    pdf.cell(200, 10, f"User: {username}", ln=True)
    pdf.cell(200, 10, f"Revenue: {revenue}", ln=True)
    pdf.cell(200, 10, f"Sales: {sales}", ln=True)
    pdf.cell(200, 10, f"Top Product: {top_product}", ln=True)

    filename = f"report_{username}.pdf"
    pdf.output(filename)

    return filename

# =========================
# LOGIN CHECK
# =========================
if st.session_state.user is None:
    login()
    st.stop()

# =========================
# DASHBOARD
# =========================
st.set_page_config(page_title="AI SaaS Dashboard", layout="wide")

st.sidebar.title(f"👤 {st.session_state.user}")

# PLAN GÖSTER
st.sidebar.markdown("### 💰 Plan")
if st.session_state.role == "free":
    st.sidebar.warning("Free Plan")
else:
    st.sidebar.success("Pro Plan")

# UPGRADE BUTTON
if st.session_state.role == "free":
    if st.sidebar.button("🚀 Pro'ya Geç"):
        cursor.execute(
            "UPDATE users SET role='pro' WHERE username=?",
            (st.session_state.user,)
        )
        conn.commit()
        st.session_state.role = "pro"
        st.sidebar.success("Artık Pro kullanıcısın 🎉")

# LOGOUT
if st.sidebar.button("Logout"):
    st.session_state.user = None
    st.session_state.role = None
    st.rerun()

st.title("🤖 AI Business Analytics SaaS Dashboard")

# =========================
# FILE UPLOAD
# =========================
uploaded_file = st.file_uploader("CSV yükle", type=["csv"])

if uploaded_file:

    df = pd.read_csv(uploaded_file)
    st.dataframe(df.head())

    required_cols = ["date", "product", "quantity", "price"]

    if not all(col in df.columns for col in required_cols):
        st.error("CSV format hatalı (date, product, quantity, price)")
    else:

        df["date"] = pd.to_datetime(df["date"])
        df["revenue"] = df["quantity"] * df["price"]

        total_revenue = df["revenue"].sum()
        total_sales = df["quantity"].sum()

        product_sales = df.groupby("product")["revenue"].sum()
        top_product = product_sales.idxmax()

        # =========================
        # SAVE DB
        # =========================
        cursor.execute("""
        INSERT INTO uploads VALUES (NULL,?,?,?,?,?)
        """, (
            st.session_state.user,
            uploaded_file.name,
            float(total_revenue),
            float(total_sales),
            str(datetime.now())
        ))
        conn.commit()

        # =========================
        # KPI
        # =========================
        c1, c2, c3 = st.columns(3)
        c1.metric("💰 Revenue", f"{total_revenue:,.0f}")
        c2.metric("🛒 Sales", total_sales)
        c3.metric("🔥 Top Product", top_product)

        # =========================
        # CHART
        # =========================
        st.subheader("📊 Product Performance")

        fig, ax = plt.subplots()
        sns.barplot(x=product_sales.values, y=product_sales.index, ax=ax)
        st.pyplot(fig)

        # =========================
        # ML RECOMMENDATION
        # =========================
        st.subheader("🤖 AI Ürün Öneri Sistemi")

        if st.session_state.role != "pro":
            st.warning("🔒 Bu özellik sadece Pro kullanıcılar için")
        else:
            basket = df.groupby(['date', 'product'])['quantity'].sum().unstack().fillna(0)
            basket = basket.applymap(lambda x: 1 if x > 0 else 0)

            frequent_items = apriori(basket, min_support=0.1, use_colnames=True)
            rules = association_rules(frequent_items, metric="lift", min_threshold=1)

            if not rules.empty:
                rules = rules.sort_values("lift", ascending=False)

                st.write("📌 En güçlü ürün ilişkileri:")

                for i in range(min(5, len(rules))):
                    a = list(rules.iloc[i]["antecedents"])[0]
                    b = list(rules.iloc[i]["consequents"])[0]
                    st.success(f"{a} ➡ {b}")
            else:
                st.warning("Yeterli veri yok")

        # =========================
        # PDF EXPORT
        # =========================
        st.subheader("📄 PDF Rapor")

        if st.session_state.role != "pro":
            st.warning("🔒 PDF export sadece Pro kullanıcılar için")
        else:
            if st.button("PDF oluştur"):
                file = create_pdf(
                    st.session_state.user,
                    total_revenue,
                    total_sales,
                    top_product
                )

                with open(file, "rb") as f:
                    st.download_button("İndir", f, file_name=file)

else:
    st.info("CSV yükleyin")