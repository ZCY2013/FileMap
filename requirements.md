# FileMap - 智能文件管理工具需求说明文档

## 1. 项目概述

### 1.1 项目名称
FileMap - 基于标签的命令行文件管理和知识图谱工具

### 1.2 项目背景
随着数字文件数量的爆炸式增长，传统的文件夹层级结构已经无法满足现代知识管理的需求。FileMap旨在提供一种基于标签（Tag）的灵活文件组织方式，并通过标签间的关系自动生成知识图谱，帮助用户更好地理解和管理文件之间的逻辑关系。

### 1.3 项目目标
- 提供灵活的多标签文件管理系统
- 支持混合模式：既可索引现有文件，也可集中管理文件
- 通过标签分组和关系构建知识图谱
- 提供强大的搜索、过滤和批量操作能力
- 帮助用户发现文件间的隐藏关联

### 1.4 目标用户
- 研究人员和学者（管理大量论文、笔记）
- 程序员（管理代码片段、文档、资源文件）
- 内容创作者（管理素材、草稿、参考资料）
- 知识工作者（需要建立个人知识库）

---

## 2. 核心功能需求

### 2.1 文件管理功能

#### 2.1.1 混合文件管理模式
- **索引模式**：
  - 扫描并索引指定目录下的文件
  - 文件保持在原始位置不变
  - 记录文件路径、元数据和标签信息
  - 监控文件变化（移动、重命名、删除）并更新索引

- **导入模式**：
  - 将文件导入到工具管理的专用目录
  - 支持复制或移动两种导入方式
  - 按照规则组织文件存储结构（如按日期、类型等）

- **模式切换**：
  - 支持将索引文件转为导入文件
  - 支持导出管理文件到指定位置

#### 2.1.2 文件基本操作
- 添加文件（索引或导入）
- 移动文件
- 复制文件
- 删除文件（软删除/硬删除）
- 重命名文件
- 查看文件详细信息
- 打开文件（调用系统默认程序）

### 2.2 标签管理功能

#### 2.2.1 标签基本操作
- 创建标签
- 删除标签
- 重命名标签
- 合并标签
- 为文件添加单个或多个标签
- 从文件移除标签
- 查看所有标签列表
- 查看标签使用统计

#### 2.2.2 标签分组/类别系统
- **标签类别定义**：
  - 支持自定义标签类别（维度）
  - 预设常用类别：
    - `type`（类型）：文档、图片、视频、代码等
    - `status`（状态）：待处理、进行中、已完成等
    - `priority`（优先级）：高、中、低
    - `topic`（主题）：项目相关、学习资料、个人等
    - `source`（来源）：书籍、网络、课程等

- **类别属性**：
  - 类别名称和描述
  - 类别下的标签是否互斥（一个文件在该类别下只能有一个标签）
  - 类别的颜色标识
  - 类别优先级（显示顺序）

- **标签归属**：
  - 每个标签必须属于一个类别
  - 支持将标签重新分配到其他类别
  - 支持创建未分类标签（属于默认的`uncategorized`类别）

#### 2.2.3 标签关系
虽然主要使用分组/类别系统，但也支持以下基础关系：
- **相关标签**：标记哪些标签经常一起使用
- **标签别名**：为标签设置别名，搜索时可以匹配

### 2.3 搜索和过滤功能

#### 2.3.1 基础搜索
- 按文件名搜索（支持通配符和正则表达式）
- 按标签搜索
- 按文件类型搜索
- 按日期范围搜索（创建日期、修改日期、添加日期）
- 按文件大小搜索

#### 2.3.2 高级搜索
- **标签组合查询**：
  - AND：同时包含多个标签
  - OR：包含任一标签
  - NOT：排除某些标签
  - 支持复杂布尔表达式：`(tag1 AND tag2) OR (tag3 AND NOT tag4)`

- **跨类别查询**：
  - 按多个类别维度组合查询
  - 例如：`type:文档 AND status:已完成 AND priority:高`

- **全文搜索**（可选）：
  - 搜索文件内容（文本文件）
  - 搜索文件元数据（EXIF、ID3等）

#### 2.3.3 过滤和排序
- 过滤条件持久化（保存常用查询）
- 多字段排序（名称、大小、日期等）
- 搜索结果导出

### 2.4 批量操作功能

