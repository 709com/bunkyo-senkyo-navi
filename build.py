"""data/*.json から public/ 以下のサイト一式を生成する。
使い方: python3 build.py
データの更新は data/ を直し、このスクリプトで作り直す（ページを直接書き換えない）。
"""
import json, html, pathlib, shutil, unicodedata
from collections import defaultdict

ROOT = pathlib.Path(__file__).parent
OUT = ROOT / "public"
SITE_URL = "https://bunkyo-senkyo.jp"
# True の間は検索エンジンに載せない（noindex）。本格公開するときに False にして build → push
NOINDEX = True
SITE_NAME = "文京区議選NAVI 2027"
MAIL = "info@takahamanaoki.com"
CONTACT = f'<a href="mailto:{MAIL}">{MAIL}</a>'  # 公選法上、告示後は連絡先表示が必要
ROBOTS_META = '<meta name="robots" content="noindex, nofollow">\n' if NOINDEX else ""
# 確認日からこの日数を過ぎたら「要再確認」と表示する（全員同じ扱い）。
# ページは作り置きなので、閲覧した日の日付でブラウザ側が判定する（作り直さなくても表示が切り替わる）
STALE_DAYS = 14
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
.brand{font-size:15px;font-weight:700;letter-spacing:.06em;color:var(--ac);text-decoration:none}
nav.main{display:flex;gap:6px 18px;flex-wrap:wrap;margin-top:6px;font-size:14px}nav.main a{text-decoration:none;color:var(--fg)}nav.main a:hover,nav.main a[aria-current]{color:var(--ac);text-decoration:underline}
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
footer.site{margin-top:44px;border-top:1px solid var(--ln);padding:22px 0 40px;font-size:13px;color:var(--mu)}
@media (max-width:520px){th,td{padding:7px 6px}.hb li{grid-template-columns:6.8em 1fr}.chart svg text{font-size:21px}}
"""

NAV = [("/kouho/", "候補者"), ("/kekka/", "過去の結果"), ("/touhyou/", "投票ガイド"), ("/about/", "掲載基準・運営者")]
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
<style>{CSS}</style></head>
<body>
<header class="site"><div class="w"><a class="brand" href="/">{SITE_NAME}</a><nav class="main">{nav}</nav></div></header>
<main class="w">{cr}{body}</main>
<footer class="site"><div class="w">
<p>運営：たかはま なおき（文京区議会議員・2027年文京区議選の立候補予定者）／連絡先：{CONTACT}<br>
このサイトは文京区・文京区議会・文京区選挙管理委員会の公式サイトではありません。掲載内容の誤りは上記までご連絡ください。<br>
最終更新 {E(UPDATED)}</p></div></footer>
{STALE_JS}
</body></html>
"""


def write(path, content):
    p = OUT / "index.html" if path == "/" else OUT / path.strip("/") / "index.html"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")


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
    c["hist"] = [(e, r) for e in elections for r in e["rows"] if r["name"] in c["result_names"]]
    if c["status"] == "現":
        assert any(e["year"] == 2023 for e, _ in c["hist"]), c["name"]
challengers = [c for c in cands if c["status"] != "現"]
incumbents = [c for c in cands if c["status"] == "現"]


