import streamlit as st
import pandas as pd
from datetime import datetime as dt
import urllib.parse

# 1. 頁面配置
st.set_page_config(page_title="大豐管理系統", layout="wide")

# 2. 數據讀取 (移除緩存，確保每次都重新計算邏輯)
URL = "https://docs.google.com/spreadsheets/d/1BA427GfGw41UWen083KSWxbdRwbe3a1SEF_H89MyBZE/export?format=xlsx"

def load_data_fresh():
    all_sh = pd.read_excel(URL, sheet_name=None)
    main_df = None
    attach_df = next((df for n, df in all_sh.items() if "檢查表" in n or "附件" in n), None)
    if attach_df is not None:
        # 處理合併儲存格
        attach_df.iloc[:, 0] = attach_df.iloc[:, 0].ffill()
        attach_df.iloc[:, 1] = attach_df.iloc[:, 1].ffill()
        # 轉字串、去空格
        attach_df = attach_df.astype(str).applymap(lambda x: x.strip())
    for n, df in all_sh.items():
        if "許可證名稱" in df.columns: main_df = df
    return main_df, attach_df

try:
    df, attach_db = load_data_fresh()
    C_NAME, C_DATE, C_TYPE = "許可證名稱", "到期日期", "許可證類型"
    df['D_OBJ'] = pd.to_datetime(df[C_DATE], errors='coerce')
    now = dt.now()

    # --- 跑馬燈警報 (恢復原始設定) ---
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
                    st.session_state["cur_a"] = a
                    st.session_state["last_p"] = sel_n
                    # 清除舊的勾選狀態，避免跨項目連動
                    for k in list(st.session_state.keys()):
                        if k.startswith("L_") or k.startswith("F_"): del st.session_state[k]
                    st.rerun()

            if st.session_state.get("last_p") == sel_n and "cur_a" in st.session_state:
                curr_act = st.session_state["cur_a"]
                st.markdown(f"### 📍 目前選擇項目：**{curr_act}**")
                
                # 取得該項目下的所有原始資料列
                target_rows = attach_db[(attach_db.iloc[:, 0] == sel_t) & (attach_db.iloc[:, 1] == curr_act)]

                # --- 第一步：法規依據 (C 欄) ---
                with st.expander("⚖️ 第一步：法規依據條件確認", expanded=True):
                    selected_rows_indices = []
                    for idx, row in target_rows.iterrows():
                        law_val = row.iloc[2] # C 欄
                        if law_val.lower() != 'nan' and law_val != '':
                            # 勾選框 key 必須包含項目的唯一標識
                            if st.checkbox(law_val, key=f"L_{idx}_{sel_n}"):
                                selected_rows_indices.append(idx)

                # --- 第二步：人員登錄 ---
                with st.expander("👤 第二步：人員登錄", expanded=True):
                    u_name = st.text_input("辦理人姓名", key=f"U_{sel_n}")

                # --- 第三步：附件清單 (D-I 欄) ---
                if u_name:
                    st.markdown("---")
                    st.subheader("📂 第三步：應檢附附件清單")
                    
                    if selected_rows_indices:
                        # 【核心連動邏輯】
                        # 從 attach_db 中只抓取那些被勾選的列 (indices)
                        final_data = attach_db.loc[selected_rows_indices]
                        
                        # 抓取 D 到 I 欄 (索引 3 到 8)
                        # 我們要把每一列對應的附件顯示出來
                        all_files_to_show = []
                        for _, r in final_data.iterrows():
                            # 每一列的附件收集起來
                            row_files = [str(r.iloc[i]).strip() for i in range(3, 9) if pd.notnull(r.iloc[i]) and str(r.iloc[i]).lower() != 'nan' and str(r.iloc[i]) != '']
                            all_files_to_show.extend(row_files)
                        
                        # 去除重複附件名稱
                        unique_files = list(dict.fromkeys(all_files_to_show))

                        if unique_files:
                            checked_f = []
                            for f_idx, f_name in enumerate(unique_files):
                                ca, cb = st.columns([0.6, 0.4])
                                if ca.checkbox(f_name, key=f"F_{f_idx}_{sel_n}"):
                                    checked_f.append(f_name)
                                cb.file_uploader("上傳", key=f"UP_{f_idx}_{sel_n}", label_visibility="collapsed")
                            
                            st.divider()
                            if st.button("🚀 提出申請並發信", use_container_width=True):
                                st.balloons()
                                st.success("申請資料已彙整，請啟動郵件系統。")
                    else:
                        st.info("💡 請在「第一步」勾選需要辦理的條件，此處才會顯示對應附件。")
    else:
        st.error("資料讀取失敗，請檢查網路。")

except Exception as e:
    st.error(f"系統錯誤: {e}")
