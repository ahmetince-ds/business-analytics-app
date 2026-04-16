import streamlit as st
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import sqlite3
from datetime import datetime
from fpdf import FPDF

# =========================
# DATABASE
# =========================
conn = sqlite3.connect("analytics.db", check_same_thread=False)
cursor = conn.cursor()

# USERS TABLE
cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    username TEXT PRIMARY KEY,
    password TEXT
)
""")

# UPLOADS TABLE
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
# SESSION STATE
# =========================
if "user" not in st.session_state:
    st.session_state.user = None

# =========================
# LOGIN FUNCTION
# =========================
def login():
    st.title("🔐 Login System")

    choice = st.radio("Seçim", ["Login", "Register"])

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Submit"):

        if choice == "Register":
            cursor.execute("INSERT OR IGNORE INTO users VALUES (?,?)", (username, password))
            conn.commit()
            st.success("Kayıt başarılı, login olabilirsiniz")

        else:
            cursor.execute("SELECT * FROM users WHERE username=? AND password=?", (username, password))
            user = cursor.fetchone()

            if user:
                st.session_state.user = username
                st.success("Login başarılı")
                st.rerun()
            else:
                st.error("Hatalı giriş")

# =========================
# PDF REPORT
# =========================
def create_pdf(username, total_revenue, total_sales, top_product):

    pdf = FPDF()
    pdf.add_page()

    pdf.set_font("Arial", size=12)

    pdf.cell(200, 10, txt="Business Analytics Report", ln=True, align="C")
    pdf.ln(10)

    pdf.cell(200, 10, txt=f"User: {username}", ln=True)
    pdf.cell(200, 10, txt=f"Total Revenue: {total_revenue}", ln=True)
    pdf.cell(200, 10, txt=f"Total Sales: {total_sales}", ln=True)
    pdf.cell(200, 10, txt=f"Top Product: {top_product}", ln=True)

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
st.set_page_config(page_title="Pro SaaS Dashboard", layout="wide")

st.sidebar.title(f"👤 {st.session_state.user}")
st.sidebar.success("Logged in")

if st.sidebar.button("Logout"):
    st.session_state.user = None
    st.rerun()

st.title("💼 PRO SaaS Business Analytics Dashboard")

# =========================
# FILE UPLOAD
# =========================
uploaded_file = st.file_uploader("CSV yükle", type=["csv"])

if uploaded_file:

    df = pd.read_csv(uploaded_file)

    st.dataframe(df.head())

    required_cols = ["date", "product", "quantity", "price"]

    if not all(col in df.columns for col in required_cols):
        st.error("CSV format hatalı")
    else:

        df["date"] = pd.to_datetime(df["date"])
        df["revenue"] = df["quantity"] * df["price"]

        total_revenue = df["revenue"].sum()
        total_sales = df["quantity"].sum()

        product_sales = df.groupby("product")["revenue"].sum().sort_values(ascending=False)
        top_product = product_sales.idxmax()

        # =========================
        # SAVE TO DB
        # =========================
        cursor.execute("""
        INSERT INTO uploads (username, filename, total_revenue, total_sales, created_at)
        VALUES (?,?,?,?,?)
        """, (
            st.session_state.user,
            uploaded_file.name,
            float(total_revenue),
            float(total_sales),
            str(datetime.now())
        ))

        conn.commit()

        # =========================
        # METRICS
        # =========================
        c1, c2, c3 = st.columns(3)

        c1.metric("💰 Revenue", f"{total_revenue:,.0f} ₺")
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
        # PDF EXPORT
        # =========================
        st.subheader("📄 Report Export")

        if st.button("Generate PDF Report"):

            file = create_pdf(
                st.session_state.user,
                total_revenue,
                total_sales,
                top_product
            )

            with open(file, "rb") as f:
                st.download_button("Download PDF", f, file_name=file)

else:
    st.info("CSV yükleyin")