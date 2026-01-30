import streamlit as st
import pandas as pd

# 1. 頁面設定
st.set_page_config(page_title="環保證照管理系統", layout="wide")

# 2. 資料連結 [您的 Google Sheet 連結]
URL = "https://docs.google.com/spreadsheets/d/1BA427GfGw41UWen083KSWxbdRwbe3a1SEF_H89MyBZE/export?format=xlsx"
SHEET_NAME = "大豐既有許可證到期提醒"

@st.cache_data(ttl=10) # 縮短快取，確保改 Excel 後立刻生效
def load_data():
    # 讀取 Excel
    df = pd.read_excel(URL, sheet_name=SHEET_NAME)
    # 強制將所有欄位名稱轉為字串並去除空白
    df.columns = [str(c).strip() for c in df.columns]
    return df

try:
    df = load_data()

    # --- 3. 側邊選單 (Sidebar) ---
    st.sidebar.markdown("## 📂 系統導覽")
    
    # 這裡用第 0 欄（A 欄：許可證類型）來做分類
    type_col = df.columns[0]
    sel_type = st.sidebar.selectbox("選擇類型", sorted(df[type_col].dropna().unique()))
    
    sub_df = df[df[type_col] == sel_type].copy()
    
    # 這裡用第 2 欄（C 欄：許可證名稱）來做選擇
    name_col = df.columns[2]
    sel_name = st.sidebar.radio("選擇許可證", sub_df[name_col].dropna().unique())

    # --- 🚀 4. 核心修正：用位置 (E 欄) 抓日期 ---
    # 找到選中名稱的那一列
    target_row = sub_df[sub_df[name_col] == sel_name].iloc[0]
    
    # 直接抓第 4 個索引（也就是第 5 欄，E 欄：到期日期）
    # 這樣不管你的標題叫什麼，程式只認位置
    raw_date_val = target_row.iloc[4] 
    
    # 強制轉字串並只取 YYYY-MM-DD
    clean_date = str(raw_date_val)[:10] if str(raw_date_val) != 'nan' else "未設定"

    # ✅ 呈現標題：名稱 (日期)
    st.title(f"📄 {sel_name} ({clean_date})")

    # 呈現管制編號（第 1 索引，B 欄）
    st.markdown(f"### 管制編號：{target_row.iloc[1]}")
    
    st.divider()

    # --- 5. 數據總表 ---
    with st.expander("📊 數據詳細內容"):
        st.dataframe(sub_df, use_container_width=True, hide_index=True)

except Exception as e:
    st.error(f"系統發生錯誤，請檢查 Excel 結構：{e}")
