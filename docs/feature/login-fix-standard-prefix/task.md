# タスク: ログイン時の404エラー修正 (標準プレフィックスへの回帰)

## 調査
- [x] `backend/function_app.py` の確認
- [x] `backend/src/main.py` の確認
- [x] `backend/src/api/auth.py` の確認
- [x] `backend/host.json` の確認
- [x] `backend/src/config.py` の確認
- [x] `frontend/src/api/client.ts` の確認
- [x] `frontend/src/pages/auth/LoginPage.tsx` の確認
- [x] 過去の修正履歴 (`docs/feature/login-not-found-fix/`) の調査
- [x] 原因の特定: FastAPI内部での `/api` プレフィックス付与と Azure の `routePrefix` 設定の競合

## 修正
- [ ] バックエンド: ルータープレフィックスから `/api` を削除 (`main.py`)
- [ ] バックエンド: `host.json` の `routePrefix` を `"api"` に変更
- [ ] バックエンド: `config.py` のデフォルトリダイレクトURIを修正
- [ ] フロントエンド: `vite.config.ts` のプロキシ設定に `rewrite` を追加
- [ ] ブランチの作成とコミット

## 検証
- [ ] ローカルでのログイン動作確認
- [ ] デプロイ後の動作確認 (ユーザーへの依頼)
- [ ] Walkthroughの作成
