#!/bin/bash
# Zhubo TTS 集成验证脚本

echo "========================================"
echo "Zhubo TTS 集成验证"
echo "========================================"
echo ""

# 检查文件是否存在
echo "1. 检查关键文件..."
files=(
    "backend/app/tts/adapters/zhubo_adapter.py"
    "backend/app/config.py"
    "backend/app/main.py"
    "backend/.env.example"
    "ZHUBO_TTS_INTEGRATION.md"
    "INTEGRATION_SUMMARY.md"
)

all_exist=true
for file in "${files[@]}"; do
    if [ -f "$file" ]; then
        echo "  ✓ $file"
    else
        echo "  ✗ $file (缺失)"
        all_exist=false
    fi
done
echo ""

# 检查语法
echo "2. 检查 Python 语法..."
python_files=(
    "backend/app/tts/adapters/zhubo_adapter.py"
    "backend/app/main.py"
    "backend/app/config.py"
)

syntax_ok=true
for file in "${python_files[@]}"; do
    if python3 -m py_compile "$file" 2>/dev/null; then
        echo "  ✓ $file"
    else
        echo "  ✗ $file (语法错误)"
        syntax_ok=false
    fi
done
echo ""

# 运行结构测试
echo "3. 运行结构测试..."
cd backend && python3 test_zhubo_structure.py
test_result=$?
cd ..
echo ""

# 总结
echo "========================================"
echo "验证总结"
echo "========================================"
if [ "$all_exist" = true ] && [ "$syntax_ok" = true ] && [ $test_result -eq 0 ]; then
    echo "✓ 所有检查通过！"
    echo ""
    echo "Zhubo TTS 已成功集成到 car-live-deployment-v3"
    echo ""
    echo "下一步："
    echo "1. 启动 Zhubo TTS 服务 (http://localhost:8765)"
    echo "2. 配置 backend/.env 文件："
    echo "   TTS_PROVIDER=zhubo"
    echo "   ZHUBO_TTS_URL=http://localhost:8765"
    echo "3. 启动 car-live-deployment-v3 后端服务"
    echo "4. 测试 TTS 功能"
    echo ""
    echo "详细说明请查看 ZHUBO_TTS_INTEGRATION.md"
    exit 0
else
    echo "✗ 部分检查失败，请检查上述输出"
    exit 1
fi
