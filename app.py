import streamlit as st
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

# =========================
# PAGE CONFIG
# =========================
st.set_page_config(page_title="Pro Business Dashboard", layout="wide")

# =========================
# SIDEBAR
# =========================
st.sidebar.title("📊 Dashboard Panel")
st.sidebar.info("🚀 Powered by Ahmet Ince Analytics")

st.sidebar.markdown("### 📌 Filtreler")

# =========================
# HEADER
# =========================
st.title("💼 PRO Business Analytics Dashboard")

st.markdown("""
### Veri odaklı satış analizi + ürün öneri sistemi
""")

# =========================
# FILE UPLOAD
# =========================
uploaded_file = st.file_uploader("CSV dosyanızı yükleyin", type=["csv"])

if uploaded_file:

    df = pd.read_csv(uploaded_file)

    st.subheader("📌 Veri Önizleme")
    st.dataframe(df.head())

    # =========================
    # CHECK
    # =========================
    required_cols = ["date", "product", "quantity", "price"]

    if not all(col in df.columns for col in required_cols):
        st.error("CSV format hatalı!")
    else:

        # =========================
        # FEATURE ENGINEERING
        # =========================
        df["date"] = pd.to_datetime(df["date"])
        df["revenue"] = df["quantity"] * df["price"]

        # =========================
        # KPI METRICS
        # =========================
        total_revenue = df["revenue"].sum()
        total_sales = df["quantity"].sum()
        avg_revenue = df["revenue"].mean()

        col1, col2, col3 = st.columns(3)

        col1.metric("💰 Toplam Gelir", f"{total_revenue:,.0f} ₺")
        col2.metric("🛒 Toplam Satış", total_sales)
        col3.metric("📦 Ortalama Gelir", f"{avg_revenue:,.2f} ₺")

        # =========================
        # PRODUCT ANALYSIS
        # =========================
        st.subheader("📦 Ürün Performansı")

        product_sales = df.groupby("product")["revenue"].sum().sort_values(ascending=False)

        fig, ax = plt.subplots()
        sns.barplot(x=product_sales.values, y=product_sales.index, ax=ax)
        st.pyplot(fig)

        # =========================
        # DAILY SALES
        # =========================
        st.subheader("📅 Günlük Satış")

        daily = df.groupby("date")["revenue"].sum()

        fig2, ax2 = plt.subplots()
        daily.plot(ax=ax2)
        st.pyplot(fig2)

        # =========================
        # INSIGHTS
        # =========================
        st.subheader("🧠 Akıllı Öneriler")

        insights = []

        top_product = product_sales.idxmax()
        low_product = product_sales.idxmin()

        insights.append(f"🔥 En iyi ürün: {top_product}")
        insights.append(f"⚠️ En zayıf ürün: {low_product}")

        if total_revenue < 1000:
            insights.append("📉 Gelir düşük → kampanya gerekli")
        else:
            insights.append("📈 İşletme sağlıklı")

        for i in insights:
            st.write(i)

        # =========================
        # 🚀 RECOMMENDATION ENGINE
        # =========================
        st.subheader("🎯 Ürün Öneri Sistemi")

        mean_value = product_sales.mean()

        strong_products = product_sales[product_sales > mean_value]
        weak_products = product_sales[product_sales <= mean_value]

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("### 🟢 Yüksek Potansiyel Ürünler")
            st.dataframe(strong_products)

        with col2:
            st.markdown("### 🔴 Geliştirilmesi Gereken Ürünler")
            st.dataframe(weak_products)

        # =========================
        # BONUS: OPPORTUNITY PRODUCTS
        # =========================
        st.subheader("🚀 Gizli Fırsatlar")

        opportunity = product_sales[
            (product_sales < mean_value) &
            (product_sales > product_sales.quantile(0.25))
        ]

        st.dataframe(opportunity)

else:
    st.info("CSV yükleyerek başlayın")