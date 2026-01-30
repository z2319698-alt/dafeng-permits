import streamlit as st
import pandas as pd
from datetime import datetime as dt
import urllib.parse

# 1. 頁面配置
st.set_page_config(page_title="大豐管理系統", layout="wide")

# 2. 讀取數據
URL = "https://docs.google.com/spreadsheets/d/1BA427GfGw41UWen083KSWxbdRwbe3a1SEF_H89MyBZE/export?format=xlsx"

@st.cache_data(ttl=30)
def load_all_data():
    all_sh = pd.read_excel(URL, sheet_name=None)
    main_df = None
    # 鎖定檢查表分頁 (GID 846283148)
    attach_df = next((df for n, df in all_sh.items() if "檢查表" in n or "附件" in n), None)
    
    if attach_df is not None:
        # 處理合併儲存格：確保「類型」與「項目」每一行都有值
        attach_df.iloc[:, 0] = attach_df.iloc[:, 0].ffill()
        attach_df.iloc[:, 1] = attach_df.iloc[:, 1].ffill()
    
    for n, df in all_sh.items():
        df.columns = [str(c).strip() for c in df.columns]
        if "許可證名稱" in df.columns:
            main_df = df
    return main_df, attach_df

try:
    df, attach_db = load_all_data()
    C_NAME, C_DATE, C_TYPE = "許可證名稱", "到期日期", "許可證類型"
    df['D'] = pd.to_datetime(df[C_DATE], errors='coerce')
    now = dt.now()

    # 3. 跑馬燈
    urgent = df[(df['D'] <= now + pd.Timedelta(days=180)) & (df['D'].notnull())]
    if not urgent.empty:
        m_txt = "　　".join([f"🚨 {r[C_NAME]}(剩{(r['D']-now).days}天)" for _,r in urgent.iterrows()])
        st.markdown(f'<div style="background:#ff4b4b;color:white;padding:10px;border-radius:5px;"><marquee scrollamount="6">{m_txt}</marquee></div>', unsafe_allow_html=True)

    # 4. 側邊選單
    st.sidebar.markdown("## 📂 系統導航")
    t_list = sorted(df[C_TYPE].unique().tolist())
    sel_t = st.sidebar.selectbox("1. 選擇類型", t_list)
    sub = df[df[C_TYPE] == sel_t].reset_index(drop=True)
    sel_n = st.sidebar.radio("2. 選擇許可證", sub[C_NAME].tolist())

    # 5. 主畫面資訊
    row = sub[sub[C_NAME] == sel_n].iloc[0]
    st.title(f"📄 {sel_n}")
    st.divider()
    raw_type = str(row[C_TYPE])

    # 6. 第三層按鈕 (動態抓取項目)
    acts_list = []
    if attach_db is not None:
        acts_list = attach_db[attach_db.iloc[:, 0].astype(str).str.contains(sel_t[:2], na=False)].iloc[:, 1].unique().tolist()
    
    if not acts_list: acts_list = ["展延"]

    st.subheader("🛠️ 第三層：辦理項目選擇")
    cols = st.columns(len(acts_list))
    for i, a in enumerate(acts_list):
        if cols[i].button(a, key=f"btn_{sel_n}_{a}", use_container_width=True):
            st.session_state["cur_a"] = a
            st.session_state["last_p"] = sel_n

    # 7. 流程執行
    if st.session_state.get("last_p") == sel_n and "cur_a" in st.session_state:
        curr_act = st.session_state["cur_a"]
        st.markdown(f"### 📍 目前選擇項目：**{curr_act}**")
        
        # 篩選 Excel 資料行
        mask = (attach_db.iloc[:, 0].astype(str).str.contains(sel_t[:2], na=False)) & \
               (attach_db.iloc[:, 1].astype(str).str.contains(curr_act[:2], na=False))
        target_rows = attach_db[mask]

        # 第一步：法規依據 (讀取 Excel 第四欄 D 欄)
        with st.expander("⚖️ 第一步：法規依據條件確認", expanded=True):
            laws_excel = target_rows.iloc[:, 3].dropna().unique().tolist()
            selected_laws = [l for l in laws_excel if st.checkbox(l, key=f"law_{sel_n}_{curr_act}_{l}")]
        
        # 第二步：人員登錄
        with st.expander("👤 第二步：人員登錄", expanded=True):
            c1, c2 = st.columns(2)
            u_name = c1.text_input("辦理人姓名", key=f"un_{sel_n}")
            u_date = c2.date_input("辦理日期", value=now, key=f"ud_{sel_n}")
            
            if u_name:
                # 第三步：應檢附附件 (讀取 Excel 第三欄 C 欄)
                st.markdown("---")
                st.subheader("📂 第三步：應檢附附件清單")
                
                attach_excel = target_rows.iloc[:, 2].dropna().unique().tolist()
                checked_f = []
                for item in attach_excel:
                    ca, cb = st.columns([0.5, 0.5])
                    if ca.checkbox(item, key=f"ck_{sel_n}_{curr_act}_{item}"):
                        checked_f.append(item)
                    cb.file_uploader("上傳", key=f"f_{sel_n}_{curr_act}_{item}", label_visibility="collapsed")
                
                # 發信
                st.divider()
                if st.button("🚀 提出申請並發信", use_container_width=True):
                    info = f"單位：{sel_n}\n項目：{curr_act}\n人員：{u_name}\n條件：{', '.join(selected_laws)}\n附件：{', '.join(checked_f)}"
                    sub_e = urllib.parse.quote(f"許可辦理申請：{sel_n}")
                    body_e = urllib.parse.quote(info)
                    st.markdown(f'<a href="mailto:andy.chen@df-recycle.com?subject={sub_e}&body={body_e}" style="background-color:#4CAF50;color:white;padding:12px;text-decoration:none;border-radius:5px;display:block;text-align:center;">📧 啟動郵件發送</a>', unsafe_allow_html=True)
            else:
                st.info("請輸入姓名以顯示第三步附件清單。")

except Exception as e:
    st.error(f"系統錯誤: {e}")
