import streamlit as st
import pandas as pd
from datetime import datetime as dt

# 1. 配置與標題
st.set_page_config(page_title="大豐許可管理系統", layout="wide")

# 2. 附件資料庫
DB = {
    "P": {
        "展延": ["清理計畫書(更新版)", "廢棄物合約影本", "負責人身分證影本"],
        "變更": ["變更申請表", "差異對照表", "製程說明圖"],
        "異動": ["異動申請書", "相關證明文件"]
    },
    "C": {
        "展延": ["原許可證正本", "車輛照片", "駕駛員證照", "處置同意文件"],
        "變更": ["變更申請表", "車輛證明", "有效保險單"],
        "變更暨展延": ["合併申請書", "全套更新附件", "清除量統計表"]
    }
}

URL = "https://docs.google.com/spreadsheets/d/1BA427GfGw41UWen083KSWxbdRwbe3a1SEF_H89MyBZE/export?format=xlsx"

# 3. 讀取並偵測分頁
@st.cache_data(ttl=60)
def load_data():
    all_sh = pd.read_excel(URL, sheet_name=None)
    for n, df in all_sh.items():
        df.columns = [str(c).strip() for c in df.columns]
        if "許可證名稱" in df.columns:
            return df
    return list(all_sh.values())[0]

try:
    df = load_data()
    # 最新欄位對齊
    C_NAME, C_DATE, C_TYPE = "許可證名稱", "到期日期", "許可證類型"
    df['D'] = pd.to_datetime(df[C_DATE], errors='coerce')
    df['T'] = df[C_TYPE].fillna("一般管理")
    now = dt.now()

    # 4. 🔥 跑馬燈功能回歸 (警報剩餘 180 天內的許可證)
    urgent = df[(df['D'] <= now + pd.Timedelta(days=180)) & (df['D'].notnull())]
    if not urgent.empty:
        m_items = []
        for _, r in urgent.iterrows():
            days = (r['D'] - now).days
            m_items.append(f"🚨 {r[C_NAME]} (剩 {days} 天)")
        marquee_txt = "　　".join(m_items)
        st.markdown(
            f'<div style="background:#ff4b4b;color:white;padding:10px;border-radius:5px;">'
            f'<marquee scrollamount="6">{marquee_txt}</marquee></div>',
            unsafe_allow_html=True
        )

    # 5. 📂 側邊欄排版復原
    st.sidebar.markdown("## 📂 系統導航")
    t_list = sorted(df['T'].unique().tolist())
    sel_t = st.sidebar.selectbox("1. 選擇類型", t_list)
    st.sidebar.markdown("---")
    
    sub = df[df['T'] == sel_t].reset_index(drop=True)
    if sub.empty: st.stop()
    sel_n = st.sidebar.radio("2. 選擇許可證名稱", sub[C_NAME].tolist())

    # 6. 主畫面顯示
    row = sub[sub[C_NAME] == sel_n].iloc[0]
    st.title(f"📄 {sel_n}")
    
    col1, col2, col3 = st.columns(3)
    d_val = row['D']
    col1.metric("到期日期", d_val.strftime('%Y-%m-%d') if pd.notnull(d_val) else "未填寫")
    
    days_left = (d_val - now).days if pd.notnull(d_val) else None
    col2.metric("剩餘天數", f"{days_left} 天" if days_left is not None else "N/A")
    col3.metric("目前類型", row['T'])

    st.divider()
    st.subheader("🛠️ 辦理項目與附件指引")

    # 匹配資料庫
    acts = None
    if "清除" in str(sel_n): acts = DB["C"]
    elif "清理" in str(sel_n) or "計畫" in str(sel_n): acts = DB["P"]

    if acts:
        # 按鈕橫向排版
        btn_cols = st.columns(len(acts))
        for i, a_name in enumerate(acts.keys()):
            if btn_cols[i].button(a_name, key=f"b_{sel_n}_{a_name}", use_container_width=True):
                st.session_state["cur_a"] = a_name
                st.session_state["cur_p"] = sel_n

        # 顯示附件勾選清單
        if st.session_state.get("cur_p") == sel_n:
            cur = st.session_state.get("cur_a")
            if cur in acts:
                st.success(f"📍 正在辦理：{cur}")
                for f in acts[cur]:
                    st.checkbox(f, key=f"c_{sel_n}_{cur}_{f}")
            else:
                st.info("👆 請選擇上方辦理項目。")
    else:
        st.info("💡 暫無預設指引。")

except Exception as e:
    st.error(f"系統錯誤: {e}")

# 7. 數據總表
st.divider()
with st.expander("📊 原始數據總表"):
    st.dataframe(df)
