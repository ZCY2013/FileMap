"""数据迁移命令"""
import click
from rich.console import Console
from rich.table import Table
from pathlib import Path

from filemap.storage.migration import DataMigration

console = Console()


@click.group(name="migrate")
def migrate_group():
    """数据迁移命令"""
    pass


@migrate_group.command(name="to-sqlite")
@click.option("--json-dir", type=click.Path(exists=True), required=True, help="JSON 数据目录")
@click.option("--sqlite-db", type=click.Path(), required=True, help="SQLite 数据库路径")
def migrate_to_sqlite(json_dir: str, sqlite_db: str):
    """从 JSON 迁移到 SQLite"""
    console.print(f"[cyan]开始迁移数据...[/cyan]")
    console.print(f"  源目录: {json_dir}")
    console.print(f"  目标数据库: {sqlite_db}")

    stats = DataMigration.migrate_from_json(
        Path(json_dir),
        Path(sqlite_db)
    )

    # 显示统计信息
    table = Table(title="迁移结果")
    table.add_column("项目", style="cyan")
    table.add_column("数量", style="green")

    table.add_row("分类", str(stats['categories']))
    table.add_row("标签", str(stats['tags']))
    table.add_row("文件", str(stats['files']))
    table.add_row("错误", str(len(stats['errors'])), style="red" if stats['errors'] else "green")

    console.print(table)

    if stats['errors']:
        console.print("\n[yellow]迁移过程中的错误:[/yellow]")
        for error in stats['errors'][:10]:  # 最多显示10个错误
            console.print(f"  [red]• {error}[/red]")

        if len(stats['errors']) > 10:
            console.print(f"  [dim]... 还有 {len(stats['errors']) - 10} 个错误[/dim]")
    else:
        console.print("\n[green]✓ 迁移成功完成！[/green]")


@migrate_group.command(name="to-json")
@click.option("--sqlite-db", type=click.Path(exists=True), required=True, help="SQLite 数据库路径")
@click.option("--json-dir", type=click.Path(), required=True, help="JSON 导出目录")
def export_to_json(sqlite_db: str, json_dir: str):
    """从 SQLite 导出到 JSON（备份）"""
    console.print(f"[cyan]开始导出数据...[/cyan]")
    console.print(f"  数据库: {sqlite_db}")
    console.print(f"  导出目录: {json_dir}")

    stats = DataMigration.export_to_json(
        Path(sqlite_db),
        Path(json_dir)
    )

    # 显示统计信息
    table = Table(title="导出结果")
    table.add_column("项目", style="cyan")
    table.add_column("数量", style="green")

    table.add_row("分类", str(stats['categories']))
    table.add_row("标签", str(stats['tags']))
    table.add_row("文件", str(stats['files']))
    table.add_row("错误", str(len(stats['errors'])), style="red" if stats['errors'] else "green")

    console.print(table)

    if stats['errors']:
        console.print("\n[yellow]导出过程中的错误:[/yellow]")
        for error in stats['errors']:
            console.print(f"  [red]• {error}[/red]")
    else:
        console.print("\n[green]✓ 导出成功完成！[/green]")
