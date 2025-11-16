"""搜索和过滤命令"""
import click
from rich.console import Console
from rich.table import Table
from typing import Optional, List
import re
from datetime import datetime

from filemap.core.models import File
from filemap.cli.main import pass_context, Context


console = Console()


@click.group(name="search")
def search_group():
    """搜索和过滤命令"""
    pass


@search_group.command(name="find")
@click.argument("keyword", required=False)
@click.option("--tags", help="标签查询表达式，例如: 'tag1 AND tag2' 或 'tag1 OR tag2'")
@click.option("--name", help="文件名模式（支持通配符）")
@click.option("--type", "mime_type", help="文件类型（MIME类型）")
@click.option("--size", help="文件大小条件，例如: '>1MB', '<100KB'")
@click.option("--date", help="日期范围，例如: '2024-01-01..2024-12-31'")
@click.option("--format", "output_format", type=click.Choice(["table", "simple", "json"]), default="table")
@pass_context
def search_files(
    ctx: Context,
    keyword: Optional[str],
    tags: Optional[str],
    name: Optional[str],
    mime_type: Optional[str],
    size: Optional[str],
    date: Optional[str],
    output_format: str,
):
    """搜索文件"""
    files = list(ctx.datastore.files.values())

    # 按关键词搜索（文件名）
    if keyword:
        files = [f for f in files if keyword.lower() in f.name.lower()]

    # 按文件名模式搜索
    if name:
        pattern = name.replace("*", ".*").replace("?", ".")
        regex = re.compile(pattern, re.IGNORECASE)
        files = [f for f in files if regex.search(f.name)]

    # 按标签搜索
    if tags:
        files = _filter_by_tags(files, tags, ctx)

    # 按文件类型搜索
    if mime_type:
        files = [f for f in files if mime_type.lower() in f.mime_type.lower()]

    # 按文件大小搜索
    if size:
        files = _filter_by_size(files, size)

    # 按日期搜索
    if date:
        files = _filter_by_date(files, date)

    # 输出结果
    if output_format == "table":
        _display_search_results(files, ctx)
    elif output_format == "simple":
        for file in files:
            click.echo(f"{file.file_id}\t{file.name}\t{file.path}")
    elif output_format == "json":
        import json
        data = [f.to_dict() for f in files]
        click.echo(json.dumps(data, indent=2, ensure_ascii=False))


def _filter_by_tags(files: List[File], query: str, ctx: Context) -> List[File]:
    """按标签查询表达式过滤文件"""
    # 解析标签查询表达式
    # 支持: tag1 AND tag2, tag1 OR tag2, NOT tag1, (tag1 OR tag2) AND tag3

    # 简化处理：先实现基础的AND/OR/NOT
    query = query.strip()

    # 将标签名转换为ID
    def get_tag_ids(tag_names: List[str]) -> List[str]:
        tag_ids = []
        for name in tag_names:
            tag = ctx.datastore.get_tag_by_name(name.strip())
            if tag:
                tag_ids.append(tag.tag_id)
        return tag_ids

    # 处理AND
    if " AND " in query:
        parts = [p.strip() for p in query.split(" AND ")]
        tag_ids = get_tag_ids(parts)
        # 文件必须包含所有标签
        return [f for f in files if all(tid in f.tags for tid in tag_ids)]

    # 处理OR
    elif " OR " in query:
        parts = [p.strip() for p in query.split(" OR ")]
        tag_ids = get_tag_ids(parts)
        # 文件包含任一标签
        return [f for f in files if any(tid in f.tags for tid in tag_ids)]

    # 处理NOT
    elif query.startswith("NOT "):
        tag_name = query[4:].strip()
        tag_ids = get_tag_ids([tag_name])
        # 文件不包含该标签
        return [f for f in files if not any(tid in f.tags for tid in tag_ids)]

    # 单个标签
    else:
        tag_ids = get_tag_ids([query])
        return [f for f in files if any(tid in f.tags for tid in tag_ids)]


def _filter_by_size(files: List[File], size_expr: str) -> List[File]:
    """按文件大小过滤"""
    # 解析大小表达式，例如: >1MB, <100KB, 1MB..10MB

    def parse_size(s: str) -> int:
        """解析大小字符串为字节数"""
        s = s.strip().upper()
        units = {"B": 1, "KB": 1024, "MB": 1024**2, "GB": 1024**3, "TB": 1024**4}

        for unit, multiplier in units.items():
            if s.endswith(unit):
                num_str = s[:-len(unit)]
                try:
                    return int(float(num_str) * multiplier)
                except ValueError:
                    return 0
        try:
            return int(s)
        except ValueError:
            return 0

    size_expr = size_expr.strip()

    # 范围查询: 1MB..10MB
    if ".." in size_expr:
        parts = size_expr.split("..")
        min_size = parse_size(parts[0])
        max_size = parse_size(parts[1])
        return [f for f in files if min_size <= f.size <= max_size]

    # 大于: >1MB
    elif size_expr.startswith(">"):
        min_size = parse_size(size_expr[1:])
        return [f for f in files if f.size > min_size]

    # 小于: <1MB
    elif size_expr.startswith("<"):
        max_size = parse_size(size_expr[1:])
        return [f for f in files if f.size < max_size]

    # 等于
    else:
        target_size = parse_size(size_expr)
        return [f for f in files if f.size == target_size]


def _filter_by_date(files: List[File], date_expr: str) -> List[File]:
    """按日期过滤"""
    # 解析日期表达式，例如: 2024-01-01..2024-12-31

    if ".." in date_expr:
        parts = date_expr.split("..")
        try:
            start_date = datetime.fromisoformat(parts[0].strip())
            end_date = datetime.fromisoformat(parts[1].strip())
            return [f for f in files if start_date <= f.added_at <= end_date]
        except ValueError:
            console.print("[yellow]警告: 日期格式错误，应为 YYYY-MM-DD[/yellow]")
            return files
    else:
        try:
            target_date = datetime.fromisoformat(date_expr.strip())
            # 匹配同一天
            return [
                f for f in files
                if f.added_at.date() == target_date.date()
            ]
        except ValueError:
            console.print("[yellow]警告: 日期格式错误，应为 YYYY-MM-DD[/yellow]")
            return files


def _display_search_results(files: List[File], ctx: Context):
    """显示搜索结果"""
    table = Table(title=f"搜索结果 (共 {len(files)} 个文件)")

    table.add_column("ID", style="cyan", no_wrap=True, max_width=12)
    table.add_column("文件名", style="white")
    table.add_column("大小", style="yellow", justify="right")
    table.add_column("类型", style="blue")
    table.add_column("标签", style="green")

    for file in files:
        # 获取标签名称
        tag_names = []
        for tag_id in file.tags[:2]:
            tag = ctx.datastore.get_tag(tag_id)
            if tag:
                tag_names.append(tag.name)
        tags_str = ", ".join(tag_names)
        if len(file.tags) > 2:
            tags_str += f" (+{len(file.tags) - 2})"

        table.add_row(
            file.file_id[:8],
            file.name[:35],
            _format_size(file.size),
            file.mime_type.split("/")[-1][:10],
            tags_str or "[dim]无[/dim]",
        )

    console.print(table)


def _format_size(size: int) -> str:
    """格式化文件大小"""
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if size < 1024.0:
            return f"{size:.1f} {unit}"
        size /= 1024.0
    return f"{size:.1f} PB"
