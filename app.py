import streamlit as st
import pandas as pd
from datetime import date
import urllib.parse

# 1. 頁面基礎設定
st.set_page_config(page_title="大豐環保許可證管理系統", layout="wide")

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
    today = pd.Timestamp(date.today())

    # --- 核心邏輯：自動判定狀態 ---
    # 將 D 欄轉為日期格式進行比對
    main_df['判斷日期'] = pd.to_datetime(main_df.iloc[:, 3], errors='coerce')
    
    def check_status(row_date):
        if pd.isna(row_date): return "未設定"
        return "✅ 有效" if row_date >= today else "❌ 已過期"

    # 這裡我們新增一個「系統判定狀態」欄位
    main_df['系統判定狀態'] = main_df['判斷日期'].apply(check_status)

    # --- 📢 跑馬燈功能 (置頂) ---
    upcoming = main_df[main_df['判斷日期'] <= today + pd.Timedelta(days=90)]
    if not upcoming.empty:
        marquee_text = " | ".join([f"⚠️ {row.iloc[2]} 於 {str(row.iloc[3])[:10]} {row['系統判定狀態']}" for _, row in upcoming.iterrows()])
        st.markdown(f"""
            <div style="background-color: #FFF3E0; padding: 10px; border-radius: 5px; border-left: 5px solid #FF9800; overflow: hidden; white-space: nowrap;">
                <marquee scrollamount="5" style="color: #E65100; font-weight: bold;">{marquee_text}</marquee>
            </div>
        """, unsafe_allow_html=True)
        st.write("")

    # --- 🌟 最頂層大標題 ---
    st.markdown("<h1 style='text-align: center; color: #2E7D32;'>🌱 大豐環保許可證管理系統</h1>", unsafe_allow_html=True)
    st.write("---")

    # --- 3. 側邊選單 ---
    st.sidebar.markdown("## 📂 系統導覽")
    sel_type = st.sidebar.selectbox("1. 選擇類型", sorted(main_df.iloc[:, 0].dropna().unique()))
    sub_main = main_df[main_df.iloc[:, 0] == sel_type].copy()
    sel_name = st.sidebar.radio("2. 選擇許可證", sub_main.iloc[:, 2].dropna().unique())

    # --- 4. 抓取主表資料 ---
    target_main = sub_main[sub_main.iloc[:, 2] == sel_name].iloc[0]
    permit_id = str(target_main.iloc[1])
    expiry_date = str(target_main.iloc[3])
    current_status = target_main['系統判定狀態']
    clean_date = expiry_date[:10] if expiry_date != 'nan' else "未設定"

    # --- 5. 許可證資訊呈現 ---
    st.title(f"📄 {sel_name}")
    
    # 根據狀態顯示不同顏色的資訊條
    if "已過期" in current_status:
        st.error(f"🆔 管制編號：{permit_id}　|　📅 到期日期：{clean_date}　|　📢 狀態：{current_status}")
    else:
        st.info(f"🆔 管制編號：{permit_id}　|　📅 到期日期：{clean_date}　|　📢 狀態：{current_status}")
    
    st.divider()

    # --- 6. 橫向按鈕複選區 ---
    db_info = file_df[file_df.iloc[:, 0] == sel_type]
    options = db_info.iloc[:, 1].dropna().unique().tolist()

    if options:
        st.subheader("🛠️ 第一步：選擇辦理項目 (可多選)")
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

        # --- 7. 申請資訊與上傳區 ---
        current_list = st.session_state.selected_actions
        if current_list:
            st.divider()
            st.markdown("### 📝 第二步：填寫申請資訊與附件")
            c1, c2 = st.columns(2)
            with c1: user_name = st.text_input("👤 申請人姓名", placeholder="請輸入姓名")
            with c2: apply_date = st.date_input("📅 提出申請日期", value=date.today())

            final_attachments = set()
            for action in current_list:
                action_row = db_info[db_info.iloc[:, 1] == action]
                if not action_row.empty:
                    attachments = action_row.iloc[0, 3:].dropna().tolist()
                    for item in attachments: final_attachments.add(str(item).strip())

            st.write("**📋 附件上傳區：**")
            for item in sorted(list(final_attachments)):
                with st.expander(f"📁 {item}", expanded=True):
                    st.file_uploader(f"請上傳檔案 - {item}", key=f"up_{item}")

            st.divider()

            # --- 8. 提出申請按鈕 ---
            st.markdown("### 📤 第三步：確認並送出")
            if st.button("🚀 提出申請", type="primary"):
                if not user_name:
                    st.warning("⚠️ 請先填寫申請人姓名！")
                else:
                    subject = f"【許可證申請】{sel_name}_{user_name}_{apply_date}"
                    body = (f"Andy 您好，\n\n同仁 {user_name} 已於 {apply_date} 提交申請。\n"
                            f"許可證：{sel_name}\n"
                            f"辦理項目：{', '.join(current_list)}\n\n"
                            f"附件清單如下：\n" + "\n".join([f"- {f}" for f in final_attachments]))
                    mailto_link = f"mailto:andy.chen@df-recycle.com?subject={urllib.parse.quote(subject)}&body={urllib.parse.quote(body)}"
                    st.success("✅ 申請資訊彙整完畢！")
                    st.link_button("📧 開啟郵件軟體發送給 Andy", mailto_link)
        else:
            st.write("👆 請點擊上方按鈕選擇辦理項目。")
    
    # --- 📊 9. 總表恢復區 (含自動判定狀態) ---
    st.write("---")
    with st.expander("📊 查看許可證管理總表 (系統自動判定效期)"):
        # 整理顯示的欄位，把系統判定的狀態移到前面
        display_df = main_df.copy()
        # 移除判斷用的輔助欄位
        display_df = display_df.drop(columns=['判斷日期'])
        st.dataframe(display_df, use_container_width=True, hide_index=True)

except Exception as e:
    st.error(f"❌ 系統錯誤：{e}")
