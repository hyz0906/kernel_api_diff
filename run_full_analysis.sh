#!/bin/bash
# run_full_analysis.sh - 执行完整分析流程

set -e

WORK_DIR="$HOME/kernel_analysis"
OLD_VERSION="v5.10"
NEW_VERSION="v6.1"

echo "========================================="
echo "Linux Kernel API 变化分析工具"
echo "========================================="
echo ""

# 步骤1: 准备环境
echo "[1/8] 准备分析环境..."
cd $WORK_DIR

# 步骤2: 生成ctags
echo "[2/8] 生成 ctags 数据库..."
bash generate_ctags.sh

# 步骤3: 执行主分析
echo "[3/8] 执行 API 差异分析..."
python3 kernel_api_analyzer.py \
    $WORK_DIR/linux-old \
    $WORK_DIR/linux-new

# 步骤4: 子系统分析
echo "[4/8] 执行子系统语义分析..."
python3 -c "
from kernel_api_analyzer import KernelAPIAnalyzer
from subsystem_analyzer import SubsystemAnalyzer
import json

with open('kernel_api_changes.json', 'r') as f:
    changes = json.load(f)

analyzer = SubsystemAnalyzer('$WORK_DIR/linux-old', '$WORK_DIR/linux-new')
subsys_changes = analyzer.analyze_subsystem_changes(changes)

changes['subsystem_analysis'] = subsys_changes

with open('kernel_api_changes.json', 'w') as f:
    json.dump(changes, f, indent=2)
"

# 步骤5: 生成报告
echo "[5/8] 生成分析报告..."
python3 generate_report.py kernel_api_changes.json

echo ""
echo "========================================="
echo "分析完成!"
echo "结果文件: kernel_api_changes.json"
echo "HTML报告: kernel_api_report.html"
echo "========================================="