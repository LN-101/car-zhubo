#!/bin/bash
# 停止 Zhubo TTS 和 car-live-deployment-v3 服务

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 配置
CAR_LIVE_DIR="/home/ln/AI/car-live-deployment-v3"
LOG_DIR="$CAR_LIVE_DIR/logs"

echo -e "${BLUE}停止所有服务...${NC}"
echo ""

# 停止 car-live 后端
if [ -f "$LOG_DIR/backend.pid" ]; then
    PID=$(cat "$LOG_DIR/backend.pid")
    if kill -0 $PID 2>/dev/null; then
        echo -e "${YELLOW}停止 car-live 后端 (PID: $PID)${NC}"
        kill $PID
        sleep 2
        if kill -0 $PID 2>/dev/null; then
            echo -e "${YELLOW}强制停止...${NC}"
            kill -9 $PID
        fi
        rm -f "$LOG_DIR/backend.pid"
        echo -e "${GREEN}✓ car-live 后端已停止${NC}"
    else
        echo -e "${YELLOW}car-live 后端进程不存在 (PID: $PID)${NC}"
        rm -f "$LOG_DIR/backend.pid"
    fi
else
    echo -e "${YELLOW}未找到 car-live 后端 PID 文件${NC}"
fi

# 停止 Zhubo TTS
if [ -f "$LOG_DIR/zhubo.pid" ]; then
    PID=$(cat "$LOG_DIR/zhubo.pid")
    if kill -0 $PID 2>/dev/null; then
        echo -e "${YELLOW}停止 Zhubo TTS (PID: $PID)${NC}"
        kill $PID
        sleep 2
        if kill -0 $PID 2>/dev/null; then
            echo -e "${YELLOW}强制停止...${NC}"
            kill -9 $PID
        fi
        rm -f "$LOG_DIR/zhubo.pid"
        echo -e "${GREEN}✓ Zhubo TTS 已停止${NC}"
    else
        echo -e "${YELLOW}Zhubo TTS 进程不存在 (PID: $PID)${NC}"
        rm -f "$LOG_DIR/zhubo.pid"
    fi
else
    echo -e "${YELLOW}未找到 Zhubo TTS PID 文件${NC}"
fi

# 检查端口
echo ""
echo -e "${BLUE}检查端口占用...${NC}"
for port in 8765 8000; do
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        echo -e "${YELLOW}! 端口 $port 仍被占用${NC}"
        PID=$(lsof -Pi :$port -sTCP:LISTEN -t)
        echo -e "  进程 PID: $PID"
        echo -e "  使用 ${YELLOW}kill $PID${NC} 手动停止"
    else
        echo -e "${GREEN}✓ 端口 $port 已释放${NC}"
    fi
done

echo ""
echo -e "${GREEN}完成！${NC}"
