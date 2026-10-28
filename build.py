"""data/*.json から public/ 以下のサイト一式を生成する。
使い方: python3 build.py
データの更新は data/ を直し、このスクリプトで作り直す（ページを直接書き換えない）。
"""
import json, html, pathlib, unicodedata
import robo  # とうひょうくん（ヒョウ柄の投票箱ロボ）の絵
from collections import defaultdict

ROOT = pathlib.Path(__file__).parent
OUT = ROOT / "public"
SITE_URL = "https://bunkyo-senkyo.jp"
# True の間は検索エンジンに載せない（noindex）。本格公開するときに False にして build → push
NOINDEX = True
SITE_NAME = "文京区議選ナビ2027"
# 訂正・削除・苦情の受付（Googleフォーム。先生のアカウントで作成、2026-10-27）
# 迷惑メール対策のため、メールアドレスはサイトに出さない。
# 公選法142条の3第3項の「電子メールアドレス等」には返信用フォームのURLも含まれる（総務省の解説）ので、
# 告示後はこのフォームへのリンクが連絡先の表示になる。
FORM_URL = "https://forms.gle/4hbVfq6LhWJ6BGDR7"
FORM_PREFILL = "https://docs.google.com/forms/d/e/1FAIpQLSdaPzgNA6QgV6D2bunWUCJ5KVS4FwtG2QM_xsuZHbxf2xrVIg/viewform"
FORM_TARGET_ENTRY = "entry.2074378040"  # フォームの「対象」欄
CONTACT = '<a href="/teisei/">受付フォーム</a>'


def teisei_href(target=""):
    """各カードの「訂正・削除を依頼」リンク。フォームの「対象」欄に名前を入れた状態で開く。"""
    from urllib.parse import quote
    if not target:
        return FORM_URL
    return f"{FORM_PREFILL}?usp=pp_url&{FORM_TARGET_ENTRY}={quote(target)}"
ROBOTS_META = '<meta name="robots" content="noindex, nofollow">\n' if NOINDEX else ""
# 確認日からこの日数を過ぎたものは、build 時に一覧を出して見直す（画面には出さない。本人方針：旗が立つと印象が悪くなるため）。
# ページは作り置きなので、閲覧した日の日付でブラウザ側が判定する（作り直さなくても表示が切り替わる）
STALE_DAYS = 14
# 候補者の並び順：50音順だと特定の人が常に先頭になるため、開くたびにランダムに入れ替える
# （実際の選挙のくじ引きにならう）。ul.shuffle の中の li を並べ替え、点線の枠（.open）は最後に残す。
# JavaScript が動かない環境では、作ったときの50音順のまま表示される。
SHUFFLE_JS = """<script>(function(){function r(n){if(window.crypto&&crypto.getRandomValues){var a=new Uint32Array(1);crypto.getRandomValues(a);return a[0]%n;}return Math.floor(Math.random()*n);}
document.querySelectorAll('ul.shuffle').forEach(function(ul){var it=[].slice.call(ul.children).filter(function(li){return !li.classList.contains('open');});
var fx=[].slice.call(ul.children).filter(function(li){return li.classList.contains('open');});
for(var i=it.length-1;i>0;i--){var j=r(i+1),t=it[i];it[i]=it[j];it[j]=t;}it.concat(fx).forEach(function(li){ul.appendChild(li);});});})();</script>"""
# 画面に入ったら動き出す（グラフが伸びる・カードがふわっと出る）。JSが動かない環境では最初から表示
MOTION_JS = """<script>(function(){
var t=[];document.querySelectorAll('.fade,.chart').forEach(function(e){t.push([e,[e]]);});
document.querySelectorAll('.grow').forEach(function(e){t.push([e.parentElement,[e]]);});
function on(l){l.forEach(function(e){e.classList.add('in');});}
if(!('IntersectionObserver' in window)){t.forEach(function(x){on(x[1]);});return;}
var ok=false;t.forEach(function(x){var io=new IntersectionObserver(function(es){ok=true;if(es[0].isIntersecting){on(x[1]);io.disconnect();}},{threshold:.1});io.observe(x[0]);});setTimeout(function(){if(!ok)t.forEach(function(x){on(x[1]);});},3000);})();</script>"""
STALE_JS = ("<script>(function(){var L=" + str(STALE_DAYS) + "*864e5,n=Date.now();"
            "document.querySelectorAll('.chk[data-d]').forEach(function(e){"
            "var t=Date.parse(e.getAttribute('data-d')+'T00:00:00+09:00');"
            "if(t&&n-t>=L){var s=document.createElement('span');s.className='muted';s.textContent='・要再確認';e.appendChild(s);}"
            "});})();</script>")


def chk(date):
    return f'（<span class="chk" data-d="{html.escape(str(date))}">{html.escape(str(date))}確認</span>）'

cand_data = json.loads((ROOT / "data/candidates.json").read_text(encoding="utf-8"))
res_data = json.loads((ROOT / "data/results.json").read_text(encoding="utf-8"))
UPDATED = cand_data["updated"]
E = lambda s: html.escape(str(s), quote=True)

