import hashlib
from datetime import datetime, timezone

import requests
import streamlit as st

import api_client

st.set_page_config(page_title="Echo", page_icon="🌈", layout="centered")

if "token" not in st.session_state:
    st.session_state.token = None
    st.session_state.email = None
    st.session_state.user_id = None
if "liked_post_ids" not in st.session_state:
    st.session_state.liked_post_ids = set()
if "active_view" not in st.session_state:
    st.session_state.active_view = "home"
if "auth_mode" not in st.session_state:
    st.session_state.auth_mode = "signin"

st.markdown(
    """
    <style>
    .stApp { background: #FFF7F2; }
    .block-container { padding-top: 2.2rem; max-width: 640px; }

    .echo-logo {
        font-size: 2.1rem; font-weight: 900; letter-spacing: -1px; line-height: 1;
        background: linear-gradient(120deg, #FF4D6D 0%, #7C3AED 100%);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        display: inline-block;
    }
    .echo-tagline { color: #9A8AA3; font-size: 0.95rem; margin-top: 2px; }

    .echo-hero { text-align: center; padding: 18px 0 4px 0; }
    .echo-hero-title {
        font-size: 2.6rem; font-weight: 900; letter-spacing: -1px;
        background: linear-gradient(120deg, #FF4D6D, #7C3AED 55%, #FFA63E);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        margin-bottom: 2px;
    }
    .echo-hero-sub { color: #9A8AA3; font-size: 1.05rem; margin-bottom: 18px; }

    .echo-chip {
        display: flex; align-items: center; gap: 10px; justify-content: flex-end;
        padding-top: 6px;
    }
    .echo-chip-name { font-weight: 700; color: #2B1A33; font-size: 0.95rem; }

    div[data-testid="stVerticalBlockBorderWrapper"] {
        background: #FFFFFF !important;
        border: 1px solid #F3E7EF !important;
        border-radius: 24px !important;
        box-shadow: 0 6px 20px rgba(124, 58, 237, 0.07);
    }

    .echo-avatar {
        width: 44px; height: 44px; border-radius: 50%; flex-shrink: 0;
        display: flex; align-items: center; justify-content: center;
        color: white; font-weight: 800; font-size: 1.05rem;
    }
    .echo-post-head { display: flex; align-items: center; gap: 12px; margin-bottom: 10px; }
    .echo-name { color: #2B1A33; font-weight: 800; font-size: 0.98rem; }
    .echo-time { color: #B9A8C2; font-size: 0.8rem; }
    .echo-fresh {
        background: #FFD23F; color: #4A3B00; font-size: 0.68rem; font-weight: 800;
        padding: 2px 9px; border-radius: 999px; margin-left: 6px; vertical-align: middle;
    }
    .echo-title { color: #231129; font-weight: 800; font-size: 1.12rem; margin: 6px 0 3px 0; }
    .echo-content { color: #4B3B52; font-size: 0.97rem; line-height: 1.55; }

    .stButton>button, .stFormSubmitButton>button {
        border-radius: 999px !important;
        border: 2px solid #F3E7EF !important;
        background: white !important;
        color: #7C3AED !important;
        font-weight: 700 !important;
    }
    .stButton>button:hover, .stFormSubmitButton>button:hover {
        border-color: #FF4D6D !important; color: #FF4D6D !important;
    }
    button[kind="primary"] {
        background: linear-gradient(120deg, #FF4D6D, #7C3AED) !important;
        border: none !important; color: white !important;
    }

    .echo-profile-avatar {
        width: 84px; height: 84px; border-radius: 50%;
        display: flex; align-items: center; justify-content: center;
        color: white; font-weight: 800; font-size: 2rem;
        margin: 4px auto 12px auto;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

AVATAR_GRADIENTS = [
    ("#FF6B9D", "#C44FD1"),
    ("#6C63FF", "#3B82F6"),
    ("#FFA63E", "#FF4D6D"),
    ("#22C1C3", "#3B82F6"),
    ("#EC4899", "#8B5CF6"),
    ("#F97316", "#FFD23F"),
]


def avatar_colors(email: str) -> tuple[str, str]:
    idx = int(hashlib.md5(email.encode()).hexdigest(), 16) % len(AVATAR_GRADIENTS)
    return AVATAR_GRADIENTS[idx]


def avatar_html(email: str, css_class: str = "echo-avatar") -> str:
    c1, c2 = avatar_colors(email)
    initial = email[0].upper() if email else "?"
    return f'<div class="{css_class}" style="background: linear-gradient(135deg, {c1}, {c2});">{initial}</div>'


def relative_time(iso_string: str) -> tuple[str, bool]:
    dt = datetime.fromisoformat(iso_string)
    now = datetime.now(dt.tzinfo) if dt.tzinfo else datetime.now()
    seconds = (now - dt).total_seconds()
    is_fresh = seconds < 3600
    if seconds < 60:
        return "just now", is_fresh
    minutes = int(seconds // 60)
    if minutes < 60:
        return f"{minutes}m ago", is_fresh
    hours = int(minutes // 60)
    if hours < 24:
        return f"{hours}h ago", is_fresh
    days = int(hours // 24)
    if days < 7:
        return f"{days}d ago", is_fresh
    weeks = int(days // 7)
    if weeks < 5:
        return f"{weeks}w ago", is_fresh
    return f"on {dt.strftime('%b %d')}", is_fresh


try:
    api_client.ping()
except requests.exceptions.RequestException:
    st.markdown('<p class="echo-logo">🌈 Echo</p>', unsafe_allow_html=True)
    st.error(f"Can't reach the server at `{api_client.BACKEND_URL}` right now. Give it a moment and refresh.")
    st.stop()


# --------------------------------------------------------------------------
# Logged out: full hero + inline sign in / join, no sidebar
# --------------------------------------------------------------------------
if not st.session_state.token:
    st.markdown(
        """
        <div class="echo-hero">
            <div class="echo-hero-title">🌈 Echo</div>
            <div class="echo-hero-sub">Drop a thought. Watch it echo.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    mode_col1, mode_col2 = st.columns(2)
    if mode_col1.button(
        "Sign in", type="primary" if st.session_state.auth_mode == "signin" else "secondary",
        use_container_width=True,
    ):
        st.session_state.auth_mode = "signin"
        st.rerun()
    if mode_col2.button(
        "Join Echo", type="primary" if st.session_state.auth_mode == "join" else "secondary",
        use_container_width=True,
    ):
        st.session_state.auth_mode = "join"
        st.rerun()

    st.write("")

    with st.container(border=True):
        if st.session_state.auth_mode == "signin":
            with st.form("login_form"):
                login_email = st.text_input("Email")
                login_password = st.text_input("Password", type="password")
                if st.form_submit_button("Let's go", type="primary", use_container_width=True):
                    try:
                        result = api_client.login(login_email, login_password)
                        st.session_state.token = result["access_token"]
                        st.session_state.email = login_email
                        st.session_state.user_id = api_client.decode_user_id(result["access_token"])
                        st.rerun()
                    except api_client.ApiError as e:
                        st.error(e.detail)
        else:
            with st.form("register_form"):
                reg_email = st.text_input("Email", key="reg_email")
                reg_password = st.text_input("Password", type="password", key="reg_password")
                if st.form_submit_button("Count me in", type="primary", use_container_width=True):
                    try:
                        api_client.register(reg_email, reg_password)
                        st.success("You're in! Switch to Sign in above.")
                    except api_client.ApiError as e:
                        st.error(e.detail)

    st.stop()

token = st.session_state.token


# --------------------------------------------------------------------------
# Logged in: top bar (logo + user chip, no sidebar)
# --------------------------------------------------------------------------
top_col1, top_col2 = st.columns([2, 2])
with top_col1:
    st.markdown('<p class="echo-logo">🌈 Echo</p>', unsafe_allow_html=True)
with top_col2:
    st.markdown(
        f"""
        <div class="echo-chip">
            {avatar_html(st.session_state.email, "echo-avatar")}
            <span class="echo-chip-name">{st.session_state.email.split('@')[0]}</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

nav_col1, nav_col2, nav_col3 = st.columns([2, 2, 1])
if nav_col1.button(
    "🏠 Home", type="primary" if st.session_state.active_view == "home" else "secondary",
    use_container_width=True,
):
    st.session_state.active_view = "home"
    st.rerun()
if nav_col2.button(
    "👤 Profile", type="primary" if st.session_state.active_view == "profile" else "secondary",
    use_container_width=True,
):
    st.session_state.active_view = "profile"
    st.rerun()
if nav_col3.button("↪", use_container_width=True, help="Sign out"):
    st.session_state.token = None
    st.session_state.email = None
    st.session_state.user_id = None
    st.rerun()

st.write("")


# --------------------------------------------------------------------------
# Post card renderer (shared by Home + Profile)
# --------------------------------------------------------------------------
def render_post(item: dict, show_owner_controls: bool, key_prefix: str) -> None:
    post, votes = item["Post"], item["votes"]
    owner_email = post["owner"]["email"]
    editing_flag = f"{key_prefix}_editing_{post['id']}"
    time_label, is_fresh = relative_time(post["created_at"])
    fresh_badge = '<span class="echo-fresh">🔥 new</span>' if is_fresh else ""

    with st.container(border=True):
        st.markdown(
            f"""
            <div class="echo-post-head">
                {avatar_html(owner_email)}
                <div>
                    <div class="echo-name">{owner_email.split('@')[0]}{fresh_badge}</div>
                    <div class="echo-time">{time_label}</div>
                </div>
            </div>
            <div class="echo-title">{post['title']}</div>
            <div class="echo-content">{post['content']}</div>
            """,
            unsafe_allow_html=True,
        )
        st.write("")

        liked = post["id"] in st.session_state.liked_post_ids
        cols = st.columns([1, 1, 1, 1, 4]) if show_owner_controls else st.columns([1, 1, 6])

        heart = "💗" if liked else "🤍"
        if cols[0].button(f"{heart} {votes}", key=f"{key_prefix}_like_{post['id']}"):
            try:
                api_client.vote(token, post["id"], 0 if liked else 1)
                if liked:
                    st.session_state.liked_post_ids.discard(post["id"])
                else:
                    st.session_state.liked_post_ids.add(post["id"])
                st.rerun()
            except api_client.ApiError as e:
                st.toast(e.detail, icon="⚠️")

        if show_owner_controls:
            if cols[1].button("✏️", key=f"{key_prefix}_edit_{post['id']}", help="Edit"):
                st.session_state[editing_flag] = True
                st.rerun()
            if cols[2].button("🗑️", key=f"{key_prefix}_delete_{post['id']}", help="Delete"):
                try:
                    api_client.delete_post(token, post["id"])
                    st.rerun()
                except api_client.ApiError as e:
                    st.error(e.detail)

        if show_owner_controls and st.session_state.get(editing_flag):
            with st.form(f"{key_prefix}_edit_form_{post['id']}"):
                edited_title = st.text_input("Title", value=post["title"])
                edited_content = st.text_area("Say more...", value=post["content"])
                save_col, cancel_col = st.columns(2)
                if save_col.form_submit_button("Save", type="primary", use_container_width=True):
                    try:
                        api_client.update_post(token, post["id"], edited_title, edited_content, post["published"])
                        st.session_state[editing_flag] = False
                        st.rerun()
                    except api_client.ApiError as e:
                        st.error(e.detail)
                if cancel_col.form_submit_button("Cancel", use_container_width=True):
                    st.session_state[editing_flag] = False
                    st.rerun()


# --------------------------------------------------------------------------
# Home
# --------------------------------------------------------------------------
if st.session_state.active_view == "home":
    with st.container(border=True):
        st.markdown(
            f"""<div class="echo-post-head">{avatar_html(st.session_state.email)}
            <div class="echo-name">What's the vibe today?</div></div>""",
            unsafe_allow_html=True,
        )
        with st.form("compose_form", clear_on_submit=True):
            new_title = st.text_input("Headline", placeholder="Give it a headline")
            new_content = st.text_area("Content", placeholder="Say something...", label_visibility="collapsed")
            if st.form_submit_button("🚀 Echo it", type="primary"):
                if not new_title or not new_content:
                    st.warning("Needs a headline and something to say.")
                else:
                    try:
                        api_client.create_post(token, new_title, new_content, True)
                        st.toast("It's live!", icon="🌈")
                        st.rerun()
                    except api_client.ApiError as e:
                        st.error(e.detail)

    search = st.text_input("", placeholder="🔍 Search the noise", label_visibility="collapsed", key="feed_search")
    try:
        posts = api_client.get_posts(token, search=search, limit=50)
    except api_client.ApiError as e:
        st.error(e.detail)
        posts = []

    if not posts:
        st.markdown(
            '<div style="text-align:center; color:#B9A8C2; padding:40px 0;">'
            "Crickets. Be the first to say something. 🦗</div>",
            unsafe_allow_html=True,
        )
    for item in posts:
        render_post(item, show_owner_controls=(item["Post"]["owner_id"] == st.session_state.user_id), key_prefix="home")


# --------------------------------------------------------------------------
# Profile
# --------------------------------------------------------------------------
else:
    c1, c2 = avatar_colors(st.session_state.email)
    try:
        all_posts = api_client.get_posts(token, limit=200)
    except api_client.ApiError as e:
        st.error(e.detail)
        all_posts = []
    my_posts = [p for p in all_posts if p["Post"]["owner_id"] == st.session_state.user_id]
    total_likes = sum(p["votes"] for p in my_posts)

    st.markdown(
        f"""
        <div style="text-align:center;">
            <div class="echo-profile-avatar" style="background: linear-gradient(135deg, {c1}, {c2});">
                {st.session_state.email[0].upper()}
            </div>
            <div class="echo-name" style="font-size:1.15rem;">{st.session_state.email}</div>
            <div class="echo-time">{len(my_posts)} echo{"es" if len(my_posts) != 1 else ""} · {total_likes} 💗</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.write("")

    if not my_posts:
        st.markdown(
            '<div style="text-align:center; color:#B9A8C2; padding:20px 0;">'
            "Nothing here yet — head to Home and say something.</div>",
            unsafe_allow_html=True,
        )
    for item in my_posts:
        render_post(item, show_owner_controls=True, key_prefix="profile")
