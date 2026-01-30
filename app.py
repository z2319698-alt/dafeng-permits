import streamlit as st
import pandas as pd
from datetime import datetime as dt
import urllib.parse

st.set_page_config(page_title="大豐管理系統", layout="wide")

URL = "https://docs.google.com/spreadsheets/d/1BA427GfGw41UWen083KSWxbdRwbe3a1SEF_H89MyBZE/export?format=xlsx"

@st.cache_data(ttl=5)
def load_all_data():
    all_sh = pd.read_excel(URL, sheet_name=None)
    main_df = None
    attach_df = next((df for n, df in all_sh.items() if "檢查表" in n or "附件" in n), None)
    if attach_df is not None:
        attach_df.iloc[:, 0] = attach_df.iloc[:, 0].ffill()
        attach_df.iloc[:, 1] = attach_df.iloc[:, 1].ffill()
        attach_df = attach_df.astype(str).applymap(lambda x: x.strip())
    for n, df in all_sh.items():
        df.columns = [str(c).strip() for c in df.columns]
        if "許可證名稱" in df.columns: main_df = df
    return main_df, attach_df

try:
    df, attach_db = load_all_data()
    C_NAME, C_DATE, C_TYPE = "許可證名稱", "到期日期", "許可證類型"
    df['D_OBJ'] = pd.to_datetime(df[C_DATE], errors='coerce')
    now = dt.now()

    # --- 跑馬燈警報 (死守不動) ---
    urgent = df[(df['D_OBJ'] <= now + pd.Timedelta(days=180)) & (df['D_OBJ'].notnull())]
    if not urgent.empty:
        m_txt = "　　".join([f"🚨 {r[C_NAME]}(剩{(r['D_OBJ']-now).days}天)" for _,r in urgent.iterrows()])
        st.markdown(f'<div style="background:#ff4b4b;color:white;padding:10px;border-radius:5px;"><marquee scrollamount="6">{m_txt}</marquee></div>', unsafe_allow_True=True)

    # 側邊選單
    st.sidebar.markdown("## 📂 系統導覽")
    t_list = sorted(df[C_TYPE].dropna().unique().tolist())
    sel_t = st.sidebar.selectbox("1. 選擇類型", t_list)
    sub = df[df[C_TYPE] == sel_t].reset_index(drop=True)
    sel_n = st.sidebar.radio("2. 選擇許可證", sub[C_NAME].tolist())

    st.title(f"📄 {sel_n}")
    st.divider()

    # --- 第三層按鈕 (B 欄) ---
    if attach_db is not None:
        type_rows = attach_db[attach_db.iloc[:, 0] == sel_t]
        acts_list = type_rows.iloc[:, 1].unique().tolist()
        acts_list = [a for a in acts_list if a.lower() != 'nan']

        if acts_list:
            st.subheader("🛠️ 第三層：辦理項目選擇")
            btn_cols = st.columns(len(acts_list))
            for i, a in enumerate(acts_list):
                if btn_cols[i].button(a, key=f"btn_{sel_n}_{a}", use_container_width=True):
                    # 【核心】點擊不同項目按鈕時，立刻清空之前的勾選狀態
                    st.session_state["cur_a"] = a
                    st.session_state["last_p"] = sel_n
                    # 清除所有第一步與第三步的 checkbox 狀態
                    keys_to_del = [k for k in st.session_state.keys() if "law_idx_" in k or "file_check_" in k]
                    for k in keys_to_del: del st.session_state[k]
                    st.rerun()

            if st.session_state.get("last_p") == sel_n and "cur_a" in st.session_state:
                curr_act = st.session_state["cur_a"]
                st.markdown(f"### 📍 目前選擇項目：**{curr_act}**")
                target_rows = attach_db[(attach_db.iloc[:, 0] == sel_t) & (attach_db.iloc[:, 1] == curr_act)]

                # --- 第一步：法規依據 (C 欄) ---
                with st.expander("⚖️ 第一步：法規依據條件確認", expanded=True):
                    selected_indices = []
                    for idx, row in target_rows.iterrows():
                        law_text = row.iloc[2]
                        if law_text.lower() != 'nan' and law_text != '':
                            # 勾選框，key 綁定該項目的索引
                            if st.checkbox(law_text, key=f"law_idx_{sel_n}_{curr_act}_{idx}"):
                                selected_indices.append(idx)

                # --- 第二步：人員登錄 ---
                with st.expander("👤 第二步：人員登錄", expanded=True):
                    u_name = st.text_input("辦理人姓名", key=f"un_{sel_n}_{curr_act}")

                # --- 第三步：附件清單 (D-I 欄) ---
                if u_name:
                    st.markdown("---")
                    st.subheader("📂 第三步：應檢附附件清單")
                    
                    if selected_indices:
                        # 【核心連動】只拿勾選列的附件欄位 D-I (index 3-8)
                        selected_rows = attach_db.loc[selected_indices]