def hbars(items, maxv, fmt, orange=()):
    li = []
    for i, (label, v) in enumerate(items):
        cls = ' class="o"' if i in orange else ""
        li.append(f'<li><span>{E(label)}</span><span class="t"><i{cls} style="width:{v / maxv * 100:.1f}%"></i><span class="v">{E(fmt(v))}</span></span></li>')
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
<p class="note">現職に比べて知られる機会が少ないため、本人の公表や政党の発表から、経歴や本人の言葉を紹介しています。50音順・敬称略。全員同じ基準です。</p>
<ul class="grid">{''.join(challenger_card(c) for c in challengers)}</ul></section>
<ul class="cards">
<li><a class="t" href="/kouho/">立候補予定者の一覧</a>氏名・党派・公式リンクを50音順に。出典と確認日つき。</li>
<li><a class="t" href="/kekka/">過去の選挙結果とグラフ</a>2011〜2023年の4回分。投票率、当選ライン、党派別の議席。</li>
<li><a class="t" href="/touhyou/">投票ガイド</a>選管の場所、期日前投票、入場券をなくしたとき、投票できる人。</li>
</ul>
<section><h2>立候補予定者（{len(cands)}人・50音順・敬称略）</h2>
<p class="note">名前を押すと、出典と過去の選挙結果のページに移ります。掲載されていない方も立候補する可能性があります。</p>
<ul class="chips">{chips}</ul></section>
<section id="party"><h2>政党の公認状況</h2><p class="note">各党の公式発表で確認できた範囲です。</p>
<div class="tbl"><table><tbody>{''.join(prow)}</tbody></table></div></section>
<section id="news"><h2>更新情報</h2><ul class="news">{news}</ul></section>
<section><h2>公式の情報へのリンク</h2><ul>{links}</ul></section>
"""
    ld = {"@context": "https://schema.org", "@type": "WebSite", "name": SITE_NAME, "url": SITE_URL + "/", "inLanguage": "ja"}
    write("/", layout("/", "文京区議会議員選挙2027 立候補予定者まとめ｜文京区議選NAVI",
                      f"2027年4月の文京区議会議員選挙（定数{el['seats']}）の立候補予定者{len(cands)}人を、政党の公認発表など公開情報だけで一覧に。過去の結果と投票ガイドも。",
                      body, jsonld=ld))


# ------------------------------------------------------------ 候補者
def stl(c):
    # 「新人」は初めての立候補と誤解されやすく、過去の立候補歴まで責任を持てないため「挑戦者」と表示する
    return "現職" if c["status"] == "現" else "挑戦者"


def src_link(x):
    return f'<a href="{E(x["source"])}" rel="noopener" target="_blank">{E(x["source_label"])}</a>{chk(x["checked"])}'


def challenger_card(c):
    """挑戦者（現職ではない方）を厚めに紹介するカード。全員同じ形。"""
    lk = " ".join(cand_links(c)) or '<span class="muted">確認中</span>'
    st = c.get("statement")
    quote = f'<blockquote class="q">「{E(st["text"])}」<cite>{src_link(st)}</cite></blockquote>' if st else ""
    prof = "".join(f'<li>{E(p["text"])}<span class="muted">（{src_link(p)}）</span></li>' for p in c.get("profile", []))
    prof = f'<ul class="prof">{prof}</ul>' if prof else ""
    return f"""<li class="card ch"><div class="top"><span class="st st-new">挑戦者</span><span class="party">{E(c['party'])}</span></div>
<div class="nm"><a href="/kouho/{c['slug']}/">{E(c['name'])}</a></div><div class="kana">{E(c['kana'])}</div>
{quote}{prof}<div class="ln">{lk}</div>
<div class="src">根拠：{src_link(c)}</div></li>"""


def cand_links(c):
    out = []
    for k, label in (("web", "公式サイト"), ("x", "X"), ("instagram", "Instagram"), ("facebook", "Facebook"), ("blog", "ブログ"), ("youtube", "YouTube"), ("line", "LINE")):
        if c["links"].get(k):
            out.append(f'<a href="{E(c["links"][k])}" rel="noopener" target="_blank">{label}</a>')
    return out


def page_kouho():
    cards = []
    for c in incumbents:
        lk = " ".join(cand_links(c)) or '<span class="muted">確認中</span>'
        op = '<span class="tag">運営者</span>' if c.get("operator") else ""
        cards.append(f"""<li class="card"><div class="top"><span class="st st-cur">現職</span><span class="party">{E(c['party'])}</span>{op}</div>
<div class="nm"><a href="/kouho/{c['slug']}/">{E(c['name'])}</a></div><div class="kana">{E(c['kana'])}</div>
<div class="ln">{lk}</div>
<div class="src">根拠：{src_link(c)}</div></li>""")
    body = f"""<div class="hero"><h1>文京区議会議員選挙2027 立候補予定者一覧</h1>
