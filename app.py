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
    # 鎖定檢查表分頁 (GID 846283148)
    attach_df = next((df for n, df in all_sh.items() if "檢查表" in n or "附件" in n), None)
    
    if attach_df is not None:
        # 處理合併儲存格：確保每一行都有類別與項目
        attach_df.iloc[:, 0] = attach_df.iloc[:, 0].ffill()
        attach_df.iloc[:, 1] = attach_df.iloc[:, 1].ffill()
        # 清除所有欄位的空格
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

    # --- 恢復跑馬燈警報 ---
    urgent = df[(df['D_OBJ'] <= now + pd.Timedelta(days=180)) & (df['D_OBJ'].notnull())]
    if not urgent.empty:
        m_txt = "　　".join([f"🚨 {r[C_NAME]}(剩{(r['D_OBJ']-now).days}天)" for _,r in urgent.iterrows()])
        st.markdown(f'<div style="background:#ff4b4b;color:white;padding:10px;border-radius:5px;"><marquee scrollamount="6">{m_txt}</marquee></div>', unsafe_allow_html=True)

    # 3. 側邊選單
    st.sidebar.markdown("## 📂 系統導航")
    t_list = sorted(df[C_TYPE].dropna().unique().tolist())
    sel_t = st.sidebar.selectbox("1. 選擇類型", t_list)
    sub = df[df[C_TYPE] == sel_t].reset_index(drop=True)
    sel_n = st.sidebar.radio("2. 選擇許可證", sub[C_NAME].tolist())

    st.title(f"📄 {sel_n}")
    st.divider()

    # --- 第三層按鈕：嚴格匹配 Excel B 欄 ---
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
            # 篩選出該類型與該項目的所有資料列
            target_rows = attach_db[(attach_db.iloc[:, 0] == sel_t) & (attach_db.iloc[:, 1] == curr_act)]

            # --- 第一步：法規依據 (讀取 C 欄，即索引 2) ---
            with st.expander("⚖️ 第一步：法規依據條件確認", expanded=True):
                laws = target_rows.iloc[:, 2].dropna().unique().tolist()
                for l in laws:
                    if str(l).lower() != 'nan' and str(l) != '':
                        st.checkbox(str(l), key=f"law_{sel_n}_{curr_act}_{l}")

            # 第二步：人員登錄
            with st.expander("👤 第二步：人員登錄", expanded=True):
                u_name = st.text_input("辦理人姓名", key=f"un_{sel_n}")
                
            # --- 第三步：附件 (讀取 D 到 I 欄，即索引 3 到 8) ---
            if u_name:
                st.markdown("---")
                st.subheader("📂 第三步：應檢附附件清單")
                # 攤平 D 到 I 欄的所有內容並去除空白與重複
                files_area = target_rows.iloc[:, 3:9].values.flatten()
                files = list(dict.fromkeys([str(f).strip() for f in files_area if pd.notnull(f) and str(f).lower() != 'nan' and str(f) != '']))
                
                checked_f = []
                for f in files:
                    ca, cb = st.columns([0.6, 0.4])
                    if ca.checkbox(f, key=f"file_{sel_n}_{curr_act}_{f}"):
                        checked_f.append(f)
                    cb.file_uploader("上傳", key=f"up_{sel_n}_{curr_act}_{f}", label_visibility="collapsed")
                
                st.divider()
                if st.button("🚀 提出申請並發信", use_container_width=True):
                    info = f"單位：{sel_n}\n項目：{curr_act}\n辦理人：{u_name}\n附件：{', '.join(checked_f)}"
                    sub_e = urllib.parse.quote(f"許可辦理申請：{sel_n}")
                    body_e = urllib.parse.quote(info)
                    st.markdown(f'<a href="mailto:andy.chen@df-recycle.com?subject={sub_e}&body={body_e}" style="background-color:#4CAF50;color:white;padding:12px;text-decoration:none;border-radius:5px;display:block;text-align:center;">📧 按此啟動郵件發送</a>', unsafe_allow_html=True)
            else:
                st.info("請輸入姓名以解鎖第三步附件清單。")
    else:
        st.info("目前此類型無須透過自主檢查表辦理。")

except Exception as e:
    st.error(f"系統錯誤: {e}")

st.divider()
with st.expander("📊 數據總表"):
    st.dataframe(df, use_container_width=True)
