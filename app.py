import streamlit as st
import pandas as pd

st.set_page_config(page_title="環保證照管理系統", layout="wide")

URL = "https://docs.google.com/spreadsheets/d/1BA427GfGw41UWen083KSWxbdRwbe3a1SEF_H89MyBZE/export?format=xlsx"
MAIN_SHEET = "大豐既有許可證到期提醒"

@st.cache_data(ttl=60) # 設定快取只有一分鐘，確保資料會更新
def load_data():
    df = pd.read_excel(URL, sheet_name=MAIN_SHEET)
    df.columns = df.columns.astype(str).str.strip()
    return df

try:
    master_df = load_data()
    
    # --- 1. 左側選單 (Sidebar) ---
    st.sidebar.markdown("## 📂 系統導覽")
    sel_type = st.sidebar.selectbox("選擇類型", sorted(master_df["許可證類型"].dropna().unique()))
    sub_df = master_df[master_df["許可證類型"] == sel_type].copy()
    
    # 這裡只抓名稱，不抓日期做選單，避免選單太長
    sel_name = st.sidebar.radio("選擇許可證", sub_df["許可證名稱"].dropna().unique())

    # --- 2. 核心抓取：直接針對選中的名稱去撈那一列的日期 ---
    # 使用 iloc[0] 確保只抓第一筆符合的資料
    target_info = sub_df[sub_df["許可證名稱"] == sel_name].iloc[0]
    
    # 【關鍵修正】不管 Excel 裡面是 Timestamp 還是字串，強行轉成 YYYY-MM-DD
    try:
        raw_date = target_info["到期日期"]
        if pd.isna(raw_date):
            date_display = "未設定"
        else:
            # 這裡強制只取前 10 位數 (即 YYYY-MM-DD)，把 00:00:00 砍掉
            date_display = str(raw_date)[:10] 
    except:
        date_display = "格式錯誤"

    # ✅ 直接呈現：名稱 (日期)
    st.title(f"📄 {sel_name} ({date_display})")

    # 順便把你要的管制編號也噴出來，位置就在標題正下方
    st.write(f"### 管制編號：{target_info['管制編號']}")

    st.divider()

    # --- 3. 數據總表 (保留原本功能) ---
    with st.expander("📊 數據詳細內容"):
        st.dataframe(sub_df, use_container_width=True, hide_index=True)

except Exception as e:
    st.error(f"程式噴錯了，請檢查 Excel 欄位：{e}")
