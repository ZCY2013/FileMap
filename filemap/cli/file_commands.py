"""文件管理命令"""
import click
from pathlib import Path
from rich.console import Console
from rich.table import Table
from typing import Optional
import shutil

from filemap.core.models import File
from filemap.cli.main import pass_context, Context


console = Console()


@click.group(name="file")
def file_group():
    """文件管理命令"""
    pass


@file_group.command(name="add")
@click.argument("file_path", type=click.Path(exists=True))
@click.option("--index", "mode", flag_value="index", default=True, help="索引模式（默认）")
@click.option("--import", "mode", flag_value="import", help="导入模式")
@click.option("--tags", help="标签列表，逗号分隔")
@click.option("--notes", help="文件备注")
@pass_context
def add_file(ctx: Context, file_path: str, mode: str, tags: Optional[str], notes: Optional[str]):
    """添加文件到FileMap"""
    file_path = Path(file_path).absolute()

    # 检查文件是否已存在
    existing = ctx.datastore.get_file_by_path(str(file_path))
    if existing:
        console.print(f"[yellow]文件已存在: {file_path}[/yellow]")
        return

    managed = mode == "import"

    # 创建File对象
    try:
        file_obj = File.from_path(str(file_path), managed=managed)
    except Exception as e:
        console.print(f"[red]错误: {e}[/red]")
        return

    # 如果是导入模式，复制文件到管理目录
    if managed:
        managed_dir = ctx.config.get_managed_dir()
        # 按年月组织文件
        year_month = file_obj.added_at.strftime("%Y/%m")
        dest_dir = managed_dir / year_month
        dest_dir.mkdir(parents=True, exist_ok=True)
        dest_path = dest_dir / file_obj.name

        # 处理重名文件
        counter = 1
        while dest_path.exists():
            stem = file_path.stem
            suffix = file_path.suffix
            dest_path = dest_dir / f"{stem}_{counter}{suffix}"
            counter += 1

        shutil.copy2(file_path, dest_path)
        file_obj.path = str(dest_path)

    # 添加备注
    if notes:
        file_obj.notes = notes

    # 添加标签
    if tags:
        tag_names = [t.strip() for t in tags.split(",")]
        for tag_name in tag_names:
            tag = ctx.datastore.get_tag_by_name(tag_name)
            if tag:
                file_obj.add_tag(tag.tag_id)
                tag.usage_count += 1
                ctx.datastore.update_tag(tag)
            else:
                console.print(f"[yellow]警告: 标签 '{tag_name}' 不存在，已忽略[/yellow]")

    # 保存文件
    ctx.datastore.add_file(file_obj)

    mode_str = "导入" if managed else "索引"
    console.print(f"[green]✓ 文件已{mode_str}: {file_obj.name}[/green]")
    console.print(f"  ID: {file_obj.file_id}")
    console.print(f"  路径: {file_obj.path}")
    console.print(f"  大小: {_format_size(file_obj.size)}")


@file_group.command(name="list")
@click.option("--tags", help="过滤标签，逗号分隔")
@click.option("--format", "output_format", type=click.Choice(["table", "simple", "json"]), default="table", help="输出格式")
@click.option("--sort", type=click.Choice(["name", "size", "date"]), default="name", help="排序方式")
@pass_context
def list_files(ctx: Context, tags: Optional[str], output_format: str, sort: str):
    """列出文件"""
    # 获取文件列表
    tag_ids = None
    if tags:
        tag_names = [t.strip() for t in tags.split(",")]
        tag_ids = []
        for tag_name in tag_names:
            tag = ctx.datastore.get_tag_by_name(tag_name)
            if tag:
                tag_ids.append(tag.tag_id)
            else:
                console.print(f"[yellow]警告: 标签 '{tag_name}' 不存在[/yellow]")

    files = ctx.datastore.list_files(tag_ids)

    # 排序
    if sort == "name":
        files.sort(key=lambda f: f.name)
    elif sort == "size":
        files.sort(key=lambda f: f.size, reverse=True)
    elif sort == "date":
        files.sort(key=lambda f: f.added_at, reverse=True)

    if output_format == "table":
        _display_files_table(files, ctx)
    elif output_format == "simple":
        for file in files:
            click.echo(f"{file.file_id}\t{file.name}\t{file.path}")
    elif output_format == "json":
        import json
        data = [f.to_dict() for f in files]
        click.echo(json.dumps(data, indent=2, ensure_ascii=False))


