import streamlit as st
import pandas as pd
from datetime import date, datetime
import smtplib
import time
from email.mime.text import MIMEText
from email.header import Header
from streamlit_gsheets import GSheetsConnection

# 1. 頁面基礎設定
st.set_page_config(page_title="大豐環保 AI 智慧監控系統", layout="wide")

# 2. 建立連線
conn = st.connection("gsheets", type=GSheetsConnection)

# --- 🧠 AI 智慧模組：近期裁處案例 (針對清運與再利用業強化) ---
def display_penalty_cases():
    st.markdown("## ⚖️ 近一年環保裁處案例重點分享")
    
    # --- 🔴 產業專屬高風險警告區 (置頂) ---
    st.markdown("""
        <div style="background-color: #721c24; padding: 20px; border-radius: 10px; border: 2px solid #f5c6cb; margin-bottom: 25px;">
            <h3 style="color: #f8d7da; margin-top: 0;">🚨 清運與再利用廠 - 核心避險警告</h3>
            <p style="color: #ffffff; font-size: 1.1rem;">
                身為清運與再利用業者，<b>「申報一致性」</b>與<b>「合規貯存」</b>是稽查頻率最高的項目。
                請務必確認收受之廢棄物代碼與許可證內容 100% 吻合。
            </p>
        </div>
    """, unsafe_allow_html=True)

    # 針對行業特性排序案例
    cases = [
        {
            "type": "⚠️ 再利用廠專屬", 
            "law": "廢棄物清理法第 39 條", 
            "reason": "再利用機構收受廢棄物後，未依管理方式規定之用途進行再利用，或貯存量超過許可上限。", 
            "penalty": "罰鍰 NT$ 6,000 ~ 300 萬 (情節嚴重可廢止許可)", 
            "key": "【超量貯存】現場堆置廢塑膠高度或範圍超過許可範圍，被認定為「非法棄置」。",
            "is_top": True
        },
        {
            "type": "⚠️ 清運業者專屬", 
            "law": "廢棄物清理法第 31 條", 
            "reason": "GPS 軌跡異常，或清運車輛未依規定即時聯單申報。", 
            "penalty": "罰鍰 NT$ 6,000 ~ 300 萬", 
            "key": "【申報落差】聯單數量與磅單不符，或清運路線與申報路徑嚴重偏離且無合理說明。",
            "is_top": True
        },
        {
            "type": "通用管理", 
            "law": "廢棄物清理法第 36 條", 
            "reason": "事業廢棄物之貯存、清除、處理方法及設施不符標示規定（如：標示牌破損、字跡模糊）。", 
            "penalty": "罰鍰 NT$ 6,000 ~ 300 萬", 
            "key": "【標示違規】廠內廢塑膠貯存區未標示廢棄物名稱、產源及聯絡人，稽查時直接開罰。",
            "is_top": False
        },
        {
            "type": "通用管理", 
            "law": "環境教育法", 
            "reason": "指派之環保專責人員未依規定參加年度環境教育講習。", 
            "penalty": "罰鍰 NT$ 5,000 ~ 1.5 萬", 
            "key": "【行政疏失】專責人員務必定期檢查環保署公文或信箱，避免漏接講習通知。",
            "is_top": False
        }
    ]
    
    for case in cases:
        # 如果是置頂案例，使用更深、更亮眼的紅色
        bg_color = "#fff5f5" if not case['is_top'] else "#fff0f0"
        border_color = "#e53935" if not case['is_top'] else "#ff1744"
        
        st.markdown(f"""
            <div style="background-color: {bg_color}; border-left: 8px solid {border_color}; padding: 18px; margin-bottom: 20px; border-radius: 8px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <b style="color: {border_color}; font-size: 1.2rem;">[{case['type']}] {case['law']}</b>
                    <span style="background-color: {border_color}; color: white; padding: 2px 10px; border-radius: 20px; font-size: 0.8rem;">{'🚩 核心風險' if case['is_top'] else '📌 注意項目'}</span>
                </div>
                <p style="margin: 10px 0; color: #333; font-size: 1rem;"><b>違規事由：</b>{case['reason']}</p>
                <p style="margin: 5px 0; color: #d32f2f; font-weight: bold;"><b>裁罰風險：</b>{case['penalty']}</p>
                <div style="margin-top: 10px; color: #ffffff; background-color: #1a237e; padding: 10px; border-radius: 5px;">
                    <b>💡 避險核心：</b>{case['key']}
                </div>
            </div>
        """, unsafe_allow_html=True)

