# 台灣即時熱搜排行榜 🔥

> 一頁掌握今天台灣大家都在搜什麼。

**線上使用：[trend.sectools.tw](https://trend.sectools.tw)**

![GitHub Pages](https://img.shields.io/badge/Hosted%20on-GitHub%20Pages-222?logo=github)
![License](https://img.shields.io/badge/license-MIT-blue)
![No Dependencies](https://img.shields.io/badge/dependencies-0-brightgreen)

## 這是什麼？

打開網頁就能看到 **Google 台灣即時熱搜關鍵字排行榜**。每個關鍵字點一下就會展開快速動作，回答使用者最想知道的問題——「這個詞為什麼在燒？」

- 🔍 **Google 一下**：直接搜尋該關鍵字
- 📰 **相關新聞**：跳轉 Google News 看事件脈絡
- 💬 **到 Threads 討論**：看社群上大家怎麼說
- 📋 **複製關鍵字**：一鍵複製，方便轉貼

除了即時熱搜，頁面下方還整理了台灣近期的重點趨勢（連假、旅遊、社群、AI），以及 DailyView、公視熱門議題等延伸資訊來源。

## 功能特色

| 功能 | 說明 |
|------|------|
| ⚡ 每小時更新 | GitHub Actions 每小時抓取 Google Trends 台灣熱搜，累積 24 小時內上榜的關鍵字 |
| 🖼️ 圖文卡片 | 前三名大圖卡、每個關鍵字附新聞縮圖與最多 3 則相關新聞 |
| 🗓️ 7 天回顧 | 錯過的熱搜一鍵回看（`history.json`） |
| 🔎 搜尋與排序 | 依熱度或最新排序、即時篩選關鍵字 |
| 🚀 SEO 預渲染 | 每次更新把熱搜寫進 `index.html` 標題、描述與結構化資料，並更新 `sitemap.xml` |
| 🌗 深淺色模式 | 一鍵切換，自動記住偏好，預設跟隨系統設定 |
| 📤 社群分享 | 原生分享、Threads、Facebook、LINE，也能單獨分享某個關鍵字 |
| 📱 響應式設計 | 手機、平板、桌機都好讀 |
| 🪶 零依賴 | 純 HTML/CSS/JavaScript 單一檔案，無任何框架與外部套件 |
| 🛟 離線備援 | 即時來源連不上時自動顯示內建快照，頁面永遠不會開天窗 |

## 運作原理

```
GitHub Actions（每小時）
      │
      ▼
抓取 Google Trends RSS (geo=TW)
      │  scripts/fetch_trends.py 解析 XML
      ▼
輸出 trends.json / history.json、預渲染 index.html → commit 回 repo → GitHub Pages 自動重新部署
      │
      ▼
使用者開啟頁面 → fetch 同源 trends.json → 渲染熱搜卡片
      │
      ▼ 讀取失敗時
顯示內建快照資料（graceful degradation）
```

這個設計不依賴任何第三方 CORS proxy、不需要伺服器，頁面載入也更快。
資料來源：[Google Trends RSS](https://trends.google.com/trending/rss?geo=TW)，非官方 API，僅作展示用途。也可以到 Actions 頁面手動觸發 `Update trends` workflow 立即更新。

## 本地開發

不需要安裝任何東西：

```bash
git clone https://github.com/stwater20/trend.git
cd trend
# 直接用瀏覽器打開 index.html，或起一個簡單的 server：
python3 -m http.server 8000
```

## 自行部署

1. Fork 這個 repo
2. Settings → Pages → Source 選 `main` branch
3. （選用）綁定自己的網域：Pages 設定填入 Custom domain，並到 DNS 加一筆 CNAME 指向 `<你的帳號>.github.io`
4. 修改 `index.html` 與 `scripts/fetch_trends.py` 裡的網址與 GitHub repo

## 貢獻

歡迎開 Issue 或 PR！一些可以做的方向：

- [x] OG 分享縮圖
- [x] 熱搜關鍵字歷史紀錄（近 7 天）
- [ ] 更多資料來源（Threads 趨勢話題、PTT 熱門看板）
- [x] 加入主畫面（Web App Manifest）

## 授權

MIT License — 隨意使用、修改、散布。
