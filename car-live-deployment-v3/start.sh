#!/usr/bin/env bash
set -e

# 获取项目根目录
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$PROJECT_ROOT/backend"
FRONTEND_DIR="$PROJECT_ROOT/frontend"

echo "=========================================="
echo "    🚀 启动汽车直播智能体服务"
echo "=========================================="

# 检查端口是否被监听
is_port_listening() {
  local port=$1
  if command -v lsof >/dev/null 2>&1; then
    lsof -i :"$port" -sTCP:LISTEN -t >/dev/null 2>&1
  elif command -v nc >/dev/null 2>&1; then
    nc -z 127.0.0.1 "$port" 2>/dev/null
  elif command -v ss >/dev/null 2>&1; then
    ss -tlpn | grep -q ":$port "
  else
    (echo >/dev/tcp/127.0.0.1/"$port") >/dev/null 2>&1
  fi
}

# 1. 启动后端 API (端口 8000)
if is_port_listening 8000; then
  echo "⚠️  后端端口 8000 已在运行中，复用现有进程。"
  BACKEND_PID=""
else
  echo "📦 正在启动后端 API 服务 (端口 8000)..."
  cd "$BACKEND_DIR"
  uv run uvicorn app.main:app --host 127.0.0.1 --port 8000 > "$PROJECT_ROOT/backend-runtime.log" 2> "$PROJECT_ROOT/backend-runtime-error.log" &
  BACKEND_PID=$!
  echo "   后端已在后台拉起 (PID: $BACKEND_PID)"
fi

# 2. 启动前端服务 (端口 5173)
if is_port_listening 5173; then
  echo "⚠️  前端端口 5173 已在运行中，复用现有进程。"
  FRONTEND_PID=""
else
  echo "🎨 正在启动前端静态服务 (端口 5173)..."
  cd "$FRONTEND_DIR"
  python3 -m http.server 5173 --bind 127.0.0.1 > "$PROJECT_ROOT/frontend-runtime.log" 2> "$PROJECT_ROOT/frontend-runtime-error.log" &
  FRONTEND_PID=$!
  echo "   前端已在后台拉起 (PID: $FRONTEND_PID)"
fi

# 3. 等待两端服务就绪
echo "⏳ 等待服务就绪..."
for i in {1..20}; do
  if is_port_listening 8000 && is_port_listening 5173; then
    break
  fi
  sleep 0.5
done

echo ""
echo "=========================================="
echo "    ✅ 所有服务已就绪！"
echo "    👉 前端控制台:   http://127.0.0.1:5173"
echo "    👉 后端 API 文档: http://127.0.0.1:8000/docs"
echo "=========================================="
echo "提示: 按 Ctrl+C 可一键停止服务；或另开终端执行 ./stop.sh"
echo ""

# 优雅退出钩子
cleanup() {
  echo ""
  echo "🛑 正在停止由本次脚本拉起的服务..."
  if [ -n "$BACKEND_PID" ]; then
    kill "$BACKEND_PID" 2>/dev/null || true
  fi
  if [ -n "$FRONTEND_PID" ]; then
    kill "$FRONTEND_PID" 2>/dev/null || true
  fi
  echo "已安全退出。"
  exit 0
}

trap cleanup INT TERM

# 如果传入了 --daemon 参数，则不阻塞前台
if [ "$1" == "--daemon" ]; then
  echo "已在后台常驻运行。停止请运行: ./stop.sh"
  exit 0
fi

# 前台挂起等待 Ctrl+C
wait
