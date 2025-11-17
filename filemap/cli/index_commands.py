"""索引管理命令"""
import click
from rich.console import Console
from rich.table import Table
from rich.progress import Progress
from pathlib import Path

from filemap.cli.main import pass_context, Context
from filemap.search.indexer import ContentIndexer


console = Console()


@click.group(name="index")
def index_group():
    """全文索引管理命令"""
    pass


@index_group.command(name="content")
@click.argument("file_id", required=False)
@click.option("--all", "index_all", is_flag=True, help="索引所有文件")
@click.option("--type", "file_type", help="只索引特定类型（pdf/txt）")
@click.option("--force", is_flag=True, help="强制重新索引")
@pass_context
def index_content(ctx: Context, file_id: str, index_all: bool, file_type: str, force: bool):
    """为文件创建全文索引"""
    # 初始化索引器
    index_dir = ctx.config.get_data_dir() / "index"
    indexer = ContentIndexer(index_dir)

    if index_all:
        # 索引所有文件
        files = list(ctx.datastore.files.values())

        # 按类型过滤
        if file_type:
            mime_map = {
                'pdf': 'application/pdf',
                'txt': 'text/plain',
            }
            if file_type in mime_map:
                target_mime = mime_map[file_type]
                files = [f for f in files if target_mime in f.mime_type]

        console.print(f"[cyan]正在索引 {len(files)} 个文件...[/cyan]")

        with Progress() as progress:
            task = progress.add_task("[green]索引中...", total=len(files))

            def update_progress(current, total, filename):
                progress.update(task, completed=current, description=f"[green]索引: {filename[:30]}")

            stats = indexer.index_files(files, progress_callback=update_progress)

        console.print(f"[green]✓ 索引完成[/green]")
        console.print(f"  成功: {stats['success']}")
        console.print(f"  失败: {stats['failed']}")
        console.print(f"  跳过: {stats['skipped']}")

    elif file_id:
        # 索引单个文件
        file = ctx.datastore.get_file(file_id)
        if not file:
            # 尝试匹配ID前缀
            for f in ctx.datastore.files.values():
                if f.file_id.startswith(file_id):
                    file = f
                    break

        if not file:
            console.print(f"[red]错误: 文件不存在 (ID: {file_id})[/red]")
            return

        # 检查是否已索引
        if not force and indexer.is_indexed(file.file_id):
            console.print(f"[yellow]文件已索引: {file.name}[/yellow]")
            console.print("[dim]使用 --force 强制重新索引[/dim]")
            return

        console.print(f"[cyan]正在索引: {file.name}[/cyan]")
        if indexer.index_file(file):
            console.print(f"[green]✓ 索引成功[/green]")
        else:
            console.print(f"[red]✗ 索引失败[/red]")

    else:
        console.print("[yellow]请指定文件ID或使用 --all 索引所有文件[/yellow]")


@index_group.command(name="status")
@pass_context
def index_status(ctx: Context):
    """查看索引状态"""
    index_dir = ctx.config.get_data_dir() / "index"

    if not index_dir.exists():
        console.print("[yellow]索引尚未创建[/yellow]")
        return

    indexer = ContentIndexer(index_dir)
    stats = indexer.get_stats()

    table = Table(title="索引状态")
    table.add_column("项目", style="cyan")
    table.add_column("值", style="white")

    table.add_row("索引文档数", str(stats['total_docs']))
    table.add_row("索引大小", _format_size(stats['index_size']))
    table.add_row("最后更新", str(stats['last_modified']) if stats['last_modified'] else '未知')
    table.add_row("索引目录", str(index_dir))

    console.print(table)


@index_group.command(name="search")
@click.argument("query")
@click.option("--limit", default=20, help="结果数量限制")
@click.option("--highlight", is_flag=True, help="高亮显示匹配内容")
@pass_context
def search_content(ctx: Context, query: str, limit: int, highlight: bool):
    """全文搜索"""
    index_dir = ctx.config.get_data_dir() / "index"

    if not index_dir.exists():
        console.print("[yellow]索引尚未创建，请先运行 'filemap index content --all'[/yellow]")
        return

    indexer = ContentIndexer(index_dir)

    console.print(f"[cyan]搜索: {query}[/cyan]\n")

    results = indexer.search(query, limit=limit, highlight=highlight)

    if not results:
        console.print("[yellow]没有找到匹配的结果[/yellow]")
        return

    console.print(f"[green]找到 {len(results)} 个结果:[/green]\n")

    for idx, result in enumerate(results, 1):
        # 获取文件信息
        file = ctx.datastore.get_file(result['file_id'])
        if not file:
            continue

        score_pct = int(result['score'] * 100)
        console.print(f"[bold]{idx}. [{score_pct}%] {result['filename']}[/bold]")
        console.print(f"   路径: [dim]{result['path']}[/dim]")

        if highlight and result['highlights']:
            for field, hl_text in result['highlights']:
                if field == 'content':
                    console.print(f"   [yellow]{hl_text}[/yellow]")

        console.print()


@index_group.command(name="rebuild")
@click.confirmation_option(prompt="确定要重建索引吗？这会删除现有索引。")
@pass_context
def rebuild_index(ctx: Context):
    """重建索引"""
    index_dir = ctx.config.get_data_dir() / "index"

    # 删除现有索引
    if index_dir.exists():
        import shutil
        shutil.rmtree(index_dir)
        console.print("[yellow]已删除现有索引[/yellow]")

    # 重新索引所有文件
    indexer = ContentIndexer(index_dir)
    files = list(ctx.datastore.files.values())

    console.print(f"[cyan]正在重建索引（共 {len(files)} 个文件）...[/cyan]")

    with Progress() as progress:
        task = progress.add_task("[green]索引中...", total=len(files))

        def update_progress(current, total, filename):
            progress.update(task, completed=current, description=f"[green]索引: {filename[:30]}")

        stats = indexer.index_files(files, progress_callback=update_progress)

    console.print(f"[green]✓ 索引重建完成[/green]")
    console.print(f"  成功: {stats['success']}")
    console.print(f"  失败: {stats['failed']}")
    console.print(f"  跳过: {stats['skipped']}")


@index_group.command(name="optimize")
@pass_context
def optimize_index(ctx: Context):
    """优化索引"""
    index_dir = ctx.config.get_data_dir() / "index"

    if not index_dir.exists():
        console.print("[yellow]索引尚未创建[/yellow]")
        return

    console.print("[cyan]正在优化索引...[/cyan]")
    indexer = ContentIndexer(index_dir)
    indexer.optimize()
    console.print("[green]✓ 索引优化完成[/green]")


def _format_size(size: int) -> str:
    """格式化文件大小"""
    for unit in ["B", "KB", "MB", "GB"]:
        if size < 1024.0:
            return f"{size:.1f} {unit}"
        size /= 1024.0
    return f"{size:.1f} TB"
