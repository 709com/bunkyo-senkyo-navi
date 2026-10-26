"""data/candidates.json から public/index.html を生成する。
使い方: python3 build.py
"""
import json, html, pathlib, unicodedata

ROOT = pathlib.Path(__file__).parent
SITE_URL = "https://bunkyo-senkyo.jp/"   # ドメイン確定後に書き換える
CONTACT = '<a href="mailto:info@takahamanaoki.com">info@takahamanaoki.com</a>'  # 公選法上、告示後は連絡先表示が必要

d = json.loads((ROOT / "data/candidates.json").read_text(encoding="utf-8"))
e = lambda s: html.escape(str(s))

def kana_key(c):
    return unicodedata.normalize("NFKC", c["kana"]).replace(" ", "")

cands = sorted(d["candidates"], key=kana_key)

rows = []
for c in cands:
    links = []
    for k, label in (("web", "公式サイト"), ("x", "X"), ("youtube", "YouTube"), ("line", "LINE")):
        if c["links"].get(k):
            links.append(f'<a href="{e(c["links"][k])}" rel="noopener" target="_blank">{label}</a>')
    link_html = " ".join(links) if links else '<span class="muted">確認中</span>'
    op = '<span class="tag op">運営者</span>' if c.get("operator") else ""
    rows.append(f"""<li class="card">
  <div class="top"><span class="st st-{'new' if c['status']=='新' else 'cur'}">{e(c['status'])}</span><span class="party">{e(c['party'])}</span>{op}</div>
  <div class="nm">{e(c['name'])}</div><div class="kana">{e(c['kana'])}</div>
  <div class="ln">{link_html}</div>
  <div class="src">根拠：<a href="{e(c['source'])}" rel="noopener" target="_blank">{e(c['source_label'])}</a>（{e(c['checked'])}確認）</div>
</li>""")

prow = []
for p in d["parties"]:
    src = f'<a href="{e(p["source"])}" rel="noopener" target="_blank">出典</a>' if p["source"] else "—"
    prow.append(f"<tr><th>{e(p['party'])}</th><td class='n'>{e(p['count'])}</td><td>{e(p['note'])}</td><td>{src}</td></tr>")

news = "".join(f"<li><time>{e(n['date'])}</time>{e(n['text'])}</li>" for n in d["news"])
links = "".join(f'<li><a href="{e(l["url"])}" rel="noopener" target="_blank">{e(l["label"])}</a></li>' for l in d["links"])
el = d["election"]
n = len(cands)

title = "文京区議会議員選挙2027 立候補予定者まとめ｜文京区議選NAVI"
desc = f"2027年4月の文京区議会議員選挙（定数{el['seats']}）の立候補予定者{n}人を、政党の公認発表など公開情報だけで一覧にしています。出典付き・50音順。"

ld = {
  "@context": "https://schema.org", "@type": "WebPage", "name": title,
  "description": desc, "url": SITE_URL, "dateModified": d["updated"], "inLanguage": "ja",
}

