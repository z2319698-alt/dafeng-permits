import streamlit as st
import pandas as pd
from datetime import datetime as dt
import urllib.parse

st.set_page_config(page_title="大豐管理系統", layout="wide")

URL = "https://docs.google.com/spreadsheets/d/1BA427GfGw41UWen083KSWxbdRwbe3a1SEF_H89MyBZE/export?format=xlsx"

# 徹底移除緩存，確保每次都讀取最新資料
def load_data_fresh():
    all_sh = pd.read_excel(URL, sheet_name=None)
    main_df = None
    # 找到附件/檢查表 Sheet
    attach_df = next((df for n, df in all_sh.items() if any(k in n for k in ["檢查表", "附件"])), None)
    if attach_df is not None:
        # 處理合併儲存格：A欄(類型)、B欄(項目)
        attach_df.iloc[:, 0] = attach_df.iloc[:, 0].ffill()
        attach_df.iloc[:, 1] = attach_df.iloc[:, 1].ffill()
        # 轉字串、去空白
        attach_df = attach_df.astype(str).applymap(lambda x: x.strip())
    
    for n, df in all_sh.items():
        if "許可證名稱" in df.columns: main_df = df
    return main_df, attach_df

try:
    df, attach_db = load_data_fresh()
    C_NAME, C_DATE, C_TYPE = "許可證名稱", "到期日期", "許可證類型"
    df['D_OBJ'] = pd.to_datetime(df[C_DATE], errors='coerce')
    now = dt.now()

    # --- 跑馬燈 (死守) ---
    urgent = df[(df['D_OBJ'] <= now + pd.Timedelta(days=180)) & (df['D_OBJ'].notnull())]
    if not urgent.empty:
        m_txt = "　　".join([f"🚨 {r[C_NAME]}(剩{(r['D_OBJ']-now).days}天)" for _,r in urgent.iterrows()])
        st.markdown(f'<div style="background:#ff4b4b;color:white;padding:10px;border-radius:5px;"><marquee scrollamount="6">{m_txt}</marquee></div>', unsafe_allow_html=True)

    # 1. 側邊導覽
    sel_t = st.sidebar.selectbox("1. 選擇類型", sorted(df[C_TYPE].dropna().unique().tolist()))
    sub = df[df[C_TYPE] == sel_t].reset_index(drop=True)
    sel_n = st.sidebar.radio("2. 選擇許可證", sub[C_NAME].tolist())

    st.title(f"📄 {sel_n}")
    st.divider()

    if attach_db is not None:
        # 2. 辦理項目 (B 欄按鈕)
        target_db = attach_db[attach_db.iloc[:, 0] == sel_t]
        acts = target_db.iloc[:, 1].unique().tolist()
        acts = [a for a in acts if a.lower() != 'nan']

        if acts:
            st.subheader("🛠️ 第三層：辦理項目選擇 (B 欄)")
            # 建立按鈕
            cols = st.columns(len(acts))
            for i, a in enumerate(acts):
                if cols[i].button(a, key=f"btn_{a}"):
                    st.session_state["active_act"] = a
                    st.rerun()

            # 當點擊了某個項目（例如：變更）
            if "active_act" in st.session_state:
                curr_a = st.session_state["active_act"]
                st.info(f"📍 目前選取項目：{curr_a}")
                
                # 篩選該項目下的所有法規列
                rows = target_db[target_db.iloc[:, 1] == curr_a]

                # --- 第一步：C 欄勾選 ---
                st.markdown("### ⚖️ 第一步：條件確認 (C 欄)")
                # 用來存放勾選了哪幾列的 Index
                checked_rows = []
                for idx, row in rows.iterrows():
                    c_text = row.iloc[2] # C 欄
                    if c_text.lower() != 'nan' and c_text != '':
                        if st.checkbox(c_text, key=f"C_CHK_{idx}"):
                            checked_rows.append(idx)

                # --- 第二步：人員登錄 ---
                st.markdown("### 👤 第二步：人員登錄")
                u_name = st.text_input("辦理人姓名", key="U_NAME_INPUT")

                # --- 第三步：附件顯示 (關鍵鎖死邏輯) ---
                if u_name and checked_rows:
                    st.markdown("---")
                    st.subheader("📂 第三步：應檢附附件清單 (D-I 欄)")
                    
                    # 重新計算附件：只針對「被勾選的列」抓 D-I 欄
                    final_attach_list = []
                    for ridx in checked_rows:
                        # 只讀取該列的 3-8 索引欄位 (D, E, F, G, H, I)
                        files = attach_db.loc[ridx].iloc[3:9].tolist()
                        final_attach_list.extend([f for f in files if str(f).lower() != 'nan' and str(f).strip() != ''])
                    
                    # 徹底去重
                    final_attach_list = list(dict.fromkeys(final_attach_list))

                    if final_attach_list:
                        for f_idx, f_name in enumerate(final_attach_list):
                            c1, c2 = st.columns([0.6, 0.4])
                            c1.markdown(f"✅ **{f_name}**")
                            c2.file_uploader("上傳", key=f"UP_{f_idx}_{f_name}", label_visibility="collapsed")
                        
                        if st.button("🚀 彙整申請內容", use_container_width=True):
                            st.success("彙整成功！")
                    else:
                        st.warning("⚠️ 此條件在 Excel 中未設定附件內容。")
                elif u_name and not checked_rows:
                    st.warning("👈 請先在上方「第一步」勾選你要辦理的條件項目！")
        else:
            st.info("此項目無須填寫檢查表。")

except Exception as e:
    st.error(f"系統發生錯誤: {e}")
