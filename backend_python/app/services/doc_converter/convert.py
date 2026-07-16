"""
文档转换统一入口
将不同格式的文档转换为RAG可读的Markdown格式
"""
import os
import sys
import argparse
import logging
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

logger = logging.getLogger(__name__)

# 支持的文件格式
SUPPORTED_FORMATS = {
    '.pdf': 'PDF文档',
    '.docx': 'Word文档',
    '.doc': 'Word旧格式',
    '.html': 'HTML网页',
    '.htm': 'HTML网页',
    '.txt': '纯文本',
    '.md': 'Markdown'
}


def get_converter(format_ext):
    """根据文件格式获取对应的转换器"""
    if format_ext == '.pdf':
        from .scripts.pdf_to_md import convert_pdf_to_md
        return convert_pdf_to_md
    elif format_ext in ['.docx', '.doc']:
        from .scripts.docx_to_md import convert_docx_to_md
        return convert_docx_to_md
    elif format_ext in ['.html', '.htm']:
        from .scripts.html_to_md import convert_html_to_md
        return convert_html_to_md
    elif format_ext == '.txt':
        from .scripts.txt_to_md import convert_txt_to_md
        return convert_txt_to_md
    elif format_ext == '.md':
        return None  # 无需转换
    else:
        return None


def convert_file(input_path, output_dir):
    """转换单个文件"""
    input_path = Path(input_path)
    output_dir = Path(output_dir)
    
    if not input_path.exists():
        logger.error(f"文件不存在: {input_path}")
        return False
    
    format_ext = input_path.suffix.lower()
    
    if format_ext not in SUPPORTED_FORMATS:
        logger.error(f"不支持的格式: {format_ext}")
        return False
    
    # Markdown文件直接复制
    if format_ext == '.md':
        output_path = output_dir / input_path.name
        output_dir.mkdir(parents=True, exist_ok=True)
        
        with open(input_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        logger.info(f"复制文件: {input_path} -> {output_path}")
        return True
    
    # 获取转换器
    converter = get_converter(format_ext)
    if converter is None:
        logger.error(f"无法获取转换器: {format_ext}")
        return False
    
    # 执行转换
    try:
        output_filename = input_path.stem + '.md'
        output_path = output_dir / output_filename
        
        logger.info(f"转换文件: {input_path} -> {output_path}")
        converter(str(input_path), str(output_path))
        
        return True
    except Exception as e:
        logger.error(f"转换失败: {input_path}, 错误: {e}")
        return False


def convert_directory(input_dir, output_dir):
    """批量转换目录下的所有文件"""
    input_dir = Path(input_dir)
    output_dir = Path(output_dir)
    
    if not input_dir.exists():
        logger.error(f"目录不存在: {input_dir}")
        return False
    
    success_count = 0
    fail_count = 0
    
    for file_path in input_dir.rglob('*'):
        if file_path.is_file():
            format_ext = file_path.suffix.lower()
            if format_ext in SUPPORTED_FORMATS:
                if convert_file(file_path, output_dir):
                    success_count += 1
                else:
                    fail_count += 1
    
    logger.info(f"转换完成: 成功 {success_count} 个, 失败 {fail_count} 个")
    return fail_count == 0


def main():
    parser = argparse.ArgumentParser(description='文档转换工具')
    parser.add_argument('--input', '-i', required=True, help='输入文件或目录')
    parser.add_argument('--output', '-o', required=True, help='输出目录')
    parser.add_argument('--format', '-f', default='md', help='输出格式（默认md）')
    
    args = parser.parse_args()
    
    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    input_path = Path(args.input)
    output_dir = Path(args.output)
    
    if input_path.is_file():
        success = convert_file(input_path, output_dir)
    elif input_path.is_dir():
        success = convert_directory(input_path, output_dir)
    else:
        logger.error(f"路径不存在: {input_path}")
        success = False
    
    if success:
        print("转换完成!")
        sys.exit(0)
    else:
        print("转换过程中有错误，请查看日志!")
        sys.exit(1)


if __name__ == '__main__':
    main()
