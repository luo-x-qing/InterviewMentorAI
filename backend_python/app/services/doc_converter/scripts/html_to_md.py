"""
HTML转Markdown转换器
支持本地HTML文件和网页内容
"""
import os
import logging
import re

logger = logging.getLogger(__name__)


def convert_html_to_md(input_path: str, output_path: str) -> bool:
    """
    将HTML文件转换为Markdown格式
    
    Args:
        input_path: HTML文件路径
        output_path: 输出Markdown文件路径
        
    Returns:
        bool: 转换是否成功
    """
    try:
        from bs4 import BeautifulSoup
    except ImportError:
        logger.error("请安装beautifulsoup4: pip install beautifulsoup4")
        return False
    
    try:
        # 读取HTML文件
        with open(input_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        # 尝试检测编码
        if 'charset=' in html_content.lower():
            match = re.search(r'charset=["\']?([a-zA-Z0-9-]+)', html_content.lower())
            if match:
                encoding = match.group(1)
                if encoding.lower() != 'utf-8':
                    try:
                        with open(input_path, 'r', encoding=encoding) as f:
                            html_content = f.read()
                    except:
                        pass
        
        # 解析HTML
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # 移除script和style标签
        for script in soup(['script', 'style']):
            script.decompose()
        
        # 转换为Markdown
        content = convert_element(soup)
        
        # 清理内容
        content = clean_content(content)
        
        # 写入文件
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        logger.info(f"HTML转换完成: {input_path} -> {output_path}")
        return True
        
    except Exception as e:
        logger.error(f"HTML转换失败: {e}")
        return False


def convert_element(element):
    """递归转换HTML元素为Markdown"""
    from bs4 import BeautifulSoup, NavigableString, Tag
    
    if isinstance(element, NavigableString):
        return str(element)
    
    if not isinstance(element, Tag):
        return ""
    
    tag_name = element.name.lower()
    
    # 标题
    if tag_name in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
        level = int(tag_name[1])
        text = element.get_text(strip=True)
        return f"{'#' * level} {text}\n\n"
    
    # 段落
    elif tag_name == 'p':
        text = element.get_text(strip=True)
        return f"{text}\n\n"
    
    # 换行
    elif tag_name == 'br':
        return "\n"
    
    # 粗体
    elif tag_name in ['b', 'strong']:
        text = element.get_text(strip=True)
        return f"**{text}**"
    
    # 斜体
    elif tag_name in ['i', 'em']:
        text = element.get_text(strip=True)
        return f"*{text}*"
    
    # 代码
    elif tag_name == 'code':
        text = element.get_text()
        return f"`{text}`"
    
    # 代码块
    elif tag_name == 'pre':
        code = element.get_text()
        return f"```\n{code}\n```\n\n"
    
    # 链接
    elif tag_name == 'a':
        href = element.get('href', '')
        text = element.get_text(strip=True)
        if href and text:
            return f"[{text}]({href})"
        return text
    
    # 图片
    elif tag_name == 'img':
        src = element.get('src', '')
        alt = element.get('alt', '图片')
        return f"![{alt}]({src})"
    
    # 无序列表
    elif tag_name == 'ul':
        items = []
        for li in element.find_all('li', recursive=False):
            items.append(f"- {li.get_text(strip=True)}")
        return "\n".join(items) + "\n\n"
    
    # 有序列表
    elif tag_name == 'ol':
        items = []
        for i, li in enumerate(element.find_all('li', recursive=False), 1):
            items.append(f"{i}. {li.get_text(strip=True)}")
        return "\n".join(items) + "\n"
    
    # 表格
    elif tag_name == 'table':
        return convert_table(element)
    
    # 其他块级元素
    elif tag_name in ['div', 'section', 'article', 'main']:
        children = []
        for child in element.children:
            children.append(convert_element(child))
        return "".join(children)
    
    # 其他元素
    else:
        return element.get_text(strip=True)


def convert_table(table):
    """将HTML表格转换为Markdown表格"""
    from bs4 import BeautifulSoup
    
    rows = []
    
    # 获取所有行
    for tr in table.find_all('tr'):
        row = []
        for cell in tr.find_all(['th', 'td']):
            row.append(cell.get_text(strip=True))
        if row:
            rows.append(row)
    
    if not rows:
        return ""
    
    # 确保所有行有相同的列数
    max_cols = max(len(row) for row in rows)
    for row in rows:
        while len(row) < max_cols:
            row.append("")
    
    # 生成Markdown表格
    headers = rows[0]
    data_rows = rows[1:] if len(rows) > 1 else []
    
    header_line = "| " + " | ".join(headers) + " |"
    separator = "| " + " | ".join(["---"] * len(headers)) + " |"
    data_lines = ["| " + " | ".join(row) + " |" for row in data_rows]
    
    return "\n".join([header_line, separator] + data_lines) + "\n\n"


def clean_content(content: str) -> str:
    """清理转换后的内容"""
    # 移除多余空行
    content = re.sub(r'\n{3,}', '\n\n', content)
    
    # 移除HTML实体
    import html
    content = html.unescape(content)
    
    # 清理特殊字符
    content = content.replace('\xa0', ' ')
    
    return content.strip()


if __name__ == '__main__':
    import sys
    if len(sys.argv) != 3:
        print("用法: python html_to_md.py <输入HTML> <输出MD>")
        sys.exit(1)
    
    convert_html_to_md(sys.argv[1], sys.argv[2])
