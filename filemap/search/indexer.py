"""全文索引管理器"""
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime
import logging

from whoosh import index
from whoosh.fields import Schema, TEXT, ID, DATETIME, NUMERIC, BOOLEAN
from whoosh.qparser import QueryParser, MultifieldParser
from whoosh.highlight import UppercaseFormatter, ContextFragmenter

from filemap.search.analyzer import ChineseAnalyzer
from filemap.search.extractors.pdf_extractor import ExtractorFactory
from filemap.core.models import File

logger = logging.getLogger(__name__)


class ContentIndexer:
    """全文索引管理器"""

    def __init__(self, index_dir: Path):
        """
        初始化索引管理器

        Args:
            index_dir: 索引目录路径
        """
        self.index_dir = Path(index_dir)
        self.index_dir.mkdir(parents=True, exist_ok=True)

        # 定义索引Schema
        self.schema = Schema(
            file_id=ID(stored=True, unique=True),
            filename=TEXT(stored=True, analyzer=ChineseAnalyzer()),
            content=TEXT(stored=True, analyzer=ChineseAnalyzer()),
            path=TEXT(stored=True),
            mime_type=TEXT(stored=True),
            page_count=NUMERIC(stored=True),
            indexed_at=DATETIME(stored=True),
            file_size=NUMERIC(stored=True),
        )

        # 创建或打开索引
        if index.exists_in(str(self.index_dir)):
            self.ix = index.open_dir(str(self.index_dir))
        else:
            self.ix = index.create_in(str(self.index_dir), self.schema)

    def index_file(self, file: File) -> bool:
        """
        为文件创建索引

        Args:
            file: 文件对象

        Returns:
            是否成功
        """
        try:
            # 提取文本
            extracted = ExtractorFactory.extract(file.path)
            if not extracted or not extracted['success']:
                logger.warning(f"Failed to extract text from {file.name}: {extracted.get('error', 'Unknown error') if extracted else 'No extractor found'}")
                return False

            # 添加到索引
            writer = self.ix.writer()
            writer.update_document(
                file_id=file.file_id,
                filename=file.name,
                content=extracted['text'],
                path=file.path,
                mime_type=file.mime_type,
                page_count=extracted['page_count'],
                indexed_at=datetime.now(),
                file_size=file.size,
            )
            writer.commit()

            logger.info(f"Indexed file: {file.name}")
            return True

        except Exception as e:
            logger.error(f"Error indexing file {file.name}: {e}")
            return False

    def index_files(self, files: List[File], progress_callback=None) -> Dict[str, int]:
        """
        批量索引文件

        Args:
            files: 文件列表
            progress_callback: 进度回调函数 (current, total, filename)

        Returns:
            统计信息 {'success': int, 'failed': int, 'skipped': int}
        """
        stats = {'success': 0, 'failed': 0, 'skipped': 0}

        for idx, file in enumerate(files):
            if progress_callback:
                progress_callback(idx + 1, len(files), file.name)

            # 检查是否支持该文件类型
            if not ExtractorFactory.get_extractor(file.path):
                stats['skipped'] += 1
                logger.debug(f"Skipped unsupported file: {file.name}")
                continue

            # 索引文件
            if self.index_file(file):
                stats['success'] += 1
            else:
                stats['failed'] += 1

        return stats

    def search(self, query_string: str, limit: int = 20,
               fields: List[str] = None, highlight: bool = False) -> List[Dict]:
        """
        全文搜索

        Args:
            query_string: 查询字符串
            limit: 返回结果数量限制
            fields: 搜索字段列表，默认为 ['filename', 'content']
            highlight: 是否高亮显示

        Returns:
            搜索结果列表
        """
        if fields is None:
            fields = ['filename', 'content']

        try:
            with self.ix.searcher() as searcher:
                # 创建多字段查询解析器
                parser = MultifieldParser(fields, schema=self.schema)
                query = parser.parse(query_string)

                # 执行搜索
                results = searcher.search(query, limit=limit)
                results.fragmenter = ContextFragmenter(maxchars=200, surround=50)

                # 处理结果
                output = []
                for hit in results:
                    result = {
                        'file_id': hit['file_id'],
                        'filename': hit['filename'],
                        'path': hit['path'],
                        'mime_type': hit.get('mime_type', ''),
                        'page_count': hit.get('page_count', 0),
                        'score': hit.score,
                        'highlights': []
                    }

                    # 添加高亮
                    if highlight:
                        # 文件名高亮
                        if 'filename' in fields:
                            hl = hit.highlights("filename", top=1)
                            if hl:
                                result['highlights'].append(('filename', hl))

                        # 内容高亮
                        if 'content' in fields:
                            hl = hit.highlights("content", top=3)
                            if hl:
                                result['highlights'].append(('content', hl))

                    output.append(result)

                return output

        except Exception as e:
            logger.error(f"Search error: {e}")
            return []

    def remove_file(self, file_id: str) -> bool:
        """
        从索引中删除文件

        Args:
            file_id: 文件ID

        Returns:
            是否成功
        """
        try:
            writer = self.ix.writer()
            writer.delete_by_term('file_id', file_id)
            writer.commit()
            return True
        except Exception as e:
            logger.error(f"Error removing file from index: {e}")
            return False

    def is_indexed(self, file_id: str) -> bool:
        """检查文件是否已索引"""
        with self.ix.searcher() as searcher:
            parser = QueryParser("file_id", schema=self.schema)
            query = parser.parse(file_id)
            results = searcher.search(query, limit=1)
            return len(results) > 0

    def get_stats(self) -> Dict:
        """获取索引统计信息"""
        with self.ix.searcher() as searcher:
            return {
                'total_docs': searcher.doc_count_all(),
                'index_size': self._get_index_size(),
                'last_modified': self._get_last_modified(),
            }

    def _get_index_size(self) -> int:
        """获取索引大小（字节）"""
        total_size = 0
        for file in self.index_dir.glob('*'):
            if file.is_file():
                total_size += file.stat().st_size
        return total_size

    def _get_last_modified(self) -> Optional[datetime]:
        """获取索引最后修改时间"""
        files = list(self.index_dir.glob('*'))
        if not files:
            return None
        latest = max(files, key=lambda f: f.stat().st_mtime)
        return datetime.fromtimestamp(latest.stat().st_mtime)

    def optimize(self) -> None:
        """优化索引"""
        try:
            with self.ix.writer() as writer:
                writer.mergetype = index.CLEAR
                writer.commit(merge=True, optimize=True)
            logger.info("Index optimized")
        except Exception as e:
            logger.error(f"Error optimizing index: {e}")

    def clear(self) -> None:
        """清空索引"""
        try:
            writer = self.ix.writer()
            writer.commit(merge=True, optimize=True, mergetype=index.CLEAR)
            logger.info("Index cleared")
        except Exception as e:
            logger.error(f"Error clearing index: {e}")

    def get_indexed_time(self, file_id: str) -> Optional[datetime]:
        """获取文件的索引时间"""
        with self.ix.searcher() as searcher:
            parser = QueryParser("file_id", schema=self.schema)
            query = parser.parse(file_id)
            results = searcher.search(query, limit=1)

            if len(results) > 0:
                indexed_at = results[0].get('indexed_at')
                if indexed_at:
                    return indexed_at
            return None

    def needs_reindex(self, file: File) -> bool:
        """
        检查文件是否需要重新索引

        Args:
            file: 文件对象

        Returns:
            True 表示需要重新索引，False 表示不需要
        """
        # 检查文件是否已索引
        if not self.is_indexed(file.file_id):
            return True

        # 获取索引时间
        indexed_time = self.get_indexed_time(file.file_id)
        if not indexed_time:
            return True

        # 检查文件修改时间
        file_path = Path(file.path)
        if not file_path.exists():
            # 文件不存在，应该从索引中删除
            self.remove_file(file.file_id)
            return False

        file_mtime = datetime.fromtimestamp(file_path.stat().st_mtime)

        # 如果文件修改时间晚于索引时间，需要重新索引
        return file_mtime > indexed_time

    def update_index(self, files: List[File], force: bool = False, progress_callback=None) -> Dict[str, int]:
        """
        智能增量更新索引

        Args:
            files: 文件列表
            force: 是否强制重新索引所有文件
            progress_callback: 进度回调函数

        Returns:
            统计信息 {'success': int, 'failed': int, 'skipped': int}
        """
        stats = {'success': 0, 'failed': 0, 'skipped': 0}

        for idx, file in enumerate(files):
            if progress_callback:
                progress_callback(idx + 1, len(files), file.name)

            # 检查是否支持该文件类型
            if not ExtractorFactory.get_extractor(file.path):
                stats['skipped'] += 1
                logger.debug(f"Skipped unsupported file: {file.name}")
                continue

            # 检查是否需要重新索引
            if not force and not self.needs_reindex(file):
                stats['skipped'] += 1
                logger.debug(f"Skipped unchanged file: {file.name}")
                continue

            # 索引文件
            if self.index_file(file):
                stats['success'] += 1
            else:
                stats['failed'] += 1

        return stats