- 批量添加标签
- 批量移除标签
- 批量移动文件
- 批量复制文件
- 批量删除文件
- 批量重命名（支持模式匹配）
- 基于搜索结果的批量操作

### 2.5 知识图谱功能

#### 2.5.1 图谱生成
- **基于标签共现**：
  - 分析哪些标签经常一起出现
  - 计算标签间的关联强度
  - 生成标签关系网络

- **基于文件关系**：
  - 识别具有相似标签组合的文件集群
  - 发现文件间的隐含关联

- **基于类别维度**：
  - 多维度分析文件分布
  - 生成类别间的关系图

#### 2.5.2 图谱可视化
- **文本模式**：
  - ASCII艺术图形展示
  - 树状结构展示
  - 表格展示关联度

- **图形模式**（可选，需要额外库）：
  - 生成网络图（GraphViz、Matplotlib等）
  - 导出为图片格式（PNG、SVG）
  - 交互式HTML可视化

#### 2.5.3 逻辑梳理功能
- **发现孤立节点**：找出很少使用或未关联的标签
- **识别核心标签**：找出连接最多文件的关键标签
- **聚类分析**：将相似的文件自动分组
- **关系推荐**：
  - 建议可能相关的标签
  - 建议文件可能缺失的标签
  - 建议可以合并的重复标签
- **时间演化**：分析标签和文件关系随时间的变化

### 2.6 统计和报告功能

#### 2.6.1 统计信息
- 文件总数和总大小
- 各类别下的文件分布
- 标签使用频率排行
- 文件类型分布
- 时间维度统计（按月/周添加的文件）
- 标签覆盖率（有标签vs无标签的文件比例）

#### 2.6.2 报告生成
- 生成文本格式报告
- 生成Markdown格式报告
- 生成HTML格式报告
- 导出统计数据为CSV/JSON

---

## 3. 数据模型设计

### 3.1 文件（File）
```yaml
file_id: string          # 唯一标识符（UUID）
name: string             # 文件名
path: string             # 文件完整路径
managed: boolean         # 是否为导入管理模式（true）或索引模式（false）
size: integer            # 文件大小（字节）
mime_type: string        # MIME类型
hash: string             # 文件哈希值（用于检测重复）
created_at: datetime     # 创建时间
modified_at: datetime    # 最后修改时间
added_at: datetime       # 添加到系统的时间
last_accessed: datetime  # 最后访问时间
tags: list[string]       # 关联的标签ID列表
metadata: dict           # 额外元数据（可扩展）
notes: string            # 用户备注
```

### 3.2 标签（Tag）
```yaml
tag_id: string           # 唯一标识符（UUID）
name: string             # 标签名称（唯一）
category: string         # 所属类别ID
description: string      # 标签描述
color: string            # 颜色标识（十六进制）
aliases: list[string]    # 别名列表
created_at: datetime     # 创建时间
usage_count: integer     # 使用次数（缓存字段）
related_tags: list       # 相关标签列表
  - tag_id: string
    strength: float      # 关联强度（0-1）
```

### 3.3 类别（Category）
```yaml
category_id: string      # 唯一标识符
name: string             # 类别名称（唯一）
description: string      # 类别描述
mutually_exclusive: bool # 该类别下的标签是否互斥
color: string            # 类别颜色
icon: string             # 图标（emoji或字符）
priority: integer        # 显示优先级
created_at: datetime     # 创建时间
```

### 3.4 知识图谱（Knowledge Graph）
```yaml
graph_id: string         # 图谱ID
generated_at: datetime   # 生成时间
nodes: list              # 节点列表
  - id: string           # 节点ID（标签ID或文件ID）
    type: string         # 节点类型（tag/file）
    label: string        # 显示名称
    properties: dict     # 节点属性
edges: list              # 边列表
  - source: string       # 源节点ID
    target: string       # 目标节点ID
    weight: float        # 边的权重
    type: string         # 关系类型
```

### 3.5 配置（Config）
```yaml
workspace:
  managed_dir: string    # 导入模式的文件存储目录
  index_dirs: list       # 索引模式监控的目录列表

storage:
  data_file: string      # 主数据文件路径
  backup_enabled: bool   # 是否启用备份
  backup_dir: string     # 备份目录

defaults:
  default_category: string  # 默认类别
  auto_tag: bool         # 是否根据文件类型自动打标签

visualization:
  graph_engine: string   # 图谱渲染引擎（text/graphviz/matplotlib）
  max_nodes: integer     # 可视化最大节点数
```

