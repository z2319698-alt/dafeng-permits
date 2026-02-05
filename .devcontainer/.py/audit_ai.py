import pandas as pd
import requests
import pytesseract
from pdf2image import convert_from_bytes
import re

# --- 1. 設定 Tesseract ---
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# --- 2. 你的雲端試算表連結 ---
SHEET_URL = "https://docs.google.com/spreadsheets/d/1BA427GfGw41UWen083KSWxbdRwbe3a1SEF_H89MyBZE/export?format=csv&gid=1439172114"

# --- 3. 你的日期關鍵字 ---
KEYWORDS = ["有效日期", "有效期限", "有效期間", "發文次日至", "許可期限", "起至"]

def cloud_audit():
    print("📊 正在讀取雲端試算表資料...")
    try:
        # 讀取試算表
        df = pd.read_csv(SHEET_URL)
        idx = int(input("🔢 請輸入要核對的列號 (全興廠請輸1, 竹北廠請輸7): ")) - 1
        
        # 取得到期日期與 PDF 雲端連結
        sheet_date = str(df.iloc[idx]['到期日期']).strip()
        pdf_link = str(df.iloc[idx]['PDF連結']).strip()
        print(f"✅ 試算表紀錄日期：{sheet_date}")
        
        # 轉換 Google Drive 連結為直接下載格式
        file_id = pdf_link.split('/')[-2] if '/file/d/' in pdf_link else pdf_link.split('id=')[-1]
        direct_url = f'https://drive.google.com/uc?export=download&id={file_id}'
        
        print(f"🌐 正在從雲端抓取 PDF 內容...")
        response = requests.get(direct_url)
        
        # 將雲端下載的 PDF 轉為圖片辨識 (不存檔)
        pages = convert_from_bytes(response.content, dpi=200)
        
        found_date = None
        for i, page in enumerate(pages):
            text = pytesseract.image_to_string(page, lang='chi_tra')
            
            # 搜尋關鍵字與日期 (支援民國轉西元)
            if any(k in text for k in KEYWORDS):
                match = re.search(r"(\d{2,3})[\s\.年/]*(\d{1,2})[\s\.月/]*(\d{1,2})", text)
                if match:
                    yy, mm, dd = match.groups()
                    year = int(yy) + 1911 if int(yy) < 1911 else int(yy)
                    found_date = f"{year}-{mm.zfill(2)}-{dd.zfill(2)}"
                    print(f"🎯 在 PDF 第 {i+1} 頁找到日期：{found_date}")
                    break
        
        if found_date:
            print("-" * 30)
            if found_date.replace('-', '') == sheet_date.replace('-', ''):
                print("🏁 核對結果：【✅ 完美吻合】")
            else:
                print(f"🏁 核對結果：【❌ 不吻合】(PDF:{found_date} / 表格:{sheet_date})")
        else:
            print("⚠️ 沒找到日期，請確認雲端 PDF 的關鍵字是否正確。")

    except Exception as e:
        print(f"❌ 執行出錯：{e}")

if __name__ == "__main__":
    cloud_audit()
