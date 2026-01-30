import streamlit as st
import pandas as pd

# 1. 頁面設定
st.set_page_config(page_title="大豐許可證管理系統", layout="wide")

# 2. 資料來源 (鎖定 Google Sheet)
URL = "https://docs.google.com/spreadsheets/d/1BA427GfGw41UWen083KSWxbdRwbe3a1SEF_H89MyBZE/export?format=xlsx"
SHEET_NAME = "大豐既有許可證到期提醒"

@st.cache_data(ttl=5) # 快取設 5 秒，確保資料即時更新
def load_data():
    df = pd.read_excel(URL, sheet_name=SHEET_NAME)
    df.columns = [str(c).strip() for c in df.columns] # 清除欄位空格
    return df

try:
    df = load_data()

    # --- 3. 側邊選單 (Sidebar) ---
    st.sidebar.markdown("## 📂 系統導覽")
    
    # 類型選擇 (A 欄)
    sel_type = st.sidebar.selectbox("1. 選擇類型", sorted(df.iloc[:, 0].dropna().unique()))
    sub_df = df[df.iloc[:, 0] == sel_type].copy()
    
    # 名稱選擇 (C 欄)
    sel_name = st.sidebar.radio("2. 選擇許可證", sub_df.iloc[:, 2].dropna().unique())

    # --- 🚀 4. 核心修正：大標題強制呈現 C 欄 + D 欄 ---
    # 根據選中的名稱，找回該筆資料
    target_row = sub_df[sub_df.iloc[:, 2] == sel_name].iloc[0]
    
    # 抓取 D 欄日期，強制切掉時間只留 YYYY-MM-DD
    raw_date = str(target_row.iloc[3])
    clean_date = raw_date[:10] if raw_date != 'nan' else "未設定"

    # ✅ 標題呈現：📄 許可證名稱 (到期日期) 
    # 效果：📄 大豐全興廠空污操作許可 (2027-02-10)
    st.title(f"📄 {sel_name} ({clean_date})")

    # 顯示管制編號 (B 欄)
    st.info(f"🆔 管制編號：{target_row.iloc[1]}")
    
    st.divider()

    # --- 5. 數據總表 (展開區塊) ---
    with st.expander("📊 查看詳細數據總表"):
        st.dataframe(sub_df, use_container_width=True, hide_index=True)

except Exception as e:
    st.error(f"系統讀取出錯：{e}")
