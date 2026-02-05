import streamlit as st
import pandas as pd
import requests
import pytesseract
from pdf2image import convert_from_bytes
import re

# --- 1. 頁面基礎配置 ---
st.set_page_config(page_title="大豐證照管理系統", layout="wide")

st.markdown("""
    <style>
    .main {
        background-color: #f5f7f9;
    }
    .stButton>button {
        width: 100%;
        border-radius: 5px;
        height: 3em;
        background-color: #007bff;
        color: white;
    }
    </style>
    """, unsafe_allow_html=True)

st.title("🛡️ 證照到期日 AI 自動核對系統")
st.info("💡 說明：點擊右側的「🔍 AI 核對」按鈕，系統會自動下載雲端 PDF 並比對到期日期。")

# --- 2. 設定區 ---
# 你的試算表 CSV 網址
SHEET_URL = "https://docs.google.com/spreadsheets/d/1BA427GfGw41UWen083KSWxbdRwbe3a1SEF_H89MyBZE/export?format=csv&gid=1439172114"

# 辨識日期前的關鍵字
KEYWORDS = ["有效日期", "有效期限", "有效期間", "發文次日至", "許可期限", "起至"]

# --- 3. AI 核心辨識函數 ---
def verify_pdf_date(pdf_link, sheet_date):
    try:
        # 解析 Google Drive 連結轉為直接下載
        file_id = ""
        if '/file/d/' in pdf_link:
            file_id = pdf_link.split('/d/')[1].split('/')[0]
        elif 'id=' in pdf_link:
            file_id = pdf_link.split('id=')[-1].split('&')[0]
        
        if not file_id:
            return False, "無效的雲端連結"

        direct_url = f'https://drive.google.com/uc?export=download&id={file_id}'
        
        # 從雲端獲取檔案內容
        response = requests.get(direct_url, timeout=10)
        if response.status_code != 200:
            return False, "無法從雲端下載檔案"

        # PDF 轉圖片 (Streamlit Cloud 環境不需要指定路徑)
        images = convert_from_bytes(response.content, dpi=150)
        
        found_date = "未偵測到日期"
        for img in images:
            # 使用繁體中文進行 OCR
            text = pytesseract.image_to_string(img, lang='chi_tra')
            
            # 檢查關鍵字
            if any(k in text for k in KEYWORDS):
                # 搜尋民國年或西元年格式
                match = re.search(r"(\d{2,3})[\s\.年/]*(\d{1,2})[\s\.月/]*(\d{1,2})", text)
                if match:
                    yy, mm, dd = match.groups()
                    # 民國轉西元判斷
                    y_val = int(yy)
                    actual_year = y_val + 1911 if y_val < 1911 else y_val
                    found_date = f"{actual_year}-{mm.zfill(2)}-{dd.zfill(2)}"
                    break
        
        # 比對 (移除符號後比對數字)
        clean_sheet = str(sheet_date).replace('-', '').replace('/', '')
        clean_pdf = found_date.replace('-', '').replace('/', '')
        
        is_match = (clean_sheet == clean_pdf)
        return is_match, found_date

    except Exception as e:
        return False, f"辨識發生錯誤: {str(e)}"

# --- 4. 讀取資料與顯示介面 ---
try:
    # 讀取試算表
    df = pd.read_csv(SHEET_URL)
    
    # 建立表頭
    h1, h2, h3, h4 = st.columns([3, 2, 1, 2])
    h1.subheader("🏢 廠區 / 名稱")
    h2.subheader("📅 試算表到期日")
    h3.subheader("🔗 檔案")
    h4.subheader("🤖 AI 核對狀態")
    st.divider()

    # 逐行顯示資料
    for index, row in df.iterrows():
        c1, c2, c3, c4 = st.columns([3, 2, 1, 2])
        
        with c1:
            st.write(f"**{row['廠區/名稱']}**")
        
        with c2:
            st.code(row['到期日期'])
        
        with c3:
            st.link_button("📂 打開", row['檔案連結'])
            
        with c4:
            # 點擊按鈕才執行辨識，節省雲端效能
            if st.button(f"🔍 AI 核對", key=f"btn_{index}"):
                with st.spinner('正在分析雲端文件...'):
                    is_ok, pdf_dt = verify_pdf_date(row['檔案連結'], row['到期日期'])
                    if is_ok:
                        st.success(f"✅ 相符 ({pdf_dt})")
                    else:
                        st.error(f"❌ 異常 (PDF: {pdf_dt})")
        st.divider()

except Exception as e:
    st.error(f"⚠️ 讀取試算表失敗，請確認連結與權限：{e}")
