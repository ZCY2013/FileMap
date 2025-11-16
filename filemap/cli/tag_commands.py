"""标签管理命令"""
import click
from rich.console import Console
from rich.table import Table
from typing import Optional

from filemap.core.models import Tag
from filemap.cli.main import pass_context, Context


console = Console()


@click.group(name="tag")
def tag_group():
    """标签管理命令"""
    pass


@tag_group.command(name="create")
@click.argument("tag_name")
@click.option("--category", help="所属类别名称")
@click.option("--description", help="标签描述")
@click.option("--color", default="#FFFFFF", help="标签颜色（十六进制）")
@pass_context
def create_tag(
    ctx: Context, tag_name: str, category: Optional[str], description: Optional[str], color: str
):
    """创建新标签"""
    # 检查标签是否已存在
    existing = ctx.datastore.get_tag_by_name(tag_name)
    if existing:
        console.print(f"[yellow]标签已存在: {tag_name}[/yellow]")
        return

    # 获取类别
    category_id = "uncategorized"
    if category:
        cat = ctx.datastore.get_category_by_name(category)
        if cat:
            category_id = cat.category_id
        else:
            console.print(f"[yellow]警告: 类别 '{category}' 不存在，使用默认类别[/yellow]")

    # 创建标签
    tag = Tag(
        name=tag_name,
        category=category_id,
        description=description or "",
        color=color,
    )

    ctx.datastore.add_tag(tag)
    console.print(f"[green]✓ 标签已创建: {tag_name}[/green]")
    console.print(f"  ID: {tag.tag_id}")
    console.print(f"  类别: {category or 'uncategorized'}")


@tag_group.command(name="list")
@click.option("--category", help="过滤类别")
@click.option("--sort", type=click.Choice(["name", "usage"]), default="name", help="排序方式")
@pass_context
def list_tags(ctx: Context, category: Optional[str], sort: str):
    """列出所有标签"""
    # 获取类别ID
    category_id = None
    if category:
        cat = ctx.datastore.get_category_by_name(category)
        if cat:
            category_id = cat.category_id
        else:
            console.print(f"[yellow]警告: 类别 '{category}' 不存在[/yellow]")
            return

    # 获取标签列表
    tags = ctx.datastore.list_tags(category_id)

    # 排序
    if sort == "name":
        tags.sort(key=lambda t: t.name)
    elif sort == "usage":
        tags.sort(key=lambda t: t.usage_count, reverse=True)

    # 显示表格
    table = Table(title=f"标签列表 (共 {len(tags)} 个)")
    table.add_column("标签名", style="cyan")
    table.add_column("类别", style="yellow")
    table.add_column("使用次数", style="green", justify="right")
    table.add_column("描述", style="white")

    for tag in tags:
        cat = ctx.datastore.get_category(tag.category)
        cat_name = cat.name if cat else "未知"

        table.add_row(
            tag.name, cat_name, str(tag.usage_count), tag.description or "[dim]无[/dim]"
        )

    console.print(table)


@tag_group.command(name="show")
@click.argument("tag_name")
@pass_context
def show_tag(ctx: Context, tag_name: str):
    """显示标签详情"""
    tag = ctx.datastore.get_tag_by_name(tag_name)
    if not tag:
        console.print(f"[red]错误: 标签不存在: {tag_name}[/red]")
        return

    # 创建详情表格
    table = Table(title=f"标签详情: {tag.name}", show_header=False)
    table.add_column("属性", style="cyan")
    table.add_column("值", style="white")

    cat = ctx.datastore.get_category(tag.category)
    cat_name = cat.name if cat else "未知"

    table.add_row("ID", tag.tag_id)
    table.add_row("名称", tag.name)
    table.add_row("类别", cat_name)
    table.add_row("使用次数", str(tag.usage_count))
    table.add_row("描述", tag.description or "[dim]无[/dim]")
    table.add_row("颜色", tag.color)
    table.add_row("创建时间", str(tag.created_at))

    if tag.aliases:
        table.add_row("别名", ", ".join(tag.aliases))

    console.print(table)


