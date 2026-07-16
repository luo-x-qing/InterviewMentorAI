"""
TXT转Markdown转换器
对纯文本进行格式化处理
"""
import os
import re
import logging

logger = logging.getLogger(__name__)


def convert_txt_to_md(input_path: str, output_path: str) -> bool:
    """
    将TXT文件转换为Markdown格式
    
    Args:
        input_path: TXT文件路径
        output_path: 输出Markdown文件路径
        
    Returns:
        bool: 转换是否成功
    """
    try:
        # 尝试不同编码读取文件
        content = read_file_with_encoding(input_path)
        
        if content is None:
            logger.error(f"无法读取文件: {input_path}")
            return False
        
        # 转换为Markdown
        md_content = convert_text_to_markdown(content)
        
        # 清理内容
        md_content = clean_content(md_content)
        
        # 写入文件
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(md_content)
        
        logger.info(f"TXT转换完成: {input_path} -> {output_path}")
        return True
        
    except Exception as e:
        logger.error(f"TXT转换失败: {e}")
        return False


def read_file_with_encoding(file_path: str) -> str:
    """尝试不同编码读取文件"""
    encodings = ['utf-8', 'gbk', 'gb2312', 'gb18030', 'latin-1']
    
    for encoding in encodings:
        try:
            with open(file_path, 'r', encoding=encoding) as f:
                content = f.read()
            return content
        except UnicodeDecodeError:
            continue
    
    # 最后尝试二进制读取
    try:
        with open(file_path, 'rb') as f:
            raw = f.read()
            # 尝试自动检测编码
            import chardet
            result = chardet.detect(raw)
            if result and result.get('encoding'):
                return raw.decode(result['encoding'])
    except:
        pass
    
    return None


def convert_text_to_markdown(text: str) -> str:
    """将纯文本转换为Markdown格式"""
    lines = text.split('\n')
    md_lines = []
    
    for line in lines:
        stripped = line.strip()
        
        # 跳过空行
        if not stripped:
            md_lines.append('')
            continue
        
        # 检测标题（常见格式）
        if is_heading(stripped):
            md_lines.append(convert_heading(stripped))
        # 检测列表项
        elif is_list_item(stripped):
            md_lines.append(convert_list_item(stripped))
        # 普通文本
        else:
            md_lines.append(stripped)
    
    return '\n'.join(md_lines)


def is_heading(line: str) -> bool:
    """判断是否为标题"""
    # 数字开头的标题：1. xxx 或 1、xxx
    if re.match(r'^\d+[.、]\s*\S', line):
        return True
    
    # 中文数字标题：一、xxx 或 （一）xxx
    if re.match(r'^[一二三四五六七八九十]+[、．.]\s*\S', line):
        return True
    
    # 大写罗马数字：I. xxx
    if re.match(r'^[IVX]+\.\s*\S', line):
        return True
    
    # 全大写或特殊格式
    if re.match(r'^[A-Z][A-Z\s]+$', line):
        return True
    
    return False


def convert_heading(line: str) -> str:
    """转换标题"""
    # 数字标题
    match = re.match(r'^(\d+)[.、]\s*(.+)', line)
    if match:
        num = int(match.group(1))
        text = match.group(2)
        # 根据数字判断标题级别
        if num <= 3:
            return f"## {text}"
        else:
            return f"### {text}"
    
    # 中文数字标题
    cn_nums = '一二三四五六七八九十'
    match = re.match(r'^([一二三四五六七八九十]+)[、．.]\s*(.+)', line)
    if match:
        num_str = match.group(1)
        num = cn_nums.index(num_str[0]) + 1 if num_str in cn_nums else 1
        text = match.group(2)
        if num <= 3:
            return f"## {text}"
        else:
            return f"### {text}"
    
    # 罗马数字
    if re.match(r'^[IVX]+\.\s*', line):
        return f"## {line}"
    
    # 全大写（可能是小标题）
    return f"### {line}"


def is_list_item(line: str) -> bool:
    """判断是否为列表项"""
    # 常见列表格式
    patterns = [
        r'^[-•●○]\s+',      # - xxx 或 • xxx
        r'^\d+[.)]\s+',     # 1. xxx 或 1) xxx
        r'^[（(]\d+[)）]\s+', # (1) xxx 或 （1）xxx
        r'^[一二三四五六七八九十]+[、]\s+', # 一、xxx
    ]
    
    for pattern in patterns:
        if re.match(pattern, line):
            return True
    
    return False


def convert_list_item(line: str) -> str:
    """转换列表项"""
    # 已经是标准Markdown格式
    if re.match(r'^[-•●○]\s+', line):
        return line
    
    # 数字列表
    match = re.match(r'^(\d+)[.)]\s+(.+)', line)
    if match:
        return f"{match.group(1)}. {match.group(2)}"
    
    # 中文数字列表
    match = re.match(r'^[（(](\d+)[)）]\s+(.+)', line)
    if match:
        return f"{match.group(1)}. {match.group(2)}"
    
    # 中文序号
    cn_nums = '一二三四五六七八九十'
    match = re.match(r'^([一二三四五六七八九十]+)[、]\s*(.+)', line)
    if match:
        num_str = match.group(1)
        num = cn_nums.index(num_str[0]) + 1 if num_str in cn_nums else 1
        return f"{num}. {match.group(2)}"
    
    # 默认转换为无序列表
    return f"- {line.lstrip()}"


def clean_content(content: str) -> str:
    """清理转换后的内容"""
    # 移除多余空行
    content = re.sub(r'\n{3,}', '\n\n', content)
    
    # 移除行首行尾空格
    lines = content.split('\n')
    lines = [line.rstrip() for line in lines]
    content = '\n'.join(lines)
    
    return content.strip()


if __name__ == '__main__':
    import sys
    if len(sys.argv) != 3:
        print("用法: python txt_to_md.py <输入TXT> <输出MD>")
        sys.exit(1)
    
    convert_txt_to_md(sys.argv[1], sys.argv[2])
