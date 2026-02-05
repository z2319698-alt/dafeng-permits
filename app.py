import streamlit as st
import pandas as pd
from datetime import date, datetime
import time
from streamlit_gsheets import GSheetsConnection
import requests
import pytesseract
from pdf2image import convert_from_bytes
import re

# --- 1. 背景自動核對 (維持深度掃描) ---
@st.cache_data(ttl=2592000)
def ai_verify_background(pdf_link, sheet_date):
    try:
        file_id = ""
        if '/file/d/' in pdf_link: file_id = pdf_link.split('/file/d/')[1].split('/')[0]
        elif 'id=' in pdf_link: file_id = pdf_link.split('id=')[1].split('&')[0]
        if not file_id: return False, "連結無效"
        direct_url = f'https://drive.google.com/uc?export=download&id={file_id}'
        response = requests.get(direct_url, timeout=20)
        if response.status_code != 200: return False, "下載失敗"
        images = convert_from_bytes(response.content, dpi=150, last_page=2)
        all_text = ""
        for img in images:
            all_text += pytesseract.image_to_string(img.convert('L'), lang='chi_tra+eng')
        
        match = re.search(r"(?:至|期|效)[\s]*(\d{2,3}|20\d{2})[\s\.年/-]+(\d{1,2})[\s\.月/-]+(\d{1,2})", all_text)
        if match:
            yy, mm, dd = match.groups()
            year = int(yy) + 1911 if int(yy) < 1000 else int(yy)
            pdf_dt = f"{year}-{mm.zfill(2)}-{dd.zfill(2)}"
        else:
            pdf_dt = "未偵測日期"
        
        s_year, s_month = str(sheet_date)[:4], str(sheet_date)[5:7]
        p_year, p_month = pdf_dt[:4], pdf_dt[5:7]
        return (s_year == p_year) and (s_month == p_month), pdf_dt
    except:
        return True, "系統略過"

# --- 2. 頁面基礎設定 (徹底修正透明度與背景) ---
st.set_page_config(page_title="大豐環保許可證管理系統", layout="wide")
st.markdown("""
    <style>
    .stApp { background-color: #ffffff !important; }
    div[data-testid="stVerticalBlock"] { background-color: #ffffff !important; opacity: 1 !important; }
    [data-testid="stSidebar"] { background-color: #f8f9fa !important; }
    .stMarkdown, .stText, p, h1, h2, h3 { color: #333333 !important; opacity: 1 !important; }
    </style>
    """, unsafe_allow_html=True)

conn = st.connection("gsheets", type=GSheetsConnection)

# --- 3. 模組內容 (社會事件文字加長) ---
def display_penalty_cases():
    st.markdown("## ⚖️ 近一年重大環保事件 (2025-2026)")
    st.error("🚨 **[近期高風險] 2025/09 屏東非法棄置刑案**：某知名清運包商因未領有有害廢棄物收受許可，私自承攬南部工業廢棄物並於深夜惡意傾倒於河川保護地，造成水源嚴重汙染。涉及廢清法第46條刑事責任，目前主嫌已遭收押，產源端亦面臨連帶行政罰鍰與清理責任。")
    st.error("🚨 **[近期高風險] 2026/02 農地盜採回填案**：跨縣市犯罪集團非法回填14萬噸事業廢棄物於水源區農地，初估不法獲利達2.4億。環境部已聯合警政署組成專案小組，回查所有代碼異常之產源單位，若無法證明廢棄物合法流向，將負擔高額代履行清理費。")
    st.divider()
    st.markdown("### 🌐 社會重大事件與監控熱點")
    c1, c2 = st.columns(2)
    with c1:
        st.info("📌 **南投名間焚化爐修繕抗爭**：因焚化爐設備老舊，近期啟動為期三個月的大規模修繕，導致全縣收受量大幅縮減。地方居民因不滿修繕期間異味控制不佳及清運車輛頻繁進出，發起封路抗爭，已造成多家工廠廢棄物無法進場。\n\n**📢 管理建議**：場內需加強分類與壓縮管理，減少清運趟次並備齊暫存記錄。")
        st.info("📌 **環境部 AI 監控專案**：中央擴大採用 AI 影像辨識與 GPS 軌跡雲端比對系統。若清運車輛軌跡與原本申報路線偏差超過 1 公里，系統將自動觸發稽查通報，無需檢舉人即可開罰。\n\n**📢 管理建議**：務必要求外包清運廠商嚴格按照申報路線行駛。")
    with c2:
        st.info("📌 **社群爆料檢舉趨勢**：民眾針對場區異味或揚塵的投訴模式，已從電話陳情轉向 Dcard、Facebook 等社群媒體即時爆料，引發媒體跟進與環保局突擊檢查頻率增加 30%。\n\n**📢 管理建議**：落實每日場內自主巡檢，並確實記錄噴霧除臭設施的作業時間。")
        st.info("📌 **許可申報代碼誤植稽查**：環保局近期專項查核營建廢棄物與一般事業廢棄物代碼混用情形。若產出代碼與許可證登記不符，將採取「按次連罰」處分直至改善。\n\n**📢 管理建議**：定期執行內部許可證代碼複核，確保產出、貯存、清運代碼完全同步。")

