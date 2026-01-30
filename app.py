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
    sel_type = st.sidebar.selectbox("1. 選擇類型", sorted(master_df["許可證類型"].dropna().unique()))
    
    # 過濾出該類型的資料
    sub_df = master_df[master_df["許可證類型"] == sel_type].copy()
    
    # --- 關鍵修正：在名稱後面直接算出日期文字 ---
    def get_date_str(name):
        row = sub_df[sub_df["許可證名稱"] == name].iloc[0]
        if pd.notna(row["到期日期"]):
            return row["到期日期"].strftime("%Y-%m-%d")
        return "未設定"

    # 選項清單
    names = sub_df["許可證名稱"].dropna().unique().tolist()
    
    # 2. 左側選單
    sel_name = st.sidebar.radio("2. 選擇許可證", names)

    # --- 🚀 這裡就是你要的：標題 + 日期 ---
    # 直接在選到名字的那一秒，就去抓它的日期
    current_date = get_date_str(sel_name)
    
    # 強制呈現在標題列
    st.title(f"📄 {sel_name} ({current_date})")

    st.divider()

    # 3. 數據總表 (原本的東西，動都不動)
    with st.expander("📊 數據詳細內容"):
        st.dataframe(sub_df, use_container_width=True, hide_index=True)

except Exception as e:
    st.error(f"執行出錯：{e}")
