import streamlit as st
import pandas as pd
from datetime import datetime as dt
import urllib.parse

# 1. 頁面配置
st.set_page_config(page_title="大豐管理系統", layout="wide")

# 2. 讀取數據
URL = "https://docs.google.com/spreadsheets/d/1BA427GfGw41UWen083KSWxbdRwbe3a1SEF_H89MyBZE/export?format=xlsx"

@st.cache_data(ttl=30) # 縮短緩存時間，讓 Excel 更新更快同步
def load_all_data():
    all_sh = pd.read_excel(URL, sheet_name=None)
    main_df = None
    # 鎖定「各縣市審查管理辦法自主檢查表」分頁
    attach_df = next((df for n, df in all_sh.items() if "檢查表" in n or "附件" in n), None)
    
    if attach_df is not None:
        # 處理合併儲存格：補齊類型與項目，確保每一行附件都能對應到正確分類
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

    # 3. 跑馬燈
    urgent = df[(df['D'] <= now + pd.Timedelta(days=180)) & (df['D'].notnull())]
    if not urgent.empty:
        m_txt = "　　".join([f"🚨 {r[C_NAME]}(剩{(r['D']-now).days}天)" for _,r in urgent.iterrows()])
        st.markdown(f'<div style="background:#ff4b4b;color:white;padding:10px;border-radius:5px;"><marquee scrollamount="6">{m_txt}</marquee></div>', unsafe_allow_html=True)

    # 4. 側邊選單
    st.sidebar.markdown("## 📂 系統導航")
    t_list = sorted(df[C_TYPE].unique().tolist())
    sel_t = st.sidebar.selectbox("1. 選擇類型", t_list)
    sub = df[df[C_TYPE] == sel_t].reset_index(drop=True)
    sel_n = st.sidebar.radio("2. 選擇許可證", sub[C_NAME].tolist())

    # 5. 主畫面資訊
    row = sub[sub[C_NAME] == sel_n].iloc[0]
    st.title(f"📄 {sel_n}")
    st.divider()
    raw_type = str(row[C_TYPE])

    # 6. 第三層按鈕 (動態從檢查表分頁抓取該類型有哪些項目)
    if attach_db is not None:
        # 找出該類型下所有的辦理項目 (例如變更、展延...)
        acts_list = attach_db[attach_db.iloc[:, 0].astype(str).str.contains(sel_t[:2], na=False)].iloc[:, 1].unique().tolist()
    else:
        acts_list = ["展延"]

    st.subheader("🛠️ 第三層：辦理項目選擇")
    cols = st.columns(len(acts_list))
    for i, a in enumerate(acts_list):
        if cols[i].button(a, key=f"btn_{sel_n}_{a}", use_container_width=True):
            st.session_state["cur_a"] = a
            st.session_state["last_p"] = sel_n

    # 7. 流程執行
    if st.session_state.get("last_p") == sel_n and "cur_a" in st.session_state:
        curr_act = st.session_state["cur_a"]
        st.markdown(f"### 📍 目前選擇：**{curr_act}**")
        
        # 篩選該項目對應的所有列
        mask = (attach_db.iloc[:, 0].astype(str).str.contains(sel_t[:2], na=False)) & \
               (attach_db.iloc[:, 1].astype(str).str.contains(curr_act[:2], na=False))
        target_rows = attach_db[mask]

        # 第一步：法規 (從 Excel 第 4 欄抓取)
        with st.expander("⚖️ 第一步：法規依據條件確認", expanded=True):
            laws_from_excel = target_rows.iloc[:, 3].dropna().unique().tolist()
            if not laws_from_excel:
                laws_from_excel = ["請參考縣市自主檢查表"]
            sel_laws = [c for c in laws_from_excel if st.checkbox(c, key=f"l_{sel_n}_{curr_act}_{c}")]
        
        # 第二步：人員登錄
        with st.expander("👤 第二步：人員登錄", expanded=True):
            c1, c2 = st.columns(2)
            u_name = c1.text_input("辦理人姓名", key=f"un_{sel_n}")
            u_date = c2.date_input("辦理日期", value=now, key=f"ud_{sel_n}")
            
            if u_name:
                # 第三步：附件 (從 Excel 第 3 欄抓取)
                st.markdown("---")
                st.subheader("📂 第三步：應檢附附件清單")
                
                attach_from_excel = target_rows.iloc[:, 2].dropna().unique().tolist()
                
                if attach_from_excel:
                    checked_f = []
                    for item in attach_from_excel:
                        ca, cb = st.columns([0.5, 0.5])
                        if ca.checkbox(item, key=f"ck_{sel_n}_{curr_act}_{item}"):
                            checked_f.append(item)
                        cb.file_uploader("上傳", key=f"f_{sel_n}_{curr_act}_{item}", label_visibility="collapsed")
                    
                    # 第四步：發信
                    st.divider()
                    if st.button("🚀 提出申請並發信", use_container_width=True):
                        info = f"單位：{sel_n}\n項目：{curr_act}\n辦理人：{u_name}\n條件：{', '.join(sel_laws)}\n附件：{', '.join(checked_f)}"
                        sub_e = urllib.parse.quote(f"許可辦理申請：{sel_n}")
                        body_e = urllib.parse.quote(info)
                        st.markdown(f'<a href="mailto:andy.chen@df-recycle.com?subject={sub_e}&body={body_e}" style="background-color:#4CAF50;color:white;padding:12px;text-decoration:none;border-radius:5px;display:block;text-align:center;">📧 啟動郵件發送申請</a>', unsafe_allow_html=True)
                else:
                    st.warning("⚠️ 查無附件清單，請確認 Excel 第三欄內容。")
            else:
                st.info("請輸入姓名以顯示附件清單。")

except Exception as e:
    st.error(f"系統錯誤: {e}")
