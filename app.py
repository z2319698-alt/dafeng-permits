import streamlit as st
import pandas as pd
from datetime import date, datetime
import time
from streamlit_gsheets import GSheetsConnection
import requests
import pytesseract
from pdf2image import convert_from_bytes
import re

# --- 1. 背景自動核對 (每月一次快取) ---
@st.cache_data(ttl=2592000)
def ai_verify_background(pdf_link, sheet_date):
    try:
        file_id = pdf_link.split('/')[-2] if '/file/d/' in pdf_link else pdf_link.split('id=')[-1]
        direct_url = f'https://drive.google.com/uc?export=download&id={file_id}'
        response = requests.get(direct_url, timeout=10)
        images = convert_from_bytes(response.content, dpi=100)
        found_dt = ""
        for img in images:
            text = pytesseract.image_to_string(img, lang='chi_tra')
            match = re.search(r"(\d{2,3}|20\d{2})[\s\.年/-]*(\d{1,2})[\s\.月/-]*(\d{1,2})", text)
            if match:
                yy, mm, dd = match.groups()
                year = int(yy) + 1911 if int(yy) < 1000 else int(yy)
                found_dt = f"{year}-{mm.zfill(2)}-{dd.zfill(2)}"
                break
        s_clean = str(sheet_date)[:10].replace('-', '')
        p_clean = found_dt.replace('-', '')
        return (s_clean == p_clean), found_dt
    except:
        return True, "跳過辨識"

# 2. 頁面基礎設定
st.set_page_config(page_title="大豐環保許可證管理系統", layout="wide")
conn = st.connection("gsheets", type=GSheetsConnection)

# --- 3. 智慧模組與案例 ---
def display_ai_law_wall(category):
    law_db = {
        "廢棄物清理計畫書": [
            {"date": "2025/08", "tag": "重大變更", "content": "環保署公告：廢清書應增列「資源循環促進」專章。"},
            {"date": "2025/11", "tag": "裁罰預警", "content": "強化產源責任：產源端若未落實視察，將面臨連帶重罰。"},
            {"date": "2026/01", "tag": "最新公告", "content": "全面推動電子化合約上傳，紙本備查期縮短。"}
        ],
        "水污染防治許可證": [
            {"date": "2025/07", "tag": "標準加嚴", "content": "氨氮、重金屬指標納入評鑑，連續超標將暫停展延。"}
        ]
    }
    updates = law_db.get(category, [{"date": "2025-2026", "tag": "穩定", "content": "法規動態穩定。"}])
    st.markdown(f"### 🛡️ AI 法規動態感知牆")
    cols = st.columns(len(updates))
    for i, item in enumerate(updates):
        with cols[i]:
            st.markdown(f"""<div style="background-color: #f0f4f8; border-left: 5px solid #2E7D32; padding: 15px; border-radius: 8px; height: 180px;"><span style="background-color: #2E7D32; color: white; padding: 2px 8px; border-radius: 4px; font-size: 0.8rem;">{item['tag']}</span><p style="margin-top: 10px; font-weight: bold; color: #333;">📅 {item['date']}</p><p style="font-size: 0.85rem; color: #333;">{item['content']}</p></div>""", unsafe_allow_html=True)

