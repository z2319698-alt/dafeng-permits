from flask import Flask, render_template, jsonify
import pandas as pd
import requests
import pytesseract
from pdf2image import convert_from_bytes
import re
import os

app = Flask(__name__)

# --- 1. 這裡放你原本的設定 (不要動到它們) ---
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
SHEET_URL = "你的 Google 試算表連結" # 這裡請填入你原本那串長長的網址

# --- 2. 你原本的的首頁路由 (讀取表格顯示在網頁上) ---
@app.route('/')
def index():
    # 這裡是你原本讀取 CSV 並 render_template('index.html', ...) 的地方
    df = pd.read_csv(SHEET_URL)
    data = df.to_dict(orient='records')
    return render_template('index.html', data=data)

# --- 3. 新增的 AI 核對後端 (這就是我剛才給你的核心代碼) ---
@app.route('/api/check_date/<int:row_index>')
def check_date(row_index):
    try:
        df = pd.read_csv(SHEET_URL)
        target_row = df.iloc[row_index]
        sheet_date = str(target_row['到期日期']).strip()
        # 注意：請確認你的 Excel 連結欄位名稱，如果是「PDF連結」就改為 ['PDF連結']
        pdf_link = str(target_row['檔案連結']).strip() 
        
        # 轉換連結並抓取
        file_id = pdf_link.split('/')[-2] if '/file/d/' in pdf_link else pdf_link.split('id=')[-1]
        direct_url = f'https://drive.google.com/uc?export=download&id={file_id}'
        
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
        
        is_match = (found_date.replace('-','') == sheet_date.replace('-',''))
        return jsonify({
            "status": "success",
            "sheet_date": sheet_date,
            "pdf_date": found_date,
            "match": is_match
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

# --- 4. 啟動伺服器 ---
if __name__ == "__main__":
    app.run(debug=True)
