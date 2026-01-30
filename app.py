import streamlit as st
import pandas as pd

# 1. 頁面設定
st.set_page_config(page_title="環保證照管理系統", layout="wide")

# 2. 資料來源
URL = "https://docs.google.com/spreadsheets/d/1BA427GfGw41UWen083KSWxbdRwbe3a1SEF_H89MyBZE/export?format=xlsx"
SHEET_NAME = "大豐既有許可證到期提醒"

@st.cache_data(ttl=30) # 快取 30 秒，方便你改 Excel 後快速看結果
def load_data():
    df = pd.read_excel(URL, sheet_name=SHEET_NAME)
    df.columns = df.columns.astype(str).str.strip()
    # 將日期統一轉成字串，並只保留日期的部分（前10位）
    if "到期日期" in df.columns:
        df["到期日期"] = df["到期日期"].astype(str).str.slice(0, 10)
    return df

try:
    df = load_data()

    # --- 3. 側邊選單 ---
    st.sidebar.markdown("## 📂 系統導覽")
    sel_type = st.sidebar.selectbox("1. 選擇類型", sorted(df["許可證類型"].dropna().unique()))
    sub_df = df[df["許可證類型"] == sel_type].copy()
    sel_name = st.sidebar.radio("2. 選擇許可證", sub_df["許可證名稱"].dropna().unique())

    # --- 4. 標題同步呈現 ---
    # 直接抓出選中名稱的那一列
    target_row = sub_df[sub_df["許可證名稱"] == sel_name].iloc[0]
    
    # 拿到日期文字 (因為在 load_data 處理過了，這裡保證是 YYYY-MM-DD)
    final_date = target_row["到期日期"]

    # ✅ 標題直接掛載括號日期
    st.title(f"📄 {sel_name} ({final_date})")

    # 呈現管制編號
    st.markdown(f"### 管制編號：{target_row['管制編號']}")
    
    st.divider()

    # --- 5. 數據總表 ---
    with st.expander("📊 數據詳細內容"):
        st.dataframe(sub_df, use_container_width=True, hide_index=True)

except Exception as e:
    st.error(f"讀取資料時發生錯誤：{e}")
