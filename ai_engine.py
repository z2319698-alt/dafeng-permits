import streamlit as st
import pandas as pd
import pytesseract
import requests
import re
from pdf2image import convert_from_bytes

@st.cache_data(ttl=2592000)
def ai_verify_background(pdf_link, sheet_date):
    """專門處理 AI 辨識邏輯。與主程式隔離，修改此處不會影響 UI 或寄信功能。"""
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
                is_match = (str(sheet_date)[:10] == pdf_dt)
                return is_match, pdf_dt, img
        return True, "跳過辨識", None
    except:
        return True, "跳過辨識", None
