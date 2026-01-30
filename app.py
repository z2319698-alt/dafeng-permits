import streamlit as st
import pandas as pd
from datetime import datetime as dt
import urllib.parse

st.set_page_config(page_title="大豐管理系統", layout="wide")

# 1. 法規資料庫 (鎖定正確對應)
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

# 2. 資料讀取邏輯 (針對 GID 846283148 分頁)
URL = "https://docs.google.com/spreadsheets/d/1BA427GfGw41UWen083KSWxbdRwbe3a1SEF_H89MyBZE/export?format=xlsx"

@st.cache_data(ttl=60)
def load_all_data():
    all_sh = pd.read_excel(URL, sheet_name=None)
    main_df = None
    # 這裡我強制尋找含有「附件」兩個字的分頁，確保對接到 GID 846283148
    attach_df = next((df for name, df in all_sh.items() if "附件" in name), None)
    
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

    # 3. 跑馬燈
    urgent = df[(df['D'] <= now + pd.Timedelta(days=180)) & (df['D'].notnull())]
    if not urgent.empty:
        m_txt = "　　".join([f"🚨 {r[C_NAME]}(剩{(r['D']-now).days}天)" for _,r in urgent.iterrows()])
        st.markdown(f'<div style="background:#ff4b4b;color:white;padding:10px;border-radius:5px;"><marquee scrollamount="6">{m_txt}</marquee></div>', unsafe_allow_html=True)

    # 4. 側邊欄
    st.sidebar.markdown("## 📂 系統導航")
    t_list = sorted(df[C_TYPE].unique().tolist())
    sel_t = st.sidebar.selectbox("1. 選擇類型", t_list)
    sub = df[df[C_TYPE] == sel_t].reset_index(drop=True)
    sel_n = st.sidebar.radio("2. 選擇許可證", sub[C_NAME].tolist())

    # 5. 主畫面基本資訊
    row = sub[sub[C_NAME] == sel_n].iloc[0]
    st.title(f"📄 {sel_n}")
    st.divider()
    raw_type = str(row[C_TYPE])

    # 6. 按鈕判定
    acts = {}
    if "清除" in raw_type: acts = {"變更":None, "變更暨展延":None, "展延":None}
    elif "清理" in raw_type: acts = {"變更":None, "展延":None, "異動":None}
    elif "水污染" in raw_type: acts = {"事前變更":None, "事後變更":None, "展延":None}

    st.subheader("🛠️ 第三層：辦理項目選擇")
    btn_cols = st.columns(len(acts))
    for i, a_name in enumerate(acts.keys()):
        if btn_cols[i].button(a_name, key=f"b_{sel_n}_{a_name}", use_container_width=True):
            st.session_state["cur_a"] = a_name
            st.session_state["last_p"] = sel_n

    # 7. 流程：法規 -> 姓名 -> 附件清單
    if st.session_state.get("last_p") == sel_n:
        curr_act = st.session_state.get("cur_a")
        st.markdown(f"### 📍 目前選擇：{curr_act}")
        
        # 第一步：法規
        with st.expander("⚖️ 第一步：法規依據條件確認", expanded=True):
            match_key = next((k for k in LAW_REQUIREMENTS if k in raw_type), None)
            conditions = LAW_REQUIREMENTS[match_key].get(curr_act, ["請參考官方規定"]) if match_key else ["請參考官方規定"]
            selected_laws = [c for c in conditions if st.checkbox(c, key=f"law_{sel_n}_{curr_act}_{c}")]

        # 第二步：登錄
        with st.expander("👤 第二步：人員登錄", expanded=True):
            c1, c2 = st.columns(2)
            u_name = c1.text_input("辦理人姓名", key=f"name_{sel_n}")
            u_date = c2.date_input("辦理日期", value=now, key=f"date_{sel_n}")
            
            if u_name:
                # 第三步：附件 (強制完整讀取)
                st.markdown("---")
                st.subheader(f"📂 第三步：應檢附附件清單 (依據 Excel 分頁)")
                
                final_items = []
                if attach_db is not None:
                    # 強制欄位名稱對
