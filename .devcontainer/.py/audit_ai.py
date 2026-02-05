import pandas as pd
import requests
import pytesseract
from pdf2image import convert_from_bytes
import re

# --- 1. 設定 Tesseract ---
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# --- 2. 你的試算表 ---
SHEET_URL = "https://docs.google.com/spreadsheets/d/1BA427GfGw41UWen083KSWxbdRwbe3a1SEF_H89MyBZE/export?format=csv&gid=1439172114"

def audit_cloud_file(row_index):
    print(f"📊 正在讀取試算表第 {row_index + 1} 筆資料...")
    df = pd.read_csv(SHEET_URL)
    
    # 抓取試算表裡的資料
    target_row = df.iloc[row_index]
    sheet_date = str(target_row['到期日期']).strip()
    pdf_link = str(target_row['檔案連結']) # 假設你的連結欄位叫「檔案連結」
    
    print(f"🔗 正在從雲端抓取 PDF 檔案...")
    
    try:
        # 這裡的邏輯是：直接從網址下載 PDF 到記憶體，不存到桌面
        # 注意：Google Drive 的連結需要特殊轉換才能直接下載
        file_id = pdf_link.split('/')[-2] if 'view' in pdf_link else pdf_link.split('=')[-1]
        direct_download_url = f'https://drive.google.com/uc?export=download&id={file_id}'
        
        response = requests.get(direct_download_url)
        
        # 將 PDF 轉為圖片辨識
        images = convert_from_bytes(response.content, dpi=200)
        
        for i, img in enumerate(images):
            text = pytesseract.image_to_string(img, lang='chi_tra')
            match = re.search(r"(\d{2,3})\s*年\s*(\d{1,2})\s*月\s*(\d{1,2})\s*日", text)
            
            if match:
                yy, mm, dd = match.groups()
                pdf_date = f"{int(yy)+1911}-{mm.zfill(2)}-{dd.zfill(2)}"
                print(f"🎯 AI 在 PDF 第 {i+1} 頁找到日期：{pdf_date}")
                
                print("-" * 30)
                if pdf_date == sheet_date:
                    print(f"✅ 【核對成功】雲端檔案日期吻合！")
                else:
                    print(f"❌ 【核對失敗】表格是 {sheet_date}，但 PDF 裡是 {pdf_date}")
                return
                
    except Exception as e:
        print(f"❌ 無法讀取雲端檔案：{e}")
        print("💡 提示：請確認該 PDF 在雲端已開啟「知道連結的任何人皆可檢視」。")

if __name__ == "__main__":
    # 你想核對第幾筆，這裡就改幾 (第 1 筆是 0, 第 7 筆是 6)
    target = int(input("請輸入你想核對的列號 (例如第1筆請輸入1): ")) - 1
    audit_cloud_file(target)
