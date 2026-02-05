import pytesseract
from pdf2image import convert_from_path
import re
import os

# --- 1. 免費軟體路徑設定 (請先安裝 Tesseract) ---
# 如果你安裝在預設位置，這行不用動
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# --- 2. 設定你的 PDF 資料夾路徑 ---
# 請將下面括號內的文字改成你電腦裡存放 PDF 的實際路徑，例如 r"C:\Users\Desktop\PDF_Files"
FOLDER_PATH = r"請填入你的PDF資料夾路徑" 

def scan_and_audit():
    print("------------------------------------------")
    if not os.path.exists(FOLDER_PATH):
        print(f"❌ 錯誤：找不到資料夾！路徑是否正確？\n目前設定為: {FOLDER_PATH}")
        return

    files = [f for f in os.listdir(FOLDER_PATH) if f.lower().endswith('.pdf')]
    if not files:
        print(f"📁 資料夾內沒有找到 PDF 檔案。")
        return

    print(f"🔍 AI 巡檢員啟動！找到 {len(files)} 個檔案，開始識圖...")

    for filename in files:
        file_path = os.path.join(FOLDER_PATH, filename)
        try:
            # 將 PDF 第一頁轉為圖片 (解析度 200 dpi)
            # 注意：這需要安裝 poppler
            pages = convert_from_path(file_path, dpi=200, first_page=1, last_page=1)
            
            # 使用 Tesseract AI 識圖 (指定繁體中文)
            text = pytesseract.image_to_string(pages[0], lang='chi_tra')
            
            # 尋找民國年日期 (例：115 年 10 月 20 日)
            match = re.search(r"(\d{2,3})\s*年\s*(\d{1,2})\s*月\s*(\d{1,2})\s*日", text)
            if match:
                yy, mm, dd = match.groups()
                ad_year = int(yy) + 1911
                print(f"✅ [成功] 檔名: {filename}")
                print(f"   -> AI 判定到期日: {ad_year}-{mm.zfill(2)}-{dd.zfill(2)}")
            else:
                print(f"⚠️ [警告] 檔名: {filename} -> AI 看到文字但找不到日期格式。")
                
        except Exception as e:
            print(f"❌ [失敗] 檔案 {filename}: {e}")
            print("   (提示：請確認是否已安裝 Poppler 並設定路徑)")

    print("------------------------------------------")
    print("🎉 巡檢任務結束！")

if __name__ == "__main__":
    scan_and_audit()
