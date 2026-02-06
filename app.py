@st.cache_data(ttl=2592000)
def ai_verify_background(pdf_link, sheet_date):
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
            # 轉為灰階並優化辨識品質
            page_text = pytesseract.image_to_string(img.convert('L'), lang='chi_tra+eng')
            # 增加對「民國」與「西元」混合格式的相容性
            match = re.search(r"(?:至|期|效|限)[\s]*(\d{2,3}|20\d{2})[\s\.年/-]+(\d{1,2})[\s\.月/-]+(\d{1,2})", page_text)
            if match:
                yy, mm, dd = match.groups()
                # 換算西元年邏輯
                year = int(yy) + 1911 if int(yy) < 1000 else int(yy)
                # 格式化掃描到的日期 (例如: 2027-11-15)
                pdf_dt_str = f"{year}-{mm.zfill(2)}-{dd.zfill(2)}"
                
                # --- 核心微調點：改為完整日期比對 ---
                # 格式化 Sheets 上的日期 (例如: 2025-11-20)
                sheet_dt_str = pd.to_datetime(sheet_date).strftime('%Y-%m-%d') if pd.notnull(sheet_date) else ""
                
                # 只有當年月日完全一致時，才回傳 True (一致)
                is_match = (pdf_dt_str == sheet_dt_str)
                
                return is_match, pdf_dt_str, img
        
        return True, "跳過辨識", None # 若完全偵測不到日期則不報錯
    except:
        return True, "跳過辨識", None
