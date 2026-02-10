import streamlit as st
import pandas as pd
from datetime import date, datetime
import time
import smtplib
from email.mime.text import MIMEText
from email.header import Header
from streamlit_gsheets import GSheetsConnection

# 1. 頁面基礎設定 (必須是第一個 Streamlit 指令)
st.set_page_config(page_title="大豐環保許可證管理系統", layout="wide")

# 2. 初始化登入狀態
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

# 3. 員工登入頁面邏輯 (畫面集中在中間)
if not st.session_state.logged_in:
    empty_l, login_col, empty_r = st.columns([1, 1.5, 1])
    with login_col:
        st.write("#")
        st.write("#")
        with st.container(border=True):
            st.title("🔐 員工登入")
            st.markdown("請輸入認證資訊以進入大豐許可證管理系統")
            emp_id = st.text_input("👤 員工編號", placeholder="例如: DF001", key="login_id")
            emp_pwd = st.text_input("🔑 登入密碼", type="password", placeholder="****", key="login_pw")
            st.write("#")
            if st.button("登入系統", use_container_width=True, type="primary"):
                if emp_id == "DF001" and emp_pwd == "1234":
                    st.session_state.logged_in = True
                    st.success("✅ 登入成功！")
                    time.sleep(0.5)
                    st.rerun()
                else:
                    st.error("❌ 員編或密碼錯誤")
            st.caption("💡 忘記密碼請洽系統管理員 Andy")
    st.stop() # 沒登入就此煞車，不跑後面的程式碼

# --- 4. 引用零件 (登入成功後才會執行到這裡) ---
try:
    from ai_engine import ai_verify_background
    from ui_components import display_penalty_cases
except ImportError:
    st.error("❌ 找不到核心零件，請確認 ai_engine.py 與 ui_components.py 是否已在根目錄。")
    st.stop()

# --- 5. 系統核心樣式與邏輯 (完全保留你原本的設定) ---

st.markdown("""
    <style>
    .stApp { background-color: #0E1117 !important; }
    p, h1, h2, h3, span, label, .stMarkdown { color: #FFFFFF !important; }
    [data-testid="stSidebar"] { background-color: #262730 !important; }
    .stDataFrame { background-color: #FFFFFF; }
    @keyframes marquee { 0% { transform: translateX(100%); } 100% { transform: translateX(-100%); } }
    .marquee-container {
        overflow: hidden; white-space: nowrap; background: #4D0000; color: #FF4D4D;
        padding: 10px 0; font-weight: bold; border: 1px solid #FF4D4D; border-radius: 5px; margin-bottom: 20px;
    }
    .marquee-text { display: inline-block; animation: marquee 15s linear infinite; }
    </style>
    """, unsafe_allow_html=True)

conn = st.connection("gsheets", type=GSheetsConnection)

@st.cache_data(ttl=5)
def load_all_data():
    m_df = conn.read(worksheet="大豐既有許可證到期提醒")
    f_df = conn.read(worksheet="附件資料庫")
    m_df.columns = [str(c).strip().replace(" ", "").replace("\n", "") for c in m_df.columns]
    f_df.columns = [str(c).strip().replace(" ", "").replace("\n", "") for c in f_df.columns]
    m_df.iloc[:, 3] = pd.to_datetime(m_df.iloc[:, 3], errors='coerce')
    return m_df, f_df

