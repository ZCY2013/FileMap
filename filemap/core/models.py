"""核心数据模型定义"""
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
import hashlib
import mimetypes
import uuid


@dataclass
class Category:
    """标签类别模型"""

    category_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    description: str = ""
    mutually_exclusive: bool = False
    color: str = "#CCCCCC"
    icon: str = ""
    priority: int = 0
    created_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            "category_id": self.category_id,
            "name": self.name,
            "description": self.description,
            "mutually_exclusive": self.mutually_exclusive,
            "color": self.color,
            "icon": self.icon,
            "priority": self.priority,
            "created_at": self.created_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "Category":
        """从字典创建对象"""
        data_copy = data.copy()
        if "created_at" in data_copy and isinstance(data_copy["created_at"], str):
            data_copy["created_at"] = datetime.fromisoformat(data_copy["created_at"])
        return cls(**data_copy)


@dataclass
class Tag:
    """标签模型"""

    tag_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    category: str = "uncategorized"  # category_id
    description: str = ""
    color: str = "#FFFFFF"
    aliases: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    usage_count: int = 0
    related_tags: List[Dict[str, float]] = field(default_factory=list)

    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            "tag_id": self.tag_id,
            "name": self.name,
            "category": self.category,
            "description": self.description,
            "color": self.color,
            "aliases": self.aliases,
            "created_at": self.created_at.isoformat(),
            "usage_count": self.usage_count,
            "related_tags": self.related_tags,
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "Tag":
        """从字典创建对象"""
        data_copy = data.copy()
        if "created_at" in data_copy and isinstance(data_copy["created_at"], str):
            data_copy["created_at"] = datetime.fromisoformat(data_copy["created_at"])
        return cls(**data_copy)

    def add_related_tag(self, tag_id: str, strength: float) -> None:
        """添加相关标签"""
        # 检查是否已存在
        for related in self.related_tags:
            if related["tag_id"] == tag_id:
                related["strength"] = strength
                return
        self.related_tags.append({"tag_id": tag_id, "strength": strength})


@dataclass
class File:
    """文件模型"""

    file_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    path: str = ""
    managed: bool = False  # True: 导入模式, False: 索引模式
    size: int = 0
    mime_type: str = ""
    hash: str = ""
    created_at: Optional[datetime] = None
    modified_at: Optional[datetime] = None
    added_at: datetime = field(default_factory=datetime.now)
    last_accessed: Optional[datetime] = None
    tags: List[str] = field(default_factory=list)  # tag_id列表
    metadata: Dict = field(default_factory=dict)
    notes: str = ""

    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            "file_id": self.file_id,
            "name": self.name,
            "path": self.path,
            "managed": self.managed,
            "size": self.size,
            "mime_type": self.mime_type,
            "hash": self.hash,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "modified_at": self.modified_at.isoformat() if self.modified_at else None,
            "added_at": self.added_at.isoformat(),
            "last_accessed": self.last_accessed.isoformat() if self.last_accessed else None,
            "tags": self.tags,
            "metadata": self.metadata,
            "notes": self.notes,
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "File":
        """从字典创建对象"""
        data_copy = data.copy()
        # 转换日期时间字段
        for field_name in ["created_at", "modified_at", "added_at", "last_accessed"]:
            if field_name in data_copy and data_copy[field_name]:
                if isinstance(data_copy[field_name], str):
                    data_copy[field_name] = datetime.fromisoformat(data_copy[field_name])
        return cls(**data_copy)

    @classmethod
    def from_path(cls, file_path: str, managed: bool = False) -> "File":
        """从文件路径创建File对象"""
        p = Path(file_path)
        if not p.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        stat = p.stat()
        mime_type, _ = mimetypes.guess_type(str(p))

        # 计算文件哈希
        file_hash = cls._calculate_hash(p)

        return cls(
            name=p.name,
            path=str(p.absolute()),
            managed=managed,
            size=stat.st_size,
            mime_type=mime_type or "application/octet-stream",
            hash=file_hash,
            created_at=datetime.fromtimestamp(stat.st_ctime),
            modified_at=datetime.fromtimestamp(stat.st_mtime),
        )

    @staticmethod
    def _calculate_hash(file_path: Path, chunk_size: int = 8192) -> str:
        """计算文件SHA256哈希值"""
        sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            while chunk := f.read(chunk_size):
                sha256.update(chunk)
        return sha256.hexdigest()

    def add_tag(self, tag_id: str) -> None:
        """添加标签"""
        if tag_id not in self.tags:
            self.tags.append(tag_id)

    def remove_tag(self, tag_id: str) -> None:
        """移除标签"""
        if tag_id in self.tags:
            self.tags.remove(tag_id)

    def has_tag(self, tag_id: str) -> bool:
        """检查是否有指定标签"""
        return tag_id in self.tags

    def update_from_filesystem(self) -> None:
        """从文件系统更新文件信息"""
        p = Path(self.path)
        if not p.exists():
            raise FileNotFoundError(f"File not found: {self.path}")

        stat = p.stat()
        self.name = p.name
        self.size = stat.st_size
        self.modified_at = datetime.fromtimestamp(stat.st_mtime)
        self.hash = self._calculate_hash(p)
