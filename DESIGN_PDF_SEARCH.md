# PDF全文搜索设计文档

## 功能概述

为FileMap添加PDF文件的全文索引和搜索功能，支持中英文混合搜索。

## 技术方案

### 核心技术栈
- **PyPDF2** - PDF文本提取
- **Whoosh** - 全文搜索引擎（纯Python）
- **jieba** - 中文分词

### 架构设计

```
filemap/
├── search/
│   ├── __init__.py
│   ├── indexer.py          # 索引构建器
│   ├── searcher.py         # 搜索器
│   └── extractors/
│       ├── pdf_extractor.py    # PDF文本提取
│       ├── txt_extractor.py    # 纯文本提取
│       └── docx_extractor.py   # Word文档提取（可选）
```

## 功能列表

### 1. 索引管理
```bash
# 为文件创建全文索引
filemap index content <file_id>

# 批量索引所有PDF
filemap index content --all --type pdf

# 重建索引
filemap index rebuild

# 查看索引状态
filemap index status
```

### 2. 全文搜索
```bash
# 搜索内容
filemap search content "机器学习"

# 混合搜索（文件名 + 内容）
filemap search full "深度学习" --in name,content

# 高级搜索
filemap search content "neural network" --highlight --context 100
```

### 3. 交互式Shell增强
```bash
filemap> index 1              # 为选中文件创建索引
filemap> search content 深度学习  # 全文搜索
filemap> highlight            # 高亮显示搜索结果
```

## 数据模型

### 索引Schema
```python
from whoosh.fields import Schema, TEXT, ID, DATETIME, NUMERIC

schema = Schema(
    file_id=ID(stored=True, unique=True),
    filename=TEXT(stored=True),
    content=TEXT(stored=True, analyzer=ChineseAnalyzer()),  # 中文分析器
    path=TEXT(stored=True),
    page_count=NUMERIC(stored=True),
    indexed_at=DATETIME(stored=True),
)
```

### 文件模型扩展
```python
class File:
    ...
    indexed: bool = False           # 是否已索引
    index_version: str = ""         # 索引版本
    content_hash: str = ""          # 内容哈希
    page_count: int = 0             # 页数（PDF）
```

## 实现细节

### 1. PDF文本提取
```python
import PyPDF2

def extract_pdf_text(file_path: str) -> dict:
    """
    提取PDF文本
    返回: {
        'text': str,           # 全文
        'pages': List[str],    # 每页文本
        'page_count': int,     # 页数
        'metadata': dict       # PDF元数据
    }
    """
    with open(file_path, 'rb') as f:
        reader = PyPDF2.PdfReader(f)
        pages = []
        for page in reader.pages:
            pages.append(page.extract_text())

        return {
            'text': '\n'.join(pages),
            'pages': pages,
            'page_count': len(reader.pages),
            'metadata': reader.metadata
        }
```

### 2. 中文分词
```python
import jieba
from whoosh.analysis import Tokenizer, Token

class ChineseTokenizer(Tokenizer):
    """中文分词器"""
    def __call__(self, value, **kw):
        for word in jieba.cut_for_search(value):
            token = Token()
            token.text = word
            yield token
```

### 3. 索引构建
```python
from whoosh.index import create_in, open_dir

def build_index(file: File):
    """为文件构建索引"""
    # 提取文本
    text_data = extract_pdf_text(file.path)

    # 添加到索引
    writer = index.writer()
    writer.add_document(
        file_id=file.file_id,
        filename=file.name,
        content=text_data['text'],
        path=file.path,
        page_count=text_data['page_count'],
        indexed_at=datetime.now()
    )
    writer.commit()

    # 更新文件状态
    file.indexed = True
    file.page_count = text_data['page_count']
```

### 4. 全文搜索
```python
from whoosh.qparser import QueryParser, MultifieldParser

def search_content(query_string: str, limit: int = 20):
    """全文搜索"""
    with index.searcher() as searcher:
        # 多字段搜索
        parser = MultifieldParser(
            ["filename", "content"],
            schema=index.schema
        )
        query = parser.parse(query_string)

        # 执行搜索
        results = searcher.search(query, limit=limit)

        # 返回结果（带高亮）
        for hit in results:
            yield {
                'file_id': hit['file_id'],
                'filename': hit['filename'],
                'score': hit.score,
                'highlights': hit.highlights("content", top=3)
            }
```

## 性能优化

### 1. 增量索引
- 只索引新增和修改的文件
- 使用文件哈希检测内容变化

### 2. 异步索引
```python
# 后台异步索引
filemap index content --async
# 查看进度
filemap index progress
```

### 3. 索引压缩
- 定期优化索引
- 删除过期索引

## 使用场景

### 场景1：学术论文管理
```bash
# 索引所有论文
filemap add ~/Papers/*.pdf --tags 论文 --index-content

# 搜索特定主题
filemap search content "transformer attention mechanism"

# 查看搜索结果
filemap> search content "BERT"
Found 5 papers:
  1. [95%] bert_paper.pdf
     ...pre-training of deep bidirectional [Transformers]...

  2. [87%] attention_is_all.pdf
     ...scaled dot-product [attention]...
```

### 场景2：代码文档搜索
```bash
# 索引技术文档
filemap add ~/Docs/*.pdf --tags 文档 --index-content

# 搜索API用法
filemap search content "async/await syntax" --type pdf
```

### 场景3：个人知识库
```bash
# 混合搜索（文件名+内容）
filemap search full "深度学习" --fuzzy

# 查看搜索上下文
filemap search content "卷积神经网络" --context 200
```

## 命令行参数

### index命令
```
filemap index content <file_id|path>
  --all              索引所有文件
  --type TYPE        只索引特定类型（pdf/txt/docx）
  --async            后台异步索引
  --force            强制重新索引
  --verbose          显示详细进度
```

### search命令
```
filemap search content <query>
  --highlight        高亮显示匹配内容
  --context N        显示上下文字符数
  --fuzzy            模糊匹配
  --limit N          限制结果数量
  --page             显示匹配的页码
  --score            显示相关度分数
```

## 存储需求

- 索引大小约为原文件的30-50%
- 例如：100MB的PDF，索引约30-50MB
- 建议预留足够磁盘空间

## 多语言支持

### 中文
- 使用jieba分词
- 支持繁简转换

### 英文
- 使用Whoosh内置分析器
- 支持词干提取（stemming）

### 混合
- 自动识别中英文
- 分别处理

## 下一步计划

1. **Phase 1**: PDF文本提取和基础索引
2. **Phase 2**: 中文分词和搜索
3. **Phase 3**: 高级搜索（高亮、上下文）
4. **Phase 4**: 其他格式支持（Word、Markdown）
5. **Phase 5**: 性能优化和缓存

## 预计工作量

- PDF提取器: 0.5天
- Whoosh索引: 1天
- 中文分词: 0.5天
- CLI集成: 1天
- 交互式Shell集成: 0.5天
- 测试和优化: 1天

**总计: 4-5天**
