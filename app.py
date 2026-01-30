import streamlit as st
import pandas as pd
from datetime import datetime as dt

st.set_page_config(page_title="大豐管理系統", layout="wide")

URL = "https://docs.google.com/spreadsheets/d/1BA427GfGw41UWen083KSWxbdRwbe3a1SEF_H89MyBZE/export?format=xlsx"

# ========= 資料讀取 =========
def load_data_raw():
    all_sh = pd.read_excel(URL, sheet_name=None)

    main_df = None
    attach_df = None

    for _, df in all_sh.items():
        if "許可證名稱" in df.columns:
            main_df = df
        if any(k in str(_) for k in ["附件", "檢查表"]):
            attach_df = df

    if attach_df is not None:
        attach_df = attach_df.copy()
        attach_df.iloc[:, 0] = attach_df.iloc[:, 0].ffill()
        attach_df.iloc[:, 1] = attach_df.iloc[:, 1].ffill()

        for c in attach_df.columns:
            if attach_df[c].dtype == "object":
                attach_df[c] = attach_df[c].map(lambda x: x.strip() if isinstance(x, str) else x)

    return main_df, attach_df


# ========= 初始化 =========
df, attach_db = load_data_raw()

C_NAME = "許可證名稱"
C_TYPE = "許可證類型"
C_DATE = "到期日期"

df["D_OBJ"] = pd.to_datetime(df[C_DATE], errors="coerce")
now = dt.now()

# ========= 跑馬燈 =========
urgent = df[(df["D_OBJ"] <= now + pd.Timedelta(days=180)) & df["D_OBJ"].notna()]
if not urgent.empty:
    msg = "　　".join(
        [f"🚨 {r[C_NAME]}（剩 {(r['D_OBJ']-now).days} 天）" for _, r in urgent.iterrows()]
    )
    st.markdown(
        f'<div style="background:#ff4b4b;color:white;padding:10px;border-radius:5px;">'
        f'<marquee scrollamount="6">{msg}</marquee></div>',
        unsafe_allow_html=True
    )

# ========= 側邊欄 =========
sel_type = st.sidebar.selectbox(
    "1️⃣ 選擇許可證類型",
    sorted(df[C_TYPE].dropna().unique())
)

sub_df = df[df[C_TYPE] == sel_type]
sel_name = st.sidebar.radio(
    "2️⃣ 選擇許可證",
    sub_df[C_NAME].tolist()
)

permit_row = sub_df[sub_df[C_NAME] == sel_name].iloc[0]

# ========= 主畫面 =========
st.title(f"📄 {sel_name}")

# ====== 許可證基本資料區塊 ======
st.markdown("### 📌 許可證基本資料")
c1, c2, c3 = st.columns(3)

with c1:
    st.metric("管制編號", permit_row.get("管制編號", "—"))

with c2:
    exp = permit_row.get(C_DATE)
    if pd.notna(exp):
        st.metric("許可證到期日期", pd.to_datetime(exp).strftime("%Y-%m-%d"))
    else:
        st.metric("許可證到期日期", "未設定")

with c3:
    if pd.notna(permit_row["D_OBJ"]):
        days_left = (permit_row["D_OBJ"] - now).days
        st.metric("剩餘天數", f"{days_left} 天")
    else:
        st.metric("剩餘天數", "—")

st.divider()

# ========= 辦理項目 =========
acts = (
    attach_db[attach_db.iloc[:, 0] == sel_type]
    .iloc[:, 1]
    .dropna()
    .unique()
    .tolist()
)

st.subheader("🛠️ 辦理項目")
cols = st.columns(len(acts))

if "cur_act" not in st.session_state:
    st.session_state["cur_act"] = acts[0]

for i, a in enumerate(acts):
    if cols[i].button(a):
        st.session_state["cur_act"] = a
        st.rerun()

cur_act = st.session_state["cur_act"]
st.info(f"目前辦理項目：{cur_act}")

# ========= 附件顯示 =========
target_row = attach_db[
    (attach_db.iloc[:, 0] == sel_type) &
    (attach_db.iloc[:, 1] == cur_act)
].iloc[0]

st.markdown("### 📂 應檢附附件")

files = [
    f for f in target_row.iloc[3:9].tolist()
    if pd.notna(f) and str(f).strip() != ""
]

if not files:
    st.warning("此辦理項目未設定附件")
else:
    for f in files:
        c1, c2 = st.columns([0.7, 0.3])
        c1.checkbox(f, key=f"chk_{cur_act}_{f}")
        c2.file_uploader("上傳", key=f"up_{cur_act}_{f}", label_visibility="collapsed")

    if st.button("🚀 送出申請"):
        st.success("附件已彙整完成")
