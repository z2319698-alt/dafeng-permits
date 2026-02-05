import pandas as pd
import requests
import pytesseract
from pdf2image import convert_from_bytes
import re
import os

# --- 1. 設定 Tesseract 路徑 ---
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# --- 2. 雲端試算表設定 ---
SHEET_URL = "https://docs.google.com/spreadsheets/d/1BA427GfGw41UWen083KSWxbdRwbe3a1SEF_H89MyBZE/export?format=csv&gid=1439172114"

# --- 3. 關鍵字清單 (根據你提供的整理) ---
KEYWORDS = ["有效日期", "有效期限", "有效期間", "發文次日至", "許可期限", "起至"]

def start_audit():
    print("==========================================")
    print("📊 正在讀取雲端試算表資料...")
    try:
        df = pd.read_csv(SHEET_URL)
        target = int(input("🔢 請輸入你想核對的列號 (例如第7筆請輸入7): ")) - 1
        
        sheet_date = str(df.iloc[target]['到期日期']).strip()
        # 這裡假設你的連結欄位名稱是「檔案連結」，請視情況修改
        pdf_link = str(df.iloc[target]['檔案連結']).strip() 
        
        print(f"✅ 試算表目標日期：{sheet_date}")
    except Exception as e:
        print(f"❌ 讀取失敗：{e}")
        return

    print(f"🌐 正在從雲端下載 PDF 進行辨識...")
    try:
        # 轉換 Google Drive 連結為直接下載格式
        file_id = ""
        if 'id=' in pdf_link:
            file_id = pdf_link.split('id=')[-1].split('&')[0]
        elif '/d/' in pdf_link:
            file_id = pdf_link.split('/d/')[1].split('/')[0]
        
        direct_url = f'https://drive.google.com/uc?export=download&id={file_id}'
        response = requests.get(direct_url)
        
        # 轉為圖片 (dpi=200 提升辨識率)
        pages = convert_from_bytes(response.content, dpi=200)
        
        found_date = None
        for i, page in enumerate(pages):
            print(f"正在掃描第 {i+1} 頁...", end="\r")
            text = pytesseract.image_to_string(page, lang='chi_tra')
            
            # 檢查是否含有任一關鍵字
            if any(k in text for k in KEYWORDS):
                # 搜尋日期格式：支援 116年10月20日、116.10.20、116/10/20
                match = re.search(r"(\d{2,3})[\s\.年/]*(\d{1,2})[\s\.月/]*(\d{1,2})", text)
                if match:
                    yy, mm, dd = match.groups()
                    # 民國轉西元
                    year = int(yy) + 1911 if int(yy) < 1911 else int(yy)
                    found_date = f"{year}-{mm.zfill(2)}-{dd.zfill(2)}"
                    print(f"\n🎯 成功在第 {i+1} 頁找到符合關鍵字的日期！")
                    break
        
        if found_date:
            print(f"📄 PDF 辨識結果 (已轉西元)：{found_date}")
            print("-" * 30)
            # 比對邏輯 (忽略橫槓或斜線差異)
            if found_date.replace('-', '') == sheet_date.replace('-', ''):
                print("🏁 核對結果：【✅ 完美吻合】")
            else:
                print("🏁 核對結果：【❌ 不吻合】")
                print(f"   試算表：{sheet_date}")
                print(f"   PDF 內容：{found_date}")
            print("-" * 30)
        else:
            print("\n⚠️ 遍尋所有頁面皆未找到包含關鍵字的日期，請檢查 PDF 解析度。")

    except Exception as e:
        print(f"\n❌ 執行過程發生錯誤：{e}")

if __name__ == "__main__":
    start_audit()
