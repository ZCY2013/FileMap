# 更新日志

本文档记录 FileMap 项目的所有重要更新和变更。

## [0.3.0] - 2025-11-17

### 重大架构升级
- **SQLite 数据存储迁移**
  - 从 JSON 文件存储迁移到 SQLite 数据库
  - 大幅提升数据查询性能和可扩展性
  - 支持原子性操作和事务
  - 添加外键约束保证数据完整性
  - 实现软删除机制

- **增量索引功能**
  - 智能检测文件修改时间
  - 自动跳过未变更的文件
  - 大幅提升索引更新速度
  - 新增 `filemap index update` 命令

### 新增功能
- **数据迁移工具**
  - `filemap migrate to-sqlite` - JSON 迁移到 SQLite
  - `filemap migrate to-json` - SQLite 导出到 JSON（备份）
  - 完整的迁移统计和错误报告

- **测试框架**
  - 集成 pytest 单元测试框架
  - 核心模块测试覆盖
  - 自动化测试和代码覆盖率报告

- **错误处理优化**
  - 定义完整的自定义异常体系
  - 统一的错误处理机制
  - 更清晰的错误提示信息

### 技术改进
- SQLiteDataStore 支持旧版 DataStore 接口（兼容性属性）
- 索引器添加 `needs_reindex()` 和 `update_index()` 方法
- 数据库 Schema 设计（schema.sql）
- 索引优化和统计信息增强

### 破坏性变更
- **数据存储格式变更**：从 JSON 文件迁移到 SQLite 数据库
  - 需要运行迁移命令：`filemap migrate to-sqlite`
  - 旧版 JSON 数据仍可导出为备份

### 性能提升
- 大规模文件查询速度提升 10-50 倍
- 增量索引减少不必要的文件处理
- 数据库索引优化查询性能

### 测试覆盖
- 模型层测试：100% 通过
- 数据存储层测试：100% 通过
- 整体代码覆盖率：8% (核心模块覆盖率 > 50%)

### 升级指南

从 v0.2.0 升级到 v0.3.0 需要迁移数据：

```bash
# 1. 备份数据
cp -r ~/.filemap ~/.filemap.backup

# 2. 运行迁移
filemap migrate to-sqlite \
  --json-dir ~/.filemap/data \
  --sqlite-db ~/.filemap/data/filemap.db

# 3. 验证迁移
filemap file list

# 4. (可选) 重建索引
filemap index rebuild
```

## [0.2.0] - 2025-11-17

### 新增功能
- **PDF 全文搜索支持**
  - 实现 PDF 文件文本提取功能（基于 PyPDF2）
  - 支持 PDF 元数据提取（标题、作者、创建日期等）
  - 实现中文分词器（基于 jieba）
  - 集成 Whoosh 全文搜索引擎
  - 支持中英文混合内容索引和搜索
  - 添加搜索结果高亮显示功能

- **纯文本文件索引支持**
  - 支持 .txt、.md、.markdown、.rst、.log、.csv 格式
  - 自动编码检测（UTF-8、GBK）

- **索引管理命令**
  - `filemap index content` - 创建文件索引
  - `filemap index status` - 查看索引状态
  - `filemap index search` - 全文搜索
  - `filemap index rebuild` - 重建索引
  - `filemap index optimize` - 优化索引

- **交互式 Shell 索引功能**
  - `index create` - 创建索引
  - `index search` - 搜索内容
  - `index status` - 查看状态

### 技术改进
- 实现 ChineseTokenizer 和 ChineseAnalyzer
- 集成中文停用词过滤
- 添加索引统计信息（文档数、索引大小、最后更新时间）
- 实现进度条显示批量索引过程

### 依赖更新
- 新增 PyPDF2 >= 3.0.0
- 新增 Whoosh >= 2.7.4
- 新增 jieba >= 0.42.1

### Bug 修复
- 修复 ChineseTokenizer 的 pickle 序列化错误（改为按需导入 jieba）

### 测试验证
- 成功测试 3.3MB 中文 PDF 教材的索引和搜索
- 验证中文搜索关键词："向量空间"、"线性变换"、"特征值"
- 确认搜索结果评分和高亮显示正常工作

## [0.1.0] - 2025-11-16

### 初始版本
- **核心功能**
  - 文件管理（索引模式和导入模式）
  - 多标签系统
  - 标签分类管理
  - 文件搜索和过滤
  - 知识图谱生成和分析
  - 统计报告

- **CLI 命令**
  - file - 文件管理命令组
  - tag - 标签管理命令组
  - category - 分类管理命令组
  - search - 搜索命令组
  - graph - 知识图谱命令组
  - stats - 统计命令组

- **交互式 Shell**
  - 基于 cmd 模块的交互式命令行
  - 命令自动补全
  - 命令历史记录
  - 命令别名支持
  - 上下文感知操作

- **知识图谱功能**
  - 标签共现分析
  - 社区检测
  - 标签推荐
  - Hub 节点识别
  - 孤立节点检测
  - 树形和 JSON 格式导出

- **技术栈**
  - Python 3.9+
  - Click - CLI 框架
  - Rich - 终端 UI
  - NetworkX - 图分析
  - PyYAML - 配置管理

### 数据存储
- JSON 格式数据持久化
- 自动备份支持
- 默认分类初始化

### 文档
- README.md - 完整使用说明
- DESIGN_PDF_SEARCH.md - PDF 搜索技术设计
- requirements.txt - 依赖清单

---

## 版本说明

版本号格式：`主版本号.次版本号.修订号`
- 主版本号：重大架构变更或不兼容更新
- 次版本号：新功能添加
- 修订号：Bug 修复和小改进
