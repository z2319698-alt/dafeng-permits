import streamlit as st
import pandas as pd

# 1. 頁面基礎設定
st.set_page_config(page_title="大豐許可證管理系統", layout="wide")

# 2. 資料來源 (鎖定 Google Sheet)
URL = "https://docs.google.com/spreadsheets/d/1BA427GfGw41UWen083KSWxbdRwbe3a1SEF_H89MyBZE/export?format=xlsx"
SHEET_NAME = "大豐既有許可證到期提醒"

try:
    # 直接讀取 Excel，不使用快取以確保資料最即時
    df = pd.read_excel(URL, sheet_name=SHEET_NAME)
    df.columns = [str(c).strip() for c in df.columns]

    # --- 🚀 關鍵核心：將 C 欄 (Index 2) 與 D 欄 (Index 3) 合併成標題變數 ---
    def get_combined_title(row):
        name = str(row.iloc[2])     # C 欄：名稱
        raw_date = str(row.iloc[3]) # D 欄：日期
        # 格式化日期，只取前 10 碼 (YYYY-MM-DD)
        clean_date = raw_date[:10] if raw_date != 'nan' else "未設定"
        return f"{name} ({clean_date})"

    # 在資料表中建立一個專門給標題用的隱藏欄位
    df["顯示標題"] = df.apply(get_combined_title, axis=1)

    # --- 3. 側邊選單 (Sidebar) ---
    st.sidebar.markdown("## 📂 系統導覽")
    
    # 類型選擇 (A 欄)
    sel_type = st.sidebar.selectbox("1. 選擇類型", sorted(df.iloc[:, 0].dropna().unique()))
    sub_df = df[df.iloc[:, 0] == sel_type].copy()
    
    # 選單選擇 (顯示 C+D 的組合)
    sel_item = st.sidebar.radio("2. 選擇許可證", sub_df["顯示標題"].tolist())

    # --- 4. 主畫面呈現 ---
    # ✅ 標題現在會同時呈現 C 欄與 D 欄的內容
    st.title(f"📄 {sel_item}")

    # 抓取並顯示對應的管制編號 (B 欄)
    target_row = sub_df[sub_df["顯示標題"] == sel_item].iloc[0]
    st.info(f"🆔 管制編號：{target_row.iloc[1]}")
    
    st.divider()

    # --- 5. 數據總表 (折疊區塊) ---
    with st.expander("📊 查看詳細數據內容"):
        # 顯示時移除我們臨時加的「顯示標題」欄位，保持畫面乾淨
        st.dataframe(sub_df.drop(columns=["顯示標題"]), use_container_width=True, hide_index=True)

except Exception as e:
    st.error(f"❌ 讀取失敗：{e}")
