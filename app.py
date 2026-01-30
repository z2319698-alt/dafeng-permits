import streamlit as st
import pandas as pd
from datetime import datetime as dt

st.set_page_config(page_title="大豐管理系統", layout="wide")

# 核心附件資料庫 - 參照「自主檢查表」規範
# 1. 應檢附文件 (通用) 
COMMON_DOCS = [
    "1. 公私場所基本資料表 (表 C)",
    "2. 公私場所製程摘要表 (表 C-A1)",
    "3. 空氣污染防制計畫書/差異說明書",
    "4. 試車計畫書",
    "5. 目的事業主管機關核准設立證明文件影本"
]

# 2. 針對不同申請類別的特定文件 
DB_CONFIG = {
    "展延": COMMON_DOCS + ["歷年清除量統計表", "原許可證正本"],
    "變更": COMMON_DOCS + [
        "公私場所差異對照表 (表 AP-D)",
        "產品或產能快速變動資料表 (表 AP-Q)",
        "空氣污染減量措施相關證明"
    ],
    "異動": COMMON_DOCS + [
        "公私場所差異對照表 (表 AP-D)",
        "異動所需之工程期程相關文件",
        "監測設施說明書及連線計畫書"
    ],
    "變更暨展延": COMMON_DOCS + [
        "公私場所差異對照表 (表 AP-D)",
        "變更事項證明文件",
        "原許可證正本",
        "全套更新附件"
    ]
}

URL = "https://docs.google.com/spreadsheets/d/1BA427GfGw41UWen083KSWxbdRwbe3a1SEF_H89MyBZE/export?format=xlsx"

@st.cache_data(ttl=60)
def load_data():
    all_sh = pd.read_excel(URL, sheet_name=None)
    for n, df in all_sh.items():
        df.columns = [str(c).strip() for c in df.columns]
        if "許可證名稱" in df.columns: return df
    return list(all_sh.values())[0]

try:
    df = load_data()
    C_NAME, C_DATE, C_TYPE = "許可證名稱", "到期日期", "許可證類型"
    C_URL = next((c for c in df.columns if "網址" in c), None)
    
    df['D'] = pd.to_datetime(df[C_DATE], errors='coerce')
    df['T'] = df[C_TYPE].fillna("一般管理")
    now = dt.now()

    # 側邊欄與導航
    st.sidebar.markdown("## 📂 系統導航")
    t_list = sorted(df['T'].unique().tolist())
    sel_t = st.sidebar.selectbox("1. 選擇類型", t_list)
    sub = df[df['T'] == sel_t].reset_index(drop=True)
    if sub.empty: st.stop()
    sel_n = st.sidebar.radio("2. 選擇許可證", sub[C_NAME].tolist())

    # 主畫面資料
    row = sub[sub[C_NAME] == sel_n].iloc[0]
    st.title(f"📄 {sel_n}")
    
    # 顯示網址連結 (Excel 聯動)
    if C_URL and pd.notnull(row[C_URL]):
        st.info(f"🔗 [點此開啟各縣市審查規範網址]({row[C_URL]})")

    st.divider()

    # 辦理項目選擇區
    if "cur_a" not in st.session_state or st.session_state.get("last_p") != sel_n:
        st.session_state["cur_a"] = "展延"
        st.session_state["last_p"] = sel_n

    btn_cols = st.columns(len(DB_CONFIG))
    for i, a_name in enumerate(DB_CONFIG.keys()):
        if btn_cols[i].button(a_name, key=f"b_{sel_n}_{a_name}", use_container_width=True):
            st.session_state["cur_a"] = a_name

    # 顯示附件勾選與上傳欄位
    curr_act = st.session_state["cur_a"]
    st.success(f"📍 正在辦理：{curr_act} (請根據下方清單準備附件)")
    
    for item in DB_CONFIG[curr_act]:
        c1, c2 = st.columns([0.4, 0.6])
        with c1:
            st.checkbox(item, key=f"ck_{sel_n}_{curr_act}_{item}")
        with c2:
            st.file_uploader("上傳檔案", key=f"up_{sel_n}_{curr_act}_{item}", label_visibility="collapsed")

except Exception as e:
    st.error(f"系統錯誤: {e}")
