import streamlit as st
import pandas as pd

# 1. 頁面基礎設定
st.set_page_config(page_title="環保證照管理系統", layout="wide")

# 2. 資料連結 (Excel)
URL = "https://docs.google.com/spreadsheets/d/1BA427GfGw41UWen083KSWxbdRwbe3a1SEF_H89MyBZE/export?format=xlsx"
SHEET_NAME = "大豐既有許可證到期提醒"

# --- 💡 這次完全不使用 @st.cache_data，確保每次刷新都是抓最新的 ---
try:
    # 直接讀取，不進快取
    df = pd.read_excel(URL, sheet_name=SHEET_NAME)
    df.columns = [str(c).strip() for c in df.columns]

    # --- 3. 側邊選單 (Sidebar) ---
    st.sidebar.markdown("## 📂 系統導覽")
    
    # 選擇類型 (A 欄)
    type_list = sorted(df.iloc[:, 0].dropna().unique())
    sel_type = st.sidebar.selectbox("1. 選擇類型", type_list)
    
    # 過濾資料
    sub_df = df[df.iloc[:, 0] == sel_type].copy()

    # --- 🚀 關鍵修正：手動建立選單清單，確保 C 欄與 E 欄黏在一起 ---
    display_options = []
    for i in range(len(sub_df)):
        name = str(sub_df.iloc[i, 2])    # C 欄：名稱
        # 直接從 E 欄位抓日期，強制擷取前 10 碼
        raw_date = str(sub_df.iloc[i, 4])
        date_part = raw_date[:10] if raw_date != 'nan' else "未設定"
        
        # 這裡就是你要的結果：名稱 (日期)
        display_options.append(f"{name} ({date_part})")

    # 2. 左側單選按鈕：直接顯示這個組合好的清單
    sel_combined = st.sidebar.radio("2. 選擇許可證", display_options)

    # --- 4. 主畫面呈現 ---
    # ✅ 標題直接顯示你點到的那個選項（裡面已經內含日期了）
    st.title(f"📄 {sel_combined}")

    # 反查該列的其他資料 (如管制編號 B 欄)
    # 找到名稱匹配的那一行
    match_name = sel_combined.split(" (")[0] # 把日期切掉回來找名稱
    target_row = sub_df[sub_df.iloc[:, 2] == match_name].iloc[0]
    
    st.markdown(f"### 管制編號：{target_row.iloc[1]}")
    
    st.divider()

    # --- 5. 數據總表 ---
    with st.expander("📊 查看詳細數據內容"):
        st.dataframe(sub_df, use_container_width=True, hide_index=True)

except Exception as e:
    st.error(f"系統運行錯誤：{e}")
    st.info("請檢查 Excel 連結是否正常，或分頁名稱是否正確。")
