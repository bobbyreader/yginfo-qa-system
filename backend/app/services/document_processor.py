import re
from pathlib import Path
from typing import List, Tuple
from langchain_community.document_loaders import PyPDFLoader, UnstructuredWordDocumentLoader

class DocumentProcessor:
    """文档解析与分块处理器"""

    CHUNK_SIZE = 500  # 每段500字
    CHUNK_OVERLAP = 50  # 重叠50字

    async def process(self, file_path: str, file_type: str) -> List[Tuple[str, dict]]:
        """处理文档，返回分段列表[(文本, 元数据), ...]"""
        if file_type == "pdf":
            text = await self._extract_pdf(file_path)
        elif file_type in ["doc", "docx"]:
            text = await self._extract_docx(file_path)
        else:
            raise ValueError(f"Unsupported file type: {file_type}")

        return self._chunk_text(text, {"source": file_path})

    async def _extract_pdf(self, file_path: str) -> str:
        loader = PyPDFLoader(file_path)
        pages = await loader.aload()
        return "\n".join([p.page_content for p in pages])

    async def _extract_docx(self, file_path: str) -> str:
        loader = UnstructuredWordDocumentLoader(file_path)
        docs = await loader.aload()
        return "\n".join([d.page_content for d in docs])

    def _chunk_text(self, text: str, metadata: dict) -> List[Tuple[str, dict]]:
        """重叠滑动窗口分块"""
        chunks = []
        start = 0
        text_length = len(text)

        while start < text_length:
            end = start + self.CHUNK_SIZE
            chunk = text[start:end]

            # 清理空白字符
            chunk = re.sub(r'\s+', ' ', chunk).strip()
            if chunk:
                chunks.append((chunk, {**metadata, "start_char": start}))

            start += self.CHUNK_SIZE - self.CHUNK_OVERLAP

        return chunks
