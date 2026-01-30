import streamlit as st
import pandas as pd

# 1. 頁面設定
st.set_page_config(page_title="大豐證照系統", layout="wide")

# 2. 資料來源 (確保連結正確)
URL = "https://docs.google.com/spreadsheets/d/1BA427GfGw41UWen083KSWxbdRwbe3a1SEF_H89MyBZE/export?format=xlsx"
SHEET_NAME = "大豐既有許可證到期提醒"

# --- 徹底拔掉快取函數，直接寫在外面 ---
try:
    # 每次跑程式都重新下載 Excel
    df = pd.read_excel(URL, sheet_name=SHEET_NAME)
    df.columns = [str(c).strip() for c in df.columns] # 清理空格

    # 3. 側邊選單
    st.sidebar.header("📂 系統導覽")
    
    # 類型選擇 (A欄)
    sel_type = st.sidebar.selectbox("1. 選擇類型", sorted(df.iloc[:, 0].dropna().unique()))
    sub = df[df.iloc[:, 0] == sel_type].copy()
    
    # 名稱選擇 (C欄)
    sel_name = st.sidebar.radio("2. 選擇許可證", sub.iloc[:, 2].dropna().unique())

    # 4. 抓取資料列
    target = sub[sub.iloc[:, 2] == sel_name].iloc[0]
    
    # 強制抓取 E 欄日期 (Index 4)
    raw_date = str(target.iloc[4])
    clean_date = raw_date[:10] if raw_date != 'nan' else "未設定日期"

    # --- 🚀 畫面呈現 (強制刷新點) ---
    st.title(f"📄 {sel_name}")
    
    # 這裡我用紅色的標籤，讓它比標題更顯眼
    st.error(f"📅 許可證到期日：{clean_date}")
    
    st.markdown(f"### 🆔 管制編號：{target.iloc[1]}")
    
    st.divider()

    # 5. 資料表
    with st.expander("📊 詳細數據"):
        st.dataframe(sub, use_container_width=True, hide_index=True)

except Exception as e:
    st.error(f"連線失敗或欄位錯誤：{e}")