<p class="lead">{len(cands)}人（挑戦者{len(challengers)}人・現職{len(incumbents)}人）。それぞれ50音順・敬称略。本人の公表や政党の発表があり次第、追加します。</p></div>
<section><h2>挑戦者（{len(challengers)}人）</h2>
<p class="note">現職ではない立候補予定者です。現職に比べて知られる機会が少ないため、本人の公表や政党の発表から、経歴や本人の言葉を厚めに紹介しています。全員同じ基準です。</p>
<ul class="grid">{''.join(challenger_card(c) for c in challengers)}</ul></section>
<section><h2>現職（{len(incumbents)}人）</h2>
<p class="note">氏名の表記は文京区議会の議員名簿に合わせています。</p>
<ul class="grid">{''.join(cards)}</ul></section>
<p class="note">掲載されていない方も立候補する可能性があります。</p>"""
    write("/kouho/", layout("/kouho/", "文京区議会議員選挙2027 立候補予定者一覧",
                            f"文京区議会議員選挙（2027年4月予定）の立候補予定者{len(cands)}人を50音順に。党派・公式リンク・出典・確認日つき。",
                            body, crumbs=[(None, "候補者")], active="/kouho/"))
    for c in cands:
        page_candidate(c)


def page_candidate(c):
    lk = cand_links(c)
    lk_html = "　".join(lk) if lk else f'確認中です。公式のサイトやSNSをお持ちの場合は、{CONTACT} までお知らせください。'
    rows = []
    for e, r in c["hist"]:
        res = "当選" if r["elected"] else ("次点" if r["runnerup"] else "落選")
        rows.append(f'<tr><td><a href="/kekka/{e["year"]}/">{e["year"]}年</a></td><td>{E(r["party"])}</td><td class="n">{fv(r["votes"])}</td><td class="n">{r["rank"]}位／{e["candidates"]}人</td><td>{res}</td></tr>')
    if rows:
        hist = f"""<div class="tbl"><table><thead><tr><th>選挙</th><th>当時の党派</th><th class="n">得票数</th><th class="n">順位</th><th>結果</th></tr></thead><tbody>{''.join(rows)}</tbody></table></div>
<p class="note">文京区選挙管理委員会が公表した結果です。党派は当時の表記のまま掲載しています。得票数の小数点以下は公式の按分票です。</p>"""
    else:
        hist = '<p class="note">2011〜2023年の4回の文京区議選の公式結果に、該当する届出名は見つかりませんでした。</p>'
    hist += '<p class="note">このサイトでは、文京区議選の公式結果だけを掲載しています。ほかの選挙への立候補歴は扱っていません。</p>'
    who = "このサイトの運営者です。" if c.get("operator") else ""
    st = c.get("statement")
    extra = ""
    if st:
        extra += f'<dt>本人の言葉</dt><dd>「{E(st["text"])}」（{src_link(st)}）</dd>'
    if c.get("profile"):
        extra += "<dt>経歴など</dt><dd><ul class=\"prof\">" + "".join(f'<li>{E(p["text"])}<span class="muted">（{src_link(p)}）</span></li>' for p in c["profile"]) + "</ul></dd>"
    body = f"""<div class="hero"><h1>{E(c['name'])}（{stl(c)}）</h1>