try:
    main_df, file_df = load_all_data()
    today = pd.Timestamp(date.today())
    
    if "mode" not in st.session_state: st.session_state.mode = "home"
    if "selected_actions" not in st.session_state: st.session_state.selected_actions = set()

    # 逾期警報跑馬燈
    expired_items = main_df[main_df.iloc[:, 3] < today].iloc[:, 2].tolist()
    if expired_items:
        st.markdown(f"""<div class="marquee-container"><div class="marquee-text">🚨 警告：以下許可證已逾期，請立即處理：{" / ".join(expired_items)} 🚨</div></div>""", unsafe_allow_html=True)

    # 側邊導航
    st.sidebar.markdown(f"## 👤 使用者: DF001")
    if st.sidebar.button("🏠 系統首頁", key="nav_home"): st.session_state.mode = "home"; st.rerun()
    if st.sidebar.button("📋 許可證辦理系統", key="nav_mgmt"): st.session_state.mode = "management"; st.rerun()
    if st.sidebar.button("📁 許可下載區", key="nav_lib"): st.session_state.mode = "library"; st.rerun()
    if st.sidebar.button("⚖️ 近期裁處案例", key="nav_case"): st.session_state.mode = "cases"; st.rerun()
    st.sidebar.divider()
    if st.sidebar.button("🔄 更新資料庫", key="nav_refresh"): st.cache_data.clear(); st.rerun()
    if st.sidebar.button("🚪 登出系統", key="nav_logout"): 
        st.session_state.logged_in = False
        st.rerun()

    # --- 頁面內容分流 ---
    if st.session_state.mode == "home":
        st.title("🚀 大豐環保許可證管理系統")
        st.markdown("---")
        st.markdown("### 💡 核心功能導引\n* **📋 許可證辦理**：警示到期日並準備附件。\n* **📁 許可下載區**：AI 自動核對，異常可【原地修正】。\n* **⚖️ 裁處案例**：掌握環境部最新稽查趨勢。")

    elif st.session_state.mode == "cases":
        display_penalty_cases() 

    elif st.session_state.mode == "library":
        st.header("📁 許可下載區 (管理員保護模式)")
        admin_pass_input = st.text_input("🔑 請輸入管理員密碼以存取檔案", type="password", key="lib_pwd")
        correct_password = st.secrets.get("admin_pass", "dafeng888")

        if admin_pass_input == correct_password:
            st.success("✅ 認證成功")
            st.divider()
            for idx, row in main_df.iterrows():
                c1, c2, c3, c4 = st.columns([2, 1, 1, 1])
                p_name, p_date, url = row.iloc[2], row.iloc[3], row.get("PDF連結", "")
                c1.markdown(f"📄 **{p_name}**")
                c2.write(f"📅 到期: {str(p_date)[:10] if pd.notnull(p_date) else '無'}")
                if pd.notna(url) and str(url).strip().startswith("http"):
                    is_match, pdf_dt, pdf_img = ai_verify_background(str(url).strip(), p_date)
                    c3.link_button("📥 下載 PDF", str(url).strip())
                    if not is_match:
                        with c4: st.markdown(f'<div style="background-color: #4D0000; color:#ff4d4d; font-weight:bold; border:1px solid #ff4d4d; border-radius:5px; text-align:center; padding:5px;">⚠️ 異常: {pdf_dt}</div>', unsafe_allow_html=True)
                        with st.expander(f"🛠️ 修正 {p_name}"):
                            col_img, col_fix = st.columns([2, 1])
                            if pdf_img: col_img.image(pdf_img, use_container_width=True)
                            new_date = col_fix.date_input("正確到期日", value=p_date.date() if pd.notnull(p_date) else date.today(), key=f"fix_date_{idx}")
                            if col_fix.button("確認修正", key=f"btn_confirm_{idx}", type="primary", use_container_width=True):
                                main_df.loc[idx, main_df.columns[3]] = pd.to_datetime(new_date)
                                conn.update(worksheet="大豐既有許可證到期提醒", data=main_df)
                                st.success("已更新！"); st.cache_data.clear(); time.sleep(1); st.rerun()
                    else:
                        c4.markdown('<div style="background-color: #0D2D0D; color:#4caf50; font-weight:bold; text-align:center; padding:5px; border-radius:5px; border:1px solid #4caf50;">✅ 一致</div>', unsafe_allow_html=True)
                st.divider()
        elif admin_pass_input != "":
            st.error("❌ 密碼錯誤")
        else:
            st.info("💡 為了確保許可證文件安全，此頁面需密碼解鎖。")

    elif st.session_state.mode == "management":
        st.sidebar.divider()
        sel_type = st.sidebar.selectbox("1. 選擇類型", sorted(main_df.iloc[:, 0].dropna().unique()))
        sub_main = main_df[main_df.iloc[:, 0] == sel_type].copy()
        sel_name = st.sidebar.radio("2. 選擇許可證", sub_main.iloc[:, 2].dropna().unique())
        target_main = sub_main[sub_main.iloc[:, 2] == sel_name].iloc[0]
        st.title(f"📄 {sel_name}")
        
        days_left = (target_main.iloc[3] - today).days
        r1_c1, r1_c2 = st.columns(2)
        with r1_c1:
            if days_left < 0: st.error(f"❌ 【已經逾期】 過期 {abs(days_left)} 天")
            elif days_left < 90: st.error(f"🚨 【嚴重警告】 剩餘 {days_left} 天")
            elif days_left < 180: st.warning(f"⚠️ 【到期預警】 剩餘 {days_left} 天")
            else: st.success(f"✅ 【狀態有效】 剩餘 {days_left} 天")
        
        with r1_c2:
            adv_txt = "🔴 立即申請" if days_left < 90 else "🟡 準備附件" if days_left < 180 else "🟢 定期複核"
            bg_color = "#4D0000" if days_left < 90 else "#332B00" if days_left < 180 else "#0D2D0D"
            st.markdown(f'<div style="background-color:{bg_color};padding:12px;border-radius:5px;border:1px solid #444;height:52px;line-height:28px;"><b>🤖 AI 建議：</b>{adv_txt}</div>', unsafe_allow_html=True)
        
        st.info(f"🆔 管制編號：{target_main.iloc[1]}  |  📅 許可到期：{str(target_main.iloc[3])[:10]}")
        st.divider()
        
        db_info = file_df[file_df.iloc[:, 0] == sel_type]
        options = db_info.iloc[:, 1].dropna().unique().tolist()
        if options:
            st.subheader("🛠️ 第一步：選擇辦理項目")
            action_cols = st.columns(len(options))
            for i, opt in enumerate(options):
                if action_cols[i].button(opt, key=f"mgmt_btn_{i}", use_container_width=True, 
                                         type="primary" if opt in st.session_state.selected_actions else "secondary"):
                    if opt in st.session_state.selected_actions: st.session_state.selected_actions.remove(opt)
                    else: st.session_state.selected_actions.add(opt)
                    st.rerun()
            
            if st.session_state.selected_actions:
                st.divider(); st.markdown("### 📝 第二步：附件上傳區")
                user_name = st.text_input("👤 申請人姓名", key="user_name_input")
                atts = set()
                for action in st.session_state.selected_actions:
                    rows = db_info[db_info.iloc[:, 1] == action]
                    if not rows.empty:
                        for item in rows.iloc[0, 3:].dropna().tolist(): atts.add(str(item).strip())
                for idx_att, item in enumerate(sorted(list(atts))):
                    with st.expander(f"📁 附件：{item}", expanded=True): 
                        st.file_uploader(f"上傳 - {item}", key=f"file_up_{idx_att}")
                
                if st.button("🚀 提出申請", type="primary", use_container_width=True, key="submit_request"):
                    if user_name:
                        try:
                            history_df = conn.read(worksheet="申請紀錄")
                            new_entry = pd.DataFrame([{"許可證名稱": sel_name, "申請人": user_name, "申請日期": datetime.now().strftime("%Y-%m-%d"), "狀態": "已提送需求", "核准日期": ""}])
                            updated_history = pd.concat([history_df, new_entry], ignore_index=True)
                            conn.update(worksheet="申請紀錄", data=updated_history)
                            
                            subject = f"【許可證申請】{sel_name}_{user_name}_{datetime.now().strftime('%Y-%m-%d')}"
                            body = f"Andy 您好，\n\n同仁 {user_name} 已提交申請。\n許可證：{sel_name}\n辦理項目：{', '.join(st.session_state.selected_actions)}"
                            msg = MIMEText(body, 'plain', 'utf-8'); msg['Subject'] = Header(subject, 'utf-8')
                            msg['From'] = st.secrets["email"]["sender"]; msg['To'] = st.secrets["email"]["receiver"]
                            with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
                                server.login(st.secrets["email"]["sender"], st.secrets["email"]["password"])
                                server.sendmail(st.secrets["email"]["sender"], [st.secrets["email"]["receiver"]], msg.as_string())
                            st.balloons(); st.success(f"✅ 申請成功並寄信給 Andy！"); st.session_state.selected_actions = set(); time.sleep(2); st.rerun()
                        except Exception as err: st.error(f"❌ 流程失敗：{err}")

    st.divider()
    with st.expander("📊 許可證總覽表", expanded=True):
        display_df = main_df.copy()
        display_df.iloc[:, 3] = display_df.iloc[:, 3].apply(lambda x: x.strftime('%Y-%m-%d') if pd.notnull(x) and hasattr(x, 'strftime') else "")
        st.dataframe(display_df, use_container_width=True, hide_index=True)

except Exception as e:
    st.error(f"❌ 系統錯誤：{e}")
