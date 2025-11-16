"""统计和报告命令"""
import click
from rich.console import Console
from rich.table import Table
from pathlib import Path
from datetime import datetime
from collections import Counter

from filemap.cli.main import pass_context, Context


console = Console()


@click.group(name="stats")
def stats_group():
    """统计和报告命令"""
    pass


@stats_group.command(name="summary")
@pass_context
def show_summary(ctx: Context):
    """显示总体统计信息"""
    stats = ctx.datastore.get_stats()

    console.print("[cyan]═══ FileMap 统计信息 ═══[/cyan]\n")

    # 基础统计
    table = Table(title="基础统计", show_header=False)
    table.add_column("项目", style="yellow")
    table.add_column("数值", style="white", justify="right")

    table.add_row("文件总数", str(stats["total_files"]))
    table.add_row("总大小", _format_size(stats["total_size"]))
    table.add_row("标签总数", str(stats["total_tags"]))
    table.add_row("类别总数", str(stats["total_categories"]))
    table.add_row("有标签的文件", str(stats["files_with_tags"]))
    table.add_row("无标签的文件", str(stats["files_without_tags"]))

    console.print(table)
    console.print("")

    # 类别分布
    if stats["category_distribution"]:
        cat_table = Table(title="类别分布")
        cat_table.add_column("类别", style="cyan")
        cat_table.add_column("文件数", style="green", justify="right")

        for cat_name, count in stats["category_distribution"].items():
            cat_table.add_row(cat_name, str(count))

        console.print(cat_table)


@stats_group.command(name="tags")
@click.option("--top", default=20, help="显示前N个标签")
@pass_context
def tag_stats(ctx: Context, top: int):
    """标签使用统计"""
    tags = list(ctx.datastore.tags.values())
    tags.sort(key=lambda t: t.usage_count, reverse=True)

    table = Table(title=f"标签使用统计 (Top {top})")
    table.add_column("排名", style="cyan", justify="right")
    table.add_column("标签名", style="white")
    table.add_column("使用次数", style="green", justify="right")
    table.add_column("类别", style="yellow")

    for idx, tag in enumerate(tags[:top], 1):
        cat = ctx.datastore.get_category(tag.category)
        cat_name = cat.name if cat else "未知"
        table.add_row(str(idx), tag.name, str(tag.usage_count), cat_name)

    console.print(table)


@stats_group.command(name="distribution")
@click.option("--by", "group_by", type=click.Choice(["type", "category", "size"]), default="type", help="分组方式")
@pass_context
def distribution_stats(ctx: Context, group_by: str):
    """文件分布统计"""
    files = list(ctx.datastore.files.values())

    if group_by == "type":
        # 按MIME类型分组
        type_counter = Counter()
        for file in files:
            mime_type = file.mime_type.split("/")[0] if "/" in file.mime_type else file.mime_type
            type_counter[mime_type] += 1

        table = Table(title="文件类型分布")
        table.add_column("类型", style="cyan")
        table.add_column("文件数", style="green", justify="right")
        table.add_column("占比", style="yellow", justify="right")

        total = sum(type_counter.values())
        for mime_type, count in type_counter.most_common():
            percentage = (count / total * 100) if total > 0 else 0
            table.add_row(mime_type, str(count), f"{percentage:.1f}%")

        console.print(table)

    elif group_by == "category":
        # 按类别分组
        cat_counter = Counter()
        for file in files:
            for tag_id in file.tags:
                tag = ctx.datastore.get_tag(tag_id)
                if tag:
                    cat = ctx.datastore.get_category(tag.category)
                    if cat:
                        cat_counter[cat.name] += 1

        table = Table(title="类别分布")
        table.add_column("类别", style="cyan")
        table.add_column("标记次数", style="green", justify="right")

        for cat_name, count in cat_counter.most_common():
            table.add_row(cat_name, str(count))

        console.print(table)

    elif group_by == "size":
        # 按文件大小分组
        size_ranges = {
            "< 1KB": 0,
            "1KB - 100KB": 0,
            "100KB - 1MB": 0,
            "1MB - 10MB": 0,
            "10MB - 100MB": 0,
            "> 100MB": 0,
        }

        for file in files:
            size = file.size
            if size < 1024:
                size_ranges["< 1KB"] += 1
            elif size < 100 * 1024:
                size_ranges["1KB - 100KB"] += 1
            elif size < 1024 * 1024:
                size_ranges["100KB - 1MB"] += 1
            elif size < 10 * 1024 * 1024:
                size_ranges["1MB - 10MB"] += 1
            elif size < 100 * 1024 * 1024:
                size_ranges["10MB - 100MB"] += 1
            else:
                size_ranges["> 100MB"] += 1

        table = Table(title="文件大小分布")
        table.add_column("大小范围", style="cyan")
        table.add_column("文件数", style="green", justify="right")
        table.add_column("占比", style="yellow", justify="right")

        total = len(files)
        for size_range, count in size_ranges.items():
            percentage = (count / total * 100) if total > 0 else 0
            table.add_row(size_range, str(count), f"{percentage:.1f}%")

        console.print(table)


