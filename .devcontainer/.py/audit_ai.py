import os
import re
import requests
import pytesseract
from pdf2image import convert_from_bytes

# --- 1. AI 識字大腦設定 ---
# 這是唯一需要留在電腦的東西
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# --- 2. 雲端資料夾設定 (從你的截圖網址抓的) ---
FOLDER_ID = '1nlAUJVghq3RjBhPUsg1-bPI54cdY7uu-'

def download_and_audit():
    print("🌐 正在連線到 Google Drive 雲端資料夾...")
    
    # 這裡我們模擬瀏覽器去抓你的檔案清單 (這需要你的資料夾有開啟「知道連結的人即可檢視」)
    # 如果不想設公開，請告訴我，我教你拿一個簡單的 Token
    url = f"https://drive.google.com/uc?export=download&id=1C72A_8E6jD2G5qWzM8Y5_M8zE6oH1A-A" # 範例 ID
    
    print(f"🔍 正在辨識雲端檔案：大豐環保竹北再利用.pdf")
    
    try:
        # 1. 直接從網路讀取 PDF 到記憶體
        # 注意：這裡我先用你那張 PDF 的直接下載連結測試
        file_id = '1C72A_8E6jD2G5qWzM8Y5_M8zE6oH1A-A' # 這是假設的 ID，需對應你的檔案
        response = requests.get(f'https://drive.google.com/uc?export=download&id={file_id}')
        
        # 2. PDF 轉圖片辨識
        pages = convert_from_bytes(response.content, dpi=200)
        text = pytesseract.image_to_string(pages[0], lang='chi_tra')
        
        # 3. 找日期
        match = re.search(r"(\d{2,3})\s*年\s*(\d{1,2})\s*月\s*(\d{1,2})\s*日", text)
        if match:
            yy, mm, dd = match.groups()
            print(f"\n✅ 【辨識成功】")
            print(f"📄 證件到期日：民國 {yy} 年 {mm} 月 {dd} 日")
            print(f"📅 西元換算：{int(yy)+1911}-{mm.zfill(2)}-{dd.zfill(2)}")
        else:
            print("\n⚠️ AI 有看到字，但沒找到日期格式，請確認 PDF 是否清晰。")
            
    except Exception as e:
        print(f"\n❌ 連線出錯：{e}")
        print("提示：請確認 Tesseract 和 Poppler 是否已就緒。")

if __name__ == "__main__":
    download_and_audit()
