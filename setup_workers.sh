#!/bin/bash

# tmuxセッションの名前
SESSION_NAME="worker_session"

# 既存のセッションがあれば削除
tmux kill-session -t $SESSION_NAME 2>/dev/null

# 新しいセッションを作成（デタッチモード）
tmux new-session -d -s $SESSION_NAME -n "manager"

# Manager ウィンドウ
tmux send-keys -t $SESSION_NAME:0 "cd $(pwd)" C-m
tmux send-keys -t $SESSION_NAME:0 "echo 'Manager Starting with Claude...'" C-m
tmux send-keys -t $SESSION_NAME:0 "claude --dangerously-skip-permissions" C-m
sleep 2
tmux send-keys -t $SESSION_NAME:0 "cat manager_instructions.md && python3 manager_automation.py" C-m

# Worker1 ウィンドウ
tmux new-window -t $SESSION_NAME:1 -n "worker1"
tmux send-keys -t $SESSION_NAME:1 "cd $(pwd)" C-m
tmux send-keys -t $SESSION_NAME:1 "echo 'Worker1 Starting with Claude...'" C-m
tmux send-keys -t $SESSION_NAME:1 "claude --dangerously-skip-permissions" C-m
sleep 2
tmux send-keys -t $SESSION_NAME:1 "cat worker1/worker1_instructions.md && python3 worker_automation.py worker1" C-m

# Worker2 ウィンドウ
tmux new-window -t $SESSION_NAME:2 -n "worker2"
tmux send-keys -t $SESSION_NAME:2 "cd $(pwd)" C-m
tmux send-keys -t $SESSION_NAME:2 "echo 'Worker2 Starting with Claude...'" C-m
tmux send-keys -t $SESSION_NAME:2 "claude --dangerously-skip-permissions" C-m
sleep 2
tmux send-keys -t $SESSION_NAME:2 "cat worker2/worker2_instructions.md && python3 worker_automation.py worker2" C-m

# Worker3 ウィンドウ
tmux new-window -t $SESSION_NAME:3 -n "worker3"
tmux send-keys -t $SESSION_NAME:3 "cd $(pwd)" C-m
tmux send-keys -t $SESSION_NAME:3 "echo 'Worker3 Starting with Claude...'" C-m
tmux send-keys -t $SESSION_NAME:3 "claude --dangerously-skip-permissions" C-m
sleep 2
tmux send-keys -t $SESSION_NAME:3 "cat worker3/worker3_instructions.md && python3 worker_automation.py worker3" C-m

# 監視ウィンドウ（ログ表示用）
tmux new-window -t $SESSION_NAME:4 -n "monitor"
tmux send-keys -t $SESSION_NAME:4 "cd $(pwd)" C-m
tmux send-keys -t $SESSION_NAME:4 "echo 'Log Monitor Starting...'" C-m
tmux send-keys -t $SESSION_NAME:4 "tail -f manager_log.txt worker*/worker*_log.txt" C-m

# 必要なディレクトリを作成
mkdir -p pending_tasks/worker1 pending_tasks/worker2 pending_tasks/worker3
mkdir -p completed_tasks/worker1 completed_tasks/worker2 completed_tasks/worker3

# セッションにアタッチ
echo "TMux session '$SESSION_NAME' created with following windows:"
echo "  0: manager   - Manager terminal"
echo "  1: worker1   - Worker1 (Data collection)"
echo "  2: worker2   - Worker2 (Data processing)"
echo "  3: worker3   - Worker3 (Report generation)"
echo "  4: monitor   - Log monitoring"
echo ""
echo "To attach to the session, run: tmux attach -t $SESSION_NAME"
echo "To switch between windows: Ctrl-b [window-number]"
echo "To detach: Ctrl-b d"
echo ""

# 自動的にセッションにアタッチするかどうか確認
read -p "Attach to the session now? (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    tmux attach -t $SESSION_NAME
fi