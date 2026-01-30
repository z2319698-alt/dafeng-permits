import streamlit as st
import pandas as pd
from datetime import datetime as dt

st.set_page_config(page_title="大豐管理系統", layout="wide")

URL = "https://docs.google.com/spreadsheets/d/1BA427GfGw41UWen083KSWxbdRwbe3a1SEF_H89MyBZE/export?format=xlsx"

def load_data_raw():
    all_sh = pd.read_excel(URL, sheet_name=None)

    main_df = None
    attach_df = None

    # 找附件表（名稱包含 檢查表 或 附件）
    for n, df in all_sh.items():
        if ("檢查表" in str(n)) or ("附件" in str(n)):
            attach_df = df
            break

    # 找主表（欄位包含 許可證名稱）
    for n, df in all_sh.items():
        if "許可證名稱" in df.columns:
            main_df = df
            break

    # 清理附件表：只做 ffill + strip，不把 NaN 變成字串 "nan"
    if attach_df is not None and not attach_df.empty:
        attach_df = attach_df.copy()

        # A/B 欄 ffill（類型、項目）
        attach_df.iloc[:, 0] = attach_df.iloc[:, 0].ffill()
        attach_df.iloc[:, 1] = attach_df.iloc[:, 1].ffill()

        # 對 object 欄位做 strip（保留 NaN）
        for col in attach_df.columns:
            if attach_df[col].dtype == "object":
                attach_df[col] = attach_df[col].map(lambda x: x.strip() if isinstance(x, str) else x)

    return main_df, attach_df


def reset_step_state():
    """切換項目/類型時，清掉舊的 checkbox / uploader / 附件勾選狀態，避免 session_state 殘留"""
    for k in list(st.session_state.keys()):
        if k.startswith("F_") or k.startswith("UP_"):
            del st.session_state[k]
    # radio/選列也清掉，確保第一步不會沿用舊選擇
    st.session_state.pop("C_RADIO", None)
    st.session_state.pop("selected_idx", None)


