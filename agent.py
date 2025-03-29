from langchain.agents import initialize_agent, Tool
from langchain.tools import tool
from langchain_together import Together
from langchain_community.utilities import SerpAPIWrapper
from langchain_core.prompts import PromptTemplate
from langchain_core.documents import Document
from langchain_community.vectorstores import FAISS
from langchain_community.document_loaders import JSONLoader
from langchain.retrievers import BM25Retriever 
from langchain.vectorstores import FAISS
from langchain_together import TogetherEmbeddings

loader = JSONLoader(
    file_path='C:/Users/sonma/Downloads/BioASQ-training12b/snippet_store.json',
    jq_schema='.[]',  # .[] lặp qua tất cả phần tử trong mảng
    text_content=True  # Dữ liệu là chuỗi văn bản
)

data = loader.load()


# tao BM25 retriever
bm25_retriever = BM25Retriever.from_documents(
  data, k = 55
)

embeddings = TogetherEmbeddings(
    model="togethercomputer/m2-bert-80M-32k-retrieval",
    api_key="927f9def0329bb3869ce4b0a7a5ba3ad826e33c395f6e38a96ecd1f7c9e85029"
)
# Tải FAISS index với allow_dangerous_deserialization=True
faiss_path = 'C:/Users/sonma/Downloads/BioASQ-training12b'
vectorstore = FAISS.load_local(
    folder_path=faiss_path,
    embeddings=embeddings,
    index_name='faiss_index',
    allow_dangerous_deserialization=True  # Thêm dòng này
)

# Tạo FAISS retriever
semantic_retriever = vectorstore.as_retriever(search_kwargs={"k": 2})
