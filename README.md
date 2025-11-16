# FileMap - 智能文件管理和知识图谱工具

FileMap 是一个基于标签的命令行文件管理系统，支持知识图谱生成和分析，帮助你更好地组织和理解文件之间的关系。

## 核心特性

- **灵活的标签系统**：为文件打多个标签，支持标签分类和分组
- **混合管理模式**：既可以索引现有文件，也可以将文件导入集中管理
- **知识图谱**：自动分析标签关系，生成可视化知识图谱
- **智能推荐**：基于标签关联推荐相关标签和文件
- **强大搜索**：支持标签组合查询、文件属性过滤
- **统计分析**：多维度统计和报告生成

## 快速开始

### 安装

```bash
# 克隆仓库
git clone https://github.com/ZCY2013/FileMap.git
cd FileMap

# 安装依赖
pip install -r requirements.txt

# 安装工具
pip install -e .
```

### 初始化工作空间

```bash
# 初始化默认工作空间 (~/.filemap)
filemap init

# 或指定自定义路径
filemap init --path /path/to/workspace
```

### 基本使用

#### 1. 创建标签和类别

```bash
# 创建类别
filemap category create "项目" --description "工作项目相关" --exclusive

# 创建标签
filemap tag create "机器学习" --category topic --description "机器学习相关资料"
filemap tag create "Python" --category type
filemap tag create "重要" --category priority
```

#### 2. 添加文件

```bash
# 索引模式（文件保持原位置）
filemap file add /path/to/document.pdf --index --tags "机器学习,Python"

# 导入模式（复制到管理目录）
filemap file add /path/to/code.py --import --tags "Python,重要" --notes "核心代码"
```

#### 3. 列出和搜索文件

```bash
# 列出所有文件
filemap file list

# 按标签过滤
filemap file list --tags "Python,机器学习"

# 高级搜索
filemap search find "document" --tags "机器学习 AND Python"
filemap search find --size ">1MB" --type "pdf"
filemap search find --date "2024-01-01..2024-12-31"
```

#### 4. 生成知识图谱

```bash
# 生成标签关系图谱
filemap graph generate --mode tags

# 显示图谱
filemap graph show --format text

# 查看核心标签
filemap graph hubs --top 10

# 发现孤立标签
filemap graph orphans --type tag

# 为文件推荐标签
filemap graph recommend <file_id> --top 5

# 社区聚类分析
filemap graph cluster
```

#### 5. 统计和报告

```bash
# 查看总体统计
filemap stats summary

# 标签使用统计
filemap stats tags --top 20

# 文件分布
filemap stats distribution --by type

# 时间趋势
filemap stats timeline --period month

# 生成报告
filemap stats report --format markdown --output report.md
```

### 6. 交互式Shell

```bash
# 启动交互式Shell
filemap shell
# 或
filemap interactive

# 在Shell中使用简化命令
filemap> list                    # 列出文件
filemap> search paper            # 搜索文件
filemap> select 1                # 选择第1个文件
filemap> tag add Python          # 为选中文件添加标签
filemap> graph tree              # 树状展示知识图谱
filemap> graph recommend         # 推荐标签
filemap> tutorial                # 查看快速入门
filemap> quit                    # 退出
```

**交互式Shell特性：**
- 命令自动补全（Tab键）
- 命令历史（上下键）
- 快捷别名（ls=list, s=search, t=tag, g=graph, q=quit）
- 上下文感知（选中文件后可以直接操作）
- 树状知识图谱展示
- 实时标签推荐

## 命令参考

### 文件管理

```bash
filemap file add <path>              # 添加文件
filemap file list                    # 列出文件
filemap file show <file_id>          # 显示文件详情
filemap file remove <file_id>        # 删除文件
filemap file update <file_id>        # 更新文件信息
```

### 标签管理

```bash
filemap tag create <name>            # 创建标签
filemap tag list                     # 列出标签
filemap tag show <name>              # 显示标签详情
filemap tag delete <name>            # 删除标签
filemap tag add <file_id> <tags>     # 为文件添加标签
filemap tag remove <file_id> <tags>  # 从文件移除标签
filemap tag stats                    # 标签统计
```

### 类别管理

```bash
filemap category create <name>       # 创建类别
filemap category list                # 列出类别
filemap category show <name>         # 显示类别详情
filemap category delete <name>       # 删除类别
```

### 搜索

```bash
filemap search find [keyword]        # 搜索文件
  --tags "tag1 AND tag2"            # 标签查询
  --name "*.pdf"                    # 文件名模式
  --type "application/pdf"          # MIME类型
  --size ">1MB"                     # 大小条件
  --date "2024-01-01..2024-12-31"   # 日期范围
```

### 知识图谱

```bash
filemap graph generate               # 生成知识图谱
filemap graph show                   # 显示图谱
filemap graph hubs                   # 核心节点
filemap graph orphans                # 孤立节点
filemap graph recommend <file_id>    # 推荐标签
filemap graph cluster                # 聚类分析
filemap graph export <file>          # 导出图谱
```