CSS = """
:root{--bg:#fbfaf7;--fg:#1d2321;--mu:#66706c;--ln:#e3e0d8;--ac:#1f6b4f;--ac2:#e9f3ee;--cd:#fff;--nw:#b5541c;--gr:#c9cdc9}
@media (prefers-color-scheme:dark){:root{--bg:#151917;--fg:#e8ece9;--mu:#9aa49f;--ln:#2c3330;--ac:#6cc39b;--ac2:#1d2a24;--cd:#1b201e;--nw:#f0a070;--gr:#4a524e}}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--fg);font:16px/1.75 "Hiragino Kaku Gothic ProN","Noto Sans JP",system-ui,sans-serif}
a{color:var(--ac)}.w{max-width:960px;margin:0 auto;padding:0 16px}
header.site{border-bottom:1px solid var(--ln);background:var(--cd)}header.site .w{padding:14px 16px}
.brand{font-size:22px;font-weight:700;letter-spacing:.04em;color:var(--ac);text-decoration:none}
nav.main{display:flex;gap:8px;flex-wrap:wrap;margin-top:10px;font-size:16px}nav.main a{text-decoration:none;color:var(--ac);border:1.5px solid var(--ac);border-radius:999px;padding:5px 14px;font-weight:700;background:var(--cd)}nav.main a:hover{background:var(--ac2)}nav.main a[aria-current]{background:var(--ac);color:#fff}
.crumb{font-size:13px;color:var(--mu);margin:16px 0 0}.crumb a{color:var(--mu)}
.hero{padding:22px 0 6px}h1{font-size:clamp(22px,4.6vw,32px);line-height:1.4;margin:6px 0 10px}
h2{font-size:21px;margin:0 0 6px;line-height:1.4}
.lead{color:var(--mu);margin:0 0 8px}.note{color:var(--mu);font-size:14px;margin:0 0 14px}
.facts{display:flex;flex-wrap:wrap;gap:10px;margin:14px 0}.facts div{background:var(--ac2);border-radius:10px;padding:8px 14px;font-size:14px}.facts b{font-size:17px}
section{padding:28px 0 6px}
.grid{list-style:none;padding:0;margin:0;display:grid;grid-template-columns:repeat(auto-fill,minmax(220px,1fr));gap:12px}
.card{background:var(--cd);border:1px solid var(--ln);border-radius:12px;padding:14px}
.card.ch .nm{font-size:20px}.q{margin:10px 0 6px;padding:8px 12px;border-left:3px solid var(--nw);background:var(--bg);font-size:15px;line-height:1.6}.q cite{display:block;font-style:normal;font-size:12px;color:var(--mu);margin-top:4px}
.prof{margin:6px 0;padding-left:1.1em;font-size:14px;line-height:1.6}.prof .muted{font-size:12px}
.top{display:flex;gap:6px;align-items:center;flex-wrap:wrap;font-size:12px}
.st{border-radius:4px;padding:1px 7px;font-weight:700;color:#fff}.st-cur{background:var(--ac)}.st-new{background:var(--nw)}
.party{color:var(--mu)}.tag{border:1px solid var(--mu);border-radius:4px;padding:0 6px;color:var(--mu)}
.nm{font-size:19px;font-weight:700;margin-top:6px}.nm a{text-decoration:none;color:var(--fg)}.nm a:hover{text-decoration:underline}.kana{font-size:12px;color:var(--mu)}
.ln{margin-top:8px;font-size:14px;display:flex;gap:10px;flex-wrap:wrap}.muted{color:var(--mu)}
.src{margin-top:8px;font-size:11.5px;color:var(--mu);line-height:1.5}
.chips{display:flex;flex-wrap:wrap;gap:8px;list-style:none;padding:0;margin:8px 0}.chips a{display:inline-block;background:var(--cd);border:1px solid var(--ln);border-radius:999px;padding:3px 12px;font-size:14px;text-decoration:none}
.tbl{overflow-x:auto}table{border-collapse:collapse;width:100%;background:var(--cd);font-size:14px}th,td{border-bottom:1px solid var(--ln);padding:8px 10px;text-align:left;vertical-align:top}th{font-weight:700;background:var(--ac2)}td.n,th.n{text-align:right;white-space:nowrap;font-variant-numeric:tabular-nums}
tr.cut td{background:var(--ac2);color:var(--ac);font-weight:700;text-align:center;font-size:13px}
tr.lose td{color:var(--mu)}
.bar{display:block;height:6px;border-radius:3px;background:var(--ac);margin-top:4px;margin-left:auto}tr.lose .bar{background:var(--gr)}
.news{list-style:none;padding:0}.news li{padding:8px 0;border-bottom:1px solid var(--ln)}.news time{color:var(--mu);font-size:13px;margin-right:12px}
.box{background:var(--cd);border:1px solid var(--ln);border-radius:12px;padding:16px 18px;font-size:15px}.box ol,.box ul{padding-left:20px;margin:6px 0}
.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:12px;list-style:none;padding:0;margin:10px 0}
.cards li{background:var(--cd);border:1px solid var(--ln);border-radius:12px;padding:14px 16px}.cards a.t{display:block;font-weight:700;font-size:17px;text-decoration:none;margin-bottom:4px}
dl.kv{display:grid;grid-template-columns:max-content 1fr;gap:6px 16px;margin:8px 0}dl.kv dt{color:var(--mu);font-size:14px}dl.kv dd{margin:0}
.hb{list-style:none;padding:0;margin:8px 0}.hb li{display:grid;grid-template-columns:8.5em 1fr;gap:4px 10px;align-items:center;padding:4px 0;font-size:14px}
.hb .t{background:var(--ac2);border-radius:4px;height:22px;position:relative;display:block;margin-right:3.8em}.hb .t i{display:block;height:100%;border-radius:4px;background:var(--ac)}.hb .t i.o{background:var(--nw)}
.hb .v{position:absolute;left:100%;top:0;padding-left:6px;white-space:nowrap;line-height:22px;font-size:13px;font-weight:700}
.chart{background:var(--cd);border:1px solid var(--ln);border-radius:12px;padding:14px 16px;margin:12px 0}
svg text{fill:var(--fg);font-size:13px}svg .ax{stroke:var(--ln)}svg .lnx{stroke:var(--ac);stroke-width:3;fill:none}svg .dot{fill:var(--ac)}
.notice{background:var(--ac2);border-bottom:1px solid var(--ln);font-size:13px}.notice .w{padding:8px 16px;display:flex;flex-wrap:wrap;gap:6px 12px;align-items:center}
.btn{display:inline-block;background:var(--nw);color:#fff !important;text-decoration:none;font-weight:700;border-radius:8px;padding:5px 12px;font-size:13px}.btn:hover{opacity:.85}
.iv{margin:6px 0;font-size:14px}.iv ul{margin:2px 0}
.card.open{border:2px dashed var(--ln);background:transparent;box-shadow:none}.card.open p{margin:6px 0}
.vb{list-style:none;padding:0;margin:10px 0}.vb li{padding:8px 0;border-bottom:1px solid var(--ln)}.vb .yr{font-weight:700;font-size:15px}
.vb .tr{position:relative;height:26px;background:var(--ac2);border-radius:5px;margin:6px 0 4px}.vb .tr i{display:block;height:100%;border-radius:5px;background:var(--ac)}.vb .tr i.lo{background:var(--gr)}
.vb .tr b{position:absolute;top:-4px;bottom:-4px;width:0;border-left:2px dashed var(--nw)}.vb .tr i.ov{position:absolute;left:0;top:0;background:var(--nw)}.vb .tr b.sq{border-left-color:var(--fg)}
.endorse{font-size:12px;color:var(--mu);border:1px dashed var(--ln);border-radius:999px;padding:1px 8px;margin-left:6px;white-space:nowrap}.terms{font-size:13px;color:var(--mu);margin-top:2px}
.all{list-style:none;padding:0;margin:8px 0}.all li>span:last-child{text-align:right;font-variant-numeric:tabular-nums}.all li{display:grid;grid-template-columns:2.4em 1fr 5.2em;gap:6px;align-items:center;font-size:12px;line-height:1.25;color:var(--mu)}
.all .t{height:7px;background:var(--ac2);border-radius:3px;position:relative}.all .t i{display:block;height:100%;border-radius:3px;background:var(--gr)}.all li.win .t i{background:var(--ac)}
.all li.me{color:var(--fg);font-weight:700}.all li.me .t i{background:var(--nw)}.all li.cut{display:block;border-top:2px dashed var(--nw);margin:4px 0 2px;padding-top:2px;font-size:11px;line-height:1.4;color:var(--nw)}
.pg{list-style:none;padding:0;margin:8px 0}.pg>li{padding:8px 0;border-bottom:1px solid var(--ln)}.say{display:flex;gap:10px;align-items:flex-end;margin:6px 0 14px}.say svg{flex:0 0 58px;width:58px;height:76px}
.bub{position:relative;background:var(--ac2);border:1.5px solid var(--ln);border-radius:14px;padding:9px 13px;font-size:14px;line-height:1.7}
.bub:before{content:"";position:absolute;left:-9px;bottom:18px;border:8px solid transparent;border-right-color:var(--ln);border-left:0}
.bub:after{content:"";position:absolute;left:-6px;bottom:19px;border:7px solid transparent;border-right-color:var(--ac2);border-left:0}
.bub .nm{display:block;font-size:12px;font-weight:700;color:var(--ac)}
.pg .pn{font-weight:700;margin-bottom:4px}.pg>li.ind{border:2px dashed var(--mu);border-radius:10px;padding:10px 12px;margin-top:14px}.pg>li.ind .t i{background:var(--mu)}.pg>li.ind .note{margin:0 0 6px}
tr.ind-sep td{border-top:2px dashed var(--mu);font-size:12px;color:var(--mu);padding-top:10px}tr.ind th,tr.ind td{background:var(--ac2)}.pg .hb li{grid-template-columns:4em 1fr;gap:0 10px;padding:3px 0}.pg .hb .t{margin-right:0}.pg .pv{grid-column:2;font-size:12px;color:var(--mu)}.pg .pv b{color:var(--fg);font-size:13px}.vb .cap{font-size:13px;color:var(--mu)}.vb .cap strong{color:var(--fg);font-size:15px}
.lg{display:flex;flex-wrap:wrap;gap:4px 14px;font-size:12.5px;color:var(--mu)}.lg i{display:inline-block;width:12px;height:12px;border-radius:3px;vertical-align:-1px;margin-right:4px}.lg i.dash{width:0;height:14px;border-left:2px dashed var(--nw);border-radius:0}
.duel{margin:14px 0 18px}.duel .yr{font-weight:700;font-size:15px;margin-bottom:4px}.duel .tr{display:flex;height:34px;border-radius:6px;overflow:hidden}
.duel .tr i{display:block;height:100%}.duel .tr i:nth-child(1){background:var(--ac)}.duel .tr i:nth-child(2){background:var(--nw)}.duel .tr i:nth-child(3){background:var(--gr)}
.duel .nm2{display:flex;justify-content:space-between;gap:8px;font-size:13.5px;margin-top:4px}.duel .nm2 span:last-child{text-align:right}.duel .nm2 b{font-size:16px}.duel .gap{font-size:13px;color:var(--mu)}
.js .grow{transform:scaleX(0);transform-origin:left center}.js .grow.in{transform:scaleX(1);transition:transform 1.1s cubic-bezier(.2,.7,.2,1)}
.js .fade{opacity:0;transform:translateY(10px)}.js .fade.in{opacity:1;transform:none;transition:opacity .6s ease,transform .6s ease}
.js .chart .lnx{stroke-dasharray:1400;stroke-dashoffset:1400}.js .chart.in .lnx{stroke-dashoffset:0;transition:stroke-dashoffset 1.6s ease}
.js .chart .dot{opacity:0}.js .chart.in .dot{opacity:1;transition:opacity .4s ease 1.2s}
@media (prefers-reduced-motion:reduce){.js .grow,.js .fade,.js .chart .lnx,.js .chart .dot{transform:none !important;opacity:1 !important;stroke-dashoffset:0 !important;transition:none !important}}
.faq details{background:var(--cd);border:1px solid var(--ln);border-radius:12px;margin:8px 0;padding:0 16px}
.faq summary{cursor:pointer;font-weight:700;padding:12px 0;list-style:none;position:relative;padding-right:1.6em}.faq summary::-webkit-details-marker{display:none}
.faq summary::after{content:"＋";position:absolute;right:0;top:12px;color:var(--ac)}.faq details[open] summary::after{content:"－"}
.faq details p{margin:0 0 14px;font-size:15px}
.chips.unc span{display:inline-block;background:var(--cd);border:1px dashed var(--mu);border-radius:999px;padding:3px 12px;font-size:14px;color:var(--mu)}
.fix{display:inline-block;margin-top:8px;font-size:12px;color:var(--mu)}
.tf label{display:block;font-weight:700;margin:12px 0 4px}.tf input,.tf select,.tf textarea{width:100%;box-sizing:border-box;font:inherit;padding:8px;border:1px solid var(--ln);border-radius:8px;background:var(--cd);color:var(--fg)}.tf textarea{min-height:140px}.tf .btn{font-size:16px;padding:10px 18px;margin-top:14px;border:0;cursor:pointer}
footer.site{margin-top:44px;border-top:1px solid var(--ln);padding:22px 0 40px;font-size:13px;color:var(--mu)}
@media (max-width:520px){nav.main{display:grid;grid-template-columns:1fr 1fr}nav.main a{text-align:center;padding:6px 8px}th,td{padding:7px 6px}.hb li{grid-template-columns:6.8em 1fr}.chart svg text{font-size:21px}}
"""

NAV = [("/kouho/", "区議選"), ("/kucho/", "区長選"), ("/touhyou/", "投票ガイド"), ("/about/", "このサイトについて")]
PAGES = []


def layout(path, title, desc, body, crumbs=None, jsonld=None, active=None):
    PAGES.append(path)
    nav = "".join(f'<a href="{h}"{" aria-current=page" if active == h else ""}>{l}</a>' for h, l in NAV)
    cr = ""
    if crumbs:
        parts = ['<a href="/">トップ</a>'] + [f'<a href="{h}">{E(l)}</a>' if h else E(l) for h, l in crumbs]
        cr = f'<p class="crumb">{" › ".join(parts)}</p>'
    ld = f'<script type="application/ld+json">{json.dumps(jsonld, ensure_ascii=False)}</script>' if jsonld else ""
    full = title if path == "/" else f"{title}｜{SITE_NAME}"
    return f"""<!doctype html>
<html lang="ja"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{E(full)}</title>
{ROBOTS_META}<meta name="description" content="{E(desc)}">
<link rel="canonical" href="{SITE_URL}{path}">
<meta property="og:title" content="{E(full)}"><meta property="og:description" content="{E(desc)}">
<meta property="og:type" content="website"><meta property="og:url" content="{SITE_URL}{path}"><meta property="og:locale" content="ja_JP">
<meta name="twitter:card" content="summary">
{ld}
<script>document.documentElement.classList.add("js")</script>
<style>{CSS}</style></head>
<body>
<header class="site"><div class="w"><a class="brand" href="/">{SITE_NAME}</a><nav class="main">{nav}</nav></div></header>
<div class="notice"><div class="w">公式サイトではありません。運営者が公開情報から集めた範囲で、運営者の責任で掲載しています。<a class="btn" href="/teisei/">訂正・削除・苦情の受付</a></div></div>
<main class="w">{cr}{body}</main>
<footer class="site"><div class="w">
<p><a class="btn" href="/teisei/">掲載内容の訂正・削除・苦情はこちら</a></p>
<p>運営：たかはま なおき（文京区議会議員・2027年文京区議選の立候補予定者）／連絡先：{CONTACT}<br>
このサイトは文京区・文京区議会・文京区選挙管理委員会の公式サイトではありません。運営者が公開情報から集めた範囲で、運営者の責任において掲載しています。<br>
最終更新 {E(UPDATED)}</p></div></footer>
{SHUFFLE_JS}
{MOTION_JS}
</body></html>
"""


def write(path, content):
    p = OUT / "index.html" if path == "/" else OUT / path.strip("/") / "index.html"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")
    WRITTEN.add(p.resolve())


def fv(v):
    return f"{int(v):,}" if float(v).is_integer() else f"{v:,.3f}"


cands = sorted(cand_data["candidates"], key=lambda c: unicodedata.normalize("NFKC", c["kana"]).replace(" ", ""))
elections = sorted(res_data["elections"], key=lambda e: e["year"])
for e in elections:
    win = [r for r in e["rows"] if r["elected"]]
    lose = [r for r in e["rows"] if not r["elected"]]
    e["last_win"] = min(win, key=lambda r: r["votes"])
    e["next"] = max(lose, key=lambda r: r["votes"])
    e["gap"] = round(e["last_win"]["votes"] - e["next"]["votes"], 3)
    e["ratio"] = e["candidates"] / e["seats"]

for c in cands:
    # 新しい選挙から順に並べる（閲覧者の関心が高い順。2026-10-28 先生の指示）
    _rn = {n.replace(" ", "") for n in c["result_names"]}
    c["hist"] = [(e, r) for e in reversed(elections) for r in e["rows"] if r["name"].replace(" ", "") in _rn]
    if c["status"] == "現":
        assert any(e["year"] == 2023 for e, _ in c["hist"]), c["name"]
challengers = [c for c in cands if c["status"] != "現"]
UNC = cand_data.get("unconfirmed_incumbents", {"members": []})
_kana = {c["kana"].replace(" ", "") for c in cands}
for m in UNC["members"]:
    assert m["kana"].replace(" ", "") not in _kana, m["name"]
