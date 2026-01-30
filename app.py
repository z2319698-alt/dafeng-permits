import streamlit as st
import pandas as pd

st.set_page_config(page_title="環保證照管理系統", layout="wide")

URL = (
    "https://docs.google.com/spreadsheets/d/"
    "1BA427GfGw41UWen083KSWxbdRwbe3a1SEF_H89MyBZE"
    "/export?format=xlsx"
)

SHEET_NAME = "大豐既有許可證到期提醒"

@st.cache_data(show_spinner=False)
def load_main_table():
    df = pd.read_excel(URL, sheet_name=SHEET_NAME)
    return df

df = load_main_table()

# ===== 欄位清理 =====
df.columns = df.columns.astype(str).str.strip()
for col in ["許可證類型", "許可證名稱", "管制編號"]:
    if col in df.columns:
        df[col] = df[col].astype(str).str.strip()

if "到期日期" in df.columns:
    df["到期日期"] = pd.to_datetime(df["到期日期"], errors="coerce")

# ===== Sidebar 導覽 =====
st.sidebar.markdown("## 📂 系統導覽")

sel_type = st.sidebar.selectbox(
    "選擇類型",
    sorted(df["許可證類型"].dropna().unique().tolist())
)

sub_df = df[df["許可證類型"] == sel_type].copy()

sel_name = st.sidebar.radio(
    "選擇許可證",
    sub_df["許可證名稱"].dropna().tolist()
)

# ===== 主畫面：精準呈現標題與副標題 =====
st.title(f"📄 {sel_name}")

# 直接從 sub_df 中找到對應名稱的那一行
target = sub_df[sub_df["許可證名稱"] == sel_name]

if not target.empty:
    res = target.iloc[0]
    # 格式化日期為 2027-02-10 這種純文字
    date_str = res["到期日期"].strftime("%Y-%m-%d") if pd.notna(res["到期日期"]) else "未設定"
    
    # 【關鍵：直接呈現你要求的文字格式】
    # 字體大小稍微小於標題，使用 h3 級別
    st.markdown(f"### 管制編號：{res['管制編號']}  到期日期：{date_str}")
else:
    # 萬一名稱對應失敗，顯示警告以供除錯
    st.warning("⚠️ 系統無法在總表中找到此許可證的詳細資料，請檢查名稱是否包含隱藏空格。")

# 保留原本的提示與數據總表
st.divider()

with st.expander("📊 數據總表"):
    st.dataframe(sub_df, use_container_width=True, hide_index=True)