---

## 4. 命令行接口设计

### 4.1 设计原则
- 简洁直观的命令结构
- 支持交互式和非交互式两种模式
- 提供丰富的参数和选项
- 输出格式可配置（文本、JSON、表格）

### 4.2 主命令结构
```bash
filemap <command> [subcommand] [options] [arguments]
```

### 4.3 文件管理命令

```bash
# 添加文件
filemap add <file_path> [--index|--import] [--tags tag1,tag2] [--notes "备注"]
filemap add --scan <directory> [--recursive] [--index|--import]

# 列出文件
filemap list [--tags tag1,tag2] [--format table|json|simple] [--sort name|size|date]
filemap ls -t "tag1 AND tag2" -f table

# 显示文件详情
filemap show <file_id|file_name>
filemap info <file_id>

# 移动文件
filemap move <file_id> <new_path>
filemap mv <file_id> <new_path>

# 复制文件
filemap copy <file_id> <dest_path>
filemap cp <file_id> <dest_path>

# 删除文件
filemap remove <file_id> [--soft|--hard]
filemap rm <file_id> -f  # 硬删除

# 打开文件
filemap open <file_id>

# 重命名文件
filemap rename <file_id> <new_name>

# 批量操作
filemap batch --query "tag1 AND tag2" --action "add-tag:urgent"
filemap batch --ids file1,file2,file3 --action "move:/new/path"
```

### 4.4 标签管理命令

```bash
# 创建标签
filemap tag create <tag_name> [--category category_name] [--description "..."] [--color "#FF0000"]

# 列出所有标签
filemap tag list [--category category_name] [--sort name|usage]
filemap tag ls -c type

# 删除标签
filemap tag delete <tag_name> [--force]
filemap tag rm <tag_name>

# 重命名标签
filemap tag rename <old_name> <new_name>

# 合并标签
filemap tag merge <tag1> <tag2> --into <target_tag>

# 为文件添加标签
filemap tag add <file_id> <tag1> [tag2 tag3...]
filemap tag <file_id> +tag1 +tag2

# 从文件移除标签
filemap tag remove <file_id> <tag1> [tag2...]
filemap tag <file_id> -tag1 -tag2

# 查看标签详情
filemap tag show <tag_name>

# 标签统计
filemap tag stats [--category category_name]
```

### 4.5 类别管理命令

```bash
# 创建类别
filemap category create <category_name> [--description "..."] [--exclusive]
filemap cat create status --exclusive

# 列出类别
filemap category list
filemap cat ls

# 删除类别
filemap category delete <category_name>

# 修改类别
filemap category edit <category_name> [--description "..."] [--exclusive true|false]

# 查看类别详情
filemap category show <category_name>
```

### 4.6 搜索命令

```bash
# 基础搜索
filemap search <keyword> [--in name|content|tags]
filemap search "项目" --in name

# 标签搜索
filemap search --tags "tag1 AND tag2"
filemap search -t "(tag1 OR tag2) AND NOT tag3"

# 高级搜索
filemap search --query "type:文档 AND status:已完成" --size ">1MB" --date "2024-01-01..2024-12-31"

# 保存搜索
filemap search --tags "urgent AND todo" --save "待办事项"

# 使用保存的搜索
filemap search --load "待办事项"

# 列出保存的搜索
filemap search --list-saved
```

### 4.7 知识图谱命令

```bash
# 生成知识图谱
filemap graph generate [--mode tags|files|full] [--min-weight 0.1]

# 显示图谱
filemap graph show [--format text|ascii|json] [--output file.png]

# 分析标签关系
filemap graph analyze tags [--top 10]

# 文件聚类
filemap graph cluster [--method kmeans|hierarchical] [--clusters 5]

# 推荐相关标签
filemap graph recommend <file_id>
filemap graph suggest-tags <file_id>

# 发现孤立标签
filemap graph orphans [--tags|--files]

# 识别核心标签
filemap graph hubs [--top 10]

# 导出图谱
filemap graph export <output_file> [--format json|graphml|dot]
```

### 4.8 统计报告命令

