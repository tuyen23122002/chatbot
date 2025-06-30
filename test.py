import requests

def test_chatbot_answer(api_url, question, expected_keywords=None):
    """
    Gửi câu hỏi tới chatbot API và kiểm tra phản hồi.
    expected_keywords: list các từ khóa mong đợi xuất hiện trong câu trả lời.
    """
    response = requests.get(api_url, params={"query": question})
    assert response.status_code == 200, f"API trả về mã lỗi: {response.status_code}"
    data = response.json()
    answer = data.get("response", "")
    print(f"Câu hỏi: {question}")
    print(f"Trả lời: {answer}\n")
    if expected_keywords:
        for kw in expected_keywords:
            assert kw.lower() in answer.lower(), f"Không tìm thấy từ khóa '{kw}' trong câu trả lời."

if __name__ == "__main__":
    API_URL = "https://0e05-42-112-61-199.ngrok-free.app/chatbot"
    # Danh sách câu hỏi kiểm thử
    test_cases = [
        {"question": "Bệnh tiểu đường là gì?", "keywords": ["bệnh", "đường huyết"]},
        {"question": "Triệu chứng của cảm cúm?", "keywords": ["triệu chứng", "sốt", "hắt hơi"]},
        {"question": "Làm sao để phòng tránh Covid-19?", "keywords": ["phòng tránh", "rửa tay", "khẩu trang"]},
    ]
    for case in test_cases:
        test_chatbot_answer(API_URL, case["question"], case["keywords"]) 