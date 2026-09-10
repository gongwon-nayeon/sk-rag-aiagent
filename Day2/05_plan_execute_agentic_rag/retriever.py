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
    # k=2는 "전수 검색/전체 정리" 같은 넓은 범위의 질문에서 페이지가 거의 누락되어
    # 답변이 부실해지는 원인이었으므로, 회수율을 높이기 위해 k를 늘린다.
    parent_retriever = ParentDocumentRetriever(
        vectorstore=vectorstore,
        docstore=docstore,
        child_splitter=child_splitter,
        parent_splitter=None,  # 페이지 = parent
        search_kwargs={"k": 6}
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
        "이 검색은 문서 제목이나 파일명이 아니라 각 페이지 내용(문장)에 대한 벡터 유사도로 동작합니다. "
        "query 인자는 실제로 문서 본문에 등장할 법한 구체적인 키워드/개체명/주제로 작성하세요 "
        "(예: 'OpenAI ChatGPT 신규 기능', 'GPT-5.6 벤치마크 성능'). "
        "'PDF', '전체 텍스트', '목차', 파일명, 문서 제목처럼 문서 자체를 가리키는 표현이나 "
        "검색 방법/절차를 설명하는 문장은 쓰지 마세요 - 그런 단어는 본문 내용과 유사도가 낮아 "
        "검색 품질이 크게 떨어집니다. 여러 동의어/표현을 폭넓게 찾아야 하면 한 번에 다 담으려 "
        "하지 말고, 동의어별로 나눠 여러 번 호출하세요.",
        document_prompt=PromptTemplate.from_template(
        "{page_content} 파일명: {source} 문서 페이지: {page}"
    ),
    )

    return parent_retriever, retriever_tool