<p class="lead">{E(c['kana'])}｜{E(c['party'])}｜文京区議会議員選挙2027の立候補予定者</p></div>
<section><h2>基本情報</h2><dl class="kv">
<dt>党派</dt><dd>{E(c['party'])}</dd><dt>区分</dt><dd>{'現職議員' if c['status']=='現' else '挑戦者（現職ではない立候補予定者）'}</dd>
{extra}<dt>公式サイト・SNS</dt><dd>{lk_html}</dd>
<dt>掲載の根拠</dt><dd>{src_link(c)}</dd></dl>
<p class="note">立候補を正式に表明しているか、党の公認が出ているかは「掲載の根拠」のとおりです。{who}</p></section>
<section><h2>過去の文京区議選の結果（公式）</h2>{hist}</section>
<p><a href="/kouho/">← 立候補予定者の一覧にもどる</a></p>"""
    ld = {"@context": "https://schema.org", "@type": "ProfilePage", "name": f"{c['name']}｜文京区議会議員選挙2027", "url": f"{SITE_URL}/kouho/{c['slug']}/", "inLanguage": "ja"}
    p = f"/kouho/{c['slug']}/"
    write(p, layout(p, f"{c['name']}（{c['party']}）文京区議会議員選挙2027",
                    f"{c['name']}（{c['party']}・{stl(c)}）の基本情報、公式リンク、過去の文京区議選の結果。出典と確認日つき。",
                    body, crumbs=[("/kouho/", "候補者"), (None, c["name"])], jsonld=ld, active="/kouho/"))


# ------------------------------------------------------------ 過去の結果
def party_stats():
    st = defaultdict(dict)
    for e in elections:
        for r in e["rows"]:
            s = st[r["party"]].setdefault(e["year"], [0, 0, 0.0])
            s[0] += 1; s[1] += r["elected"]; s[2] += r["votes"]
    return st


def page_kekka():
    ys = [e["year"] for e in elections]
    st = party_stats()
    overview = "".join(f"""<tr><th scope=row><a href="/kekka/{e['year']}/">{E(e['label'])}</a></th><td class="n">{e['candidates']}人</td><td class="n">{e['seats']}</td><td class="n">{e['ratio']:.2f}倍</td><td class="n">{e['turnout']:.2f}%</td><td class="n">{e['electorate']:,}</td><td class="n">{fv(e['last_win']['votes'])}</td><td class="n">{fv(e['next']['votes'])}</td><td class="n">{e['gap']:,.0f}</td></tr>""" for e in elections)
    turnout_svg = line_chart([(e["year"], e["turnout"]) for e in elections], 40, 60, 5, "%", "文京区議選の投票率の推移")
    items, orange = [], []
    for e in elections:
        items.append((f"{e['year']} 最下位当選", e["last_win"]["votes"]))
        items.append((f"{e['year']} 次点", e["next"]["votes"])); orange.append(len(items) - 1)
    lastwin = hbars(items, max(v for _, v in items), fv, tuple(orange))
    cb = [(f"{e['year']}年 候補者", e["candidates"]) for e in elections] + [("定数", 34)]
    candbars = hbars(cb, 50, lambda v: f"{int(v)}人", (len(cb) - 1,))
    allp = sorted(st, key=lambda p: (-sum(st[p][y][1] for y in st[p]), p))
    prow = []
    for p in allp:
        cells = "".join(f'<td class="n">{st[p][y][1]}／{st[p][y][0]}</td>' if y in st[p] else '<td class="n muted">—</td>' for y in ys)
        prow.append(f"<tr><th scope=row>{E(p)}</th>{cells}</tr>")
    same = [p for p in allp if all(y in st[p] for y in ys)]
    srow = []
    for p in same:
        cells = "".join(f'<td class="n">当選 {st[p][y][1]}／候補 {st[p][y][0]}<br>得票合計 {st[p][y][2]:,.0f}</td>' for y in ys)
        srow.append(f"<tr><th scope=row>{E(p)}</th>{cells}</tr>")
    head = "".join(f'<th class="n">{y}年</th>' for y in ys)
    ylinks = "".join(f'<li><a href="/kekka/{e["year"]}/">{E(e["label"])}の全候補の得票</a></li>' for e in reversed(elections))
    srcs = "、".join(f'<a href="{E(e["source"])}" rel="noopener" target="_blank">{e["year"]}年</a>' for e in elections)
    first, last = elections[0], elections[-1]
    body = f"""<div class="hero"><h1>文京区議会議員選挙の過去の結果（2011〜2023年）</h1>
