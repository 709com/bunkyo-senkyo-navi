# 公開手順書（GitHub ＋ Cloudflare Pages）

対象：文京区議選NAVI 2027（bunkyo-senkyo.jp）
読み手：Claude Code と 先生ご本人。【本人】と書いた手順は人が画面で行う（ログイン・契約・権限の許可はAIが代行しない）。

## 0. 前提
- 【本人】ムームードメインで bunkyo-senkyo.jp を取得済み
- 【本人】GitHubアカウントあり。Cloudflareアカウント（無料）を作成済み

## 1. リポジトリを作る（Claude Code）
1. このフォルダ一式（data/・build.py・public/・CLAUDE.md・PUBLISH.md）を作業フォルダに置く
2. `python3 build.py` で public/index.html を生成
3. GitHubに公開リポジトリ `bunkyo-senkyo-navi` を作成し、main ブランチへプッシュ
   - public/ も含めてコミットする（Cloudflare側でビルドしない運用）
   - 公開リポジトリにする理由：掲載データと更新履歴を誰でも確認でき、中立性の説明になる

## 2. Cloudflare Pages とつなぐ（【本人】画面操作。Claude Codeは横で案内）
1. Cloudflare → Workers & Pages → 作成 → Pages → 「Gitに接続」
2. GitHubの連携を許可し、`bunkyo-senkyo-navi` を選ぶ
3. 設定：フレームワーク「なし」／ビルドコマンド「空欄」／出力ディレクトリ `public`
4. 保存してデプロイ → `*.pages.dev` のURLで表示を確認

## 3. ドメインを向ける（【本人】画面操作）
1. Cloudflare → 「サイトを追加」→ bunkyo-senkyo.jp（Freeプラン）
2. 表示された2つのネームサーバーを、ムームードメインの「ネームサーバ設定変更」→「GMOペパボ以外のネームサーバを使用する」に入力
3. 反映後（数時間〜1日）、Pagesプロジェクト → カスタムドメイン → bunkyo-senkyo.jp と www.bunkyo-senkyo.jp を追加
4. https://bunkyo-senkyo.jp で表示されることを確認

## 4. 公開後のチェック（Claude Code）
- スマホ幅で崩れないか
- 全出典リンクが開けるか（リンク切れ確認）
- 連絡先 info@takahamanaoki.com が表示されているか
- Google Search Console に登録し、サイトマップ代わりにトップURLを送信（【本人】ログイン）

## 5. 以後の更新
CLAUDE.md の手順どおり：data を直す → build → 本人に差分報告 → 「OK」で main にプッシュ → 自動で公開