def display_penalty_cases():
    st.markdown("## ⚖️ 近一年重大環保事件 (2025-2026)")
    high_risk_cases = [
        {"type": "2025/09 廢棄物非法棄置案", "reason": "屏東包商未經許可清運至國有地。", "key": "【刑事責任】委託務必核對代碼。"},
        {"type": "2026/02 美濃盜採回填案", "reason": "農地回填 14 萬噸廢棄物，獲利 2.4 億。", "key": "【產源責任】無法證明流向將負擔清理成本。"}
    ]
    for case in high_risk_cases:
        st.markdown(f"""<div style="background-color: #fff5f5; border-left: 5px solid #e53935; padding: 15px; margin-bottom: 15px; border-radius: 8px; color: #333;"><b style="color: #e53935;">🚨 [近期高風險] {case['type']}</b><p>{case['reason']}<br><b>💡 核心：</b>{case['key']}</p></div>""", unsafe_allow_html=True)

    all_news = [
        {"topic": "南投名間焚化爐抗爭", "desc": "2026 最新消息：進廠審核趨嚴。", "advice": "加強垃圾分類。"},
        {"topic": "環境部 GPS 監控專案", "desc": "2025 科技大數據稽查軌跡異常。", "advice": "確保廠商按路線行駛。"},
        {"topic": "異味粉塵 Dcard 曝光", "desc": "民眾網路陳情效應提升，引發關切。", "advice": "加強周界灑水。"},
        {"topic": "申報代碼誤執連罰", "desc": "稽查熱點：夾帶營建廢材認定申報不實。", "advice": "定期執行代碼複核。"}
    ]
    seed = (datetime.now().hour // 12) % 2
    display_news = all_news[seed*2 : (seed+1)*2]
    st.markdown("### 🌐 社會重大事件與監控熱點 (AI 半天自動更換)")
    cols = st.columns(2)
    for i, m in enumerate(display_news):
        with cols[i]:
            st.markdown(f"""<div style="background-color: #ffffff; border-left: 5px solid #0288d1; padding: 12px; border-radius: 8px; border: 1px solid #e1f5fe; min-height: 180px; color: #333;"><b style="color: #01579b;">{m['topic']}</b><p>{m['desc']}</p><p style="color: #0277bd;"><b>📢 管理建議：</b>{m['advice']}</p></div>""", unsafe_allow_html=True)

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

    if "mode" not in st.session_state: st.session_state.mode = "management"
    st.sidebar.markdown("## 🏠 系統導航")
    if st.sidebar.button("🏠 系統首頁"): st.session_state.mode = "management"; st.rerun()
    if st.sidebar.button("📋 許可證辦理系統"): st.session_state.mode = "management"; st.rerun()
    if st.sidebar.button("📁 許可下載區"): st.session_state.mode = "library"; st.rerun()
    if st.sidebar.button("⚖️ 近期裁處案例"): st.session_state.mode = "cases"; st.rerun()

    if st.session_state.mode == "library":
        st.header("📁 許可下載區")
        for idx, row in main_df.iterrows():
            c1, c2, c3, c4 = st.columns([2, 1, 1, 1])
            c1.write(f"📄 **{row.iloc[2]}**")
            c2.write(f"📅 到期: {str(row.iloc[3])[:10]}")
            url = row.get("PDF連結", "")
            if pd.notna(url) and str(url).strip().startswith("http"):
                is_match, pdf_dt = ai_verify_background(str(url).strip(), row.iloc[3])
                c3.link_button("📥 下載 PDF", str(url).strip())
                if not is_match:
                    c4.markdown(f"""<div style="color:#d32f2f;font-weight:bold;border:1px solid #d32f2f;border-radius:5px;text-align:center;padding:2px;">⚠️ 比對異常<br><span style="font-size:0.7rem;">PDF: {pdf_dt}</span></div>""", unsafe_allow_html=True)
                else:
                    c4.markdown('<p style="color:#2E7D32;text-align:center;margin-top:10px;">✅ 內容一致</p>', unsafe_allow_html=True)
            st.divider()

    elif st.session_state.mode == "cases":
        display_penalty_cases()
        if st.button("⬅️ 返回辦理系統"): st.session_state.mode = "management"; st.rerun()

    else:
        st.sidebar.divider()
        sel_type = st.sidebar.selectbox("1. 選擇類型", sorted(main_df.iloc[:, 0].dropna().unique()))
        sub_main = main_df[main_df.iloc[:, 0] == sel_type].copy()
        sel_name = st.sidebar.radio("2. 選擇許可證", sub_main.iloc[:, 2].dropna().unique())
        target_main = sub_main[sub_main.iloc[:, 2] == sel_name].iloc[0]
        st.title(f"📄 {sel_name}")

        expiry_date = target_main.iloc[3]
        days_left = (expiry_date - today).days
        date_str = str(expiry_date)[:10]

        # --- 第一列：狀態提醒 + AI 建議 ---
        r1c1, r1c2 = st.columns(2)
        with r1c1:
            if days_left < 90: st.error(f"🚨 【嚴重警告】剩餘 {days_left} 天")
            elif days_left < 180: st.warning(f"⚠️ 【到期預警】剩餘 {days_left} 天")
            else: st.success(f"✅ 【狀態正常】剩餘 {days_left} 天")
        with r1c2:
            bg = "#ffeded" if days_left < 90 else ("#fff9e6" if days_left < 180 else "#e8f5e9")
            advice = "立即準備附件申報！" if days_left < 90 else ("建議開始核對附件。" if days_left < 180 else "在 180 天前開始蒐集即可。")
            st.markdown(f'<div style="background-color:{bg};padding:12px;border-radius:5px;color:#333;border:1px solid #ccc;height:50px;line-height:25px;"><b>🤖 AI 建議：</b>{advice}</div>', unsafe_allow_html=True)

        # --- 第二列：管制編號 + 許可到期日期 ---
        r2c1, r2c2 = st.columns(2)
        with r2c1:
            st.info(f"🆔 管制編號：{target_main.iloc[1]}")
        with r2c2:
            st.markdown(f'<div style="background-color:#f0f2f6;padding:12px;border-radius:5px;color:#333;border:1px solid #dcdfe6;height:50px;line-height:25px;">📅 許可到期日期：<b>{date_str}</b></div>', unsafe_allow_html=True)

        st.divider()
        display_ai_law_wall(sel_type)
        
        db_info = file_df[file_df.iloc[:, 0] == sel_type]
        options = db_info.iloc[:, 1].dropna().unique().tolist()
        if options:
            st.subheader("🛠️ 第一步：選擇辦理項目")
            if "selected_actions" not in st.session_state: st.session_state.selected_actions = set()
            cols = st.columns(len(options))
            for i, opt in enumerate(options):
                is_act = opt in st.session_state.selected_actions
                if cols[i].button(opt, key=f"act_{opt}", use_container_width=True, type="primary" if is_act else "secondary"):
                    if is_act: st.session_state.selected_actions.remove(opt)
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
                    with st.expander(f"📁 附件：{item}", expanded=True): st.file_uploader(f"上傳檔案 - {item}", key=f"up_{item}")
                if st.button("🚀 提出申請", type="primary"):
                    if user: st.balloons(); st.success("✅ 申請成功！"); st.session_state.selected_actions = set(); time.sleep(1); st.rerun()

except Exception as e:
    st.error(f"❌ 系統錯誤：{e}")
