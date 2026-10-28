"""文京区議会インターネット議会中継（公式）の「議員名で選ぶ」から、議員ごとの一般質問の録画を集めて data/videos.json に書く。
出典：https://bunkyo-city.stream.jfit.co.jp/?tpl=speaker_list
使い方：python tools/import_videos.py
・載せるのは、日付・会議名・再生ページのリンクだけ（質問の題名は載せない。分量の差で印象が変わらないように）。
・議員名は中継サイトの表記。候補者データとの対応は NAME_MAP と空白を除いた一致で取る。
"""
import datetime
import html
import json
import pathlib
import re
import urllib.request

BASE = "https://bunkyo-city.stream.jfit.co.jp/"
ROOT = pathlib.Path(__file__).resolve().parent.parent
UA = {"User-Agent": "Mozilla/5.0 (bunkyo-senkyo.jp; navi2027)"}
# 中継サイトの表記 → このサイトの表記（空白を除いて比べても一致しないもの）
NAME_MAP = {"豪一": "佐藤 豪一", "田中香澄": "田中 かすみ"}


def get(url):
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=30) as r:
        return r.read().decode("utf-8", "replace")


def text(s):
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", s))).strip()


def era(y, m, d):
    # 令和n年 → 西暦
    return f"{2018 + int(y)}-{int(m):02d}-{int(d):02d}"


def main():
    top = get(BASE + "?tpl=speaker_list")
    people = re.findall(r'<a class="speaker__link" href="/\?tpl=speaker_result&amp;speaker_id=(\d+)">([^<]+)</a>', top)
    out = {"fetched": datetime.date.today().isoformat(), "source": BASE + "?tpl=speaker_list", "members": {}}
    for sid, raw in people:
        name = re.sub(r"（.*?）", "", raw).replace("　", "").replace(" ", "").strip()
        name = NAME_MAP.get(name, name)
        page = get(BASE + f"?tpl=speaker_result&speaker_id={sid}")
        items = []
        # 1件ずつ：「令和◯年◯月定例議会 ◯月◯日 本会議 一般質問 … 再生（play_vod&inquiry_id=…）」
        body = page.split("検索結果一覧", 1)[-1]
        for block in re.split(r"(?=令和\s*\d+\s*年\s*\d+\s*月)", body):
            m = re.match(r"令和\s*(\d+)\s*年\s*(\d+)\s*月([^<]*?定例議会)", text(block))
            v = re.search(r'tpl=play_vod&amp;inquiry_id=(\d+)', block)
            if not (m and v):
                continue
            t = text(block)
            dm = re.search(r"(\d+)\s*月\s*(\d+)\s*日\s*(\S+)\s*(\S+)", t[m.end():])
            year = m.group(1)
            date = era(year, dm.group(1), dm.group(2)) if dm else ""
            items.append({"date": date, "meeting": f"令和{year}年{m.group(2)}月{m.group(3).strip()}",
                          "kind": f"{dm.group(3)} {dm.group(4)}" if dm else "",
                          "url": BASE + f"?tpl=play_vod&inquiry_id={v.group(1)}"})
        out["members"][name] = {"speaker_url": BASE + f"?tpl=speaker_result&speaker_id={sid}", "label": raw.strip(), "items": items}
        print(name, len(items), [i["date"] for i in items])
    (ROOT / "data/videos.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
