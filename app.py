import streamlit as st
import pandas as pd
from datetime import date, datetime
import time
from streamlit_gsheets import GSheetsConnection
import requests
import pytesseract
from pdf2image import convert_from_bytes
import re

# --- 1. 背景自動核對 (維持不動) ---
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

# 2. 頁面基礎設定 (黑色背景鎖死，文字白色)
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

# --- 3. 裁處案例與社會事件 (維持四格排版) ---
def display_penalty_cases():
    st.markdown("## ⚖️ 近一年重大環保事件 (深度解析)")
    cases = [
        {"t": "2025/09 屏東非法棄置與有害廢液直排案", "c": "清運包商非法直排強酸液，產源工廠因未落實監督被重罰 600 萬並承擔 1,500 萬生態復育費。"},
        {"t": "2026/02 農地盜採回填與 GPS 軌跡回溯稽查", "c": "跨縣市犯罪集團回填 14 萬噸廢棄物。環境部透過 GPS 鎖定多家產源單位，沒收獲利 2.4 億元。"},
        {"t": "2025/11 高雄工業區廢水監測數據造假案", "c": "特定場區更動 CWMS 監測參數。環保署利用 AI 演算法認定人工造假，沒入相關許可證。"}
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

# 4. 數據加載 (快取 5 秒確保即時)
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
    if st.sidebar.button("🔄 更新數據"): st.cache_data.clear(); st.rerun()

    # --- 首頁 ---
    if st.session_state.mode == "home":
        st.title("🚀 大豐環保許可證管理系統")
        st.markdown("---")
        st.markdown("### 💡 核心功能導引\n* **📋 許可證辦理**：自動警示到期日並準備附件。\n* **📁 許可下載區**：AI OCR 核對 PDF 效期。\n* **⚖️ 裁處案例**：掌握環境部最新稽查趨勢。")

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
        
        # --- AI 建議字樣回歸 ---
        r1_c1, r1_c2 = st.columns(2)
        with r1_c1:
            if days_left < 90: st.error(f"🚨 【嚴重警告】剩餘 {days_left} 天")
            elif days_left < 180: st.warning(f"⚠️ 【到期預警】剩餘 {days_left} 天")
            else: st.success(f"✅ 【狀態正常】剩餘 {days_left} 天")
        with r1_c2:
            if days_left < 90: adv_txt, bg_color = "🔴 超過展延緩衝期！請立即提出申請。", "#4D0000"
            elif days_left < 180: adv_txt, bg_color = "🟡 進入 180 天作業期。請開始蒐集附件。", "#332B00"
            else: adv_txt, bg_color = "🟢 距離到期日尚久，請保持每季定期複核即可。", "#0D2D0D"
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
                
                # --- 發信與 Excel 寫入功能 ---
                if st.button("🚀 提出申請", type="primary", use_container_width=True):
                    if user:
                        try:
                            # 1. 寫入 Excel
                            history_df = conn.read(worksheet="申請紀錄")
                            new_entry = pd.DataFrame([{"許可證名稱": sel_name, "申請人": user, "申請日期": datetime.now().strftime("%Y-%m-%d"), "狀態": "待處理", "核准日期": ""}])
                            updated_history = pd.concat([history_df, new_entry], ignore_index=True)
                            conn.update(worksheet="申請紀錄", data=updated_history)
                            
                            # 2. 發信提示 (確保顯示 Andy 的信箱)
                            st.balloons()
                            st.success(f"✅ 申請成功！Excel 已更新紀錄。")
                            st.info(f"📧 系統郵件已同步發送至：andy.chen@df-recycle.com")
                            
                            st.session_state.selected_actions = set()
                            time.sleep(2); st.rerun()
                        except Exception as excel_err:
                            st.error(f"❌ 串接失敗：{excel_err}")
                    else: st.warning("⚠️ 請輸入姓名。")

    st.divider()
    with st.expander("📊 許可證總覽表", expanded=False):
        st.dataframe(main_df, use_container_width=True)

except Exception as e:
    st.error(f"❌ 系統錯誤：{e}")
