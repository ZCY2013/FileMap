"""知识图谱命令"""
import click
from rich.console import Console
from rich.table import Table
from pathlib import Path

from filemap.graph.knowledge_graph import KnowledgeGraph
from filemap.cli.main import pass_context, Context


console = Console()


@click.group(name="graph")
def graph_group():
    """知识图谱命令"""
    pass


@graph_group.command(name="generate")
@click.option("--mode", type=click.Choice(["tags", "files", "full"]), default="tags", help="生成模式")
@pass_context
def generate_graph(ctx: Context, mode: str):
    """生成知识图谱"""
    console.print(f"[cyan]正在生成{mode}模式的知识图谱...[/cyan]")

    kg = KnowledgeGraph(ctx.datastore)
    kg.generate(mode=mode)

    stats = kg.get_stats()
    console.print(f"[green]✓ 知识图谱已生成[/green]")
    console.print(f"  节点数: {stats['total_nodes']}")
    console.print(f"  边数: {stats['total_edges']}")
    console.print(f"  平均度: {stats['avg_degree']:.2f}")
    console.print(f"  密度: {stats['density']:.4f}")
    console.print(f"  连通分量: {stats['connected_components']}")

    # 保存到数据目录
    graph_path = ctx.config.get_data_dir() / "graph.json"
    kg.save(str(graph_path))
    console.print(f"  已保存到: {graph_path}")


@graph_group.command(name="show")
@click.option("--format", "output_format", type=click.Choice(["text", "json"]), default="text", help="显示格式")
@click.option("--output", type=click.Path(), help="输出到文件")
@pass_context
def show_graph(ctx: Context, output_format: str, output: str):
    """显示知识图谱"""
    # 加载图谱
    graph_path = ctx.config.get_data_dir() / "graph.json"
    if not graph_path.exists():
        console.print("[yellow]知识图谱未生成，请先运行 'filemap graph generate'[/yellow]")
        return

    kg = KnowledgeGraph(ctx.datastore)
    kg.generate(mode="tags")  # 重新生成

    if output_format == "text":
        text_viz = kg.visualize_text()
        if output:
            with open(output, "w", encoding="utf-8") as f:
                f.write(text_viz)
            console.print(f"[green]✓ 已保存到: {output}[/green]")
        else:
            console.print(text_viz)

    elif output_format == "json":
        import json
        data = kg.export_json()
        json_str = json.dumps(data, ensure_ascii=False, indent=2)
        if output:
            with open(output, "w", encoding="utf-8") as f:
                f.write(json_str)
            console.print(f"[green]✓ 已保存到: {output}[/green]")
        else:
            console.print(json_str)


@graph_group.command(name="hubs")
@click.option("--top", default=10, help="显示前N个核心节点")
@pass_context
def show_hubs(ctx: Context, top: int):
    """显示核心节点"""
    kg = KnowledgeGraph(ctx.datastore)
    kg.generate(mode="tags")

    hubs = kg.find_hubs(top_n=top)

    table = Table(title=f"核心节点 (Top {top})")
    table.add_column("排名", style="cyan", justify="right")
    table.add_column("类型", style="yellow")
    table.add_column("名称", style="white")
    table.add_column("连接数", style="green", justify="right")
    table.add_column("使用次数", style="blue", justify="right")

    for idx, (node_id, degree) in enumerate(hubs, 1):
        node_data = kg.graph.nodes[node_id]
        node_type = node_data.get("type", "unknown")
        name = node_data.get("name", "未知")
        usage = node_data.get("usage_count", 0)

        table.add_row(str(idx), node_type, name, str(degree), str(usage))

    console.print(table)


@graph_group.command(name="orphans")
@click.option("--type", "node_type", type=click.Choice(["tag", "file", "all"]), default="all", help="节点类型")
@pass_context
def show_orphans(ctx: Context, node_type: str):
    """显示孤立节点"""
    kg = KnowledgeGraph(ctx.datastore)
    kg.generate(mode="full")

    filter_type = None if node_type == "all" else node_type
    orphans = kg.find_orphans(node_type=filter_type)

    console.print(f"[cyan]孤立节点 (共 {len(orphans)} 个):[/cyan]")

    for node_id in orphans:
        node_data = kg.graph.nodes[node_id]
        ntype = node_data.get("type", "unknown")
        name = node_data.get("name", "未知")
        console.print(f"  [{ntype}] {name}")


@graph_group.command(name="recommend")
@click.argument("file_id")
@click.option("--top", default=5, help="推荐数量")
@pass_context
def recommend_tags(ctx: Context, file_id: str, top: int):
    """为文件推荐标签"""
    file = ctx.datastore.get_file(file_id)
    if not file:
        console.print(f"[red]错误: 文件不存在 (ID: {file_id})[/red]")
        return

    kg = KnowledgeGraph(ctx.datastore)
    kg.generate(mode="tags")

    recommendations = kg.recommend_tags(file_id, top_n=top)

    if not recommendations:
        console.print("[yellow]暂无推荐标签[/yellow]")
        return

    console.print(f"[cyan]为文件 '{file.name}' 推荐的标签:[/cyan]")

    table = Table()
    table.add_column("排名", style="cyan", justify="right")
    table.add_column("标签名", style="white")
    table.add_column("推荐分数", style="green", justify="right")
    table.add_column("类别", style="yellow")

    for idx, (tag_id, score) in enumerate(recommendations, 1):
        tag = ctx.datastore.get_tag(tag_id)
        if tag:
            cat = ctx.datastore.get_category(tag.category)
            cat_name = cat.name if cat else "未知"
            table.add_row(str(idx), tag.name, f"{score:.2f}", cat_name)

    console.print(table)


@graph_group.command(name="cluster")
@pass_context
def cluster_analysis(ctx: Context):
    """聚类分析"""
    kg = KnowledgeGraph(ctx.datastore)
    kg.generate(mode="full")

    communities = kg.find_communities()

    console.print(f"[cyan]发现 {len(communities)} 个社区/聚类:[/cyan]\n")

    for comm_id, nodes in communities.items():
        # 统计社区中的节点类型
        tag_count = sum(1 for n in nodes if kg.graph.nodes[n].get("type") == "tag")
        file_count = sum(1 for n in nodes if kg.graph.nodes[n].get("type") == "file")

        console.print(f"[yellow]社区 {comm_id + 1}[/yellow] (节点: {len(nodes)}, 标签: {tag_count}, 文件: {file_count})")

        # 显示一些代表性节点
        for node_id in nodes[:5]:
            node_data = kg.graph.nodes[node_id]
            ntype = node_data.get("type", "unknown")
            name = node_data.get("name", "未知")
            console.print(f"  • [{ntype}] {name}")

        if len(nodes) > 5:
            console.print(f"  ... 还有 {len(nodes) - 5} 个节点")
        console.print("")


@graph_group.command(name="export")
@click.argument("output_file", type=click.Path())
@click.option("--format", "output_format", type=click.Choice(["json", "graphml"]), default="json", help="导出格式")
@pass_context
def export_graph(ctx: Context, output_file: str, output_format: str):
    """导出知识图谱"""
    kg = KnowledgeGraph(ctx.datastore)
    kg.generate(mode="full")

    output_path = Path(output_file)

    if output_format == "json":
        kg.save(str(output_path))
        console.print(f"[green]✓ 已导出为JSON: {output_path}[/green]")

    elif output_format == "graphml":
        import networkx as nx
        nx.write_graphml(kg.graph, str(output_path))
        console.print(f"[green]✓ 已导出为GraphML: {output_path}[/green]")
