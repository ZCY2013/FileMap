"""类别管理命令"""
import click
from rich.console import Console
from rich.table import Table
from typing import Optional

from filemap.core.models import Category
from filemap.cli.main import pass_context, Context


console = Console()


@click.group(name="category")
def category_group():
    """类别管理命令"""
    pass


@category_group.command(name="create")
@click.argument("category_name")
@click.option("--description", help="类别描述")
@click.option("--exclusive", is_flag=True, help="该类别下的标签是否互斥")
@click.option("--color", default="#CCCCCC", help="类别颜色")
@click.option("--icon", default="📁", help="类别图标")
@pass_context
def create_category(
    ctx: Context,
    category_name: str,
    description: Optional[str],
    exclusive: bool,
    color: str,
    icon: str,
):
    """创建新类别"""
    # 检查类别是否已存在
    existing = ctx.datastore.get_category_by_name(category_name)
    if existing:
        console.print(f"[yellow]类别已存在: {category_name}[/yellow]")
        return

    # 创建类别
    category = Category(
        name=category_name,
        description=description or "",
        mutually_exclusive=exclusive,
        color=color,
        icon=icon,
        priority=len(ctx.datastore.categories) + 1,
    )

    ctx.datastore.add_category(category)
    console.print(f"[green]✓ 类别已创建: {category_name}[/green]")
    console.print(f"  ID: {category.category_id}")
    console.print(f"  互斥: {'是' if exclusive else '否'}")


@category_group.command(name="list")
@pass_context
def list_categories(ctx: Context):
    """列出所有类别"""
    categories = ctx.datastore.list_categories()

    table = Table(title=f"类别列表 (共 {len(categories)} 个)")
    table.add_column("图标", style="white")
    table.add_column("名称", style="cyan")
    table.add_column("互斥", style="yellow", justify="center")
    table.add_column("标签数", style="green", justify="right")
    table.add_column("描述", style="white")

    for cat in categories:
        # 统计该类别下的标签数
        tags = ctx.datastore.list_tags(cat.category_id)
        tag_count = len(tags)

        table.add_row(
            cat.icon,
            cat.name,
            "✓" if cat.mutually_exclusive else "✗",
            str(tag_count),
            cat.description or "[dim]无[/dim]",
        )

    console.print(table)


@category_group.command(name="show")
@click.argument("category_name")
@pass_context
def show_category(ctx: Context, category_name: str):
    """显示类别详情"""
    cat = ctx.datastore.get_category_by_name(category_name)
    if not cat:
        console.print(f"[red]错误: 类别不存在: {category_name}[/red]")
        return

    # 创建详情表格
    table = Table(title=f"类别详情: {cat.name}", show_header=False)
    table.add_column("属性", style="cyan")
    table.add_column("值", style="white")

    table.add_row("ID", cat.category_id)
    table.add_row("名称", cat.name)
    table.add_row("图标", cat.icon)
    table.add_row("描述", cat.description or "[dim]无[/dim]")
    table.add_row("互斥", "是" if cat.mutually_exclusive else "否")
    table.add_row("颜色", cat.color)
    table.add_row("优先级", str(cat.priority))
    table.add_row("创建时间", str(cat.created_at))

    console.print(table)

    # 显示该类别下的标签
    tags = ctx.datastore.list_tags(cat.category_id)
    if tags:
        console.print(f"\n该类别下的标签 (共 {len(tags)} 个):")
        for tag in tags[:10]:
            console.print(f"  • {tag.name} (使用 {tag.usage_count} 次)")
        if len(tags) > 10:
            console.print(f"  ... 还有 {len(tags) - 10} 个标签")


@category_group.command(name="delete")
@click.argument("category_name")
@click.confirmation_option(prompt="确定要删除此类别吗？该类别下的标签将移动到未分类。")
@pass_context
def delete_category(ctx: Context, category_name: str):
    """删除类别"""
    if category_name == "uncategorized":
        console.print("[red]错误: 不能删除默认的未分类类别[/red]")
        return

    cat = ctx.datastore.get_category_by_name(category_name)
    if not cat:
        console.print(f"[red]错误: 类别不存在: {category_name}[/red]")
        return

    ctx.datastore.remove_category(cat.category_id)
    console.print(f"[green]✓ 类别已删除: {category_name}[/green]")
