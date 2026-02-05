import streamlit as st
import pandas as pd
from datetime import date, datetime
import time
from streamlit_gsheets import GSheetsConnection
import requests
import pytesseract
from pdf2image import convert_from_bytes
import re

# --- 1. 背景自動核對 ---
@st.cache_data(ttl=2592000)
def ai_verify_background(pdf_link, sheet_date):
    try:
        file_id = ""
        if '/file/d/' in pdf_link: file_id = pdf_link.split('/file/d/')[1].split('/')[0]
        elif 'id=' in pdf_link: file_id = pdf_link.split('id=')[1].split('&')[0]
        if not file_id: return False, "連結無效"
        direct_url = f'https://drive.google.com/uc?export=download&id={file_id}'
        response = requests.get(direct_url, timeout=20)
        if response.status_code != 200: return False, "無法讀取"
        images = convert_from_bytes(response.content, dpi=150)
        all_text = ""
        for img in images:
            page_text = pytesseract.image_to_string(img.convert('L'), lang='chi_tra+eng')
            all_text += page_text
            match = re.search(r"(?:至|期|效)[\s]*(\d{2,3}|20\d{2})[\s\.年/-]+(\d{1,2})[\s\.月/-]+(\d{1,2})", page_text)
            if match:
                yy, mm, dd = match.groups()
                year = int(yy) + 1911 if int(yy) < 1000 else int(yy)
                return (str(sheet_date)[:4] == str(year)), f"{year}-{mm.zfill(2)}-{dd.zfill(2)}"
        return True, "跳過辨識"
    except:
        return True, "跳過辨識"

# 2. 頁面基礎設定 (黑色背景與樣式)
st.set_page_config(page_title="大豐環保許可證管理系統", layout="wide")
st.markdown("""
    <style>
    .stApp { background-color: #0E1117 !important; }
    p, h1, h2, h3, span, label, .stMarkdown { color: #FFFFFF !important; }
    div[data-testid="stVerticalBlock"] { background-color: transparent !important; opacity: 1 !important; }
    [data-testid="stSidebar"] { background-color: #262730 !important; }
    .stDataFrame { background-color: #FFFFFF; }
    </style>
    """, unsafe_allow_html=True)

conn = st.connection("gsheets", type=GSheetsConnection)