incumbents = [c for c in cands if c["status"] == "現"]
NEWEST_FIRST = list(reversed(elections))  # 表やグラフは新しい選挙を上に（2026-10-28 先生の指示）
Y0, Y1, NE = elections[0]["year"], elections[-1]["year"], len(elections)
TERMS = cand_data.get("terms_source")


_SAY = [0]


def say(text):
    """とうひょうくんが説明する吹き出し。使い方や数字の読み方の説明だけに使う
    （特定の候補や政党をほめたり、すすめたりしない。1ページに3か所まで）。"""
    _SAY[0] += 1
    return (f'<div class="say"><svg viewBox="0 0 64 84" role="img" aria-label="とうひょうくん（ヒョウ柄の投票箱のキャラクター）">'
            f'{robo.robot(f"s{_SAY[0]}")}</svg><div class="bub"><span class="nm">とうひょうくん</span>{text}</div></div>')


def party_html(c):
    """党派。推薦などは政党の所属ではない参考情報なので、点線の枠で別に示す。"""
    en = f'<span class="endorse">{E(c["endorse"])}</span>' if c.get("endorse") else ""
    return f'<span class="party">{E(c["party"])}</span>{en}'


def party_text(c):
    return c["party"] + (f"（{c['endorse']}）" if c.get("endorse") else "")


def terms_html(c):
    return f'<div class="terms">当選{c["terms"]}回</div>' if c.get("terms") else ""


def hbars(items, maxv, fmt, orange=()):
    li = []
    for i, (label, v) in enumerate(items):
        cls = "grow o" if i in orange else "grow"
        li.append(f'<li><span>{E(label)}</span><span class="t"><i class="{cls}" style="width:{v / maxv * 100:.1f}%"></i><span class="v">{E(fmt(v))}</span></span></li>')
    return f'<ul class="hb">{"".join(li)}</ul>'


def line_chart(points, ymin, ymax, step, unit, label):
    W, H, L, R, T, B = 560, 260, 56, 24, 28, 36
    n = len(points)
    pad = 36  # 端の点のラベルが縦軸の目盛りや枠に重ならないように内側へ寄せる
    xs = [L + pad + (W - L - R - 2 * pad) * i / (n - 1) for i in range(n)]
    y = lambda v: T + (H - T - B) * (1 - (v - ymin) / (ymax - ymin))
    g, v = [], ymin
    while v <= ymax + 1e-9:
        g.append(f'<line class="ax" x1="{L}" x2="{W-R}" y1="{y(v):.1f}" y2="{y(v):.1f}"/><text x="{L-8}" y="{y(v)+4:.1f}" text-anchor="end">{v:g}{unit}</text>')
        v += step
    pts = " ".join(f"{x:.1f},{y(p[1]):.1f}" for x, p in zip(xs, points))
    dots = "".join(f'<circle class="dot" cx="{x:.1f}" cy="{y(p[1]):.1f}" r="5"/><text x="{x:.1f}" y="{y(p[1])-12:.1f}" text-anchor="middle" font-weight="700">{p[1]:.2f}{unit}</text><text x="{x:.1f}" y="{H-12}" text-anchor="middle">{p[0]}年</text>' for x, p in zip(xs, points))
    return f'<svg viewBox="0 0 {W} {H}" width="100%" role="img" aria-label="{E(label)}">{"".join(g)}<polyline class="lnx" points="{pts}"/>{dots}</svg>'


# ------------------------------------------------------------ トップ
def page_index():
    chips = "".join(f'<li><a href="/kouho/{c["slug"]}/">{E(c["name"])}</a></li>' for c in cands)
    prow = []
    for p in cand_data["parties"]:
        s = f'<a href="{E(p["source"])}" rel="noopener" target="_blank">出典</a>' if p["source"] else "—"
        prow.append(f"<tr><th scope=row>{E(p['party'])}</th><td class='n'>{E(p['count'])}</td><td>{E(p['note'])}</td><td>{s}</td></tr>")
    news = "".join(f"<li><time>{E(n['date'])}</time>{E(n['text'])}</li>" for n in cand_data["news"])
    links = "".join(f'<li><a href="{E(l["url"])}" rel="noopener" target="_blank">{E(l["label"])}</a></li>' for l in cand_data["links"])
    el = cand_data["election"]
    body = f"""
<div class="hero"><h1>文京区議会議員選挙2027<br>立候補予定者まとめ</h1>
<p class="lead">政党の公認発表など、公開されている情報だけで作った一覧です。すべてに出典と確認日を付けています。</p>
<div class="facts"><div>投票日 <b>{E(el['date_note'])}</b></div><div>定数 <b>{el['seats']}</b></div><div>掲載中の予定者 <b>{len(cands)}人</b></div></div></div>
<section><h2>挑戦者（現職ではない立候補予定者・{len(challengers)}人）</h2>
{say("挑戦者（いまは議員ではない人）は、現職より知られる機会が少ないよね。だから、本人の公表や政党の発表から、経歴や本人の言葉を紹介しているよ。基準は全員同じで、並び順は開くたびに入れ替わるよ。名前は敬称略だよ。")}
<ul class="grid shuffle">{''.join(challenger_card(c) for c in challengers)}{open_card()}</ul></section>
<ul class="cards">
<li><a class="t" href="/kouho/">区議選2027</a>立候補予定者{len(cands)}人の一覧（出典と確認日つき）、報道、過去{NE}回の結果とグラフ。</li>
<li><a class="t" href="/kucho/">区長選挙2027</a>立候補予定者{len(kc_cands)}人、現在の区長の状況、報道、過去4回の結果。</li>
<li><a class="t" href="/touhyou/">投票ガイド</a>選管の場所、期日前投票、入場券をなくしたとき、投票できる人。</li>
</ul>
<section><h2>立候補予定者（{len(cands)}人・敬称略）</h2>
<p class="note">名前を押すと、出典と過去の選挙結果のページに移ります。掲載されていない方も立候補する可能性があります。</p>
<ul class="chips shuffle">{chips}</ul></section>
{votematch_html(cand_data)}{votematch_html(kucho)}<section id="party"><h2>政党の公認状況</h2><p class="note">各党の公式発表で確認できた範囲です。</p>
<div class="tbl"><table><tbody>{''.join(prow)}</tbody></table></div></section>
<section id="news"><h2>更新情報</h2><ul class="news">{news}</ul></section>
<section><h2>公式の情報へのリンク</h2><ul>{links}</ul></section>
"""
    ld = {"@context": "https://schema.org", "@type": "WebSite", "name": SITE_NAME, "url": SITE_URL + "/", "inLanguage": "ja"}
    write("/", layout("/", "文京区議会議員選挙2027 立候補予定者まとめ｜文京区議選ナビ2027",
                      f"2027年4月の文京区議会議員選挙（定数{el['seats']}）の立候補予定者{len(cands)}人を、政党の公認発表など公開情報だけで一覧に。過去の結果と投票ガイドも。",
                      body, jsonld=ld))


# ------------------------------------------------------------ 候補者
def stl(c):
    # 「新人」は初めての立候補と誤解されやすく、過去の立候補歴まで責任を持てないため「挑戦者」と表示する
    return "現職" if c["status"] == "現" else "挑戦者"


def src_link(x):
    return f'<a href="{E(x["source"])}" rel="noopener" target="_blank">{E(x["source_label"])}</a>{chk(x["checked"])}'


def article_list(arts):
    """報道機関の記事。日付・媒体・見出し・リンクだけ（要約・論評なし）。新しい順。"""
    if not arts:
        return '<p class="note">まだありません。見つけ次第、日付・媒体・見出し・リンクを載せます。</p>'
    li = "".join(f'<li><time>{E(a["date"])}</time>{E(a["media"])}「<a href="{E(a["url"])}" rel="noopener" target="_blank">{E(a["title"])}</a>」</li>'
                 for a in sorted(arts, key=lambda a: a["date"], reverse=True))
    return f'<ul class="news">{li}</ul><p class="note">立候補予定者の立候補・支援・公約・経歴に触れた報道を、見出しに区名がなくても、特定の候補に有利・不利かを問わずすべて載せています。見出しは原文のままで、要約や論評はしていません。記事の数は報道の量をそのまま映したもので、このサイトによる候補の評価ではありません。立候補予定者全員の名前で、毎日記事を探しています。</p>'


def interview_html(c):
    """候補ごとのインタビュー記事（任意）。interview: [{"title","url","date"}]。空なら何も出さない。"""
    iv = c.get("interview") or []
    if not iv:
        return ""
    li = "".join(f'<li><a href="{E(x["url"])}" rel="noopener" target="_blank">{E(x.get("title") or "インタビュー")}</a>{("（" + E(x["date"]) + "）") if x.get("date") else ""}</li>' for x in iv)
    return f'<div class="iv"><b>インタビュー</b><ul class="prof">{li}</ul></div>'


def votematch_html(data):
    """ボートマッチ（任意）。votematch: [{"label","url","note"}]。空なら何も出さない。"""
    vm = data.get("votematch") or []
    if not vm:
        return ""
    li = "".join(f'<li><a class="t" href="{E(x["url"])}" rel="noopener" target="_blank">{E(x["label"])}</a>{E(x.get("note", ""))}</li>' for x in vm)
    return f'<section><h2>ボートマッチ</h2><ul class="cards">{li}</ul><p class="note">いくつかの質問に答えると、考えの近い候補がわかる外部のサイトです。</p></section>'


def challenger_card(c, base="/kouho/"):
    """挑戦者（現職ではない方）を厚めに紹介するカード。全員同じ形。"""
    lk = " ".join(cand_links(c))
    st = c.get("statement")
    quote = f'<blockquote class="q">「{E(st["text"])}」<cite>{src_link(st)}</cite></blockquote>' if st else ""
    prof = "".join(f'<li>{E(p["text"])}<span class="muted">（{src_link(p)}）</span></li>' for p in c.get("profile", []))
    prof = f'<ul class="prof">{prof}</ul>' if prof else ""
    return f"""<li class="card fade{' ch' if c['status'] != '現' else ''}"><div class="top"><span class="st {'st-cur' if c['status'] == '現' else 'st-new'}">{stl(c)}</span>{party_html(c)}</div>
<div class="nm">{f'<a href="{base}{c["slug"]}/">{E(c["name"])}</a>' if base else E(c["name"])}</div><div class="kana">{E(c['kana'])}</div>{terms_html(c)}
{quote}{prof}{c.get('hist_html', '')}{interview_html(c)}{f'<div class="ln">{lk}</div>' if lk else ''}
<div class="src">根拠：{src_link(c)}</div><a class="fix" href="{E(teisei_href(c['name']))}" rel="noopener" target="_blank">この掲載の訂正・削除を依頼</a></li>"""


def unconfirmed_html():
    """立候補の意向をまだ確認できていない現職議員。出るとも出ないとも決めつけず、氏名だけを並べる。"""
    ms = UNC["members"]
    if not ms:
        return ""
    chips = "".join(f'<li><span>{E(m["name"])}<span class="muted">（当選{m["terms"]}回）</span></span></li>' for m in ms)
    return f"""<section><h2>立候補の意向をまだ確認できていない現職議員（{len(ms)}人）</h2>
{say("ここに並んでいるのは、いまの区議会議員で、次の選挙に出るかどうかが、まだわからない人たちだよ。立候補予定者ではないから注意してね。出るとわかったら上の一覧に移すし、引退を表明したらこの欄から外すよ。名前は敬称略で、並び順は開くたびに入れ替わるよ。")}
<ul class="chips shuffle unc">{chips}</ul>
<p class="src">出典：{src_link(UNC)}　当選回数：{src_link(TERMS)}</p></section>"""