@tag_group.command(name="delete")
@click.argument("tag_name")
@click.confirmation_option(prompt="确定要删除此标签吗？这将从所有文件中移除此标签。")
@pass_context
def delete_tag(ctx: Context, tag_name: str):
    """删除标签"""
    tag = ctx.datastore.get_tag_by_name(tag_name)
    if not tag:
        console.print(f"[red]错误: 标签不存在: {tag_name}[/red]")
        return

    ctx.datastore.remove_tag(tag.tag_id)
    console.print(f"[green]✓ 标签已删除: {tag_name}[/green]")


@tag_group.command(name="add")
@click.argument("file_id")
@click.argument("tag_names", nargs=-1, required=True)
@pass_context
def add_tag_to_file(ctx: Context, file_id: str, tag_names: tuple):
    """为文件添加标签"""
    file = ctx.datastore.get_file(file_id)
    if not file:
        console.print(f"[red]错误: 文件不存在 (ID: {file_id})[/red]")
        return

    added_count = 0
    for tag_name in tag_names:
        tag = ctx.datastore.get_tag_by_name(tag_name)
        if tag:
            if not file.has_tag(tag.tag_id):
                file.add_tag(tag.tag_id)
                tag.usage_count += 1
                ctx.datastore.update_tag(tag)
                added_count += 1
            else:
                console.print(f"[yellow]文件已有标签: {tag_name}[/yellow]")
        else:
            console.print(f"[yellow]警告: 标签不存在: {tag_name}[/yellow]")

    if added_count > 0:
        ctx.datastore.update_file(file)
        console.print(f"[green]✓ 已添加 {added_count} 个标签到文件: {file.name}[/green]")


@tag_group.command(name="remove")
@click.argument("file_id")
@click.argument("tag_names", nargs=-1, required=True)
@pass_context
def remove_tag_from_file(ctx: Context, file_id: str, tag_names: tuple):
    """从文件移除标签"""
    file = ctx.datastore.get_file(file_id)
    if not file:
        console.print(f"[red]错误: 文件不存在 (ID: {file_id})[/red]")
        return

    removed_count = 0
    for tag_name in tag_names:
        tag = ctx.datastore.get_tag_by_name(tag_name)
        if tag:
            if file.has_tag(tag.tag_id):
                file.remove_tag(tag.tag_id)
                tag.usage_count = max(0, tag.usage_count - 1)
                ctx.datastore.update_tag(tag)
                removed_count += 1
            else:
                console.print(f"[yellow]文件没有标签: {tag_name}[/yellow]")
        else:
            console.print(f"[yellow]警告: 标签不存在: {tag_name}[/yellow]")

    if removed_count > 0:
        ctx.datastore.update_file(file)
        console.print(f"[green]✓ 已从文件移除 {removed_count} 个标签: {file.name}[/green]")


@tag_group.command(name="stats")
@click.option("--category", help="过滤类别")
@pass_context
def tag_stats(ctx: Context, category: Optional[str]):
    """标签使用统计"""
    category_id = None
    if category:
        cat = ctx.datastore.get_category_by_name(category)
        if cat:
            category_id = cat.category_id

    tags = ctx.datastore.list_tags(category_id)
    tags.sort(key=lambda t: t.usage_count, reverse=True)

    table = Table(title="标签使用统计")
    table.add_column("排名", style="cyan", justify="right")
    table.add_column("标签名", style="white")
    table.add_column("使用次数", style="green", justify="right")
    table.add_column("类别", style="yellow")

    for idx, tag in enumerate(tags[:20], 1):  # 显示前20个
        cat = ctx.datastore.get_category(tag.category)
        cat_name = cat.name if cat else "未知"
        table.add_row(str(idx), tag.name, str(tag.usage_count), cat_name)

    console.print(table)
