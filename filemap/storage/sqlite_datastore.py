"""SQLite 数据存储层"""
import sqlite3
from pathlib import Path
from typing import List, Dict, Optional, Any
from datetime import datetime
import logging
from contextlib import contextmanager

from filemap.core.models import File, Tag, Category

logger = logging.getLogger(__name__)


class SQLiteDataStore:
    """基于 SQLite 的数据存储"""

    def __init__(self, db_path: Path):
        """
        初始化数据存储

        Args:
            db_path: 数据库文件路径
        """
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        # 初始化数据库
        self._init_db()

        # 创建默认分类
        self._create_default_categories()

    def _init_db(self):
        """初始化数据库"""
        schema_file = Path(__file__).parent / "schema.sql"

        with self._get_connection() as conn:
            # 启用外键约束
            conn.execute("PRAGMA foreign_keys = ON")

            # 执行 schema
            with open(schema_file, 'r', encoding='utf-8') as f:
                conn.executescript(f.read())

            conn.commit()
            logger.info(f"Database initialized at {self.db_path}")

    @contextmanager
    def _get_connection(self):
        """获取数据库连接（上下文管理器）"""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row  # 支持字典式访问
        try:
            yield conn
        finally:
            conn.close()

    def _create_default_categories(self):
        """创建默认分类"""
        default_categories = [
            Category(name="uncategorized", description="未分类标签", mutually_exclusive=False),
            Category(name="type", description="文件类型", mutually_exclusive=True),
            Category(name="status", description="文件状态", mutually_exclusive=True),
            Category(name="priority", description="优先级", mutually_exclusive=True),
            Category(name="topic", description="主题标签", mutually_exclusive=False),
        ]

        for category in default_categories:
            self.add_category(category)

    # ==================== 文件操作 ====================

    def add_file(self, file: File) -> bool:
        """添加文件"""
        try:
            with self._get_connection() as conn:
                # 使用 file.modified_at 作为 updated_at
                updated_at = file.modified_at or file.created_at or datetime.now()
                created_at = file.created_at or file.added_at or datetime.now()

                conn.execute("""
                    INSERT INTO files (file_id, name, path, managed, mime_type, size, hash,
                                      created_at, updated_at, indexed, indexed_at, deleted)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    file.file_id, file.name, file.path, file.managed, file.mime_type,
                    file.size, file.hash,
                    created_at.isoformat() if isinstance(created_at, datetime) else created_at,
                    updated_at.isoformat() if isinstance(updated_at, datetime) else updated_at,
                    False, None, False
                ))

                # 添加标签关联
                if file.tags:
                    for tag_name in file.tags:
                        tag = self.get_tag_by_name(tag_name)
                        if tag:
                            conn.execute("""
                                INSERT OR IGNORE INTO file_tags (file_id, tag_id, added_at)
                                VALUES (?, ?, ?)
                            """, (file.file_id, tag.tag_id, datetime.now()))

                conn.commit()
                logger.info(f"Added file: {file.name}")
                return True
        except sqlite3.IntegrityError as e:
            logger.error(f"File already exists: {file.path}")
            return False
        except Exception as e:
            logger.error(f"Error adding file: {e}")
            return False

    def get_file(self, file_id: str) -> Optional[File]:
        """获取文件"""
        with self._get_connection() as conn:
            cursor = conn.execute("""
                SELECT * FROM files WHERE file_id = ? AND deleted = 0
            """, (file_id,))
            row = cursor.fetchone()

            if not row:
                return None

            return self._row_to_file(row, conn)

    def get_file_by_path(self, path: str) -> Optional[File]:
        """通过路径获取文件"""
        with self._get_connection() as conn:
            cursor = conn.execute("""
                SELECT * FROM files WHERE path = ? AND deleted = 0
            """, (path,))
            row = cursor.fetchone()

            if not row:
                return None

            return self._row_to_file(row, conn)

    def list_files(self, filters: Optional[Dict[str, Any]] = None) -> List[File]:
        """列出文件"""
        query = "SELECT * FROM files WHERE deleted = 0"
        params = []

        if filters:
            if 'managed' in filters:
                query += " AND managed = ?"
                params.append(filters['managed'])

            if 'mime_type' in filters:
                query += " AND mime_type LIKE ?"
                params.append(f"%{filters['mime_type']}%")

        query += " ORDER BY created_at DESC"

        with self._get_connection() as conn:
            cursor = conn.execute(query, params)
            rows = cursor.fetchall()

            return [self._row_to_file(row, conn) for row in rows]

    def update_file(self, file: File) -> bool:
        """更新文件"""
        try:
            with self._get_connection() as conn:
                conn.execute("""
                    UPDATE files
                    SET name = ?, path = ?, mime_type = ?, size = ?, hash = ?, updated_at = ?
                    WHERE file_id = ?
                """, (
                    file.name, file.path, file.mime_type, file.size, file.hash,
                    datetime.now(), file.file_id
                ))
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Error updating file: {e}")
            return False

    def remove_file(self, file_id: str) -> bool:
        """删除文件（软删除）"""
        try:
            with self._get_connection() as conn:
                conn.execute("""
                    UPDATE files SET deleted = 1 WHERE file_id = ?
                """, (file_id,))
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Error removing file: {e}")
            return False

    def _row_to_file(self, row: sqlite3.Row, conn: sqlite3.Connection) -> File:
        """将数据库行转换为 File 对象"""
        # 获取文件的标签
        cursor = conn.execute("""
            SELECT t.name FROM tags t
            JOIN file_tags ft ON t.tag_id = ft.tag_id
            WHERE ft.file_id = ?
        """, (row['file_id'],))
        tags = [r['name'] for r in cursor.fetchall()]

        # 时间字段转换
        created_at = datetime.fromisoformat(row['created_at']) if row['created_at'] else None
        updated_at = datetime.fromisoformat(row['updated_at']) if row['updated_at'] else None

        return File(
            file_id=row['file_id'],
            name=row['name'],
            path=row['path'],
            managed=bool(row['managed']),
            mime_type=row['mime_type'],
            size=row['size'],
            hash=row['hash'],
            created_at=created_at,
            modified_at=updated_at,  # 数据库用 updated_at，模型用 modified_at
            added_at=created_at or datetime.now(),  # 使用 created_at 作为 added_at
            tags=tags
        )

    # ==================== 标签操作 ====================

    def add_tag(self, tag: Tag) -> bool:
        """添加标签"""
        try:
            with self._get_connection() as conn:
                # Tag 模型使用 category 而不是 category_id
                category_id = tag.category if hasattr(tag, 'category') else None
                conn.execute("""
                    INSERT INTO tags (tag_id, name, category_id, color, description, created_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    tag.tag_id, tag.name, category_id, tag.color,
                    tag.description, tag.created_at.isoformat() if isinstance(tag.created_at, datetime) else tag.created_at
                ))
                conn.commit()
                logger.info(f"Added tag: {tag.name}")
                return True
        except sqlite3.IntegrityError:
            logger.error(f"Tag already exists: {tag.name}")
            return False
        except Exception as e:
            logger.error(f"Error adding tag: {e}")
            return False

    def get_tag(self, tag_id: str) -> Optional[Tag]:
        """获取标签"""
        with self._get_connection() as conn:
            cursor = conn.execute("SELECT * FROM tags WHERE tag_id = ?", (tag_id,))
            row = cursor.fetchone()

            if not row:
                return None

            return self._row_to_tag(row, conn)

    def get_tag_by_name(self, name: str) -> Optional[Tag]:
        """通过名称获取标签"""
        with self._get_connection() as conn:
            cursor = conn.execute("SELECT * FROM tags WHERE name = ?", (name,))
            row = cursor.fetchone()

            if not row:
                return None

            return self._row_to_tag(row, conn)

    def list_tags(self, category_id: Optional[str] = None) -> List[Tag]:
        """列出标签"""
        query = "SELECT * FROM tags"
        params = []

        if category_id:
            query += " WHERE category_id = ?"
            params.append(category_id)

        query += " ORDER BY name"

        with self._get_connection() as conn:
            cursor = conn.execute(query, params)
            rows = cursor.fetchall()

            return [self._row_to_tag(row, conn) for row in rows]

    def remove_tag(self, tag_id: str) -> bool:
        """删除标签"""
        try:
            with self._get_connection() as conn:
                conn.execute("DELETE FROM tags WHERE tag_id = ?", (tag_id,))
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Error removing tag: {e}")
            return False

    def _row_to_tag(self, row: sqlite3.Row, conn: Optional[sqlite3.Connection] = None) -> Tag:
        """将数据库行转换为 Tag 对象"""
        # 计算使用次数
        usage_count = 0
        if conn:
            cursor = conn.execute("""
                SELECT COUNT(*) as count FROM file_tags WHERE tag_id = ?
            """, (row['tag_id'],))
            usage_count = cursor.fetchone()['count']

        return Tag(
            tag_id=row['tag_id'],
            name=row['name'],
            category=row['category_id'],  # 兼容旧字段名
            color=row['color'],
            description=row['description'],
            created_at=row['created_at'],
            usage_count=usage_count
        )

    # ==================== 分类操作 ====================

    def add_category(self, category: Category) -> bool:
        """添加分类"""
        try:
            with self._get_connection() as conn:
                conn.execute("""
                    INSERT OR IGNORE INTO categories (category_id, name, description, exclusive, created_at)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    category.category_id, category.name, category.description,
                    category.mutually_exclusive, category.created_at
                ))
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Error adding category: {e}")
            return False

    def get_category(self, category_id: str) -> Optional[Category]:
        """获取分类"""
        with self._get_connection() as conn:
            cursor = conn.execute("SELECT * FROM categories WHERE category_id = ?", (category_id,))
            row = cursor.fetchone()

            if not row:
                return None

            return self._row_to_category(row)

    def get_category_by_name(self, name: str) -> Optional[Category]:
        """通过名称获取分类"""
        with self._get_connection() as conn:
            cursor = conn.execute("SELECT * FROM categories WHERE name = ?", (name,))
            row = cursor.fetchone()

            if not row:
                return None

            return self._row_to_category(row)

    def list_categories(self) -> List[Category]:
        """列出所有分类"""
        with self._get_connection() as conn:
            cursor = conn.execute("SELECT * FROM categories ORDER BY name")
            rows = cursor.fetchall()

            return [self._row_to_category(row) for row in rows]

    def remove_category(self, category_id: str) -> bool:
        """删除分类"""
        try:
            with self._get_connection() as conn:
                conn.execute("DELETE FROM categories WHERE category_id = ?", (category_id,))
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Error removing category: {e}")
            return False

    def _row_to_category(self, row: sqlite3.Row) -> Category:
        """将数据库行转换为 Category 对象"""
        return Category(
            category_id=row['category_id'],
            name=row['name'],
            description=row['description'],
            mutually_exclusive=bool(row['exclusive']),  # 数据库用 exclusive，模型用 mutually_exclusive
            created_at=row['created_at']
        )

    # ==================== 文件-标签关联操作 ====================

    def add_tag_to_file(self, file_id: str, tag_id: str) -> bool:
        """为文件添加标签"""
        try:
            with self._get_connection() as conn:
                # 检查分类互斥性
                tag = self.get_tag(tag_id)
                if tag and tag.category:  # tag.category 是 category_id
                    category = self.get_category(tag.category)
                    if category and category.mutually_exclusive:
                        # 删除同分类的其他标签
                        conn.execute("""
                            DELETE FROM file_tags
                            WHERE file_id = ? AND tag_id IN (
                                SELECT tag_id FROM tags WHERE category_id = ?
                            )
                        """, (file_id, tag.category))

                # 添加新标签
                conn.execute("""
                    INSERT OR IGNORE INTO file_tags (file_id, tag_id, added_at)
                    VALUES (?, ?, ?)
                """, (file_id, tag_id, datetime.now()))

                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Error adding tag to file: {e}")
            return False

    def remove_tag_from_file(self, file_id: str, tag_id: str) -> bool:
        """从文件移除标签"""
        try:
            with self._get_connection() as conn:
                conn.execute("""
                    DELETE FROM file_tags WHERE file_id = ? AND tag_id = ?
                """, (file_id, tag_id))
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Error removing tag from file: {e}")
            return False

    def get_files_by_tag(self, tag_id: str) -> List[File]:
        """获取具有指定标签的所有文件"""
        with self._get_connection() as conn:
            cursor = conn.execute("""
                SELECT f.* FROM files f
                JOIN file_tags ft ON f.file_id = ft.file_id
                WHERE ft.tag_id = ? AND f.deleted = 0
                ORDER BY f.created_at DESC
            """, (tag_id,))
            rows = cursor.fetchall()

            return [self._row_to_file(row, conn) for row in rows]

    def get_files_by_tags(self, tag_ids: List[str], match_all: bool = True) -> List[File]:
        """
        获取具有指定标签的文件

        Args:
            tag_ids: 标签ID列表
            match_all: True=匹配所有标签(AND), False=匹配任一标签(OR)
        """
        if not tag_ids:
            return []

        with self._get_connection() as conn:
            if match_all:
                # 必须包含所有标签
                placeholders = ','.join('?' * len(tag_ids))
                cursor = conn.execute(f"""
                    SELECT f.* FROM files f
                    WHERE f.deleted = 0 AND f.file_id IN (
                        SELECT file_id FROM file_tags
                        WHERE tag_id IN ({placeholders})
                        GROUP BY file_id
                        HAVING COUNT(DISTINCT tag_id) = ?
                    )
                    ORDER BY f.created_at DESC
                """, (*tag_ids, len(tag_ids)))
            else:
                # 包含任一标签
                placeholders = ','.join('?' * len(tag_ids))
                cursor = conn.execute(f"""
                    SELECT DISTINCT f.* FROM files f
                    JOIN file_tags ft ON f.file_id = ft.file_id
                    WHERE ft.tag_id IN ({placeholders}) AND f.deleted = 0
                    ORDER BY f.created_at DESC
                """, tag_ids)

            rows = cursor.fetchall()
            return [self._row_to_file(row, conn) for row in rows]

    # ==================== 统计信息 ====================

    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        with self._get_connection() as conn:
            stats = {}

            # 文件统计
            cursor = conn.execute("SELECT COUNT(*) as count FROM files WHERE deleted = 0")
            stats['total_files'] = cursor.fetchone()['count']

            cursor = conn.execute("SELECT COUNT(*) as count FROM files WHERE managed = 1 AND deleted = 0")
            stats['managed_files'] = cursor.fetchone()['count']

            cursor = conn.execute("SELECT COUNT(*) as count FROM files WHERE indexed = 1 AND deleted = 0")
            stats['indexed_files'] = cursor.fetchone()['count']

            cursor = conn.execute("SELECT SUM(size) as total FROM files WHERE deleted = 0")
            stats['total_size'] = cursor.fetchone()['total'] or 0

            # 标签统计
            cursor = conn.execute("SELECT COUNT(*) as count FROM tags")
            stats['total_tags'] = cursor.fetchone()['count']

            # 分类统计
            cursor = conn.execute("SELECT COUNT(*) as count FROM categories")
            stats['total_categories'] = cursor.fetchone()['count']

            return stats

    # ==================== 索引状态管理 ====================

    def mark_indexed(self, file_id: str) -> bool:
        """标记文件已索引"""
        try:
            with self._get_connection() as conn:
                conn.execute("""
                    UPDATE files SET indexed = 1, indexed_at = ? WHERE file_id = ?
                """, (datetime.now(), file_id))
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Error marking file as indexed: {e}")
            return False

    def is_indexed(self, file_id: str) -> bool:
        """检查文件是否已索引"""
        with self._get_connection() as conn:
            cursor = conn.execute("""
                SELECT indexed FROM files WHERE file_id = ?
            """, (file_id,))
            row = cursor.fetchone()
            return bool(row['indexed']) if row else False

    def get_indexed_time(self, file_id: str) -> Optional[datetime]:
        """获取文件索引时间"""
        with self._get_connection() as conn:
            cursor = conn.execute("""
                SELECT indexed_at FROM files WHERE file_id = ?
            """, (file_id,))
            row = cursor.fetchone()
            if row and row['indexed_at']:
                return datetime.fromisoformat(row['indexed_at'])
            return None

    # ==================== 兼容性属性 ====================

    @property
    def files(self) -> Dict[str, File]:
        """
        兼容旧版 DataStore 接口
        返回所有文件的字典（file_id -> File）
        """
        all_files = self.list_files()
        return {f.file_id: f for f in all_files}

    @property
    def tags(self) -> Dict[str, Tag]:
        """
        兼容旧版 DataStore 接口
        返回所有标签的字典（tag_id -> Tag）
        """
        all_tags = self.list_tags()
        return {t.tag_id: t for t in all_tags}

    @property
    def categories(self) -> Dict[str, Category]:
        """
        兼容旧版 DataStore 接口
        返回所有分类的字典（category_id -> Category）
        """
        all_categories = self.list_categories()
        return {c.category_id: c for c in all_categories}