def open_card():
    """挑戦者の欄の最後に置く点線の枠。まだ載っていない方への案内（人数の予想はしない）。"""
    el = cand_data["election"]
    return f"""<li class="card open"><div class="nm">ほかにも立候補を予定している方へ</div>
<p>本人の公表や政党の発表を確認でき次第、ほかの方と同じ基準で掲載します。ご本人からのご連絡も受け付けています。</p>
<p class="note">定数{el['seats']}に対し、いま掲載している立候補予定者は{len(cands)}人です。</p>
<a class="btn" href="{E(FORM_URL)}" rel="noopener" target="_blank">掲載についてのご連絡</a></li>"""


def cand_links(c):
    out = []
    for k, label in (("web", "公式サイト"), ("x", "X"), ("instagram", "Instagram"), ("facebook", "Facebook"), ("blog", "ブログ"), ("youtube", "YouTube"), ("line", "LINE")):
        if c["links"].get(k):
            out.append(f'<a href="{E(c["links"][k])}" rel="noopener" target="_blank">{label}</a>')
    return out


def page_kouho():
    cards = []
    for c in incumbents:
        lk = " ".join(cand_links(c))
        op = ""  # 運営者も皆さんと同じ形で並べる（2026-10-28 先生の指示。運営者であることは「このサイトについて」で説明）
        cards.append(f"""<li class="card fade"><div class="top"><span class="st st-cur">現職</span>{party_html(c)}{op}</div>
<div class="nm"><a href="/kouho/{c['slug']}/">{E(c['name'])}</a></div><div class="kana">{E(c['kana'])}</div>{terms_html(c)}
{interview_html(c)}{f'<div class="ln">{lk}</div>' if lk else ''}
<div class="src">根拠：{src_link(c)}</div><a class="fix" href="{E(teisei_href(c['name']))}" rel="noopener" target="_blank">この掲載の訂正・削除を依頼</a></li>""")
    body = f"""<div class="hero"><h1>文京区議会議員選挙2027 立候補予定者一覧</h1>
<p class="lead">{len(cands)}人（挑戦者{len(challengers)}人・現職{len(incumbents)}人）。敬称略。並び順は開くたびに入れ替わります。本人の公表や政党の発表があり次第、追加します。</p></div>
<section><h2>挑戦者（{len(challengers)}人）</h2>
{say("挑戦者（いまは議員ではない人）は、現職より知られる機会が少ないよね。だから、本人の公表や政党の発表から、経歴や本人の言葉を厚めに紹介しているよ。基準は全員同じだよ。")}
<ul class="grid shuffle">{''.join(challenger_card(c) for c in challengers)}{open_card()}</ul></section>
<section><h2>現職（{len(incumbents)}人）</h2>
<p class="note">氏名は、選挙で使われている表記（選挙ドットコムや政党の発表などの表記）を優先しています。当選回数は{src_link(TERMS)}によります。</p>
<ul class="grid shuffle">{''.join(cards)}</ul></section>
{unconfirmed_html()}
<p class="note">掲載されていない方も立候補する可能性があります。</p>
{votematch_html(cand_data)}<section><h2>区議選に関する報道</h2>
<p class="note">文京区議選の情勢などを伝える報道機関の記事です。</p>{article_list(cand_data.get('articles', []))}</section>
<section id="kekka"><h2>過去の文京区議選の結果（公式・{Y0}〜{Y1}年）</h2>{kekka_html()}</section>"""
    write("/kouho/", layout("/kouho/", "文京区議会議員選挙2027 立候補予定者と過去の結果",
                            f"文京区議会議員選挙（2027年4月予定）の立候補予定者{len(cands)}人の一覧。党派・公式リンク・出典・確認日つき。過去{NE}回（{Y0}〜{Y1}年）の公式結果も。",
                            body, crumbs=[(None, "区議選")], active="/kouho/"))
    for c in cands:
        page_candidate(c)
    for e in elections:
        page_year(e)


KOHO_2023 = "https://www.city.bunkyo.lg.jp/documents/6195/202341782855.pdf"
KOHO_2023_KUCHO = "https://www.city.bunkyo.lg.jp/documents/6195/202341782930.pdf"


def last_election_html(c):
    """前回（最新）の区議選の概要。全員同じ形。本人の結果を先に、全体の数字とグラフを後に。"""
    e = elections[-1]
    mine = [r for ee, r in c["hist"] if ee is e]
    me = mine[0] if mine else None
    lead = ""
    if me:
        res = "当選" if me["elected"] else ("次点" if me["runnerup"] else "落選")
        lead = f'<p class="lead"><strong>{E(c["name"])}：{fv(me["votes"])}票・{me["rank"]}位／{e["candidates"]}人・{res}</strong>　<span class="muted">（当時の党派：{E(me["party"])}）</span></p>'
    else:
        lead = f'<p class="note">{E(c["name"])}は、{e["year"]}年の文京区議選の候補者の中には見つかりませんでした（届出名で照合）。</p>'
    facts = f'''<div class="facts"><div>投票率 <b>{e['turnout']:.2f}%</b></div><div>候補者 <b>{e['candidates']}人</b></div><div>定数 <b>{e['seats']}</b></div><div>最下位当選 <b>{fv(e['last_win']['votes'])}票</b></div><div>次点 <b>{fv(e['next']['votes'])}票</b></div></div>'''
    maxv = max(r["votes"] for r in e["rows"])
    li = []
    for i, r in enumerate(e["rows"]):
        if i == e["seats"]:
            li.append(f'<li class="cut">▲ 当選（定数{e["seats"]}）／ ▼ 落選</li>')
        cls = " ".join(x for x in ("win" if r["elected"] else "", "me" if me is r else "") if x)
        # 本人の行も大きさ・並びは同じにし、色だけで示す（2026-10-28 先生の指示）
        li.append(f'<li class="{cls}"><span>{r["rank"]}位</span><span class="t"><i class="grow" style="width:{r["votes"] / maxv * 100:.1f}%"></i></span><span>{fv(r["votes"])}</span></li>')
    chart = f'''<div class="chart"><ul class="all">{"".join(li)}</ul>
<div class="lg"><span><i style="background:var(--ac)"></i>当選した人</span><span><i style="background:var(--gr)"></i>落選した人</span>{'<span><i style="background:var(--nw)"></i>' + E(c["name"]) + '</span>' if me else ''}</div></div>'''
    return f'''<section><h2>前回（{e['year']}年）の文京区議選</h2>{lead}{facts}
<h3>全{e['candidates']}人の得票（得票順）</h3>{chart}
<p class="note">文京区選挙管理委員会が公表した結果です。全員の氏名は<a href="/kekka/{e['year']}/">{e['year']}年の結果のページ</a>にあります。投票率の推移などは<a href="/kouho/#kekka">過去の結果</a>にまとめています。</p></section>'''


def page_candidate(c):
    lk = cand_links(c)
    rows = []
    for e, r in c["hist"]:
        res = "当選" if r["elected"] else ("次点" if r["runnerup"] else "落選")
        rows.append(f'<tr><td><a href="/kekka/{e["year"]}/">{e["year"]}年</a></td><td>{E(r["party"])}</td><td class="n">{fv(r["votes"])}</td><td class="n">{r["rank"]}位／{e["candidates"]}人</td><td>{res}</td></tr>')
    if rows:
        top = max(max(r["votes"], e["last_win"]["votes"]) for e, r in c["hist"]) * 1.08
        bars = []
        for e, r in c["hist"]:
            res = "当選" if r["elected"] else ("次点" if r["runnerup"] else "落選")
            bars.append(f"""<li><div class="yr"><a href="/kekka/{e['year']}/">{e['year']}年</a>　<span class="muted">（当時の党派：{E(r['party'])}）</span></div>
<div class="tr"><i class="grow{'' if r['elected'] else ' lo'}" style="width:{r['votes'] / top * 100:.1f}%"></i><b style="left:{e['last_win']['votes'] / top * 100:.1f}%"></b></div>
<div class="cap"><strong>{fv(r['votes'])}票</strong>　{r['rank']}位／{e['candidates']}人・{res}　（最下位当選 {fv(e['last_win']['votes'])}票）</div></li>""")
        hist = f"""<div class="chart"><ul class="vb">{''.join(bars)}</ul>
<div class="lg"><span><i style="background:var(--ac)"></i>得票（当選）</span><span><i style="background:var(--gr)"></i>得票（落選）</span><span><i class="dash"></i>その回の最下位当選の得票</span></div></div>
<details><summary class="note">表で見る</summary><div class="tbl"><table><thead><tr><th>選挙</th><th>当時の党派</th><th class="n">得票数</th><th class="n">順位</th><th>結果</th></tr></thead><tbody>{''.join(rows)}</tbody></table></div></details>
<p class="note">文京区選挙管理委員会が公表した結果です。新しい選挙から順に並べています。党派は当時の届出の表記で、いまの所属とは限りません。得票数の小数点以下は公式の按分票です。</p>"""
    else:
        hist = f'<p class="note">{Y0}〜{Y1}年の{NE}回の文京区議選の公式結果に、該当する届出名は見つかりませんでした。</p>'
    won = sum(1 for _, r in c["hist"] if r["elected"])
    if c.get("terms") and c["terms"] > won:
        hist += f'<p class="note">当選回数は{c["terms"]}回です（{src_link(TERMS)}）。このサイトに載せている{Y0}年以降の結果では、そのうち{won}回分を確認できます。{Y0}年より前の結果は、区の記録で確認を進めています。</p>'
    if any(e["year"] == 2023 for e, _ in c["hist"]):
        hist += f'<p class="note">2023年の選挙のときの本人の主張は、文京区選挙管理委員会が公開している<a href="{KOHO_2023}" rel="noopener" target="_blank">選挙公報（PDF・約9MB・全候補分）</a>で読めます。</p>'
    hist += '<p class="note">このサイトでは、文京区議選の公式結果だけを掲載しています。ほかの選挙への立候補歴は扱っていません。</p>'
    who = ""  # 運営者も皆さんと同じ形にする（2026-10-28）
    st = c.get("statement")
    extra = ""
    if c.get("terms"):
        extra += f'<dt>当選回数</dt><dd>{c["terms"]}回<br><span class="muted">出典：{src_link(TERMS)}</span></dd>'
    if st:
        extra += f'<dt>本人の言葉</dt><dd>「{E(st["text"])}」（{src_link(st)}）</dd>'
    if c.get("profile"):
        extra += "<dt>経歴など</dt><dd><ul class=\"prof\">" + "".join(f'<li>{E(p["text"])}<span class="muted">（{src_link(p)}）</span></li>' for p in c["profile"]) + "</ul></dd>"
    if lk:
        extra += f'<dt>公式サイト・SNS</dt><dd>{"　".join(lk)}</dd>'
    body = f"""<div class="hero"><h1>{E(c['name'])}（{stl(c)}）</h1>
<p class="lead">{E(c['kana'])}｜{E(party_text(c))}｜文京区議会議員選挙2027の立候補予定者</p></div>
<section><h2>基本情報</h2><dl class="kv">
<dt>党派</dt><dd>{party_html(c)}</dd><dt>区分</dt><dd>{'現職議員' if c['status']=='現' else '挑戦者（現職ではない立候補予定者）'}</dd>
{extra}{('<dt>インタビュー</dt><dd>' + interview_html(c) + '</dd>') if c.get('interview') else ''}
<dt>掲載の根拠</dt><dd>{src_link(c)}</dd></dl>
<p class="note">立候補を正式に表明しているか、党の公認が出ているかは「掲載の根拠」のとおりです。{'点線の枠は推薦などの参考情報で、政党の所属ではありません。' if c.get('endorse') else ''}{who}</p><a class="fix" href="{E(teisei_href(c['name']))}" rel="noopener" target="_blank">この掲載の訂正・削除を依頼</a></section>
{last_election_html(c)}
<section><h2>過去の文京区議選の結果（公式・新しい順）</h2>{hist}</section>
<p><a href="/kouho/">← 立候補予定者の一覧にもどる</a></p>"""
    ld = {"@context": "https://schema.org", "@type": "ProfilePage", "name": f"{c['name']}｜文京区議会議員選挙2027", "url": f"{SITE_URL}/kouho/{c['slug']}/", "inLanguage": "ja"}
    p = f"/kouho/{c['slug']}/"
    write(p, layout(p, f"{c['name']}（{party_text(c)}）文京区議会議員選挙2027",
                    f"{c['name']}（{party_text(c)}・{stl(c)}）の基本情報、公式リンク、過去の文京区議選の結果。出典と確認日つき。",
                    body, crumbs=[("/kouho/", "区議選"), (None, c["name"])], jsonld=ld, active="/kouho/"))


