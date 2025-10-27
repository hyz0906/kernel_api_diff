#!/bin/bash
# generate_ctags.sh - 为两个版本生成ctags

WORK_DIR="$HOME/kernel_analysis"

generate_tags() {
    local kernel_dir=$1
    local output_name=$2
    
    echo "正在为 $kernel_dir 生成 ctags..."
    cd $kernel_dir
    
    # 生成详细的ctags，包含所有符号信息
    ctags \
        --languages=C \
        --c-kinds=+defgmstuv \
        --fields=+iaS \
        --extra=+fq \
        --output-format=json \
        -o tags.json \
        -R \
        --exclude=Documentation \
        --exclude=tools \
        --exclude=samples \
        --exclude=scripts \
        --exclude=*.o \
        --exclude=*.a \
        .
    
    # 同时生成传统格式以便查询
    ctags \
        --languages=C \
        --c-kinds=+defgmstuv \
        --fields=+iaS \
        --extra=+fq \
        -R \
        --exclude=Documentation \
        --exclude=tools \
        --exclude=samples \
        --exclude=scripts \
        .
    
    echo "Tags 生成完成: $kernel_dir/tags.json"
}

generate_tags "$WORK_DIR/linux-old" "old"
generate_tags "$WORK_DIR/linux-new" "new"