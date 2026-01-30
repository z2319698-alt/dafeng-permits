import streamlit as st
import pandas as pd
from datetime import datetime as dt

st.set_page_config(page_title="大豐管理系統", layout="wide")

URL = "https://docs.google.com/spreadsheets/d/1BA427GfGw41UWen083KSWxbdRwbe3a1SEF_H89MyBZE/export?format=xlsx"

def load_data_fresh():
    all_sh = pd.read_excel(URL, sheet_name=None)
    main_df = None
    # 鎖定附件工作表
    attach_df = next((df for n, df in all_sh.items() if any(k in n for k in ["檢查表", "附件"])), None)
    if attach_df is not None:
        attach_df.columns = [str(c).strip() for c in attach_df.columns]
        attach_df.iloc[:, 0] = attach_df.iloc[:, 0].ffill()
        attach_df.iloc[:, 1] = attach_df.iloc[:, 1].ffill()
        attach_df = attach_df.astype(str).applymap(lambda x: x.strip())
    
    for n, df in all_sh.items():
        if "許可證名稱" in df.columns: main_df = df
    return main_df, attach_df

try:
    df, attach_db = load_data_fresh()
    C_NAME, C_DATE, C_TYPE = "許可證名稱", "到期日期", "許可證類型"
    df['D_OBJ'] = pd.to_datetime(df[C_DATE], errors='coerce')
    now = dt.now()

    # --- 跑馬燈 ---
    urgent = df[(df['D_OBJ'] <= now + pd.Timedelta(days=180)) & (df['D_OBJ'].notnull())]
    if not urgent.empty:
        m_txt = "　　".join([f"🚨 {r[C_NAME]}(剩{(r['D_OBJ']-now).days}天)" for _,r in urgent.iterrows()])
        st.markdown(f'<div style="background:#ff4b4b;color:white;padding:10px;border-radius:5px;"><marquee scrollamount="6">{m_txt}</marquee></div>', unsafe_allow_html=True)

    # 1. 側邊選單
    sel_t = st.sidebar.selectbox("選擇類型", sorted(df[C_TYPE].dropna().unique().tolist()))
    sub = df[df[C_TYPE] == sel_t].reset_index(drop=True)
    sel_n = st.sidebar.radio("選擇許可證", sub[C_NAME].tolist())

    st.title(f"📄 {sel_n}")
    st.divider()

    if attach_db is not None:
        # 篩選出該類型 A 下的所有項目 B
        target_db = attach_db[attach_db.iloc[:, 0] == sel_t]
        acts = target_db.iloc[:, 1].unique().tolist()
        acts = [a for a in acts if a.lower() != 'nan']

        if acts:
            st.subheader("🛠️ 項目選擇")
            cols = st.columns(len(acts))
            for i, a in enumerate(acts):
                if cols[i].button(a, key=f"B_BTN_{a}"):
                    # 徹底清空狀態，不讓舊附件殘留
                    for k in list(st.session_state.keys()):
                        if k.startswith("C_") or k.startswith("U_"): del st.session_state[k]
                    st.session_state["cur_act"] = a
                    st.rerun()

            if "cur_act" in st.session_state:
                curr_a = st.session_state["cur_act"]
                st.info(f"📍 目前項目：{curr_a}")
                
                # 取得「變更」項目下的所有行
                rows = target_db[target_db.iloc[:, 1] == curr_a]

                # --- 第一步：C 欄勾選 ---
                st.markdown("### ⚖️ 第一步：條件確認 (C 欄)")
                active_files = []
                for idx, row in rows.iterrows():
                    c_text = row.iloc[2]
                    if c_text.lower() != 'nan' and c_text != '':
                        # 每一行 C 欄都是獨立的開關
                        if st.checkbox(c_text, key=f"C_CHK_{sel_n}_{idx}"):
                            # 只有勾了這行，才把這行的 D-I 欄抓進來
                            row_files = [str(row.iloc[i]).strip() for i in range(3, 9) if str(row.iloc[i]).lower() != 'nan' and str(row.iloc[i]) != '']
                            active_files.extend(row_files)

                # --- 第二步：姓名 ---
                u_name = st.text_input("👤 第二步：人員登錄 (輸入姓名後顯示附件)", key=f"U_NAME_{sel_n}_{curr_a}")

                # --- 第三步：附件 (強制隔離邏輯) ---
                if u_name and active_files:
                    st.divider()
                    st.markdown("### 📂 第三步：應檢附附件清單")
                    
                    # 徹底去重
                    final_set = list(dict.fromkeys(active_files))

                    for f_name in final_set:
                        c1, c2 = st.columns([0.6, 0.4])
                        c1.markdown(f"✅ **{f_name}**")
                        # Key 包含當前許可證名稱，確保切換時組件會強制更新
                        c2.file_uploader("上傳", key=f"UP_{sel_n}_{curr_a}_{f_name}", label_visibility="collapsed")
                    
                    if st.button("🚀 彙整送出", use_container_width=True):
                        st.balloons()
                elif u_name:
                    st.warning("👈 請先勾選「第一步」的條件，系統才會顯示該條件對應的附件。")

except Exception as e:
    st.error(f"系統崩潰: {e}")
