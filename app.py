import streamlit as st
import pandas as pd

# ================= 基本設定 =================
st.set_page_config(page_title="環保證照管理系統", layout="wide")

URL = (
    "https://docs.google.com/spreadsheets/d/"
    "1BA427GfGw41UWen083KSWxbdRwbe3a1SEF_H89MyBZE"
    "/export?format=xlsx"
)

SHEET_NAME = "大豐既有許可證到期提醒"

# ================= 讀取資料 =================
@st.cache_data(show_spinner=False)
def load_data():
    df = pd.read_excel(URL, sheet_name=SHEET_NAME)
    return df

df = load_data()

# ================= 資料清理 =================
df.columns = df.columns.astype(str).str.strip()

df["許可證類型"] = df["許可證類型"].astype(str).str.strip()
df["許可證名稱"] = df["許可證名稱"].astype(str).str.strip()
df["管制編號"] = df["管制編號"].astype(str).str.strip()
df["到期日期"] = pd.to_datetime(df["到期日期"], errors="coerce")

# ================= Sidebar =================
st.sidebar.markdown("## 📂 系統導航")

sel_type = st.sidebar.selectbox(
    "選擇類型",
    sorted(df["許可證類型"].dropna().unique().tolist())
)

sub_df = df[df["許可證類型"] == sel_type]

sel_name = st.sidebar.radio(
    "選擇許可證",
    sub_df["許可證名稱"].dropna().unique().tolist()
)

# ================= 主畫面 =================
st.title(f"📄 {sel_name}")

# 直接抓那一列
row = sub_df[sub_df["許可證名稱"] == sel_name].iloc[0]

permit_no = row["管制編號"]
expire_dt = (
    row["到期日期"].strftime("%Y-%m-%d")
    if pd.notna(row["到期日期"])
    else "未設定"
)

# ✅ 你要的那一行（跟截圖一樣）
st.markdown(
    f"<h4>管制編號：{permit_no}　　到期日期：{expire_dt}</h4>",
    unsafe_allow_html=True
)

# ================= 下面原本的東西（可留可刪） =================
st.divider()

with st.expander("📊 數據總表"):
    st.dataframe(sub_df, use_container_width=True, hide_index=True)
