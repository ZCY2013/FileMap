"""数据存储管理"""
import json
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime
import shutil

from filemap.core.models import File, Tag, Category


class DataStore:
    """数据存储管理类"""

    def __init__(self, data_dir: Path):
        """
        初始化数据存储

        Args:
            data_dir: 数据目录路径
        """
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)

        # 数据文件路径
        self.files_path = self.data_dir / "files.json"
        self.tags_path = self.data_dir / "tags.json"
        self.categories_path = self.data_dir / "categories.json"
        self.graph_path = self.data_dir / "graph.json"

        # 内存中的数据
        self.files: Dict[str, File] = {}
        self.tags: Dict[str, Tag] = {}
        self.categories: Dict[str, Category] = {}

        # 加载数据
        self._load_all()

    def _load_all(self) -> None:
        """加载所有数据"""
        self._load_files()
        self._load_tags()
        self._load_categories()

    def _load_files(self) -> None:
        """加载文件数据"""
        if self.files_path.exists():
            with open(self.files_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                self.files = {fid: File.from_dict(fdata) for fid, fdata in data.items()}
        else:
            self.files = {}

    def _load_tags(self) -> None:
        """加载标签数据"""
        if self.tags_path.exists():
            with open(self.tags_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                self.tags = {tid: Tag.from_dict(tdata) for tid, tdata in data.items()}
        else:
            self.tags = {}

    def _load_categories(self) -> None:
        """加载类别数据"""
        if self.categories_path.exists():
            with open(self.categories_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                self.categories = {
                    cid: Category.from_dict(cdata) for cid, cdata in data.items()
                }
        else:
            # 创建默认的未分类类别
            self.categories = {}
            self._create_default_categories()

    def _create_default_categories(self) -> None:
        """创建默认类别"""
        default_categories = [
            Category(
                name="uncategorized",
                description="未分类的标签",
                color="#CCCCCC",
                icon="📌",
                priority=999,
            ),
            Category(
                name="type",
                description="文件类型",
                mutually_exclusive=True,
                color="#4A90E2",
                icon="📁",
                priority=1,
            ),
            Category(
                name="status",
                description="状态标记",
                mutually_exclusive=True,
                color="#7ED321",
                icon="✓",
                priority=2,
            ),
            Category(
                name="priority",
                description="优先级",
                mutually_exclusive=True,
                color="#F5A623",
                icon="⭐",
                priority=3,
            ),
            Category(
                name="topic",
                description="主题分类",
                mutually_exclusive=False,
                color="#BD10E0",
                icon="🏷️",
                priority=4,
            ),
        ]

        for cat in default_categories:
            self.categories[cat.category_id] = cat

        self.save_categories()

    def save_files(self) -> None:
        """保存文件数据"""
        data = {fid: file.to_dict() for fid, file in self.files.items()}
        self._save_json(self.files_path, data)

    def save_tags(self) -> None:
        """保存标签数据"""
        data = {tid: tag.to_dict() for tid, tag in self.tags.items()}
        self._save_json(self.tags_path, data)

    def save_categories(self) -> None:
        """保存类别数据"""
        data = {cid: cat.to_dict() for cid, cat in self.categories.items()}
        self._save_json(self.categories_path, data)

    def save_all(self) -> None:
        """保存所有数据"""
        self.save_files()
        self.save_tags()
        self.save_categories()

    def _save_json(self, file_path: Path, data: Dict) -> None:
        """保存JSON文件"""
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    # ==================== 文件操作 ====================

    def add_file(self, file: File) -> None:
        """添加文件"""
        self.files[file.file_id] = file
        self.save_files()

    def get_file(self, file_id: str) -> Optional[File]:
        """获取文件"""
        return self.files.get(file_id)

    def get_file_by_path(self, path: str) -> Optional[File]:
        """通过路径获取文件"""
        for file in self.files.values():
            if file.path == path:
                return file
        return None

    def remove_file(self, file_id: str) -> bool:
        """移除文件"""
        if file_id in self.files:
            del self.files[file_id]
            self.save_files()
            return True
        return False

    def update_file(self, file: File) -> None:
        """更新文件"""
        self.files[file.file_id] = file
        self.save_files()

    def list_files(self, tag_ids: Optional[List[str]] = None) -> List[File]:
        """列出文件"""
        files = list(self.files.values())

        if tag_ids:
            # 过滤包含指定标签的文件
            files = [f for f in files if any(tid in f.tags for tid in tag_ids)]

        return files

    # ==================== 标签操作 ====================

    def add_tag(self, tag: Tag) -> None:
        """添加标签"""
        self.tags[tag.tag_id] = tag
        self.save_tags()

    def get_tag(self, tag_id: str) -> Optional[Tag]:
        """获取标签"""
        return self.tags.get(tag_id)

    def get_tag_by_name(self, name: str) -> Optional[Tag]:
        """通过名称获取标签"""
        for tag in self.tags.values():
            if tag.name == name or name in tag.aliases:
                return tag
        return None

    def remove_tag(self, tag_id: str) -> bool:
        """移除标签"""
        if tag_id in self.tags:
            # 从所有文件中移除此标签
            for file in self.files.values():
                if tag_id in file.tags:
                    file.remove_tag(tag_id)
            self.save_files()

            del self.tags[tag_id]
            self.save_tags()
            return True
        return False

    def update_tag(self, tag: Tag) -> None:
        """更新标签"""
        self.tags[tag.tag_id] = tag
        self.save_tags()

    def list_tags(self, category_id: Optional[str] = None) -> List[Tag]:
        """列出标签"""
        tags = list(self.tags.values())

        if category_id:
            tags = [t for t in tags if t.category == category_id]

        return tags

    # ==================== 类别操作 ====================

    def add_category(self, category: Category) -> None:
        """添加类别"""
        self.categories[category.category_id] = category
        self.save_categories()

    def get_category(self, category_id: str) -> Optional[Category]:
        """获取类别"""
        return self.categories.get(category_id)

    def get_category_by_name(self, name: str) -> Optional[Category]:
        """通过名称获取类别"""
        for cat in self.categories.values():
            if cat.name == name:
                return cat
        return None

    def remove_category(self, category_id: str) -> bool:
        """移除类别"""
        if category_id in self.categories:
            # 将此类别下的标签移动到未分类
            uncategorized = self.get_category_by_name("uncategorized")
            if uncategorized:
                for tag in self.tags.values():
                    if tag.category == category_id:
                        tag.category = uncategorized.category_id
                self.save_tags()

            del self.categories[category_id]
            self.save_categories()
            return True
        return False

    def update_category(self, category: Category) -> None:
        """更新类别"""
        self.categories[category.category_id] = category
        self.save_categories()

    def list_categories(self) -> List[Category]:
        """列出所有类别"""
        return sorted(self.categories.values(), key=lambda c: c.priority)

    # ==================== 备份和恢复 ====================

    def backup(self, backup_path: Path) -> None:
        """备份数据"""
        backup_path = Path(backup_path)
        backup_path.mkdir(parents=True, exist_ok=True)

        # 生成备份文件名（包含时间戳）
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = backup_path / f"filemap_backup_{timestamp}.zip"

        # 创建zip备份
        shutil.make_archive(
            str(backup_file.with_suffix("")), "zip", self.data_dir
        )

    def restore(self, backup_file: Path) -> None:
        """从备份恢复数据"""
        backup_file = Path(backup_file)
        if not backup_file.exists():
            raise FileNotFoundError(f"Backup file not found: {backup_file}")

        # 解压备份文件
        shutil.unpack_archive(str(backup_file), str(self.data_dir))

        # 重新加载数据
        self._load_all()

    # ==================== 统计信息 ====================

    def get_stats(self) -> Dict:
        """获取统计信息"""
        total_size = sum(f.size for f in self.files.values())

        # 统计各类别的文件数量
        category_dist = {}
        for file in self.files.values():
            for tag_id in file.tags:
                tag = self.tags.get(tag_id)
                if tag:
                    cat_name = self.categories.get(tag.category, None)
                    if cat_name:
                        cat_name = cat_name.name
                        category_dist[cat_name] = category_dist.get(cat_name, 0) + 1

        return {
            "total_files": len(self.files),
            "total_size": total_size,
            "total_tags": len(self.tags),
            "total_categories": len(self.categories),
            "category_distribution": category_dist,
            "files_with_tags": sum(1 for f in self.files.values() if f.tags),
            "files_without_tags": sum(1 for f in self.files.values() if not f.tags),
        }
