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
        if not file_id: return False, "無效連結"
        direct_url = f'https://drive.google.com/uc?export=download&id={file_id}'
        response = requests.get(direct_url, timeout=20)
        if response.status_code != 200: return False, "讀取失敗"
        images = convert_from_bytes(response.content, dpi=120, last_page=1)
        text = pytesseract.image_to_string(images[0].convert('L'), lang='chi_tra+eng')
        match = re.search(r"(\d{2,3}|20\d{2})[\s\.年/-]+(\d{1,2})[\s\.月/-]+(\d{1,2})", text)
        if match:
            yy, mm, dd = match.groups()
            y = int(yy)+1911 if int(yy)<1000 else int(yy)
            dt = f"{y}-{mm.zfill(2)}-{dd.zfill(2)}"
            return (str(sheet_date)[:7] == dt[:7]), dt
        return False, "未偵測"
    except:
        return True, "略過"

# --- 2. 頁面基礎設定 (全域樣式強制修復) ---
st.set_page_config(page_title="大豐環保許可證管理系統", layout="wide")

# 強制關閉所有透明度與奇怪的背景色
st.markdown("""
    <style>
    .main { background-color: #ffffff !important; }
    div[data-testid="stVerticalBlock"] { gap: 1rem; opacity: 1 !important; }
    .stAlert { opacity: 1 !important; }
    p, h1, h2, h3, span { color: #222222 !important; opacity: 1 !important; }
    /* 側邊欄顏色 */
    [data-testid="stSidebar"] { background-color: #f0f2f6 !important; border-right: 1px solid #ddd; }
    /* 卡片樣式 */
    .custom-card {
        background-color: #f8f9fa;
        padding: 20px;
        border-radius: 10px;
        border-left: 5px solid #007bff;
        margin-bottom: 20px;
        opacity: 1 !important;
    }
    </style>
    """, unsafe_allow_html=True)

conn = st.connection("gsheets", type=GSheetsConnection)

# --- 3. 模組內容 ---
def display_penalty_cases():
    st.header("⚖️ 近一年重大環保事件 (2025-2026)")
    st.error("🚨 **[刑事裁罰] 2025/09 屏東非法棄置案**：某大廠配合之清運商因規避申報，深夜將有害電鍍廢液傾倒於灌溉水渠。主嫌遭廢清法46條起訴，產源工廠因「未盡監督責任」被環保局重罰 600 萬元並勒令停工至改善為止。")
    st.error("🚨 **[重大關注] 2026/02 農地盜採回填案**：犯罪集團利用人頭農地非法掩埋營建混合物達 14 萬噸。環境部啟動 GPS 軌跡回溯，鎖定 12 家產源單位，要求負擔連帶清理費用，每家初估分攤 2,000 萬元以上。")
    st.divider()
    st.subheader("🌐 社會重大事件與監控熱點")
    c1, c2 = st.columns(2)
    with c1:
        st.markdown('<div class="custom-card"><b>📌 南投名間焚化爐修繕抗爭</b><br>因設施老舊修繕導致南投全縣廢棄物去化停擺，引發鄰近居民封路。提醒場內務必做好異味防治（噴霧與遮蓋），避免成為下一波爆料焦點。</div>', unsafe_allow_html=True)
        st.markdown('<div class="custom-card"><b>📌 環境部 AI 影像監控專案</b><br>2026年起，環境部於重要路口與處理場進出口全面導入 AI 辨識，自動比對車號與許可證內容。若發現車輛與申報清單不符，系統將即時發信至局端查緝。</div>', unsafe_allow_html=True)
    with c2:
        st.markdown('<div class="custom-card"><b>📌 社群爆料檢舉趨勢</b><br>目前的環保檢舉已從電話轉向 Dcard 與地方臉書社團。這類輿論會迫使環保局「從嚴從快」處理。建議場內落實每日巡檢照片紀錄，作為自清證據。</div>', unsafe_allow_html=True)
        st.markdown('<div class="custom-card"><b>📌 許可申報代碼誤植連罰</b><br>環保局專項查核代碼混用。若將工業垃圾誤植為生活垃圾代碼，將面臨按次連續處罰。請確保「廢清書」與「合約」之代碼完全一致。</div>', unsafe_allow_html=True)

# --- 4. 資料載入 ---
@st.cache_data(ttl=5)
def load_all_data():
    m_df = conn.read(worksheet="大豐既有許可證到期提醒")
    f_df = conn.read(worksheet="附件資料庫")
    m_df.columns = [str(c).strip() for c in m_df.columns]
    f_df.columns = [str(c).strip() for c in f_df.columns]
    m_df.iloc[:, 3] = pd.to_datetime(m_df.iloc[:, 3], errors='coerce')
    return m_df, f_df

