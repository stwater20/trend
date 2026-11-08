#!/usr/bin/env python3
"""抓取 Google Trends 台灣熱搜 RSS，輸出 trends.json / history.json，
並把最新熱搜預先寫進 index.html（SEO 與首屏秒開）與 sitemap.xml。"""
import html
import json
import re
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime

RSS_URL = "https://trends.google.com/trending/rss?geo=TW"
SITE_URL = "https://trend.sectools.tw/"
NS = {"ht": "https://trends.google.com/trending/rss"}
TW_TZ = timezone(timedelta(hours=8))
POOL_HOURS = 24      # 熱搜池保留時間：RSS 一次只給約 10 筆，累積 24 小時內的關鍵字
MAX_ITEMS = 30
HISTORY_DAYS = 7


def traffic_num(s):
    m = re.match(r"([\d,]+)", s or "")
    return int(m.group(1).replace(",", "")) if m else 0


def fetch_rss(now):
    req = urllib.request.Request(RSS_URL, headers={"User-Agent": "Mozilla/5.0"})
    root = ET.fromstring(urllib.request.urlopen(req, timeout=30).read())
    items = []
    for it in root.iter("item"):
        kw = " ".join((it.findtext("title") or "").split())
        if not kw:
            continue
        try:
            start = parsedate_to_datetime(it.findtext("pubDate")).astimezone(TW_TZ)
        except (TypeError, ValueError):
            start = now
        news = []
        for n in it.findall("ht:news_item", NS):
            t = n.findtext("ht:news_item_title", default="", namespaces=NS).strip()
            u = n.findtext("ht:news_item_url", default="", namespaces=NS).strip()
            s = n.findtext("ht:news_item_source", default="", namespaces=NS).strip()
            if t and u:
                news.append({"t": html.unescape(t), "u": u, "s": s})
        items.append({
            "kw": kw,
            "traffic": it.findtext("ht:approx_traffic", default="", namespaces=NS),
            "start": start.isoformat(timespec="minutes"),
            "pic": it.findtext("ht:picture", default="", namespaces=NS),
            "news": news[:3],
        })
    return items


def load_json(path, default):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return default


def merge_pool(fresh, prev, now):
    """新抓到的關鍵字與前次資料合併，保留 POOL_HOURS 內出現過的熱搜。"""
    prev_updated = prev.get("updated_iso")
    if not prev_updated and prev.get("updated"):            # 舊格式只有 "YYYY-MM-DD HH:MM"
        prev_updated = prev["updated"].replace(" ", "T") + "+08:00"
    prev_updated = prev_updated or now.isoformat(timespec="minutes")
    pool = {}
    for it in prev.get("items", []):
        it = dict(it)
        it.setdefault("start", prev_updated)          # 舊格式沒有 start
        if isinstance(it.get("news"), dict):           # 舊格式 news 是單一物件
            it["news"] = [it["news"]]
        it["news"] = it.get("news") or []
        pool[it["kw"].lower()] = it
    for it in fresh:
        old = pool.get(it["kw"].lower())
        if old:
            if traffic_num(old.get("traffic")) > traffic_num(it["traffic"]):
                it["traffic"] = old["traffic"]
            it["start"] = min(it["start"], old["start"])
            it["news"] = it["news"] or old["news"]
            it["pic"] = it["pic"] or old.get("pic", "")
        pool[it["kw"].lower()] = it
    cutoff = now - timedelta(hours=POOL_HOURS)
    items = [it for it in pool.values()
             if datetime.fromisoformat(it["start"]) >= cutoff]
    items.sort(key=lambda it: (traffic_num(it["traffic"]), it["start"]), reverse=True)
    return items[:MAX_ITEMS]


