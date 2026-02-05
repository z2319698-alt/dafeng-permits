import pandas as pd
import pytesseract
from pdf2image import convert_from_path
import re
import os

# --- 設定區 ---
# 1. 識字大腦路徑
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# 2. 你的試算表網址 (轉為 CSV 下載格式)
SHEET_URL = "https://docs.google.com/spreadsheets/d/1BA427GfGw41UWen083KSWxbdRwbe3a1SEF_H89MyBZE/export?format=csv&gid=1439172114"

def start_audit():
    print("📊 正在讀取 Google 試算表資料...")
    try:
        df = pd.read_csv(SHEET_URL)
        # 假設你的試算表有一欄叫 '到期日期'，請確認欄位名稱
        sheet_date = str(df.iloc[0]['到期日期']).strip() 
        print(f"📌 試算表記錄的日期為: {sheet_date}")
    except Exception as e:
        print(f"❌ 讀取試算表失敗: {e}")
        return

    print("\n🔍 正在辨識本地 PDF 檔案...")
    # 這裡先抓你資料夾裡的第一個 PDF
    pdf_files = [f for f in os.listdir('.') if f.lower().endswith('.pdf')]
    if not pdf_files:
        print("📁 找不到 PDF 檔案，請確認檔案放在 .py 資料夾內。")
        return

    target_pdf = pdf_files[0]
    try:
        pages = convert_from_path(target_pdf, dpi=200, first_page=1, last_page=1)
        text = pytesseract.image_to_string(pages[0], lang='chi_tra')
        
        # 抓取民國年格式 (例如 115 年 10 月 20 日)
        match = re.search(r"(\d{2,3})\s*年\s*(\d{1,2})\s*月\s*(\d{1,2})\s*日", text)
        if match:
            yy, mm, dd = match.groups()
            pdf_date = f"{int(yy)+1911}/{mm.zfill(2)}/{dd.zfill(2)}"
            print(f"📄 PDF 辨識到的日期為: {pdf_date}")
            
            # --- 進行核對 ---
            print("\n--- 核對結果 ---")
            if pdf_date in sheet_date or sheet_date in pdf_date:
                print("✅ 【吻合】PDF 日期與試算表一致！")
            else:
                print(f"❌ 【不吻合】兩邊日期不同！(PDF: {pdf_date} vs 表格: {sheet_date})")
        else:
            print("⚠️ 無法在 PDF 中找到日期格式。")
            
    except Exception as e:
        print(f"❌ 辨識過程發生錯誤: {e}")

if __name__ == "__main__":
    start_audit()
