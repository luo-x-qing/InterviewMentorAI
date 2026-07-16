"""
PDF转Markdown转换器
支持普通PDF和扫描版PDF（需要OCR）
"""
import os
import logging

logger = logging.getLogger(__name__)


def convert_pdf_to_md(input_path: str, output_path: str) -> bool:
    """
    将PDF文件转换为Markdown格式
    
    Args:
        input_path: PDF文件路径
        output_path: 输出Markdown文件路径
        
    Returns:
        bool: 转换是否成功
    """
    try:
        import pdfplumber
    except ImportError:
        logger.error("请安装pdfplumber: pip install pdfplumber")
        return False
    
    try:
        content_parts = []
        
        with pdfplumber.open(input_path) as pdf:
            for i, page in enumerate(pdf.pages):
                # 提取文本
                text = page.extract_text()
                if text:
                    content_parts.append(f"## 第 {i + 1} 页\n\n{text}\n")
                
                # 提取表格
                tables = page.extract_tables()
                for table in tables:
                    if table:
                        # 转换为Markdown表格
                        md_table = convert_table_to_markdown(table)
                        if md_table:
                            content_parts.append(f"\n{md_table}\n")
        
        # 合并内容
        content = "\n".join(content_parts)
        
        # 清理内容
        content = clean_content(content)
        
        # 写入文件
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        logger.info(f"PDF转换完成: {input_path} -> {output_path}")
        return True
        
    except Exception as e:
        logger.error(f"PDF转换失败: {e}")
        return False


def convert_table_to_markdown(table):
    """将表格转换为Markdown格式"""
    if not table or len(table) < 1:
        return ""
    
    # 处理表头
    headers = [str(cell) if cell else "" for cell in table[0]]
    
    # 处理数据行
    rows = []
    for row in table[1:]:
        rows.append([str(cell) if cell else "" for cell in row])
    
    # 生成Markdown表格
    header_line = "| " + " | ".join(headers) + " |"
    separator = "| " + " | ".join(["---"] * len(headers)) + " |"
    data_lines = ["| " + " | ".join(row) + " |" for row in rows]
    
    return "\n".join([header_line, separator] + data_lines)


def clean_content(content: str) -> str:
    """清理转换后的内容"""
    import re
    
    # 移除多余空行
    content = re.sub(r'\n{3,}', '\n\n', content)
    
    # 移除页眉页脚（常见模式）
    content = re.sub(r'^第\s*\d+\s*页.*$', '', content, flags=re.MULTILINE)
    
    # 移除多余空格
    content = re.sub(r' +', ' ', content)
    
    return content.strip()


if __name__ == '__main__':
    import sys
    if len(sys.argv) != 3:
        print("用法: python pdf_to_md.py <输入PDF> <输出MD>")
        sys.exit(1)
    
    convert_pdf_to_md(sys.argv[1], sys.argv[2])
