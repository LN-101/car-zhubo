#!/bin/bash
# Zhubo TTS + car-live-deployment-v3 一键启动脚本

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 配置
ZHUBO_DIR="/home/ln/AI/zhubo"
CAR_LIVE_DIR="/home/ln/AI/car-live-deployment-v3"
BACKEND_DIR="$CAR_LIVE_DIR/backend"
FRONTEND_DIR="$CAR_LIVE_DIR/frontend"

# Zhubo TTS 默认配置
ZHUBO_PORT=8765
ZHUBO_HOST="0.0.0.0"

# car-live 后端默认配置
CAR_LIVE_PORT=8000
CAR_LIVE_HOST="0.0.0.0"

# car-live 前端默认配置
FRONTEND_PORT=5173
FRONTEND_HOST="127.0.0.1"

# 日志文件
LOG_DIR="$CAR_LIVE_DIR/logs"
ZHUBO_LOG="$LOG_DIR/zhubo_tts.log"
BACKEND_LOG="$LOG_DIR/backend.log"
FRONTEND_LOG="$LOG_DIR/frontend.log"

# 创建日志目录
mkdir -p "$LOG_DIR"

echo -e "${BLUE}╔════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║                                                                ║${NC}"
echo -e "${BLUE}║     Zhubo TTS + car-live-deployment-v3 一键启动               ║${NC}"
echo -e "${BLUE}║          (Zhubo TTS + 后端 API + 前端服务)                     ║${NC}"
echo -e "${BLUE}║                                                                ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════════╝${NC}"
echo ""

# 函数：检查端口是否被占用
check_port() {
    local port=$1
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1 ; then
        return 0  # 端口被占用
    else
        return 1  # 端口空闲
    fi
}

# 函数：等待服务启动
wait_for_service() {
    local url=$1
    local name=$2
    local max_wait=30
    local count=0
    
    echo -ne "${YELLOW}等待 $name 启动"
    while [ $count -lt $max_wait ]; do
        if curl -s "$url" > /dev/null 2>&1; then
            echo -e " ${GREEN}✓${NC}"
            return 0
        fi
        echo -n "."
        sleep 1
        count=$((count + 1))
    done
    echo -e " ${RED}✗${NC}"
    return 1
}

# 函数：停止服务
stop_services() {
    echo ""
    echo -e "${YELLOW}正在停止服务...${NC}"
    
    # 停止前端
    if [ -f "$LOG_DIR/frontend.pid" ]; then
        PID=$(cat "$LOG_DIR/frontend.pid")
        if kill -0 $PID 2>/dev/null; then
            echo -e "${YELLOW}  停止前端服务 (PID: $PID)${NC}"
            kill $PID
            rm -f "$LOG_DIR/frontend.pid"
        fi
    fi
    
    # 停止 car-live 后端
    if [ -f "$LOG_DIR/backend.pid" ]; then
        PID=$(cat "$LOG_DIR/backend.pid")
        if kill -0 $PID 2>/dev/null; then
            echo -e "${YELLOW}  停止 car-live 后端 (PID: $PID)${NC}"
            kill $PID
            rm -f "$LOG_DIR/backend.pid"
        fi
    fi
    
    # 停止 Zhubo TTS
    if [ -f "$LOG_DIR/zhubo.pid" ]; then
        PID=$(cat "$LOG_DIR/zhubo.pid")
        if kill -0 $PID 2>/dev/null; then
            echo -e "${YELLOW}  停止 Zhubo TTS (PID: $PID)${NC}"
            kill $PID
            rm -f "$LOG_DIR/zhubo.pid"
        fi
    fi
    
    echo -e "${GREEN}服务已停止${NC}"
    exit 0
}

# 捕获 Ctrl+C
trap stop_services INT TERM

# 1. 检查目录
echo -e "${BLUE}[1/7] 检查项目目录...${NC}"
if [ ! -d "$ZHUBO_DIR" ]; then
    echo -e "${RED}✗ Zhubo 目录不存在: $ZHUBO_DIR${NC}"
    exit 1
fi
if [ ! -d "$BACKEND_DIR" ]; then
    echo -e "${RED}✗ car-live 后端目录不存在: $BACKEND_DIR${NC}"
    exit 1
fi
if [ ! -d "$FRONTEND_DIR" ]; then
    echo -e "${RED}✗ car-live 前端目录不存在: $FRONTEND_DIR${NC}"
    exit 1
fi
echo -e "${GREEN}✓ 项目目录检查通过${NC}"

