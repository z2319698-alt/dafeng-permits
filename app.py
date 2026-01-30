import streamlit as st
import pandas as pd

# 1. 頁面設定
st.set_page_config(page_title="環保證照管理系統", layout="wide")

# 2. 資料連結 (Excel)
URL = "https://docs.google.com/spreadsheets/d/1BA427GfGw41UWen083KSWxbdRwbe3a1SEF_H89MyBZE/export?format=xlsx"
SHEET_NAME = "大豐既有許可證到期提醒"

@st.cache_data(ttl=5)
def load_data():
    # 直接讀取 Excel
    df = pd.read_excel(URL, sheet_name=SHEET_NAME)
    # 清理欄位名稱空白
    df.columns = [str(c).strip() for c in df.columns]
    return df

try:
    df = load_data()

    # --- 3. 側邊選單 (Sidebar) ---
    st.sidebar.markdown("## 📂 系統導覽")
    
    # 選擇類型 (A 欄)
    sel_type = st.sidebar.selectbox("1. 選擇類型", sorted(df.iloc[:, 0].dropna().unique()))
    
    # 過濾出該類型的資料範圍 (例如該類型的 C2-C17 與 E2-E17)
    sub_df = df[df.iloc[:, 0] == sel_type].copy()

    # --- 🚀 關鍵修正：強制合併 C 欄與 E 欄內容 ---
    # 我們建立一個新欄位叫「組合名稱」，把名稱和日期黏起來
    def combine_name_date(row):
        name = str(row.iloc[2]) # C 欄：名稱
        date_val = str(row.iloc[4])[:10] # E 欄：日期 (只取前10位)
        if date_val == 'nan': date_val = "未設定"
        return f"{name} ({date_val})"

    sub_df["組合名稱"] = sub_df.apply(combine_name_date, axis=1)

    # 2. 左側選單：直接讓使用者選這個「已經黏好日期」的選項
    # 這樣 sel_name 本身就已經包含了 C+E 的內容
    sel_combined = st.sidebar.radio("2. 選擇許可證", sub_df["組合名稱"].unique())

    # --- 4. 主畫面呈現 ---
    # 標題直接噴出你選到的「組合名稱」
    st.title(f"📄 {sel_combined}")

    # 為了顯示下方的管制編號，我們反查回原始資料
    target_row = sub_df[sub_df["組合名稱"] == sel_combined].iloc[0]
    st.markdown(f"### 管制編號：{target_row.iloc[1]}") # B 欄
    
    st.divider()

    # --- 5. 數據總表 ---
    with st.expander("📊 查看詳細數據內容"):
        # 顯示時把我們臨時加的「組合名稱」刪掉，保持畫面乾淨
        st.dataframe(sub_df.drop(columns=["組合名稱"]), use_container_width=True, hide_index=True)

except Exception as e:
    st.error(f"執行失敗：{e}")
