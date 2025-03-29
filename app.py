# streamlit_app.py
import streamlit as st
import requests
import json
from datetime import datetime

# Cấu hình trang Streamlit
st.set_page_config(
    page_title="Chatbot AI",
    page_icon="🤖",
    layout="centered"
)

# Khởi tạo API key cho WeatherAPI
WEATHER_API_KEY = "8ae493ecabbe4dacb2482848252503"
WEATHER_BASE_URL = "http://api.weatherapi.com/v1"

def get_weather(city):
    """Lấy thông tin thời tiết cho một thành phố"""
    try:
        # Gọi API thời tiết
        params = {
            "key": WEATHER_API_KEY,
            "q": city,
            "aqi": "no"
        }
        response = requests.get(f"{WEATHER_BASE_URL}/current.json", params=params)
        
        if response.status_code == 200:
            data = response.json()
            location = data["location"]
            current = data["current"]
            
            weather_info = f"""
            🌤️ Thông tin thời tiết tại {location['name']}, {location['country']}:
            🌡️ Nhiệt độ: {current['temp_c']}°C
            💧 Độ ẩm: {current['humidity']}%
            💨 Tốc độ gió: {current['wind_kph']} km/h
            🌪️ Hướng gió: {current['wind_dir']}
            ⏰ Cập nhật: {datetime.fromtimestamp(location['localtime_epoch']).strftime('%H:%M')}
            """
            return weather_info
        else:
            return f"❌ Không thể lấy thông tin thời tiết cho {city}. Vui lòng kiểm tra lại tên thành phố."
    except Exception as e:
        return f"❌ Lỗi khi lấy thông tin thời tiết: {str(e)}"

# Tiêu đề ứng dụng
st.title("💬 Chatbot AI")
st.markdown("Trò chuyện với trợ lý ảo thông minh")

# Khởi tạo lịch sử chat trong session state nếu chưa có
if "messages" not in st.session_state:
    st.session_state.messages = []

# Hiển thị lịch sử chat
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Nhập liệu từ người dùng
if prompt := st.chat_input("Nhập câu hỏi của bạn..."):
    # Hiển thị tin nhắn người dùng
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # Thêm tin nhắn người dùng vào lịch sử
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    # Hiển thị indicator đang tải
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        message_placeholder.markdown("🤔 Đang suy nghĩ...")
        
        try:
            # Kiểm tra nếu câu hỏi liên quan đến thời tiết
            if "thời tiết" in prompt.lower() or "weather" in prompt.lower():
                # Tìm tên thành phố trong câu hỏi
                words = prompt.lower().split()
                weather_keywords = ["thời tiết", "weather", "ở", "tại", "in", "at"]
                city = next((word for word in words if word not in weather_keywords), None)
                
                if city:
                    weather_response = get_weather(city)
                    message_placeholder.markdown(weather_response)
                    st.session_state.messages.append({"role": "assistant", "content": weather_response})
                else:
                    message_placeholder.markdown("Vui lòng chỉ định tên thành phố để tôi có thể cung cấp thông tin thời tiết.")
                    st.session_state.messages.append({"role": "assistant", "content": "Vui lòng chỉ định tên thành phố để tôi có thể cung cấp thông tin thời tiết."})
            else:
                # Gửi request đến FastAPI endpoint cho các câu hỏi khác
                API_URL = "https://95c8-2405-4802-500c-dfb0-f59f-23ad-404e-4bde.ngrok-free.app/chatbot"
                response = requests.get(
                    API_URL,
                    params={"query": prompt}
                )
                
                if response.status_code == 200:
                    bot_response = response.json()["response"]
                    message_placeholder.markdown(bot_response)
                    st.session_state.messages.append({"role": "assistant", "content": bot_response})
                else:
                    message_placeholder.markdown(f"❌ Lỗi: Không thể kết nối đến API (Mã lỗi: {response.status_code})")
        
        except Exception as e:
            message_placeholder.markdown(f"❌ Lỗi: {str(e)}")

# Thêm sidebar với hướng dẫn
with st.sidebar:
    st.title("Hướng dẫn")
    st.markdown("""
    **Cách sử dụng:**
    1. Nhập câu hỏi của bạn vào ô nhập liệu
    2. Để hỏi về thời tiết, hãy nhập: "thời tiết ở [tên thành phố]"
    3. Chatbot sẽ trả lời sau vài giây
    4. Tiếp tục cuộc trò chuyện!
    """)
    
    st.markdown("---")
    st.markdown("Ứng dụng được phát triển với Streamlit và FastAPI")
    
    # Nút xóa lịch sử
    if st.button("Xóa lịch sử trò chuyện"):
        st.session_state.messages = []
        st.rerun()