import streamlit as st
import pandas as pd
from datetime import datetime as dt
import urllib.parse

st.set_page_config(page_title="大豐管理系統", layout="wide")

URL = "https://docs.google.com/spreadsheets/d/1BA427GfGw41UWen083KSWxbdRwbe3a1SEF_H89MyBZE/export?format=xlsx"

# 徹底放棄緩存，每一秒都重新讀取
def load_data_raw():
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
    df, attach_db = load_data_raw()
    C_NAME, C_DATE, C_TYPE = "許可證名稱", "到期日期", "許可證類型"
    df['D_OBJ'] = pd.to_datetime(df[C_DATE], errors='coerce')
    now = dt.now()

    # --- 跑馬燈 ---
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
        # 按鈕項目 (B 欄)
        acts = attach_db[attach_db.iloc[:, 0] == sel_t].iloc[:, 1].unique().tolist()
        acts = [a for a in acts if a.lower() != 'nan']

        if acts:
            st.subheader("🛠️ 項目選擇")
            cols = st.columns(len(acts))
            for i, a in enumerate(acts):
                if cols[i].button(a, key=f"B_{a}"):
                    st.session_state["cur_a"] = a
                    st.rerun()

            if "cur_a" in st.session_state:
                curr_a = st.session_state["cur_a"]
                st.info(f"目前項目：{curr_a}")
                
                # 篩選出該項目的所有列
                target_rows = attach_db[(attach_db.iloc[:, 0] == sel_t) & (attach_db.iloc[:, 1] == curr_a)]

                # --- 第一步：C 欄勾選 ---
                st.markdown("### ⚖️ 第一步：條件確認 (C 欄)")
                selected_indices = []
                for idx, row in target_rows.iterrows():
                    c_val = row.iloc[2]
                    if c_val.lower() != 'nan' and c_val != '':
                        if st.checkbox(c_val, key=f"C_{idx}"):
                            selected_indices.append(idx)

                # --- 第二步：姓名 ---
                st.markdown("### 👤 第二步：人員登錄")
                u_name = st.text_input("輸入姓名以解鎖附件清單", key="U_NAME")

                # --- 第三步：D-I 欄附件 (只有勾了且有名字才準出現) ---
                if u_name and selected_indices:
                    st.divider()
                    st.markdown("### 📂 第三步：應檢附附件 (D-I 欄)")
                    
                    # 這裡是關鍵：只拿「勾選列」的附件
                    final_files = []
                    for s_idx in selected_indices:
                        # 抓取該列的 D 到 I 欄
                        row_data = attach_db.loc[s_idx].iloc[3:9].tolist()
                        final_files.extend([f for f in row_data if f.lower() != 'nan' and f != ''])
                    
                    # 去重
                    final_files = list(dict.fromkeys(final