# 2. 检查 Python 和依赖
echo -e "${BLUE}[2/7] 检查 Python 环境...${NC}"
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}✗ Python3 未安装${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Python3: $(python3 --version)${NC}"

# 3. 检查端口占用
echo -e "${BLUE}[3/7] 检查端口占用...${NC}"
if check_port $ZHUBO_PORT; then
    echo -e "${YELLOW}! 端口 $ZHUBO_PORT 已被占用，Zhubo TTS 可能已在运行${NC}"
    ZHUBO_RUNNING=true
else
    ZHUBO_RUNNING=false
fi

if check_port $CAR_LIVE_PORT; then
    echo -e "${RED}✗ 端口 $CAR_LIVE_PORT 已被占用，请先停止占用该端口的服务${NC}"
    exit 1
fi

if check_port $FRONTEND_PORT; then
    echo -e "${YELLOW}! 端口 $FRONTEND_PORT 已被占用，前端服务可能已在运行${NC}"
    FRONTEND_RUNNING=true
else
    FRONTEND_RUNNING=false
fi

# 4. 启动 Zhubo TTS
if [ "$ZHUBO_RUNNING" = false ]; then
    echo -e "${BLUE}[4/7] 启动 Zhubo TTS...${NC}"
    
    # 检查 IndexTTS 虚拟环境（用于运行 Zhubo API）
    INDEX_TTS_VENV="/home/ln/AI/index-tts/.venv"
    if [ ! -d "$INDEX_TTS_VENV" ]; then
        echo -e "${RED}✗ IndexTTS 虚拟环境不存在: $INDEX_TTS_VENV${NC}"
        echo -e "${YELLOW}  请先安装 IndexTTS 并设置虚拟环境${NC}"
        exit 1
    fi
    
    # 检查 Zhubo API 服务器
    if [ ! -f "$ZHUBO_DIR/tts_broadcast/api_server.py" ]; then
        echo -e "${RED}✗ 找不到 Zhubo API 服务器: $ZHUBO_DIR/tts_broadcast/api_server.py${NC}"
        exit 1
    fi
    
    # 安装 fastapi 和 uvicorn 到 IndexTTS 虚拟环境（如果没有）
    if ! "$INDEX_TTS_VENV/bin/python" -c "import fastapi, uvicorn" 2>/dev/null; then
        echo -e "${YELLOW}  安装 FastAPI 和 uvicorn...${NC}"
        "$INDEX_TTS_VENV/bin/pip" install fastapi uvicorn[standard] > /dev/null 2>&1
    fi
    
    # 使用 IndexTTS 虚拟环境启动 Zhubo API
    cd "$ZHUBO_DIR"
    nohup "$INDEX_TTS_VENV/bin/python" -m tts_broadcast.api_server \
        --host $ZHUBO_HOST \
        --port $ZHUBO_PORT \
        --repo /home/ln/AI/index-tts \
        > "$ZHUBO_LOG" 2>&1 &
    ZHUBO_PID=$!
    
    echo $ZHUBO_PID > "$LOG_DIR/zhubo.pid"
    echo -e "${GREEN}✓ Zhubo TTS 已启动 (PID: $ZHUBO_PID)${NC}"
    echo -e "${YELLOW}  日志: $ZHUBO_LOG${NC}"
    
    # 等待 Zhubo TTS 启动
    if ! wait_for_service "http://localhost:$ZHUBO_PORT/health" "Zhubo TTS"; then
        echo -e "${RED}✗ Zhubo TTS 启动失败，请查看日志: $ZHUBO_LOG${NC}"
        tail -20 "$ZHUBO_LOG"
        stop_services
        exit 1
    fi
else
    echo -e "${BLUE}[4/7] Zhubo TTS 已在运行${NC}"
    echo -e "${GREEN}✓ 跳过启动${NC}"
fi

# 5. 配置 car-live 后端
echo -e "${BLUE}[5/7] 配置 car-live 后端...${NC}"
cd "$BACKEND_DIR"

# 检查 .env 文件
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}! .env 文件不存在，正在创建...${NC}"
    cp .env.example .env
fi

# 更新 .env 配置
if grep -q "^TTS_PROVIDER=" .env; then
    sed -i 's/^TTS_PROVIDER=.*/TTS_PROVIDER=zhubo/' .env
else
    echo "TTS_PROVIDER=zhubo" >> .env
fi

if grep -q "^ZHUBO_TTS_URL=" .env; then
    sed -i "s|^ZHUBO_TTS_URL=.*|ZHUBO_TTS_URL=http://localhost:$ZHUBO_PORT|" .env
else
    echo "ZHUBO_TTS_URL=http://localhost:$ZHUBO_PORT" >> .env
fi

echo -e "${GREEN}✓ 配置已更新:${NC}"
echo -e "  TTS_PROVIDER=zhubo"
echo -e "  ZHUBO_TTS_URL=http://localhost:$ZHUBO_PORT"