```bash
# 查看统计信息
filemap stats [--category category_name]

# 生成报告
filemap report [--format text|markdown|html] [--output report.md]

# 标签使用排行
filemap stats tags [--top 20]

# 文件分布
filemap stats distribution [--by type|category|date]

# 时间趋势
filemap stats timeline [--period day|week|month]

# 导出数据
filemap export <output_file> [--format csv|json]
```

### 4.9 系统管理命令

```bash
# 初始化工作空间
filemap init [--path /path/to/workspace]

# 配置管理
filemap config set <key> <value>
filemap config get <key>
filemap config list

# 索引维护
filemap index rebuild
filemap index update
filemap index clean  # 清理已删除文件的索引

# 备份恢复
filemap backup create [--output backup.zip]
filemap backup restore <backup_file>

# 数据库优化
filemap optimize

# 显示帮助
filemap help [command]
filemap --help
```

### 4.10 交互式模式

```bash
# 进入交互式shell
filemap interactive
filemap shell

# 在交互模式下可以直接输入命令，无需filemap前缀
> add /path/to/file --tags work,important
> search -t work
> graph show
> exit
```

---

## 5. 技术需求

### 5.1 开发语言
- **Python 3.9+**：主要开发语言

### 5.2 核心依赖库
- **Click** 或 **Typer**：命令行界面框架
- **Rich**：终端美化输出（表格、进度条、颜色）
- **PyYAML** 或 **Toml**：配置文件解析
- **pathlib**：文件路径处理
- **hashlib**：文件哈希计算
- **watchdog**：文件系统监控（索引模式）
- **NetworkX**：图谱生成和分析
- **pandas**：数据分析和统计
- **python-magic** 或 **mimetypes**：文件类型识别

### 5.3 可选依赖
- **Graphviz** / **pydot**：图谱可视化
- **matplotlib** / **plotly**：数据可视化
- **whoosh** 或 **tantivy**：全文搜索
- **Jinja2**：HTML报告模板
- **prompt_toolkit**：交互式shell增强

### 5.4 数据存储
- **主数据文件**：JSON或YAML格式
  - `filemap.json`：文件和标签数据
  - `categories.json`：类别定义
  - `config.json`：配置信息
  - `graph.json`：知识图谱缓存

- **文件组织**：
  ```
  ~/.filemap/
  ├── config.yaml          # 配置文件
  ├── data/
  │   ├── files.json       # 文件数据
  │   ├── tags.json        # 标签数据
  │   ├── categories.json  # 类别数据
  │   └── graph.json       # 图谱缓存
  ├── managed/             # 导入模式的文件存储
  │   ├── 2024/
  │   ├── 2025/
  │   └── ...
  ├── backups/             # 备份目录
  └── logs/                # 日志文件
  ```

### 5.5 性能要求
- 支持至少10,000个文件的管理
- 搜索响应时间 < 1秒（10,000文件规模）
- 图谱生成时间 < 5秒（1,000标签，5,000文件）
- 内存占用 < 200MB（正常使用）

---

## 6. 非功能性需求

### 6.1 可用性
- 提供详细的帮助文档和示例
- 错误信息清晰明确，提供解决建议
- 支持命令自动补全（bash/zsh）
- 提供交互式向导（初次使用）

### 6.2 可靠性
- 数据自动备份（可配置）
- 操作日志记录
- 危险操作需确认（删除、批量操作等）
- 数据完整性校验

### 6.3 可维护性
- 模块化设计，高内聚低耦合
- 完善的代码注释和文档
- 单元测试覆盖率 > 80%
- 遵循PEP 8代码规范

### 6.4 可扩展性
- 插件系统（未来）
- 自定义元数据字段
- 可配置的文件类型规则
- 支持自定义报告模板

### 6.5 兼容性
- 支持主流操作系统（Windows、macOS、Linux）
- Python 3.9+
- 数据格式向后兼容

---

## 7. 实施计划

### 7.1 第一阶段：核心功能（MVP）
- [ ] 项目初始化和配置系统
- [ ] 文件索引功能
- [ ] 基础标签管理（创建、删除、添加到文件）
- [ ] 类别系统
- [ ] 简单搜索（按标签、文件名）
- [ ] 基础CLI命令