# ------------------------------------------------------------ 過去の結果
def party_stats():
    st = defaultdict(dict)
    for e in elections:
        for r in e["rows"]:
            s = st[r["party"]].setdefault(e["year"], [0, 0, 0.0])
            s[0] += 1; s[1] += r["elected"]; s[2] += r["votes"]
    return st


def kekka_html():
    """区議選の過去の結果（比較・グラフ・党派別）。/kouho/ の下に載せる。表とグラフは新しい選挙が上。"""
    ys = [e["year"] for e in NEWEST_FIRST]
    st = party_stats()
    overview = "".join(f"""<tr><th scope=row><a href="/kekka/{e['year']}/">{E(e['label'])}</a></th><td class="n">{e['candidates']}人</td><td class="n">{e['seats']}</td><td class="n">{e['ratio']:.2f}倍</td><td class="n">{e['turnout']:.2f}%</td><td class="n">{e['electorate']:,}</td><td class="n">{fv(e['last_win']['votes'])}</td><td class="n">{fv(e['next']['votes'])}</td><td class="n">{e['gap']:,.0f}</td></tr>""" for e in NEWEST_FIRST)
    turnout_svg = line_chart([(e["year"], e["turnout"]) for e in elections], 40, 60, 5, "%", "文京区議選の投票率の推移")
    # 最下位当選の得票を棒、次点の得票を点線で示す（立候補者数のグラフと同じ形。2026-10-28 先生の指示）
    top = max(e["last_win"]["votes"] for e in elections) * 1.1
    lw = []
    for e in NEWEST_FIRST:
        lw.append(f"""<li><div class="yr"><a href="/kekka/{e['year']}/">{e['year']}年</a></div>
<div class="tr"><i class="grow" style="width:{e['last_win']['votes'] / top * 100:.1f}%"></i><b class="sq" style="left:{e['next']['votes'] / top * 100:.1f}%"></b></div>
<div class="cap">最下位当選 <strong>{fv(e['last_win']['votes'])}票</strong>　次点 <strong>{fv(e['next']['votes'])}票</strong>　差 {e['gap']:,.0f}票</div></li>""")
    lastwin = f'<ul class="vb">{"".join(lw)}</ul><div class="lg"><span><i style="background:var(--ac)"></i>最下位で当選した人の得票</span><span><i class="dash" style="border-color:var(--fg)"></i>次点（落選した中で最多）の得票</span></div>'
    # 立候補者数の棒に、定数を点線で重ねる
    cmax = max(e["candidates"] for e in elections) * 1.1
    cbl = []
    for e in NEWEST_FIRST:
        cbl.append(f"""<li><div class="yr"><a href="/kekka/{e['year']}/">{e['year']}年</a></div>
<div class="tr"><i class="grow" style="width:{e['candidates'] / cmax * 100:.1f}%"></i><b class="sq" style="left:{e['seats'] / cmax * 100:.1f}%"></b></div>
<div class="cap">立候補 <strong>{e['candidates']}人</strong>　定数 {e['seats']}　倍率 {e['ratio']:.2f}倍</div></li>""")
    candbars = f'<ul class="vb">{"".join(cbl)}</ul><div class="lg"><span><i style="background:var(--ac)"></i>立候補者数</span><span><i class="dash" style="border-color:var(--fg)"></i>定数</span></div>'
    # 無所属は一つの団体ではないので、表の一番下に置く
    allp = sorted(st, key=lambda p: (p == "無所属", -sum(st[p][y][1] for y in st[p]), p))
    prow = []
    for p in allp:
        cells = "".join(f'<td class="n">{st[p][y][1]}／{st[p][y][0]}</td>' if y in st[p] else '<td class="n muted">—</td>' for y in ys)
        if p == "無所属":  # 無所属は政党ではないので、区切って参考値として示す（2026-10-28 先生の指示）
            prow.append(f'<tr class="ind-sep"><td colspan="{len(ys) + 1}">▼ 参考：無所属は政党ではありません。無所属で立候補した人の人数を足した参考値です。</td></tr>')
            prow.append(f'<tr class="ind"><th scope=row>無所属（参考）</th>{cells}</tr>')
        else:
            prow.append(f"<tr><th scope=row>{E(p)}</th>{cells}</tr>")
    same = [p for p in allp if all(y in st[p] for y in ys)]
    srow, pgl = [], []
    smax = max(st[p][y][2] for p in same for y in ys)
    for p in same:
        cells = "".join(f'<td class="n">当選 {st[p][y][1]}／候補 {st[p][y][0]}<br>得票合計 {st[p][y][2]:,.0f}</td>' for y in ys)
        srow.append(f"<tr><th scope=row>{E(p)}</th>{cells}</tr>")
        bars = "".join(f'<li><span>{y}年</span><span class="t"><i class="grow" style="width:{st[p][y][2] / smax * 100:.1f}%"></i></span><span class="pv"><b>{st[p][y][2]:,.0f}票</b>　当選{st[p][y][1]}人／候補{st[p][y][0]}人</span></li>' for y in ys)
        if p == "無所属":
            pgl.append(f'<li class="ind"><div class="pn">無所属（参考）</div><p class="note">政党ではありません。無所属で立候補した一人ひとりの得票を足した参考値です。</p><ul class="hb">{bars}</ul></li>')
        else:
            pgl.append(f'<li><div class="pn">{E(p)}</div><ul class="hb">{bars}</ul></li>')
    head = "".join(f'<th class="n">{y}年</th>' for y in ys)
    ylinks = "".join(f'<li><a href="/kekka/{e["year"]}/">{E(e["label"])}の全候補の得票</a></li>' for e in reversed(elections))
    srcs = "、".join(f'<a href="{E(e["source"])}" rel="noopener" target="_blank">{e["year"]}年</a>' for e in NEWEST_FIRST)
    first, last = elections[0], elections[-1]
    body = f"""{say(f"区の選挙管理委員会が発表した、{Y0}年から{Y1}年までの{NE}回の結果をまとめたよ。次の選挙の予想じゃなくて、本当にあった数字だよ。表と棒グラフは、新しい選挙が上に来るように並べたよ。")}
<section><h2>{NE}回の比較</h2><div class="tbl"><table><thead><tr><th>選挙</th><th class="n">候補者</th><th class="n">定数</th><th class="n">倍率</th><th class="n">投票率</th><th class="n">有権者数</th><th class="n">最下位当選の得票</th><th class="n">次点の得票</th><th class="n">差</th></tr></thead><tbody>{overview}</tbody></table></div>
<p class="note">倍率＝候補者数÷定数。得票数は公式の数字で、按分票による小数点以下を含みます（「差」は小数点以下を四捨五入）。2003年の有権者数は、2007年の結果ページの「前回」欄の数字です。</p></section>
<section><h2>投票率の推移</h2><div class="chart">{turnout_svg}<p class="note">縦軸は40〜60%です。左が古い選挙、右が新しい選挙です。</p></div></section>
<section><h2>何票で当選したか（最下位当選と次点）</h2><div class="chart">{lastwin}
<p class="note">棒が最下位で当選した人の得票、点線が次点の人の得票です。点線から棒の先までが、当落を分けた差です。</p></div></section>
<section><h2>立候補者数と定数</h2><div class="chart">{candbars}<p class="note">点線が定数（{NE}回とも34）です。棒が点線より長い分だけ、落選する人が出ます。</p></div></section>
<section><h2>党派別の当選者数と候補者数</h2><p class="note">「当選／候補」の人数です。党派名は当時の公式の表記のままで、名称が変わった党は別の行に分かれています（合算していません）。</p>
<div class="tbl"><table><thead><tr><th>党派</th>{head}</tr></thead><tbody>{''.join(prow)}</tbody></table></div></section>
<section><h2>{NE}回とも同じ名前で続く党派の得票</h2><p class="note">得票合計は、その党派の候補者の得票を足した数字です（無所属は個人の得票の合計で、一つの団体ではありません）。</p>
<div class="chart"><ul class="pg">{''.join(pgl)}</ul></div>
<details><summary class="note">表で見る</summary><div class="tbl"><table><thead><tr><th>党派</th>{head}</tr></thead><tbody>{''.join(srow)}</tbody></table></div></details></section>
<section><h2>回ごとの全候補の得票</h2><ul>{ylinks}</ul></section>
<section><h2>数字の出典と読み方</h2><div class="box"><ul>
<li>出典：文京区選挙管理委員会の各回の結果ページ（{srcs}）。取得日 {E(res_data['fetched'])}。</li>
<li>取り込んだ数字は、公式の投票者数・無効票などから求めた有効票と、全候補の得票の合計が一致することを確認しています（2003年は無効票の数が公表ページにないため、この確認はしていません）。</li>
<li>この表やグラフは過去の結果です。次の選挙の当落を予想するものではありません。</li></ul></div></section>"""
    # 区議選ページの中の小見出しにする
    return body.replace("<h2>", "<h3>").replace("</h2>", "</h3>")


