# 更新日志

本文档记录 FileMap 项目的所有重要更新和变更。

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
