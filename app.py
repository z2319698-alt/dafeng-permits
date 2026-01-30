import streamlit as st
import pandas as pd

# 1. 頁面基礎設定
st.set_page_config(page_title="大豐許可證管理系統", layout="wide")

# 2. 資料來源
URL = "https://docs.google.com/spreadsheets/d/1BA427GfGw41UWen083KSWxbdRwbe3a1SEF_H89MyBZE/export?format=xlsx"
SHEET_NAME = "大豐既有許可證到期提醒"

try:
    # 讀取 Excel
    df = pd.read_excel(URL, sheet_name=SHEET_NAME)
    df.columns = [str(c).strip() for c in df.columns]

    # --- 3. 側邊選單 (Sidebar) ---
    st.sidebar.markdown("## 📂 系統導覽")
    
    # 類型選擇 (A 欄)
    sel_type = st.sidebar.selectbox("1. 選擇類型", sorted(df.iloc[:, 0].dropna().unique()))
    sub_df = df[df.iloc[:, 0] == sel_type].copy()
    
    # 名稱選擇 (C 欄)
    sel_name = st.sidebar.radio("2. 選擇許可證", sub_df.iloc[:, 2].dropna().unique())

    # --- 4. 關鍵修正：抓取對應的資料列 ---
    target_row = sub_df[sub_df.iloc[:, 2] == sel_name].iloc[0]
    
    # 取得 B 欄管制編號與 D 欄日期
    permit_id = str(target_row.iloc[1]) # B 欄
    raw_date = str(target_row.iloc[3])  # D 欄
    clean_date = raw_date[:10] if raw_date != 'nan' else "未設定"

    # --- 5. 主畫面呈現 ---
    # ✅ 標題：恢復純名稱 (C 欄)
    st.title(f"📄 {sel_name}")

    # ✅ 副標題：管制編號 + 到期日期 (B 欄 + D 欄)
    # 使用藍色區塊顯示，格式清晰
    st.info(f"🆔 管制編號：{permit_id}　|　📅 到期日期：{clean_date}")
    
    st.divider()

    # 6. 詳細資料表
    with st.expander("📊 查看詳細數據內容"):
        st.dataframe(sub_df, use_container_width=True, hide_index=True)

except Exception as e:
    st.error(f"❌ 讀取失敗：{e}")
