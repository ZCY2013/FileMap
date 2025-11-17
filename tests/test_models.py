"""核心模型测试"""
import pytest
from filemap.core.models import File, Tag, Category
from pathlib import Path


class TestFile:
    """File 模型测试"""

    def test_from_path(self, sample_file):
        """测试从路径创建文件"""
        assert sample_file.name == "test.txt"
        assert sample_file.size > 0
        assert sample_file.hash is not None

    def test_add_tag(self):
        """测试添加标签"""
        file = File(name="test.txt")
        file.add_tag("tag1")
        assert "tag1" in file.tags

    def test_remove_tag(self):
        """测试移除标签"""
        file = File(name="test.txt", tags=["tag1", "tag2"])
        file.remove_tag("tag1")
        assert "tag1" not in file.tags
        assert "tag2" in file.tags


class TestTag:
    """Tag 模型测试"""

    def test_create_tag(self):
        """测试创建标签"""
        tag = Tag(name="测试", category="topic")
        assert tag.name == "测试"
        assert tag.category == "topic"

    def test_add_related_tag(self):
        """测试添加相关标签"""
        tag = Tag(name="tag1")
        tag.add_related_tag("tag2", 0.8)
        assert len(tag.related_tags) == 1
        assert tag.related_tags[0]["tag_id"] == "tag2"


class TestCategory:
    """Category 模型测试"""

    def test_create_category(self):
        """测试创建分类"""
        cat = Category(name="类型", mutually_exclusive=True)
        assert cat.name == "类型"
        assert cat.mutually_exclusive is True
