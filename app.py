import streamlit as st
import pandas as pd
import requests
import pytesseract
from pdf2image import convert_from_bytes
import re

# --- 1. 基礎設定 ---
st.set_page_config(page_title="大豐環保證照管理系統", layout="wide")
st.title("📋 證照到期 AI 自動核對系統")

# Google 試算表 CSV 連結
SHEET_URL = "https://docs.google.com/spreadsheets/d/1BA427GfGw41UWen083KSWxbdRwbe3a1SEF_H89MyBZE/export?format=csv&gid=1439172114"

# Tesseract 路徑 (本地測試用，Streamlit Cloud 部署時需另設)
# pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# --- 2. 核心 AI 核對函數 ---
def verify_pdf_date(pdf_link, sheet_date):
    try:
        # 轉換連結
        file_id = pdf_link.split('/')[-2] if '/file/d/' in pdf_link else pdf_link.split('id=')[-1]
        direct_url = f'https://drive.google.com/uc?export=download&id={file_id}'
        
        # 下載並辨識
        response = requests.get(direct_url)
        pages = convert_from_bytes(response.content, dpi=150)
        
        found_date = "未找到"
        keywords = ["有效日期", "有效期限", "有效期間", "發文次日至", "許可期限", "起至"]
        
        for page in pages:
            text = pytesseract.image_to_string(page, lang='chi_tra')
            if any(k in text for k in keywords):
                match = re.search(r"(\d{2,3})[\s\.年/]*(\d{1,2})[\s\.月/]*(\d{1,2})", text)
                if match:
                    yy, mm, dd = match.groups()
                    year = int(yy) + 1911 if int(yy) < 1911 else int(yy)
                    found_date = f"{year}-{mm.zfill(2)}-{dd.zfill(2)}"
                    break
        
        # 比對
        is_match = (found_date.replace('-','') == str(sheet_date).replace('-',''))
        return is_match, found_date
    except Exception as e:
        return False, f"錯誤: {str(e)}"

# --- 3. 讀取並顯示資料 ---
try:
    df = pd.read_csv(SHEET_URL)
    
    # 建立表格
    for index, row in df.iterrows():
        col1, col2, col3, col4 = st.columns([3, 2, 2, 2])
        
        with col1:
            st.write(f"**{row['廠區/名稱']}**")
        with col2:
            st.write(f"📅 到期日: {row['到期日期']}")
        with col3:
            # 下載/查看按鈕
            st.link_button("查看 PDF", row['檔案連結'])
        with col4:
            # AI 核對按鈕 (每個按鈕需要唯一 key)
            if st.button(f"🔍 AI 核對", key=f"btn_{index}"):
                with st.spinner('AI 正在翻閱雲端文件...'):
                    is_ok, pdf_dt = verify_pdf_date(row['檔案連結'], row['到期日期'])
                    if is_ok:
                        st.success(f"✅ 相符 ({pdf_dt})")
                    else:
                        st.error(f"❌ 異常 (PDF內容: {pdf_dt})")
        st.divider()

except Exception as e:
    st.error(f"無法讀取試算表: {e}")
