"""主CLI入口"""
import click
from pathlib import Path

from filemap.utils.config import get_config, init_config
from filemap.storage.datastore import DataStore


# 全局上下文
class Context:
    """CLI上下文"""

    def __init__(self):
        self.config = None
        self.datastore = None


pass_context = click.make_pass_decorator(Context, ensure=True)


@click.group()
@click.version_option(version="0.1.0")
@pass_context
def cli(ctx: Context):
    """FileMap - 智能文件管理和知识图谱工具"""
    # 初始化配置
    ctx.config = get_config()
    # 初始化数据存储
    data_dir = ctx.config.get_data_dir()
    ctx.datastore = DataStore(data_dir)


@cli.command()
@click.option("--path", type=click.Path(), help="工作空间路径")
@pass_context
def init(ctx: Context, path: str):
    """初始化FileMap工作空间"""
    if path:
        workspace_path = Path(path).expanduser()
    else:
        workspace_path = Path.home() / ".filemap"

    workspace_path.mkdir(parents=True, exist_ok=True)

    # 创建必要的目录
    (workspace_path / "data").mkdir(exist_ok=True)
    (workspace_path / "managed").mkdir(exist_ok=True)
    (workspace_path / "backups").mkdir(exist_ok=True)
    (workspace_path / "logs").mkdir(exist_ok=True)

    # 初始化配置
    config_path = workspace_path / "config.yaml"
    config = init_config(config_path)

    # 设置路径
    config.set("storage.data_dir", str(workspace_path / "data"))
    config.set("workspace.managed_dir", str(workspace_path / "managed"))
    config.set("storage.backup_dir", str(workspace_path / "backups"))

    # 初始化数据存储（会创建默认类别）
    datastore = DataStore(workspace_path / "data")

    click.echo(f"✓ FileMap工作空间已初始化: {workspace_path}")
    click.echo(f"  - 数据目录: {workspace_path / 'data'}")
    click.echo(f"  - 管理目录: {workspace_path / 'managed'}")
    click.echo(f"  - 备份目录: {workspace_path / 'backups'}")
    click.echo(f"  - 配置文件: {config_path}")


# 导入子命令组
from filemap.cli import file_commands, tag_commands, category_commands, search_commands, graph_commands, stats_commands

cli.add_command(file_commands.file_group)
cli.add_command(tag_commands.tag_group)
cli.add_command(category_commands.category_group)
cli.add_command(search_commands.search_group)
cli.add_command(graph_commands.graph_group)
cli.add_command(stats_commands.stats_group)


if __name__ == "__main__":
    cli()
