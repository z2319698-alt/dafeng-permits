import streamlit as st
import pandas as pd

# 1. 頁面設定
st.set_page_config(page_title="環保證照管理系統", layout="wide")

# 2. 資料連結
URL = "https://docs.google.com/spreadsheets/d/1BA427GfGw41UWen083KSWxbdRwbe3a1SEF_H89MyBZE/export?format=xlsx"
SHEET_NAME = "大豐既有許可證到期提醒"

# --- 徹底放棄快取，確保標題日期秒更新 ---
def load_data_fresh():
    df = pd.read_excel(URL, sheet_name=SHEET_NAME)
    df.columns = df.columns.astype(str).str.strip()
    return df

try:
    df = load_data_fresh()

    # --- 側邊選單 (Sidebar) ---
    st.sidebar.markdown("## 📂 系統導覽")
    
    # 選擇類型
    t_list = sorted(df["許可證類型"].dropna().unique().tolist())
    sel_type = st.sidebar.selectbox("選擇類型", t_list)
    
    # 過濾資料
    sub = df[df["許可證類型"] == sel_type].copy()
    
    # 選擇許可證名稱
    n_list = sub["許可證名稱"].dropna().tolist()
    sel_name = st.sidebar.radio("選擇許可證", n_list)

    # --- 🚀 關鍵核心：標題後面直接黏上日期 ---
    # 從同一張表抓日期 (E 欄)
    target_row = sub[sub["許可證名稱"] == sel_name].iloc[0]
    raw_date = str(target_row["到期日期"])
    
    # 清理日期文字 (只取 YYYY-MM-DD 部分)
    clean_date = raw_date.split(" ")[0] if " " in raw_date else raw_date

    # ✅ 這是你要的：標題字串直接強行組合
    # 顯示效果如：📄 大豐全興廠空污操作許可 (2027-02-10)
    st.title(f"📄 {sel_name} ({clean_date})")

    # --- 副標題：呈現管制編號 ---
    st.markdown(f"#### 管制編號：{target_row['管制編號']}")
    
    st.divider()

    # --- 數據總表 ---
    with st.expander("📊 數據總表"):
        st.dataframe(sub, use_container_width=True, hide_index=True)

except Exception as e:
    st.error(f"讀取失敗：{e}")
