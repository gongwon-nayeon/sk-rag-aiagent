from pathlib import Path

import fitz
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma
from langchain_classic.retrievers import ParentDocumentRetriever
from langchain_core.stores import InMemoryByteStore
from langchain_core.tools import create_retriever_tool

BASE_DIR = Path(__file__).resolve().parent.parent


def setup_retriever():
    file_path = BASE_DIR / "dataset" / "(PDF)SPRi AI Brief 2026년 8월호.pdf"
    persist_directory = BASE_DIR / "chroma_db"
    db_exists = persist_directory.is_dir() and any(persist_directory.iterdir())

    # PyMuPDF로 문서 로드 (재사용 시에도 parent page 원본 복원을 위해 필요)
    doc = fitz.open(file_path)
    docs = []

    for page_num in range(len(doc)):
        page = doc[page_num]
        text = page.get_text("text", sort=True)

        # Langchain Document 형식으로 변환
        docs.append(
            Document(
                page_content=text,
                metadata={
                    "source": str(file_path),
                    "page": page_num + 1  # 1부터 시작
                }
            )
        )

    doc.close()
    print(f"총 {len(docs)}페이지 로드 완료")

    # child_splitter 정의
    child_splitter = RecursiveCharacterTextSplitter(chunk_size=400, chunk_overlap=50)

    # 벡터스토어 생성 (기존 chroma_db가 있으면 그대로 로드, 없으면 새로 생성 후 저장)
    embeddings = OpenAIEmbeddings()
    vectorstore = Chroma(
        collection_name="ai_doc",
        embedding_function=embeddings,
        persist_directory=str(persist_directory)
    )

    # docstore 생성 (InMemoryByteStore)
    docstore = InMemoryByteStore()

    # ParentDocumentRetriever 생성
    parent_retriever = ParentDocumentRetriever(
        vectorstore=vectorstore,
        docstore=docstore,
        child_splitter=child_splitter,
        parent_splitter=None,  # 페이지 = parent
        search_kwargs={"k": 2}
    )

    if db_exists and vectorstore._collection.count() > 0:
        # 기존 chroma_db 재사용: 재임베딩 없이 doc_id -> 원본 페이지만 docstore에 복원
        print("기존 chroma_db를 재사용합니다 (재임베딩 없음)...")
        existing = vectorstore._collection.get(include=["metadatas"])
        page_by_doc_id = {
            metadata["doc_id"]: metadata["page"] for metadata in existing["metadatas"]
        }
        page_to_doc = {d.metadata["page"]: d for d in docs}
        full_docs = [
            (doc_id, page_to_doc[page])
            for doc_id, page in page_by_doc_id.items()
            if page in page_to_doc
        ]
        docstore.mset(full_docs)
    else:
        # 문서 추가
        print("chroma_db가 없어 새로 생성합니다. 문서를 벡터스토어에 추가 중...")
        parent_retriever.add_documents(docs)

    child_count = vectorstore._collection.count()
    parent_count = len(list(docstore.yield_keys()))
    print(f"child chunk 수: {child_count}, parent page 수: {parent_count}")

    # Retriever Tool 생성
    from langchain_core.prompts import PromptTemplate
    retriever_tool = create_retriever_tool(
        parent_retriever,
        "retrieve_AI_brief",
        "AI 기술 관련 정보를 SPRi AI Brief에서 검색하고 반환합니다.",
        document_prompt=PromptTemplate.from_template(
        "{page_content} 파일명: {source} 문서 페이지: {page}"
    ),
    )

    return parent_retriever, retriever_tool
