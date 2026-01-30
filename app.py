import streamlit as st
import pandas as pd
from datetime import datetime as dt
import urllib.parse

st.set_page_config(page_title="大豐管理系統", layout="wide")

URL = "https://docs.google.com/spreadsheets/d/1BA427GfGw41UWen083KSWxbdRwbe3a1SEF_H89MyBZE/export?format=xlsx"

@st.cache_data(ttl=10)
def load_all_data():
    all_sh = pd.read_excel(URL, sheet_name=None)
    main_df = None
    attach_df = next((df for n, df in all_sh.items() if "檢查表" in n or "附件" in n), None)
    
    if attach_df is not None:
        # 處理合併儲存格：確保每一行都有對應的類型與項目
        attach_df.iloc[:, 0] = attach_df.iloc[:, 0].ffill()
        attach_df.iloc[:, 1] = attach_df.iloc[:, 1].ffill()
        # 移除空格避免匹配失敗
        for i in range(4):
            attach_df.iloc[:, i] = attach_df.iloc[:, i].astype(str).str.strip()
            
    for n, df in all_sh.items():
        df.columns = [str(c).strip() for c in df.columns]
        if "許可證名稱" in df.columns:
            main_df = df
    return main_df, attach_df

try:
    df, attach_db = load_all_data()
    C_NAME, C_DATE, C_TYPE = "許可證名稱", "到期日期", "許可證類型"
    df['D'] = pd.to_datetime(df[C_DATE], errors='coerce')

    # 側邊選單
    st.sidebar.markdown("## 📂 系統導航")
    t_list = sorted(df[C_TYPE].unique().tolist())
    sel_t = st.sidebar.selectbox("1. 選擇類型", t_list)
    sub = df[df[C_TYPE] == sel_t].reset_index(drop=True)
    sel_n = st.sidebar.radio("2. 選擇許可證", sub[C_NAME].tolist())

    st.title(f"📄 {sel_n}")
    st.divider()

    # 第三層按鈕：嚴格對應 Excel B 欄
    acts_list = []
    if attach_db is not None:
        acts_list = attach_db[attach_db.iloc[:, 0] == sel_t].iloc[:, 1].unique().tolist()
        # 排除掉 'nan' 字串
        acts_list = [a for a in acts_list if a != 'nan']

    if acts_list:
        st.subheader("🛠️ 第三層：辦理項目選擇")
        cols = st.columns(len(acts_list))
        for i, a in enumerate(acts_list):
            if cols[i].button(a, key=f"btn_{sel_n}_{a}", use_container_width=True):
                st.session_state["cur_a"] = a
                st.session_state["last_p"] = sel_n

    if st.session_state.get("last_p") == sel_n and "cur_a" in st.session_state:
        curr_act = st.session_state["cur_a"]
        st.markdown(f"### 📍 目前選擇項目：**{curr_act}**")
        
        # 篩選 Excel 對應資料
        target_rows = attach_db[(attach_db.iloc[:, 0] == sel_t) & (attach_db.iloc[:, 1] == curr_act)]

        # --- 第一步：法規依據 (讀取 D 欄) ---
        with st.expander("⚖️ 第一步：法規依據條件確認", expanded=True):
            laws = target_rows.iloc[:, 3].replace('nan', pd.NA).dropna().unique().tolist()
            if laws:
                sel_laws = [l for l in laws if st.checkbox(l, key=f"l_{sel_n}_{curr_act}_{l}")]
            else:
                st.write("Excel 中此項目無辦理條件內容。")

        # --- 第二步：人員登錄 ---
        with st.expander("👤 第二步：人員登錄", expanded=True):
            u_name = st.text_input("辦理人姓名", key=f"un_{sel_n}")
            if u_name:
                # --- 第三步：應檢附附件清單 (讀取 C 欄) ---
                st.markdown("---")
                st.subheader("📂 第三步：應檢附附件清單")
                
                files = target_rows.iloc[:, 2].replace('nan', pd.NA).dropna().unique().tolist()
                if files:
                    checked_f = []
                    for f in files:
                        ca, cb = st.columns([0.5, 0.5])
                        if ca.checkbox(f, key=f"fck_{sel_n}_{curr_act}_{f}"):
                            checked_f.append(f)
                        cb.file_uploader("上傳", key=f"fup_{sel_n}_{curr_act}_{f}", label_visibility="collapsed")
                
                    st.divider()
                    if st.button("🚀 提出申請並發信", use_container_width=True):
                        info = f"單位：{sel_n}\n項目：{curr_act}\n人員：{u_name}\n附件：{', '.join(checked_f)}"
                        sub_e = urllib.parse.quote(f"許可辦理申請：{sel_n}")
                        body_e = urllib.parse.quote(info)
                        st.markdown(f'<a href="mailto:andy.chen@df-recycle.com?subject={sub_e}&body={body_e}" style="background-color:#4CAF50;color:white;padding:12px;text-decoration:none;border-radius:5px;display:block;text-align:center;">📧 啟動郵件發送</a>', unsafe_allow_html=True)
                else:
                    st.warning("Excel 中找不到此項目的附件內容 (C 欄)。")
            else:
                st.info("請輸入姓名以顯示第三步附件清單。")

except Exception as e:
    st.error(f"系統錯誤: {e}")
