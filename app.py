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

    # --- 4. 抓取主表資料 ---
    target_main = sub_main[sub_main.iloc[:, 2] == sel_name].iloc[0]
    permit_id = str(target_main.iloc[1])
    expiry_date = str(target_main.iloc[3])
    clean_date = expiry_date[:10] if expiry_date != 'nan' else "未設定"

    # --- 5. 主畫面標題 ---
    st.title(f"📄 {sel_name}")
    st.info(f"🆔 管制編號：{permit_id}　|　📅 到期日期：{clean_date}")
    
    st.divider()

    # --- 6. 🚀 第三層：複選辦理項目 (質感複選框) ---
    db_info = file_df[file_df.iloc[:, 0] == sel_type]
    options = db_info.iloc[:, 1].dropna().unique().tolist()

    if options:
        st.subheader("🛠️ 請勾選辦理項目 (可多選)")
        # 使用 multiselect 達成複選，且具有高質感標籤效果
        selected_actions = st.multiselect("選取的項目：", options, default=None, placeholder="請選擇一項或多項辦理項目...")

        # --- 7. 第四層：動態合併附件與上傳欄位 ---
        if selected_actions:
            st.write(f"### 📂 辦理清單：{', '.join(selected_actions)}")
            
            # 用來存儲所有合併後的附件（使用 set 避免重複）
            all_attachments = set()
            steps_content = []

            for action in selected_actions:
                action_data = db_info[db_info.iloc[:, 1] == action].iloc[0]
                # 蒐集步驟說明
                step_text = str(action_data.iloc[2])
                if step_text != 'nan':
                    steps_content.append(f"**【{action}】**: {step_text}")
                
                # 蒐集附件 (從 D 欄以後)
                items = action_data.iloc[3:].dropna().tolist()
                for i in items:
                    all_attachments.add(i)

            # 顯示合併後的步驟說明
            with st.container(border=True):
                st.write("**💡 綜合辦理步驟說明：**")
                for step in steps_content:
                    st.write(step)
            
            st.divider()
            st.write("**📋 請上傳下列合併後的檢附資料：**")
            
            # 顯示合併後的所有上傳欄位
            if all_attachments:
                # 轉回 list 並排序，確保顯示整齊
                sorted_attachments = sorted(list(all_attachments))
                for idx, item in enumerate(sorted_attachments, 1):
                    with st.expander(f"附件 {idx}：{item}", expanded=True):
                        st.file_uploader(f"請上傳 - {item}", key=f"upload_{item}")
            else:
                st.info("所選項目無需檢附額外附件。")
        else:
            st.warning("👈 請先在上方勾選至少一項辦理項目。")
    else:
        st.warning(f"⚠️ 資料庫中找不到『{sel_type}』的辦理項目")

except Exception as e:
    st.error(f"❌ 系統錯誤：{e}")
