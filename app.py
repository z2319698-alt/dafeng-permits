import streamlit as st
import pandas as pd
from datetime import datetime as dt

st.set_page_config(page_title="DEBUG-證照系統", layout="wide")

URL = (
    "https://docs.google.com/spreadsheets/d/"
    "1BA427GfGw41UWen083KSWxbdRwbe3a1SEF_H89MyBZE"
    "/export?format=xlsx"
)

# ===== 讀資料 =====
@st.cache_data(show_spinner=False)
def load_data():
    sheets = pd.read_excel(URL, sheet_name=None)
    main_df = None
    for name, df in sheets.items():
        if "許可證名稱" in df.columns:
            main_df = df.copy()
    if main_df is None:
        raise ValueError("❌ 找不到包含『許可證名稱』的工作表")
    return main_df

df = load_data()

# ===== 強制顯示 df 狀態（證據 1）=====
st.write("🔍 數據總表欄位：", df.columns.tolist())
st.write("🔍 數據總表筆數：", len(df))

# ===== Sidebar =====
st.sidebar.header("系統導航")

sel_type = st.sidebar.selectbox(
    "選擇類型（DEBUG）",
    df["許可證類型"].dropna().unique().tolist()
)

sub_df = df[df["許可證類型"] == sel_type]

sel_name = st.sidebar.radio(
    "選擇許可證（DEBUG）",
    sub_df["許可證名稱"].tolist()
)

# ===== 主畫面 =====
st.title(f"📄 {sel_name}")

# ===== 再顯示一次目前選到什麼（證據 2）=====
st.write("👉 目前選到的類型：", sel_type)
st.write("👉 目前選到的許可證名稱：", sel_name)

# ===== 關鍵：數據總表顯示 =====
row = df[df["許可證名稱"] == sel_name]

st.write("🔍 篩選後 row 是否為空：", row.empty)
st.write("🔍 篩選後 row：")
st.dataframe(row)

if not row.empty:
    r = row.iloc[0]

    st.markdown("## 📌 許可證基本資料（一定會顯示）")

    c1, c2, c3 = st.columns(3)

    with c1:
        st.metric("管制編號", str(r.get("管制編號", "—")))

    with c2:
        exp = r.get("到期日期")
        st.metric(
            "到期日期",
            exp.strftime("%Y-%m-%d") if pd.notna(exp) else "未設定"
        )

    with c3:
        if pd.notna(exp):
            st.metric("剩餘天數", f"{(exp - pd.Timestamp.now()).days} 天")
        else:
            st.metric("剩餘天數", "—")
else:
    st.error("❌ row 是空的，代表主表中沒有這個『許可證名稱』")
