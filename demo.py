import json
import numpy as np
from together import Together
import faiss
from crewai import Agent, Crew, Task, LLM, Process
import pickle
import os

# Khởi tạo client Together AI
client = Together(api_key="1c7d99bf90081e1ae99ebf59f15649aff7648238f07cf9742d0de0bcd1cc5f6c")

# Hàm tạo embedding sử dụng Together AI
def embed_text_together(texts):
    embeddings = []
    for text in texts:
        try:
            response = client.embeddings.create(
                model="togethercomputer/m2-bert-80M-32k-retrieval",
                input=text
            )
            embedding = response.data[0].embedding
            embeddings.append(embedding)
        except Exception as e:
            print(f"Lỗi khi tạo embedding cho đoạn văn bản: {text[:50]}... Lỗi: {e}")
            embeddings.append(np.zeros(768))
    return np.array(embeddings, dtype=np.float32)
    
# Hàm gọi LLM
llm = LLM(
    model="together_ai/meta-llama/Llama-3.3-70B-Instruct-Turbo-Free",
    temperature=0.7,
    api_key="1c7d99bf90081e1ae99ebf59f15649aff7648238f07cf9742d0de0bcd1cc5f6c"
)

# Hàm truy vấn FAISS
def query_faiss(query, faiss_index, snippet_store, k=5):
    query_embedding = embed_text_together([query])
    distances, indices = faiss_index.search(query_embedding, k)
    results = [snippet_store[idx] for idx in indices[0] if idx >= 0 and idx < len(snippet_store)]
    return results

# Định nghĩa các Agent
# Định nghĩa các Agent
analyzer_agent = Agent(
    role="Query Analyzer",
    goal="Phân tích query để quyết định trả lời trực tiếp hay cần truy vấn cơ sở dữ liệu y học.",
    backstory="Một chuyên gia ngôn ngữ tự nhiên có khả năng phân tích truy vấn đầu vào, xác định ý định của người dùng và quyết định có cần tìm kiếm thêm thông tin từ cơ sở dữ liệu y học hay không.",
    verbose=True,
    llm=llm,
)

retriever_agent = Agent(
    role="FAISS Retriever",
    goal="Truy vấn cơ sở dữ liệu FAISS chứa thông tin y học để lấy các đoạn văn bản liên quan đến query.",
    backstory="Một công cụ tìm kiếm thông minh chuyên truy xuất thông tin y học từ cơ sở dữ liệu FAISS, giúp tìm ra những đoạn văn bản có liên quan nhất đến câu hỏi của người dùng.",
    verbose=True,
    llm=llm,
)

answer_agent = Agent(
    role="Answer Generator",
    goal="Tổng hợp thông tin và tạo câu trả lời chính xác, ngắn gọn dựa trên query và dữ liệu y học (nếu có).",
    backstory="Một chuyên gia tạo nội dung có khả năng hiểu các truy vấn y học, tổng hợp thông tin từ nhiều nguồn và đưa ra câu trả lời chính xác, súc tích, dễ hiểu cho người dùng.",
    verbose=True,
    llm=llm
)

# Định nghĩa các Task
def analyze_task(query):
    return Task(
        description=f"""
        Phân tích câu hỏi sau: "{query}"
        - Nếu câu hỏi thuộc lĩnh vực y học, trả về:
          {{
            "response": "NEED_RETRIEVAL",
            "tag": "[RETRIEVAL]"
          }}
        - Nếu câu hỏi không liên quan đến lĩnh vực y học, sử dụng kiến thức của LLM để trả lời và trả về:
          {{
            "response": "câu trả lời trực tiếp từ LLM tại đây",
            "tag": "[DIRECT]"
          }}
        Đảm bảo phản hồi là chuỗi JSON hợp lệ với các khóa "response" và "tag".
        """,
        agent=analyzer_agent,
        expected_output="Chuỗi JSON hợp lệ với các khóa 'response' và 'tag'."
    )

def retrieve_task(query, faiss_index, snippet_store):
    return Task(
        description=f"""
        Truy xuất thông tin y học liên quan đến truy vấn: "{query}"
        Truy vấn FAISS để tìm các đoạn văn bản y học liên quan.
        """,
        agent=retriever_agent,
        expected_output="Danh sách các đoạn văn bản liên quan từ FAISS.",
        async_execution=False,
        context=lambda: {"query_results": query_faiss(query, faiss_index, snippet_store)}
    )