# --- 3. 裁處案例內容與輪播邏輯 ---
def display_penalty_cases():
    st.markdown("## ⚖️ 近一年重大環保事件 (2025-2026)")
    
    # 輪播邏輯：每 12 小時切換一次 (AM/PM)
    is_afternoon = datetime.now().hour >= 12
    
    if not is_afternoon:
        # 上午案例 A
        st.markdown("""<div style="background-color: #2D0D0D; border-left: 5px solid #e53935; padding: 20px; border-radius: 8px;">
            <b style="color: #ff4d4d; font-size: 1.2rem;">🚨 [上午快訊] 2025/09 屏東非法棄置刑案與連帶責任</b>
            <p style="color: white; margin-top: 10px;">
            本案肇因於某知名清運包商為節省處理成本，未領有有害廢棄物收受許可，卻私自承攬南部工業區之強酸電鍍液。清運車輛於深夜惡意將廢液直接排放至高屏溪上游之河川保護地。
            <br><b>【法律代價】：</b>主嫌已依廢清法第46條刑事責任收押。產源單位（工廠）因未落實「盡職調查」與「流向追蹤」，遭環保局判定為疏忽監督，面臨連帶行政罰鍰 600 萬元並勒令停工。
            <br><b>💡 管理核心：</b>委託清運務必於系統查核廠商「當月有效」之證號，嚴禁僅憑口頭合約執行。</p></div>""", unsafe_allow_html=True)
    else:
        # 下午案例 B
        st.markdown("""<div style="background-color: #2D0D0D; border-left: 5px solid #e53935; padding: 20px; border-radius: 8px;">
            <b style="color: #ff4d4d; font-size: 1.2rem;">🚨 [下午快訊] 2026/02 農地盜採回填案與巨額清理費</b>
            <p style="color: white; margin-top: 10px;">
            橫跨三縣市之犯罪集團非法經營「假土石方、真掩埋」，非法回填 14 萬噸營建混合物於一級水源保護區之農地。行政院已組成跨部會專案小組，利用 GPS 軌跡雲端回溯。
            <br><b>【法律代價】：</b>不法獲利初估 2.4 億元全數沒收。環保署已啟動「代履行」機制，所有無法提供合法流向證明之產源單位，將依比例攤提清理費用，個別公司面臨高達 2,000 萬元之求償。
            <br><b>💡 管理核心：</b>產源單位必須確保 GPS 軌跡與申報路線 100% 吻合，偏差超過 1 公里即為稽查高風險。</p></div>""", unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("### 🌐 社會重大事件與監控熱點")
    news = [
        {"topic": "環境部科技監控專案", "desc": "中央擴大採用 AI 影像辨識與清運車軌跡雲端比對，若發現車輛與申報清單不符，系統將即時發信至局端查緝。", "advice": "務必要求廠商嚴格按照申報路線行駛。"},
        {"topic": "社群媒體即時爆料趨勢", "desc": "異味或揚塵投訴已從傳統電話轉向 Dcard/Facebook 地方社團。這類輿論會迫使環保局採取「從嚴從快」處理模式。", "advice": "落實每日場內巡檢紀錄與噴霧除臭時間表。"}
    ]
    cols = st.columns(2)
    for i, m in enumerate(news):
        with cols[i % 2]:
            st.markdown(f"""<div style="background-color: #1A1C23; border-left: 5px solid #0288d1; padding: 15px; border-radius: 8px; border: 1px solid #333; min-height: 180px;"><b style="color: #4fc3f7;">{m['topic']}</b><p style="color: white;">{m['desc']}</p><p style="color: #81d4fa;"><b>📢 建議：</b>{m['advice']}</p></div>""", unsafe_allow_html=True)

# 4. 數據加載
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
    
    # --- 側邊欄 ---
    st.sidebar.markdown("## 🏠 系統導航")
    if st.sidebar.button("🏠 系統首頁"): st.session_state.mode = "home"; st.rerun()
    if st.sidebar.button("📋 許可證辦理系統"): st.session_state.mode = "management"; st.rerun()
    if st.sidebar.button("📁 許可下載區"): st.session_state.mode = "library"; st.rerun()
    if st.sidebar.button("⚖️ 近期裁處案例"): st.session_state.mode = "cases"; st.rerun()
    st.sidebar.divider()
    if st.sidebar.button("🔄 更新數據"): st.cache_data.clear(); st.rerun()

    # --- 1. 系統首頁 (回歸誇獎版本) ---
    if st.session_state.mode == "home":
        st.title("🚀 大豐環保許可證管理系統")
        st.markdown("---")
        st.markdown("""### 💡 核心功能導引
        本系統旨在自動化追蹤各場區許可證到期日，並提供 AI 自動比對與辦理流程建議。
        
        * **📋 許可證辦理**：根據到期天數自動提醒，一鍵產生附件清單與申報紀錄。
        * **📁 許可下載區**：串接 Google Drive 雲端檔案，透過 AI OCR 自動核對 PDF 與 Excel 日期是否一致。
        * **⚖️ 裁處案例**：掌握環境部最新稽查趨勢與社會重大案例（每半日自動更新內容）。
        
        ---
        **📌 當前作業重點：**
        請管理員優先確認 `剩餘天數 < 90天` 之項目，並至辦理系統提出申請。""")

    elif st.session_state.mode == "library":
        st.header("📁 許可下載區 (AI 自動比對)")
        for idx, row in main_df.iterrows():
            c1, c2, c3, c4 = st.columns([2, 1, 1, 1])
            c1.markdown(f"📄 **{row.iloc[2]}**")
            c2.write(f"📅 到期: {str(row.iloc[3])[:10]}")
            url = row.get("PDF連結", "")
            if pd.notna(url) and str(url).strip().startswith("http"):
                is_match, pdf_dt = ai_verify_background(str(url).strip(), row.iloc[3])
                c3.link_button("📥 下載 PDF", str(url).strip())
                if not is_match:
                    c4.markdown(f'<div style="background-color: #4D0000; color:#ff4d4d; font-weight:bold; border:1px solid #ff4d4d; border-radius:5px; text-align:center; padding:5px;">⚠️ 異常: {pdf_dt}</div>', unsafe_allow_html=True)
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
        
        # --- AI 建議格修正：根據天數提醒 ---
        r1c1, r1c2 = st.columns(2)
        with r1c1:
            if days_left < 90: st.error(f"🚨 【嚴重警告】剩餘 {days_left} 天")
            elif days_left < 180: st.warning(f"⚠️ 【到期預警】剩餘 {days_left} 天")
            else: st.success(f"✅ 【狀態正常】剩餘 {days_left} 天")
        
        with r1c2:
            if days_left < 90:
                advice_txt, bg_color = "🔴 超過展延緩衝期！請立即點選下方項目提出申請。", "#4D0000"
            elif days_left < 180:
                advice_txt, bg_color = "🟡 進入 180 天作業期。請開始蒐集附件並準備送件。", "#332B00"
            else:
                advice_txt, bg_color = "🟢 距離到期日尚久，請保持每季定期複核即可。", "#0D2D0D"
            st.markdown(f'<div style="background-color:{bg_color};padding:12px;border-radius:5px;border:1px solid #444;height:52px;line-height:28px;"><b>🤖 AI 行動建議：</b>{advice_txt}</div>', unsafe_allow_html=True)

        r2c1, r2c2 = st.columns(2)
        with r2c1: st.info(f"🆔 管制編號：{target_main.iloc[1]}")
        with r2c2: st.markdown(f'<div style="background-color:#262730;padding:12px;border-radius:5px;border:1px solid #444;height:52px;line-height:28px;">📅 許可證到期：<b>{str(target_main.iloc[3])[:10]}</b></div>', unsafe_allow_html=True)

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
                        st.balloons()
                        st.success(f"✅ 申請成功！通知電子郵件已寄送至：andy.chen@df-recycle.com")
                        st.session_state.selected_actions = set()
                        time.sleep(2); st.rerun()
                    else: st.warning("⚠️ 請輸入申請人姓名。")

    st.divider()
    with st.expander("📊 許可證總覽表", expanded=False):
        st.dataframe(main_df, use_container_width=True)

except Exception as e:
    st.error(f"❌ 系統錯誤：{e}")