# 6. 启动 car-live 后端
echo -e "${BLUE}[6/7] 启动 car-live 后端...${NC}"
cd "$BACKEND_DIR"

# 检查虚拟环境
if [ ! -d ".venv" ]; then
    echo -e "${RED}✗ 虚拟环境不存在: $BACKEND_DIR/.venv${NC}"
    echo -e "${YELLOW}  请先运行: cd $BACKEND_DIR && python3 -m venv .venv && .venv/bin/pip install -r requirements.txt${NC}"
    stop_services
    exit 1
fi

# 启动后端（使用虚拟环境）
nohup "$BACKEND_DIR/.venv/bin/python" -m uvicorn app.main:app --host $CAR_LIVE_HOST --port $CAR_LIVE_PORT > "$BACKEND_LOG" 2>&1 &
BACKEND_PID=$!
echo $BACKEND_PID > "$LOG_DIR/backend.pid"
echo -e "${GREEN}✓ car-live 后端已启动 (PID: $BACKEND_PID)${NC}"
echo -e "${YELLOW}  日志: $BACKEND_LOG${NC}"

# 等待后端启动
if ! wait_for_service "http://localhost:$CAR_LIVE_PORT/docs" "car-live 后端"; then
    echo -e "${RED}✗ car-live 后端启动失败，请查看日志: $BACKEND_LOG${NC}"
    tail -20 "$BACKEND_LOG"
    stop_services
    exit 1
fi

# 7. 启动前端服务
if [ "$FRONTEND_RUNNING" = false ]; then
    echo -e "${BLUE}[7/7] 启动前端服务...${NC}"
    cd "$FRONTEND_DIR"
    nohup python3 -m http.server $FRONTEND_PORT --bind $FRONTEND_HOST > "$FRONTEND_LOG" 2>&1 &
    FRONTEND_PID=$!
    echo $FRONTEND_PID > "$LOG_DIR/frontend.pid"
    echo -e "${GREEN}✓ 前端服务已启动 (PID: $FRONTEND_PID)${NC}"
    echo -e "${YELLOW}  日志: $FRONTEND_LOG${NC}"
    
    # 等待前端启动
    sleep 2
    if ! check_port $FRONTEND_PORT; then
        echo -e "${RED}✗ 前端服务启动失败，请查看日志: $FRONTEND_LOG${NC}"
        tail -20 "$FRONTEND_LOG"
        stop_services
        exit 1
    fi
else
    echo -e "${BLUE}[7/7] 前端服务已在运行${NC}"
    echo -e "${GREEN}✓ 跳过启动${NC}"
fi

# 启动完成
echo ""
echo -e "${GREEN}╔════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║                                                                ║${NC}"
echo -e "${GREEN}║                    🎉 启动成功！                               ║${NC}"
echo -e "${GREEN}║                                                                ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${BLUE}服务地址:${NC}"
echo -e "  ${GREEN}✓${NC} 前端控制台:     http://$FRONTEND_HOST:$FRONTEND_PORT"
echo -e "  ${GREEN}✓${NC} car-live 后端:  http://localhost:$CAR_LIVE_PORT"
echo -e "  ${GREEN}✓${NC} API 文档:       http://localhost:$CAR_LIVE_PORT/docs"
echo -e "  ${GREEN}✓${NC} Zhubo TTS:      http://localhost:$ZHUBO_PORT"
echo ""
echo -e "${BLUE}日志文件:${NC}"
echo -e "  前端服务:   $FRONTEND_LOG"
echo -e "  后端服务:   $BACKEND_LOG"
echo -e "  Zhubo TTS:  $ZHUBO_LOG"
echo ""
echo -e "${BLUE}测试命令:${NC}"
echo -e "  ${YELLOW}curl -X POST http://localhost:$CAR_LIVE_PORT/api/tts/stream \\${NC}"
echo -e "    ${YELLOW}-H 'Content-Type: application/json' \\${NC}"
echo -e "    ${YELLOW}-d '{\"text\": \"你好，这是测试\", \"voice_id\": \"female_warm_01\"}' \\${NC}"
echo -e "    ${YELLOW}--output test.wav${NC}"
echo ""
echo -e "${BLUE}管理命令:${NC}"
echo -e "  查看前端日志:     tail -f $FRONTEND_LOG"
echo -e "  查看后端日志:     tail -f $BACKEND_LOG"
echo -e "  查看 Zhubo 日志:  tail -f $ZHUBO_LOG"
echo -e "  停止所有服务:     按 Ctrl+C 或运行 $CAR_LIVE_DIR/stop_services.sh"
echo ""
echo -e "${YELLOW}所有服务已在后台运行${NC}"
echo -e "${YELLOW}停止所有服务: $CAR_LIVE_DIR/stop_services.sh${NC}"
echo ""
