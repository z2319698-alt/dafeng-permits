import streamlit as st
import pandas as pd
from datetime import datetime as dt
import urllib.parse

# 1. 基本設定
st.set_page_config(page_title="大豐管理系統", layout="wide")

# 2. 自動讀取資料
URL = "https://docs.google.com/spreadsheets/d/1BA427GfGw41UWen083KSWxbdRwbe3a1SEF_H89MyBZE/export?format=xlsx"

@st.cache_data(ttl=5) # 5秒自動更新一次，您改Excel網頁馬上變
def load_data():
    all_sheets = pd.read_excel(URL, sheet_name=None)
    main_df = None
    check_df = None
    
    # 尋找主表與檢查表
    for name, df in all_sheets.items():
        df.columns = [str(c).strip() for c in df.columns]
        if "許可證名稱" in df.columns:
            main_df = df
        if "檢查表" in name or "各縣市" in name:
            check_df = df
            # 自動處理合併儲存格
            check_df.iloc[:, 0] = check_df.iloc[:, 0].ffill()
            check_df.iloc[:, 1] = check_df.iloc[:, 1].ffill()
    return main_df, check_df

try:
    df, c_db = load_data()
    C_NAME, C_DATE, C_TYPE = "許可證名稱", "到期日期", "許可證類型"
    df['D_OBJ'] = pd.to_datetime(df[C_DATE], errors='coerce')
    now = dt.now()

    # --- 跑馬燈警報 ---
    urgent = df[(df['D_OBJ'] <= now + pd.Timedelta(days=180)) & (df['D_OBJ'].notnull())]
    if not urgent.empty:
        m_items = [f"🚨 {r[C_NAME]}(剩{(r['D_OBJ']-now).days}天)" for _,r in urgent.iterrows()]
        st.markdown(f'<div style="background:#ff4b4b;color:white;padding:10px;border-radius:5px;"><marquee scrollamount="6">{"　　".join(m_items)}</marquee></div>', unsafe_allow_html=True)

    # 3. 側邊導覽
    st.sidebar.markdown("## 📂 系統導航")
    types = sorted(df[C_TYPE].dropna().unique().tolist())
    sel_t = st.sidebar.selectbox("1. 選擇類型", types)
    sub = df[df[C_TYPE] == sel_t].reset_index(drop=True)
    sel_n = st.sidebar.radio("2. 選擇許可證", sub[C_NAME].tolist())

    # 4. 主畫面顯示
    st.title(f"📄 {sel_n}")
    curr_row = sub[sub[C_NAME] == sel_n].iloc[0]
    st.write(f"**目前效期：** {curr_row[C_DATE]}")
    st.divider()

    # 5. 自動產生第三層按鈕 (從Excel B欄抓取)
    if c_db is not None:
        # 完全比對類型 A 欄
        match_acts = c_db[c_db.iloc[:, 0] == sel_t].iloc[:, 1].dropna().unique().tolist()
        match_acts = [a for a in match_acts if str(a).lower() != 'nan']
        
        if match_acts:
            st.subheader("🛠️ 第三層：辦理項目選擇")
            cols = st.columns(len(match_acts))
            for i, act_name in enumerate(match_acts):
                if cols[i].button(act_name, key=f"btn_{sel_n}_{act_name}", use_container_width=True):
                    st.session_state["act"] = act_name
                    st.session_state["p_name"] = sel_n

    # 6. 點擊按鈕後顯示內容
    if st.session_state.get("p_name") == sel_n and "act" in st.session_state:
        cur_a = st.session_state["act"]
        st.markdown(f"### 📍 辦理項目：**{cur_a}**")
        
        # 篩選 Excel 內容
        rows = c_db[(c_db.iloc[:, 0] == sel_t) & (c_db.iloc[:, 1] == cur_a)]

        # 第一步：辦理條件 (D 欄)
        with st.expander("⚖️ 第一步：法規依據條件確認", expanded=True):
            laws = rows.iloc[:, 3].dropna().unique().tolist()
            for l in laws:
                if str(l).lower() != 'nan': st.checkbox(str(l), key=f"l_{sel_n}_{cur_a}_{l}")
            if not laws: st.write("無特定辦理條件。")

        # 第二步：登錄
        with st.expander("👤 第二步：人員登錄", expanded=True):
            u_name = st.text_input("辦理人姓名", key=f"un_{sel_n}")
            
        # 第三步：附件 (C 欄)
        if u_name:
            with st.expander("📂 第三步：應檢附附件清單", expanded=True):
                files = rows.iloc[:, 2].dropna().unique().tolist()
                checked_files = []
                for f in files:
                    if str(f).lower() != 'nan':
                        c_a, c_b = st.columns([0.6, 0.4])
                        if c_a.checkbox(str(f), key=f"f_{sel_n}_{cur_a}_{f}"):
                            checked_files.append(str(f))
                        c_b.file_uploader("上傳", key=f"up_{sel_n}_{cur_a}_{f}", label_visibility="collapsed")
                
                if st.button("🚀 提出申請並發信", use_container_width=True):
                    mail_info = f"單位：{sel_n}\n項目：{cur_a}\n辦理人：{u_name}\n勾選附件：{', '.join(checked_files)}"
                    sub_enc = urllib.parse.quote(f"許可申請：{sel_n}")
                    body_enc = urllib.parse.quote(mail_info)
                    st.markdown(f'<a href="mailto:andy.chen@df-recycle.com?subject={sub_enc}&body={body_enc}" style="background-color:#4CAF50;color:white;padding:12px;text-decoration:none;border-radius:5px;display:block;text-align:center;">📧 啟動郵件發送申請</a>', unsafe_allow_html=True)

except Exception as e:
    st.error(f"系統自動同步中，請稍候... (錯誤訊息: {e})")

st.divider()
with st.expander("📊 許可證總表數據回饋"):
    st.dataframe(df, use_container_width=True)
