import streamlit as st
import pandas as pd

# 1. 基礎設定與 Excel 連結
st.set_page_config(page_title="環保證照管理系統", layout="wide")
URL = "https://docs.google.com/spreadsheets/d/1BA427GfGw41UWen083KSWxbdRwbe3a1SEF_H89MyBZE/export?format=xlsx"
SHEET_NAME = "大豐既有許可證到期提醒"

@st.cache_data(ttl=5) # 快取設極短，確保資料變動立刻更新
def load_data():
    df = pd.read_excel(URL, sheet_name=SHEET_NAME)
    df.columns = [str(c).strip() for c in df.columns] # 清理欄位空白
    return df

try:
    df = load_data()

    # --- 2. 左側選單 (Sidebar) ---
    st.sidebar.markdown("## 📂 系統導覽")
    
    # 選擇類型 (A 欄)
    type_col = df.columns[0]
    sel_type = st.sidebar.selectbox("1. 選擇類型", sorted(df[type_col].dropna().unique()))
    
    # 過濾出該類型的 C2-C17 與 E2-E17 資料
    sub_df = df[df[type_col] == sel_type].copy()

    # --- 🚀 核心修正：強制將 C 欄(名稱)與 E 欄(日期) 合併 ---
    def combine_info(row):
        # 抓取 C 欄名稱
        name = str(row.iloc[2])
        # 抓取 E 欄日期並強制轉為前10位字串
        date_val = str(row.iloc[4])[:10]
        if date_val == 'nan' or date_val == 'None':
            date_val = "未設定"
        return f"{name} ({date_val})"

    # 在過濾後的資料中建立一個「組合標題」欄位
    sub_df["組合標題"] = sub_df.apply(combine_info, axis=1)

    # 讓側邊欄選單顯示這個「組合標題」
    # 這樣你點選時，sel_combined 內容就是：大豐全興廠空污操作許可 (2027-02-10)
    sel_combined = st.sidebar.radio("2. 選擇許可證", sub_df["組合標題"].tolist())

    # --- 3. 主畫面呈現 ---
    # ✅ 標題直接顯示你選到的組合內容，這下絕對不會沒日期了
    st.title(f"📄 {sel_combined}")

    # 反查該列的其他資料 (如管制編號 B 欄)
    target_row = sub_df[sub_df["組合標題"] == sel_combined].iloc[0]
    st.markdown(f"### 管制編號：{target_row.iloc[1]}")
    
    st.divider()

    # --- 4. 數據總表 (下方呈現) ---
    with st.expander("📊 查看詳細數據內容"):
        # 顯示時移除我們加的臨時欄位
        st.dataframe(sub_df.drop(columns=["組合標題"]), use_container_width=True, hide_index=True)

except Exception as e:
    st.error(f"系統運行錯誤：{e}")