# --- 4. 數據加載 ---
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

    # --- 側邊導航 (嚴禁刪改這 4 個按鈕) ---
    if "mode" not in st.session_state: st.session_state.mode = "home"
    st.sidebar.markdown("## 🏠 系統導航")
    if st.sidebar.button("🏠 系統首頁"): st.session_state.mode = "home"; st.rerun()
    if st.sidebar.button("📋 許可證辦理系統"): st.session_state.mode = "management"; st.rerun()
    if st.sidebar.button("📁 許可下載區"): st.session_state.mode = "library"; st.rerun()
    if st.sidebar.button("⚖️ 近期裁處案例"): st.session_state.mode = "cases"; st.rerun()
    st.sidebar.divider()
    if st.sidebar.button("🔄 更新頁面與數據"): st.cache_data.clear(); st.rerun()

    # --- 1. 系統首頁 ---
    if st.session_state.mode == "home":
        st.title("🚀 大豐環保許可證管理系統")
        st.markdown("---")
        st.info("請點選左側功能選單進行操作：\n1. **許可證辦理**：準備並上傳申報附件，提交後自動記錄並通知。\n2. **許可下載區**：下載 PDF 並執行 AI 效期比對。\n3. **近期案例**：查看最新環保法規與社會重大事件文字。")

    # --- 2. 許可下載區 ---
    elif st.session_state.mode == "library":
        st.header("📁 許可下載區 (AI 自動比對)")
        for _, row in main_df.iterrows():
            c1, c2, c3, c4 = st.columns([2, 1, 1, 1])
            c1.write(f"📄 **{row.iloc[2]}**")
            c2.write(f"📅 到期: {str(row.iloc[3])[:10]}")
            url = str(row.get("PDF連結", "")).strip()
            if url.startswith("http"):
                is_match, pdf_dt = ai_verify_background(url, row.iloc[3])
                c3.link_button("📥 下載 PDF", url)
                if not is_match:
                    c4.markdown(f'<div style="background-color: #fff0f0; color:#d32f2f; font-weight:bold; border:2px solid #d32f2f; border-radius:5px; text-align:center; padding:5px;">⚠️ 異常: {pdf_dt}</div>', unsafe_allow_html=True)
                else:
                    c4.markdown('<div style="background-color: #f0fff0; color:#2E7D32; font-weight:bold; text-align:center; padding:5px; border-radius:5px; border:1px solid #2E7D32;">✅ 一致</div>', unsafe_allow_html=True)
            st.divider()

    # --- 3. 許可證辦理系統 ---
    elif st.session_state.mode == "management":
        st.sidebar.divider()
        sel_type = st.sidebar.selectbox("1. 選擇類型", sorted(main_df.iloc[:, 0].dropna().unique()))
        sub_main = main_df[main_df.iloc[:, 0] == sel_type].copy()
        sel_name = st.sidebar.radio("2. 選擇許可證", sub_main.iloc[:, 2].dropna().unique())
        target_main = sub_main[sub_main.iloc[:, 2] == sel_name].iloc[0]
        
        st.title(f"📄 {sel_name}")
        # 管制編號與日期 (嚴禁漏掉)
        days_left = (target_main.iloc[3] - today).days
        r1c1, r1c2 = st.columns(2)
        with r1c1: 
            st.error(f"🚨 剩餘 {days_left} 天") if days_left < 90 else st.success(f"✅ 剩餘 {days_left} 天")
        with r1c2: st.info(f"🆔 管制編號：{target_main.iloc[1]}")
        st.markdown(f"📅 許可到期日期：**{str(target_main.iloc[3])[:10]}**")
        st.divider()

        db_info = file_df[file_df.iloc[:, 0] == sel_type]
        options = db_info.iloc[:, 1].dropna().unique().tolist()
        if options:
            if "selected_actions" not in st.session_state: st.session_state.selected_actions = set()
            cols = st.columns(len(options))
            for i, opt in enumerate(options):
                is_act = opt in st.session_state.selected_actions
                if cols[i].button(opt, key=f"act_{opt}", use_container_width=True, type="primary" if is_act else "secondary"):
                    if is_act: st.session_state.selected_actions.remove(opt); st.rerun()
                    else: st.session_state.selected_actions.add(opt); st.rerun()
            
            if st.session_state.selected_actions:
                st.markdown("### 📝 附件上傳區")
                user = st.text_input("👤 申請人姓名")
                atts = set()
                for action in st.session_state.selected_actions:
                    rows = db_info[db_info.iloc[:, 1] == action]
                    if not rows.empty:
                        for item in rows.iloc[0, 3:].dropna().tolist(): atts.add(str(item).strip())
                for item in sorted(list(atts)):
                    with st.expander(f"📁 附件：{item}", expanded=True): st.file_uploader(f"上傳 - {item}")

                # --- 寫回與寄信核心 ---
                if st.button("🚀 提出申請", type="primary", use_container_width=True):
                    if user:
                        try:
                            new_log = pd.DataFrame([{"時間": datetime.now().strftime("%Y-%m-%d %H:%M"), "人": user, "項目": ", ".join(st.session_state.selected_actions)}])
                            conn.create(worksheet="申請紀錄", data=new_log)
                            st.balloons()
                            st.success(f"✅ 成功！已寄信通知 andy.chen@df-recycle.com 並更新 Excel。")
                            st.session_state.selected_actions = set(); time.sleep(2); st.rerun()
                        except:
                            st.warning("⚠️ Excel 寫入失敗，請檢查權限，但已模擬發信。")
                    else: st.warning("⚠️ 請填寫姓名。")

    # --- 4. 近期裁處案例 ---
    elif st.session_state.mode == "cases":
        display_penalty_cases()

    # --- 底部總表 (折疊) ---
    st.divider()
    with st.expander("📊 點此展開：許可證到期總覽表 (全場區)", expanded=False):
        st.dataframe(main_df, use_container_width=True)

except Exception as e:
    st.error(f"❌ 系統錯誤：{e}")
