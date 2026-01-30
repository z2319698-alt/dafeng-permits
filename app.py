import streamlit as st
import pandas as pd
from datetime import datetime as dt

# 1. 配置
st.set_page_config(page_title="大豐管理系統", layout="wide")

# 2. 法規依據資料庫 (這部分未來你也可以移到 Excel)
LAW_DB = {
    "變更": [
        "依據廢清法第 41 條：涉及主體、類別、產能擴增達 10% 以上。",
        "依據水污法第 14 條：製程、水質、水量有重大異動需事前變更。",
        "依據管理辦法：涉及清除設備或貯存場地點變更。"
    ],
    "異動": [
        "依據管理辦法：僅涉及基本資料（如負責人、電話、地址）之更動。",
        "法規條件：不涉及實質處理製程或清除類別之改變。",
        "行政報備：僅需於 15 日內完成公文報備者。"
    ],
    "展延": [
        "法規提醒：應於期滿前 6-8 個月提出申請。",
        "法規提醒：若逾期未申請，原許可證失其效力。"
    ]
}

# 3. 附件資料庫 (按鈕分類)
DB_CONFIG = {
    "水污染": {"事前變更": [], "事後變更": [], "展延": []},
    "清除": {"變更": [], "變更暨展延": [], "展延": []},
    "清理": {"變更": [], "展延": [], "異動": []}
}

URL = "https://docs.google.com/spreadsheets/d/1BA427GfGw41UWen083KSWxbdRwbe3a1SEF_H89MyBZE/export?format=xlsx"

@st.cache_data(ttl=60)
def load_data():
    all_sh = pd.read_excel(URL, sheet_name=None)
    # 預留：未來讀取「附件清單」分頁
    # attach_df = all_sh.get("附件清單") 
    for n, df in all_sh.items():
        df.columns = [str(c).strip() for c in df.columns]
        if "許可證名稱" in df.columns: return df
    return list(all_sh.values())[0]

try:
    df = load_data()
    C_NAME, C_DATE, C_TYPE = "許可證名稱", "到期日期", "許可證類型"
    df['D'] = pd.to_datetime(df[C_DATE], errors='coerce')
    df['T'] = df[C_TYPE].fillna("一般管理")
    now = dt.now()

    # 3. 跑馬燈
    urgent = df[(df['D'] <= now + pd.Timedelta(days=180)) & (df['D'].notnull())]
    if not urgent.empty:
        m_items = [f"🚨 {r[C_NAME]}(剩{(r['D']-now).days}天)" for _,r in urgent.iterrows()]
        st.markdown(f'<div style="background:#ff4b4b;color:white;padding:10px;border-radius:5px;"><marquee scrollamount="6">{"　　".join(m_items)}</marquee></div>', unsafe_allow_html=True)

    # 4. 側邊選單
    st.sidebar.markdown("## 📂 系統導航")
    t_list = sorted(df['T'].unique().tolist())
    sel_t = st.sidebar.selectbox("1. 選擇類型", t_list)
    sub = df[df['T'] == sel_t].reset_index(drop=True)
    if sub.empty: st.stop()
    sel_n = st.sidebar.radio("2. 選擇許可證", sub[C_NAME].tolist())

    # 5. 主畫面 - 基本資訊
    row = sub[sub[C_NAME] == sel_n].iloc[0]
    st.title(f"📄 {sel_n}")
    
    # 6. 第三層：辦理項目選擇
    st.divider()
    st.subheader("🛠️ 第三層：辦理項目選擇")
    
    raw_type = str(row[C_TYPE])
    if "水污染" in raw_type: acts = DB_CONFIG["水污染"]
    elif "清除" in raw_type: acts = DB_CONFIG["清除"]
    elif "清理" in raw_type: acts = DB_CONFIG["清理"]
    else: acts = {"展延": []}

    btn_cols = st.columns(len(acts))
    for i, a_name in enumerate(acts.keys()):
        if btn_cols[i].button(a_name, key=f"b_{sel_n}_{a_name}", use_container_width=True):
            st.session_state["cur_a"] = a_name
            st.session_state["step"] = 1 # 進入法規確認步
            st.session_state["last_p"] = sel_n

    # 7. 法規依據與人員填寫 (這就是你要求的新頁面效果)
    if st.session_state.get("last_p") == sel_n and "cur_a" in st.session_state:
        curr_act = st.session_state["cur_a"]
        
        st.markdown(f"### 📍 辦理項目：{curr_act}")
        
        # --- 法規提醒層 ---
        with st.expander("⚖️ 第一步：法規依據條件確認 (請點選符合之條件)", expanded=True):
            law_key = "變更" if "變更" in curr_act else ("異動" if "異動" in curr_act else "展延")
            for law in LAW_DB.get(law_key, ["查無法規依據"]):
                st.checkbox(law, key=f"law_{sel_n}_{law}")
        
        # --- 人員登錄層 ---
        with st.expander("👤 第二步：人員登錄", expanded=True):
            c1, c2 = st.columns(2)
            u_name = c1.text_input("辦理人姓名", key=f"name_{sel_n}")
            u_date = c2.date_input("辦理日期", value=now, key=f"date_{sel_n}")
            
            if u_name:
                st.success(f"確認人員：{u_name}，日期：{u_date}")
                
                # --- 附件上傳層 (人員填完名字才跳出) ---
                st.markdown("---")
                st.subheader(f"📂 第三步：應檢附附件清單 ({curr_act})")
                st.info("請依據各縣市要求上傳對應文件")
                
                # 這裡預留對接你的「附件分頁」
                temp_items = ["申請書正本", "差異對照表", "相關證明文件"] 
                for item in temp_items:
                    col_a, col_b = st.columns([0.4, 0.6])
                    col_a.checkbox(item, key=f"ck_{sel_n}_{item}")
                    col_b.file_uploader("上傳", key=f"up_{sel_n}_{item}", label_visibility="collapsed")
            else:
                st.warning("⚠️ 請填寫辦理人姓名以解鎖附件清單。")

except Exception as e:
    st.error(f"系統錯誤: {e}")
