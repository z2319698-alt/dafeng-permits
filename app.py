import streamlit as st
import pandas as pd
from datetime import datetime as dt

# 1. 配置
st.set_page_config(page_title="大豐管理系統", layout="wide")

# 2. 附件資料庫 (精準分類)
DB = {
    "P": {
        "展延": ["清理計畫書(更新版)", "廢棄物合約影本", "負責人身分證影本"],
        "變更": ["變更申請表", "差異對照表", "製程說明圖"],
        "異動": ["異動申請書", "相關證明文件"]
    },
    "C": {
        "展延": ["原許可證正本", "車輛照片 (含排氣檢驗)", "駕駛員證照及勞保卡", "廢棄物處置同意文件"],
        "變更": ["變更申請表", "變更事項證明", "行照影本", "保險單影本"],
        "變更暨展延": ["變更暨展延申請表", "全套更新版附件", "歷年清除量統計表", "切結書"]
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
    df['D'] = pd.to_datetime(df[C_DATE], errors='coerce')
    df['T'] = df[C_TYPE].fillna("一般管理")
    now = dt.now()

    # 3. 頂部跑馬燈警報
    urgent = df[(df['D'] <= now + pd.Timedelta(days=180)) & (df['D'].notnull())]
    if not urgent.empty:
        m_items = [f"🚨 {r[C_NAME]}(剩{(r['D']-now).days}天)" for _,r in urgent.iterrows()]
        txt = "　　".join(m_items)
        st.markdown(f'<div style="background:#ff4b4b;color:white;padding:10px;border-radius:5px;"><marquee scrollamount="6">{txt}</marquee></div>', unsafe_allow_html=True)

    # 4. 側邊選單復原 (你原本的樣式)
    st.sidebar.markdown("## 📂 系統導航")
    t_list = sorted(df['T'].unique().tolist())
    sel_t = st.sidebar.selectbox("1. 選擇類型", t_list)
    st.sidebar.markdown("---")
    
    sub = df[df['T'] == sel_t].reset_index(drop=True)
    if sub.empty: st.stop()
    sel_n = st.sidebar.radio("2. 選擇許可證", sub[C_NAME].tolist())

    # 5. 主畫面數據展示
    row = sub[sub[C_NAME] == sel_n].iloc[0]
    st.title(f"📄 {sel_n}")
    
    c1, c2, c3 = st.columns(3)
    d_val = row['D']
    c1.metric("到期日期", d_val.strftime('%Y-%m-%d') if pd.notnull(d_val) else "未填寫")
    days_left = (d_val - now).days if pd.notnull(d_val) else None
    c2.metric("剩餘天數", f"{days_left} 天" if days_left else "N/A")
    c3.metric("目前類型", row['T'])

    st.divider()

    # 6. 辦理項目 (解決不見的問題)
    # 強制判斷類型，確保按鈕一定會出來
    if "清除" in str(sel_n):
        acts = DB["C"]
    elif "清理" in str(sel_n) or "計畫" in str(sel_n):
        acts = DB["P"]
    else:
        acts = None

    if acts:
        st.subheader("🛠️ 辦理項目指引")
        # 預設動作為「展延」
        if "cur_a" not in st.session_state or st.session_state.get("last_p") != sel_n:
            st.session_state["cur_a"] = "展延"
            st.session_state["last_p"] = sel_n

        # 渲染橫排按鈕
        btn_cols = st.columns(len(acts))
        for i, a_name in enumerate(acts.keys()):
            if btn_cols[i].button(a_name, key=f"btn_{sel_n}_{a_name}", use_container_width=True):
                st.session_state["cur_a"] = a_name

        # 顯示選中的勾選單
        curr_act = st.session_state["cur_a"]
        if curr_act in acts:
            st.success(f"📍 正在辦理：{curr_act}")
            for item in acts[curr_act]:
                st.checkbox(item, key=f"chk_{sel_n}_{curr_act}_{item}")
    else:
        st.info("💡 該項目暫無辦理指引。")

except Exception as e:
    st.error(f"錯誤: {e}")

# 7. 原始數據 (呈現完整表格，不隱藏欄位)
st.divider()
st.subheader("📊 原始數據總表")
with st.expander("展開查看完整 Excel 表格"):
    st.dataframe(df, use_container_width=True)
