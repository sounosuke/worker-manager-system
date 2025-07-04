#!/bin/bash

# シンプルなClaude起動スクリプト
echo "🚀 Starting Claude Workers"

# 既存のセッションを終了
tmux kill-session -t manager 2>/dev/null
tmux kill-session -t worker1 2>/dev/null
tmux kill-session -t worker2 2>/dev/null
tmux kill-session -t worker3 2>/dev/null

# Manager
tmux new-session -d -s manager -n "manager"
tmux send-keys -t manager:0 "cd $(pwd)" C-m
tmux send-keys -t manager:0 "claude --dangerously-skip-permissions" C-m

# Worker1
tmux new-session -d -s worker1 -n "worker1"
tmux send-keys -t worker1:0 "cd $(pwd)" C-m
tmux send-keys -t worker1:0 "claude --dangerously-skip-permissions" C-m

# Worker2
tmux new-session -d -s worker2 -n "worker2"
tmux send-keys -t worker2:0 "cd $(pwd)" C-m
tmux send-keys -t worker2:0 "claude --dangerously-skip-permissions" C-m

# Worker3
tmux new-session -d -s worker3 -n "worker3"
tmux send-keys -t worker3:0 "cd $(pwd)" C-m
tmux send-keys -t worker3:0 "claude --dangerously-skip-permissions" C-m

echo "完了！"
echo "接続方法:"
echo "  tmux attach -t manager"
echo "  tmux attach -t worker1"
echo "  tmux attach -t worker2"
echo "  tmux attach -t worker3"