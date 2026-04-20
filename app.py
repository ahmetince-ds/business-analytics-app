import streamlit as st
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import sqlite3
from datetime import datetime
from fpdf import FPDF
from mlxtend.frequent_patterns import apriori, association_rules

# =========================
# PAGE CONFIG + UI
# =========================
st.set_page_config(page_title="Smart Analytics", page_icon="📊", layout="wide")

st.markdown("""
<style>
body {background-color: #0E1117; color: white;}
.stMetric {background-color: #1c1f26; padding: 15px; border-radius: 10px;}
.stButton>button {background-color: #4CAF50; color: white; border-radius: 10px;}
</style>
""", unsafe_allow_html=True)

# LOGO + HEADER
st.image("assets/logo.png", width=120)
st.markdown("""
<h1 style='color:#4CAF50;'>Smart Business Analytics</h1>
<p style='color:gray;'>AI destekli satış ve müşteri analizi</p>
""", unsafe_allow_html=True)

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

# DEMO USER
cursor.execute("INSERT OR IGNORE INTO users VALUES ('demo','1234','pro')")
conn.commit()

# =========================
# SESSION
# =========================
if "user" not in st.session_state:
    st.session_state.user = None

if "role" not in st.session_state:
    st.session_state.role = None

# =========================
# LOGIN
# =========================
def login():
    st.title("🔐 Login / Register")

    choice = st.radio("Seçim", ["Login", "Register"])

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Devam Et"):
        if choice == "Register":
            cursor.execute("INSERT OR IGNORE INTO users VALUES (?,?,?)",
                           (username, password, "free"))
            conn.commit()
            st.success("Kayıt başarılı (Free kullanıcı)")

        else:
            cursor.execute("SELECT * FROM users WHERE username=? AND password=?",
                           (username, password))
            user = cursor.fetchone()

            if user:
                st.session_state.user = user[0]
                st.session_state.role = user[2]
                st.rerun()
            else:
                st.error("Hatalı giriş")

    st.markdown("### ⚡ Hızlı Giriş")
    st.info("Demo hesap: demo / 1234")

    if st.button("Demo ile giriş yap"):
        st.session_state.user = "demo"
        st.session_state.role = "pro"
        st.rerun()

# LOGIN CHECK
if st.session_state.user is None:
    login()
    st.stop()

# =========================
# SIDEBAR
# =========================
st.sidebar.title(f"👤 {st.session_state.user}")

st.sidebar.markdown("### 💰 Plan")
if st.session_state.role == "free":
    st.sidebar.warning("Free Plan")
else:
    st.sidebar.success("Pro Plan")

if st.session_state.role == "free":
    if st.sidebar.button("🚀 Pro'ya Geç"):
        cursor.execute("UPDATE users SET role='pro' WHERE username=?",
                       (st.session_state.user,))
        conn.commit()
        st.session_state.role = "pro"
        st.sidebar.success("Pro oldun 🎉")

if st.sidebar.button("Logout"):
    st.session_state.user = None
    st.session_state.role = None
    st.rerun()

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

        product_sales = df.groupby("product")["revenue"].sum()
        top_product = product_sales.idxmax()

        # SAVE DB
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
        # KPI CARDS
        # =========================
        c1, c2, c3 = st.columns(3)

        with c1:
            st.markdown(f"""
            <div style='background:#1c1f26;padding:20px;border-radius:10px'>
            <h3>💰 Revenue</h3>
            <h2>{total_revenue:,.0f} ₺</h2>
            </div>
            """, unsafe_allow_html=True)

        with c2:
            st.markdown(f"""
            <div style='background:#1c1f26;padding:20px;border-radius:10px'>
            <h3>🛒 Sales</h3>
            <h2>{total_sales}</h2>
            </div>
            """, unsafe_allow_html=True)

        with c3:
            st.markdown(f"""
            <div style='background:#1c1f26;padding:20px;border-radius:10px'>
            <h3>🔥 Top Product</h3>
            <h2>{top_product}</h2>
            </div>
            """, unsafe_allow_html=True)

        # =========================
        # CHART
        # =========================
        st.subheader("📊 Ürün Performansı")
        fig, ax = plt.subplots()
        sns.barplot(x=product_sales.values, y=product_sales.index, ax=ax)
        st.pyplot(fig)

        # =========================
        # AI RECOMMENDATION
        # =========================
        st.subheader("🤖 AI Recommendation Engine")

        if st.session_state.role != "pro":
            st.warning("🔒 Sadece Pro kullanıcılar")
        else:
            basket = df.groupby(['date', 'product'])['quantity'].sum().unstack().fillna(0)
            basket = basket > 0  # CLEAN FIX

            frequent_items = apriori(basket, min_support=0.1, use_colnames=True)
            rules = association_rules(frequent_items, metric="lift", min_threshold=1)

            if not rules.empty:
                rules = rules.sort_values("lift", ascending=False)

                for i in range(min(5, len(rules))):
                    a = list(rules.iloc[i]["antecedents"])[0]
                    b = list(rules.iloc[i]["consequents"])[0]
                    st.success(f"{a} ➡ {b}")
            else:
                st.warning("Yeterli veri yok")

        # =========================
        # PDF
        # =========================
        st.subheader("📄 PDF Rapor")

        def create_pdf():
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Arial", size=12)

            pdf.cell(200, 10, "Business Report", ln=True)
            pdf.cell(200, 10, f"Revenue: {total_revenue}", ln=True)
            pdf.cell(200, 10, f"Sales: {total_sales}", ln=True)
            pdf.cell(200, 10, f"Top Product: {top_product}", ln=True)

            file = "report.pdf"
            pdf.output(file)
            return file

        if st.session_state.role != "pro":
            st.warning("🔒 PDF sadece Pro kullanıcılar için")
        else:
            if st.button("PDF oluştur"):
                file = create_pdf()
                with open(file, "rb") as f:
                    st.download_button("İndir", f, file_name=file)

else:
    st.info("CSV yükleyin")