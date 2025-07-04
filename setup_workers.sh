#!/bin/bash

# Manager セッション
MANAGER_SESSION="manager_session"
WORKER1_SESSION="worker1_session"
WORKER2_SESSION="worker2_session"
WORKER3_SESSION="worker3_session"

# 既存のセッションがあれば削除
tmux kill-session -t $MANAGER_SESSION 2>/dev/null
tmux kill-session -t $WORKER1_SESSION 2>/dev/null
tmux kill-session -t $WORKER2_SESSION 2>/dev/null
tmux kill-session -t $WORKER3_SESSION 2>/dev/null

# Manager セッション作成
tmux new-session -d -s $MANAGER_SESSION -n "manager"
tmux send-keys -t $MANAGER_SESSION:0 "cd $(pwd)" C-m
tmux send-keys -t $MANAGER_SESSION:0 "echo 'Manager Starting with Claude...'" C-m
tmux send-keys -t $MANAGER_SESSION:0 "claude --dangerously-skip-permissions" C-m
sleep 3
tmux send-keys -t $MANAGER_SESSION:0 "cat manager_instructions.md && python3 manager_automation.py" Enter

# Worker1 セッション作成
tmux new-session -d -s $WORKER1_SESSION -n "worker1"
tmux send-keys -t $WORKER1_SESSION:0 "cd $(pwd)" C-m
tmux send-keys -t $WORKER1_SESSION:0 "echo 'Worker1 Starting with Claude...'" C-m
tmux send-keys -t $WORKER1_SESSION:0 "claude --dangerously-skip-permissions" C-m
sleep 3
tmux send-keys -t $WORKER1_SESSION:0 "cat worker_session_instructions.md && python3 worker_session_automation.py worker1" Enter

# Worker2 セッション作成
tmux new-session -d -s $WORKER2_SESSION -n "worker2"
tmux send-keys -t $WORKER2_SESSION:0 "cd $(pwd)" C-m
tmux send-keys -t $WORKER2_SESSION:0 "echo 'Worker2 Starting with Claude...'" C-m
tmux send-keys -t $WORKER2_SESSION:0 "claude --dangerously-skip-permissions" C-m
sleep 3
tmux send-keys -t $WORKER2_SESSION:0 "cat worker_session_instructions.md && python3 worker_session_automation.py worker2" Enter

# Worker3 セッション作成
tmux new-session -d -s $WORKER3_SESSION -n "worker3"
tmux send-keys -t $WORKER3_SESSION:0 "cd $(pwd)" C-m
tmux send-keys -t $WORKER3_SESSION:0 "echo 'Worker3 Starting with Claude...'" C-m
tmux send-keys -t $WORKER3_SESSION:0 "claude --dangerously-skip-permissions" C-m
sleep 3
tmux send-keys -t $WORKER3_SESSION:0 "cat worker_session_instructions.md && python3 worker_session_automation.py worker3" Enter

# 監視用セッション作成
MONITOR_SESSION="monitor_session"
tmux kill-session -t $MONITOR_SESSION 2>/dev/null
tmux new-session -d -s $MONITOR_SESSION -n "monitor"
tmux send-keys -t $MONITOR_SESSION:0 "cd $(pwd)" C-m
tmux send-keys -t $MONITOR_SESSION:0 "echo 'Log Monitor Starting...'" C-m
tmux send-keys -t $MONITOR_SESSION:0 "tail -f manager_log.txt worker*/worker*_log.txt" C-m

# 必要なディレクトリを作成
mkdir -p pending_tasks/worker1 pending_tasks/worker2 pending_tasks/worker3
mkdir -p completed_tasks/worker1 completed_tasks/worker2 completed_tasks/worker3

# セッション情報を表示
echo "TMux sessions created:"
echo "  manager_session  - Manager terminal"
echo "  worker1_session  - Worker1 (Data collection)"
echo "  worker2_session  - Worker2 (Data processing)"
echo "  worker3_session  - Worker3 (Report generation)"
echo "  monitor_session  - Log monitoring"
echo ""
echo "To attach to sessions:"
echo "  tmux attach -t manager_session"
echo "  tmux attach -t worker1_session"
echo "  tmux attach -t worker2_session"
echo "  tmux attach -t worker3_session"
echo "  tmux attach -t monitor_session"
echo ""
echo "To list all sessions: tmux ls"
echo "To kill all sessions: tmux kill-server"
echo ""

# 管理者セッションにアタッチするかどうか確認
read -p "Attach to manager session now? (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    tmux attach -t $MANAGER_SESSION
fi