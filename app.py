import streamlit as st
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="環保證照管理系統", layout="wide")

# ===== Google Sheet 位置 =====
URL = (
    "https://docs.google.com/spreadsheets/d/"
    "1BA427GfGw41UWen083KSWxbdRwbe3a1SEF_H89MyBZE"
    "/export?format=xlsx"
)

# ===== 讀取「就是你截圖那一張表」=====
@st.cache_data(show_spinner=False)
def load_main_table():
    df = pd.read_excel(URL)  # 不指定 sheet，預設第一張（你截圖那張）
    return df

df = load_main_table()

# ===== 基本清理（非常重要）=====
df["許可證名稱"] = df["許可證名稱"].astype(str).str.strip()
df["許可證類型"] = df["許可證類型"].astype(str).str.strip()
df["到期日期"] = pd.to_datetime(df["到期日期"], errors="coerce")

# ===== Sidebar =====
st.sidebar.markdown("## 📂 系統導航")

sel_type = st.sidebar.selectbox(
    "選擇類型",
    sorted(df["許可證類型"].unique())
)

sub_df = df[df["許可證類型"] == sel_type]

sel_name = st.sidebar.radio(
    "選擇許可證",
    sub_df["許可證名稱"].tolist()
)

# ===== 主畫面 =====
st.title(f"📄 {sel_name}")

# ===== 核心：直接顯示數據總表資料 =====
row = sub_df[sub_df["許可證名稱"] == sel_name]

if row.empty:
    st.error("❌ 找不到對應的許可證資料（名稱不一致）")
else:
    r = row.iloc[0]

    st.markdown("### 📌 許可證基本資料")

    c1, c2 = st.columns(2)

    with c1:
        st.metric("管制編號", r["管制編號"])

    with c2:
        if pd.notna(r["到期日期"]):
            st.metric(
                "到期日期",
                r["到期日期"].strftime("%Y-%m-%d")
            )
        else:
            st.metric("到期日期", "未設定")
