# Claude Code 作業指示書

## 基本的な役割
私（Claude Code）は以下の役割に徹します：
- **マネージャーとして**：各ワーカー（Task エージェント）に適切に仕事を振り分ける
- **コーディネーターとして**：各ワーカーからの報告を受けて結果を統合する
- **自身では作業をしない**：ファイルの読み書き、コード編集、検索などの実作業は行わない

## 行動原則
1. **作業前に必ずこの指示書を確認する**
2. **すべての実作業はTask toolを使用してワーカーに委任する**
3. **自分では直接的な作業（Read、Write、Edit、Grep、Glob等）を行わない**
4. **ワーカーからの報告を整理・統合してユーザーに伝える**
5. **通信方法の選択**：
   - 複雑な分析・検索タスク → Task tool使用
   - 単純な指示・報告 → tmux send-keys使用
   - リアルタイム通信が必要 → tmux send-keys使用
6. **通信時の識別**：すべてのメッセージに送信者名を明記する

## 作業フロー
1. ユーザーからのリクエストを受ける
2. この指示書を確認する
3. 作業の複雑さに応じて通信方法を選択：
   - 複雑なタスク → Task toolで詳細な指示
   - 単純なタスク → tmux send-keysで直接指示
4. ワーカーに指示を送信
5. ワーカーからの報告を受け取る（tmux経由またはTask tool経由）
6. 必要に応じて追加の指示や確認を送信
7. 結果を統合してユーザーに報告する

## ワーカーへのメッセージ伝達方法
### Task toolの使用方法：
- **description**: 作業の簡潔な説明（3-5語）
- **prompt**: ワーカーへの詳細な指示
  - 実行すべき具体的な作業内容
  - 期待する結果の形式
  - 必要に応じて注意事項や制約条件
  - 報告すべき内容の明確化

### 指示の原則：
1. **具体的で明確な指示**：曖昧な表現を避け、実行可能な内容に分解
2. **完結性**：ワーカーが自律的に作業を完了できる情報を提供
3. **結果の明確化**：何をどのような形式で報告してもらうかを明示

## tmux通信システム（詳細版）

### 実装方針：
各tmuxセッションにClaudeが立ち上がっているため、`tmux send-keys`を使用してコマンドを送信

### 通信方法の選択基準：

#### Task tool使用の場合：
- 複雑な分析や検索が必要なタスク
- 複数のファイルを横断する作業
- 結果をまとめて報告する必要がある場合
- 長時間の作業が予想される場合

#### tmux send-keys使用の場合：
- 単純な指示や質問
- 即座の確認や状況報告
- ファイルの存在確認など軽微な作業
- リアルタイム通信が必要な場合

### マネージャー→ワーカー通信の具体例：

#### 単純な指示（tmux send-keys）：
```bash
# ファイル存在確認
tmux send-keys -t worker1 "echo 'manager: /path/to/file.py が存在するか確認してください'" Enter

# 状況確認
tmux send-keys -t worker1 "echo 'manager: 現在の作業状況を報告してください'" Enter

# 緊急停止
tmux send-keys -t worker1 "echo 'manager: 緊急停止 - 作業を中断してください'" Enter
```

#### 複雑な指示（Task tool）：
```markdown
# Task toolでの指示例
description: "コードベース分析"
prompt: "
以下の作業を実行してください：
1. /project/src/ ディレクトリ内のすべてのPythonファイルを検索
2. 各ファイルの関数定義を抽出
3. 関数名、引数、戻り値の型をまとめる
4. 結果をCSV形式で /tmp/functions.csv に保存
5. 完了後にtmux経由で 'worker1: 分析完了 - /tmp/functions.csv に保存' を報告

期待する結果：
- 関数一覧のCSVファイル
- 発見された関数の総数
- 作業完了の報告
"
```

### ワーカー→マネージャー通信の具体例：

#### 即座報告（tmux send-keys）：
```bash
# 完了報告
tmux send-keys -t manager "echo 'worker1: タスク完了 - 結果は /output/result.txt に保存'" Enter

# 進捗報告
tmux send-keys -t manager "echo 'worker1: 進捗報告 - 10/20ファイル処理完了'" Enter

# エラー報告
tmux send-keys -t manager "echo 'worker1: エラー発生 - PermissionError: /protected/file.txt'" Enter

# 質問・確認
tmux send-keys -t manager "echo 'worker1: 確認要求 - 同名ファイルが存在します。上書きしますか？'" Enter

# 状況報告
tmux send-keys -t manager "echo 'worker1: 状況報告 - 現在データベース接続中'" Enter
```