# --- 🧠 AI 智慧模組：法規動態牆 (其餘維持不變) ---
def display_ai_law_wall(category):
    law_db = {
        "廢棄物清理計畫書": [
            {"date": "2025/08", "tag": "再利用專點", "content": "再利用機構應全面檢討收受之廢塑膠種類，若涉及跨區收受需注意回報機制。"},
            {"date": "2025/11", "tag": "清運重點", "content": "GPS 裝置應定期檢驗，若訊號不穩導致軌跡斷層，將視為惡意逃避監控。"},
            {"date": "2026/01", "tag": "最新公告", "content": "全面推動電子化合約上傳，再利用廠需檢附年度產製紀錄備查。"}
        ],
        "水污染防治許可證": [
            {"date": "2025/07", "tag": "標準加嚴", "content": "洗條設備之洗滌水排入溝渠前，需符合最新修正之放流水標準。"},
            {"date": "2025/12", "tag": "技術導引", "content": "鼓勵廠區設置雨污分流系統，避免雨水混入廢水導致處理負荷過大。"}
        ]
    }
    updates = law_db.get(category, [{"date": "2025-2026", "tag": "穩定", "content": "目前此類別法規穩定，請依現行法規辦理展延。"}])
    st.markdown(f"### 🛡️ AI 法規動態感知牆 (近一年)")
    cols = st.columns(len(updates))
    for i, item in enumerate(updates):
        with cols[i]:
            st.markdown(f"""<div style="background-color: #f0f4f8; border-left: 5px solid #2E7D32; padding: 15px; border-radius: 8px; box-shadow: 2px 2px 5px rgba(0,0,0,0.1); height: 180px;"><span style="background-color: #2E7D32; color: white; padding: 2px 8px; border-radius: 4px; font-size: 0.8rem;">{item['tag']}</span><p style="margin-top: 10px; color: #1a3a3a; font-weight: bold; font-size: 0.9rem;">📅 {item['date']}</p><p style="color: #333; font-size: 0.85rem; line-height: 1.4;">{item['content']}</p></div>""", unsafe_allow_html=True)

# 3. 數據加載
@st.cache_data(ttl=10)
def load_main_data():
    main_df = conn.read(worksheet="大豐既有許可證到期提醒")
    file_df = conn.read(worksheet="附件資料庫")
    main_df.columns = [str(c).strip() for c in main_df.columns]
    file_df.columns = [str(c).strip() for c in file_df.columns]
    return main_df, file_df

@st.cache_data(ttl=5)
def load_logs():
    try:
        df = conn.read(worksheet="申請紀錄")
        return df.dropna(how='all')
    except:
        return pd.DataFrame(columns=["許可證名稱", "申請人", "申請日期", "狀態", "核准日期"])

