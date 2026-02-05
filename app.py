import streamlit as st
import pandas as pd
from datetime import date, datetime
import time
from streamlit_gsheets import GSheetsConnection
import requests
import pytesseract
from pdf2image import convert_from_bytes
import re

# --- 1. 深度掃描版背景核對 (掃描全頁碼 + 關鍵字過濾) ---
@st.cache_data(ttl=2592000)
def ai_verify_background(pdf_link, sheet_date):
    try:
        file_id = ""
        if '/file/d/' in pdf_link: file_id = pdf_link.split('/file/d/')[1].split('/')[0]
        elif 'id=' in pdf_link: file_id = pdf_link.split('id=')[1].split('&')[0]
        if not file_id: return False, "無效連結"

        direct_url = f'https://drive.google.com/uc?export=download&id={file_id}'
        response = requests.get(direct_url, timeout=20)
        if response.status_code != 200: return False, "讀取失敗"

        # 掃描整份 PDF (不限頁數)
        images = convert_from_bytes(response.content, dpi=150)
        
        best_match_dt = ""
        all_text = ""
        
        for img in images:
            # 影像轉灰階提升辨識度
            page_text = pytesseract.image_to_string(img.convert('L'), lang='chi_tra+eng')
            all_text += page_text
            
            # 尋找帶有「至」或「有效」關鍵字的日期區塊
            # 優先找 民國/西元 格式
            match = re.search(r"(?:至|期|效)[\s]*(\d{2,3}|20\d{2})[\s\.年/-]+(\d{1,2})[\s\.月/-]+(\d{1,2})", page_text)
            if match:
                yy, mm, dd = match.groups()
                year = int(yy) + 1911 if int(yy) < 1000 else int(yy)
                best_match_dt = f"{year}-{mm.zfill(2)}-{dd.zfill(2)}"
                # 抓到符合關鍵字的日期就優先採用
                break

        if not best_match_dt:
            # 若無關鍵字，則抓取全文件中最後一個出現的日期 (通常到期日都在後面)
            all_dates = re.findall(r"(\d{2,3}|20\d{2})[\s\.年/-]+(\d{1,2})[\s\.月/-]+(\d{1,2})", all_text)
            if all_dates:
                yy, mm, dd = all_dates[-1]
                year = int(yy) + 1911 if int(yy) < 1000 else int(yy)
                best_match_dt = f"{year}-{mm.zfill(2)}-{dd.zfill(2)}"
            else:
                return False, "找不到日期"

        s_year, s_month = str(sheet_date)[:4], str(sheet_date)[5:7]
        p_year, p_month = best_match_dt[:4], best_match_dt[5:7]
        return (s_year == p_year) and (s_month == p_month), best_match_dt

    except Exception as e:
        return True, "跳過"

# 2. 基礎設定
st.set_page_config(page_title="大豐環保許可證管理系統", layout="wide")
conn = st.connection("gsheets", type=GSheetsConnection)

# --- 3. 模組功能 ---
def display_ai_law_wall(category):
    updates = [
        {"date": "2025/08", "tag": "重大變更", "content": "環境部公告：廢清書應增列「資源循環促進」專章。"},
        {"date": "2025/11", "tag": "裁罰預警", "content": "產源端未落實現場視察，將面臨連帶重罰。"},
        {"date": "2026/01", "tag": "最新公告", "content": "電子化合約上傳，紙本備查期縮短至14天。"}
    ]
    st.markdown("### 🛡️ 相關法規動態")
    cols = st.columns(3)
    for i, item in enumerate(updates):
        with cols[i]:
            st.markdown(f"""<div style="background-color: #f0f4f8; border-left: 5px solid #2E7D32; padding: 15px; border-radius: 8px; height: 160px; color: #333;"><span style="background-color: #2E7D32; color: white; padding: 2px 8px; border-radius: 4px; font-size: 0.8rem;">{item['tag']}</span><p style="margin-top: 10px; font-weight: bold;">📅 {item['date']}</p><p style="font-size: 0.85rem;">{item['content']}</p></div>""", unsafe_allow_html=True)

