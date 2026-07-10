#!/usr/bin/env python3
"""抓取 Google Trends 台灣熱搜 RSS，輸出 trends.json 供前端讀取。"""
import json
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone

RSS_URL = "https://trends.google.com/trending/rss?geo=TW"
NS = {"ht": "https://trends.google.com/trending/rss"}
TW_TZ = timezone(timedelta(hours=8))


def main():
    req = urllib.request.Request(RSS_URL, headers={"User-Agent": "Mozilla/5.0"})
    xml_data = urllib.request.urlopen(req, timeout=30).read()
    root = ET.fromstring(xml_data)

    items = []
    for it in root.iter("item"):
        kw = " ".join((it.findtext("title") or "").split())
        if not kw:
            continue
        traffic = it.findtext("ht:approx_traffic", default="", namespaces=NS)
        news = None
        n = it.find("ht:news_item", NS)
        if n is not None:
            t = n.findtext("ht:news_item_title", default="", namespaces=NS)
            u = n.findtext("ht:news_item_url", default="", namespaces=NS)
            if t and u:
                news = {"t": t, "u": u}
        items.append({"kw": kw, "traffic": traffic, "news": news})

    if not items:
        raise SystemExit("No items parsed; keep previous trends.json")

    out = {
        "updated": datetime.now(TW_TZ).strftime("%Y-%m-%d %H:%M"),
        "items": items[:20],
    }
    with open("trends.json", "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    print("Wrote", len(out["items"]), "items")


if __name__ == "__main__":
    main()