@file_group.command(name="show")
@click.argument("file_id")
@pass_context
def show_file(ctx: Context, file_id: str):
    """显示文件详情"""
    file = ctx.datastore.get_file(file_id)
    if not file:
        console.print(f"[red]错误: 文件不存在 (ID: {file_id})[/red]")
        return

    # 创建详情表格
    table = Table(title=f"文件详情: {file.name}", show_header=False)
    table.add_column("属性", style="cyan")
    table.add_column("值", style="white")

    table.add_row("ID", file.file_id)
    table.add_row("文件名", file.name)
    table.add_row("路径", file.path)
    table.add_row("模式", "导入管理" if file.managed else "索引")
    table.add_row("大小", _format_size(file.size))
    table.add_row("类型", file.mime_type)
    table.add_row("哈希", file.hash[:16] + "...")
    table.add_row("创建时间", str(file.created_at))
    table.add_row("修改时间", str(file.modified_at))
    table.add_row("添加时间", str(file.added_at))

    # 显示标签
    if file.tags:
        tag_names = []
        for tag_id in file.tags:
            tag = ctx.datastore.get_tag(tag_id)
            if tag:
                tag_names.append(tag.name)
        table.add_row("标签", ", ".join(tag_names))
    else:
        table.add_row("标签", "[dim]无[/dim]")

    if file.notes:
        table.add_row("备注", file.notes)

    console.print(table)


@file_group.command(name="remove")
@click.argument("file_id")
@click.option("--hard", is_flag=True, help="硬删除（同时删除文件）")
@click.confirmation_option(prompt="确定要删除此文件吗？")
@pass_context
def remove_file(ctx: Context, file_id: str, hard: bool):
    """删除文件"""
    file = ctx.datastore.get_file(file_id)
    if not file:
        console.print(f"[red]错误: 文件不存在 (ID: {file_id})[/red]")
        return

    # 如果是硬删除且文件是导入管理的，删除物理文件
    if hard and file.managed:
        try:
            Path(file.path).unlink()
            console.print(f"[yellow]已删除物理文件: {file.path}[/yellow]")
        except Exception as e:
            console.print(f"[red]删除物理文件失败: {e}[/red]")

    # 从数据库删除
    ctx.datastore.remove_file(file_id)
    console.print(f"[green]✓ 文件已从FileMap移除: {file.name}[/green]")


@file_group.command(name="update")
@click.argument("file_id")
@pass_context
def update_file(ctx: Context, file_id: str):
    """从文件系统更新文件信息"""
    file = ctx.datastore.get_file(file_id)
    if not file:
        console.print(f"[red]错误: 文件不存在 (ID: {file_id})[/red]")
        return

    try:
        file.update_from_filesystem()
        ctx.datastore.update_file(file)
        console.print(f"[green]✓ 文件信息已更新: {file.name}[/green]")
    except FileNotFoundError:
        console.print(f"[red]错误: 文件不存在于文件系统: {file.path}[/red]")
    except Exception as e:
        console.print(f"[red]错误: {e}[/red]")


def _display_files_table(files: list, ctx: Context):
    """以表格形式显示文件列表"""
    table = Table(title=f"文件列表 (共 {len(files)} 个)")

    table.add_column("ID", style="cyan", no_wrap=True, max_width=12)
    table.add_column("文件名", style="white")
    table.add_column("大小", style="yellow", justify="right")
    table.add_column("标签", style="green")
    table.add_column("添加时间", style="blue")

    for file in files:
        # 获取标签名称
        tag_names = []
        for tag_id in file.tags[:3]:  # 只显示前3个标签
            tag = ctx.datastore.get_tag(tag_id)
            if tag:
                tag_names.append(tag.name)
        tags_str = ", ".join(tag_names)
        if len(file.tags) > 3:
            tags_str += f" (+{len(file.tags) - 3})"

        table.add_row(
            file.file_id[:8],
            file.name[:40],
            _format_size(file.size),
            tags_str or "[dim]无[/dim]",
            file.added_at.strftime("%Y-%m-%d %H:%M"),
        )

    console.print(table)


def _format_size(size: int) -> str:
    """格式化文件大小"""
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if size < 1024.0:
            return f"{size:.1f} {unit}"
        size /= 1024.0
    return f"{size:.1f} PB"