@stats_group.command(name="timeline")
@click.option("--period", type=click.Choice(["day", "week", "month"]), default="month", help="时间周期")
@click.option("--limit", default=12, help="显示最近N个周期")
@pass_context
def timeline_stats(ctx: Context, period: str, limit: int):
    """时间趋势统计"""
    files = list(ctx.datastore.files.values())
    files.sort(key=lambda f: f.added_at)

    # 按周期分组
    period_counter = Counter()

    for file in files:
        if period == "day":
            key = file.added_at.strftime("%Y-%m-%d")
        elif period == "week":
            key = file.added_at.strftime("%Y-W%W")
        else:  # month
            key = file.added_at.strftime("%Y-%m")

        period_counter[key] += 1

    # 显示最近N个周期
    recent_periods = sorted(period_counter.keys(), reverse=True)[:limit]
    recent_periods.reverse()

    table = Table(title=f"文件添加趋势 ({period})")
    table.add_column("时间", style="cyan")
    table.add_column("文件数", style="green", justify="right")
    table.add_column("趋势", style="yellow")

    max_count = max(period_counter.values()) if period_counter else 1

    for key in recent_periods:
        count = period_counter[key]
        # 生成简单的条形图
        bar_length = int((count / max_count) * 20)
        bar = "█" * bar_length
        table.add_row(key, str(count), bar)

    console.print(table)


@stats_group.command(name="report")
@click.option("--format", "output_format", type=click.Choice(["text", "markdown", "html"]), default="text", help="报告格式")
@click.option("--output", type=click.Path(), help="输出文件路径")
@pass_context
def generate_report(ctx: Context, output_format: str, output: str):
    """生成统计报告"""
    stats = ctx.datastore.get_stats()

    if output_format == "text":
        report = _generate_text_report(ctx, stats)
    elif output_format == "markdown":
        report = _generate_markdown_report(ctx, stats)
    elif output_format == "html":
        report = _generate_html_report(ctx, stats)
    else:
        report = "不支持的格式"

    if output:
        with open(output, "w", encoding="utf-8") as f:
            f.write(report)
        console.print(f"[green]✓ 报告已保存到: {output}[/green]")
    else:
        console.print(report)


