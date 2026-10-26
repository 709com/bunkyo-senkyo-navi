# 文京区議選NAVI 2027 運営ルール（Claude Code向け）

このサイトは、2027年文京区議会議員選挙の立候補予定者を公開情報だけでまとめる静的サイト。運営者は立候補予定者本人（たかはま なおき）なので、中立性と正確性を最優先する。

## 更新の流れ
1. `data/candidates.json` を編集する（ページを直接書き換えない）
2. `python3 build.py` で `public/index.html` を生成
3. 変更点を本人に日本語で報告し、「OK」をもらってから公開（デプロイ）する

## 掲載基準（絶対に守る）
- 掲載できる根拠は3つだけ：本人の公表／政党の公式発表／選挙ドットコム等への本人掲載。うわさ・議会内の話・推測では載せない
- すべての候補に出典URLと確認日を付ける
- 並びは50音順。運営者本人も他の人と同じ形式。運営者だけ目立たせない
- 評価・論評・得票予想・票読みは載せない（内部資料とは完全に分ける）
- 他候補について不確かな情報は載せない（公選法235条 虚偽事項公表罪のリスク）
- 公約・選挙公報の画像は転載しない。リンクで紹介する
- 運営者のLINE登録誘導などの宣伝をページに入れない

## 告示後
- ウェブサイト更新は可能だが、運営者の連絡先（メールアドレス等）の表示が必須。`build.py` の CONTACT を必ず設定する
- 投票の呼びかけを他候補に不利な形でしない

## 定期巡回（予定）
- 各党の公認ページ、選挙ドットコム、候補者の公式サイトを確認し、変更があれば候補データと「更新情報」を更新案として本人に提示する

## v2（複数ページ化）
- data/candidates.json（候補・政党・更新情報）と data/results.json（過去結果。tools/import_results.py で生成・検算済み）から `python3 build.py` で全ページを生成
- ページ：/ /kouho/ /kouho/<slug>/ /kekka/ /kekka/<年>/ /touhyou/ 他6ページ /about/ 404 sitemap robots
- 現職は必ず2023年の結果に名前が一致する（build時にassert）

## 引き継ぎメモ（2026-10-26 チャットから）
未完了（完了扱いにしない）
- main への push（公開）は未実施。pages.dev に出ているのは古い1ページ版
- 独自ドメイン未接続。Cloudflare から「active」のメールが届いたら、Pages に bunkyo-senkyo.jp と www を追加（本人作業）
- 旧サイト bunkyo-kosodate.net の非公開化は本人作業（Coming Soon プラグイン＋noindex）
- 判断待ち台帳に2件登録済み

気をつけること
- ページを直接書き換えない。data/*.json を直して build する（直接直すと次の build で消える）
- 未確認の項目（区選管の受付時間、区長選・都議選の年齢など）は「—」のまま。わかったら埋め、必ず確認日を付ける
- 川畑さん：本人の表明URLが取れたら「未確認」の表示を外す
- 告示後は連絡先の表示が必須（build.py の CONTACT は設定済み）
- 自動巡回は未実装。作るなら「提案→本人のOK→反映」。SNSリンクは公式サイトから辿れるものだけ
- zip で上書きするときは、古い版が混ざらないよう先にフォルダごとバックアップ
- このPCの python3 は Microsoft Store への案内だけで動かない。C:\Users\709co\AppData\Local\Programs\Python\Python311\python.exe で build する
- 表示確認用サーバー：D:\AI作業用\.claude\launch.json の「navi2027-local」（http://localhost:8027）

## 検索エンジンの扱い（2026-10-26 本人方針）
- ページは公開のまま（誰でも開ける）。ただし積極的に発信しないため、検索サイトには出さない
- build.py の `NOINDEX = True` で、全ページに noindex、Cloudflare 用 `_headers` に X-Robots-Tag、robots.txt からサイトマップの案内を外している
- robots.txt で巡回を拒否しない（拒否すると noindex が読まれず、URLだけ検索に出ることがある）
- Google Search Console への登録・サイトマップ送信は、本人が本格公開を決めるまでしない。解除は `NOINDEX = False` → build → 本人OK → push
