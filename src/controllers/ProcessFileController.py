from .BaseController import BaseController
from .ProjectController import ProjectController  

import os 

from langchain_community.document_loaders import TextLoader
from langchain_community.document_loaders import PyMuPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from models import ProcessingEnum

from typing import List


class ProcessFileController(BaseController):
    def __init__(self, project_id: str):
        super().__init__()

        self.project_id = project_id
        self.project_path = ProjectController().get_project_path(project_id=project_id)
    
    def get_file_extension(self, file_name: str):
        return os.path.splitext(file_name)[-1]
    
    def get_file_loader(self, file_name: str):
        """Return the appropriate LangChain loader based on file extension."""
        file_extension = self.get_file_extension(file_name)
        file_path = os.path.join(self.project_path, file_name)

        if file_extension == ProcessingEnum.TXT.value:
            return TextLoader(file_path, encoding="utf-8")
        elif file_extension == ProcessingEnum.PDF.value:
            return PyMuPDFLoader(file_path)
        else:
            raise ValueError(f"Unsupported file type: {file_extension}")

    def get_file_content(self, file_name: str):
        """Load the file and return a list of LangChain Document objects (one per page)."""
        loader = self.get_file_loader(file_name)
        return loader.load()

    def process_file_content(
        self,
        file_content: list,
        chunk_size: int,
        chunk_overlap: int,
    ) -> List[Document]:
        """
        Split each loaded page/document into smaller chunks using
        RecursiveCharacterTextSplitter, preserving per-page metadata.

        Args:
            file_content:   List of LangChain Document objects returned by loader.load()
            chunk_size:     Maximum number of characters per chunk.
            chunk_overlap:  Number of characters to overlap between consecutive chunks
                            (prevents context from being cut at chunk boundaries).
        """
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            # Tries these separators in order; falls back to the next if the
            # text still exceeds chunk_size after splitting on the current one.
            separators=["\n\n", "\n", ". ", " ", ""],
            length_function=len,
        )

        chunks: List[Document] = []

        for page_doc in file_content:
            # split_text returns plain strings; we re-attach the source metadata
            page_chunks = text_splitter.split_text(page_doc.page_content)

            for chunk_text in page_chunks:
                if not chunk_text.strip():
                    continue  # skip empty chunks

                chunks.append(Document(
                    page_content=chunk_text.strip(),
                    # Each chunk carries the metadata of the page it came from,
                    # NOT just metadatas[0] for every chunk.
                    metadata=page_doc.metadata,
                ))

        return chunks