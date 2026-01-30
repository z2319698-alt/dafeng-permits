import streamlit as st
import pandas as pd
from datetime import datetime as dt
import urllib.parse

# 1. 頁面配置
st.set_page_config(page_title="大豐管理系統", layout="wide")

# 2. 精確法規資料庫
LAW_REQUIREMENTS = {
    "廢棄物清理計畫書": {
        "變更": ["涉及主體、類別、產能擴增達 10% 以上 (廢清法第 31 條)", "廢棄物項目增加或數量異動逾 10%"],
        "異動": ["基本資料更動 (負責人、聯絡人等)", "不涉及製程改變之行政異動"],
        "展延": ["依規於期滿前提出展延申請"]
    },
    "廢棄物清除許可證": {
        "變更": ["清除車輛增加、減少或規格異動", "清除廢棄物種類增加"],
        "變更暨展延": ["同時涉及證照到期與車輛/種類變更"],
        "展延": ["許可證效期屆滿前 6-8 個月申請"]
    },
    "水污染防治措施": {
        "事前變更": ["廢(污)水處理程序改變 (水污法第 14 條)", "每日最大廢水產生量增加 10%"],
        "事後變更": ["不涉及程序改變之微幅異動備查"],
        "展延": ["水污染防治許可效期展延"]
    }
}

# 3. 讀取數據
URL = "https://docs.google.com/spreadsheets/d/1BA427GfGw41UWen083KSWxbdRwbe3a1SEF_H89MyBZE/export?format=xlsx"

@st.cache_data(ttl=60)
def load_all_data():
    all_sh = pd.read_excel(URL, sheet_name=None)
    main_df = None
    # 鎖定含有「檢查表」或「附件」字眼的分頁
    attach_df = next((df for name, df in all_sh.items() if "檢查表" in name or "附件" in name), None)
    
    # 處理合併儲存格：確保類型與項目每一行都有值
    if attach_df is not None:
        attach_df.iloc[:, 0] = attach_df.iloc[:, 0].ffill()
        attach_df.iloc[:, 1] = attach_df.iloc[:, 1].ffill()
    
    for n, df in all_sh.items():
        df.columns = [str(c).strip() for c in df.columns]
        if "許可證名稱" in df.columns:
            main_df = df
    return main_df, attach_df

try:
    df, attach_db = load_all_data()
    C_NAME, C_DATE, C_TYPE = "許可證名稱", "到期日期", "許可證類型"
    df['D'] = pd.to_datetime(df[C_DATE], errors='coerce')
    now = dt.now()

    # 4. 跑馬燈
    urgent = df[(df['D'] <= now + pd.Timedelta(days=180)) & (df['D'].notnull())]
    if not urgent.empty:
        m_txt = "　　".join([f"🚨 {r[C_NAME]}(剩{(r['D']-now).days}天)" for _,r in urgent.iterrows()])
        st.markdown(f'<div style="background:#ff4b4b;color:white;padding:10px;border-radius:5px;"><marquee scrollamount="6">{m_txt}</marquee></div>', unsafe_allow_html=True)

    # 5. 側邊選單
    st.sidebar.markdown("## 📂 系統導航")
    t_list = sorted(df[C_TYPE].unique().tolist())
    sel_t = st.sidebar.selectbox("1. 選擇類型", t_list)
    sub = df[df[C_TYPE] == sel_t].reset_index(drop=True)
    sel_n = st.sidebar.radio("2. 選擇許可證", sub[C_NAME].tolist())

    # 6. 主畫面基本資訊
    row = sub[sub[C_NAME] == sel_n].iloc[0]
    st.title(f"📄 {sel_n}")
    st.divider()
    raw_type = str(row[C_TYPE])

    # 7. 第三層：按鈕判定
    acts_list = []
    if "清除" in raw_type: acts_list = ["變更", "變更暨展延", "展延"]
    elif "清理" in raw_type: acts_list = ["變更", "展延", "異動"]
    elif "水污染" in raw_type: acts_list = ["事前變更", "事後變更", "展延"]
    else: acts_list = ["展延"]

    st.subheader("🛠️ 第三層：辦理項目選擇")
    btn_cols = st.columns(len(acts_list))
    for i, a_name in enumerate(acts_list):
        if btn_cols[i].button(a_name, key=f"btn_{sel_n}_{a_name}", use_container_width=True):
            st.session_state["cur_a"] = a_name
            st.session_state["last_p"] = sel_n

    # 8. 流程執行
    if st.session_state.get("last_p") == sel_n and "cur
