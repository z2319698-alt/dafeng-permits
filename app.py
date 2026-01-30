import streamlit as st
import pandas as pd
from datetime import datetime as dt
import urllib.parse

# 1. 頁面配置
st.set_page_config(page_title="大豐管理系統", layout="wide")

# 2. 精確法規資料庫 (對齊各項辦理法規)
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

# 3. 讀取 Excel 數據
URL = "https://docs.google.com/spreadsheets/d/1BA427GfGw41UWen083KSWxbdRwbe3a1SEF_H89MyBZE/export?format=xlsx"

@st.cache_data(ttl=60)
def load_all_data():
    all_sh = pd.read_excel(URL, sheet_name=None)
    main_df = None
    # 搜尋含有「檢查表」或「附件」字眼的分頁 (對應 GID 846283148)
    attach_df = next((df for name, df in all_sh.items() if "檢查表" in name or "附件" in name), None)
    
    # 處理合併儲存格：向下填充，確保每一列都有對應的類型與項目標籤
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

    # 6. 主畫面
    row = sub[sub[C_NAME] == sel_n].iloc[0]
    st.title(f"📄 {sel_n}")
    st.divider()
    raw_type = str(row[C_TYPE])

    # 7. 第三層按鈕
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
    if st.session_state.get("last_p") == sel_n and "cur_a" in st.session_state:
        curr_act = st.session_state["cur_a"]
        st.markdown(f"### 📍 目前選擇：**{curr_act}**")
        
        with st.expander("⚖️ 第一步：法規依據條件確認", expanded=True):
            match_key = next((k for k in LAW_REQUIREMENTS if k in raw_type), None)
            conditions = LAW_REQUIREMENTS[match_key].get(curr_act, ["參考各縣市審查自主檢查表"]) if match_key else ["參考規範"]
            selected_laws = [c for c in conditions if st.checkbox(c, key=f"law_{sel_n}_{curr_act}_{c}")]
        
        with st.expander("👤 第二步：人員登錄", expanded=True):
            c1, c2 = st.columns(2)
            u_name = c1.text_input("辦理人姓名", key=f"user_name_{sel_n}")
            u_date = c2.date_input("辦理日期", value=now, key=f"user_date_{sel_n}")
            
            if u_name:
                st.markdown("---")
                st.subheader("📂 第三步：應檢附附件清單")
                
                final_items = []
                if attach_db is not None:
                    # 使用 iterrows 逐列檢查，搭配向下填充過的數據
                    for _, r in attach_db.iterrows():
                        # 類型(第一欄)與項目(第二欄)模糊匹配
                        t_match = str(sel_t)[:2] in str(r.iloc[0])
                        a_match = str(curr_act)[:2] in str(r.iloc[1])
                        if t_match and a_match and pd.notnull(r.iloc[2]):
                            final_items.append(str(r.iloc[2]))
                
                final_items = list(dict.fromkeys(final_items)) # 移除重複
                
                if final_items:
                    checked_files = []
                    for item in final_items:
                        col_a, col_b = st.columns([0.5, 0.5])
                        if col_a.checkbox(item, key=f"chk_{sel_n}_{curr_act}_{item}"):
                            checked_files.append(item)
                        col_b.file_uploader("上傳", key=f"f_{sel_n}_{curr_act}_{item}", label_visibility="collapsed")
                    
                    st.divider()
                    if st.button("🚀 提出申請並發信", use_container_width=True):
                        mail_body = f"申請單位：{sel_n}\n項目：{curr_act}\n辦理人：{u_name}\n日期：{u_date}\n已選附件：{', '.join(checked_files)}"
                        sub_enc = urllib.parse.quote(f"許可辦理申請：{sel_n}")
                        body_enc = urllib.parse.quote(mail_body)
                        mailto_url = f"mailto:andy.chen@df-recycle.com?subject={sub_enc}&body={body_enc}"
                        st.markdown(f'<a href="{mailto_url}" style="background-color:#4CAF50; color:white; padding:12px; text-decoration:none; border-radius:5px; display:block; text-align:center;">📧 按此啟動郵件系統發信給 Andy</a>', unsafe_allow_html=True)
                else:
                    st.warning("⚠️ 查無附件清單，請檢查 Excel '自主檢查表' 分頁內容。")
            else:
                st.warning("⚠️ 請
