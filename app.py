import streamlit as st
import pandas as pd
from datetime import datetime as dt
import urllib.parse

# 1. 頁面配置
st.set_page_config(page_title="大豐管理系統", layout="wide")

# 2. 數據讀取
URL = "https://docs.google.com/spreadsheets/d/1BA427GfGw41UWen083KSWxbdRwbe3a1SEF_H89MyBZE/export?format=xlsx"

@st.cache_data(ttl=5)
def load_all_data():
    all_sh = pd.read_excel(URL, sheet_name=None)
    main_df = None
    attach_df = next((df for n, df in all_sh.items() if "檢查表" in n or "附件" in n), None)
    
    if attach_df is not None:
        # 處理合併儲存格
        attach_df.iloc[:, 0] = attach_df.iloc[:, 0].ffill()
        attach_df.iloc[:, 1] = attach_df.iloc[:, 1].ffill()
        attach_df = attach_df.applymap(lambda x: str(x).strip() if pd.notnull(x) else x)
            
    for n, df in all_sh.items():
        df.columns = [str(c).strip() for c in df.columns]
        if "許可證名稱" in df.columns:
            main_df = df
    return main_df, attach_df

try:
    df, attach_db = load_all_data()
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
    row_info = sub[sub[C_NAME] == sel_n].iloc[0]
    st.write(f"**目前效期：** {row_info[C_DATE]}")
    st.divider()

    # --- 第三層按鈕 (B欄) ---
    acts_list = []
    if attach_db is not None:
        acts_list = attach_db[attach_db.iloc[:, 0] == sel_t].iloc[:, 1].unique().tolist()
        acts_list = [a for a in acts_list if str(a).lower() != 'nan']

    if acts_list:
        st.subheader("🛠️ 第三層：辦理項目選擇")
        btn_cols = st.columns(len(acts_list))
        for i, a in enumerate(acts_list):
            if btn_cols[i].button(a, key=f"btn_{sel_n}_{a}", use_container_width=True):
                st.session_state["cur_a"] = a
                st.session_state["last_p"] = sel_n
        
        if st.session_state.get("last_p") == sel_n and "cur_a" in st.session_state:
            curr_act = st.session_state["cur_a"]
            st.markdown(f"### 📍 目前選擇項目：**{curr_act}**")
            target_rows = attach_db[(attach_db.iloc[:, 0] == sel_t) & (attach_db.iloc[:, 1] == curr_act)]

            # --- 第一步：法規依據 (C 欄) - 勾選功能 ---
            with st.expander("⚖️ 第一步：法規依據條件確認", expanded=True):
                laws_in_excel = target_rows.iloc[:, 2].unique().tolist()
                selected_conditions = []
                for l in laws_in_excel:
                    if str(l).lower() != 'nan' and str(l) != '':
                        if st.checkbox(str(l), key=f"law_{sel_n}_{curr_act}_{l}"):
                            selected_conditions.append(str(l))

            # --- 第二步：人員登錄 ---
            with st.expander("👤 第二步：人員登錄", expanded=True):
                u_name = st.text_input("辦理人姓名", key=f"un_{sel_n}")
                
            # --- 第三步：附件 (D 到 I 欄) - 精準連動 ---
            if u_name:
                st.markdown("---")
                st.subheader("📂 第三步：應檢附附件清單")
                
                if selected_conditions:
                    # 只抓取「第一步被勾選」的那幾列
                    matched_data = target_rows[target_rows.iloc[:, 2].isin(selected_conditions)]
                    # 攤平 D 到 I 欄 (index 3-8)
                    files_flat = matched_data.iloc[:, 3:9].values.flatten()
                    final_files = list(dict.fromkeys([str(f).strip() for f in files_flat if pd.notnull(f) and str(f).lower() != 'nan' and str(f) != '']))
                    
                    if final_files:
                        checked_f = []
                        for f in final_files:
                            ca, cb = st.columns([0.6, 0.4])
                            if ca.checkbox(f, key=f"f_{sel_n}_{curr_act}_{f}"):
                                checked_f.append(f)
                            cb.file_uploader("上傳", key=f"up_{sel_n}_{curr_act}_{f}", label_visibility="collapsed")
                        
                        st.divider()
                        if st.button("🚀 提出申請並發信", use_container_width=True):
                            info = f"單位：{sel_n}\n項目：{curr_act}\n人員：{u_name}\n勾選條件：{', '.join(selected_conditions)}\n附件：{', '.join(checked_f)}"
                            sub_e = urllib.parse.quote(f"許可辦理申請：{sel_n}")
                            body_e = urllib.parse.quote(info)
                            st.markdown(f'<a href="mailto:andy.chen@df-recycle.com?subject={sub_e}&body={body_e}" style="background-color:#4CAF50;color:white;padding:12px;text-decoration:none;border-radius:5px;display:block;text-align:center;">📧 啟動郵件系統</a>', unsafe_allow_html=True)
                else:
                    st.info("請在第一步勾選辦理條件，系統將自動產生對應附件。")
    else:
        # 應回收、水污染等原始狀態回歸
        st.info("目前此類型無須透過自主檢查表辦理。")

except Exception as e:
    st.error(f"系統錯誤: {e}")
