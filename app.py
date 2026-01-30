import streamlit as st
import pandas as pd
from datetime import datetime as dt

# ================= 基本設定 =================
st.set_page_config(
    page_title="大豐環保證照管理系統",
    layout="wide"
)

DATA_URL = (
    "https://docs.google.com/spreadsheets/d/"
    "1BA427GfGw41UWen083KSWxbdRwbe3a1SEF_H89MyBZE"
    "/export?format=xlsx"
)

# ================= 資料讀取 =================
@st.cache_data(show_spinner=False)
def load_data():
    sheets = pd.read_excel(DATA_URL, sheet_name=None)

    main_df = None
    attach_df = None

    for name, df in sheets.items():
        if "許可證名稱" in df.columns:
            main_df = df.copy()
        if "附件" in name or "檢查表" in name:
            attach_df = df.copy()

    if main_df is None:
        raise ValueError("找不到包含『許可證名稱』的數據總表")

    # 日期處理
    if "到期日期" in main_df.columns:
        main_df["到期日期"] = pd.to_datetime(
            main_df["到期日期"], errors="coerce"
        )

    return main_df, attach_df


df, attach_db = load_data()
now = dt.now()

# ================= Sidebar =================
st.sidebar.markdown("## 📂 系統導航")

# 選擇類型
permit_types = sorted(df["許可證類型"].dropna().unique())
sel_type = st.sidebar.selectbox(
    "選擇類型",
    permit_types
)

# 依類型篩選許可證
sub_df = df[df["許可證類型"] == sel_type]

sel_name = st.sidebar.radio(
    "選擇許可證",
    sub_df["許可證名稱"].tolist()
)

# ================= 跑馬燈（快到期） =================
if "到期日期" in df.columns:
    urgent = df[
        (df["到期日期"].notna()) &
        (df["到期日期"] <= now + pd.Timedelta(days=60))
    ]

    if not urgent.empty:
        txt = "　　".join([
            f"🚨 {r['許可證名稱']}（剩 {(r['到期日期']-now).days} 天）"
            for _, r in urgent.iterrows()
        ])
        st.markdown(
            f"""
            <div style="background:#ff4b4b;
                        color:white;
                        padding:10px;
                        border-radius:6px;">
            <marquee>{txt}</marquee>
            </div>
            """,
            unsafe_allow_html=True
        )

# ================= 主畫面 =================
st.title(f"📄 {sel_name}")

# ===== 直接顯示「數據總表」資料（你要的重點）=====
row = df[df["許可證名稱"] == sel_name]

if row.empty:
    st.warning("⚠️ 數據總表中找不到該許可證資料")
else:
    r = row.iloc[0]

    st.markdown("### 📌 許可證基本資料")

    c1, c2, c3 = st.columns(3)

    with c1:
        st.metric(
            "管制編號",
            str(r.get("管制編號", "—"))
        )

    with c2:
        exp = r.get("到期日期")
        if pd.notna(exp):
            st.metric(
                "許可證到期日期",
                exp.strftime("%Y-%m-%d")
            )
        else:
            st.metric("許可證到期日期", "未設定")

    with c3:
        if pd.notna(exp):
            st.metric(
                "剩餘天數",
                f"{(exp - now).days} 天"
            )
        else:
            st.metric("剩餘天數", "—")

    st.divider()

# =================（以下：可選，之後再用）=================
# 這一段你可以留著、關掉、或之後再接流程
with st.expander("📊 數據總表（該類型全部許可證）"):
    st.dataframe(
        sub_df,
        use_container_width=True,
        hide_index=True
    )
