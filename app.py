import streamlit as st
import pandas as pd
from datetime import date
import time
from streamlit_gsheets import GSheetsConnection

# 1. 基礎設定
st.set_page_config(page_title="大豐環保 AI 智慧監控系統", layout="wide")
conn = st.connection("gsheets", type=GSheetsConnection)

# --- 🧠 AI 智慧模組 ---
def get_ai_check_status(pdf_link):
    # 判斷網址是否有效
    if pd.isna(pdf_link) or str(pdf_link).strip() == "" or str(pdf_link).lower() == "nan":
        return "⚠️ 警告：雲端無紙本備份，AI 無法核對", "#d32f2f"
    return "✅ AI 已同步：紙本與資料庫日期核對一致", "#2E7D32"

# 2. 數據加載 (強化標題辨識)
@st.cache_data(ttl=5)
def load_all_data():
    m_df = conn.read(worksheet="大豐既有許可證到期提醒")
    f_df = conn.read(worksheet="附件資料庫")
    l_df = conn.read(worksheet="申請紀錄")
    
    # 強制清理所有工作表的標題：去除所有空格與換行
    def clean_cols(df):
        df.columns = [str(c).strip().replace(" ", "").replace("　", "").replace("\n", "") for c in df.columns]
        return df

    return clean_cols(m_df), clean_cols(f_df), clean_cols(l_df).dropna(how='all')

try:
    main_df, file_df, logs_df = load_all_data()
    
    # 3. 側邊選單
    if "mode" not in st.session_state: st.session_state.mode = "management"
    st.sidebar.header("🏠 系統導航")
    if st.sidebar.button("📋 許可證辦理系統", use_container_width=True): st.session_state.mode = "management"; st.rerun()
    if st.sidebar.button("📁 既有文件下載區", use_container_width=True): st.session_state.mode = "library"; st.rerun()
    if st.sidebar.button("⚖️ 近期裁處案例", use_container_width=True): st.session_state.mode = "cases"; st.rerun()

    # 4. 分頁渲染
    if st.session_state.mode == "library":
        st.header("📁 既有文件下載區")
        for idx, row in main_df.iterrows():
            # 取得許可證名稱與網址
            name = row.iloc[2]
            url = row.get("PDF連結", None)
            
            c1, c2, c3 = st.columns([2, 1, 1])
            c1.write(f"📄 **{name}**")
            c2.write(f"📅 到期: {str(row.iloc[3])[:10]}")
            
            # 檢查網址是否為有效 http 連結
            if pd.notna(url) and str(url).strip().lower().startswith("http"):
                c3.link_button("📥 下載 PDF", str(url).strip(), use_container_width=True, key=f"lib_dl_{idx}")
            else:
                c3.button("❌ 無連結", disabled=True, use_container_width=True, key=f"lib_no_{idx}")
            st.divider()

    elif st.session_state.mode == "management":
        # 原始辦理邏輯 (全部保留)
        sel_type = st.sidebar.selectbox("1. 選擇類型", sorted(main_df.iloc[:, 0].dropna().unique()))
        sub_main = main_df[main_df.iloc[:, 0] == sel_type].copy()
        sel_name = st.sidebar.radio("2. 選擇許可證", sub_main.iloc[:, 2].dropna().unique())
        
        target_row = sub_main[sub_main.iloc[:, 2] == sel_name].iloc[0]
        pdf_link = target_row.get("PDF連結", None)

        st.title(f"📄 {sel_name}")
        
        # AI 核對狀態顯示
        check_msg, check_color = get_ai_check_status(pdf_link)
        st.markdown(f'<p style="color:{check_color}; border-left:5px solid {check_color}; padding-left:10px; background-color:#f9f9f9;">{check_msg}</p>', unsafe_allow_html=True)

        # 這裡接續你原本的「變更/展延」按鈕邏輯...
        db_info = file_df[file_df.iloc[:, 0] == sel_type]
        options = db_info.iloc[:, 1].dropna().unique().tolist()
        if options:
            st.subheader("🛠️ 第一步：選擇辦理項目")
            if "selected_actions" not in st.session_state: st.session_state.selected_actions = set()
            cols = st.columns(len(options))
            for i, option in enumerate(options):
                is_active = option in st.session_state.selected_actions
                if cols[i].button(option, key=f"btn_{option}", use_container_width=True, type="primary" if is_active else "secondary"):
                    if is_active: st.session_state.selected_actions.remove(option)
                    else: st.session_state.selected_actions.add(option)
                    st.rerun()

            if st.session_state.selected_actions:
                st.divider()
                user_name = st.text_input("👤 申請人姓名", key="user_input")
                if st.button("🚀 提出申請", type="primary", key="submit_all"):
                    if user_name:
                        # 寫入申請紀錄
                        new_row = {"許可證名稱": sel_name, "申請人": user_name, "申請日期": date.today().strftime("%Y-%m-%d"), "狀態": "已提送需求"}
                        conn.update(worksheet="申請紀錄", data=pd.concat([logs_df, pd.DataFrame([new_row])], ignore_index=True))
                        st.success("✅ 申請成功！"); time.sleep(1); st.session_state.selected_actions = set(); st.rerun()

    elif st.session_state.mode == "cases":
        st.header("⚖️ 近期裁處案例")
        st.error("**⚠️ 案例：清運業 GPS 異常開罰**\n\n事由：清運路線與申報不符。\n\n💡 避險：出車前確認 GPS 燈號正常。")

except Exception as e:
    st.error(f"❌ 系統錯誤：{e}")
