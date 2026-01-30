import streamlit as st
import pandas as pd

# 1. 頁面設定
st.set_page_config(page_title="大豐管理系統", layout="wide")

# 2. 資料來源 (直接鎖定你的 Google Sheet)
URL = "https://docs.google.com/spreadsheets/d/1BA427GfGw41UWen083KSWxbdRwbe3a1SEF_H89MyBZE/export?format=xlsx"

# 這次不設函數，直接在最外層跑，強制每一秒都重新讀取
try:
    # 讀取 Excel (不指定 SHEET_NAME，預設讀取第一張表)
    df = pd.read_excel(URL)
    df.columns = [str(c).strip() for c in df.columns]

    # --- 🚀 核心：強行在選單字串裡就加入日期 ---
    # 我們不再叫程式去「找」日期，我們在產生清單時就把它黏起來
    # C 欄位是名稱 (Index 2)，E 欄位是日期 (Index 4)
    
    def force_combine(row):
        n = str(row.iloc[2]) # 名稱
        d = str(row.iloc[4])[:10] # 日期
        return f"{n} --- 【到期日：{d}】"

    df["顯示名稱"] = df.apply(force_combine, axis=1)

    # 3. 側邊選單
    st.sidebar.title("📂 系統導覽")
    
    # 類型過濾 (A 欄)
    all_types = sorted(df.iloc[:, 0].dropna().unique())
    sel_type = st.sidebar.selectbox("1. 選擇類型", all_types)
    
    sub = df[df.iloc[:, 0] == sel_type].copy()
    
    # 選擇許可證 (這裡的選項現在已經內含日期了)
    sel_item = st.sidebar.radio("2. 選擇許可證", sub["顯示名稱"].tolist())

    # 4. 主畫面呈現
    # ✅ 標題直接顯示這個內含日期的字串
    st.title(f"📄 {sel_item}")

    # 顯示管制編號 (B 欄)
    target = sub[sub["顯示名稱"] == sel_item].iloc[0]
    st.info(f"管制編號：{target.iloc[1]}")
    
    st.divider()

    # 5. 詳細表
    with st.expander("📊 原始數據對照"):
        st.dataframe(sub, use_container_width=True)

except Exception as e:
    st.error(f"連線或讀取失敗：{e}")
