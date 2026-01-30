import streamlit as st
import pandas as pd

# 1. 頁面基礎設定
st.set_page_config(page_title="大豐許可證管理系統", layout="wide")

# 2. 資料來源
URL = "https://docs.google.com/spreadsheets/d/1BA427GfGw41UWen083KSWxbdRwbe3a1SEF_H89MyBZE/export?format=xlsx"

@st.cache_data(ttl=5)
def load_all_data():
    main_df = pd.read_excel(URL, sheet_name="大豐既有許可證到期提醒")
    file_df = pd.read_excel(URL, sheet_name="附件資料庫")
    main_df.columns = [str(c).strip() for c in main_df.columns]
    file_df.columns = [str(c).strip() for c in file_df.columns]
    return main_df, file_df

try:
    main_df, file_df = load_all_data()

    # --- 3. 側邊選單 (第一、二層) ---
    st.sidebar.markdown("## 📂 系統導覽")
    sel_type = st.sidebar.selectbox("1. 選擇類型", sorted(main_df.iloc[:, 0].dropna().unique()))
    sub_main = main_df[main_df.iloc[:, 0] == sel_type].copy()
    sel_name = st.sidebar.radio("2. 選擇許可證", sub_main.iloc[:, 2].dropna().unique())

    # --- 4. 抓取主表資料 (B欄編號, D欄日期) ---
    target_main = sub_main[sub_main.iloc[:, 2] == sel_name].iloc[0]
    permit_id = str(target_main.iloc[1])
    expiry_date = str(target_main.iloc[3])
    clean_date = expiry_date[:10] if expiry_date != 'nan' else "未設定"

    # --- 5. 主畫面標題 ---
    st.title(f"📄 {sel_name}")
    st.info(f"🆔 管制編號：{permit_id}　|　📅 到期日期：{clean_date}")
    
    st.divider()

    # --- 6. 🚀 第三層：質感按鈕 (辦理項目選擇) ---
    db_info = file_df[file_df.iloc[:, 0] == sel_type]
    options = db_info.iloc[:, 1].dropna().unique().tolist()

    if options:
        st.subheader("🛠️ 請選擇辦理項目")
        
        # 使用 columns 做出橫向按鈕質感
        cols = st.columns(len(options))
        selected_action = None
        
        # 利用 session_state 紀錄點選了哪一個按鈕
        if "active_btn" not in st.session_state:
            st.session_state.active_btn = options[0]

        for i, option in enumerate(options):
            if cols[i].button(option, use_container_width=True, type="primary" if st.session_state.active_btn == option else "secondary"):
                st.session_state.active_btn = option
        
        sel_action = st.session_state.active_btn

        # --- 7. 第四層：顯示附件 + 上傳欄位 ---
        if sel_action:
            st.markdown(f"### 📂 正在辦理：{sel_action}")
            action_data = db_info[db_info.iloc[:, 1] == sel_action].iloc[0]
            
            # 辦理說明
            with st.container(border=True):
                st.write("**💡 辦理步驟說明：**")
                st.write(action_data.iloc[2] if str(action_data.iloc[2]) != 'nan' else "無特別說明")
            
            st.write("**📋 請上傳下列檢附資料：**")
            # 抓取 D 欄之後的所有附件名稱
            attachments = action_data.iloc[3:].dropna().tolist()
            
            if attachments:
                for idx, item in enumerate(attachments, 1):
                    # 每一項附件都給一個獨立的上傳框，這樣才有「質感」
                    with st.expander(f"第 {idx} 項：{item}", expanded=True):
                        st.file_uploader(f"點擊或拖曳檔案上傳 - {item}", key=f"file_{sel_action}_{idx}")
            else:
                st.info("此項目無需檢附額外附件。")
    else:
        st.warning(f"⚠️ 資料庫中找不到『{sel_type}』的辦理項目")

except Exception as e:
    st.error(f"❌ 系統錯誤：{e}")
