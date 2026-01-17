#!/bin/bash

# 字体子集生成工具 v1.1
# 用法：./font-subset.sh 输入字体.ttf [输出字体.woff2]

# 设置需要保留的字符（复制您的文本到这里）
TEXT="飛飛的個人主頁子曰君子不器孟子曰我知言我善養吾浩然之氣荀子曰君子能則寬容易直以開道人不能則恭敬繜絀以畏事人小人能則倨傲僻違以驕溢人不能則妬嫉怨誹以傾覆人故曰君子能則人榮學焉不能則人樂告之小人能則人賤學焉不能則人羞告之"

# 检查参数
if [ $# -lt 1 ]; then
    echo "错误：请指定输入字体文件"
    echo "用法: $0 输入字体.ttf [输出字体.woff2]"
    exit 1
fi

INPUT_FONT=$1
OUTPUT_FONT=${2:-"${INPUT_FONT%.*}-subset.woff2"}

# 检查依赖
check_dependency() {
    if ! command -v $1 &> /dev/null; then
        echo "错误: 未找到 $1，请先安装: pip install fonttools"
        exit 1
    fi
}

check_dependency pyftsubset

# 创建临时文件
TEMP_FILE=$(mktemp)

# 生成子集字体
echo "正在生成字体子集..."
pyftsubset "$INPUT_FONT" \
  --text="$TEXT" \
  --output-file="$TEMP_FILE" \
  --flavor=woff2 \
  --with-zopfli \
  --layout-features='*' \
  --glyph-names \
  --symbol-cmap \
  --legacy-cmap \
  --notdef-glyph \
  --notdef-outline \
  --recommended-glyphs \
  --name-IDs='*' \
  --name-languages='*'

# 检查结果
if [ $? -eq 0 ] && [ -f "$TEMP_FILE" ]; then
    mv "$TEMP_FILE" "$OUTPUT_FONT"
    ORIG_SIZE=$(stat -c%s "$INPUT_FONT")
    NEW_SIZE=$(stat -c%s "$OUTPUT_FONT")
    RATIO=$((100 * NEW_SIZE / ORIG_SIZE))
    
    echo "------------------------------------------------"
    echo "成功生成字体子集: $OUTPUT_FONT"
    echo "原始大小: $(numfmt --to=iec $ORIG_SIZE)"
    echo "子集大小: $(numfmt --to=iec $NEW_SIZE) (缩减 ${RATIO}%)"
    echo "包含字符数: ${#TEXT}"
    echo "------------------------------------------------"
else
    echo "错误: 字体子集生成失败"
    rm -f "$TEMP_FILE"
    exit 1
fi
