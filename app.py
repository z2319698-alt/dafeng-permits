import streamlit as st
import pandas as pd
from datetime import datetime as dt
import urllib.parse

st.set_page_config(page_title="大豐管理系統", layout="wide")

URL = "https://docs.google.com/spreadsheets/d/1BA427GfGw41UWen083KSWxbdRwbe3a1SEF_H89MyBZE/export?format=xlsx"

# 1. 數據讀取 (徹底移除緩存)
def get_data_live():
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
    df, attach_db = get_data_live()
    C_NAME, C_DATE, C_TYPE = "許可證名稱", "到期日期", "許可證類型"
    df['D_OBJ'] = pd.to_datetime(df[C_DATE], errors='coerce')
    now = dt.now()

    # --- 跑馬燈警報 ---
    urgent = df[(df['D_OBJ'] <= now + pd.Timedelta(days=180)) & (df['D_OBJ'].notnull())]
    if not urgent.empty:
        m_txt = "　　".join([f"🚨 {r[C_NAME]}(剩{(r['D_OBJ']-now).days}天)" for _,r in urgent.iterrows()])
        st.markdown(f'<div style="background:#ff4b4b;color:white;padding:10px;border-radius:5px;"><marquee scrollamount="6">{m_txt}</marquee></div>', unsafe_allow_html=True)

    # 2. 側邊選單
    sel_t = st.sidebar.selectbox("1. 選擇類型", sorted(df[C_TYPE].dropna().unique().tolist()))
    sub = df[df[C_TYPE] == sel_t].reset_index(drop=True)
    sel_n = st.sidebar.radio("2. 選擇許可證", sub[C_NAME].tolist())

    st.title(f"📄 {sel_n}")
    st.divider()

    if attach_db is not None:
        # 3. 辦理項目 (B 欄)
        acts = attach_db[attach_db.iloc[:, 0] == sel_t].iloc[:, 1].unique().tolist()
        acts = [a for a in acts if a.lower() != 'nan']

        if acts:
            st.subheader("🛠️ 第三層：辦理項目選擇")
            cols = st.columns(len(acts))
            for i, a in enumerate(acts):
                if cols[i].button(a, key=f"B_{a}"):
                    st.session_state["cur_a"] = a
                    # 切換項目時強制清空所有勾選與緩存
                    st.rerun()

            if "cur_a" in st.session_state:
                curr_a = st.session_state["cur_a"]
                st.info(f"📍 目前選取項目：{curr_a}")
                
                # 取得該項目的所有相關列 (DataFrame)
                target_rows = attach_db[(attach_db.iloc[:, 0] == sel_t) & (attach_db.iloc[:, 1] == curr_a)]

                # --- 第一步：C 欄勾選 ---
                with st.expander("⚖️ 第一步：法規依據條件確認", expanded=True):
                    # 用來存儲「被勾選的那幾列」的資料
                    checked_indices = []
                    for idx, row in target_rows.iterrows():
                        law_label = row.iloc[2]
                        if law_label.lower() != 'nan' and law_label != '':
                            if st.checkbox(law_label, key=f"C_CHK_{idx}"):
                                checked_indices.append(idx)

                # --- 第二步：登錄姓名 ---
                with st.expander("👤 第二步：人員登錄", expanded=True):
                    u_name = st.text_input("辦理人姓名", key="U_NAME")

                # --- 第三步：附件 (D-I 欄) ---
                # 【核心邏輯】：只有勾了且有名字，才開始「畫」附件區塊
                if u_name and checked_indices:
                    st.markdown("---")
                    st.subheader("📂 第三步：應檢附附件清單")
                    
                    # 從原始數據中「只」拿出勾選的那幾列
                    final_rows = attach_db.loc[checked_indices]
                    
                    # 抓取這幾列的 D 到 I 欄，並攤平成一維清單
                    all_attachments = []
                    for _, r in final_rows.iterrows():
                        # 只拿 3 到 8 索引的內容 (即 D-I 欄)
                        row_files = [str(r.iloc[i]).strip() for i in range(3, 9) if pd.notnull(r.iloc[i]) and str(r.iloc[i]).lower() != 'nan' and str(r.iloc[i]) != '']
                        all_attachments.extend(row_files)
                    
                    # 去除重複項
                    unique_attachments = list(dict.fromkeys(all_attachments))

                    if unique_attachments:
                        for f_name in unique_attachments:
                            c1, c2 = st.columns([0.7, 0.3])
                            c1.checkbox(f_name, key=f"FIN_{f_name}")
                            c2.file_uploader("上傳", key=f"UP_{f_name}", label_visibility="collapsed")
                        
                        if st.button("🚀 提出申請", use_container_width=True):
                            st.success("申請資料已就緒！")
                    else:
                        st.warning("⚠️ Excel 中此條件未設定對應附件。")
                elif u_name:
                    st.warning("👈 請在第一步勾選辦理條件，附件清單才會顯示。")
        else:
            st.info("此類型無須透過自主檢查表辦理。")

except Exception as e:
    st.error(f"系統異常: {e}")
