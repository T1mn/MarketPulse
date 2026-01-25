# RAG 模块使用指北

基于 ChromaDB + Sentence-Transformers 的检索增强生成模块，用于知识库问答。

## 核心组件

| 组件 | 用途 |
|------|------|
| `RAGRetriever` | 检索入口，构建上下文 |
| `VectorStore` | ChromaDB 向量存储 |
| `EmbeddingModel` | 文本嵌入（默认 m3e-base） |
| `DocumentLoader` | 加载 JSON/Markdown/文本 |

## 快速开始

```python
from core.rag import retriever, DocumentLoader

# 1. 添加单条知识
await retriever.add_knowledge(
    content="如何充值？支持银行卡、支付宝、微信支付。",
    metadata={"category": "faq", "source": "customer_service"}
)

# 2. 检索相关内容
results = await retriever.retrieve("怎么充钱", top_k=3)
for r in results:
    print(f"[{r.score:.2f}] {r.content[:50]}...")

# 3. 构建 RAG 上下文（用于 LLM 输入）
context = await retriever.build_context(
    query="充值方式",
    intent="customer_service",
    max_length=2000
)
```

## 常见场景

### 批量导入 FAQ

```python
from core.rag import retriever, DocumentLoader

# 从 JSON 加载
docs = DocumentLoader.load_json("data/knowledge_base/faq/zh.json")
count = await retriever.batch_add_knowledge(docs)
print(f"导入 {count} 条知识")
```

### 从目录加载文档

```python
# 递归加载 .json/.md/.txt 文件
docs = DocumentLoader.load_directory(
    "data/knowledge_base",
    file_types=[".json", ".md"],
    recursive=True
)
await retriever.batch_add_knowledge(docs)
```

### 按类别过滤检索

```python
# 只检索 FAQ 类文档
results = await retriever.retrieve(
    query="手续费多少",
    filters={"category": "faq"},
    top_k=5
)
```

## 配置项

在 `config/chatbot_config.py` 中调整：

```python
retrieval_top_k: int = 5          # 检索数量
similarity_threshold: float = 0.7  # 相似度阈值
```

向量数据库路径：`config/base.py` → `VECTOR_DB_PATH`

## 文件结构

```
core/rag/
├── __init__.py        # 导出入口
├── retriever.py       # RAGRetriever 检索器
├── vector_store.py    # VectorStore 向量存储
├── embeddings.py      # EmbeddingModel 嵌入模型
└── document_loader.py # DocumentLoader 文档加载
```
