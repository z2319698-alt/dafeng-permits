import streamlit as st
import pandas as pd

st.set_page_config(page_title="環保證照管理系統", layout="wide")

URL = (
    "https://docs.google.com/spreadsheets/d/"
    "1BA427GfGw41UWen083KSWxbdRwbe3a1SEF_H89MyBZE"
    "/export?format=xlsx"
)

# 你新增的那個專門用來匹配的分頁名稱
MATCH_SHEET = "選擇許可證"
# 原始資料的分頁名稱
DATA_SHEET = "大豐既有許可證到期提醒"

@st.cache_data(show_spinner=False)
def load_all_data():
    # 同時讀取兩個分頁
    all_data = pd.read_excel(URL, sheet_name=None)
    master_df = all_data.get(DATA_SHEET)
    match_df = all_data.get(MATCH_SHEET)
    
    # 統一清理欄位與字串空白
    for df in [master_df, match_df]:
        if df is not None:
            df.columns = df.columns.astype(str).str.strip()
            df = df.applymap(lambda x: str(x).strip() if isinstance(x, str) else x)
    
    # 轉換日期格式
    if "到期日期" in match_df.columns:
        match_df["到期日期"] = pd.to_datetime(match_df["到期日期"], errors="coerce")
        
    return master_df, match_df

try:
    master, match_db = load_all_data()

    # 1. 側邊欄：從原始資料表抓取類型與名稱
    st.sidebar.markdown("## 📂 系統導覽")
    sel_type = st.sidebar.selectbox("選擇類型", sorted(master["許可證類型"].unique()))
    sub_df = master[master["許可證類型"] == sel_type]
    sel_name = st.sidebar.radio("選擇許可證", sub_df["許可證名稱"].unique())

    # 2. 主畫面標題
    st.title(f"📄 {sel_name}")

    # 3. 副標題呈現：去「選擇許可證」分頁匹配
    # 這裡直接用 sel_name 去匹配「選擇許可證」分頁裡的名稱欄位
    hit = match_db[match_db["名稱"] == sel_name] 

    if not hit.empty:
        r = hit.iloc[0]
        p_no = r["管制編號"]
        # 處理日期顯示
        exp_dt = r["到期日期"].strftime("%Y-%m-%d") if pd.notna(r["到期日期"]) else "未設定"
        
        # ✅ 在標題正下方噴出你要的格式
        st.markdown(f"#### 管制編號：{p_no}　　到期日期：{exp_dt}")
    else:
        # 如果匹配失敗，顯示這行字讓你確認 Excel 內容
        st.write(f"⚠️ 找不到匹配項：請確認『{MATCH_SHEET}』分頁中有『{sel_name}』這個名稱")

    st.divider()

    # 4. 下方原本的數據表格
    with st.expander("📊 查看詳細數據總表"):
        st.dataframe(sub_df, use_container_width=True, hide_index=True)

except Exception as e:
    st.error(f"讀取分頁時出錯，請確認分頁名稱是否正確：{e}")
