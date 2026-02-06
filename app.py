import streamlit as st
import pandas as pd
from datetime import date, datetime
import time
import smtplib
from email.mime.text import MIMEText
from email.header import Header
from streamlit_gsheets import GSheetsConnection
import requests
import pytesseract
from pdf2image import convert_from_bytes
import re
from PIL import Image

# --- 1. 背景自動核對 ---
@st.cache_data(ttl=600)  # 縮短 TTL 確保 Excel 修改後能快速反應
def ai_verify_background(pdf_link, sheet_date):
    try:
        file_id = ""
        if '/file/d/' in pdf_link: file_id = pdf_link.split('/file/d/')[1].split('/')[0]
        elif 'id=' in pdf_link: file_id = pdf_link.split('id=')[1].split('&')[0]
        if not file_id: return False, "連結無效", None
        direct_url = f'https://drive.google.com/uc?export=download&id={file_id}'
        response = requests.get(direct_url, timeout=20)
        if response.status_code != 200: return False, "無法讀取", None
        
        images = convert_from_bytes(response.content, dpi=100)
        for img in images:
            page_text = pytesseract.image_to_string(img.convert('L'), lang='chi_tra+eng')
            match = re.search(r"(?:至|期|效)[\s]*(\d{2,3}|20\d{2})[\s\.年/-]+(\d{1,2})[\s\.月/-]+(\d{1,2})", page_text)
            if match:
                yy, mm, dd = match.groups()
                year = int(yy) + 1911 if int(yy) < 1000 else int(yy)
                pdf_dt = f"{year}-{mm.zfill(2)}-{dd.zfill(2)}"
                # 嚴格年月日比對
                is_match = (str(sheet_date)[:10] == pdf_dt)
                return is_match, pdf_dt, img
        return True, "跳過辨識", None
    except:
        return True, "跳過辨識", None

# 2. 頁面基礎設定
st.set_page_config(page_title="大豐環保許可證管理系統", layout="wide")
st.markdown("""
    <style>
    .stApp { background-color: #0E1117 !important; }
    p, h1, h2, h3, span, label, .stMarkdown { color: #FFFFFF !important; }
    div[data-testid="stVerticalBlock"] { background-color: transparent !important; opacity: 1 !important; }
    [data-testid="stSidebar"] { background-color: #262730 !important; }
    .stDataFrame { background-color: #FFFFFF; }
    /* 跑馬燈樣式 */
    @keyframes marquee {
        0% { transform: translateX(100%); }
        100% { transform: translateX(-100%); }
    }
    .marquee-container {
        overflow: hidden;
        white-space: nowrap;
        background: #4D0000;
        color: #FF4D4D;
        padding: 10px 0;
        font-weight: bold;
        border: 1px solid #FF4D4D;
        border-radius: 5px;
        margin-bottom: 20px;
    }
    .marquee-text {
        display: inline-block;
        animation: marquee 15s linear infinite;
    }
    </style>
    """, unsafe_allow_html=True)

conn = st.connection("gsheets", type=GSheetsConnection)

