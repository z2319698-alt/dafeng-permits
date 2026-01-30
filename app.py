import streamlit as st
import pandas as pd

st.set_page_config(page_title="環保證照管理系統", layout="wide")

URL = "https://docs.google.com/spreadsheets/d/1BA427GfGw41UWen083KSWxbdRwbe3a1SEF_H89MyBZE/export?format=xlsx"
MAIN_SHEET = "大豐既有許可證到期提醒"
MAP_SHEET = "選擇許可證"

@st.cache_data(show_spinner=False)
def load_data():
    all_sh = pd.read_excel(URL, sheet_name=None)
    # 讀取總表
    df = all_sh.get(MAIN_SHEET)
    df.columns = df.columns.astype(str).str.strip()
    # 讀取你的 2.0 匹配分頁
    m_df = all_sh.get(MAP_SHEET)
    if m_df is not None:
        m_df.columns = m_df.columns.astype(str).str.strip()
    return df, m_df

try:
    master_df, match_db = load_data()
    
    # 1. Sidebar 導覽邏輯 (保留你原本的操作習慣)
    st.sidebar.markdown("## 📂 系統導覽")
    sel_type = st.sidebar.selectbox("選擇類型", sorted(master_df["許可證類型"].dropna().unique()))
    sub_df = master_df[master_df["許可證類型"] == sel_type].copy()
    sel_name = st.sidebar.radio("選擇許可證", sub_df["許可證名稱"].dropna().unique())

    # 2. 主畫面標題
    st.title(f"📄 {sel_name}")

    # ==========================================
    # 🚀 2.0 同步呈現模組：標題正下方副標題
    # ==========================================
    if match_db is not None:
        # 強制用左邊選到的名字去「選擇許可證」分頁找
        # 使用 strip() 防止 Excel 裡有肉眼看不見的空格
        hit = match_db[match_db["名稱"].astype(str).str.strip() == str(sel_name).strip()]
        
        if not hit.empty:
            r = hit.iloc[0]
            p_no = r["管制編號"]
            # 格式化日期
            try:
                dt_obj = pd.to_datetime(r["到期日期"])
                expire_dt = dt_obj.strftime("%Y-%m-%d") if pd.notna(dt_obj) else "未設定"
            except:
                expire_dt = str(r["到期日期"])
            
            # ✅ 直接噴出你要的副標題：管制編號與日期
            st.markdown(f"#### 管制編號：{p_no} ｜ 到期日期：{expire_dt}")
        else:
            # 備援：萬一 2.0 分頁沒這筆，改從總表抓，保證不留白
            f_row = sub_df[sub_df["許可證名稱"] == sel_name].iloc[0]
            f_dt = pd.to_datetime(f_row["到期日期"]).strftime("%Y-%m-%d") if pd.notna(f_row["到期日期"]) else "未設定"
            st.markdown(f"#### 管制編號：{f_row['管制編號']} ｜ 到期日期：{f_dt}")
    # ==========================================

    st.divider()

    # 3. 原本的數據總表呈現 (完全保留)
    with st.expander("📊 數據詳細內容"):
        st.dataframe(sub_df, use_container_width=True, hide_index=True)

except Exception as e:
    st.error(f"系統合併運行失敗：{e}")
