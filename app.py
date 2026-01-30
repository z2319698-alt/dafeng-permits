import streamlit as st
import pandas as pd
from datetime import datetime as dt
import urllib.parse

# 1. 頁面配置
st.set_page_config(page_title="大豐管理系統", layout="wide")

# 2. 數據讀取 (移除緩存，確保每次都是抓最新的 Excel 與邏輯)
URL = "https://docs.google.com/spreadsheets/d/1BA427GfGw41UWen083KSWxbdRwbe3a1SEF_H89MyBZE/export?format=xlsx"

def load_data_no_cache():
    all_sh = pd.read_excel(URL, sheet_name=None)
    main_df = None
    attach_df = next((df for n, df in all_sh.items() if "檢查表" in n or "附件" in n), None)
    if attach_df is not None:
        attach_df.iloc[:, 0] = attach_df.iloc[:, 0].ffill()
        attach_df.iloc[:, 1] = attach_df.iloc[:, 1].ffill()
        attach_df = attach_df.astype(str).applymap(lambda x: x.strip())
    for n, df in all_sh.items():
        if "許可證名稱" in df.columns: main_df = df
    return main_df, attach_df

try:
    df, attach_db = load_data_no_cache()
    C_NAME, C_DATE, C_TYPE = "許可證名稱", "到期日期", "許可證類型"
    df['D_OBJ'] = pd.to_datetime(df[C_DATE], errors='coerce')
    now = dt.now()

    # --- 跑馬燈警報 ---
    urgent = df[(df['D_OBJ'] <= now + pd.Timedelta(days=180)) & (df['D_OBJ'].notnull())]
    if not urgent.empty:
        m_txt = "　　".join([f"🚨 {r[C_NAME]}(剩{(r['D_OBJ']-now).days}天)" for _,r in urgent.iterrows()])
        st.markdown(f'<div style="background:#ff4b4b;color:white;padding:10px;border-radius:5px;"><marquee scrollamount="6">{m_txt}</marquee></div>', unsafe_allow_html=True)

    # 3. 側邊選單
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
                    # 換按鈕就徹底重置 session
                    st.session_state["cur_a"] = a
                    st.session_state["last_p"] = sel_n
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
                            # 使用絕對唯一的索引作為 key，防止狀態殘留
                            if st.checkbox(law_text, key=f"chk_v2_{idx}_{sel_n}"):
                                selected_indices.append(idx)

                # --- 第二步：人員登錄 ---
                with st.expander("👤 第二步：人員登錄", expanded=True):
                    u_name = st.text_input("辦理人姓名", key=f"user_{sel_n}_{curr_act}")

                # --- 第三步：附件清單 (D-I 欄) ---
                if u_name:
                    st.markdown("---")
                    st.subheader("📂 第三步：應檢附附件清單")
                    
                    if selected_indices:
                        # 【核心連動邏輯】
                        # 根據第一步勾選的列索引(idx)，只去那些列裡面找 D-I 欄
                        matched_rows = attach_db.loc[selected_indices]
                        files_raw = matched_rows.iloc[:, 3:9].values.flatten()
                        # 精準過濾：去重、去空、去 nan
                        final_files = list(dict.fromkeys([str(f).strip() for f in files_raw if pd.notnull(f) and str(f).lower() != 'nan' and str(f) != '']))
                        
                        if final_files:
                            for f_idx, f_name in enumerate(final_files):
                                ca, cb = st.columns([0.6, 0.4])
                                # checkbox 僅作確認，不影響連動
                                ca.checkbox(f_name, key=f"f_final_{sel_n}_{f_idx}")
                                cb.file_uploader("上傳", key=f"up_final_{sel_n}_{f_idx}", label_visibility="collapsed")
                            
                            st.divider()
                            if st.button("🚀 提出申請並發信", use_container_width=True):
                                st.success("申請資料已彙整成功。")
                    else:
                        st.info("💡 請在「第一步」勾選您要辦理的具體條件。")
    else:
        st.error("資料庫讀取異常")

except Exception as e:
    st.error(f"系統錯誤: {e}")
