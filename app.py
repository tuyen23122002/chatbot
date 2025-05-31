import streamlit as st
import hashlib
from sqlalchemy import create_engine, text

# Kết nối SQL Server
server = "PC\\MSSQLSERVER02"
database = "ChatbotDB"
driver = "ODBC Driver 17 for SQL Server"

connection_string = f"mssql+pyodbc://@{server}/{database}?driver={driver}&Trusted_Connection=yes"
engine = create_engine(connection_string)

# Hàm hash mật khẩu
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# Hàm kiểm tra đăng nhập
def check_login(username, password):
    hashed_pw = hash_password(password)
    with engine.connect() as conn:
        query = text("SELECT id FROM users WHERE username = :username AND password_hash = :password_hash")
        result = conn.execute(query, {"username": username, "password_hash": hashed_pw}).fetchone()
        return result[0] if result else None

# Hàm đăng ký tài khoản
def register_user(username, password):
    hashed_pw = hash_password(password)
    try:
        with engine.connect() as conn:
            query = text("INSERT INTO users (username, password_hash) VALUES (:username, :password_hash)")
            conn.execute(query, {"username": username, "password_hash": hashed_pw})
            conn.commit()
        return True
    except Exception as e:
        return str(e)

# Hàm tạo cuộc hội thoại mới
def create_new_conversation(user_id, title):
    with engine.connect() as conn:
        query = text("INSERT INTO conversations (user_id, title) OUTPUT INSERTED.id VALUES (:user_id, :title)")
        result = conn.execute(query, {"user_id": user_id, "title": title}).fetchone()
        conn.commit()
    return result[0] if result else None

# Hàm lấy danh sách hội thoại của user
def get_conversations(user_id):
    with engine.connect() as conn:
        query = text("SELECT id, title FROM conversations WHERE user_id = :user_id ORDER BY created_at DESC")
        result = conn.execute(query, {"user_id": user_id}).fetchall()
    return [{"id": row[0], "title": row[1]} for row in result]

# Hàm lấy tin nhắn của cuộc hội thoại
def get_messages(conversation_id):
    with engine.connect() as conn:
        query = text("SELECT sender, message_text FROM messages WHERE conversation_id = :conversation_id ORDER BY created_at")
        result = conn.execute(query, {"conversation_id": conversation_id}).fetchall()
    return [{"sender": row[0], "text": row[1]} for row in result]

# Hàm lưu tin nhắn vào DB
def save_message(conversation_id, sender, text):
    with engine.connect() as conn:
        query = text("INSERT INTO messages (conversation_id, sender, message_text) VALUES (:conversation_id, :sender, :text)")
        conn.execute(query, {"conversation_id": conversation_id, "sender": sender, "text": text})
        conn.commit()

# Giao diện chatbot
def chatbot_ui():
    st.title("🤖 Chatbot AI")
    user_id = st.session_state["user_id"]

    # Sidebar hiển thị danh sách hội thoại
    st.sidebar.header("📜 Lịch sử hội thoại")
    conversations = get_conversations(user_id)

    conversation_options = {c["title"]: c["id"] for c in conversations}
    selected_conversation_title = st.sidebar.selectbox("Chọn hội thoại", list(conversation_options.keys()), index=0 if conversations else None)
    
    if selected_conversation_title:
        selected_conversation_id = conversation_options[selected_conversation_title]
        st.session_state["conversation_id"] = selected_conversation_id
    else:
        st.session_state["conversation_id"] = None

    # Nút tạo hội thoại mới
    new_title = st.sidebar.text_input("Nhập tên cuộc hội thoại")
    if st.sidebar.button("➕ Tạo mới"):
        if new_title:
            new_conversation_id = create_new_conversation(user_id, new_title)
            if new_conversation_id:
                st.session_state["conversation_id"] = new_conversation_id
                st.rerun()
        else:
            st.sidebar.warning("Vui lòng nhập tên cuộc hội thoại!")

    # Hiển thị nội dung hội thoại
    if st.session_state["conversation_id"]:
        messages = get_messages(st.session_state["conversation_id"])
        for msg in messages:
            if msg["sender"] == "user":
                st.markdown(f"👤 **Bạn**: {msg['text']}")
            else:
                st.markdown(f"🤖 **Bot**: {msg['text']}")

        # Ô nhập tin nhắn
        user_input = st.text_input("Nhập tin nhắn:")
        if st.button("Gửi"):
            if user_input:
                save_message(st.session_state["conversation_id"], "user", user_input)
                st.rerun()

        if st.button("Đăng xuất"):
            st.session_state["logged_in"] = False
            st.session_state.pop("user_id", None)
            st.rerun()

# Giao diện đăng nhập & đăng ký
def login_register_ui():
    st.title("🔐 Đăng Nhập / Đăng Ký")

    menu = ["Đăng Nhập", "Đăng Ký"]
    choice = st.selectbox("Chọn chế độ", menu)

    if choice == "Đăng Nhập":
        st.subheader("Đăng Nhập")
        username = st.text_input("Tên đăng nhập")
        password = st.text_input("Mật khẩu", type="password")

        if st.button("Đăng nhập"):
            user_id = check_login(username, password)
            if user_id:
                st.session_state["logged_in"] = True
                st.session_state["user_id"] = user_id
                st.rerun()  # Load lại trang để hiển thị giao diện chatbot
            else:
                st.error("Sai tài khoản hoặc mật khẩu!")

    elif choice == "Đăng Ký":
        st.subheader("Đăng Ký Tài Khoản")
        new_user = st.text_input("Tên đăng nhập")
        new_password = st.text_input("Mật khẩu", type="password")

        if st.button("Đăng ký"):
            result = register_user(new_user, new_password)
            if result is True:
                st.success("Đăng ký thành công! Vui lòng đăng nhập.")
            else:
                st.error(f"Lỗi: {result}")

# Chạy ứng dụng
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

if st.session_state["logged_in"]:
    chatbot_ui()
else:
    login_register_ui()