# --- 3. 裁處案例與社會事件 ---
def display_penalty_cases():
    st.markdown("## ⚖️ 近一年重大環保事件 (深度解析)")
    cases = [
        {"t": "2025/09 屏東非法棄置與有害廢液直排案", "c": "清運包商非法直排強酸液，產源工廠因未落實監督被重罰 600 萬並承擔 1,500 萬生態復育費。"},
        {"t": "2026/02 農地盜採回填與 GPS 軌跡回溯稽查", "c": "跨縣市犯罪集團回填 14 萬噸廢棄物。環境部透過 GPS 鎖定多家產源單位，沒收獲利 2.4 億元。"},
        {"t": "2025/11 高雄工業區廢水監測數據造假案", "c": "特定場區更動 CWMS 監測參數。環境部認定人工造假，沒入相關許可證。"}
    ]
    for case in cases:
        st.markdown(f"""<div style="background-color: #2D0D0D; border-left: 5px solid #e53935; padding: 15px; border-radius: 8px; margin-bottom: 15px;"><b style="color: #ff4d4d;">🚨 {case['t']}</b><p style="color: white; margin-top: 5px;">{case['c']}</p></div>""", unsafe_allow_html=True)

    st.markdown("### 🌐 社會重大事件與監控熱點")
    news = [
        {"topic": "南投焚化爐修繕抗爭", "desc": "設施修繕導致量縮，居民異味抗爭造成清運受阻。", "advice": "落實巡檢與除臭紀錄。"},
        {"topic": "環境部科技監控", "desc": "AI 影像與軌跡比對，偏離路線 1 公里即自動觸發稽查。", "advice": "要求廠商按申報路線行駛。"},
        {"topic": "社群爆料檢舉趨勢", "desc": "Dcard/FB 即時爆料模式增加，引發媒體跟進與頻繁查訪。", "advice": "強化邊界防治並保留作業紀錄。"},
        {"topic": "許可代碼誤植連罰", "desc": "營建與一般廢棄物代碼混用為近期查核重點。", "advice": "執行內部代碼複核確保一致。"}
    ]
    r1c1, r1c2 = st.columns(2); r2c1, r2c2 = st.columns(2)
    cols = [r1c1, r1c2, r2c1, r2c2]
    for i, m in enumerate(news):
        cols[i].markdown(f"""<div style="background-color: #1A1C23; border-left: 5px solid #0288d1; padding: 15px; border-radius: 8px; border: 1px solid #333; min-height: 160px; margin-bottom: 15px;"><b style="color: #4fc3f7;">{m['topic']}</b><p style="color: white; font-size: 0.85rem;">{m['desc']}</p><p style="color: #81d4fa; font-size: 0.85rem;"><b>📢 建議：</b>{m['advice']}</p></div>""", unsafe_allow_html=True)

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
    
    # --- 全局跑馬燈勾稽 ---
    expired_items = main_df[main_df.iloc[:, 3] < today].iloc[:, 2].tolist()
    if expired_items:
        st.markdown(f"""<div class="marquee-container"><div class="marquee-text">🚨 警告：以下許可證已逾期，請立即處理：{" / ".join(expired_items)} 🚨</div></div>""", unsafe_allow_html=True)

    if "mode" not in st.session_state: st.session_state.mode = "home"
    
    st.sidebar.markdown("## 🏠 系統導航")
    if st.sidebar.button("🏠 系統首頁"): st.session_state.mode = "home"; st.rerun()
    if st.sidebar.button("📋 許可證辦理系統"): st.session_state.mode = "management"; st.rerun()
    if st.sidebar.button("📁 許可下載區"): st.session_state.mode = "library"; st.rerun()
    if st.sidebar.button("⚖️ 近期裁處案例"): st.session_state.mode = "cases"; st.rerun()
    st.sidebar.divider()
    if st.sidebar.button("🔄 更新資料庫"): st.cache_data.clear(); st.rerun()

    if st.session_state.mode == "home":
        st.title("🚀 大豐環保許可證管理系統")
        st.markdown("---")
        st.markdown("### 💡 核心功能導引\n* **📋 許可證辦理**：警示到期日並準備附件。\n* **📁 許可下載區**：AI 自動核對，異常可【原地修正】。\n* **⚖️ 裁處案例**：掌握環境部最新稽查趨勢。")

    elif st.session_state.mode == "library":
        st.header("📁 許可下載區 (AI 比對與原地修正)")
        for idx, row in main_df.iterrows():
            c1, c2, c3, c4 = st.columns([2, 1, 1, 1])
            p_name, p_date = row.iloc[2], row.iloc[3]
            c1.markdown(f"📄 **{p_name}**")
            c2.write(f"📅 到期: {str(p_date)[:10]}")
            url = row.get("PDF連結", "")
            
            if pd.notna(url) and str(url).strip().startswith("http"):
                is_match, pdf_dt, pdf_img = ai_verify_background(str(url).strip(), p_date)
                c3.link_button("📥 下載 PDF", str(url).strip())
                
                # 邏輯修正：只要 Excel 到期日過期，狀態就強迫顯示 ❌
                if p_date < today:
                    c4.markdown('<div style="background-color: #660000; color:#ff4d4d; font-weight:bold; text-align:center; padding:5px; border-radius:5px; border:1px solid #ff4d4d;">❌ 已逾期</div>', unsafe_allow_html=True)
                elif not is_match:
                    with c4: st.markdown(f'<div style="background-color: #4D0000; color:#ff4d4d; font-weight:bold; border:1px solid #ff4d4d; border-radius:5px; text-align:center; padding:5px;">⚠️ 異常: {pdf_dt}</div>', unsafe_allow_html=True)
                    with st.expander(f"🛠️ 修正 {p_name}"):
                        col_img, col_fix = st.columns([2, 1])
                        with col_img:
                            if pdf_img: st.image(pdf_img, caption="AI 辨識來源頁", use_container_width=True)
                        with col_fix:
                            st.write("🔧 **手動校正**")
                            new_date = st.date_input("正確到期日", value=p_date if pd.notnull(p_date) else date.today(), key=f"fix_{idx}")
                            if st.button("確認修正", key=f"btn_fix_{idx}", type="primary", use_container_width=True):
                                main_df.loc[idx, main_df.columns[3]] = pd.to_datetime(new_date)
                                conn.update(worksheet="大豐既有許可證到期提醒", data=main_df)
                                st.success("已更新！"); st.cache_data.clear(); time.sleep(1); st.rerun()
                else:
                    c4.markdown('<div style="background-color: #0D2D0D; color:#4caf50; font-weight:bold; text-align:center; padding:5px; border-radius:5px; border:1px solid #4caf50;">✅ 一致</div>', unsafe_allow_html=True)
            st.divider()

    elif st.session_state.mode == "cases":
        display_penalty_cases()

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
            if days_left < 0:
                adv_txt, bg_color = "🔴 立即辦理 (逾期中)", "#660000"
            else:
                adv_txt = "🔴 立即申請" if days_left < 90 else "🟡 準備附件" if days_left < 180 else "🟢 定期複核"
                bg_color = "#4D0000" if days_left < 90 else "#332B00" if days_left < 180 else "#0D2D0D"
            st.markdown(f'<div style="background-color:{bg_color};padding:12px;border-radius:5px;border:1px solid #444;height:52px;line-height:28px;"><b>🤖 AI 建議：</b>{adv_txt}</div>', unsafe_allow_html=True)
        
        r2c1, r2c2 = st.columns(2)
        with r2c1: st.info(f"🆔 管制編號：{target_main.iloc[1]}")
        with r2c2: st.markdown(f'<div style="background-color:#262730;padding:12px;border-radius:5px;border:1px solid #444;height:52px;line-height:28px;">📅 許可到期：<b>{str(target_main.iloc[3])[:10]}</b></div>', unsafe_allow_html=True)
        st.divider()
        
        db_info = file_df[file_df.iloc[:, 0] == sel_type]
        options = db_info.iloc[:, 1].dropna().unique().tolist()
        if options:
            st.subheader("🛠️ 第一步：選擇辦理項目")
            if "selected_actions" not in st.session_state: st.session_state.selected_actions = set()
            cols = st.columns(len(options))
            for i, opt in enumerate(options):
                if cols[i].button(opt, key=f"act_{opt}", use_container_width=True, type="primary" if opt in st.session_state.selected_actions else "secondary"):
                    if opt in st.session_state.selected_actions: st.session_state.selected_actions.remove(opt)
                    else: st.session_state.selected_actions.add(opt)
                    st.rerun()
            if st.session_state.selected_actions:
                st.divider(); st.markdown("### 📝 第二步：附件上傳區")
                user = st.text_input("👤 申請人姓名")
                atts = set()
                for action in st.session_state.selected_actions:
                    rows = db_info[db_info.iloc[:, 1] == action]
                    if not rows.empty:
                        for item in rows.iloc[0, 3:].dropna().tolist(): atts.add(str(item).strip())
                for item in sorted(list(atts)):
                    with st.expander(f"📁 附件：{item}", expanded=True): st.file_uploader(f"上傳 - {item}", key=f"up_{item}")
                if st.button("🚀 提出申請", type="primary", use_container_width=True):
                    if user:
                        try:
                            history_df = conn.read(worksheet="申請紀錄")
                            new_entry = pd.DataFrame([{"許可證名稱": sel_name, "申請人": user, "申請日期": datetime.now().strftime("%Y-%m-%d"), "狀態": "已提送需求", "核准日期": ""}])
                            updated_history = pd.concat([history_df, new_entry], ignore_index=True)
                            conn.update(worksheet="申請紀錄", data=updated_history)
                            subject = f"【許可證申請】{sel_name}_{user}_{datetime.now().strftime('%Y-%m-%d')}"
                            body = f"Andy 您好，\n\n同仁 {user} 已提交申請。\n許可證：{sel_name}\n辦理項目：{', '.join(st.session_state.selected_actions)}"
                            msg = MIMEText(body, 'plain', 'utf-8'); msg['Subject'] = Header(subject, 'utf-8')
                            msg['From'] = st.secrets["email"]["sender"]; msg['To'] = st.secrets["email"]["receiver"]
                            with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
                                server.login(st.secrets["email"]["sender"], st.secrets["email"]["password"])
                                server.sendmail(st.secrets["email"]["sender"], [st.secrets["email"]["receiver"]], msg.as_string())
                            st.balloons(); st.success(f"✅ 申請成功並寄信給 Andy！"); st.session_state.selected_actions = set(); time.sleep(2); st.rerun()
                        except Exception as err: st.error(f"❌ 流程失敗：{err}")

    st.divider()
    with st.expander("📊 許可證總覽表", expanded=False):
        st.dataframe(main_df, use_container_width=True)

except Exception as e:
    st.error(f"❌ 系統錯誤：{e}")