### 7.2 第二阶段：增强功能
- [ ] 文件导入管理模式
- [ ] 高级搜索（布尔表达式、多维度）
- [ ] 批量操作
- [ ] 文件系统监控（watchdog）
- [ ] 统计和报告功能
- [ ] 数据备份恢复

### 7.3 第三阶段：知识图谱
- [ ] 标签关系分析
- [ ] 知识图谱生成
- [ ] 文本模式可视化
- [ ] 聚类分析
- [ ] 推荐系统
- [ ] 孤立节点和核心标签识别

### 7.4 第四阶段：优化和扩展
- [ ] 图形化可视化（Graphviz、HTML）
- [ ] 全文搜索
- [ ] 交互式shell模式
- [ ] 性能优化
- [ ] 插件系统
- [ ] Web界面（可选）

---

## 8. 风险和限制

### 8.1 技术风险
- 大规模文件处理的性能问题
- 跨平台文件路径处理复杂性
- 文件移动后索引失效问题

### 8.2 缓解措施
- 使用增量索引和缓存机制
- 使用pathlib确保跨平台兼容
- 实现文件哈希追踪和路径自动更新

### 8.3 已知限制
- JSON存储在超大规模（10万+文件）时性能受限
- 图谱可视化在终端的表现有限
- 全文搜索需要额外索引，增加存储开销

---

## 9. 成功标准

### 9.1 功能完整性
- 所有核心功能按需求实现
- 通过所有测试用例
- 支持文档完整

### 9.2 性能指标
- 满足第5.5节性能要求
- 无内存泄漏
- 启动时间 < 500ms

### 9.3 用户体验
- 命令直观易用，符合Unix哲学
- 错误处理友好
- 文档清晰完整

### 9.4 代码质量
- 测试覆盖率 > 80%
- 无严重bug
- 代码可维护性评分 > B（通过代码质量工具评估）

---

## 10. 附录

### 10.1 术语表
- **索引模式**：仅记录文件元数据，文件保持在原位置
- **导入模式**：将文件复制/移动到工具管理的目录
- **标签类别**：标签的分类维度，如类型、状态等
- **知识图谱**：基于标签和文件关系生成的网络结构
- **节点**：图谱中的实体（标签或文件）
- **边**：图谱中节点间的关系

### 10.2 参考资料
- [TagSpaces](https://www.tagspaces.org/) - 文件标签管理工具
- [Obsidian](https://obsidian.md/) - 知识图谱笔记软件
- [NetworkX Documentation](https://networkx.org/) - 图论库
- [Click Documentation](https://click.palletsprojects.com/) - CLI框架

### 10.3 示例用例

#### 用例1：研究人员管理论文
```bash
# 索引论文目录
filemap add --scan ~/Papers --recursive --index

# 创建类别和标签
filemap category create topic --description "研究主题"
filemap tag create "机器学习" --category topic
filemap tag create "深度学习" --category topic
filemap tag create "已读" --category status

# 为论文打标签
filemap tag add paper123.pdf "机器学习" "深度学习" "已读"

# 查找特定主题的已读论文
filemap search -t "机器学习 AND 已读"

# 生成研究主题关系图
filemap graph generate --mode tags
filemap graph show
```

#### 用例2：程序员管理代码片段
```bash
# 导入代码片段
filemap add ~/snippets/auth.py --import --tags "Python,认证,后端"

# 批量标记前端代码
filemap batch --query "type:代码 AND name:*.js" --action "add-tag:前端"

# 查找所有Python认证相关代码
filemap search -t "Python AND 认证"

# 分析代码片段的主题分布
filemap graph cluster --method kmeans --clusters 5
filemap stats distribution --by topic
```

#### 用例3：发现知识盲点
```bash
# 生成完整知识图谱
filemap graph generate --mode full

# 找出孤立的标签（可能被遗忘的主题）
filemap graph orphans --tags

# 识别核心知识领域
filemap graph hubs --top 10

# 获取推荐阅读（基于标签关联）
filemap graph recommend --tags "机器学习"
```

---

## 变更记录

| 版本 | 日期 | 修改内容 | 作者 |
|------|------|----------|------|
| 1.0 | 2025-11-16 | 初始版本 | Claude |

---

**文档状态**：待审核
**下一步行动**：用户审核和反馈，确认需求后进入设计阶段
