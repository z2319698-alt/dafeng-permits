import streamlit as st
import pandas as pd

# 1. 頁面設定
st.set_page_config(page_title="大豐許可證管理系統", layout="wide")

# 2. 資料來源 (鎖定 Google Sheet)
URL = "https://docs.google.com/spreadsheets/d/1BA427GfGw41UWen083KSWxbdRwbe3a1SEF_H89MyBZE/export?format=xlsx"
SHEET_NAME = "大豐既有許可證到期提醒"

try:
    # 徹底拔掉快取，確保直接讀取你改好的 Excel
    df = pd.read_excel(URL, sheet_name=SHEET_NAME)
    df.columns = [str(c).strip() for c in df.columns]

    # --- 3. 側邊選單 (Sidebar) ---
    st.sidebar.markdown("## 📂 系統導覽")
    
    # A 欄 (位置0)：許可證類型
    sel_type = st.sidebar.selectbox("1. 選擇類型", sorted(df.iloc[:, 0].dropna().unique()))
    sub_df = df[df.iloc[:, 0] == sel_type].copy()
    
    # --- 🚀 關鍵：這裡直接抓你改好的 D 欄 (位置3) ---
    # 因為你說你已經把 D 欄改成名稱+日期了，我們直接用它
    sel_header = st.sidebar.radio("2. 選擇許可證", sub_df.iloc[:, 3].dropna().unique())

    # --- 4. 主畫面呈現 ---
    # ✅ 直接顯示你選到的 D 欄內容
    st.title(f"📄 {sel_header}")

    # 抓取對應的管制編號 (B 欄，位置1)
    target_row = sub_df[sub_df.iloc[:, 3] == sel_header].iloc[0]
    st.info(f"🆔 管制編號：{target_row.iloc[1]}")
    
    st.divider()

    # --- 5. 詳細資料表 ---
    with st.expander("📊 原始數據明細"):
        st.dataframe(sub_df, use_container_width=True, hide_index=True)

except Exception as e:
    st.error(f"讀取失敗：{e}")