def page_year(e):
    y = e["year"]
    maxv = max(r["votes"] for r in e["rows"])
    rows = []
    for i, r in enumerate(e["rows"]):
        if i == e["seats"]:
            rows.append(f'<tr class="cut"><td colspan="3">▲ 当選（定数{e["seats"]}人）／ ▼ 落選</td></tr>')
        cls = "" if r["elected"] else ' class="lose"'
        mark = "（次点）" if r["runnerup"] else ""
        rows.append(f'<tr{cls}><td class="n">{r["rank"]}</td><td>{E(r["name"])}{mark}<br><span class="muted">{E(r["party"])}</span></td><td class="n">{fv(r["votes"])}<span class="bar grow" style="width:{r["votes"]/maxv*100:.1f}%"></span></td></tr>')
    pv = {}
    for r in e["rows"]:
        s = pv.setdefault(r["party"], [0, 0, 0.0]); s[0] += 1; s[1] += r["elected"]; s[2] += r["votes"]
    prow = "".join(f'<tr><th scope=row>{E(p)}</th><td class="n">{v[1]}／{v[0]}</td><td class="n">{v[2]:,.0f}</td></tr>' for p, v in sorted(pv.items(), key=lambda kv: (-kv[1][1], -kv[1][2])))
    nav = " ・ ".join(f'<a href="/kekka/{x["year"]}/">{x["year"]}年</a>' for x in NEWEST_FIRST if x["year"] != y)
    body = f"""<div class="hero"><h1>{E(e['label'])}文京区議会議員選挙の結果（全候補の得票）</h1>
<p class="lead">{E(e['date'])}執行。{e['candidates']}人が立候補し、定数{e['seats']}人が当選しました。</p></div>
<div class="facts"><div>投票率 <b>{e['turnout']:.2f}%</b></div><div>当日有権者数 <b>{e['electorate']:,}人</b></div><div>投票者数 <b>{e['voters']:,}人</b></div><div>最下位当選 <b>{fv(e['last_win']['votes'])}票</b></div><div>次点 <b>{fv(e['next']['votes'])}票</b></div></div>
<section><h2>全候補の得票（得票順）</h2><div class="tbl"><table><thead><tr><th class="n">順位</th><th>氏名・党派</th><th class="n">得票数</th></tr></thead><tbody>{''.join(rows)}</tbody></table></div>
<p class="note">氏名・党派は当時の届出の表記のままです。得票数の小数点以下は公式の按分票です。{f"無効票 {e['invalid']:,}票。" if e['invalid'] is not None else ""}</p></section>
<section><h2>党派別（この回の公式の党派名）</h2><div class="tbl"><table><thead><tr><th>党派</th><th class="n">当選／候補</th><th class="n">得票合計</th></tr></thead><tbody>{prow}</tbody></table></div></section>
<section><div class="box">出典：<a href="{E(e['source'])}" rel="noopener" target="_blank">文京区選挙管理委員会 {E(e['label'])}の結果</a>（取得日 {E(res_data['fetched'])}）<br>他の年：{nav}　／　<a href="/kouho/#kekka">過去の結果の比較にもどる</a></div></section>"""
    p = f"/kekka/{y}/"
    write(p, layout(p, f"{e['label']}文京区議会議員選挙の結果 全候補の得票",
                    f"{e['label']}の文京区議選の結果。{e['candidates']}人の得票、投票率{e['turnout']:.2f}%、最下位当選{fv(e['last_win']['votes'])}票。出典は文京区選管。",
                    body, crumbs=[("/kouho/", "区議選"), ("/kouho/#kekka", "過去の結果"), (None, f"{y}年")], active="/kouho/"))


# ------------------------------------------------------------ 投票ガイド
SRC_FAQ = ("文京区「よくある質問（選挙）」", "https://www.city.bunkyo.lg.jp/b045/p007504.html", "2023-05-01更新のページを2026-10-26に確認")
SRC_2024 = ("文京区「令和6年7月7日執行 東京都知事選挙」", "https://www.city.bunkyo.lg.jp/b045/p006414/p000001.html", "2026-10-26確認")
SRC_KINDS = ("文京区「選挙の種類」", "https://www.city.bunkyo.lg.jp/b045/p006374.html", "2026-10-26確認")
SRC_TOKYO = ("東京都選挙管理委員会「お問い合わせ」", "https://www.senkyo.metro.tokyo.lg.jp/inquiry", "2026-10-26確認")
MAP_BUNKYO = "https://www.google.com/maps/search/?api=1&query=" + "文京シビックセンター"
MAP_TOKYO = "https://www.google.com/maps/search/?api=1&query=" + "東京都庁第一本庁舎"
GUIDE = []


def src_box(*srcs):
    li = "".join(f'<li><a href="{E(u)}" rel="noopener" target="_blank">{E(n)}</a>（{E(d)}）</li>' for n, u, d in srcs)
    return f'<section><div class="box"><b>出典</b><ul>{li}</ul><p class="note" style="margin:6px 0 0">内容は変わることがあります。投票の前に、文京区選挙管理委員会（03-5803-1287）の最新の案内をご確認ください。</p></div></section>'


