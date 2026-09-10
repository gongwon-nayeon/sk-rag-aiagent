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
    dataset_dir = BASE_DIR / "dataset"
    persist_directory = BASE_DIR / "chroma_db"
    # 01~04번이 쓰는 "ai_doc" 컬렉션과 구분되는 05 전용 컬렉션 (같은 chroma_db 디렉터리를 공유해도 충돌 없음)
    collection_name = "ai_doc_05_full_dataset"
    db_exists = persist_directory.is_dir() and any(persist_directory.iterdir())

    pdf_paths = sorted(dataset_dir.glob("*.pdf"))
    if not pdf_paths:
        raise FileNotFoundError(f"dataset 폴더에 PDF가 없습니다: {dataset_dir}")

    # PyMuPDF로 dataset 폴더의 모든 PDF를 로드 (재사용 시에도 parent page 원본 복원을 위해 필요)
    docs = []
    for pdf_path in pdf_paths:
        doc = fitz.open(pdf_path)
        for page_num in range(len(doc)):
            page = doc[page_num]
            text = page.get_text("text", sort=True)

            # Langchain Document 형식으로 변환
            docs.append(
                Document(
                    page_content=text,
                    metadata={
                        "source": pdf_path.name,
                        "page": page_num + 1  # 1부터 시작
                    }
                )
            )
        doc.close()

    print(f"PDF {len(pdf_paths)}개, 총 {len(docs)}페이지 로드 완료")

    # child_splitter 정의
    child_splitter = RecursiveCharacterTextSplitter(chunk_size=400, chunk_overlap=50)

    # 벡터스토어 생성 (기존 chroma_db가 있으면 그대로 로드, 없으면 새로 생성 후 저장)
    embeddings = OpenAIEmbeddings()
    vectorstore = Chroma(
        collection_name=collection_name,
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
        # 기존 컬렉션 재사용: 재임베딩 없이 doc_id -> 원본 페이지만 docstore에 복원
        # (여러 PDF의 페이지 번호가 겹칠 수 있으므로 파일명+페이지 조합으로 복원한다)
        print(f"기존 '{collection_name}' 컬렉션을 재사용합니다 (재임베딩 없음)...")
        existing = vectorstore._collection.get(include=["metadatas"])
        key_by_doc_id = {
            metadata["doc_id"]: (metadata["source"], metadata["page"])
            for metadata in existing["metadatas"]
        }
        doc_by_key = {(d.metadata["source"], d.metadata["page"]): d for d in docs}
        full_docs = [
            (doc_id, doc_by_key[key])
            for doc_id, key in key_by_doc_id.items()
            if key in doc_by_key
        ]
        docstore.mset(full_docs)
    else:
        # 문서 추가
        print(f"'{collection_name}' 컬렉션이 없어 새로 생성합니다. 문서를 벡터스토어에 추가 중...")
        parent_retriever.add_documents(docs)

    child_count = vectorstore._collection.count()
    parent_count = len(list(docstore.yield_keys()))
    print(f"child chunk 수: {child_count}, parent page 수: {parent_count}")

    # Retriever Tool 생성
    from langchain_core.prompts import PromptTemplate
    retriever_tool = create_retriever_tool(
        parent_retriever,
        "retrieve_AI_brief",
        "dataset 폴더의 AI 관련 문서 전체에서 정보를 검색하고 반환합니다. "
        "query 인자는 검색 엔진에 바로 입력할 핵심 키워드나 짧은 구/질문으로 작성하세요 "
        "(예: 'OpenAI ChatGPT 신규 기능'). 검색 방법이나 절차를 설명하는 문장을 넣지 마세요.",
        document_prompt=PromptTemplate.from_template(
        "{page_content} 파일명: {source} 문서 페이지: {page}"
    ),
    )

    return parent_retriever, retriever_tool
