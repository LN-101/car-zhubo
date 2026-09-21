#!/usr/bin/env bash
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "=========================================="
echo "    🛑 停止汽车直播智能体服务"
echo "=========================================="

kill_by_port() {
  local port=$1
  local pids=""
  if command -v lsof >/dev/null 2>&1; then
    pids=$(lsof -ti :"$port" 2>/dev/null || true)
  elif command -v fuser >/dev/null 2>&1; then
    fuser "$port/tcp" 2>/dev/null | tr -s ' ' '\n' || true
  fi

  if [ -n "$pids" ]; then
    echo "正在释放端口 $port 上的进程 (PID: $pids)..."
    for pid in $pids; do
      kill -15 "$pid" 2>/dev/null || true
    done
    sleep 1
    # 强制杀死残留
    for pid in $pids; do
      kill -9 "$pid" 2>/dev/null || true
    done
  else
    echo "端口 $port 没有被占用。"
  fi
}

kill_by_port 8000
kill_by_port 5173

echo "✅ 所有服务已停止。"
