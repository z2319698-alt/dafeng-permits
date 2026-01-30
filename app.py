import streamlit as st
import pandas as pd

st.set_page_config(page_title="環保證照管理系統", layout="wide")

URL = (
    "https://docs.google.com/spreadsheets/d/"
    "1BA427GfGw41UWen083KSWxbdRwbe3a1SEF_H89MyBZE"
    "/export?format=xlsx"
)

# 分頁名稱定義
MATCH_SHEET = "選擇許可證"
DATA_SHEET = "大豐既有許可證到期提醒"

@st.cache_data(show_spinner=False)
def load_and_map_data():
    # 讀取 Excel 內所有分頁
    all_sh = pd.read_excel(URL, sheet_name=None)
    
    # 1. 抓取原始總表
    master = all_sh.get(DATA_SHEET)
    if master is not None:
        master.columns = master.columns.astype(str).str.strip()
        master['到期日期'] = pd.to_datetime(master['到期日期'], errors='coerce')
    
    # 2. 抓取你新做的「選擇許可證」分頁
    match_df = all_sh.get(MATCH_SHEET)
    lookup_table = {}
    if match_df is not None:
        match_df.columns = match_df.columns.astype(str).str.strip()
        # 把名稱當 Key，編號跟日期當 Value 存成字典，配對最快最準
        for _, row in match_df.iterrows():
            name_key = str(row['名稱']).strip()
            lookup_table[name_key] = {
                "no": str(row['管制編號']).strip(),
                "date": pd.to_datetime(row['到期日期'], errors='coerce').strftime("%Y-%m-%d") if pd.notna(row['到期日期']) else "未設定"
            }
            
    return master, lookup_table

try:
    master_df, lookup = load_and_map_data()

    # --- 左側導航 ---
    st.sidebar.markdown("## 📂 系統導覽")
    sel_type = st.sidebar.selectbox("選擇類型", sorted(master_df["許可證類型"].dropna().unique()))
    sub = master_df[master_df["許可證類型"] == sel_type]
    sel_name = st.sidebar.radio("選擇許可證", sub["許可證名稱"].dropna().unique())

    # --- 主畫面標題 ---
    st.title(f"📄 {sel_name}")

    # --- ✅ 副標題呈現：直接從字典抓資料 ---
    # 這裡完全不寫 if else 邏輯了，直接去 lookup 字典裡撈
    clean_key = str(sel_name).strip()
    
    if clean_key in lookup:
        info = lookup[clean_key]
        # 直接印出你想要的格式
        st.markdown(f"### 管制編號：{info['no']}　　到期日期：{info['date']}")
    else:
        # 如果字典裡找不到，我直接把「數據總表」裡的第一筆抓出來湊合用，保證不留白
        fallback = sub[sub["許可證名稱"] == sel_name]
        if not fallback.empty:
            f_row = fallback.iloc[0]
            f_date = f_row["到期日期"].strftime("%Y-%m-%d") if pd.notna(f_row["到期日期"]) else "未設定"
            st.markdown(f"### 管制編號：{f_row['管制編號']}　　到期日期：{f_date}")

    st.divider()

    # --- 下方數據表 ---
    with st.expander("📊 數據總表"):
        st.dataframe(sub, use_container_width=True, hide_index=True)

except Exception as e:
    st.error(f"系統錯誤: {e}")
