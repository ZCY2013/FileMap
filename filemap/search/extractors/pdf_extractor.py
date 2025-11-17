"""PDF文本提取器"""
from typing import Dict, List, Optional
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class PDFExtractor:
    """PDF文本提取器"""

    @staticmethod
    def extract(file_path: str) -> Dict:
        """
        从PDF文件提取文本

        Args:
            file_path: PDF文件路径

        Returns:
            {
                'text': str,           # 全文
                'pages': List[str],    # 每页文本
                'page_count': int,     # 页数
                'metadata': dict,      # PDF元数据
                'success': bool,       # 是否成功
                'error': str          # 错误信息
            }
        """
        try:
            import PyPDF2

            result = {
                'text': '',
                'pages': [],
                'page_count': 0,
                'metadata': {},
                'success': False,
                'error': ''
            }

            with open(file_path, 'rb') as f:
                reader = PyPDF2.PdfReader(f)

                # 提取元数据
                try:
                    metadata = reader.metadata
                    if metadata:
                        result['metadata'] = {
                            'title': metadata.get('/Title', ''),
                            'author': metadata.get('/Author', ''),
                            'subject': metadata.get('/Subject', ''),
                            'creator': metadata.get('/Creator', ''),
                            'producer': metadata.get('/Producer', ''),
                            'creation_date': str(metadata.get('/CreationDate', '')),
                        }
                except Exception as e:
                    logger.warning(f"Failed to extract PDF metadata: {e}")

                # 提取文本
                pages = []
                for page_num, page in enumerate(reader.pages):
                    try:
                        text = page.extract_text()
                        pages.append(text)
                    except Exception as e:
                        logger.warning(f"Failed to extract text from page {page_num}: {e}")
                        pages.append('')

                result['pages'] = pages
                result['page_count'] = len(reader.pages)
                result['text'] = '\n'.join(pages)
                result['success'] = True

            return result

        except ImportError:
            return {
                'text': '',
                'pages': [],
                'page_count': 0,
                'metadata': {},
                'success': False,
                'error': 'PyPDF2 not installed. Install with: pip install PyPDF2'
            }
        except FileNotFoundError:
            return {
                'text': '',
                'pages': [],
                'page_count': 0,
                'metadata': {},
                'success': False,
                'error': f'File not found: {file_path}'
            }
        except Exception as e:
            logger.error(f"Error extracting PDF: {e}")
            return {
                'text': '',
                'pages': [],
                'page_count': 0,
                'metadata': {},
                'success': False,
                'error': str(e)
            }

    @staticmethod
    def can_extract(file_path: str) -> bool:
        """检查是否可以提取该文件"""
        path = Path(file_path)
        return path.suffix.lower() == '.pdf'


class TextExtractor:
    """纯文本提取器"""

    @staticmethod
    def extract(file_path: str) -> Dict:
        """从文本文件提取内容"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                text = f.read()

            return {
                'text': text,
                'pages': [text],  # 文本文件没有分页
                'page_count': 1,
                'metadata': {},
                'success': True,
                'error': ''
            }
        except UnicodeDecodeError:
            # 尝试其他编码
            try:
                with open(file_path, 'r', encoding='gbk') as f:
                    text = f.read()
                return {
                    'text': text,
                    'pages': [text],
                    'page_count': 1,
                    'metadata': {},
                    'success': True,
                    'error': ''
                }
            except Exception as e:
                return {
                    'text': '',
                    'pages': [],
                    'page_count': 0,
                    'metadata': {},
                    'success': False,
                    'error': f'Encoding error: {e}'
                }
        except Exception as e:
            return {
                'text': '',
                'pages': [],
                'page_count': 0,
                'metadata': {},
                'success': False,
                'error': str(e)
            }

    @staticmethod
    def can_extract(file_path: str) -> bool:
        """检查是否可以提取该文件"""
        path = Path(file_path)
        text_extensions = {'.txt', '.md', '.markdown', '.rst', '.log', '.csv'}
        return path.suffix.lower() in text_extensions


class ExtractorFactory:
    """提取器工厂"""

    _extractors = [
        PDFExtractor,
        TextExtractor,
    ]

    @classmethod
    def get_extractor(cls, file_path: str):
        """获取适合的提取器"""
        for extractor_class in cls._extractors:
            if extractor_class.can_extract(file_path):
                return extractor_class
        return None

    @classmethod
    def extract(cls, file_path: str) -> Optional[Dict]:
        """自动选择提取器并提取文本"""
        extractor = cls.get_extractor(file_path)
        if extractor:
            return extractor.extract(file_path)
        return None