def _generate_text_report(ctx: Context, stats: dict) -> str:
    """生成文本格式报告"""
    lines = []
    lines.append("=" * 60)
    lines.append(f"FileMap 统计报告")
    lines.append(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append("=" * 60)
    lines.append("")

    lines.append("基础统计:")
    lines.append(f"  文件总数: {stats['total_files']}")
    lines.append(f"  总大小: {_format_size(stats['total_size'])}")
    lines.append(f"  标签总数: {stats['total_tags']}")
    lines.append(f"  类别总数: {stats['total_categories']}")
    lines.append(f"  有标签的文件: {stats['files_with_tags']}")
    lines.append(f"  无标签的文件: {stats['files_without_tags']}")
    lines.append("")

    # 标签TOP10
    tags = sorted(ctx.datastore.tags.values(), key=lambda t: t.usage_count, reverse=True)
    lines.append("标签使用 TOP 10:")
    for idx, tag in enumerate(tags[:10], 1):
        lines.append(f"  {idx}. {tag.name}: {tag.usage_count} 次")

    return "\n".join(lines)


def _generate_markdown_report(ctx: Context, stats: dict) -> str:
    """生成Markdown格式报告"""
    lines = []
    lines.append("# FileMap 统计报告")
    lines.append(f"\n**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    lines.append("## 基础统计\n")
    lines.append("| 项目 | 数值 |")
    lines.append("|------|------|")
    lines.append(f"| 文件总数 | {stats['total_files']} |")
    lines.append(f"| 总大小 | {_format_size(stats['total_size'])} |")
    lines.append(f"| 标签总数 | {stats['total_tags']} |")
    lines.append(f"| 类别总数 | {stats['total_categories']} |")
    lines.append(f"| 有标签的文件 | {stats['files_with_tags']} |")
    lines.append(f"| 无标签的文件 | {stats['files_without_tags']} |")
    lines.append("")

    # 标签TOP10
    tags = sorted(ctx.datastore.tags.values(), key=lambda t: t.usage_count, reverse=True)
    lines.append("## 标签使用 TOP 10\n")
    lines.append("| 排名 | 标签名 | 使用次数 |")
    lines.append("|------|--------|----------|")
    for idx, tag in enumerate(tags[:10], 1):
        lines.append(f"| {idx} | {tag.name} | {tag.usage_count} |")

    return "\n".join(lines)


def _generate_html_report(ctx: Context, stats: dict) -> str:
    """生成HTML格式报告"""
    html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>FileMap 统计报告</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; }}
        h1 {{ color: #333; }}
        table {{ border-collapse: collapse; width: 100%; margin: 20px 0; }}
        th, td {{ border: 1px solid #ddd; padding: 12px; text-align: left; }}
        th {{ background-color: #4CAF50; color: white; }}
        tr:nth-child(even) {{ background-color: #f2f2f2; }}
    </style>
</head>
<body>
    <h1>FileMap 统计报告</h1>
    <p><strong>生成时间</strong>: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>

    <h2>基础统计</h2>
    <table>
        <tr><th>项目</th><th>数值</th></tr>
        <tr><td>文件总数</td><td>{stats['total_files']}</td></tr>
        <tr><td>总大小</td><td>{_format_size(stats['total_size'])}</td></tr>
        <tr><td>标签总数</td><td>{stats['total_tags']}</td></tr>
        <tr><td>类别总数</td><td>{stats['total_categories']}</td></tr>
        <tr><td>有标签的文件</td><td>{stats['files_with_tags']}</td></tr>
        <tr><td>无标签的文件</td><td>{stats['files_without_tags']}</td></tr>
    </table>
"""

    # 标签TOP10
    tags = sorted(ctx.datastore.tags.values(), key=lambda t: t.usage_count, reverse=True)
    html += """
    <h2>标签使用 TOP 10</h2>
    <table>
        <tr><th>排名</th><th>标签名</th><th>使用次数</th></tr>
"""
    for idx, tag in enumerate(tags[:10], 1):
        html += f"        <tr><td>{idx}</td><td>{tag.name}</td><td>{tag.usage_count}</td></tr>\n"

    html += """    </table>
</body>
</html>"""

    return html


def _format_size(size: int) -> str:
    """格式化文件大小"""
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if size < 1024.0:
            return f"{size:.1f} {unit}"
        size /= 1024.0
    return f"{size:.1f} PB"
