
import streamlit as st
import json
import os
import uuid
import random
from datetime import datetime
from pathlib import Path
from html import escape

# --------------------------------------------------
# APP CONFIGURATION
# --------------------------------------------------
st.set_page_config(
    page_title="ChatterBox | Connect & Share",
    page_icon="💬",
    layout="wide",
    initial_sidebar_state="expanded"
)

APP_DIR = Path("chat_data")
UPLOAD_DIR = APP_DIR / "uploads"
DATA_FILE = APP_DIR / "messages.json"

APP_DIR.mkdir(exist_ok=True)
UPLOAD_DIR.mkdir(exist_ok=True)

MAX_UPLOAD_MB = 50
MAX_UPLOAD_BYTES = MAX_UPLOAD_MB * 1024 * 1024

# --------------------------------------------------
# CUSTOM STYLING
# --------------------------------------------------
st.markdown("""
<style>
    .stApp {
        background: linear-gradient(135deg, #101827, #18243a);
        color: #f2f5ff;
    }
    [data-testid="stSidebar"] {
        background: #111b2c;
    }
    .hero {
        padding: 22px;
        border-radius: 18px;
        background: linear-gradient(120deg, #6545d8, #168aad);
        color: white;
        margin-bottom: 18px;
    }
    .hero h1 { margin: 0; font-size: 34px; }
    .hero p { margin: 7px 0 0 0; }
    .message-card {
        padding: 12px 15px;
        border-radius: 15px;
        background: #202e45;
        border: 1px solid #354762;
        margin: 7px 0;
        overflow-wrap: anywhere;
    }
    .message-meta {
        font-size: 12px;
        color: #aabbd5;
        margin-bottom: 5px;
    }
    .stButton button {
        border-radius: 12px;
    }
    footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# --------------------------------------------------
# LOCAL DATA STORAGE
# --------------------------------------------------
def load_messages():
    if not DATA_FILE.exists():
        return []
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as file:
            return json.load(file)
    except (json.JSONDecodeError, OSError):
        return []

def save_messages(messages):
    # Suitable for a local prototype, not concurrent production use.
    temp_file = DATA_FILE.with_suffix(".tmp")
    with open(temp_file, "w", encoding="utf-8") as file:
        json.dump(messages, file, ensure_ascii=False, indent=2)
    os.replace(temp_file, DATA_FILE)

if "messages" not in st.session_state:
    st.session_state.messages = load_messages()

if "username" not in st.session_state:
    st.session_state.username = ""

if "room" not in st.session_state:
    st.session_state.room = "General"

if "dark_mode" not in st.session_state:
    st.session_state.dark_mode = True

if "reply_to" not in st.session_state:
    st.session_state.reply_to = ""

# --------------------------------------------------
# SIDEBAR: PROFILE AND ROOMS
# --------------------------------------------------
with st.sidebar:
    st.markdown("# 💬 ChatterBox")
    st.caption("Your space. Your people. Your conversations.")

    st.divider()
    st.subheader("👤 Your profile")

    username = st.text_input(
        "Display name",
        value=st.session_state.username,
        max_chars=30,
        placeholder="Enter your name"
    )
    st.session_state.username = username.strip()

    st.selectbox(
        "Conversation room",
        ["General", "Friends", "Memes & GIFs", "Study Group", "Work"],
        key="room"
    )

    st.divider()
    st.subheader("✨ Quick actions")

    if st.button("🎲 Random conversation starter", use_container_width=True):
        starters = [
            "What made you smile today? 😊",
            "If you could travel anywhere, where would you go? 🌍",
            "Share a song you cannot stop listening to! 🎵",
            "What is one skill you want to learn? 🚀",
            "What is your favourite movie of all time? 🎬",
            "Send your best meme! 😂"
        ]
        st.session_state.suggested_message = random.choice(starters)

    if st.button("🧹 Clear this room", use_container_width=True):
        st.session_state.messages = [
            m for m in st.session_state.messages
            if m.get("room") != st.session_state.room
        ]
        save_messages(st.session_state.messages)
        st.rerun()

    st.divider()
    st.caption("Prototype mode: messages are stored on this server.")

# --------------------------------------------------
# HEADER
# --------------------------------------------------
st.markdown("""
<div class="hero">
    <h1>💬 ChatterBox</h1>
    <p>Talk, laugh, share memories, and stay connected.</p>
</div>
""", unsafe_allow_html=True)

if not st.session_state.username:
    st.info("Enter your display name in the sidebar to start chatting.")

# --------------------------------------------------
# CHAT ROOM INFORMATION
# --------------------------------------------------
room = st.session_state.room
room_messages = [
    m for m in st.session_state.messages
    if m.get("room") == room
]

col1, col2, col3 = st.columns(3)
col1.metric("💬 Messages", len(room_messages))
col2.metric("👥 Room", room)
col3.metric("📎 Sharing", "Enabled")

st.divider()

# --------------------------------------------------
# MESSAGE DISPLAY
# --------------------------------------------------
st.subheader(f"💭 {room}")

if not room_messages:
    st.markdown("""
    ### 👋 Welcome to the conversation!
    No messages yet. Be the first to say hello.
    """)

for message in room_messages:
    with st.container(border=True):
        sender = escape(str(message.get("sender", "Unknown")))
        timestamp = escape(str(message.get("timestamp", "")))
        text = str(message.get("text", ""))

        st.markdown(
            f"**{sender}**  ·  <small>{timestamp}</small>",
            unsafe_allow_html=True
        )

        if message.get("reply_to"):
            st.caption("↪ Replying to: " + message["reply_to"])

        if text:
            st.markdown(text)

        # Render stored media files safely.
        attachment = message.get("attachment")
        if attachment:
            file_path = Path(attachment)
            if file_path.exists() and UPLOAD_DIR.resolve() in file_path.resolve().parents:
                mime = message.get("mime", "")
                if mime.startswith("image/"):
                    if mime == "image/gif":
                        st.image(str(file_path))
                    else:
                        st.image(str(file_path))
                elif mime.startswith("video/"):
                    st.video(str(file_path))
                elif mime.startswith("audio/"):
                    st.audio(str(file_path))
                else:
                    with open(file_path, "rb") as media_file:
                        st.download_button(
                            f"📎 Download {message.get('filename', 'attachment')}",
                            media_file.read(),
                            file_name=message.get("filename", "attachment"),
                            key=f"download_{message['id']}"
                        )

        if message.get("gif_url"):
            gif_url = message["gif_url"]
            if gif_url.startswith(("https://", "http://")):
                st.image(gif_url, caption="GIF")

        reactions = message.get("reactions", {})
        if reactions:
            st.caption(
                "  ".join(
                    f"{emoji} {count}"
                    for emoji, count in reactions.items()
                )
            )

        c1, c2, c3, c4 = st.columns(4)

        with c1:
            if st.button("❤️", key=f"like_{message['id']}"):
                reactions = message.setdefault("reactions", {})
                reactions["❤️"] = reactions.get("❤️", 0) + 1
                save_messages(st.session_state.messages)
                st.rerun()

        with c2:
            if st.button("😂", key=f"laugh_{message['id']}"):
                reactions = message.setdefault("reactions", {})
                reactions["😂"] = reactions.get("😂", 0) + 1
                save_messages(st.session_state.messages)
                st.rerun()

        with c3:
            if st.button("👍", key=f"thumb_{message['id']}"):
                reactions = message.setdefault("reactions", {})
                reactions["👍"] = reactions.get("👍", 0) + 1
                save_messages(st.session_state.messages)
                st.rerun()

        with c4:
            if st.button("↩️ Reply", key=f"reply_{message['id']}"):
                st.session_state.reply_to = (
                    f"{message.get('sender', 'Unknown')}: "
                    f"{message.get('text', '')[:100]}"
                )
                st.rerun()

# --------------------------------------------------
# COMPOSER AND ATTACHMENTS
# --------------------------------------------------
st.divider()
st.subheader("✍️ Write a message")

if st.session_state.reply_to:
    st.info("Replying to: " + st.session_state.reply_to)
    if st.button("Cancel reply"):
        st.session_state.reply_to = ""
        st.rerun()

with st.form("message_form", clear_on_submit=True):
    message_text = st.text_area(
        "Message",
        value=st.session_state.get("suggested_message", ""),
        placeholder="Type something nice...",
        max_chars=5000,
        height=100
    )

    uploaded_file = st.file_uploader(
        "📎 Attach a picture, GIF, video, audio, or document",
        type=[
            "png", "jpg", "jpeg", "webp", "gif",
            "mp4", "webm", "mov",
            "mp3", "wav", "ogg",
            "pdf", "txt", "csv", "docx", "xlsx", "zip"
        ],
        help=f"Maximum file size: {MAX_UPLOAD_MB} MB"
    )

    gif_url = st.text_input(
        "🎞️ Optional GIF URL",
        placeholder="Paste a direct GIF image URL (e.g. from a GIF service)"
    )

    st.caption("Quick emojis: 😀 😂 🥰 😎 🔥 🎉 ❤️ 👍 🚀 🌈")

    send = st.form_submit_button(
        "🚀 Send message",
        use_container_width=True
    )

    if send:
        if not st.session_state.username:
            st.error("Please enter your display name in the sidebar.")
        elif not message_text.strip() and not uploaded_file and not gif_url.strip():
            st.warning("Write a message or attach a file before sending.")
        elif uploaded_file and uploaded_file.size > MAX_UPLOAD_BYTES:
            st.error(f"File exceeds the {MAX_UPLOAD_MB} MB limit.")
        elif gif_url.strip() and not gif_url.strip().startswith("https://"):
            st.error("Use a secure HTTPS URL for a GIF.")
        else:
            attachment_path = None
            mime = None
            filename = None

            if uploaded_file:
                mime = uploaded_file.type or "application/octet-stream"
                filename = Path(uploaded_file.name).name
                extension = Path(filename).suffix.lower()

                allowed_extensions = {
                    ".png", ".jpg", ".jpeg", ".webp", ".gif",
                    ".mp4", ".webm", ".mov", ".mp3", ".wav", ".ogg",
                    ".pdf", ".txt", ".csv", ".docx", ".xlsx", ".zip"
                }

                if extension not in allowed_extensions:
                    st.error("Unsupported attachment.")
                    st.stop()

                safe_name = f"{uuid.uuid4().hex}{extension}"
                destination = UPLOAD_DIR / safe_name
                destination.write_bytes(uploaded_file.getvalue())
                attachment_path = str(destination)

            new_message = {
                "id": uuid.uuid4().hex,
                "room": room,
                "sender": st.session_state.username,
                "timestamp": datetime.now().strftime("%d %b %Y, %I:%M %p"),
                "text": message_text.strip(),
                "attachment": attachment_path,
                "mime": mime,
                "filename": filename,
                "gif_url": gif_url.strip(),
                "reply_to": st.session_state.reply_to,
                "reactions": {}
            }

            st.session_state.messages.append(new_message)
            save_messages(st.session_state.messages)
            st.session_state.reply_to = ""
            st.session_state.pop("suggested_message", None)
            st.rerun()

# --------------------------------------------------
# GIF SEARCH SHORTCUT
# --------------------------------------------------
st.divider()
with st.expander("🎞️ Find GIFs to share"):
    st.write("Search for a GIF using your preferred GIF service.")
    st.link_button(
        "Open GIPHY",
        "https://giphy.com/",
        use_container_width=True
    )
    st.caption(
        "Copy a GIF's direct HTTPS image URL and paste it into "
        "the GIF URL field above. Some provider page URLs are not direct images."
    )

# --------------------------------------------------
# FOOTER
# --------------------------------------------------
st.divider()
st.caption(
    "ChatterBox prototype • Keep conversations kind • "
    "Do not upload confidential information."
)
