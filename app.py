import streamlit as st
import pandas as pd

# 1. 頁面基礎設定
st.set_page_config(page_title="大豐許可證管理系統", layout="wide")

# 2. 資料來源
URL = "https://docs.google.com/spreadsheets/d/1BA427GfGw41UWen083KSWxbdRwbe3a1SEF_H89MyBZE/export?format=xlsx"

@st.cache_data(ttl=5)
def load_all_data():
    # 讀取主表與附件資料庫
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

    # --- 4. 抓取主表資料 (B欄:管制編號, D欄:到期日) ---
    target_main = sub_main[sub_main.iloc[:, 2] == sel_name].iloc[0]
    permit_id = str(target_main.iloc[1]) # B欄
    expiry_date = str(target_main.iloc[3]) # D欄
    clean_date = expiry_date[:10] if expiry_date != 'nan' else "未設定"

    # --- 5. 主畫面呈現 (依據截圖樣式) ---
    st.title(f"📄 {sel_name}")
    st.info(f"🆔 管制編號：{permit_id}　|　📅 到期日期：{clean_date}")
    
    st.divider()

    # --- 6. 橫向按鈕複選區 (質感樣式) ---
    db_info = file_df[file_df.iloc[:, 0] == sel_type]
    options = db_info.iloc[:, 1].dropna().unique().tolist() # B欄辦理項目

    if options:
        st.markdown("### 🛠️ 請選擇辦理項目 (可多選)")
        
        # 使用 session_state 儲存複選結果
        if "selected_actions" not in st.session_state:
            st.session_state.selected_actions = set()

        # 做出橫向按鈕列
        cols = st.columns(len(options))
        for i, option in enumerate(options):
            is_active = option in st.session_state.selected_actions
            # 點擊按鈕切換選中狀態
            if cols[i].button(option, key=f"btn_{option}", use_container_width=True, 
                              type="primary" if is_active else "secondary"):
                if is_active:
                    st.session_state.selected_actions.remove(option)
                else:
                    st.session_state.selected_actions.add(option)
                st.rerun()

        # --- 7. 下一步：顯示對應的合併附件與上傳欄位 ---
        current_list = st.session_state.selected_actions
        if current_list:
            st.markdown(f"#### 📂 已選項目：{', '.join(current_list)}")
            
            # 合併所有需要上傳的附件名稱 (D欄以後)
            final_attachments = set()
            for action in current_list:
                # 安全抓取該辦理項目的資料
                action_row = db_info[db_info.iloc[:, 1] == action]
                if not action_row.empty:
                    # 抓取 D 欄開始的所有非空白內容
                    attachments = action_row.iloc[0, 3:].dropna().tolist()
                    for item in attachments:
                        final_attachments.add(str(item).strip())

            st.write("---")
            st.write("**📋 綜合應檢附附件上傳區：**")
            
            # 顯示上傳欄位
            if final_attachments:
                for idx, item in enumerate(sorted(list(final_attachments)), 1):
                    # 每個附件獨立一個帶有標題的上傳區
                    with st.container(border=True):
                        st.markdown(f"**{idx}. {item}**")
                        st.file_uploader(f"點擊上傳檔案...", key=f"up_{item}")
            else:
                st.info("所選項目無需額外附件。")
        else:
            st.write("👆 請點擊上方按鈕開始辦理。")
    else:
        st.warning(f"⚠️ 在附件資料庫中找不到『{sel_type}』的對應項目")

except Exception as e:
    st.error(f"❌ 系統錯誤：{e}")
