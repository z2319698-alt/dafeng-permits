import streamlit as st
import pandas as pd
from datetime import date

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

    # --- 5. 主畫面標題 ---
    st.title(f"📄 {sel_name}")
    st.info(f"🆔 管制編號：{permit_id}　|　📅 到期日期：{clean_date}")
    
    st.divider()

    # --- 6. 橫向複選按鈕 ---
    db_info = file_df[file_df.iloc[:, 0] == sel_type]
    options = db_info.iloc[:, 1].dropna().unique().tolist()

    if options:
        st.markdown("### 🛠️ 第一步：選擇辦理項目")
        if "selected_actions" not in st.session_state:
            st.session_state.selected_actions = set()

        cols = st.columns(len(options))
        for i, option in enumerate(options):
            is_active = option in st.session_state.selected_actions
            if cols[i].button(option, key=f"btn_{option}", use_container_width=True, 
                              type="primary" if is_active else "secondary"):
                if is_active: st.session_state.selected_actions.remove(option)
                else: st.session_state.selected_actions.add(option)
                st.rerun()

        # --- 7. 上傳與資訊填寫區 ---
        current_list = st.session_state.selected_actions
        if current_list:
            st.divider()
            st.markdown("### 📝 第二步：填寫申請資訊與上傳附件")
            
            # ✅ 新增：同仁姓名與申請日期
            c1, c2 = st.columns(2)
            with c1:
                user_name = st.text_input("👤 申請人姓名", placeholder="請輸入姓名")
            with c2:
                apply_date = st.date_input("📅 提出申請日期", value=date.today())

            # 合併附件
            final_attachments = set()
            for action in current_list:
                action_row = db_info[db_info.iloc[:, 1] == action]
                if not action_row.empty:
                    attachments = action_row.iloc[0, 3:].dropna().tolist()
                    for item in attachments:
                        final_attachments.add(str(item).strip())

            # 上傳區域
            st.write("**📋 附件上傳：**")
            uploaded_files = {}
            for item in sorted(list(final_attachments)):
                uploaded_files[item] = st.file_uploader(f"請上傳 - {item}", key=f"up_{item}")

            st.divider()

            # --- 8. 🚀 提出申請按鈕 ---
            st.markdown("### 📤 第三步：送出申請")
            if st.button("🚀 點我提出申請", use_container_width=True, type="primary"):
                if not user_name:
                    st.warning("⚠️ 請填寫申請人姓名後再送出！")
                else:
                    # 這裡建立 Mail 連結
                    subject = f"【許可證申請】{sel_name}_{user_name}_{apply_date}"
                    body = f"您好，\n\n同仁 {user_name} 已於 {apply_date} 提出申請。\n" \
                           f"許可證：{sel_name}\n" \
                           f"辦理項目：{', '.join(current_list)}\n\n" \
                           f"附件清單：\n" + "\n".join([f"- {f}" for f in final_attachments])
                    
                    # 產生 mailto 連結（自動開啟 Outlook/Gmail）
                    import urllib.parse
                    mailto_link = f"mailto:andy.chen@df-recycle.com?subject={urllib.parse.quote(subject)}&body={urllib.parse.quote(body)}"
                    
                    st.success(f"✅ 申請資訊已彙整完畢！")
                    st.markdown(f"**[請點擊此處開啟郵件軟體發送給 Andy]({mailto_link})**")
                    st.info("💡 註：由於瀏覽器限制，請點擊上方連結後，將剛才上傳的檔案拖進郵件附件中發出。")

        else:
            st.write("👆 請點擊上方按鈕開始辦理。")

except Exception as e:
    st.error(f"❌ 系統錯誤：{e}")
