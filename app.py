import streamlit as st
import pandas as pd
from datetime import datetime as dt
import urllib.parse

st.set_page_config(page_title="大豐管理系統", layout="wide")

URL = "https://docs.google.com/spreadsheets/d/1BA427GfGw41UWen083KSWxbdRwbe3a1SEF_H89MyBZE/export?format=xlsx"

# 徹底砍掉緩存，保證每次重新計算
def load_data_final():
    all_sh = pd.read_excel(URL, sheet_name=None)
    main_df = None
    attach_df = next((df for n, df in all_sh.items() if "檢查表" in n or "附件" in n), None)
    if attach_df is not None:
        # 重要：補齊合併儲存格 (類別、項目)
        attach_df.iloc[:, 0] = attach_df.iloc[:, 0].ffill()
        attach_df.iloc[:, 1] = attach_df.iloc[:, 1].ffill()
        # 轉字串並修剪空白
        attach_df = attach_df.astype(str).applymap(lambda x: x.strip())
    for n, df in all_sh.items():
        if "許可證名稱" in df.columns: main_df = df
    return main_df, attach_df

try:
    df, attach_db = load_data_final()
    C_NAME, C_DATE, C_TYPE = "許可證名稱", "到期日期", "許可證類型"
    df['D_OBJ'] = pd.to_datetime(df[C_DATE], errors='coerce')
    now = dt.now()

    # --- 跑馬燈 (死守不動) ---
    urgent = df[(df['D_OBJ'] <= now + pd.Timedelta(days=180)) & (df['D_OBJ'].notnull())]
    if not urgent.empty:
        m_txt = "　　".join([f"🚨 {r[C_NAME]}(剩{(r['D_OBJ']-now).days}天)" for _,r in urgent.iterrows()])
        st.markdown(f'<div style="background:#ff4b4b;color:white;padding:10px;border-radius:5px;"><marquee scrollamount="6">{m_txt}</marquee></div>', unsafe_allow_html=True)

    # 側邊選單
    sel_t = st.sidebar.selectbox("1. 選擇類型", sorted(df[C_TYPE].dropna().unique().tolist()))
    sub = df[df[C_TYPE] == sel_t].reset_index(drop=True)
    sel_n = st.sidebar.radio("2. 選擇許可證", sub[C_NAME].tolist())

    st.title(f"📄 {sel_n}")
    st.divider()

    if attach_db is not None:
        # --- B 欄按鈕項目 ---
        # 僅抓取符合類別的項目
        type_mask = (attach_db.iloc[:, 0] == sel_t)
        acts = attach_db[type_mask].iloc[:, 1].unique().tolist()
        acts = [a for a in acts if a.lower() != 'nan']

        if acts:
            st.subheader("🛠️ 第三層：辦理項目選擇 (B 欄)")
            cols = st.columns(len(acts))
            for i, a in enumerate(acts):
                if cols[i].button(a, key=f"BTN_{a}"):
                    # 點擊按鈕時徹底清空先前的勾選狀態
                    st.session_state["cur_act"] = a
                    st.session_state["sel_indices"] = []
                    st.rerun()

            if "cur_act" in st.session_state:
                curr_a = st.session_state["cur_act"]
                st.info(f"📍 目前選擇項目：{curr_a}")
                
                # 篩選出該項目的所有「原始列」
                target_rows = attach_db[(attach_db.iloc[:, 0] == sel_t) & (attach_db.iloc[:, 1] == curr_a)]

                # --- 第一步：C 欄勾選 ---
                with st.expander("⚖️ 第一步：法規依據條件確認 (C 欄)", expanded=True):
                    # 用一個臨時清單紀錄勾選的「列索引」
                    current_selected = []
                    for idx, row in target_rows.iterrows():
                        c_val = row.iloc[2]
                        if c_val.lower() != 'nan' and c_val != '':
                            # 使用 row index 作為 key 的一部分，保證唯一
                            if st.checkbox(c_val, key=f"CHK_C_{idx}"):
                                current_selected.append(idx)
                    # 更新至 session_state
                    st.session_state["sel_indices"] = current_selected

                # --- 第二步：人員登錄 ---
                with st.expander("👤 第二步：人員登錄", expanded=True):
                    u_name = st.text_input("辦理人姓名", key="USER_INPUT")

                # --- 第三步：D-I 欄附件 (嚴格連動) ---
                if u_name and st.session_state.get("sel_indices"):
                    st.markdown("---")
                    st.subheader("📂 第三步：應檢附附件清單 (D-I 欄)")
                    
                    # 只抓取勾選的那幾列
                    matched_rows = attach_db.loc[st.session_state["sel_indices"]]
                    
                    # 抓取 D(3) 到 I(8) 欄位
                    all_files = []
                    for _, r in matched_rows.iterrows():
                        row_files = r.iloc[3:9].tolist()
                        all_files.extend([f for f in row_files if f.lower() != 'nan' and f != ''])
                    
                    # 附件去重
                    final_files = list(dict.fromkeys(all_files))

                    if final_files:
                        for f_name in final_files:
                            c1, c2 = st.columns([0.6, 0.4])
                            c1.checkbox(f_name, key=f"FILE_{f_name}")
                            c2.file_uploader("上傳", key=f"UP_{f_name}", label_visibility="collapsed")
                        
                        if st.button("🚀 提出申請並發信", use_container_width=True):
                            st.success("資料已彙整成功，請啟動郵件發送。")
                    else:
                        st.warning("⚠️ 此條件在 Excel 中未設定任何附件。")
                elif u_name:
                    st.warning("👈 請先在「第一步」勾選條件，系統才會顯示對應附件。")

except Exception as e:
    st.error(f"系統崩潰，請通知工程師: {e}")
