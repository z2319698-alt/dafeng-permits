import streamlit as st
import pandas as pd
from datetime import datetime as dt
import urllib.parse

st.set_page_config(page_title="大豐管理系統", layout="wide")

URL = "https://docs.google.com/spreadsheets/d/1BA427GfGw41UWen083KSWxbdRwbe3a1SEF_H89MyBZE/export?format=xlsx"

def load_all_data():
    all_sh = pd.read_excel(URL, sheet_name=None)
    main_df = None
    attach_df = next((df for n, df in all_sh.items() if "檢查表" in n or "附件" in n), None)
    if attach_df is not None:
        attach_df.iloc[:, 0] = attach_df.iloc[:, 0].ffill()
        attach_df.iloc[:, 1] = attach_df.iloc[:, 1].ffill()
        # 轉字串去空格
        attach_df = attach_df.astype(str).applymap(lambda x: x.strip())
    for n, df in all_sh.items():
        if "許可證名稱" in df.columns: main_df = df
    return main_df, attach_df

try:
    df, attach_db = load_all_data()
    C_NAME, C_DATE, C_TYPE = "許可證名稱", "到期日期", "許可證類型"
    df['D_OBJ'] = pd.to_datetime(df[C_DATE], errors='coerce')
    now = dt.now()

    # --- 跑馬燈 (死守) ---
    urgent = df[(df['D_OBJ'] <= now + pd.Timedelta(days=180)) & (df['D_OBJ'].notnull())]
    if not urgent.empty:
        m_txt = "　　".join([f"🚨 {r[C_NAME]}(剩{(r['D_OBJ']-now).days}天)" for _,r in urgent.iterrows()])
        st.markdown(f'<div style="background:#ff4b4b;color:white;padding:10px;border-radius:5px;"><marquee scrollamount="6">{m_txt}</marquee></div>', unsafe_allow_html=True)

    # 1. 導覽
    sel_t = st.sidebar.selectbox("1. 選擇類型", sorted(df[C_TYPE].dropna().unique().tolist()))
    sub = df[df[C_TYPE] == sel_t].reset_index(drop=True)
    sel_n = st.sidebar.radio("2. 選擇許可證", sub[C_NAME].tolist())

    st.title(f"📄 {sel_n}")
    st.divider()

    if attach_db is not None:
        # 2. 項目按鈕 (B 欄)
        target_db = attach_db[attach_db.iloc[:, 0] == sel_t]
        acts = target_db.iloc[:, 1].unique().tolist()
        acts = [a for a in acts if a.lower() != 'nan']

        if acts:
            st.subheader("🛠️ 辦理項目選擇")
            cols = st.columns(len(acts))
            for i, a in enumerate(acts):
                if cols[i].button(a, key=f"btn_{a}"):
                    st.session_state["cur_a"] = a
                    st.rerun()

            if "cur_a" in st.session_state:
                curr_a = st.session_state["cur_a"]
                st.info(f"📍 目前選取：{curr_a}")
                
                # 篩選該項目的資料
                rows = target_db[target_db.iloc[:, 1] == curr_a]

                # --- 第一步：C 欄勾選 ---
                st.markdown("### ⚖️ 第一步：條件確認 (C 欄)")
                # 這裡最重要：建立一個清單存儲「真正被勾選的列索引」
                active_indices = []
                for idx, row in rows.iterrows():
                    c_text = row.iloc[2]
                    if c_text.lower() != 'nan' and c_text != '':
                        # 只有當 checkbox 被勾選時，才把該列的 index 加入清單
                        if st.checkbox(c_text, key=f"C_{idx}"):
                            active_indices.append(idx)

                # --- 第二步：姓名 ---
                u_name = st.text_input("👤 第二步：辦理人姓名", key="user_name")

                # --- 第三步：D-I 欄附件 (嚴格連動) ---
                if u_name and active_indices:
                    st.markdown("---")
                    st.subheader("📂 第三步：應檢附附件清單")
                    
                    # 重新根據被勾選的 index 抓取附件內容
                    all_needed_files = []
                    for s_idx in active_indices:
                        # 抓取該列的 D,E,F,G,H,I 欄位 (index 3 到 8)
                        # 這邊是「一對一」的關鍵，絕對不抓沒勾的那幾列
                        row_attachments = attach_db.loc[s_idx].iloc[3:9].tolist()
                        all_needed_files.extend([f for f in row_attachments if f.lower() != 'nan' and f != ''])
                    
                    # 去除重複
                    final_files = list(dict.fromkeys(all_needed_files))

                    if final_files:
                        for f_name in final_files:
                            c1, c2 = st.columns([0.6, 0.4])
                            c1.markdown(f"📦 **{f_name}**")
                            c2.file_uploader("上傳", key=f"U_{f_name}", label_visibility="collapsed")
                        
                        if st.button("🚀 彙整並送出"):
                            st.success("申請資料已彙整！")
                    else:
                        st.warning("Excel 中此條件橫向沒有填寫任何附件內容。")
                elif u_name:
                    st.warning("👈 請在「第一步」勾選你要辦理的具體條件。")
        else:
            st.info("無須透過檢查表辦理。")

except Exception as e:
    st.error(f"系統錯誤: {e}")