try:
    df, attach_db = load_data_raw()

    if df is None or df.empty:
        st.error("主資料表讀取失敗：找不到包含『許可證名稱』欄位的工作表。")
        st.stop()

    C_NAME, C_DATE, C_TYPE = "許可證名稱", "到期日期", "許可證類型"
    df["D_OBJ"] = pd.to_datetime(df[C_DATE], errors="coerce")
    now = dt.now()

    # --- 跑馬燈 ---
    urgent = df[(df["D_OBJ"] <= now + pd.Timedelta(days=180)) & (df["D_OBJ"].notnull())]
    if not urgent.empty:
        m_txt = "　　".join([f"🚨 {r[C_NAME]}(剩{(r['D_OBJ']-now).days}天)" for _, r in urgent.iterrows()])
        st.markdown(
            f'<div style="background:#ff4b4b;color:white;padding:10px;border-radius:5px;">'
            f'<marquee scrollamount="6">{m_txt}</marquee></div>',
            unsafe_allow_html=True
        )

    # --- 側邊選單 ---
    type_list = sorted(df[C_TYPE].dropna().unique().tolist())
    if not type_list:
        st.error("主資料表內找不到任何『許可證類型』。")
        st.stop()

    sel_t = st.sidebar.selectbox("1. 選擇類型", type_list, key="SEL_TYPE")

    sub = df[df[C_TYPE] == sel_t].reset_index(drop=True)
    if sub.empty:
        st.warning("此類型沒有許可證資料。")
        st.stop()

    sel_n = st.sidebar.radio("2. 選擇許可證", sub[C_NAME].tolist(), key="SEL_PERMIT")

    st.title(f"📄 {sel_n}")
    st.divider()

    if attach_db is None or attach_db.empty:
        st.warning("找不到附件/檢查表工作表，或附件表為空。")
        st.stop()

    # --- 按鈕項目 (B 欄) ---
    # A欄=類型, B欄=項目
    acts = (
        attach_db[attach_db.iloc[:, 0] == sel_t]
        .iloc[:, 1]
        .dropna()
        .astype(str)
        .map(lambda x: x.strip())
        .unique()
        .tolist()
    )

    acts = [a for a in acts if a != ""]

    if not acts:
        st.warning("附件表中，此類型沒有任何『項目(B欄)』。")
        st.stop()

    st.subheader("🛠️ 項目選擇")
    cols = st.columns(len(acts))

    # 初始化/自動選第一個項目（避免 cur_a 空掉）
    if "cur_a" not in st.session_state:
        st.session_state["cur_a"] = acts[0]
        reset_step_state()

    for i, a in enumerate(acts):
        if cols[i].button(a, key=f"B_{a}"):
            # 切換項目時清 state，避免舊勾選污染
            st.session_state["cur_a"] = a
            reset_step_state()
            st.rerun()

    curr_a = st.session_state["cur_a"]
    st.info(f"目前項目：{curr_a}")

    # 篩選出該項目的所有列：A=類型，B=項目
    target_rows = attach_db[(attach_db.iloc[:, 0] == sel_t) & (attach_db.iloc[:, 1] == curr_a)]

    if target_rows.empty:
        st.warning("附件表中找不到該『類型 + 項目』對應的資料列。")
        st.stop()

    # --- 第一步：C 欄 單選（radio） ---
    st.markdown("### ⚖️ 第一步：條件確認 (C 欄)")

    c_options = []
    for idx, row in target_rows.iterrows():
        c_val = row.iloc[2]  # C 欄
        if pd.notna(c_val) and str(c_val).strip() != "":
            c_options.append((idx, str(c_val).strip()))

    if not c_options:
        st.warning("此項目在 C 欄沒有可選條件（C 欄為空）。")
        selected_idx = None
    else:
        labels = [lab for _, lab in c_options]
        choice_label = st.radio("請選擇辦理條件", labels, index=0, key="C_RADIO")
        selected_idx = next(idx for idx, lab in c_options if lab == choice_label)
        st.session_state["selected_idx"] = selected_idx

        # Debug：你可以留著確認是不是抓到你要的那一列（例如 D9）
        st.caption(f"Debug：選到列 index = {selected_idx} / C欄 = {attach_db.loc[selected_idx].iloc[2]}")

    # --- 第二步：姓名 ---
    st.markdown("### 👤 第二步：人員登錄")
    u_name = st.text_input("輸入姓名以解鎖附件清單", key="U_NAME").strip()

    # --- 第三步：D-I 欄附件（只顯示「單一選列」的 D~I） ---
    if u_name and (selected_idx is not None):
        st.divider()
        st.markdown("### 📂 第三步：應檢附附件 (D-I 欄)")

        # 只抓「被選到那一列」的 D~I 欄（0:A,1:B,2:C,3:D...8:I）
        row_data = attach_db.loc[selected_idx].iloc[3:9].tolist()

        final_files = []
        for f in row_data:
            if pd.notna(f) and str(f).strip() != "":
                final_files.append(str(f).strip())

        # 去重（保留順序）
        final_files = list(dict.fromkeys(final_files))

        if final_files:
            for f_name in final_files:
                c1, c2 = st.columns([0.7, 0.3])
                c1.checkbox(f_name, key=f"F_{selected_idx}_{f_name}")
                c2.file_uploader("上傳", key=f"UP_{selected_idx}_{f_name}", label_visibility="collapsed")

            if st.button("🚀 送出申請"):
                st.success("已彙整，請發信！")
        else:
            st.warning("Excel 中此條件未設定附件（D~I 欄為空）。")

    elif u_name and (selected_idx is None):
        st.warning("👈 請先在第一步選擇辦理條件！")

except Exception as e:
    st.error(f"系統崩潰: {e}")