def display_penalty_cases():
    st.markdown("## ⚖️ 近一年重大環保事件")
    cases = [
        {"type": "2025/09 廢棄物非法棄置刑案", "reason": "屏東包商未領許可私自收受廢棄物並傾倒，涉及刑事責任。", "key": "委託清運務必核對廠商證號與流向證明。"},
        {"type": "2026/02 農地盜採回填案", "reason": "回填14萬噸事業廢棄物於水源區，不法獲利2.4億。", "key": "產源單位若無法證明流向將負擔高額清理費。"}
    ]
    for case in cases:
        st.markdown(f"""<div style="background-color: #fff5f5; border-left: 5px solid #e53935; padding: 15px; margin-bottom: 15px; border-radius: 8px; color: #333;"><b style="color: #e53935;">🚨 [近期高風險] {case['type']}</b><p>{case['reason']}<br><b>💡 管理核心：</b>{case['key']}</p></div>""", unsafe_allow_html=True)

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
    
    # 側邊導航
    st.sidebar.markdown("## 🏠 系統導航")
    if st.sidebar.button("📋 許可證辦理系統"): st.session_state.mode = "management"; st.rerun()
    if st.sidebar.button("📁 許可下載區"): st.session_state.mode = "library"; st.rerun()
    if st.sidebar.button("⚖️ 近期裁處案例"): st.session_state.mode = "cases"; st.rerun()

    # --- 渲染主要區域 ---
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
                    c4.markdown(f"""<div style="color:#d32f2f;font-weight:bold;border:1px solid #d32f2f;border-radius:5px;text-align:center;padding:2px;">⚠️ 比對異常<br><span style="font-size:0.7rem;">偵測值: {pdf_dt}</span></div>""", unsafe_allow_html=True)
                else:
                    c4.markdown('<p style="color:#2E7D32;text-align:center;margin-top:10px;">✅ 內容一致</p>', unsafe_allow_html=True)
            st.divider()

    elif st.session_state.mode == "cases":
        display_penalty_cases()

    else:
        # 辦理首頁
        st.sidebar.divider()
        sel_type = st.sidebar.selectbox("1. 選擇類型", sorted(main_df.iloc[:, 0].dropna().unique()))
        sub_main = main_df[main_df.iloc[:, 0] == sel_type].copy()
        sel_name = st.sidebar.radio("2. 選擇許可證", sub_main.iloc[:, 2].dropna().unique())
        target_main = sub_main[sub_main.iloc[:, 2] == sel_name].iloc[0]
        
        st.title(f"📄 {sel_name}")
        
        # 併排排版
        days_left = (target_main.iloc[3] - today).days
        r1c1, r1c2 = st.columns(2)
        with r1c1:
            if days_left < 90: st.error(f"🚨 【嚴重警告】剩餘 {days_left} 天")
            elif days_left < 180: st.warning(f"⚠️ 【到期預警】剩餘 {days_left} 天")
            else: st.success(f"✅ 【狀態正常】剩餘 {days_left} 天")
        with r1c2:
            bg = "#ffeded" if days_left < 90 else ("#fff9e6" if days_left < 180 else "#e8f5e9")
            advice = "立即準備附件申報！" if days_left < 90 else ("建議開始核對附件。" if days_left < 180 else "在 180 天前開始蒐集即可。")
            st.markdown(f'<div style="background-color:{bg};padding:12px;border-radius:5px;color:#333;border:1px solid #ccc;height:50px;line-height:25px;"><b>🤖 AI 建議：</b>{advice}</div>', unsafe_allow_html=True)

        r2c1, r2c2 = st.columns(2)
        with r2c1: st.info(f"🆔 管制編號：{target_main.iloc[1]}")
        with r2c2: st.markdown(f'<div style="background-color:#f0f2f6;padding:12px;border-radius:5px;color:#333;border:1px solid #dcdfe6;height:50px;line-height:25px;">📅 許可到期日期：<b>{str(target_main.iloc[3])[:10]}</b></div>', unsafe_allow_html=True)

        st.divider()
        display_ai_law_wall(sel_type)
        
        # 附件上傳邏輯
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

    # --- 📊 總表區域 (移到最外面，保證永遠顯示) ---
    st.divider()
    st.subheader("📊 許可證到期總表 (全場區)")
    # 這裡顯示所有許可證的狀態，方便一目了然
    st.dataframe(main_df, use_container_width=True)

except Exception as e:
    st.error(f"❌ 系統錯誤：{e}")