# --- 以下邏輯維持一開始代碼的穩定性 ---
try:
    main_df, file_df = load_main_data()
    logs_df = load_logs()
    today = pd.Timestamp(date.today())

    # 判定邏輯
    main_df['判斷日期'] = pd.to_datetime(main_df.iloc[:, 3], errors='coerce')
    def get_real_status(row_date):
        if pd.isna(row_date): return "未設定"
        if row_date < today: return "❌ 已過期"
        elif row_date <= today + pd.Timedelta(days=180): return "⚠️ 準備辦理"
        else: return "✅ 有效"
    main_df['最新狀態'] = main_df['判斷日期'].apply(get_real_status)

    # 跑馬燈
    upcoming = main_df[main_df['最新狀態'].isin(["❌ 已過期", "⚠️ 準備辦理"])]
    if not upcoming.empty:
        marquee_text = " | ".join([f"{row['最新狀態']}：{row.iloc[2]} (到期日: {str(row.iloc[3])[:10]})" for _, row in upcoming.iterrows()])
        st.markdown(f'<div style="background-color: #FFF3E0; padding: 10px; border-radius: 5px; border-left: 5px solid #FF9800; overflow: hidden; white-space: nowrap;"><marquee scrollamount="5" style="color: #E65100; font-weight: bold;">{marquee_text}</marquee></div>', unsafe_allow_html=True)

    st.markdown("<h1 style='text-align: center; color: #2E7D32;'>🌱 大豐環保 AI 智慧監控系統</h1>", unsafe_allow_html=True)
    st.write("---")

    # 側邊選單
    st.sidebar.markdown("## 🏠 系統導航")
    if st.sidebar.button("🔄 刷新資料庫", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

    if "mode" not in st.session_state: st.session_state.mode = "management"
    if st.sidebar.button("📋 許可證辦理系統", use_container_width=True):
        st.session_state.mode = "management"; st.rerun()
    if st.sidebar.button("⚖️ 近期裁處案例", use_container_width=True):
        st.session_state.mode = "cases"; st.rerun()

    # 畫面渲染
    if st.session_state.mode == "cases":
        display_penalty_cases()
        if st.button("⬅️ 返回辦理系統"):
            st.session_state.mode = "management"; st.rerun()
    else:
        # 原始管理頁面
        st.sidebar.divider()
        sel_type = st.sidebar.selectbox("1. 選擇類型", sorted(main_df.iloc[:, 0].dropna().unique()))
        sub_main = main_df[main_df.iloc[:, 0] == sel_type].copy()
        sel_name = st.sidebar.radio("2. 選擇許可證", sub_main.iloc[:, 2].dropna().unique())

        target_main = sub_main[sub_main.iloc[:, 2] == sel_name].iloc[0]
        expiry_date = str(target_main.iloc[3])
        st.title(f"📄 {sel_name}")

        expiry_dt_obj = pd.to_datetime(expiry_date, errors='coerce')
        if not pd.isna(expiry_dt_obj):
            earliest_submit = expiry_dt_obj - pd.Timedelta(days=180)
            start_prep = earliest_submit - pd.Timedelta(days=30)
            display_ai_law_wall(sel_type)
            st.write("")
            c1, c2, c3 = st.columns(3)
            c1.metric("法規投件日(最早)", earliest_submit.strftime('%Y-%m-%d'))
            c2.metric("AI 建議準備日", start_prep.strftime('%Y-%m-%d'))
            days_diff = (earliest_submit - today).days
            if today < start_prep: c3.success(f"時間充裕 (剩 {days_diff} 天)")
            elif start_prep <= today < earliest_submit: c3.warning(f"準備中 (剩 {days_diff} 天)")
            else: c3.error("已可投件！")

        st.divider()
        # 辦理按鈕功能 (保留原始代碼所有按鈕邏輯)
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
                user_name = st.text_input("👤 申請人姓名")
                if st.button("🚀 提出申請", type="primary"):
                    if user_name:
                        new_data = {col: "" for col in logs_df.columns}
                        new_data.update({"許可證名稱": sel_name, "申請人": user_name, "申請日期": date.today().strftime("%Y-%m-%d"), "狀態": "已提送需求"})
                        conn.update(worksheet="申請紀錄", data=pd.concat([logs_df, pd.DataFrame([new_data])], ignore_index=True))
                        st.balloons(); st.success("✅ 申請成功！"); st.cache_data.clear()
                        time.sleep(1); st.session_state.selected_actions = set(); st.rerun()

        # 總表
        st.write("---")
        with st.expander("📊 查看許可證管理總表"):
            st.dataframe(main_df.drop(columns=['判斷日期', '最新狀態'], errors='ignore'), use_container_width=True, hide_index=True)

except Exception as e:
    st.error(f"❌ 系統錯誤：{e}")