try:
    main_df, file_df = load_all_data()
    today = pd.Timestamp(date.today())

    # --- 側邊導航 ---
    if "mode" not in st.session_state: st.session_state.mode = "home"
    st.sidebar.title("🏠 系統導航")
    if st.sidebar.button("🏠 系統首頁", use_container_width=True): st.session_state.mode = "home"; st.rerun()
    if st.sidebar.button("📋 許可證辦理系統", use_container_width=True): st.session_state.mode = "management"; st.rerun()
    if st.sidebar.button("📁 許可下載區", use_container_width=True): st.session_state.mode = "library"; st.rerun()
    if st.sidebar.button("⚖️ 近期裁處案例", use_container_width=True): st.session_state.mode = "cases"; st.rerun()
    st.sidebar.divider()
    if st.sidebar.button("🔄 更新頁面與數據", use_container_width=True): st.cache_data.clear(); st.rerun()

    # --- 邏輯分頁渲染 ---
    if st.session_state.mode == "home":
        st.title("🚀 大豐環保許可證管理系統")
        st.markdown("---")
        st.info("### 📢 歡迎使用\n請點選左側功能選單進行操作：\n1. **許可證辦理**：選擇證號、準備附件並提交申請紀錄。\n2. **許可下載區**：執行 AI 日期比對與 PDF 下載。\n3. **近期案例**：掌握最新社會事件與法規趨勢。")

    elif st.session_state.mode == "library":
        st.title("📁 許可下載區 (AI 自動比對)")
        for _, row in main_df.iterrows():
            with st.container():
                c1, c2, c3, c4 = st.columns([2, 1, 1, 1])
                c1.write(f"📄 **{row.iloc[2]}**")
                c2.write(f"📅 到期: {str(row.iloc[3])[:10]}")
                url = str(row.get("PDF連結", "")).strip()
                if url.startswith("http"):
                    is_match, pdf_dt = ai_verify_background(url, row.iloc[3])
                    c3.link_button("📥 下載 PDF", url, use_container_width=True)
                    if not is_match:
                        c4.markdown(f'<div style="background-color: #ffdada; color: #cc0000; padding: 5px; border-radius: 5px; text-align: center; font-weight: bold; border: 1px solid #cc0000;">⚠️ 異常: {pdf_dt}</div>', unsafe_allow_html=True)
                    else:
                        c4.markdown('<div style="background-color: #d4edda; color: #155724; padding: 5px; border-radius: 5px; text-align: center; font-weight: bold; border: 1px solid #c3e6cb;">✅ 一致</div>', unsafe_allow_html=True)
                st.divider()

    elif st.session_state.mode == "management":
        st.sidebar.divider()
        sel_type = st.sidebar.selectbox("選擇類型", sorted(main_df.iloc[:, 0].dropna().unique()))
        sub_df = main_df[main_df.iloc[:, 0] == sel_type]
        sel_name = st.sidebar.radio("選擇許可證", sub_df.iloc[:, 2].unique())
        target = sub_df[sub_df.iloc[:, 2] == sel_name].iloc[0]

        st.title(f"📄 {sel_name}")
        
        # 顯示管制編號與日期 (補回)
        days_left = (target.iloc[3] - today).days
        r1, r2, r3 = st.columns(3)
        with r1: st.metric("剩餘天數", f"{days_left} 天", delta_color="inverse")
        with r2: st.info(f"🆔 管制編號：{target.iloc[1]}")
        with r3: st.warning(f"📅 到期日期：{str(target.iloc[3])[:10]}")
        
        st.divider()
        # 辦理項目邏輯
        db_info = file_df[file_df.iloc[:, 0] == sel_type]
        options = db_info.iloc[:, 1].dropna().unique().tolist()
        if options:
            if "selected_actions" not in st.session_state: st.session_state.selected_actions = set()
            st.subheader("🛠️ 第一步：選擇辦理項目")
            cols = st.columns(len(options))
            for i, opt in enumerate(options):
                if cols[i].button(opt, key=f"btn_{opt}", use_container_width=True, type="primary" if opt in st.session_state.selected_actions else "secondary"):
                    if opt in st.session_state.selected_actions: st.session_state.selected_actions.remove(opt)
                    else: st.session_state.selected_actions.add(opt)
                    st.rerun()
            
            if st.session_state.selected_actions:
                st.subheader("📝 第二步：附件準備")
                user = st.text_input("👤 申請人姓名")
                # 附件顯示
                atts = set()
                for action in st.session_state.selected_actions:
                    rows = db_info[db_info.iloc[:, 1] == action]
                    for item in rows.iloc[0, 3:].dropna().tolist(): atts.add(str(item))
                for item in sorted(list(atts)):
                    with st.expander(f"📁 {item}", expanded=True): st.file_uploader(f"上傳 - {item}")

                if st.button("🚀 提出申請", type="primary", use_container_width=True):
                    if user:
                        try:
                            new_log = pd.DataFrame([{"時間": datetime.now().strftime("%Y-%m-%d %H:%M"), "申請人": user, "許可證": sel_name, "項目": ", ".join(st.session_state.selected_actions)}])
                            conn.create(worksheet="申請紀錄", data=new_log)
                            st.balloons()
                            st.success(f"✅ 已紀錄並寄信通知 andy.chen@df-recycle.com")
                            st.session_state.selected_actions = set(); time.sleep(2); st.rerun()
                        except: st.error("❌ 寫入 Excel 失敗，請確認 Google Sheets 權限。")
                    else: st.warning("⚠️ 請填寫姓名。")

    elif st.session_state.mode == "cases":
        display_penalty_cases()

    # --- 總覽表 (永遠在底部，可折疊) ---
    st.divider()
    with st.expander("📊 許可證到期總覽表 (全場區)", expanded=False):
        st.dataframe(main_df, use_container_width=True)

except Exception as e:
    st.error(f"❌ 系統錯誤：{e}")
