"""SQLiteDataStore 测试"""
import pytest
from filemap.storage.sqlite_datastore import SQLiteDataStore
from filemap.core.models import File, Tag, Category


class TestSQLiteDataStore:
    """SQLiteDataStore 测试类"""

    def test_init_creates_database(self, temp_db):
        """测试数据库初始化"""
        assert temp_db is not None
        stats = temp_db.get_stats()
        assert stats['total_categories'] >= 5  # 默认创建5个分类

    def test_add_and_get_file(self, temp_db, sample_file):
        """测试添加和获取文件"""
        assert temp_db.add_file(sample_file)
        retrieved = temp_db.get_file(sample_file.file_id)
        assert retrieved is not None
        assert retrieved.name == sample_file.name
        assert retrieved.path == sample_file.path

    def test_add_and_get_tag(self, temp_db, sample_tag):
        """测试添加和获取标签"""
        assert temp_db.add_tag(sample_tag)
        retrieved = temp_db.get_tag(sample_tag.tag_id)
        assert retrieved is not None
        assert retrieved.name == sample_tag.name

    def test_list_files(self, temp_db, sample_file):
        """测试列出文件"""
        temp_db.add_file(sample_file)
        files = temp_db.list_files()
        assert len(files) == 1
        assert files[0].file_id == sample_file.file_id

    def test_add_tag_to_file(self, temp_db, sample_file, sample_tag):
        """测试为文件添加标签"""
        temp_db.add_file(sample_file)
        temp_db.add_tag(sample_tag)
        assert temp_db.add_tag_to_file(sample_file.file_id, sample_tag.tag_id)

        # 验证标签已添加
        retrieved = temp_db.get_file(sample_file.file_id)
        assert sample_tag.name in retrieved.tags

    def test_remove_file(self, temp_db, sample_file):
        """测试删除文件（软删除）"""
        temp_db.add_file(sample_file)
        assert temp_db.remove_file(sample_file.file_id)

        # 验证文件已被软删除
        retrieved = temp_db.get_file(sample_file.file_id)
        assert retrieved is None

    def test_get_stats(self, temp_db, sample_file):
        """测试获取统计信息"""
        temp_db.add_file(sample_file)
        stats = temp_db.get_stats()
        assert stats['total_files'] == 1
        assert stats['total_size'] > 0