def guide_page(path, h1, desc, lead, body, qa, srcs):
    GUIDE.append((path, h1, lead))
    b = f'<div class="hero"><h1>{E(h1)}</h1><p class="lead">{E(lead)}</p></div>{body}{src_box(*srcs)}<p><a href="/touhyou/">← 投票ガイドにもどる</a></p>'
    ld = {"@context": "https://schema.org", "@type": "FAQPage", "name": h1, "url": SITE_URL + path, "inLanguage": "ja",
          "mainEntity": [{"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in qa]}
    write(path, layout(path, h1, desc, b, crumbs=[("/touhyou/", "投票ガイド"), (None, h1)], jsonld=ld, active="/touhyou/"))


def page_touhyou():
    qa = [("文京区選挙管理委員会はどこにありますか？", "文京シビックセンター（東京都文京区春日1丁目16番21号）の11階北側にあります。電話は03-5803-1287です。"),
          ("東京都選挙管理委員会はどこにありますか？", "東京都庁第一本庁舎北側40階（東京都新宿区西新宿二丁目8番1号）です。窓口は平日9時から17時（12時から13時は休憩、選挙期間中を除く）です。")]
    body = f"""<section><h2>文京区選挙管理委員会事務局（区の選挙の窓口）</h2>
<dl class="kv"><dt>所在地</dt><dd>〒112-8555 東京都文京区春日1丁目16番21号<br><b>文京シビックセンター11階北側</b></dd>
<dt>電話</dt><dd><a href="tel:0358031287">03-5803-1287</a>　FAX 03-5803-1357</dd>
<dt>問い合わせ</dt><dd><a href="https://logoform.jp/form/6KSu/554407" rel="noopener" target="_blank">お問い合わせフォーム（文京区）</a></dd>
<dt>地図</dt><dd><a href="{E(MAP_BUNKYO)}" rel="noopener" target="_blank">Googleマップで文京シビックセンターを開く</a></dd></dl>
<p class="note">文京シビックセンターは文京区役所の本庁舎です。最寄りは、東京メトロの後楽園駅、都営地下鉄の春日駅です（目安です。出入口などは区の案内でご確認ください）。窓口の受付時間は、区の公式ページで確認できていないため、お電話でご確認ください。</p></section>
<section><h2>東京都選挙管理委員会事務局（都全体の選挙の窓口）</h2>
<dl class="kv"><dt>所在地</dt><dd>〒163-8001 東京都新宿区西新宿二丁目8番1号<br><b>東京都庁第一本庁舎北側40階</b></dd>
<dt>窓口の時間</dt><dd>平日 9:00〜17:00（12:00〜13:00は休憩。選挙期間中は除く）</dd>
<dt>地図</dt><dd><a href="{E(MAP_TOKYO)}" rel="noopener" target="_blank">Googleマップで東京都庁を開く</a></dd></dl>
<div class="tbl"><table><thead><tr><th>担当</th><th>主な内容</th><th>電話</th></tr></thead><tbody>
<tr><td>選挙課</td><td>立候補・選挙運動</td><td class="n">03-5000-7259</td></tr>
<tr><td>選挙課</td><td>選挙の啓発</td><td class="n">03-5000-7260</td></tr>
<tr><td>選挙課</td><td>その他</td><td class="n">03-5000-7258</td></tr>
<tr><td>総務課</td><td>政治団体の届出</td><td class="n">03-5000-7257</td></tr></tbody></table></div>
<p class="note">都選管の電話は、内容ごとに番号が分かれています。おかけ間違いにご注意ください。</p></section>
<section><h2>どちらに聞けばいい？</h2><div class="box">
<p>投票所や入場券（選挙のお知らせ）、期日前投票など、<b>文京区で投票するときの手続きは、まず文京区選管</b>にお尋ねください。</p>
<p>政治団体の届出や、都全体の選挙の運動のルールなどは、東京都選管の担当です。迷ったときは、文京区選管に電話するのが確実です。</p></div></section>"""
    guide_page("/touhyou/senkan/", "文京区選管・東京都選管はどこ？ 住所・電話・何階か",
               "文京区選挙管理委員会は文京シビックセンター11階北側、東京都選挙管理委員会は都庁第一本庁舎北側40階。住所・電話・窓口時間を公式情報でまとめました。",
               "文京区選管は文京シビックセンター11階北側。東京都選管は都庁第一本庁舎40階です。", body, qa, [SRC_KINDS, SRC_TOKYO])

    qa = [("期日前投票はいつからいつまでですか？", "公示日・告示日の翌日から投票日の前日までです。時間は午前8時30分から午後8時までで、開設期間は投票所ごとに異なります。")]
    body = """<section><h2>いつ・どこで</h2><div class="box"><ul>
<li>期間：公示日・告示日の翌日から、投票日の前日まで（開設期間は投票所ごとに異なります）</li>
<li>時間：毎日 <b>8:30〜20:00</b></li>
<li>持ち物：選挙のお知らせ（入場券）をお持ちください。</li></ul></div></section>
<section><h2>期日前投票所の例（2024年7月の都知事選のとき）</h2>
<p class="note">2027年の区議選の期日前投票所は、まだ発表されていません。場所は選挙ごとに区が決めます。参考として、前回の都知事選での場所を示します。</p>
<div class="tbl"><table><thead><tr><th>場所</th><th>住所</th></tr></thead><tbody>
<tr><td>文京シビックセンター 1階 ギャラリーシビック（2024年は6月21日〜7月6日）</td><td>春日1-16-21</td></tr>
<tr><td>大原地域活動センター 1階 多目的室A</td><td>千石1-4-3</td></tr>
<tr><td>音羽地域活動センター 2階 洋室A・B</td><td>音羽1-22-14</td></tr>
<tr><td>汐見地域活動センター 2階 洋室A・B</td><td>千駄木3-2-6</td></tr></tbody></table></div></section>"""
    guide_page("/touhyou/kijitsuzen/", "文京区の期日前投票はいつ・どこで？ 時間と場所の例",
               "文京区の期日前投票は、告示日の翌日から投票日の前日まで、8:30〜20:00。前回の期日前投票所の例をまとめました。",
               "告示の翌日から投票日の前日まで、8時30分から20時までです。", body, qa, [SRC_FAQ, SRC_2024])

    qa = [("選挙のお知らせ（入場券）がなくても投票できますか？", "選挙人名簿に登録されていれば、入場券がなくても投票できます。投票所の係員に申し出てください。")]
    body = """<section><div class="box"><ul>
<li><b>届かなくても、なくしても、</b>選挙人名簿に登録されていれば投票できます。</li>
<li>投票所の係員に、お知らせがないことを申し出てください。</li>
<li>登録されているか分からないときは、文京区選挙管理委員会（<a href="tel:0358031287">03-5803-1287</a>）にお問い合わせください。</li></ul></div></section>"""
    guide_page("/touhyou/nyujoken/", "選挙のお知らせ（入場券）が届かない・なくしたとき",
               "文京区で選挙のお知らせ（入場券）が届かない、またはなくしたときでも、名簿に登録されていれば投票できます。",
               "名簿に登録されていれば、お知らせがなくても投票できます。", body, qa, [SRC_FAQ])

    qa = [("文京区の選挙で投票できるのは誰ですか？", "満18歳以上の日本国民で、選挙人名簿に登録されている人です。登録には、引き続き3か月以上、文京区に住民登録していることが必要です。")]
    body = """<section><div class="box"><ul>
<li>満<b>18歳以上</b>の<b>日本国民</b></li>
<li><b>選挙人名簿に登録</b>されていること</li>
<li>名簿への登録には、<b>引き続き3か月以上、文京区に住民登録</b>していること</li></ul></div></section>
<section><h2>引っ越したばかりの人は</h2><p>転居の時期によっては、前の住所の自治体で投票する場合があります。ご自身のケースは、文京区選挙管理委員会（<a href="tel:0358031287">03-5803-1287</a>）にお尋ねください。</p></section>"""
    guide_page("/touhyou/shikaku/", "文京区の選挙で投票できる人は？ 18歳以上・3か月以上",
               "文京区の選挙で投票できるのは、満18歳以上の日本国民で、選挙人名簿に登録されている人。名簿への登録には3か月以上の住民登録が必要です。",
               "満18歳以上で、文京区に3か月以上住民登録している日本国民です。", body, qa, [SRC_FAQ])

    qa = [("文京区の投票所はいくつありますか？", "区内に26の投票所があり、小・中学校などが使われています。")]
    body = """<section><div class="box"><ul>
<li>区内の投票所は <b>26か所</b>で、小・中学校などが使われています。</li>
<li>ご自身の投票所は、<b>選挙のお知らせ（入場券）に書かれています</b>。</li>
<li>投票所は選挙ごとに変わることがあります。投票の前にご確認ください。</li></ul></div></section>
<section><h2>当日に行けないとき</h2><p><a href="/touhyou/kijitsuzen/">期日前投票</a>のほか、不在者投票があります。詳しくは文京区選管へお問い合わせください。</p></section>"""
    guide_page("/touhyou/tohjitsu/", "文京区の投票所はどこ？ 26か所",
               "文京区には26の投票所があり、小・中学校などが使われています。ご自身の投票所は選挙のお知らせで確認できます。",
               "区内26か所。ご自身の投票所は、選挙のお知らせに書かれています。", body, qa, [SRC_FAQ])

    qa = [("文京区議会議員選挙の定数と任期は？", "定数は34人、任期満了日は令和9年（2027年）4月30日です。")]
    body = """<div class="tbl"><table><thead><tr><th>選挙</th><th class="n">定数</th><th>任期満了日</th><th>立候補できる年齢</th><th>届出の期限</th></tr></thead><tbody>
<tr><th scope=row>文京区議会議員</th><td class="n">34</td><td>2027年4月30日</td><td>25歳以上</td><td>投票日の7日前まで（告示）</td></tr>
<tr><th scope=row>文京区長</th><td class="n">1</td><td>2027年4月26日</td><td>—</td><td>—</td></tr>
<tr><th scope=row>東京都議会議員（文京区）</th><td class="n">2</td><td>2025年7月22日（実施済み）</td><td>—</td><td>投票日の9日前まで（告示）</td></tr>
<tr><th scope=row>東京都知事</th><td class="n">1</td><td>2028年7月30日</td><td>30歳以上</td><td>投票日の17日前まで（告示）</td></tr></tbody></table></div>
<p class="note">「—」は、区の「選挙の種類」のページで確認できていない項目です。2027年の区議選の告示日・投票日は、まだ発表されていません。</p>"""
    guide_page("/touhyou/shurui/", "区議選・区長選・都議選の違い（定数・任期・年齢）",
               "文京区で行われる区議選・区長選・都議選・都知事選の、定数・任期満了日・立候補できる年齢・届出期限を、区の公式ページから一覧にしました。",
               "文京区の区議選・区長選・都議選・都知事選の定数と任期の一覧です。", body, qa, [SRC_KINDS])

    items = "".join(f'<li><a class="t" href="{p}">{E(h)}</a>{E(l)}</li>' for p, h, l in GUIDE)
    body = f"""<div class="hero"><h1>文京区の選挙 投票ガイド</h1>
<p class="lead">投票の前に知っておきたいことを、文京区選挙管理委員会などの公式情報から、質問ごとにまとめました。</p></div>
<ul class="cards">{items}</ul>
<section><h2>次の選挙の日程</h2><p>文京区議会議員選挙は<b>2027年4月</b>の予定です（任期満了日は4月30日）。告示日と投票日は、文京区選挙管理委員会が決めて発表します。決まり次第、このページを更新します。</p></section>
{src_box(SRC_FAQ, SRC_KINDS)}"""
    write("/touhyou/", layout("/touhyou/", "文京区の選挙 投票ガイド（期日前投票・入場券・選管の場所）",
                              "文京区の選挙の投票ガイド。選管の場所、期日前投票、入場券をなくしたとき、投票できる人、投票所を、公式情報で質問ごとにまとめました。",
                              body, crumbs=[(None, "投票ガイド")], active="/touhyou/"))


# ------------------------------------------------------------ 区長選
kucho = json.loads((ROOT / "data/kucho.json").read_text(encoding="utf-8"))
kc_cands = sorted(kucho["candidates"], key=lambda c: unicodedata.normalize("NFKC", c["kana"]).replace(" ", ""))
kc_results = sorted(kucho["results"], key=lambda r: r["year"])
for r in kc_results:  # 検算：候補の得票合計＝投票者数−無効票−不足票
    assert sum(x["votes"] for x in r["rows"]) == r["voters"] - r["invalid"] - r["shortage"], r["year"]
for c in kc_cands:
    hist = [(r, x) for r in reversed(kc_results) for x in r["rows"] if x["name"] in c.get("result_names", [])]
    if hist:
        c["hist_html"] = '<ul class="prof">' + "".join(
            f'<li>{r["year"]}年の文京区長選：{x["votes"]:,}票（{"当選" if x["elected"] else "落選"}）<span class="muted">（<a href="{E(r["source"])}" rel="noopener" target="_blank">文京区選挙管理委員会</a>）</span></li>'
            for r, x in hist) + "</ul>"


def page_kucho():
    el, m = kucho["election"], kucho["mayor"]
    msrc = "".join(f'<li>{src_link(s)}</li>' for s in m["sources"])
    rows = []
    for r in reversed(kc_results):
        cand = "".join(f'<tr><td>{E(x["name"])}</td><td>{E(x["party"])}</td><td class="n">{x["votes"]:,}</td><td>{"当選" if x["elected"] else "落選"}</td></tr>' for x in sorted(r["rows"], key=lambda x: -x["votes"]))
        ele = f'{r["electorate"]:,}人' if r["electorate"] else "—"
        rows.append(f"""<section><h3>{E(r['label'])}（{E(r['date'])}）</h3>
<div class="tbl"><table><thead><tr><th>候補者</th><th>党派</th><th class="n">得票数</th><th>結果</th></tr></thead><tbody>{cand}</tbody></table></div>
<p class="note">投票率 {r['turnout']:.2f}%／当日有権者数 {ele}／投票者数 {r['voters']:,}人。出典：<a href="{E(r['source'])}" rel="noopener" target="_blank">文京区選挙管理委員会</a>（取得日 {E(kucho['results_fetched'])}）</p></section>""")
    turnout_svg = line_chart([(r["year"], r["turnout"]) for r in kc_results], 40, 60, 5, "%", "文京区長選の投票率の推移")
    # 得票の割合（帯グラフ）。色は得票順（1位=緑、2位=橙、3位=灰）で、人や党派による色分けはしない
    duels = []
    for r in reversed(kc_results):
        xs = sorted(r["rows"], key=lambda x: -x["votes"])
        tot = sum(x["votes"] for x in xs)
        segs = "".join(f'<i style="width:{x["votes"] / tot * 100:.2f}%" title="{E(x["name"])} {x["votes"]:,}票"></i>' for x in xs)
        names = "".join(f'<span>{E(x["name"])}<br><b>{x["votes"] / tot * 100:.1f}%</b>　{x["votes"]:,}票</span>' for x in xs[:2])
        more = "".join(f'<br>ほか {E(x["name"])} {x["votes"]:,}票（{x["votes"] / tot * 100:.1f}%）' for x in xs[2:])
        duels.append(f"""<div class="duel"><div class="yr">{E(r['label'])}</div><div class="tr grow">{segs}</div>
<div class="nm2">{names}</div><div class="gap">1位と2位の差 {xs[0]['votes'] - xs[1]['votes']:,}票{more}</div></div>""")
    cards = "".join(challenger_card(c, base=None) for c in kc_cands) or '<li class="card">まだいません。</li>'
    body = f"""<div class="hero"><h1>文京区長選挙2027</h1>
<p class="lead">区議選と同じ基準で、公開されている情報だけをまとめています。すべてに出典と確認日を付けています。</p>
<div class="facts"><div>投票日 <b>{E(el['date_note'])}</b></div><div>区長の任期満了 <b>2027年4月26日</b></div><div>立候補予定者 <b>{len(kc_cands)}人</b></div></div></div>
<section><h2>立候補予定者（{len(kc_cands)}人・敬称略）</h2>
{say("ここは、本人の公表や会見の報道などで、区長選に出る意向が確かめられた人だよ。全員同じ基準で紹介していて、並び順は開くたびに入れ替わるよ。")}
<ul class="grid shuffle">{cards}</ul></section>
<section><h2>現在の区長</h2><div class="box"><p><b>{E(m['name'])}</b>（{E(m['kana'])}）<br>{E(m['note'])}</p>
<p>{E(m['intention'])}</p><ul class="prof">{msrc}</ul><a class="fix" href="{E(teisei_href(m['name']))}" rel="noopener" target="_blank">この掲載の訂正・削除を依頼</a></div>
<p class="note">現在の区長は、立候補の意向を表明するまで、立候補予定者には含めていません。表明した場合は、上の立候補予定者に「現職」として掲載します。</p></section>
{votematch_html(kucho)}<section><h2>区長選に関する報道</h2>{article_list(kucho['articles'])}</section>
<section><h2>過去の文京区長選の結果（公式）</h2>
<h3>得票の割合</h3><div class="chart">{''.join(duels)}<p class="note">有効票に占める各候補の得票の割合です。色は得票の順（1位が緑、2位が橙）で、人や党派で色を分けてはいません。</p></div>
<h3>投票率の推移</h3><div class="chart">{turnout_svg}<p class="note">投票率の推移。縦軸は40〜60%です。</p></div>
{''.join(rows)}
<p class="note">2023年の区長選の各候補の主張は、文京区選挙管理委員会が公開している<a href="{KOHO_2023_KUCHO}" rel="noopener" target="_blank">選挙公報（PDF）</a>で読めます。</p>
<p class="note">得票数は、どの回も「投票者数−無効票−不足票」と一致することを確かめています。当日有権者数は、区長選の結果ページに記載がない回は「—」としています。</p></section>"""
    write("/kucho/", layout("/kucho/", "文京区長選挙2027 立候補予定者と過去の結果",
                            f"2027年4月の文京区長選挙の立候補予定者{len(kc_cands)}人、現在の区長の状況、報道、過去4回（2011〜2023年）の公式結果。出典と確認日つき。",
                            body, crumbs=[(None, "区長選")], active="/kucho/"))


# ------------------------------------------------------------ 訂正・削除・苦情の受付
def page_teisei():
    how = f"""<p><a class="btn" style="font-size:17px;padding:12px 20px" href="{E(FORM_URL)}" rel="noopener" target="_blank">受付フォームを開く</a></p>
<p class="note">Googleフォームが開きます。Googleへのログインは不要です。ご用件と内容だけで送れます（お名前・ご連絡先は任意）。各候補の欄にある「この掲載の訂正・削除を依頼」から開くと、対象の欄にその方のお名前が入った状態で開きます。</p>"""
    body = f"""<div class="hero"><h1>訂正・削除・苦情の受付</h1>
<p class="lead">このサイトは公式サイトではなく、運営者が公開情報から集めた範囲で、運営者の責任において掲載しています。誤りのご指摘、掲載の削除のご依頼、苦情やご意見を、どなたからでも受け付けます。</p></div>
<section><h2>受付</h2>{how}</section>
<section><h2>対応の方針</h2><div class="box"><ul>
<li><b>ご本人からの削除のご依頼</b>：ご本人であることを確認できたものは、原則としてすぐに掲載を取り下げます。</li>
<li><b>訂正のご依頼</b>：出典を確認のうえ、速やかに直します。直した内容は「更新情報」でお知らせします。</li>
<li><b>苦情・ご意見</b>：運営者が必ず目を通し、必要な対応をします。</li>
<li>ご連絡先をいただいた場合は、対応の結果をお返事します。</li>
</ul></div></section>
<section><h2>いただいた情報の扱い</h2><p>お名前やご連絡先は、このご依頼への対応のためだけに使い、ほかの目的には使いません。ご依頼の内容を、ご本人の同意なく公開することはありません。</p></section>
<section><h2>運営者</h2><p>たかはま なおき（文京区議会議員・2027年文京区議選の立候補予定者）<br>連絡先：<a href="{E(FORM_URL)}" rel="noopener" target="_blank">受付フォーム</a></p></section>"""
    write("/teisei/", layout("/teisei/", "訂正・削除・苦情の受付", "文京区議選ナビ2027の掲載内容について、訂正・削除のご依頼や苦情を受け付けます。ご本人と確認できた削除のご依頼には原則すぐに応じます。",
                             body, crumbs=[(None, "訂正・削除・苦情の受付")]))


# よくある質問（このサイトについて の一番上）。答えは掲載基準と食い違わないように
FAQ = [
    ("このサイトは、誰が作っているのですか？",
     "たかはま なおきが、文京区の選挙の投票率向上を目指し、個人で運営しています。私自身も、2027年の文京区議選の立候補予定者です。文京区や公的機関の公式サイトではありません。"),
    ("立候補予定者が運営していて、中立なのですか？",
     "載せる中身は、できる限り公平にしています。全員を同じ基準・同じ形式で載せ、運営者本人も特別扱いしていません。並び順は開くたびに入れ替わります。評価や得票の予想、投票のお願いは載せません。すべての情報に出典と確認日を付けています。"),
    ("どうやって、載せる人を決めているのですか？",
     "本人の公表、政党の発表、本人の会見や表明を伝えた報道、選挙ドットコムの「予想される顔ぶれ」のどれかで確認できた方を載せています。本人の表明をまだ確認できていない方には、その旨を書き添えています。"),
    ("ここに載っていない人は、立候補しないのですか？",
     "いいえ。このサイトが公開情報で確認できた方だけを載せているので、ほかにも立候補する方がいる可能性があります。毎日ウェブで確認していて、確認でき次第、追加します。"),
    ("自分や家族についての掲載を、直したり消したりしてほしいです。",
     "受付フォームからお知らせください。ご本人と確認できた削除のご依頼には、原則としてすぐに応じます。誤りのご指摘は、出典を確かめて速やかに直します。"),
    ("候補者の写真がないのはなぜですか？",
     "写真には撮影した人の著作権や、写っている人の権利があるため、このサイトでは載せていません。写真は、各候補の公式サイトやSNSでご覧ください。"),
    ("情報は、いつ時点のものですか？",
     "それぞれの情報に「確認日」を付けています。定期的に出典を確かめ直し、変わっていれば更新しています。"),
    ("投票日や投票所は、どこで調べればいいですか？",
     "日程は文京区選挙管理委員会が発表します。決まり次第、このサイトでもお知らせします。投票所や期日前投票などは「投票ガイド」にまとめています。"),
]


def page_about():
    faq = "".join(f"<details><summary>{E(q)}</summary><p>{E(a.replace('{STALE_DAYS}', str(STALE_DAYS)))}</p></details>" for q, a in FAQ)
    faq = faq.replace("受付フォーム", f'<a href="{E(FORM_URL)}" rel="noopener" target="_blank">受付フォーム</a>', 1).replace("「投票ガイド」", '<a href="/touhyou/">「投票ガイド」</a>', 1)
    body = f"""<div class="hero"><h1>このサイトについて</h1><p class="lead">よくある質問と、このサイトが何をどういう基準で載せているかの説明です。このサイトは公式サイトではなく、運営者が公開情報から集めた範囲で、運営者の責任において掲載しています。誤りや削除のご依頼は<a href="/teisei/">受付ページ</a>からお寄せください。</p></div>
<section class="faq"><h2>よくある質問</h2>{faq}</section>
<section><h2>掲載の基準</h2><div class="box"><ol>
<li>掲載するのは、本人の公表、政党の公式発表、本人の会見や表明を報じた報道機関の記事のいずれかで確認できた方と、選挙ドットコムの「予想される顔ぶれ」に載っている方です（区議選・区長選とも同じ基準）。後者は「本人の立候補表明は未確認」と明記し、表明を確認でき次第、表記を改めます。うわさや推測では掲載しません。</li>
<li>並び順は、ページを開くたびにランダムに入れ替わります。実際の選挙で届出の順番をくじ引きで決めるのにならい、特定の人が常に先頭にならないようにするためです。運営者本人も他の方とまったく同じ形式で掲載しています。</li>
<li>現職ではない立候補予定者を「挑戦者」として先に紹介し、本人の公表や政党の発表にある経歴・本人の言葉を厚めに載せます。現職に比べて知られる機会が少ないためで、挑戦者は全員同じ基準です。過去の立候補歴は、文京区議選の公式結果だけを載せ、ほかの選挙への立候補歴は扱いません。</li>
<li>評価・論評・得票予想・順位づけは載せません。</li>
<li>公約や選挙公報は転載せず、文京区選挙管理委員会の公式のページへのリンクで紹介します。</li>
<li>公式サイトやSNSへのリンクは、ご本人のものと確かめられたものだけを載せます（なりすまし防止）。</li>
<li>報道機関の記事は、文京区の区長選・区議選と、その立候補予定者の立候補・支援・公約・経歴に触れたものを、見出しに区名がなくても、特定の候補に有利・不利かを問わず、見つけたものをすべて載せます。載せるのは日付・媒体・見出し（原文のまま）・リンクだけで、要約や論評は付けません。記事の数は報道の量を映したもので、候補の評価ではありません。立候補予定者全員の名前で毎日記事を探し、その記録を残しています。</li>
<li>すべての情報に、出典と確認日を付けます。定期的に出典を見直して更新します。</li></ol></div></section>
<section><h2>過去の結果と投票ガイドについて</h2><p>過去の結果は文京区選挙管理委員会が公表した数字を使い、公式の合計と一致することを確認しています。投票ガイドは文京区・東京都の選挙管理委員会の公式ページを出典としています。</p></section>
<section><h2>運営者</h2><div class="box"><p>たかはま なおき（文京区議会議員・無所属）<br>このサイトの運営者は、2027年の文京区議会議員選挙の立候補予定者です。そのため、中立であることを最優先にして運営しています。</p>
<p>誤りのご指摘、掲載・修正・削除のご希望は、受付フォームからお寄せください。確認のうえ、速やかに対応します。<br>連絡先：{CONTACT}</p>
<p class="muted">このサイトは、文京区・文京区議会・文京区選挙管理委員会の公式サイトではありません。</p></div></section>"""
    write("/about/", layout("/about/", "このサイトについて（よくある質問・掲載基準・運営者）", "文京区議選ナビ2027のよくある質問、掲載基準、情報の出典、運営者と連絡先。運営者は立候補予定者本人で、全員を同じ形式で掲載しています。",
                            body, crumbs=[(None, "このサイトについて")], active="/about/"))


# マスタールール：ファイルを削除しない。
# 作り直す前に、今の public/ を _old_builds/public_日時/ へ名前を変えて保管し、まっさらな public/ に作る。
# 古い版は消さずに残る（_old_builds は GitHub に入れない。整理が必要になったら先生が消す）
import datetime as _dt0
OLD_BUILDS = ROOT / "_old_builds"
if OUT.exists() and any(OUT.iterdir()):
    OLD_BUILDS.mkdir(exist_ok=True)
    _keep = OLD_BUILDS / ("public_" + _dt0.datetime.now().strftime("%Y%m%d-%H%M%S"))
    try:
        OUT.rename(_keep)
    except OSError as _e:
        raise SystemExit(f"public/ の名前を変えられませんでした（確認用サーバーなどが使っている可能性）。消さずに止めます：{_e}")
    print("前の版を保管しました：", _keep.relative_to(ROOT))
OUT.mkdir(parents=True, exist_ok=True)
WRITTEN = set()


def _out(name):
    p = OUT / name
    WRITTEN.add(p.resolve())
    return p
page_index(); page_kouho(); page_kucho(); page_touhyou(); page_teisei(); page_about()
n_pages = len(PAGES)
_out("404.html").write_text(layout("/404", "ページが見つかりません", "お探しのページは見つかりませんでした。", '<div class="hero"><h1>ページが見つかりません</h1><p><a href="/">トップにもどる</a></p></div>'), encoding="utf-8")
PAGES.remove("/404")
sm = "".join(f"<url><loc>{SITE_URL}{p}</loc><lastmod>{UPDATED}</lastmod></url>" for p in PAGES)
_out("sitemap.xml").write_text(f'<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{sm}</urlset>', encoding="utf-8")
# robots.txt で拒否すると noindex の指示が読まれないため、巡回は許可したまま noindex で止める
_out("robots.txt").write_text("User-agent: *\nAllow: /\n" + ("" if NOINDEX else f"Sitemap: {SITE_URL}/sitemap.xml\n"), encoding="utf-8")
if NOINDEX:
    # Cloudflare Pages の設定ファイル。pages.dev 側も含め、全ファイルに「検索に載せない」を付ける
    _out("_headers").write_text("/*\n  X-Robots-Tag: noindex, nofollow\n", encoding="utf-8")
# 旧「過去の結果」ページ（/kekka/）は区議選ページの下に統合した。古いリンクはそこへ転送する
_out("_redirects").write_text("/kekka /kouho/#kekka 301\n/kekka/ /kouho/#kekka 301\n", encoding="utf-8")
# 内部用：確認日が STALE_DAYS 日を過ぎたもの（画面には出さない）
import datetime as _dt
_today = _dt.date.today()
_old = []
def _walk(x, where):
    if isinstance(x, dict):
        if "checked" in x:
            try:
                d = _dt.date.fromisoformat(str(x["checked"]))
                if (_today - d).days >= STALE_DAYS:
                    _old.append(f"{where}:{x.get('name') or x.get('source_label') or x.get('text','')[:20]} ({x['checked']})")
            except ValueError:
                pass
        for k, v in x.items():
            _walk(v, where)
    elif isinstance(x, list):
        for v in x:
            _walk(v, where)
_walk(cand_data, "区議"); _walk(kucho, "区長")
if _old:
    print(f"確認日が{STALE_DAYS}日以上前のもの {len(_old)}件（見直してください）:")
    for o in _old:
        print("  ", o)
_stale = sorted(str(f.relative_to(OUT)) for f in OUT.rglob("*") if f.is_file() and f.resolve() not in WRITTEN)
if _stale:
    print(f"今回は作らなかった古いファイルが public に {len(_stale)} 件あります（公開されたままになるので、先生に削除をお願いする）:")
    for f in _stale:
        print("  ", f)
print("built", len(PAGES), "pages")
