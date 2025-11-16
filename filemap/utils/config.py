"""配置管理"""
import yaml
from pathlib import Path
from typing import Any, Dict, Optional


class Config:
    """配置管理类"""

    DEFAULT_CONFIG = {
        "workspace": {
            "managed_dir": "~/.filemap/managed",
            "index_dirs": [],
        },
        "storage": {
            "data_dir": "~/.filemap/data",
            "backup_enabled": True,
            "backup_dir": "~/.filemap/backups",
        },
        "defaults": {
            "default_category": "uncategorized",
            "auto_tag": False,
        },
        "visualization": {
            "graph_engine": "text",
            "max_nodes": 100,
        },
    }

    def __init__(self, config_path: Optional[Path] = None):
        """
        初始化配置管理

        Args:
            config_path: 配置文件路径，默认为 ~/.filemap/config.yaml
        """
        if config_path is None:
            config_path = Path.home() / ".filemap" / "config.yaml"

        self.config_path = Path(config_path)
        self.config: Dict[str, Any] = {}
        self._load_config()

    def _load_config(self) -> None:
        """加载配置文件"""
        if self.config_path.exists():
            with open(self.config_path, "r", encoding="utf-8") as f:
                self.config = yaml.safe_load(f) or {}
            # 合并默认配置
            self.config = self._merge_config(self.DEFAULT_CONFIG, self.config)
        else:
            # 使用默认配置
            self.config = self.DEFAULT_CONFIG.copy()
            self._save_config()

    def _merge_config(self, default: Dict, custom: Dict) -> Dict:
        """合并配置，custom覆盖default"""
        result = default.copy()
        for key, value in custom.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._merge_config(result[key], value)
            else:
                result[key] = value
        return result

    def _save_config(self) -> None:
        """保存配置文件"""
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.config_path, "w", encoding="utf-8") as f:
            yaml.dump(self.config, f, default_flow_style=False, allow_unicode=True)

    def get(self, key: str, default: Any = None) -> Any:
        """
        获取配置值，支持点号分隔的键路径

        Args:
            key: 配置键，例如 "workspace.managed_dir"
            default: 默认值

        Returns:
            配置值
        """
        keys = key.split(".")
        value = self.config
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        return value

    def set(self, key: str, value: Any) -> None:
        """
        设置配置值

        Args:
            key: 配置键，例如 "workspace.managed_dir"
            value: 配置值
        """
        keys = key.split(".")
        config = self.config
        for k in keys[:-1]:
            if k not in config or not isinstance(config[k], dict):
                config[k] = {}
            config = config[k]
        config[keys[-1]] = value
        self._save_config()

    def get_data_dir(self) -> Path:
        """获取数据目录"""
        data_dir = self.get("storage.data_dir")
        return Path(data_dir).expanduser()

    def get_managed_dir(self) -> Path:
        """获取管理文件目录"""
        managed_dir = self.get("workspace.managed_dir")
        return Path(managed_dir).expanduser()

    def get_backup_dir(self) -> Path:
        """获取备份目录"""
        backup_dir = self.get("storage.backup_dir")
        return Path(backup_dir).expanduser()

    def get_index_dirs(self) -> list:
        """获取索引目录列表"""
        return self.get("workspace.index_dirs", [])

    def add_index_dir(self, directory: str) -> None:
        """添加索引目录"""
        index_dirs = self.get_index_dirs()
        if directory not in index_dirs:
            index_dirs.append(directory)
            self.set("workspace.index_dirs", index_dirs)

    def remove_index_dir(self, directory: str) -> None:
        """移除索引目录"""
        index_dirs = self.get_index_dirs()
        if directory in index_dirs:
            index_dirs.remove(directory)
            self.set("workspace.index_dirs", index_dirs)

    def reset(self) -> None:
        """重置为默认配置"""
        self.config = self.DEFAULT_CONFIG.copy()
        self._save_config()

    def list_all(self) -> Dict:
        """列出所有配置"""
        return self.config.copy()


# 全局配置实例
_config_instance: Optional[Config] = None


def get_config() -> Config:
    """获取全局配置实例"""
    global _config_instance
    if _config_instance is None:
        _config_instance = Config()
    return _config_instance


def init_config(config_path: Optional[Path] = None) -> Config:
    """
    初始化配置

    Args:
        config_path: 配置文件路径

    Returns:
        Config实例
    """
    global _config_instance
    _config_instance = Config(config_path)
    return _config_instance