### 统计

```bash
filemap stats summary                # 总体统计
filemap stats tags                   # 标签统计
filemap stats distribution           # 分布统计
filemap stats timeline               # 时间趋势
filemap stats report                 # 生成报告
```

## 使用场景

### 场景1：研究人员管理论文

```bash
# 1. 创建学术相关的类别和标签
filemap category create "研究领域" --description "研究方向分类"
filemap tag create "深度学习" --category "研究领域"
filemap tag create "计算机视觉" --category "研究领域"
filemap tag create "已读" --category status
filemap tag create "待读" --category status

# 2. 索引论文目录
filemap file add ~/Papers/paper1.pdf --index --tags "深度学习,计算机视觉,已读"
filemap file add ~/Papers/paper2.pdf --index --tags "深度学习,待读"

# 3. 搜索特定主题的已读论文
filemap search find --tags "深度学习 AND 已读"

# 4. 生成研究主题关系图
filemap graph generate --mode tags
filemap graph show

# 5. 发现研究盲点
filemap graph orphans --type tag
```

### 场景2：程序员管理代码和资源

```bash
# 1. 创建技术栈标签
filemap tag create "Python" --category type
filemap tag create "JavaScript" --category type
filemap tag create "前端" --category topic
filemap tag create "后端" --category topic

# 2. 导入代码文件到管理目录
filemap file add ~/code/auth.py --import --tags "Python,后端,重要"
filemap file add ~/code/ui.js --import --tags "JavaScript,前端"

# 3. 批量查找后端代码
filemap search find --tags "后端"

# 4. 分析技术栈分布
filemap stats distribution --by category

# 5. 生成知识图谱发现代码关联
filemap graph generate --mode files
filemap graph cluster
```

### 场景3：知识管理和学习

```bash
# 1. 建立知识体系标签
filemap category create "知识领域" --description "学习的知识分类"
filemap tag create "编程" --category "知识领域"
filemap tag create "设计" --category "知识领域"
filemap tag create "商业" --category "知识领域"

# 2. 索引学习资料
filemap file add ~/Books/python_book.pdf --index --tags "编程,Python"
filemap file add ~/Notes/design_principles.md --index --tags "设计"

# 3. 生成知识图谱
filemap graph generate --mode full

# 4. 发现知识连接
filemap graph hubs --top 10

# 5. 推荐相关学习资料
filemap graph recommend <file_id>
```

## 项目结构

```
filemap/
├── filemap/
│   ├── __init__.py
│   ├── core/              # 核心数据模型
│   │   └── models.py      # File, Tag, Category 模型
│   ├── storage/           # 数据存储
│   │   └── datastore.py   # JSON 持久化
│   ├── utils/             # 工具函数
│   │   └── config.py      # 配置管理
│   ├── graph/             # 知识图谱
│   │   └── knowledge_graph.py
│   └── cli/               # 命令行界面
│       ├── main.py
│       ├── file_commands.py
│       ├── tag_commands.py
│       ├── category_commands.py
│       ├── search_commands.py
│       ├── graph_commands.py
│       └── stats_commands.py
├── tests/                 # 测试
├── docs/                  # 文档
├── requirements.txt       # 依赖
├── setup.py              # 安装配置
└── README.md             # 说明文档
```

## 配置

配置文件位于 `~/.filemap/config.yaml`：

```yaml
workspace:
  managed_dir: ~/.filemap/managed  # 导入模式的文件存储目录
  index_dirs: []                   # 索引目录列表

storage:
  data_dir: ~/.filemap/data        # 数据目录
  backup_enabled: true             # 启用备份
  backup_dir: ~/.filemap/backups   # 备份目录

defaults:
  default_category: uncategorized  # 默认类别
  auto_tag: false                  # 自动标签

visualization:
  graph_engine: text               # 图谱引擎
  max_nodes: 100                   # 最大节点数
```

## 技术栈

- **Python 3.9+**
- **Click** - CLI 框架
- **Rich** - 终端美化
- **NetworkX** - 图谱分析
- **PyYAML** - 配置管理
- **Pandas** - 数据分析

## 开发计划

### 已完成 ✅
- [x] 核心数据模型
- [x] 文件管理功能
- [x] 标签和类别系统
- [x] 搜索和过滤
- [x] 知识图谱生成
- [x] 统计和报告
- [x] 交互式 Shell（命令补全、历史记录、树状图谱展示）

### 计划中 🚧
- [ ] 文件系统监控（watchdog）
- [ ] 全文搜索
- [ ] 图形化可视化（Graphviz）
- [ ] Web 界面
- [ ] 插件系统

## 贡献

欢迎提交 Issue 和 Pull Request！

## 许可证

MIT License

## 作者

**ZCY2013**

## 联系方式

- 问题反馈：[GitHub Issues](https://github.com/ZCY2013/FileMap/issues)
- 邮箱：zcy32897629@126.com

---

**FileMap** - 让文件管理更智能，让知识关联更清晰
