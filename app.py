import streamlit as st
import pandas as pd

# 1. 頁面基礎設定
st.set_page_config(page_title="大豐許可證管理系統", layout="wide")

# 2. 資料來源 (鎖定 Google Sheet)
URL = "https://docs.google.com/spreadsheets/d/1BA427GfGw41UWen083KSWxbdRwbe3a1SEF_H89MyBZE/export?format=xlsx"
SHEET_NAME = "大豐既有許可證到期提醒"

# 徹底拔掉舊快取，確保資料即時讀取
try:
    # 讀取 Excel
    df = pd.read_excel(URL, sheet_name=SHEET_NAME)
    # 清除欄位標題可能的空格
    df.columns = [str(c).strip() for c in df.columns]

    # --- 🚀 關鍵核心：預先組合 C 欄 (Index 2) 與 D 欄 (Index 3) ---
    def combine_info(row):
        name = str(row.iloc[2])     # C 欄：名稱
        # 處理日期：只取前 10 位 (YYYY-MM-DD)，若沒填則顯示未設定
        raw_date = str(row.iloc[3])
        clean_date = raw_date[:10] if raw_date != 'nan' else "未設定"
        return f"{name} ({clean_date})"

    # 建立一個隱藏的組合欄位供標題使用
    df["標題組合"] = df.apply(combine_info, axis=1)

    # --- 3. 側邊選單 (Sidebar) ---
    st.sidebar.markdown("## 📂 系統導覽")
    
    # 類型選擇 (A 欄)
    sel_type = st.sidebar.selectbox("1. 選擇類型", sorted(df.iloc[:, 0].dropna().unique()))
    sub_df = df[df.iloc[:, 0] == sel_type].copy()
    
    # 選單選擇 (顯示 C+D 的組合)
    sel_item = st.sidebar.radio("2. 選擇許可證", sub_df["標題組合"].tolist())

    # --- 4. 主畫面呈現 ---
    # ✅ 標題直接噴出你指定的兩格資料 (C+D)
    st.title(f"📄 {sel_item}")

    # 抓取該列的其他資訊 (例如 B 欄的管制編號)
    target_row = sub_df[sub_df["標題組合"] == sel_item].iloc[0]
    st.info(f"🆔 管制編號：{target_row.iloc[1]}")
    
    st.divider()

    # --- 5. 數據總表 (折疊區塊) ---
    with st.expander("📊 查看詳細數據明細"):
        # 顯示時移除我們加的臨時組合欄位
        st.dataframe(sub_df.drop(columns=["標題組合"]), use_container_width=True, hide_index=True)

except Exception as e:
    st.error(f"❌ 系統讀取失敗，請確認 Excel 分頁名稱是否為「{SHEET_NAME}」。")
    st.info(f"偵測到的錯誤：{e}")
