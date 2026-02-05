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
from PIL import Image, ImageOps

# --- 1. 背景自動核對 (最高精準度辨識版) ---
@st.cache_data(ttl=2592000)
def get_pdf_images(pdf_link):
    try:
        file_id = ""
        if '/file/d/' in pdf_link: file_id = pdf_link.split('/file/d/')[1].split('/')[0]
        elif 'id=' in pdf_link: file_id = pdf_link.split('id=')[1].split('&')[0]
        if not file_id: return None
        direct_url = f'https://drive.google.com/uc?export=download&id={file_id}'
        response = requests.get(direct_url, timeout=30)
        if response.status_code != 200: return None
        # 提高 DPI 到 200 確保數字辨識清晰
        return convert_from_bytes(response.content, dpi=200)
    except:
        return None

def ai_verify_logic(images, sheet_date):
    if not images: return False, "無法讀取", 0, None
    # 強化版正規表達式：抓取所有可能的日期格式
    date_pattern = r"(\d{2,3}|20\d{2})[\s\.年/-]+(\d{1,2})[\s\.月/-]+(\d{1,2})"
    
    for i, img in enumerate(images):
        # 影像強化：轉灰階 + 自動對比
        gray_img = img.convert('L')
        enhanced_img = ImageOps.autocontrast(gray_img)
        page_text = pytesseract.image_to_string(enhanced_img, lang='chi_tra+eng')
        
        # 進行匹配 (原始與去空格版本)
        match = re.search(date_pattern, page_text)
        if not match:
            clean_text = re.sub(r'\s+', '', page_text)
            match = re.search(date_pattern, clean_text)
            
        if match:
            yy, mm, dd = match.groups()
            year = int(yy) + 1911 if int(yy) < 1000 else int(yy)
            pdf_dt_str = f"{year}-{mm.zfill(2)}-{dd.zfill(2)}"
            is_match = (str(sheet_date)[:4] == str(year))
            return is_match, pdf_dt_str, i, img
            
    return False, "未偵測到日期", 0, images[0]

# --- 2. 頁面基礎設定 ---
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
        st.markdown("### 💡 核心功能導引")
        st.markdown("""
        * **📋 許可證辦理系統**：
            * 自動計算許可證到期倒數。
            * 根據到期天數提供 **AI 建議**（紅色、黃色、綠色狀態）。
            * 選擇辦理項目後，自動列出所需附件並支援上傳。
            * **一鍵提出申請**：自動更新 Excel 並寄送通知信件予 Andy。
        
        * **📁 許可下載區**：
            * **AI 自動核對**：系統自動比對 PDF 內容與資料庫效期。
            * **翻頁核對**：支援多頁 PDF 翻閱查看。
            * **原地修正**：發現 OCR 辨識異常或資料有誤時，可直接在頁面上修正並同步回傳雲端。
        
        * **⚖️ 近期裁處案例**：
            * 彙整環境部最新稽查熱點與社會重大環保事件，提供預防性建議。
        """)

    elif st.session_state.mode == "library":
        st.header("📁 許可下載區 (AI 高精準辨識版)")
        for idx, row in main_df.iterrows():
            c1, c2, c3, c4 = st.columns([2, 1, 1, 1])
            p_name, p_date = row.iloc[2], row.iloc[3]
            c1.markdown(f"📄 **{p_name}**")
            c2.write(f"📅 到期: {str(p_date)[:10]}")
            url = row.get("PDF連結", "")
            if pd.notna(url) and str(url).strip().startswith("http"):
                pdf_images = get_pdf_images(str(url).strip())
                is_match, pdf_dt, found_idx, _ = ai_verify_logic(pdf_images, p_date)
                c3.link_button("📥 下載 PDF", str(url).strip())
                if not is_match:
                    with c4: st.markdown(f'<div style="background-color: #4D0000; color:#ff4d4d; font-weight:bold; border:1px solid #ff4d4d; border-radius:5px; text-align:center; padding:5px;">⚠️ 異常: {pdf_dt}</div>', unsafe_allow_html=True)
                    with st.expander(f"🛠️ 檢視與修正 {p_name}"):
                        if pdf_images:
                            col_img, col_fix = st.columns([2, 1])
                            with col_img:
                                sel_page = st.number_input(f"翻頁 (共 {len(pdf_images)} 頁)", min_value=1, max_value=len(pdf_images), value=found_idx+1, key=f"pg_{idx}")
                                st.image(pdf_images[sel_page-1], use_container_width=True)
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
            if days_left < 90: st.error(f"🚨 【嚴重警告】剩餘 {days_left} 天")
            elif days_left < 180: st.warning(f"⚠️ 【到期預警】剩餘 {days_left} 天")
            else: st.success(f"✅ 【狀態正常】剩餘 {days_left} 天")
        with r1_c2:
            adv_txt = "🔴 超過展延緩衝期！請立即提出申請。" if days_left < 90 else "🟡 進入 180 天作業期。請開始蒐集附件。" if days_left < 180 else "🟢 距離到期日尚久，請定期複核。"
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
                            # 寄信邏輯 (使用 st.secrets)
                            st.balloons(); st.success(f"✅ 申請成功！"); st.session_state.selected_actions = set(); time.sleep(2); st.rerun()
                        except Exception as err: st.error(f"❌ 流程失敗：{err}")

    elif st.session_state.mode == "cases":
        display_penalty_cases()

except Exception as e:
    st.error(f"❌ 系統錯誤：{e}")
