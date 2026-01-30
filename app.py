import streamlit as st
import pandas as pd

# 設定頁面寬度
st.set_page_config(page_title="環保證照管理系統", layout="wide")

# 固定連結與分頁名稱
URL = "https://docs.google.com/spreadsheets/d/1BA427GfGw41UWen083KSWxbdRwbe3a1SEF_H89MyBZE/export?format=xlsx"
SHEET_NAME = "大豐既有許可證到期提醒"

@st.cache_data(show_spinner=False)
def load_data():
    # 讀取 Excel
    df = pd.read_excel(URL, sheet_name=SHEET_NAME)
    # 清理欄位空白
    df.columns = df.columns.astype(str).str.strip()
    # 轉換日期格式 (針對 E 欄 到期日期)
    if "到期日期" in df.columns:
        df["到期日期"] = pd.to_datetime(df["到期日期"], errors="coerce")
    return df

try:
    df = load_data()

    # --- 1. 左側選單 (Sidebar) ---
    st.sidebar.markdown("## 📂 系統導覽")
    
    # 選擇類型
    types = sorted(df["許可證類型"].dropna().unique().tolist())
    sel_type = st.sidebar.selectbox("選擇類型", types)
    
    # 根據類型過濾資料
    sub_df = df[df["許可證類型"] == sel_type].copy()
    
    # 選擇許可證名稱
    names = sub_df["許可證名稱"].dropna().tolist()
    sel_name = st.sidebar.radio("選擇許可證", names)

    # --- 2. 核心改動：直接抓取對應資料列 ---
    # 根據左側選中的 sel_name，直接從 sub_df 抓出那一列
    target_row = sub_df[sub_df["許可證名稱"] == sel_name].iloc[0]
    
    # 格式化到期日期 (E 欄)
    if pd.notna(target_row["到期日期"]):
        date_str = target_row["到期日期"].strftime("%Y-%m-%d")
    else:
        date_str = "未設定"

    # ✅ 你要的：在標題後面加上到期日期
    # 呈現效果：📄 大豐全興廠空污操作許可 (2027-02-10)
    st.title(f"📄 {sel_name} ({date_str})")

    # --- 3. 標題下方副標題：呈現管制編號 ---
    st.markdown(f"#### 管制編號：{target_row['管制編號']}")
    
    st.divider()

    # --- 4. 數據總表 (展開後可看全表) ---
    with st.expander("📊 數據總表", expanded=False):
        st.dataframe(sub_df, use_container_width=True, hide_index=True)

except Exception as e:
    st.error(f"系統讀取失敗，錯誤原因：{e}")
