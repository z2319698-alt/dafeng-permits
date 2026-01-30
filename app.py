import streamlit as st
import pandas as pd
from datetime import datetime as dt

st.set_page_config(page_title="大豐管理系統", layout="wide")

# 1. 精確法規資料庫 - 依照「類別」與「項目」拆分
# 這些條件你可以依據實際檢查表修改
LAW_REQUIREMENTS = {
    "廢棄物清理計畫書": {
        "變更": [
            "涉及主體、類別、產能擴增達 10% 以上 (廢清法第 31 條)",
            "產出廢棄物項目增加或數量異動逾 10%",
            "製程改變導致廢棄物特性變更"
        ],
        "異動": [
            "僅基本資料更動 (負責人、聯絡地址等)",
            "不涉及製程改變之微幅異動"
        ]
    },
    "廢棄物清除許可證": {
        "變更": [
            "清除車輛增加、減少或規格異動",
            "清除廢棄物種類增加",
            "貯存場、轉運站地點或容量變更"
        ]
    },
    "水污染防治措施": {
        "事前變更": [
            "廢(污)水處理技術或程序改變 (水污法第 14 條)",
            "每日最大廢(污)水產生量增加 10% 以上",
            "放流口位置變更"
        ]
    }
}

URL = "https://docs.google.com/spreadsheets/d/1BA427GfGw41UWen083KSWxbdRwbe3a1SEF_H89MyBZE/export?format=xlsx"

@st.cache_data(ttl=60)
def load_data():
    all_sh = pd.read_excel(URL, sheet_name=None)
    main_df = None
    attach_df = all_sh.get("附件資料庫") # 預留讀取你的新分頁
    
    for n, df in all_sh.items():
        df.columns = [str(c).strip() for c in df.columns]
        if "許可證名稱" in df.columns:
            main_df = df
            break
    return main_df, attach_df

try:
    df, attach_db = load_data()
    C_NAME, C_DATE, C_TYPE = "許可證名稱", "到期日期", "許可證類型"
    df['D'] = pd.to_datetime(df[C_DATE], errors='coerce')
    now = dt.now()

    # 跑馬燈
    urgent = df[(df['D'] <= now + pd.Timedelta(days=180)) & (df['D'].notnull())]
    if not urgent.empty:
        m_txt = "　　".join([f"🚨 {r[C_NAME]}(剩{(r['D']-now).days}天)" for _,r in urgent.iterrows()])
        st.markdown(f'<div style="background:#ff4b4b;color:white;padding:10px;border-radius:5px;"><marquee scrollamount="6">{m_txt}</marquee></div>', unsafe_allow_html=True)

    # 側邊選單
    st.sidebar.markdown("## 📂 系統導航")
    t_list = sorted(df[C_TYPE].unique().tolist())
    sel_t = st.sidebar.selectbox("1. 選擇類型", t_list)
    sub = df[df[C_TYPE] == sel_t].reset_index(drop=True)
    sel_n = st.sidebar.radio("2. 選擇許可證", sub[C_NAME].tolist())

    # 主畫面
    row = sub[sub[C_NAME] == sel_n].iloc[0]
    st.title(f"📄 {sel_n}")
    
    # 第三層：辦理項目
    st.divider()
    raw_type = str(row[C_TYPE])
    
    # 動態決定按鈕
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

    # 新頁面流程
    if st.session_state.get("last_p") == sel_n:
        curr_act = st.session_state.get("cur_a")
        st.markdown(f"### 📍 辦理項目：{curr_act}")
        
        # 1. 依據類型顯示法規 (精確對應)
        with st.expander("⚖️ 第一步：法規依據條件確認", expanded=True):
            # 模糊匹配類型關鍵字
            match_key = next((k for k in LAW_REQUIREMENTS if k in raw_type), None)
            conditions = []
            if match_key:
                conditions = LAW_REQUIREMENTS[match_key].get(curr_act, ["請參考各縣市主管機關規定"])
            
            for cond in conditions:
                st.checkbox(cond, key=f"law_{sel_n}_{curr_act}_{cond}")
        
        # 2. 人員登錄
        with st.expander("👤 第二步：人員登錄", expanded=True):
            c1, c2 = st.columns(2)
            u_name = c1.text_input("辦理人姓名", key=f"name_{sel_n}")
            c2.date_input("辦理日期", value=now, key=f"date_{sel_n}")
            
            if u_name:
                # 3. 顯示附件 (從 Excel 讀取或保底)
                st.markdown("---")
                st.subheader(f"📂 第三步：應檢附附件清單")
                
                final_items = []
                if attach_db is not None:
                    # 從「附件資料庫」分頁過濾
                    mask = (attach_db["許可證類型"] == sel_t) & (attach_db["辦理項目"] == curr_act)
                    final_items = attach_db[mask]["附件名稱"].tolist()
                
                if not final_items:
                    final_items = ["申請書正本", "各縣市要求證明文件"] # 保底顯示
                
                for item in final_items:
                    col_a, col_b = st.columns([0.4, 0.6])
                    col_a.checkbox(item, key=f"ck_{sel_n}_{item}")
                    col_b.file_uploader("上傳", key=f"up_{sel_n}_{item}", label_visibility="collapsed")
            else:
                st.warning("請填寫姓名以進入附件清單。")

except Exception as e:
    st.error(f"錯誤: {e}")
