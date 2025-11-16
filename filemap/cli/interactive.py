"""交互式CLI Shell"""
import cmd
import shlex
from pathlib import Path
from typing import List, Optional
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich.tree import Tree

from filemap.utils.config import get_config
from filemap.storage.datastore import DataStore
from filemap.core.models import File, Tag, Category
from filemap.graph.knowledge_graph import KnowledgeGraph


console = Console()


class FileMapShell(cmd.Cmd):
    """FileMap交互式Shell"""

    intro = """
╔═══════════════════════════════════════════════════════════════╗
║           FileMap Interactive Shell v0.1.0                    ║
║           智能文件管理和知识图谱工具                            ║
╠═══════════════════════════════════════════════════════════════╣
║  输入 'help' 查看可用命令    输入 'quit' 或 'exit' 退出        ║
║  输入 'tutorial' 查看快速入门指南                              ║
╚═══════════════════════════════════════════════════════════════╝
"""
    prompt = "\033[1;36mfilemap>\033[0m "

    def __init__(self):
        super().__init__()
        # 初始化配置和数据存储
        self.config = get_config()
        self.datastore = DataStore(self.config.get_data_dir())
        self.knowledge_graph = KnowledgeGraph(self.datastore)

        # 上下文状态
        self.current_files: List[File] = []  # 当前查询结果
        self.selected_file: Optional[File] = None  # 选中的文件
        self.last_search: str = ""  # 上次搜索条件

        # 命令别名
        self.aliases = {
            "ls": "list",
            "ll": "list",
            "q": "quit",
            "?": "help",
            "s": "search",
            "t": "tag",
            "f": "file",
            "g": "graph",
        }

    def precmd(self, line: str) -> str:
        """预处理命令，处理别名"""
        if not line:
            return line

        parts = line.split()
        if parts and parts[0] in self.aliases:
            parts[0] = self.aliases[parts[0]]
            return " ".join(parts)
        return line

    def emptyline(self) -> bool:
        """空行不重复上一条命令"""
        return False

    def default(self, line: str) -> None:
        """未知命令处理"""
        console.print(f"[red]未知命令: {line}[/red]")
        console.print("输入 'help' 查看可用命令")

    # ==================== 文件管理命令 ====================

    def do_list(self, arg: str) -> None:
        """列出文件 [--tags TAG1,TAG2] [--limit N]"""
        args = self._parse_args(arg)
        tags = args.get("tags", "")
        limit = int(args.get("limit", 20))

        tag_ids = None
        if tags:
            tag_names = [t.strip() for t in tags.split(",")]
            tag_ids = []
            for name in tag_names:
                tag = self.datastore.get_tag_by_name(name)
                if tag:
                    tag_ids.append(tag.tag_id)

        files = self.datastore.list_files(tag_ids)[:limit]
        self.current_files = files

        if not files:
            console.print("[yellow]没有找到文件[/yellow]")
            return

        self._display_files(files)

    def do_add(self, arg: str) -> None:
        """添加文件: add <路径> [--tags TAG1,TAG2] [--notes 备注]"""
        if not arg:
            console.print("[red]请指定文件路径[/red]")
            return

        args = self._parse_args(arg)
        if not args.get("_positional"):
            console.print("[red]请指定文件路径[/red]")
            return

        file_path = Path(args["_positional"][0]).expanduser().absolute()
        if not file_path.exists():
            console.print(f"[red]文件不存在: {file_path}[/red]")
            return

        # 检查是否已存在
        existing = self.datastore.get_file_by_path(str(file_path))
        if existing:
            console.print(f"[yellow]文件已存在: {file_path}[/yellow]")
            return

        # 创建文件对象
        try:
            file_obj = File.from_path(str(file_path), managed=False)
        except Exception as e:
            console.print(f"[red]错误: {e}[/red]")
            return

        # 添加标签
        tags = args.get("tags", "")
        if tags:
            tag_names = [t.strip() for t in tags.split(",")]
            for tag_name in tag_names:
                tag = self.datastore.get_tag_by_name(tag_name)
                if tag:
                    file_obj.add_tag(tag.tag_id)
                    tag.usage_count += 1
                    self.datastore.update_tag(tag)
                else:
                    console.print(f"[yellow]标签不存在: {tag_name}[/yellow]")

        # 添加备注
        if "notes" in args:
            file_obj.notes = args["notes"]

        self.datastore.add_file(file_obj)
        console.print(f"[green]✓ 文件已添加: {file_obj.name}[/green]")
        console.print(f"  ID: {file_obj.file_id[:8]}")

    def do_show(self, arg: str) -> None:
        """显示文件详情: show <文件ID或序号>"""
        if not arg:
            if self.selected_file:
                self._show_file_detail(self.selected_file)
            else:
                console.print("[yellow]请指定文件ID或先选择文件[/yellow]")
            return

        file = self._get_file_by_arg(arg)
        if file:
            self.selected_file = file
            self._show_file_detail(file)

    def do_select(self, arg: str) -> None:
        """选择文件: select <序号>（基于当前列表）"""
        if not arg:
            console.print("[yellow]请指定文件序号[/yellow]")
            return

        try:
            idx = int(arg) - 1
            if 0 <= idx < len(self.current_files):
                self.selected_file = self.current_files[idx]
                console.print(f"[green]已选择: {self.selected_file.name}[/green]")
            else:
                console.print("[red]序号超出范围[/red]")
        except ValueError:
            console.print("[red]请输入有效的数字[/red]")

    def do_remove(self, arg: str) -> None:
        """删除文件: remove <文件ID或序号>"""
        file = self._get_file_by_arg(arg)
        if not file:
            return

        confirm = input(f"确定要删除 '{file.name}' 吗？(y/N): ")
        if confirm.lower() == "y":
            self.datastore.remove_file(file.file_id)
            console.print(f"[green]✓ 已删除: {file.name}[/green]")
            if self.selected_file and self.selected_file.file_id == file.file_id:
                self.selected_file = None

    # ==================== 标签管理命令 ====================

    def do_tag(self, arg: str) -> None:
        """标签操作: tag <子命令> [参数]
        子命令:
          list              - 列出所有标签
          create <名称>     - 创建新标签
          add <标签名>      - 为选中文件添加标签
          remove <标签名>   - 从选中文件移除标签
          show <标签名>     - 显示标签详情
        """
        if not arg:
            self._tag_list()
            return

        parts = arg.split(None, 1)
        subcmd = parts[0]
        subarg = parts[1] if len(parts) > 1 else ""

        if subcmd == "list":
            self._tag_list()
        elif subcmd == "create":
            self._tag_create(subarg)
        elif subcmd == "add":
            self._tag_add(subarg)
        elif subcmd == "remove":
            self._tag_remove(subarg)
        elif subcmd == "show":
            self._tag_show(subarg)
        else:
            console.print(f"[red]未知的标签子命令: {subcmd}[/red]")

    def _tag_list(self) -> None:
        """列出所有标签"""
        tags = sorted(self.datastore.tags.values(), key=lambda t: t.usage_count, reverse=True)

        table = Table(title="标签列表")
        table.add_column("#", style="dim")
        table.add_column("标签名", style="cyan")
        table.add_column("类别", style="yellow")
        table.add_column("使用次数", style="green", justify="right")

        for idx, tag in enumerate(tags[:20], 1):
            cat = self.datastore.get_category(tag.category)
            cat_name = cat.name if cat else "未知"
            table.add_row(str(idx), tag.name, cat_name, str(tag.usage_count))

        console.print(table)

    def _tag_create(self, name: str) -> None:
        """创建标签"""
        if not name:
            console.print("[yellow]请指定标签名称[/yellow]")
            return

        existing = self.datastore.get_tag_by_name(name)
        if existing:
            console.print(f"[yellow]标签已存在: {name}[/yellow]")
            return

        tag = Tag(name=name)
        self.datastore.add_tag(tag)
        console.print(f"[green]✓ 标签已创建: {name}[/green]")

    def _tag_add(self, tag_name: str) -> None:
        """为选中文件添加标签"""
        if not self.selected_file:
            console.print("[yellow]请先选择文件 (使用 'select' 命令)[/yellow]")
            return

        if not tag_name:
            console.print("[yellow]请指定标签名称[/yellow]")
            return

        tag = self.datastore.get_tag_by_name(tag_name)
        if not tag:
            # 询问是否创建
            create = input(f"标签 '{tag_name}' 不存在，是否创建？(y/N): ")
            if create.lower() == "y":
                tag = Tag(name=tag_name)
                self.datastore.add_tag(tag)
            else:
                return

        if not self.selected_file.has_tag(tag.tag_id):
            self.selected_file.add_tag(tag.tag_id)
            tag.usage_count += 1
            self.datastore.update_tag(tag)
            self.datastore.update_file(self.selected_file)
            console.print(f"[green]✓ 已添加标签 '{tag_name}' 到 {self.selected_file.name}[/green]")
        else:
            console.print(f"[yellow]文件已有标签: {tag_name}[/yellow]")

    def _tag_remove(self, tag_name: str) -> None:
        """从选中文件移除标签"""
        if not self.selected_file:
            console.print("[yellow]请先选择文件[/yellow]")
            return

        tag = self.datastore.get_tag_by_name(tag_name)
        if not tag:
            console.print(f"[red]标签不存在: {tag_name}[/red]")
            return

        if self.selected_file.has_tag(tag.tag_id):
            self.selected_file.remove_tag(tag.tag_id)
            tag.usage_count = max(0, tag.usage_count - 1)
            self.datastore.update_tag(tag)
            self.datastore.update_file(self.selected_file)
            console.print(f"[green]✓ 已移除标签 '{tag_name}'[/green]")
        else:
            console.print(f"[yellow]文件没有标签: {tag_name}[/yellow]")

    def _tag_show(self, name: str) -> None:
        """显示标签详情"""
        tag = self.datastore.get_tag_by_name(name)
        if not tag:
            console.print(f"[red]标签不存在: {name}[/red]")
            return

        cat = self.datastore.get_category(tag.category)
        cat_name = cat.name if cat else "未知"

        panel = Panel(
            f"ID: {tag.tag_id}\n"
            f"名称: {tag.name}\n"
            f"类别: {cat_name}\n"
            f"使用次数: {tag.usage_count}\n"
            f"描述: {tag.description or '无'}",
            title=f"标签: {tag.name}",
            border_style="cyan",
        )
        console.print(panel)

    # ==================== 搜索命令 ====================

    def do_search(self, arg: str) -> None:
        """搜索文件: search <关键词> 或 search --tags TAG1,TAG2"""
        if not arg:
            console.print("[yellow]请输入搜索条件[/yellow]")
            return

        args = self._parse_args(arg)
        files = list(self.datastore.files.values())

        # 按标签搜索
        if "tags" in args:
            tag_names = [t.strip() for t in args["tags"].split(",")]
            tag_ids = []
            for name in tag_names:
                tag = self.datastore.get_tag_by_name(name)
                if tag:
                    tag_ids.append(tag.tag_id)

            if tag_ids:
                files = [f for f in files if any(tid in f.tags for tid in tag_ids)]

        # 按关键词搜索
        if args.get("_positional"):
            keyword = " ".join(args["_positional"]).lower()
            files = [f for f in files if keyword in f.name.lower()]

        self.current_files = files
        self.last_search = arg

        if files:
            console.print(f"[green]找到 {len(files)} 个文件:[/green]")
            self._display_files(files[:20])
        else:
            console.print("[yellow]没有找到匹配的文件[/yellow]")

    def do_filter(self, arg: str) -> None:
        """快速过滤当前列表: filter <关键词>"""
        if not self.current_files:
            console.print("[yellow]当前没有文件列表，请先执行 list 或 search[/yellow]")
            return

        if not arg:
            console.print("[yellow]请输入过滤关键词[/yellow]")
            return

        keyword = arg.lower()
        filtered = [f for f in self.current_files if keyword in f.name.lower()]
        self.current_files = filtered

        if filtered:
            console.print(f"[green]过滤后剩余 {len(filtered)} 个文件:[/green]")
            self._display_files(filtered[:20])
        else:
            console.print("[yellow]没有匹配的文件[/yellow]")

    # ==================== 知识图谱命令 ====================

    def do_graph(self, arg: str) -> None:
        """知识图谱: graph <子命令>
        子命令:
          show      - 显示图谱概览
          hubs      - 显示核心节点
          tree      - 树状展示标签关系
          recommend - 为选中文件推荐标签
        """
        if not arg:
            arg = "show"

        parts = arg.split()
        subcmd = parts[0]

        if subcmd == "show":
            self._graph_show()
        elif subcmd == "hubs":
            self._graph_hubs()
        elif subcmd == "tree":
            self._graph_tree()
        elif subcmd == "recommend":
            self._graph_recommend()
        else:
            console.print(f"[red]未知的图谱子命令: {subcmd}[/red]")

    def _graph_show(self) -> None:
        """显示图谱概览"""
        console.print("[cyan]正在生成知识图谱...[/cyan]")
        self.knowledge_graph.generate(mode="tags")

        stats = self.knowledge_graph.get_stats()
        text = self.knowledge_graph.visualize_text()

        console.print(text)
        console.print(f"\n[dim]密度: {stats['density']:.4f}, 连通分量: {stats['connected_components']}[/dim]")

    def _graph_hubs(self) -> None:
        """显示核心节点"""
        self.knowledge_graph.generate(mode="tags")
        hubs = self.knowledge_graph.find_hubs(top_n=10)

        table = Table(title="核心标签 (连接最多)")
        table.add_column("排名", style="cyan")
        table.add_column("标签", style="white")
        table.add_column("连接数", style="green", justify="right")

        for idx, (node_id, degree) in enumerate(hubs, 1):
            node_data = self.knowledge_graph.graph.nodes[node_id]
            name = node_data.get("name", "未知")
            table.add_row(str(idx), name, str(degree))

        console.print(table)

    def _graph_tree(self) -> None:
        """树状展示标签关系"""
        self.knowledge_graph.generate(mode="tags")

        # 构建树
        tree = Tree("📊 知识图谱")

        # 按类别分组
        categories = {}
        for tag in self.datastore.tags.values():
            cat = self.datastore.get_category(tag.category)
            cat_name = cat.name if cat else "uncategorized"
            if cat_name not in categories:
                categories[cat_name] = []
            categories[cat_name].append(tag)

        for cat_name, tags in categories.items():
            cat_branch = tree.add(f"[yellow]{cat_name}[/yellow]")
            for tag in sorted(tags, key=lambda t: t.usage_count, reverse=True)[:10]:
                # 获取相关标签
                related = []
                if tag.tag_id in self.knowledge_graph.graph:
                    neighbors = list(self.knowledge_graph.graph.neighbors(tag.tag_id))[:3]
                    for n_id in neighbors:
                        n_data = self.knowledge_graph.graph.nodes[n_id]
                        related.append(n_data.get("name", ""))

                related_str = f" → {', '.join(related)}" if related else ""
                cat_branch.add(f"[cyan]{tag.name}[/cyan] ({tag.usage_count}){related_str}")

        console.print(tree)

    def _graph_recommend(self) -> None:
        """为选中文件推荐标签"""
        if not self.selected_file:
            console.print("[yellow]请先选择文件[/yellow]")
            return

        self.knowledge_graph.generate(mode="tags")
        recommendations = self.knowledge_graph.recommend_tags(self.selected_file.file_id, top_n=5)

        if not recommendations:
            console.print("[yellow]暂无推荐[/yellow]")
            return

        console.print(f"为 [cyan]{self.selected_file.name}[/cyan] 推荐的标签:")
        for tag_id, score in recommendations:
            tag = self.datastore.get_tag(tag_id)
            if tag:
                console.print(f"  • {tag.name} (分数: {score:.2f})")

    # ==================== 统计命令 ====================

    def do_stats(self, arg: str) -> None:
        """显示统计信息"""
        stats = self.datastore.get_stats()

        panel = Panel(
            f"文件总数: {stats['total_files']}\n"
            f"总大小: {self._format_size(stats['total_size'])}\n"
            f"标签总数: {stats['total_tags']}\n"
            f"类别总数: {stats['total_categories']}\n"
            f"有标签文件: {stats['files_with_tags']}\n"
            f"无标签文件: {stats['files_without_tags']}",
            title="📊 统计信息",
            border_style="green",
        )
        console.print(panel)

    # ==================== 系统命令 ====================

    def do_clear(self, arg: str) -> None:
        """清屏"""
        console.clear()

    def do_tutorial(self, arg: str) -> None:
        """显示快速入门指南"""
        tutorial = """
[bold cyan]FileMap 快速入门指南[/bold cyan]

[yellow]1. 添加文件[/yellow]
   > add ~/Documents/paper.pdf --tags 机器学习,Python

[yellow]2. 列出文件[/yellow]
   > list
   > list --tags Python

[yellow]3. 搜索文件[/yellow]
   > search paper
   > search --tags 机器学习

[yellow]4. 选择文件[/yellow]
   > select 1          # 选择列表中的第1个文件
   > show              # 查看详情

[yellow]5. 管理标签[/yellow]
   > tag list          # 列出所有标签
   > tag create 新标签  # 创建标签
   > tag add Python    # 为选中文件添加标签
   > tag remove Python # 移除标签

[yellow]6. 知识图谱[/yellow]
   > graph show        # 显示图谱
   > graph hubs        # 核心节点
   > graph tree        # 树状展示
   > graph recommend   # 推荐标签

[yellow]7. 快捷别名[/yellow]
   ls = list, s = search, t = tag, g = graph, q = quit

[dim]提示: 使用 Tab 键可以自动补全命令和参数[/dim]
"""
        console.print(tutorial)

    def do_quit(self, arg: str) -> bool:
        """退出交互式Shell"""
        console.print("[cyan]再见！[/cyan]")
        return True

    def do_exit(self, arg: str) -> bool:
        """退出交互式Shell"""
        return self.do_quit(arg)

    def do_EOF(self, arg: str) -> bool:
        """处理Ctrl+D"""
        console.print()
        return self.do_quit(arg)

    # ==================== 自动补全 ====================

    def complete_tag(self, text: str, line: str, begidx: int, endidx: int) -> List[str]:
        """标签命令的自动补全"""
        subcmds = ["list", "create", "add", "remove", "show"]
        parts = line.split()

        if len(parts) == 2:
            # 补全子命令
            return [s for s in subcmds if s.startswith(text)]
        elif len(parts) >= 3:
            # 补全标签名
            tag_names = [t.name for t in self.datastore.tags.values()]
            return [t for t in tag_names if t.startswith(text)]

        return []

    def complete_search(self, text: str, line: str, begidx: int, endidx: int) -> List[str]:
        """搜索命令的自动补全"""
        if "--tags" in line:
            # 补全标签名
            tag_names = [t.name for t in self.datastore.tags.values()]
            return [t for t in tag_names if t.startswith(text)]
        return ["--tags"]

    def complete_graph(self, text: str, line: str, begidx: int, endidx: int) -> List[str]:
        """图谱命令的自动补全"""
        subcmds = ["show", "hubs", "tree", "recommend"]
        return [s for s in subcmds if s.startswith(text)]

    def complete_show(self, text: str, line: str, begidx: int, endidx: int) -> List[str]:
        """show命令的自动补全（文件ID）"""
        if self.current_files:
            # 返回文件ID的前缀
            ids = [f.file_id[:8] for f in self.current_files]
            return [i for i in ids if i.startswith(text)]
        return []

    def complete_select(self, text: str, line: str, begidx: int, endidx: int) -> List[str]:
        """select命令的自动补全（序号）"""
        if self.current_files:
            return [str(i) for i in range(1, len(self.current_files) + 1) if str(i).startswith(text)]
        return []

    # ==================== 辅助方法 ====================

    def _parse_args(self, arg_string: str) -> dict:
        """解析命令参数"""
        result = {"_positional": []}
        if not arg_string:
            return result

        try:
            parts = shlex.split(arg_string)
        except ValueError:
            parts = arg_string.split()

        i = 0
        while i < len(parts):
            if parts[i].startswith("--"):
                key = parts[i][2:]
                if i + 1 < len(parts) and not parts[i + 1].startswith("--"):
                    result[key] = parts[i + 1]
                    i += 2
                else:
                    result[key] = True
                    i += 1
            else:
                result["_positional"].append(parts[i])
                i += 1

        return result

    def _get_file_by_arg(self, arg: str) -> Optional[File]:
        """根据参数获取文件（支持ID或序号）"""
        if not arg:
            return None

        # 尝试作为序号
        try:
            idx = int(arg) - 1
            if 0 <= idx < len(self.current_files):
                return self.current_files[idx]
        except ValueError:
            pass

        # 尝试作为文件ID
        file = self.datastore.get_file(arg)
        if file:
            return file

        # 尝试匹配ID前缀
        for f in self.datastore.files.values():
            if f.file_id.startswith(arg):
                return f

        console.print(f"[red]找不到文件: {arg}[/red]")
        return None

    def _display_files(self, files: List[File]) -> None:
        """显示文件列表"""
        table = Table()
        table.add_column("#", style="dim", width=3)
        table.add_column("ID", style="cyan", width=10)
        table.add_column("文件名", style="white")
        table.add_column("大小", style="yellow", justify="right")
        table.add_column("标签", style="green")

        for idx, file in enumerate(files, 1):
            # 获取标签名
            tag_names = []
            for tag_id in file.tags[:3]:
                tag = self.datastore.get_tag(tag_id)
                if tag:
                    tag_names.append(tag.name)
            tags_str = ", ".join(tag_names)
            if len(file.tags) > 3:
                tags_str += f" +{len(file.tags) - 3}"

            table.add_row(
                str(idx),
                file.file_id[:8],
                file.name[:40],
                self._format_size(file.size),
                tags_str or "[dim]无[/dim]",
            )

        console.print(table)

    def _show_file_detail(self, file: File) -> None:
        """显示文件详情"""
        tag_names = []
        for tag_id in file.tags:
            tag = self.datastore.get_tag(tag_id)
            if tag:
                tag_names.append(tag.name)

        content = f"""[bold]ID:[/bold] {file.file_id}
[bold]名称:[/bold] {file.name}
[bold]路径:[/bold] {file.path}
[bold]大小:[/bold] {self._format_size(file.size)}
[bold]类型:[/bold] {file.mime_type}
[bold]添加时间:[/bold] {file.added_at.strftime('%Y-%m-%d %H:%M')}
[bold]修改时间:[/bold] {file.modified_at.strftime('%Y-%m-%d %H:%M') if file.modified_at else '未知'}
[bold]标签:[/bold] {', '.join(tag_names) or '无'}
[bold]备注:[/bold] {file.notes or '无'}"""

        panel = Panel(content, title=f"📄 {file.name}", border_style="blue")
        console.print(panel)

    def _format_size(self, size: int) -> str:
        """格式化文件大小"""
        for unit in ["B", "KB", "MB", "GB", "TB"]:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} PB"


def run_interactive_shell():
    """运行交互式Shell"""
    shell = FileMapShell()
    try:
        shell.cmdloop()
    except KeyboardInterrupt:
        console.print("\n[cyan]再见！[/cyan]")
