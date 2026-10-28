"""文京区選挙管理委員会「選挙の記録（令和5年執行 区議会議員選挙・区長選挙）」から、
区議選の年齢階層別・町丁目別の有権者数・投票者数を取り出して data/kiroku_r5.json に書く。
出典：https://www.city.bunkyo.lg.jp/documents/10880/r5kiroku.pdf（p.34〜38）
使い方：python tools/import_kiroku.py <PDFから取り出した文字のファイル(all.txt)>
・投票率は、公表の人数から計算し直す（公表の率に誤記がある行があるため。例：目白台3丁目「410.00」）。
・合計と一致するかを検算し、合わなければ止める。
・投票所の立会人など、個人名が載っている表は取り込まない。
"""
import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
SRC = "https://www.city.bunkyo.lg.jp/documents/10880/r5kiroku.pdf"


def num(x):
    return int(x.replace(",", ""))


def pages(text, a, b):
    m = re.search(rf"--- p{a}\n(.*?)--- p{b + 1}\n", text, re.S)
    return m.group(1)


def main(path):
    t = pathlib.Path(path).read_text(encoding="utf-8")
    # 年齢階層別（PDFの p42 = 冊子の38ページ）
    p = pages(t, 42, 42)
    head = ["18～19", "20～24", "25～29", "30～34", "35～39", "40～44", "45～49", "50～54", "55～59", "60～64", "65～69", "70～74", "75～79", "80以上"]
    rows = [l for l in p.splitlines() if re.match(r"^(男|女|計|平均) [\d,. ]+$", l)]
    elect = [num(x) for x in rows[2].split()[1:]]   # 有権者 計
    voted = [num(x) for x in rows[5].split()[1:]]   # 投票者 計
    assert len(elect) == len(head) + 1 and len(voted) == len(head) + 1
    assert sum(elect[:-1]) == elect[-1] == 178703, "有権者の合計が合いません"
    assert sum(voted[:-1]) == voted[-1] == 93212, "投票者の合計が合いません"
    age = [{"age": h, "electorate": e, "voters": v, "turnout": round(v / e * 100, 2)} for h, e, v in zip(head, elect, voted)]
    # 町丁目別（p38〜39 = 冊子の34〜35ページ）
    q = pages(t, 38, 39)
    town, cur = [], ""
    for l in q.splitlines():
        m = re.match(r"^(?:(\S)\s?(\S)?\s+)?([１２３４５６７])\s+([\d,]+)\s+[\d,]+\s+[\d,]+\s+([\d,]+)\s", l)
        mm = re.match(r"^([^\d\s]+(?:\s[^\d\s]+)?)\s+([１２３４５６７])\s+([\d,]+)\s+[\d,]+\s+[\d,]+\s+([\d,]+)\s", l)
        m2 = re.match(r"^([１２３４５６７])\s+([\d,]+)\s+[\d,]+\s+[\d,]+\s+([\d,]+)\s", l)
        if mm:
            cur = mm.group(1).replace(" ", "").replace("　", "")
            chome, e, v = mm.group(2), num(mm.group(3)), num(mm.group(4))
        elif m2 and cur:
            chome, e, v = m2.group(1), num(m2.group(2)), num(m2.group(3))
        else:
            continue
        town.append({"town": f"{cur}{'１２３４５６７'.index(chome) + 1}丁目", "electorate": e, "voters": v, "turnout": round(v / e * 100, 2)})
    se, sv = sum(x["electorate"] for x in town), sum(x["voters"] for x in town)
    print("町丁目", len(town), "有権者", se, "投票者", sv)
    out = {"source": SRC, "source_label": "文京区選挙管理委員会「令和5年執行 文京区議会議員選挙及び文京区長選挙の記録」", "election": "2023年 文京区議会議員選挙",
           "total": {"electorate": 178703, "voters": 93212, "turnout": 52.16}, "age": age, "town": town,
           "town_check": {"electorate": se, "voters": sv}}
    (ROOT / "data/kiroku_r5.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    for a in age:
        print(a)


if __name__ == "__main__":
    main(sys.argv[1])