<p class="lead">文京区選挙管理委員会が公表した4回分の結果を、グラフと表にまとめました。今回の予想ではなく、過去の公式の数字です。</p></div>
<section><h2>4回の比較</h2><div class="tbl"><table><thead><tr><th>選挙</th><th class="n">候補者</th><th class="n">定数</th><th class="n">倍率</th><th class="n">投票率</th><th class="n">有権者数</th><th class="n">最下位当選の得票</th><th class="n">次点の得票</th><th class="n">差</th></tr></thead><tbody>{overview}</tbody></table></div>
<p class="note">倍率＝候補者数÷定数。得票数は公式の数字で、按分票による小数点以下を含みます（「差」は小数点以下を四捨五入）。</p></section>
<section><h2>投票率の推移</h2><div class="chart">{turnout_svg}<p class="note">縦軸は40〜60%です。4回続けて上がっています。</p></div></section>
<section><h2>何票で当選したか（最下位当選と次点）</h2><div class="chart">{lastwin}
<p class="note">緑が最下位で当選した人、橙が次点（落選した中で最多）の得票数です。{first['year']}年は差が{first['gap']:,.0f}票、{last['year']}年は{last['gap']:,.0f}票でした。</p></div></section>
<section><h2>立候補者数と定数</h2><div class="chart">{candbars}<p class="note">定数は4回とも34です。立候補者数は{first['year']}年の{first['candidates']}人から、{last['year']}年の{last['candidates']}人まで減っています。</p></div></section>
<section><h2>党派別の当選者数と候補者数</h2><p class="note">「当選／候補」の人数です。党派名は当時の公式の表記のままで、名称が変わった党は別の行に分かれています（合算していません）。</p>
<div class="tbl"><table><thead><tr><th>党派</th>{head}</tr></thead><tbody>{''.join(prow)}</tbody></table></div></section>
<section><h2>4回とも同じ名前で続く党派の得票</h2><p class="note">得票合計は、その党派の候補者の得票を足した数字です（無所属は個人の得票の合計で、一つの団体ではありません）。</p>
<div class="tbl"><table><thead><tr><th>党派</th>{head}</tr></thead><tbody>{''.join(srow)}</tbody></table></div></section>
<section><h2>回ごとの全候補の得票</h2><ul>{ylinks}</ul></section>
<section><h2>数字の出典と読み方</h2><div class="box"><ul>
<li>出典：文京区選挙管理委員会の各回の結果ページ（{srcs}）。取得日 {E(res_data['fetched'])}。</li>
<li>取り込んだ数字は、公式の投票者数・無効票などから求めた有効票と、全候補の得票の合計が一致することを確認しています。</li>
<li>この表やグラフは過去の結果です。次の選挙の当落を予想するものではありません。</li></ul></div></section>"""
    ld = {"@context": "https://schema.org", "@type": "Dataset", "name": "文京区議会議員選挙の結果（2011〜2023年）", "description": "文京区選挙管理委員会が公表した区議選4回分の得票・投票率", "inLanguage": "ja", "url": f"{SITE_URL}/kekka/"}
    write("/kekka/", layout("/kekka/", "文京区議会議員選挙の過去の結果（2011〜2023年）グラフと当選ライン",
                            "文京区議選の2011・2015・2019・2023年の結果を、投票率・当選ライン（最下位当選の得票）・党派別の当選者数でまとめました。出典は文京区選管。",
                            body, crumbs=[(None, "過去の結果")], jsonld=ld, active="/kekka/"))
    for e in elections:
        page_year(e)


def page_year(e):
    y = e["year"]
    maxv = max(r["votes"] for r in e["rows"])
    rows = []
    for i, r in enumerate(e["rows"]):
        if i == e["seats"]:
            rows.append(f'<tr class="cut"><td colspan="3">▲ 当選（定数{e["seats"]}人）／ ▼ 落選</td></tr>')
        cls = "" if r["elected"] else ' class="lose"'
        mark = "（次点）" if r["runnerup"] else ""
        rows.append(f'<tr{cls}><td class="n">{r["rank"]}</td><td>{E(r["name"])}{mark}<br><span class="muted">{E(r["party"])}</span></td><td class="n">{fv(r["votes"])}<span class="bar" style="width:{r["votes"]/maxv*100:.1f}%"></span></td></tr>')
    pv = {}
    for r in e["rows"]:
        s = pv.setdefault(r["party"], [0, 0, 0.0]); s[0] += 1; s[1] += r["elected"]; s[2] += r["votes"]
    prow = "".join(f'<tr><th scope=row>{E(p)}</th><td class="n">{v[1]}／{v[0]}</td><td class="n">{v[2]:,.0f}</td></tr>' for p, v in sorted(pv.items(), key=lambda kv: (-kv[1][1], -kv[1][2])))
    nav = " ・ ".join(f'<a href="/kekka/{x["year"]}/">{x["year"]}年</a>' for x in elections if x["year"] != y)
    body = f"""<div class="hero"><h1>{E(e['label'])}文京区議会議員選挙の結果（全候補の得票）</h1>
<p class="lead">{E(e['date'])}執行。{e['candidates']}人が立候補し、定数{e['seats']}人が当選しました。</p></div>
<div class="facts"><div>投票率 <b>{e['turnout']:.2f}%</b></div><div>当日有権者数 <b>{e['electorate']:,}人</b></div><div>投票者数 <b>{e['voters']:,}人</b></div><div>最下位当選 <b>{fv(e['last_win']['votes'])}票</b></div><div>次点 <b>{fv(e['next']['votes'])}票</b></div></div>
<section><h2>全候補の得票（得票順）</h2><div class="tbl"><table><thead><tr><th class="n">順位</th><th>氏名・党派</th><th class="n">得票数</th></tr></thead><tbody>{''.join(rows)}</tbody></table></div>
<p class="note">氏名・党派は当時の届出の表記のままです。得票数の小数点以下は公式の按分票です。無効票 {e['invalid']:,}票。</p></section>
<section><h2>党派別（この回の公式の党派名）</h2><div class="tbl"><table><thead><tr><th>党派</th><th class="n">当選／候補</th><th class="n">得票合計</th></tr></thead><tbody>{prow}</tbody></table></div></section>
<section><div class="box">出典：<a href="{E(e['source'])}" rel="noopener" target="_blank">文京区選挙管理委員会 {E(e['label'])}の結果</a>（取得日 {E(res_data['fetched'])}）<br>他の年：{nav}　／　<a href="/kekka/">4回の比較にもどる</a></div></section>"""
    p = f"/kekka/{y}/"
    write(p, layout(p, f"{e['label']}文京区議会議員選挙の結果 全候補の得票",
                    f"{e['label']}の文京区議選の結果。{e['candidates']}人の得票、投票率{e['turnout']:.2f}%、最下位当選{fv(e['last_win']['votes'])}票。出典は文京区選管。",
                    body, crumbs=[("/kekka/", "過去の結果"), (None, f"{y}年")], active="/kekka/"))


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


def page_about():
    body = f"""<div class="hero"><h1>掲載基準と運営者</h1><p class="lead">このサイトが、何を、どういう基準で載せているかの説明です。</p></div>
