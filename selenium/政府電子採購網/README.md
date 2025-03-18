# 政府電子採購網爬蟲

此專案示範如何使用 Selenium 爬取政府電子採購網的招標資訊。

## 免責聲明

- 本程式碼僅供學習和研究使用
- 切勿用於非法用途，如有侵權請聯繫刪除
- 請注意控制爬取速度，避免對目標網站造成影響
- 建議先閱讀目標網站的 robots.txt 文件
- 政府網站的數據僅供參考，請以官方公佈為準

## 環境需求

- Python 3.7+
- Chrome 瀏覽器
- ChromeDriver

## 安裝指南

### 安裝 ChromeDriver

macOS:
```bash
brew install chromedriver
```

Windows:
```bash
choco install chromedriver
```

### 安裝相依套件

```bash
pip install --upgrade selenium undetected-chromedriver requests lxml fake-useragent
```

## Ubuntu/Linux 環境

```bash
apt-get update
apt-get install -y --upgrade chromium-chromedriver
```

## 使用方式

1. 安裝所需套件
2. 確認 ChromeDriver 版本與 Chrome 瀏覽器版本相符
3. 修改 _config.json 改檔案名稱為 config.json，並設定相關參數
4. 執行程式：
```bash
python main.py
```

## 錯誤排除

1. 在執行爬蟲過程中，若發現詳情頁無法正常載入，可能是網站的反爬機制檢測到了爬蟲行為，請打開瀏覽器，手動輸入網址，並完成驗證後(目前為樸克牌圖形驗證機制)再次執行爬蟲。
2. 版本問題，請確認 ChromeDriver 版本與 Chrome 瀏覽器版本相符；webdriver-manager 會自動下載相應版本的 ChromeDriver，但有時會出現版本不相符的問題，此時可以手動下載相應版本的 ChromeDriver，並將其放在 PATH 中。

## 注意事項

- 請遵守網站的使用條款和政策
- 建議設定適當的請求延遲時間
- 定期檢查程式的執行狀態和日誌
