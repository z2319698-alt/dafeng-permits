import streamlit as st
import pandas as pd
from datetime import datetime as dt

# 1. 配置
st.set_page_config(page_title="大豐管理系統", layout="wide")

# 2. 依照類型設定各自的選項與附件
DB_CONFIG = {
    "清除": {
        "變更": ["變更申請表", "差異對照表", "變更事項證明", "行照影本", "保險單"],
        "變更暨展延": ["變更暨展延申請表", "全套更新版附件", "歷年清除量統計表", "切結書"],
        "展延": ["原許可證正本", "清除合約書", "技術員證照", "勞保卡", "車照/排煙檢驗"]
    },
    "清理": {
        "變更": ["清理計畫書變更申請表", "製程說明圖", "廢棄物產出量對照表"],
        "展延": ["清理計畫書展延申請表", "最新版清理計畫書", "廢棄物委託契約影本"],
        "異動": ["異動申請書", "相關證明文件", "基本資料變更證明"]
    },
    "水污染": {
        "事前變更": ["事前變更申請書", "技師簽證", "水措設施變更圖說"],
        "事後變更": ["事後變更備查文件", "變更前後對照說明", "現場照片"],
        "展延": ["水污染展延申請表", "原核准文件", "最近一次水質檢測報告"]
    }
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

    # 3. 跑馬燈警報
    urgent = df[(df['D'] <= now + pd.Timedelta(days=180)) & (df['D'].notnull())]
    if not urgent.empty:
        m_items = [f"🚨 {r[C_NAME]}(剩{(r['D']-now).days}天)" for _,r in urgent.iterrows()]
        txt = "　　".join(m_items)
        st.markdown(f'<div style="background:#ff4b4b;color:white;padding:10px;border-radius:5px;"><marquee scrollamount="6">{txt}</marquee></div>', unsafe_allow_html=True)

    # 4. 側邊選單
    st.sidebar.markdown("## 📂 系統導航")
    t_list = sorted(df['T'].unique().tolist())
    sel_t = st.sidebar.selectbox("選擇類型", t_list)
    st.sidebar.markdown("---")
    sub = df[df['T'] == sel_t].reset_index(drop=True)
    if sub.empty: st.stop()
    sel_n = st.sidebar.radio("選擇許可證", sub[C_NAME].tolist())

    # 5. 主畫面顯示
    row = sub[sub[C_NAME] == sel_n].iloc[0]
    st.title(f"📄 {sel_n}")
    
    c1, c2, c3 = st.columns(3)
    d_val = row['D']
    c1.metric("到期日期", d_val.strftime('%Y-%m-%d') if pd.notnull(d_val) else "未填")
    days_left = (d_val - now).days if pd.notnull(d_val) else None
    c2.metric("剩餘天數", f"{days_left} 天" if days_left else "N/A")
    c3.metric("Excel 標記分類", row[C_TYPE])

    st.divider()

    # 6. 核心判定：模糊匹配類型
    st.subheader("🛠️ 辦理項目指引")
    
    raw_type = str(row[C_TYPE])
    acts = None
    
    # 只要標題包含關鍵字就抓取
    if "水污染" in raw_type:
        acts = DB_CONFIG["水污染"]
    elif "清除" in raw_type:
        acts = DB_CONFIG["清除"]
    elif "清理" in raw_type:
        acts = DB_CONFIG["清理"]
    else:
        # 萬一都沒對上，給一個保底選項
        acts = {"展延": ["請確認 Excel 類型名稱"], "變更": ["請確認 Excel 類型名稱"]}

    # 初始化與切換狀態
    if "cur_a" not in st.session_state or st.session_state.get("last_p") != sel_n:
        st.session_state["cur_a"] = list(acts.keys())[0]
        st.session_state["last_p"] = sel_n

    btn_cols = st.columns(len(acts))
    for i, a_name in enumerate(acts.keys()):
        if btn_cols[i].button(a_name, key=f"b_{sel_n}_{a_name}", use_container_width=True):
            st.session_state["cur_a"] = a_name

    # 7. 顯示附件與上傳
    curr_act = st.session_state["cur_a"]
    st.success(f"📍 正在辦理：{curr_act}")
    
    for item in acts.get(curr_act, []):
        c1, c2 = st.columns([0.4, 0.6])
        with c1:
            st.checkbox(item, key=f"ck_{sel_n}_{curr_act}_{item}")
        with c2:
            st.file_uploader("上傳檔案", key=f"up_{sel_n}_{curr_act}_{item}", label_visibility="collapsed")

except Exception as e:
    st.error(f"系統錯誤: {e}")

st.divider()
with st.expander("展開查看完整 Excel 表格"):
    st.dataframe(df, use_container_width=True)