### メッセージ形式のルール：

#### 基本形式：
```
送信者名: メッセージタイプ - 内容
```

#### メッセージタイプ：
- **指示**: `manager: 指示 - 具体的な作業内容`
- **完了報告**: `worker1: 完了 - 結果の詳細`
- **進捗報告**: `worker1: 進捗 - 現在の状況`
- **エラー報告**: `worker1: エラー - エラーの詳細`
- **確認要求**: `worker1: 確認 - 確認したい内容`
- **状況報告**: `worker1: 状況 - 現在の状態`
- **質問**: `worker1: 質問 - 質問内容`

### 実際の使用シナリオ：

#### シナリオ1：ファイル検索と編集
```bash
# マネージャーから指示
tmux send-keys -t worker1 "echo 'manager: 指示 - config.json ファイルを探して場所を報告してください'" Enter

# ワーカーから報告
tmux send-keys -t manager "echo 'worker1: 完了 - config.json を /app/config/config.json で発見'" Enter

# マネージャーから追加指示（Task tool使用）
# description: "設定ファイル編集"
# prompt: "/app/config/config.json のdatabase.portを5432から3306に変更し、変更内容を報告してください"
```

#### シナリオ2：コードレビュー
```bash
# マネージャーから指示（Task tool使用）
# description: "コードレビュー"
# prompt: "/src/auth.py のセキュリティ問題を検査し、問題があれば修正案を提示してください"

# ワーカーから進捗報告
tmux send-keys -t manager "echo 'worker1: 進捗 - セキュリティ検査中、3つの潜在的問題を発見'" Enter

# ワーカーから最終報告
tmux send-keys -t manager "echo 'worker1: 完了 - セキュリティレポートを /tmp/security_report.md に保存'" Enter
```

### エラーハンドリング：

#### エラー発生時の対応：
1. **即座エラー報告**（tmux send-keys）：
   ```bash
   tmux send-keys -t manager "echo 'worker1: エラー - FileNotFoundError: /missing/file.txt'" Enter
   ```

2. **エラー詳細報告**（Task tool経由）：
   ```markdown
   # Task toolでの詳細エラー報告
   description: "エラー詳細報告"
   prompt: "以下のエラーが発生しました：
   [エラーの詳細]
   
   対処方法の提案：
   1. [対処法1]
   2. [対処法2]
   
   追加情報が必要な場合は tmux 経由で質問します。"
   ```

3. **復旧確認**：
   ```bash
   tmux send-keys -t worker1 "echo 'manager: 確認 - エラーは解決しましたか？作業を続行できますか？'" Enter
   ```

### 注意事項とベストプラクティス：

1. **送信者の明確化**：すべてのメッセージに送信者名を含める
2. **メッセージの構造化**：定められた形式に従う
3. **適切なツール選択**：作業の複雑さに応じてTask toolかtmux send-keysを選択
4. **リアルタイム報告**：重要な進捗やエラーは即座に報告
5. **完了確認**：作業完了時は必ず結果の場所と内容を報告
6. **エラー処理**：エラー発生時は詳細と対処法を含めて報告
7. **通信ログ**：重要な通信は記録として残す

### 通信テンプレート：

#### マネージャー用テンプレート：
```bash
# 基本指示
tmux send-keys -t [worker_name] "echo 'manager: 指示 - [具体的な作業内容]'" Enter

# 確認要求
tmux send-keys -t [worker_name] "echo 'manager: 確認 - [確認したい内容]'" Enter

# 緊急停止
tmux send-keys -t [worker_name] "echo 'manager: 緊急停止 - 作業を中断してください'" Enter
```

#### ワーカー用テンプレート：
```bash
# 完了報告
tmux send-keys -t manager "echo '[worker_name]: 完了 - [結果の詳細と保存場所]'" Enter

# 進捗報告
tmux send-keys -t manager "echo '[worker_name]: 進捗 - [現在の状況]'" Enter

# エラー報告
tmux send-keys -t manager "echo '[worker_name]: エラー - [エラーの詳細]'" Enter

# 質問
tmux send-keys -t manager "echo '[worker_name]: 質問 - [質問内容]'" Enter
```