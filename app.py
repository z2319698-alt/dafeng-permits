import streamlit as st
import pandas as pd

# 設定頁面
st.set_page_config(page_title="環保證照管理系統", layout="wide")

# 1. 資料連結與分頁名稱 
URL = "https://docs.google.com/spreadsheets/d/1BA427GfGw41UWen083KSWxbdRwbe3a1SEF_H89MyBZE/export?format=xlsx"
SHEET_NAME = "大豐既有許可證到期提醒"

@st.cache_data(ttl=60)
def load_data():
    # 讀取 Excel 第一個分頁 
    df = pd.read_excel(URL, sheet_name=SHEET_NAME)
    # 強制清理欄位前後空格
    df.columns = df.columns.astype(str).str.strip()
    return df

try:
    df = load_data()

    # --- 2. 左側選單 (Sidebar) ---
    st.sidebar.markdown("## 📂 系統導覽")
    
    # 選擇類型 (欄位：許可證類型) 
    sel_type = st.sidebar.selectbox("選擇類型", sorted(df["許可證類型"].dropna().unique()))
    
    # 過濾該類型的資料
    sub_df = df[df["許可證類型"] == sel_type].copy()
    
    # 選擇名稱 (欄位：許可證名稱) 
    sel_name = st.sidebar.radio("選擇許可證", sub_df["許可證名稱"].dropna().unique())

    # --- 3. 核心：標題直接抓取同分頁的「到期日期」 ---
    # 根據左邊選的名稱，找出該列資料 
    target_row = sub_df[sub_df["許可證名稱"] == sel_name].iloc[0]
    
    # 抓取「到期日期」欄位 (Excel 中的 E 欄) 
    # 使用字串擷取前 10 位 (YYYY-MM-DD)，確保不會出現 00:00:00
    raw_date = str(target_row["到期日期"])
    clean_date = raw_date[:10] if raw_date != "nan" else "未設定"

    # ✅ 呈現你要的結果：標題名稱 + 括號日期
    st.title(f"📄 {sel_name} ({clean_date})")

    # 在標題下方顯示管制編號 
    st.markdown(f"### 管制編號：{target_row['管制編號']}")
    
    st.divider()

    # --- 4. 數據總表 (下方呈現) ---
    with st.expander("📊 數據總表"):
        st.dataframe(sub_df, use_container_width=True, hide_index=True)

except Exception as e:
    st.error(f"系統讀取失敗：{e}")