<section><h2>掲載の基準</h2><div class="box"><ol>
<li>掲載するのは、本人の公表、政党の公式発表のいずれかで確認できた方と、選挙ドットコムの「予想される顔ぶれ」に載っている方です。後者は「本人の立候補表明は未確認」と明記し、表明を確認でき次第、表記を改めます。うわさや推測では掲載しません。</li>
<li>並び順は50音順です。運営者本人も他の方とまったく同じ形式で掲載しています。</li>
<li>現職ではない立候補予定者を「挑戦者」として先に紹介し、本人の公表や政党の発表にある経歴・本人の言葉を厚めに載せます。現職に比べて知られる機会が少ないためで、挑戦者は全員同じ基準です。過去の立候補歴は、文京区議選の公式結果だけを載せ、ほかの選挙への立候補歴は扱いません。</li>
<li>評価・論評・得票予想・順位づけは載せません。</li>
<li>公約や選挙公報は転載せず、文京区選挙管理委員会の公式のページへのリンクで紹介します。</li>
<li>公式サイトやSNSへのリンクは、ご本人のサイトや政党のページからリンクされているものだけを載せます（なりすまし防止）。</li>
<li>すべての情報に、出典と確認日を付けます。確認日から{STALE_DAYS}日以上たったものには「要再確認」と表示し、出典を見直して更新します。</li></ol></div></section>
<section><h2>過去の結果と投票ガイドについて</h2><p>過去の結果は文京区選挙管理委員会が公表した数字を使い、公式の合計と一致することを確認しています。投票ガイドは文京区・東京都の選挙管理委員会の公式ページを出典としています。</p></section>
<section><h2>運営者</h2><div class="box"><p>たかはま なおき（文京区議会議員・無所属）<br>このサイトの運営者は、2027年の文京区議会議員選挙の立候補予定者です。そのため、中立であることを最優先にして運営しています。</p>
<p>誤りのご指摘、掲載・修正・削除のご希望は、次のアドレスまでご連絡ください。確認のうえ、速やかに対応します。<br>連絡先：{CONTACT}</p>
<p class="muted">このサイトは、文京区・文京区議会・文京区選挙管理委員会の公式サイトではありません。</p></div></section>"""
    write("/about/", layout("/about/", "掲載基準と運営者", "文京区議選NAVI 2027の掲載基準、情報の出典、運営者と連絡先。運営者は立候補予定者本人で、全員を同じ形式で掲載しています。",
                            body, crumbs=[(None, "掲載基準・運営者")], active="/about/"))


if OUT.exists():
    shutil.rmtree(OUT)
OUT.mkdir(parents=True)
page_index(); page_kouho(); page_kekka(); page_touhyou(); page_about()
n_pages = len(PAGES)
(OUT / "404.html").write_text(layout("/404", "ページが見つかりません", "お探しのページは見つかりませんでした。", '<div class="hero"><h1>ページが見つかりません</h1><p><a href="/">トップにもどる</a></p></div>'), encoding="utf-8")
PAGES.remove("/404")
sm = "".join(f"<url><loc>{SITE_URL}{p}</loc><lastmod>{UPDATED}</lastmod></url>" for p in PAGES)
(OUT / "sitemap.xml").write_text(f'<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{sm}</urlset>', encoding="utf-8")
# robots.txt で拒否すると noindex の指示が読まれないため、巡回は許可したまま noindex で止める
(OUT / "robots.txt").write_text("User-agent: *\nAllow: /\n" + ("" if NOINDEX else f"Sitemap: {SITE_URL}/sitemap.xml\n"), encoding="utf-8")
if NOINDEX:
    # Cloudflare Pages の設定ファイル。pages.dev 側も含め、全ファイルに「検索に載せない」を付ける
    (OUT / "_headers").write_text("/*\n  X-Robots-Tag: noindex, nofollow\n", encoding="utf-8")
print("built", len(PAGES), "pages")