def update_history(history, items, now):
    days = history.get("days", {})
    for it in items:
        day = it["start"][:10]
        lst = {x["kw"].lower(): x for x in days.get(day, [])}
        old = lst.get(it["kw"].lower())
        if not old or traffic_num(it["traffic"]) > traffic_num(old["traffic"]):
            lst[it["kw"].lower()] = {"kw": it["kw"], "traffic": it["traffic"]}
        days[day] = sorted(lst.values(), key=lambda x: traffic_num(x["traffic"]), reverse=True)[:20]
    keep = sorted(days, reverse=True)[:HISTORY_DAYS]
    return {"days": {d: days[d] for d in sorted(keep, reverse=True)}}


def esc(s):
    return html.escape(s or "", quote=True)


def prerender(data, now):
    """把熱搜寫進 index.html 的標記區塊，讓搜尋引擎與無 JS 環境也看得到內容。"""
    with open("index.html", encoding="utf-8") as f:
        page = f.read()
    items = data["items"]
    top = [it["kw"] for it in items[:3]]
    date_label = f"{now.month}/{now.day}"

    title = f"台灣即時熱搜排行榜 {date_label}｜{'、'.join(top)}… 今天大家在搜什麼"
    desc = (f"{now.month} 月 {now.day} 日台灣 Google 熱搜：" + "、".join(it["kw"] for it in items[:6])
            + "。每小時自動更新，點關鍵字立刻看相關新聞與討論。")
    page = re.sub(r"<title>.*?</title>", f"<title>{esc(title)}</title>", page, flags=re.S)
    page = re.sub(r'(<meta name="description" content=")[^"]*(")', rf"\g<1>{esc(desc)}\g<2>", page)
    page = re.sub(r'(<meta property="og:description" content=")[^"]*(")', rf"\g<1>{esc(desc)}\g<2>", page)

    lis = []
    for i, it in enumerate(items):
        head = it["news"][0]["t"] if it["news"] else ""
        lis.append(f'<li><b>{i + 1}. {esc(it["kw"])}</b> {esc(it["traffic"])} 次搜尋'
                   + (f' — {esc(head)}' if head else "") + "</li>")
    static = "<ol class=\"seo-list\">" + "".join(lis) + "</ol>"
    page = re.sub(r"<!--TRENDS-->.*?<!--/TRENDS-->", lambda _: f"<!--TRENDS-->{static}<!--/TRENDS-->", page, flags=re.S)

    ld = {
        "@context": "https://schema.org", "@type": "ItemList",
        "name": f"台灣 Google 熱搜關鍵字 {now:%Y-%m-%d}",
        "itemListElement": [{"@type": "ListItem", "position": i + 1, "name": it["kw"]}
                            for i, it in enumerate(items[:20])],
    }
    page = re.sub(r'(<script type="application/ld\+json" id="ld-list">).*?(</script>)',
                  lambda m: m.group(1) + json.dumps(ld, ensure_ascii=False) + m.group(2), page, flags=re.S)
    # 內嵌資料：首屏不必等 fetch
    embedded = json.dumps(data, ensure_ascii=False).replace("</", "<\\/")
    page = re.sub(r'(<script type="application/json" id="data">).*?(</script>)',
                  lambda m: m.group(1) + embedded + m.group(2), page, flags=re.S)
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(page)

    with open("sitemap.xml", "w", encoding="utf-8") as f:
        f.write('<?xml version="1.0" encoding="UTF-8"?>\n'
                '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
                f"  <url><loc>{SITE_URL}</loc><lastmod>{now.isoformat(timespec='seconds')}</lastmod>"
                "<changefreq>hourly</changefreq><priority>1.0</priority></url>\n"
                "</urlset>\n")


def main():
    now = datetime.now(TW_TZ)
    fresh = fetch_rss(now)
    if not fresh:
        raise SystemExit("No items parsed; keep previous trends.json")

    items = merge_pool(fresh, load_json("trends.json", {}), now)
    history = update_history(load_json("history.json", {}), items, now)
    data = {
        "updated": now.strftime("%Y-%m-%d %H:%M"),
        "updated_iso": now.isoformat(timespec="minutes"),
        "items": items,
        "history": history["days"],
    }
    with open("trends.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
    with open("history.json", "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=1)
    prerender(data, now)
    print("Wrote", len(items), "items")


if __name__ == "__main__":
    main()
