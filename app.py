import streamlit as st
import pandas as pd

# 1. 頁面設定
st.set_page_config(page_title="環保證照管理系統", layout="wide")

# 2. 資料連結
URL = "https://docs.google.com/spreadsheets/d/1BA427GfGw41UWen083KSWxbdRwbe3a1SEF_H89MyBZE/export?format=xlsx"
SHEET_NAME = "大豐既有許可證到期提醒"

@st.cache_data(show_spinner=False)
def load_data():
    df = pd.read_excel(URL, sheet_name=SHEET_NAME)
    df.columns = df.columns.astype(str).str.strip()
    # 轉換日期格式
    if "到期日期" in df.columns:
        df["到期日期"] = pd.to_datetime(df["到期日期"], errors="coerce")
    return df

try:
    df = load_data()

    # --- 3. 側邊欄 (Sidebar) ---
    st.sidebar.markdown("## 📂 系統導覽")
    
    # 選擇類型
    sel_type = st.sidebar.selectbox("選擇類型", sorted(df["許可證類型"].dropna().unique().tolist()))
    sub_df = df[df["許可證類型"] == sel_type].copy()

    # --- 🚀 關鍵核心：在選單清單裡就直接把日期接上去 ---
    def make_label(row):
        name = str(row["許可證名稱"])
        dt = row["到期日期"]
        dt_str = dt.strftime("%Y-%m-%d") if pd.notna(dt) else "未設定"
        return f"{name} ({dt_str})"

    # 建立一個「顯示名稱」到「原始列索引」的對應，保證點選精準
    sub_df["display_name"] = sub_df.apply(make_label, axis=1)
    
    # 左側單選按鈕呈現「名稱 (日期)」
    sel_display = st.sidebar.radio("選擇許可證", sub_df["display_name"].tolist())

    # --- 4. 主畫面呈現 ---
    # 根據選中的 display_name 反推原始資料
    target_row = sub_df[sub_df["display_name"] == sel_display].iloc[0]

    # ✅ 標題直接顯示選中的文字（內含日期）
    st.title(f"📄 {sel_display}")

    # 呈現管制編號
    st.markdown(f"### 管制編號：{target_row['管制編號']}")
    
    st.divider()

    # --- 5. 數據總表 ---
    with st.expander("📊 數據總表"):
        # 顯示時把暫存的 display_name 欄位拔掉
        st.dataframe(sub_df.drop(columns=["display_name"]), use_container_width=True, hide_index=True)

except Exception as e:
    st.error(f"執行失敗：{e}")
