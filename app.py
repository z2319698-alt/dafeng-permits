import streamlit as st
import pandas as pd

# 1. 頁面基礎設定
st.set_page_config(page_title="大豐許可證管理系統", layout="wide")

# 2. 資料來源 (鎖定你的 Google Sheet)
URL = "https://docs.google.com/spreadsheets/d/1BA427GfGw41UWen083KSWxbdRwbe3a1SEF_H89MyBZE/export?format=xlsx"
SHEET_NAME = "大豐既有許可證到期提醒"

@st.cache_data(ttl=5) # 快取設 5 秒，確保資料同步
def load_data():
    # 讀取 Excel
    df = pd.read_excel(URL, sheet_name=SHEET_NAME)
    # 清理所有欄位名稱的空格
    df.columns = [str(c).strip() for c in df.columns]
    return df

try:
    df = load_data()

    # --- 3. 側邊選單 (Sidebar) ---
    st.sidebar.markdown("## 📂 系統導覽")
    
    # A 欄：許可證類型
    types = sorted(df.iloc[:, 0].dropna().unique())
    sel_type = st.sidebar.selectbox("選擇類型", types)
    
    # 過濾該類型的資料
    sub_df = df[df.iloc[:, 0] == sel_type].copy()

    # --- 🚀 關鍵核心：直接抓取 C 欄 + D 欄 ---
    # 建立一個選項清單，內容是 "C欄文字 (D欄日期)"
    def make_header(row):
        name = str(row.iloc[2]) # C 欄：許可證名稱
        date = str(row.iloc[3])[:10] # D 欄：到期日期 (只取日期部分)
        if date == "nan": date = "未設定"
        return f"{name} ({date})"

    sub_df["顯示標題"] = sub_df.apply(make_header, axis=1)

    # 讓側邊欄顯示組合好的名稱
    sel_title = st.sidebar.radio("選擇許可證", sub_df["顯示標題"].tolist())

    # --- 4. 主畫面呈現 ---
    # ✅ 這裡就是你要的：標題直接呈現這兩格合併後的內容
    st.title(f"📄 {sel_title}")

    # 抓取該列的其他資訊 (例如 B 欄的管制編號)
    target_row = sub_df[sub_df["顯示標題"] == sel_title].iloc[0]
    st.info(f"管制編號：{target_row.iloc[1]}")
    
    st.divider()

    # --- 5. 資料總表 ---
    with st.expander("📊 原始數據對照"):
        st.dataframe(sub_df.drop(columns=["顯示標題"]), use_container_width=True, hide_index=True)

except Exception as e:
    st.error(f"資料讀取失敗，請確認 Excel 分頁名稱。錯誤訊息：{e}")
