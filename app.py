import streamlit as st
import pandas as pd

# 1. 頁面基礎設定
st.set_page_config(page_title="環保證照管理系統", layout="wide")

# 2. 資料來源 (鎖定 Google Sheet)
URL = "https://docs.google.com/spreadsheets/d/1BA427GfGw41UWen083KSWxbdRwbe3a1SEF_H89MyBZE/export?format=xlsx"
SHEET_NAME = "大豐既有許可證到期提醒"

@st.cache_data(ttl=5)
def load_data():
    # 讀取 Excel 並清理標題空白
    df = pd.read_excel(URL, sheet_name=SHEET_NAME)
    df.columns = [str(c).strip() for c in df.columns]
    return df

try:
    df = load_data()

    # --- 3. 側邊選單 (Sidebar) ---
    st.sidebar.markdown("## 📂 系統導覽")
    
    # 選擇類型 (A 欄)
    sel_type = st.sidebar.selectbox("1. 選擇類型", sorted(df.iloc[:, 0].dropna().unique()))
    sub_df = df[df.iloc[:, 0] == sel_type].copy()
    
    # 選擇名稱 (C 欄)
    sel_name = st.sidebar.radio("2. 選擇許可證", sub_df.iloc[:, 2].dropna().unique())

    # --- 4. 關鍵核心：在大標題呈現 C 欄 + D 欄 ---
    # 根據選中的名稱 (C欄)，找回該筆資料的日期 (D欄)
    target_row = sub_df[sub_df.iloc[:, 2] == sel_name].iloc[0]
    
    # 抓取 D 欄日期並格式化 (只取 YYYY-MM-DD)
    target_date = str(target_row.iloc[3])[:10] if str(target_row.iloc[3]) != 'nan' else "未設定"

    # ✅ 標題呈現：名稱(C欄) + 日期(D欄)
    # 這就是你要的 C2-C17 與 D2-D17 的對應呈現
    st.title(f"📄 {sel_name} ({target_date})")

    # 顯示管制編號 (B 欄)
    st.markdown(f"### 🆔 管制編號：{target_row.iloc[1]}")
    
    st.divider()

    # --- 5. 數據總表 (下方折疊區塊) ---
    with st.expander("📊 查看詳細數據總表"):
        st.dataframe(sub_df, use_container_width=True, hide_index=True)

except Exception as e:
    st.error(f"系統讀取失敗：{e}")
