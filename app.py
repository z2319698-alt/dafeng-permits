import streamlit as st
import pandas as pd

st.set_page_config(page_title="環保證照管理系統", layout="wide")

URL = (
    "https://docs.google.com/spreadsheets/d/"
    "1BA427GfGw41UWen083KSWxbdRwbe3a1SEF_H89MyBZE"
    "/export?format=xlsx"
)
SHEET_NAME = "大豐既有許可證到期提醒"

@st.cache_data(show_spinner=False)
def load_data():
    # 讀取 Excel
    df = pd.read_excel(URL, sheet_name=SHEET_NAME)
    # 基本清理：把欄位的前後空白去掉
    df.columns = df.columns.astype(str).str.strip()
    # 轉換日期格式
    if "到期日期" in df.columns:
        df["到期日期"] = pd.to_datetime(df["到期日期"], errors="coerce")
    return df

try:
    master = load_data()
    
    # 1. 側邊欄過濾邏輯
    st.sidebar.markdown("## 📂 系統導覽")
    
    # 選類型
    types = sorted(master["許可證類型"].dropna().unique().tolist())
    sel_type = st.sidebar.selectbox("選擇類型", types)
    
    # 根據類型過濾出子表
    sub = master[master["許可證類型"] == sel_type].copy()
    
    # 選名稱
    names = sub["許可證名稱"].dropna().tolist()
    sel_name = st.sidebar.radio("選擇許可證", names)

    # 2. 主畫面呈現
    # 直接顯示標題
    st.title(f"📄 {sel_name}")

    # 【關鍵：不比對、不正規化，直接拿 sub 裡面名稱對應的那一列】
    # 既然 sel_name 是從 sub 抓出來的，這行絕對 100% 抓得到資料
    target_info = sub[sub["許可證名稱"] == sel_name].iloc[0]

    # 準備資料
    permit_no = target_info["管制編號"]
    expire_dt = target_info["到期日期"].strftime("%Y-%m-%d") if pd.notna(target_info["到期日期"]) else "未設定"

    # ✅ 標題正下方呈現（字體設為 h4，稍微縮小）
    st.markdown(f"#### 管制編號：{permit_no}　　到期日期：{expire_dt}")

    # 3. 底部數據總表
    st.divider()
    with st.expander("📊 數據總表（當前類型所有資料）"):
        st.dataframe(sub, use_container_width=True, hide_index=True)

except Exception as e:
    st.error(f"系統發生預期外的錯誤：{e}")
