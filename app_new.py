import streamlit as st
import requests
import time
import re
from PIL import Image
from io import BytesIO

# Page Configuration
st.set_page_config(page_title="AI Chatbot", page_icon="🤖")

# Custom CSS Styling
st.markdown("""
    <style>
        body { background-color: #f4f4f4; }
        .user-message { background-color: #dcf8c6; padding: 10px; border-radius: 10px;margin-top: 10px; margin-bottom: 10px; }
        .bot-message { background-color: #ebebeb; padding: 10px; border-radius: 10px; }
        .image-container { margin: 10px 0; }
    </style>
""", unsafe_allow_html=True)

# Title
st.markdown("<h1 style='text-align: center; color: #4a90e2;'>🤖 AI Chatbot</h1>", unsafe_allow_html=True)

# API Endpoint
api_url = "https://5896-1-55-245-5.ngrok-free.app/chatbot"

# Session State Initialization
if "messages" not in st.session_state:
    st.session_state["messages"] = []

# Display Chat History
for message in st.session_state["messages"]:
    with st.container():
        if message["role"] == "user":
            st.markdown(f"<div class='user-message'>👤 {message['content']}</div>", unsafe_allow_html=True)
        else:
            if "image" in message:
                st.markdown("<div class='image-container'>", unsafe_allow_html=True)
                st.image(message["image"], caption="Ảnh tạo bởi AI", use_column_width=True)
                st.markdown("</div>", unsafe_allow_html=True)
            if "content" in message:
                st.markdown(f"<div class='bot-message'>🤖 {message['content']}</div>", unsafe_allow_html=True)

# User Input
query = st.chat_input("Nhập câu hỏi của bạn...")

if query:
    # Add User Message to Session State
    st.session_state["messages"].append({"role": "user", "content": query})
    with st.container():
        st.markdown(f"<div class='user-message'>👤 {query}</div>", unsafe_allow_html=True)

    # Processing Response with Loading Spinner
    with st.spinner("Đang phản hồi..."):
        time.sleep(1)
        try:
            # API Call
            response = requests.get(api_url, params={"query": query})
            
            if response.status_code == 200:
                bot_reply = response.json().get("response", "Lỗi: API không trả về phản hồi.")
                
                # Check for Image URL
                url_match = re.search(r"https?://[^\s]+", bot_reply)
                image_url = url_match.group(0) if url_match else None

                bot_message = {"role": "assistant"}

                if image_url:
                    st.markdown(f'[📷 Link ảnh tạo ra tại đây]({image_url})', unsafe_allow_html=True)
                else:
                    # Text Response Handling
                    bot_message["content"] = bot_reply
                    st.session_state["messages"].append(bot_message)
                    with st.container():
                        st.markdown(f"<div class='bot-message'>🤖 {bot_reply}</div>", unsafe_allow_html=True)
            else:
                st.error(f"Lỗi API: {response.status_code}")

        except Exception as e:
            st.error(f"Lỗi kết nối: {str(e)}")