import streamlit as st
import pandas as pd
from datetime import datetime as dt

# 1. 配置網頁
st.set_page_config(page_title="大豐許可管理系統", layout="wide")

# 2. 定義核心資料庫
DB = {
    "P": {
        "展延": ["清理計畫書(更新版)", "廢棄物合約影本", "負責人身分證影本"],
        "變更": ["變更申請表", "差異對照表", "製程說明圖"],
        "異動": ["異動申請書", "相關證明文件"]
    },
    "C": {
        "展延": ["原許可證正本", "車輛照片 (含排氣檢驗)", "駕駛員證照及勞保卡", "廢棄物處置同意文件"],
        "變更": ["變更申請表", "變更事項證明文件", "行照影本", "保險單影本"],
        "變更暨展延": ["變更暨展延申請表", "全套更新版附件", "歷年清除量統計表", "相關切結書"]
    }
}

URL = "https://docs.google.com/spreadsheets/d/1BA427GfGw41UWen083KSWxbdRwbe3a1SEF_H89MyBZE/export?format=xlsx"

# 3. 讀取資料 - 自動掃描所有分頁
@st.cache_data(ttl=60)
def load_data_from_any_sheet():
    all_sheets = pd.read_excel(URL, sheet_name=None)
    for sheet_name, df in all_sheets.items():
        # 清除標題空格並轉字串
        df.columns = [str(c).strip() for c in df.columns]
        # 只要這分頁包含關鍵欄位，就認定是這張表
        if "清除許可證名稱" in df.columns:
            return df
    # 保底回傳第一個分頁
    return list(all_sheets.values())[0]

try:
    df = load_data_from_any_sheet()
    
    # 強制校對關鍵欄位名稱 (防止 Excel 些微改名)
    c_name = next((c for c in df.columns if "清除許可證名稱" in c), None)
    c_date = next((c for c in df.columns if "許可證期日" in c), None)
    c_type = next((c for c in df.columns if "變更項目" in c), None)

    if not c_name or not c_date:
        st.error("❌ 找不到關鍵欄位，請檢查 Excel 標題是否包含 '清除許可證名稱' 與 '許可證期日'")
        st.write("目前偵測到的欄位有：", df.columns.tolist())
        st.stop()

    # 4. 資料清洗
    df['D'] = pd.to_datetime(df[c_date], errors='coerce')
    df['T'] = df[c_type].fillna("一般管理")
    df['N'] = df[c_name]
    now = dt.now()

    # 5. 側邊選單
    st.sidebar.header("📂 系統選單")
    t_list = sorted(df['T'].unique().tolist())
    sel_t = st.sidebar.selectbox("1. 選擇類型", t_list)
    
    sub = df[df['T'] == sel_t].reset_index(drop=True)
    if sub.empty:
        st.stop()
        
    sel_n = st.sidebar.radio("2. 選擇許可證", sub['N'].tolist())

    # 6. 主畫面
    row_match = sub[sub['N'] == sel_n]
    if not row_match.empty:
        row = row_match.iloc[0]
        st.title(f"📄 {sel_n}")
        
        col1, col2 = st.columns(2)
        d_val = row['D']
        col1.metric("到期日期", d_val.strftime('%Y-%m-%d') if pd.notnull(d_val) else "未填寫")
        
        days_left = (d_val - now).days if pd.notnull(d_val) else None
        status_color = "green" if (days_left and days_left > 90) else "red"
        col2.markdown(f"**剩餘天數：** <span style='color:{status_color};font-size:24px;'>{days_left if days_left else 'N/A'} 天</span>", unsafe_allow_html=True)
        
        st.divider()
        st.subheader("🛠️ 辦理項目指引")

        # 匹配邏輯
        acts = None
        if "清除" in str(sel_n):
            acts = DB["C"]
        elif "清理" in str(sel_n) or "計畫" in str(sel_n):
            acts = DB["P"]

        if acts:
            # 建立按鈕
            btn_cols = st.columns(len(acts))
            for i, a_name in enumerate(acts.keys()):
                if btn_cols[i].button(a_name, key=f"btn_{sel_n}_{a_name}", use_container_width=True):
                    st.session_state["active_act"] = a_name
                    st.session_state["active_id"] = sel_n

            # 顯示附件
            if st.session_state.get("active_id") == sel_n:
                cur = st.session_state.get("active_act")
                if cur and cur in acts:
                    st.success(f"📍 正在辦理：{cur}")
                    st.info("請確認以下附件是否已備妥：")
                    for item in acts[cur]:
                        st.checkbox(item, key=f"ck_{sel_n}_{cur}_{item}")
            else:
                st.info("👆 請選擇上方辦理項目。")
        else:
            st.info("💡 暫無預設指引。")

except Exception as e:
    st.error(f"系統啟動失敗：{e}")

# 7. 底層數據
st.divider()
with st.expander("📊 原始數據總表"):
    st.dataframe(df)