def answer_task(query, context=None):
    context_str = ""
    if context and "query_results" in context:
        context_str = "\n\n".join([f"Đoạn {i+1}: {text}" for i, text in enumerate(context["query_results"])]);
    
    return Task(
        description=f"""
        Tạo câu trả lời cho câu hỏi: "{query}"
        Thông tin từ cơ sở dữ liệu y học:
        {context_str if context_str else "Không có thông tin liên quan."}
        """,
        agent=answer_agent,
        expected_output="Câu trả lời ngắn gọn và chính xác dựa trên dữ liệu y học hoặc kiến thức chung."
    )

# Hàm tải FAISS index và snippet store có sẵn
def load_existing_faiss(index_path, snippets_path):
    print(f"Đang tải FAISS index từ {index_path}...")
    faiss_index = faiss.read_index(index_path)
    
    print(f"Đang tải snippet store từ {snippets_path}...")
    # Kiểm tra định dạng file snippet
    if snippets_path.endswith('.json'):
        with open(snippets_path, "r", encoding="utf-8") as f:
            snippet_store = json.load(f)
    elif snippets_path.endswith('.pkl'):
        with open(snippets_path, "rb") as f:
            snippet_store = pickle.load(f)
    else:
        raise ValueError("Định dạng file snippet không được hỗ trợ. Chỉ hỗ trợ .json và .pkl")
    
    return faiss_index, snippet_store

# Hàm chính để xử lý câu hỏi
def process_query(query, faiss_index, snippet_store):
    # Tạo tác vụ phân tích
    analysis_task = analyze_task(query)

    # Khởi tạo Crew
    crew = Crew(
        agents=[analyzer_agent, retriever_agent, answer_agent],
        tasks=[analysis_task],
        process=Process.sequential,
        verbose=True
    )
    
    inputs = {"query": query}
    
    # Gọi kickoff
    analysis_result = crew.kickoff(inputs)
    
    # Xử lý kết quả
    try:
        if not isinstance(analysis_result, str):
            raise ValueError(f"Kỳ vọng một chuỗi từ kickoff, nhận được {type(analysis_result)}: {analysis_result}")
        
        analysis_data = json.loads(analysis_result)
        
        # Kiểm tra kết quả phân tích
        if analysis_data.get("response") == "NEED_RETRIEVAL" and analysis_data.get("tag") == "[RETRIEVAL]":
            retrieval_task_instance = retrieve_task(query, faiss_index, snippet_store)
            retrieval_result = crew.process_task(retrieval_task_instance)
            
            answer_task_instance = answer_task(query, {"query_results": retrieval_result["query_results"]})
            final_answer = crew.process_task(answer_task_instance)
            return final_answer
        else:
            return analysis_data["response"]
    except json.JSONDecodeError as e:
        return f"Lỗi khi phân tích JSON từ kết quả phân tích: {str(e)}. Kết quả thô: {analysis_result}"
    except ValueError as e:
        return f"Lỗi khi xử lý kết quả kickoff: {str(e)}. Kết quả thô: {analysis_result}"
# Hàm main
def main():
     # Đường dẫn đến file FAISS index và snippet store có sẵn
    faiss_index_path = r"C:\Users\sonma\Downloads\BioASQ-training12b\faiss_index.bin"
    snippet_store_path = r"C:\Users\sonma\Downloads\BioASQ-training12b\snippet_store.json"
    
    # Tải FAISS index và snippet store
    try:
        faiss_index, snippet_store = load_existing_faiss(faiss_index_path, snippet_store_path)
        print(f"Đã tải thành công FAISS index và snippet store với {len(snippet_store)} đoạn văn bản.")
    except Exception as e:
        print(f"Lỗi khi tải file: {e}")
        return
    
    
    print("\n===== CHAT BOT DEMO =====")
    print("Nhập 'quit' hoặc 'exit' để thoát")
    
    while True:
        user_query = input("\nNhập câu hỏi của bạn: ")
        if user_query.lower() in ["quit", "exit"]:
            break
        
        answer = process_query(user_query, faiss_index, snippet_store)
        print(f"Câu trả lời: {answer}")

if __name__ == "__main__":
    main()