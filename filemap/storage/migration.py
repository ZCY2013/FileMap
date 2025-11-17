"""数据迁移工具：JSON to SQLite"""
import json
from pathlib import Path
from datetime import datetime
import logging
from typing import Dict, Any

from filemap.core.models import File, Tag, Category
from filemap.storage.sqlite_datastore import SQLiteDataStore

logger = logging.getLogger(__name__)


class DataMigration:
    """数据迁移工具"""

    @staticmethod
    def migrate_from_json(json_dir: Path, sqlite_db: Path) -> Dict[str, Any]:
        """
        从 JSON 迁移到 SQLite

        Args:
            json_dir: JSON 数据目录
            sqlite_db: SQLite 数据库路径

        Returns:
            迁移统计信息
        """
        stats = {
            'categories': 0,
            'tags': 0,
            'files': 0,
            'errors': []
        }

        logger.info("Starting migration from JSON to SQLite...")

        # 创建 SQLite 数据存储
        datastore = SQLiteDataStore(sqlite_db)

        # 读取 JSON 文件
        json_files_path = json_dir / "files.json"
        json_tags_path = json_dir / "tags.json"
        json_categories_path = json_dir / "categories.json"

        # 1. 迁移分类
        if json_categories_path.exists():
            try:
                with open(json_categories_path, 'r', encoding='utf-8') as f:
                    categories_data = json.load(f)

                for cat_id, cat_data in categories_data.items():
                    category = Category(
                        category_id=cat_id,
                        name=cat_data['name'],
                        description=cat_data.get('description', ''),
                        exclusive=cat_data.get('exclusive', False),
                        created_at=cat_data.get('created_at', datetime.now().isoformat())
                    )
                    if datastore.add_category(category):
                        stats['categories'] += 1
                    else:
                        # 分类已存在（默认分类），跳过
                        pass

                logger.info(f"Migrated {stats['categories']} categories")
            except Exception as e:
                error_msg = f"Error migrating categories: {e}"
                logger.error(error_msg)
                stats['errors'].append(error_msg)

        # 2. 迁移标签
        if json_tags_path.exists():
            try:
                with open(json_tags_path, 'r', encoding='utf-8') as f:
                    tags_data = json.load(f)

                for tag_id, tag_data in tags_data.items():
                    tag = Tag(
                        tag_id=tag_id,
                        name=tag_data['name'],
                        category_id=tag_data.get('category_id'),
                        color=tag_data.get('color'),
                        description=tag_data.get('description', ''),
                        created_at=tag_data.get('created_at', datetime.now().isoformat())
                    )
                    if datastore.add_tag(tag):
                        stats['tags'] += 1

                logger.info(f"Migrated {stats['tags']} tags")
            except Exception as e:
                error_msg = f"Error migrating tags: {e}"
                logger.error(error_msg)
                stats['errors'].append(error_msg)

        # 3. 迁移文件
        if json_files_path.exists():
            try:
                with open(json_files_path, 'r', encoding='utf-8') as f:
                    files_data = json.load(f)

                for file_id, file_data in files_data.items():
                    file = File(
                        file_id=file_id,
                        name=file_data['name'],
                        path=file_data['path'],
                        managed=file_data.get('managed', False),
                        mime_type=file_data.get('mime_type', ''),
                        size=file_data.get('size', 0),
                        hash=file_data.get('hash', ''),
                        created_at=file_data.get('created_at', datetime.now().isoformat()),
                        updated_at=file_data.get('updated_at', datetime.now().isoformat()),
                        tags=file_data.get('tags', [])
                    )
                    if datastore.add_file(file):
                        stats['files'] += 1
                    else:
                        error_msg = f"Failed to add file: {file.name}"
                        logger.warning(error_msg)
                        stats['errors'].append(error_msg)

                logger.info(f"Migrated {stats['files']} files")
            except Exception as e:
                error_msg = f"Error migrating files: {e}"
                logger.error(error_msg)
                stats['errors'].append(error_msg)

        logger.info("Migration completed!")
        logger.info(f"Summary: {stats['categories']} categories, {stats['tags']} tags, {stats['files']} files")

        if stats['errors']:
            logger.warning(f"Encountered {len(stats['errors'])} errors during migration")

        return stats

    @staticmethod
    def export_to_json(sqlite_db: Path, json_dir: Path) -> Dict[str, Any]:
        """
        从 SQLite 导出到 JSON（备份用）

        Args:
            sqlite_db: SQLite 数据库路径
            json_dir: JSON 导出目录

        Returns:
            导出统计信息
        """
        stats = {
            'categories': 0,
            'tags': 0,
            'files': 0,
            'errors': []
        }

        logger.info("Starting export from SQLite to JSON...")

        json_dir = Path(json_dir)
        json_dir.mkdir(parents=True, exist_ok=True)

        # 创建数据存储
        datastore = SQLiteDataStore(sqlite_db)

        try:
            # 导出分类
            categories = datastore.list_categories()
            categories_data = {}
            for cat in categories:
                categories_data[cat.category_id] = {
                    'name': cat.name,
                    'description': cat.description,
                    'exclusive': cat.exclusive,
                    'created_at': cat.created_at
                }

            with open(json_dir / "categories.json", 'w', encoding='utf-8') as f:
                json.dump(categories_data, f, ensure_ascii=False, indent=2)
            stats['categories'] = len(categories)

            # 导出标签
            tags = datastore.list_tags()
            tags_data = {}
            for tag in tags:
                tags_data[tag.tag_id] = {
                    'name': tag.name,
                    'category_id': tag.category_id,
                    'color': tag.color,
                    'description': tag.description,
                    'created_at': tag.created_at
                }

            with open(json_dir / "tags.json", 'w', encoding='utf-8') as f:
                json.dump(tags_data, f, ensure_ascii=False, indent=2)
            stats['tags'] = len(tags)

            # 导出文件
            files = datastore.list_files()
            files_data = {}
            for file in files:
                files_data[file.file_id] = {
                    'name': file.name,
                    'path': file.path,
                    'managed': file.managed,
                    'mime_type': file.mime_type,
                    'size': file.size,
                    'hash': file.hash,
                    'created_at': file.created_at,
                    'updated_at': file.updated_at,
                    'tags': file.tags
                }

            with open(json_dir / "files.json", 'w', encoding='utf-8') as f:
                json.dump(files_data, f, ensure_ascii=False, indent=2)
            stats['files'] = len(files)

            logger.info("Export completed!")
            logger.info(f"Summary: {stats['categories']} categories, {stats['tags']} tags, {stats['files']} files")

        except Exception as e:
            error_msg = f"Error during export: {e}"
            logger.error(error_msg)
            stats['errors'].append(error_msg)

        return stats
