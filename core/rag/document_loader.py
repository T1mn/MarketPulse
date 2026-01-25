"""文档加载器"""
import logging
import json
from typing import List, Dict, Any, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class DocumentLoader:
    """
    文档加载器

    支持从多种来源加载知识：
    1. JSON 文件（FAQ, 知识库）
    2. Markdown 文件
    3. 文本文件
    4. 数据库（TODO）
    5. API（TODO）
    """

    @staticmethod
    def load_json(file_path: str) -> List[Dict[str, Any]]:
        """
        加载 JSON 文件

        Args:
            file_path: 文件路径

        Returns:
            List[Dict]: 文档列表
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            if isinstance(data, list):
                documents = data
            elif isinstance(data, dict):
                # 如果是字典，转换为列表
                documents = [data]
            else:
                logger.error(f"Invalid JSON format: {file_path}")
                return []

            logger.info(f"✅ Loaded {len(documents)} documents from {file_path}")
            return documents

        except FileNotFoundError:
            logger.error(f"File not found: {file_path}")
            return []
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error in {file_path}: {e}")
            return []
        except Exception as e:
            logger.error(f"Error loading {file_path}: {e}")
            return []

    @staticmethod
    def load_markdown(file_path: str, split_by_heading: bool = True) -> List[Dict[str, Any]]:
        """
        加载 Markdown 文件

        Args:
            file_path: 文件路径
            split_by_heading: 是否按标题分割

        Returns:
            List[Dict]: 文档列表
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            if split_by_heading:
                # 按一级标题分割
                sections = content.split('\n# ')
                documents = []

                for i, section in enumerate(sections):
                    if i == 0 and not section.startswith('# '):
                        # 第一个不是标题的部分，跳过或作为前言
                        if section.strip():
                            documents.append({
                                'content': section.strip(),
                                'metadata': {
                                    'source': file_path,
                                    'section': 'intro',
                                    'type': 'markdown'
                                }
                            })
                    else:
                        # 提取标题和内容
                        lines = section.split('\n', 1)
                        title = lines[0].strip() if i == 0 else f"# {lines[0].strip()}"
                        body = lines[1] if len(lines) > 1 else ""

                        documents.append({
                            'content': f"{title}\n\n{body}".strip(),
                            'metadata': {
                                'source': file_path,
                                'title': title.replace('# ', ''),
                                'type': 'markdown'
                            }
                        })

                logger.info(f"✅ Loaded {len(documents)} sections from {file_path}")
                return documents

            else:
                # 整个文件作为一个文档
                return [{
                    'content': content,
                    'metadata': {
                        'source': file_path,
                        'type': 'markdown'
                    }
                }]

        except Exception as e:
            logger.error(f"Error loading markdown {file_path}: {e}")
            return []

    @staticmethod
    def load_text(file_path: str, chunk_size: int = 1000) -> List[Dict[str, Any]]:
        """
        加载文本文件并分块

        Args:
            file_path: 文件路径
            chunk_size: 块大小（字符数）

        Returns:
            List[Dict]: 文档列表
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # 分块
            chunks = []
            for i in range(0, len(content), chunk_size):
                chunk = content[i:i + chunk_size]
                chunks.append({
                    'content': chunk,
                    'metadata': {
                        'source': file_path,
                        'chunk_index': i // chunk_size,
                        'type': 'text'
                    }
                })

            logger.info(f"✅ Loaded {len(chunks)} chunks from {file_path}")
            return chunks

        except Exception as e:
            logger.error(f"Error loading text {file_path}: {e}")
            return []

    @staticmethod
    def load_directory(
        directory: str,
        file_types: List[str] = None,
        recursive: bool = True
    ) -> List[Dict[str, Any]]:
        """
        加载目录中的所有文档

        Args:
            directory: 目录路径
            file_types: 文件类型列表（如 ['.json', '.md']）
            recursive: 是否递归子目录

        Returns:
            List[Dict]: 文档列表
        """
        if file_types is None:
            file_types = ['.json', '.md', '.txt']

        path = Path(directory)
        if not path.exists():
            logger.error(f"Directory not found: {directory}")
            return []

        documents = []

        # 获取文件列表
        if recursive:
            files = [f for f in path.rglob('*') if f.suffix in file_types]
        else:
            files = [f for f in path.glob('*') if f.suffix in file_types]

        for file_path in files:
            file_str = str(file_path)

            if file_path.suffix == '.json':
                docs = DocumentLoader.load_json(file_str)
            elif file_path.suffix == '.md':
                docs = DocumentLoader.load_markdown(file_str)
            elif file_path.suffix == '.txt':
                docs = DocumentLoader.load_text(file_str)
            else:
                continue

            documents.extend(docs)

        logger.info(f"✅ Loaded {len(documents)} documents from directory: {directory}")
        return documents
