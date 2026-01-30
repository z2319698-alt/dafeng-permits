import streamlit as st
import pandas as pd

st.set_page_config(page_title="環保證照管理系統", layout="wide")

URL = "https://docs.google.com/spreadsheets/d/1BA427GfGw41UWen083KSWxbdRwbe3a1SEF_H89MyBZE/export?format=xlsx"
MAIN_SHEET = "大豐既有許可證到期提醒"

@st.cache_data(show_spinner=False)
def load_data():
    df = pd.read_excel(URL, sheet_name=MAIN_SHEET)
    df.columns = df.columns.astype(str).str.strip()
    if "到期日期" in df.columns:
        df["到期日期"] = pd.to_datetime(df["到期日期"], errors="coerce")
    return df

try:
    master_df = load_data()
    
    # 1. Sidebar 導覽
    st.sidebar.markdown("## 📂 系統導覽")
    sel_type = st.sidebar.selectbox("選擇類型", sorted(master_df["許可證類型"].dropna().unique()))
    sub_df = master_df[master_df["許可證類型"] == sel_type].copy()
    sel_name = st.sidebar.radio("選擇許可證", sub_df["許可證名稱"].dropna().unique())

    # 2. 抓取該許可證的日期資料
    target_row = sub_df[sub_df["許可證名稱"] == sel_name].iloc[0]
    date_val = target_row["到期日期"].strftime("%Y-%m-%d") if pd.notna(target_row["到期日期"]) else "未設定"

    # ✅ 你要的：標題後面直接加日期
    st.title(f"📄 {sel_name} ({date_val})")

    st.divider()

    # 3. 數據總表 (保留不動)
    with st.expander("📊 數據詳細內容"):
        st.dataframe(sub_df, use_container_width=True, hide_index=True)

except Exception as e:
    st.error(f"執行出錯：{e}")
