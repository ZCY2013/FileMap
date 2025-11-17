"""Pytest配置和fixtures"""
import pytest
import tempfile
from pathlib import Path
from filemap.storage.sqlite_datastore import SQLiteDataStore
from filemap.core.models import File, Tag, Category


@pytest.fixture
def temp_dir():
    """临时目录"""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def temp_db(temp_dir):
    """临时数据库"""
    db_path = temp_dir / "test.db"
    datastore = SQLiteDataStore(db_path)
    yield datastore


@pytest.fixture
def sample_file(temp_dir):
    """示例文件"""
    file_path = temp_dir / "test.txt"
    file_path.write_text("Hello, World!")
    return File.from_path(str(file_path))


@pytest.fixture
def sample_tag():
    """示例标签"""
    return Tag(name="测试标签", category="topic", description="用于测试的标签")


@pytest.fixture
def sample_category():
    """示例分类"""
    return Category(name="test_category", description="测试分类", mutually_exclusive=False)
