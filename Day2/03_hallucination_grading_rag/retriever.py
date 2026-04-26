import fitz
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma
from langchain_classic.retrievers import ParentDocumentRetriever
from langchain_core.stores import InMemoryByteStore
from langchain_core.tools import create_retriever_tool


def setup_retriever():
    file_path = "../dataset/SPRi AI Brief 4월호_260401.pdf"

    # PyMuPDF로 문서 로드
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
                    "source": file_path,
                    "page": page_num + 1  # 1부터 시작
                }
            )
        )

    doc.close()
    print(f"총 {len(docs)}페이지 로드 완료")

    # child_splitter 정의
    child_splitter = RecursiveCharacterTextSplitter(chunk_size=400, chunk_overlap=50)

    # 벡터스토어 생성 (persist 없이 메모리에만)
    embeddings = OpenAIEmbeddings()
    vectorstore = Chroma(
        collection_name="april_doc",
        embedding_function=embeddings
    )

    # docstore 생성 (InMemoryByteStore)
    docstore = InMemoryByteStore()

    # ParentDocumentRetriever 생성
    parent_retriever = ParentDocumentRetriever(
        vectorstore=vectorstore,
        docstore=docstore,
        child_splitter=child_splitter,
        parent_splitter=None,  # 페이지 = parent
        search_kwargs={"k": 1}
    )

    # 문서 추가
    print("문서를 벡터스토어에 추가 중...")
    parent_retriever.add_documents(docs)

    child_count = vectorstore._collection.count()
    parent_count = len(list(docstore.yield_keys()))
    print(f"child chunk 수: {child_count}, parent page 수: {parent_count}")

    # Retriever Tool 생성
    retriever_tool = create_retriever_tool(
        parent_retriever,
        "retrieve_AI_brief",
        "AI 기술 관련 정보를 SPRi AI Brief에서 검색하고 반환합니다.",
    )

    return parent_retriever, retriever_tool