page = f"""<!doctype html>
<html lang="ja"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{e(title)}</title>
<meta name="description" content="{e(desc)}">
<link rel="canonical" href="{SITE_URL}">
<meta property="og:title" content="{e(title)}"><meta property="og:description" content="{e(desc)}">
<meta property="og:type" content="website"><meta property="og:url" content="{SITE_URL}">
<meta name="twitter:card" content="summary">
<script type="application/ld+json">{json.dumps(ld, ensure_ascii=False)}</script>
<style>
:root{{--bg:#fbfaf7;--fg:#1d2321;--mu:#66706c;--ln:#e3e0d8;--ac:#1f6b4f;--ac2:#e9f3ee;--cd:#fff;--nw:#b5541c}}
@media (prefers-color-scheme:dark){{:root{{--bg:#151917;--fg:#e8ece9;--mu:#9aa49f;--ln:#2c3330;--ac:#6cc39b;--ac2:#1d2a24;--cd:#1b201e;--nw:#f0a070}}}}
*{{box-sizing:border-box}}body{{margin:0;background:var(--bg);color:var(--fg);font:16px/1.7 "Hiragino Kaku Gothic ProN","Noto Sans JP",system-ui,sans-serif}}
a{{color:var(--ac)}}.w{{max-width:960px;margin:0 auto;padding:0 16px}}
header{{border-bottom:1px solid var(--ln);background:var(--cd)}}header .w{{padding:28px 16px 22px}}
.brand{{font-size:13px;letter-spacing:.12em;color:var(--ac);font-weight:700}}
h1{{font-size:clamp(22px,4.6vw,32px);line-height:1.35;margin:6px 0 8px}}
.lead{{color:var(--mu);margin:0}}
.facts{{display:flex;flex-wrap:wrap;gap:10px;margin-top:16px}}.facts div{{background:var(--ac2);border-radius:10px;padding:8px 14px;font-size:14px}}.facts b{{font-size:18px}}
nav{{position:sticky;top:0;background:var(--bg);border-bottom:1px solid var(--ln);z-index:2}}nav .w{{display:flex;gap:18px;overflow-x:auto;padding:10px 16px;font-size:14px;white-space:nowrap}}nav a{{text-decoration:none}}
section{{padding:34px 0 8px}}h2{{font-size:21px;margin:0 0 6px}}.note{{color:var(--mu);font-size:14px;margin:0 0 16px}}
.grid{{list-style:none;padding:0;margin:0;display:grid;grid-template-columns:repeat(auto-fill,minmax(220px,1fr));gap:12px}}
.card{{background:var(--cd);border:1px solid var(--ln);border-radius:12px;padding:14px}}
.top{{display:flex;gap:6px;align-items:center;flex-wrap:wrap;font-size:12px}}
.st{{border-radius:4px;padding:1px 7px;font-weight:700;color:#fff}}.st-cur{{background:var(--ac)}}.st-new{{background:var(--nw)}}
.party{{color:var(--mu)}}.tag.op{{border:1px solid var(--mu);border-radius:4px;padding:0 6px;color:var(--mu)}}
.nm{{font-size:19px;font-weight:700;margin-top:6px}}.kana{{font-size:12px;color:var(--mu)}}
.ln{{margin-top:8px;font-size:14px;display:flex;gap:10px}}.muted{{color:var(--mu)}}
.src{{margin-top:8px;font-size:11.5px;color:var(--mu);line-height:1.5}}
.tbl{{overflow-x:auto}}table{{border-collapse:collapse;width:100%;background:var(--cd);font-size:14px}}th,td{{border-bottom:1px solid var(--ln);padding:10px;text-align:left}}td.n{{font-weight:700;white-space:nowrap}}
.news{{list-style:none;padding:0}}.news li{{padding:8px 0;border-bottom:1px solid var(--ln)}}.news time{{color:var(--mu);font-size:13px;margin-right:12px}}
.box{{background:var(--cd);border:1px solid var(--ln);border-radius:12px;padding:16px 18px;font-size:14px}}.box ol{{padding-left:20px;margin:6px 0}}
footer{{margin-top:40px;border-top:1px solid var(--ln);padding:22px 0 40px;font-size:13px;color:var(--mu)}}
</style></head>
<body>
<header><div class="w">
<div class="brand">文京区議選NAVI 2027</div>
<h1>文京区議会議員選挙2027<br>立候補予定者まとめ</h1>
<p class="lead">政党の公認発表など、公開されている情報だけで作った一覧です。すべてに出典と確認日を付けています。</p>
<div class="facts"><div>投票日 <b>{e(el['date_note'])}</b></div><div>定数 <b>{el['seats']}</b></div><div>掲載中の予定者 <b>{n}人</b></div><div>最終更新 <b>{e(d['updated'])}</b></div></div>
</div></header>
<nav><div class="w"><a href="#list">立候補予定者</a><a href="#party">政党の公認状況</a><a href="#news">更新情報</a><a href="#links">投票の情報</a><a href="#policy">掲載基準・運営者</a></div></nav>
<main class="w">
<section id="list"><h2>立候補予定者一覧（{n}人・50音順・敬称略）</h2>
<p class="note">氏名は前回選挙の届出名などに合わせています。本人の公表や政党の発表があり次第追加します。掲載されていない方も立候補する可能性があります。</p>
<ul class="grid">{''.join(rows)}</ul></section>
<section id="party"><h2>政党の公認状況</h2><p class="note">各党の公式発表で確認できた範囲です。</p>
<div class="tbl"><table><tbody>{''.join(prow)}</tbody></table></div></section>
<section id="news"><h2>更新情報</h2><ul class="news">{news}</ul></section>
<section id="links"><h2>投票の情報・前回の選挙</h2><ul>{links}</ul></section>
<section id="policy"><h2>掲載基準と運営者</h2><div class="box">
<ol><li>掲載するのは、本人の公表、政党の公式発表、選挙ドットコム等への本人掲載のいずれかで確認できた方だけです。うわさや推測では掲載しません。</li>
<li>並び順は50音順です。運営者本人も他の方とまったく同じ形式で掲載しています。</li>
<li>評価・論評・得票予想は載せません。</li>
<li>誤りの指摘や、掲載・修正・削除のご希望は下記までご連絡ください。確認のうえ速やかに対応します。</li></ol>
<p>運営：たかはま なおき（文京区議会議員・2027年文京区議選の立候補予定者）<br>連絡先：{CONTACT}</p>
<p class="muted">このサイトは文京区・文京区議会・文京区選挙管理委員会の公式サイトではありません。</p>
</div></section>
</main>
<footer><div class="w">© 文京区議選NAVI 2027 ／ 最終更新 {e(d['updated'])}</div></footer>
</body></html>
"""
out = ROOT / "public"; out.mkdir(exist_ok=True)
(out / "index.html").write_text(page, encoding="utf-8")
print("built", out / "index.html", n, "candidates")
