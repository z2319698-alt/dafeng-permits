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

    # --- 3. 側邊選單 ---
    st.sidebar.markdown("## 📂 系統導覽")
    sel_type = st.sidebar.selectbox("1. 選擇類型", sorted(main_df.iloc[:, 0].dropna().unique()))
    sub_main = main_df[main_df.iloc[:, 0] == sel_type].copy()
    sel_name = st.sidebar.radio("2. 選擇許可證", sub_main.iloc[:, 2].dropna().unique())

    # --- 4. 抓取主表資料 ---
    target_main = sub_main[sub_main.iloc[:, 2] == sel_name].iloc[0]
    permit_id = str(target_main.iloc[1])
    expiry_date = str(target_main.iloc[3])
    clean_date = expiry_date[:10] if expiry_date != 'nan' else "未設定"

    # --- 5. 主畫面呈現 ---
    st.title(f"📄 {sel_name}")
    st.info(f"🆔 管制編號：{permit_id}　|　📅 到期日期：{clean_date}")
    
    st.divider()

    # --- 6. 🚀 第三層：橫向按鈕 (複選模式) ---
    db_info = file_df[file_df.iloc[:, 0] == sel_type]
    options = db_info.iloc[:, 1].dropna().unique().tolist()

    if options:
        st.subheader("🛠️ 請選擇辦理項目 (可多選)")
        
        # 初始化 Session State 來儲存選中的項目
        if "selected_options" not in st.session_state:
            st.session_state.selected_options = set()

        # 做出橫向按鈕
        cols = st.columns(len(options))
        for i, option in enumerate(options):
            # 判斷按鈕顏色：選中為 primary，未選為 secondary
            is_selected = option in st.session_state.selected_options
            if cols[i].button(
                option, 
                key=f"btn_{option}", 
                use_container_width=True, 
                type="primary" if is_selected else "secondary"
            ):
                # 點擊切換狀態
                if is_selected:
                    st.session_state.selected_options.remove(option)
                else:
                    st.session_state.selected_options.add(option)
                st.rerun() # 點擊後立即刷新畫面

        # --- 7. 第四層：顯示合併後的附件 ---
        current_selections = st.session_state.selected_options
        
        if current_selections:
            st.write(f"### 📂 已選項目：{', '.join(current_selections)}")
            
            all_attachments = set()
            
            for action in current_selections:
                action_data = db_info[db_info.iloc[:, 1] == action].iloc[0]
                # 蒐集附件
                items = action_data.iloc[3:].dropna().tolist()
                for i in items:
                    all_attachments.add(i)
            
            st.divider()
            st.write("**📋 請上傳檢附資料：**")
            
            if all_attachments:
                # 排序顯示，視覺更整齊
                for idx, item in enumerate(sorted(list(all_attachments)), 1):
                    with st.expander(f"附件 {idx}：{item}", expanded=True):
                        st.file_uploader(f"請上傳 - {item}", key=f"file_{item}")
            else:
                st.info("所選項目無需附件。")
        else:
            st.write("👉 請點擊上方按鈕選擇辦理項目。")
    else:
        st.warning(f"⚠️ 找不到『{sel_type}』的辦理項目")

except Exception as e:
    st.error(f"❌ 系統錯誤：{e}")
