import streamlit as st
import pandas as pd
import re
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from openai import OpenAI

# ============================================================
# 페이지 설정
# ============================================================
st.set_page_config(
    page_title="유튜브 댓글 수집기",
    page_icon="📺",
    layout="wide"
)

# ============================================================
# 스타일
# ============================================================
st.markdown("""
<style>
    /* ─── 전체 배경 ─── */
    .stApp {
        background: linear-gradient(180deg, #0E1117 0%, #151B28 50%, #1A1F2E 100%);
    }

    /* ─── 헤더 ─── */
    .main-header {
        font-size: 2.8rem;
        font-weight: 800;
        text-align: center;
        background: linear-gradient(90deg, #FF4B4B, #FF8E53);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.3rem;
    }
    .sub-header {
        font-size: 1.05rem;
        text-align: center;
        color: #8892A0;
        margin-bottom: 2rem;
    }

    /* ─── 영상 카드 ─── */
    .video-card {
        background: linear-gradient(135deg, #1E2536, #252D40);
        border: 1px solid #2D3548;
        border-radius: 16px;
        padding: 24px;
        margin-bottom: 20px;
    }
    .video-title {
        font-size: 1.3rem;
        font-weight: 700;
        color: #FFFFFF;
        margin-bottom: 8px;
    }
    .video-channel {
        color: #8892A0;
        font-size: 0.95rem;
    }

    /* ─── 통계 카드 ─── */
    .stat-card {
        background: linear-gradient(135deg, #1E2536, #2A3350);
        border: 1px solid #2D3548;
        border-radius: 14px;
        padding: 20px;
        text-align: center;
        transition: transform 0.2s;
    }
    .stat-card:hover {
        transform: translateY(-3px);
        box-shadow: 0 8px 25px rgba(255, 75, 75, 0.15);
    }
    .stat-number {
        font-size: 1.8rem;
        font-weight: 800;
        background: linear-gradient(90deg, #FF4B4B, #FF8E53);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    .stat-label {
        font-size: 0.85rem;
        color: #8892A0;
        margin-top: 4px;
    }

    /* ─── 댓글 카드 ─── */
    .comment-box {
        background: linear-gradient(135deg, #1A2033, #212944);
        border: 1px solid #2D3548;
        border-left: 4px solid #FF4B4B;
        padding: 16px 20px;
        margin-bottom: 12px;
        border-radius: 0 12px 12px 0;
        transition: transform 0.2s;
    }
    .comment-box:hover {
        transform: translateX(4px);
        box-shadow: 0 4px 20px rgba(255, 75, 75, 0.1);
    }
    .comment-author {
        font-weight: 700;
        color: #E0E0E0;
        font-size: 0.95rem;
    }
    .comment-text {
        color: #B0B8C8;
        margin-top: 6px;
        font-size: 0.92rem;
        line-height: 1.6;
        white-space: pre-wrap;
    }
    .comment-meta {
        color: #5A6577;
        font-size: 0.78rem;
        margin-top: 8px;
    }

    /* ─── TOP 댓글 ─── */
    .top-comment-box {
        background: linear-gradient(135deg, #1E2536, #2A2040);
        border: 1px solid #3D2D5C;
        border-left: 4px solid #FF8E53;
        padding: 16px 20px;
        margin-bottom: 12px;
        border-radius: 0 12px 12px 0;
    }

    /* ─── AI 요약 카드 ─── */
    .ai-summary-card {
        background: linear-gradient(135deg, #1A2040, #1E2850);
        border: 1px solid #3D4A6B;
        border-radius: 16px;
        padding: 28px;
        margin: 20px 0;
        position: relative;
        overflow: hidden;
    }
    .ai-summary-card::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 3px;
        background: linear-gradient(90deg, #667eea, #764ba2, #FF4B4B);
    }
    .ai-summary-title {
        font-size: 1.1rem;
        font-weight: 700;
        color: #C8B6FF;
        margin-bottom: 12px;
    }
    .ai-summary-text {
        color: #C8D0DC;
        font-size: 0.95rem;
        line-height: 1.8;
    }

    /* ─── 도넛 차트 컨테이너 ─── */
    .donut-container {
        display: flex;
        justify-content: center;
        align-items: center;
        gap: 40px;
        flex-wrap: wrap;
        margin: 20px 0;
    }
    .donut-item {
        text-align: center;
    }
    .donut-label {
        color: #8892A0;
        font-size: 0.85rem;
        margin-top: 8px;
    }

    /* ─── 바 차트 커스텀 ─── */
    .custom-bar-container {
        background: linear-gradient(135deg, #1A2033, #212944);
        border: 1px solid #2D3548;
        border-radius: 16px;
        padding: 24px;
        margin: 10px 0;
    }
    .custom-bar-row {
        display: flex;
        align-items: center;
        margin-bottom: 14px;
    }
    .custom-bar-label {
        color: #B0B8C8;
        font-size: 0.88rem;
        width: 80px;
        text-align: right;
        margin-right: 14px;
        font-weight: 600;
    }
    .custom-bar-track {
        flex: 1;
        background-color: #1A1F2E;
        border-radius: 20px;
        height: 28px;
        overflow: hidden;
        position: relative;
    }
    .custom-bar-fill {
        height: 100%;
        border-radius: 20px;
        display: flex;
        align-items: center;
        padding-left: 12px;
        font-size: 0.8rem;
        font-weight: 700;
        color: white;
        transition: width 0.8s ease;
        min-width: 40px;
    }

    /* ─── 사이드바 ─── */
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #141824, #1A2035);
        border-right: 1px solid #2D3548;
    }
    section[data-testid="stSidebar"] .stRadio > label {
        color: #FAFAFA !important;
        font-weight: 600 !important;
    }
    section[data-testid="stSidebar"] .stRadio [role="radiogroup"] label {
        color: #E0E0E0 !important;
        background-color: #1E2536 !important;
        border: 1px solid #2D3548 !important;
        border-radius: 10px !important;
        padding: 10px 14px !important;
        margin-bottom: 6px !important;
        transition: all 0.2s;
    }
    section[data-testid="stSidebar"] .stRadio [role="radiogroup"] label:hover {
        border-color: #FF4B4B !important;
        background-color: #252D40 !important;
    }
    section[data-testid="stSidebar"] .stRadio [role="radiogroup"] label[data-checked="true"],
    section[data-testid="stSidebar"] .stRadio [role="radiogroup"] label[aria-checked="true"] {
        background-color: #2A1525 !important;
        border-color: #FF4B4B !important;
        color: #FF8E53 !important;
    }
    section[data-testid="stSidebar"] .stNumberInput label {
        color: #E0E0E0 !important;
    }
    section[data-testid="stSidebar"] h5 {
        color: #FF8E53 !important;
    }

    /* ─── 입력창 ─── */
    .stTextInput > div > div > input {
        background-color: #1A2033 !important;
        border: 1px solid #2D3548 !important;
        border-radius: 10px !important;
        color: #FAFAFA !important;
        padding: 12px 16px !important;
        font-size: 1rem !important;
    }
    .stTextInput > div > div > input:focus {
        border-color: #FF4B4B !important;
        box-shadow: 0 0 0 2px rgba(255, 75, 75, 0.2) !important;
    }

    /* ─── 다운로드 버튼 ─── */
    .stDownloadButton > button {
        background: linear-gradient(90deg, #00C853, #00E676) !important;
        border: none !important;
        border-radius: 10px !important;
        color: #0E1117 !important;
        font-weight: 700 !important;
    }

    /* ─── 탭 ─── */
    .stTabs [data-baseweb="tab-list"] {
        background-color: #1A2033;
        border-radius: 12px;
        padding: 4px;
        gap: 4px;
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 8px;
        color: #8892A0;
        font-weight: 600;
    }
    .stTabs [aria-selected="true"] {
        background-color: #2A3350 !important;
        color: #FF4B4B !important;
    }

    /* ─── 구분선 ─── */
    hr { border-color: #2D3548 !important; }

    /* ─── 데이터프레임 ─── */
    .stDataFrame [data-testid="stDataFrameResizable"] {
        border: 1px solid #2D3548 !important;
        border-radius: 12px !important;
        overflow: hidden;
    }
    [data-testid="stMetricValue"] {
        color: #FF4B4B !important;
        font-weight: 800 !important;
    }
</style>
""", unsafe_allow_html=True)

# ============================================================
# API 키
# ============================================================
YOUTUBE_API_KEY = st.secrets["YOUTUBE_API_KEY"]
OPENAI_API_KEY = st.secrets.get("OPENAI_API_KEY", "")

# ============================================================
# 함수들
# ============================================================
def extract_video_id(url):
    patterns = [
        r'(?:https?://)?(?:www\.)?youtube\.com/watch\?v=([a-zA-Z0-9_-]{11})',
        r'(?:https?://)?youtu\.be/([a-zA-Z0-9_-]{11})',
        r'(?:https?://)?(?:www\.)?youtube\.com/embed/([a-zA-Z0-9_-]{11})',
        r'(?:https?://)?(?:www\.)?youtube\.com/shorts/([a-zA-Z0-9_-]{11})',
        r'^([a-zA-Z0-9_-]{11})$',
    ]
    for p in patterns:
        m = re.search(p, url.strip())
        if m:
            return m.group(1)
    return None


def get_video_info(youtube, video_id):
    try:
        resp = youtube.videos().list(part="snippet,statistics", id=video_id).execute()
        if resp["items"]:
            s = resp["items"][0]["snippet"]
            t = resp["items"][0]["statistics"]
            return {
                "title": s.get("title", ""),
                "channel": s.get("channelTitle", ""),
                "published": s.get("publishedAt", "")[:10],
                "views": int(t.get("viewCount", 0)),
                "likes": int(t.get("likeCount", 0)),
                "comments_count": int(t.get("commentCount", 0)),
                "thumbnail": s.get("thumbnails", {}).get("high", {}).get("url", ""),
            }
    except HttpError as e:
        st.error(f"영상 정보 오류: {e}")
    return None


def get_all_comments(youtube, video_id, max_comments, progress_bar, status_text):
    comments = []
    npt = None
    try:
        while len(comments) < max_comments:
            req = youtube.commentThreads().list(
                part="snippet", videoId=video_id, maxResults=100,
                order="relevance", pageToken=npt, textFormat="plainText"
            )
            resp = req.execute()
            for item in resp.get("items", []):
                if len(comments) >= max_comments:
                    break
                sn = item["snippet"]["topLevelComment"]["snippet"]
                comments.append({
                    "작성자": sn.get("authorDisplayName", ""),
                    "댓글": sn.get("textDisplay", ""),
                    "좋아요": sn.get("likeCount", 0),
                    "작성일": sn.get("publishedAt", "")[:10],
                    "수정일": sn.get("updatedAt", "")[:10],
                })
            progress_bar.progress(min(len(comments) / max_comments, 1.0))
            status_text.text(f"💬 {len(comments):,}개 수집 중...")
            npt = resp.get("nextPageToken")
            if not npt:
                break
    except HttpError as e:
        reason = ""
        if e.error_details:
            reason = e.error_details[0].get("reason", "")
        if reason == "commentsDisabled":
            st.warning("⚠️ 댓글이 비활성화된 영상입니다.")
        else:
            st.error(f"댓글 수집 오류: {e}")
    progress_bar.progress(1.0)
    status_text.text(f"✅ 총 {len(comments):,}개 수집 완료!")
    return comments


def format_number(n):
    if n >= 100000000:
        return f"{n/100000000:.1f}억"
    elif n >= 10000:
        return f"{n/10000:.1f}만"
    elif n >= 1000:
        return f"{n/1000:.1f}천"
    return f"{n:,}"


def summarize_comments(comments_list, video_title):
    """OpenAI로 댓글 요약"""
    if not OPENAI_API_KEY:
        return None
    try:
        client = OpenAI(api_key=OPENAI_API_KEY)
        sample = comments_list[:200]
        comments_text = "\n".join([f"- {c['댓글']}" for c in sample])
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "너는 유튜브 댓글을 분석하는 전문가야. 한국어로 답변해."},
                {"role": "user", "content": f"""
다음은 유튜브 영상 '{video_title}'의 댓글들이야.

{comments_text}

아래 형식으로 분석해줘:

🗣️ **전체 분위기**: (댓글들의 전반적인 분위기를 2~3줄로)

📌 **자주 언급되는 주제 TOP 3**:
1. ...
2. ...
3. ...

💬 **대표 의견 요약**: (시청자들이 공통적으로 하는 말을 3~4줄로 자연스럽게)

😊 **긍정 vs 부정 비율**: (대략적인 비율과 한줄 설명)
"""}
            ],
            max_tokens=800,
            temperature=0.7
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"요약 생성 중 오류: {e}"


def make_custom_bar_chart(data_dict, colors, title):
    """둥근 커스텀 바 차트 HTML 생성"""
    if not data_dict:
        return ""
    max_val = max(data_dict.values()) if max(data_dict.values()) > 0 else 1
    bars_html = ""
    for i, (label, value) in enumerate(data_dict.items()):
        pct = (value / max_val) * 100
        color = colors[i % len(colors)]
        bars_html += f"""
        <div class="custom-bar-row">
            <div class="custom-bar-label">{label}</div>
            <div class="custom-bar-track">
                <div class="custom-bar-fill" style="width: {max(pct, 8)}%; background: linear-gradient(90deg, {color}, {color}dd);">
                    {value:,}
                </div>
            </div>
        </div>
        """
    return f"""
    <div class="custom-bar-container">
        <div style="color:#E0E0E0; font-weight:700; font-size:1.05rem; margin-bottom:18px;">{title}</div>
        {bars_html}
    </div>
    """


def make_donut_svg(percentage, color, size=120):
    """SVG 도넛 차트"""
    radius = 45
    circumference = 2 * 3.14159 * radius
    offset = circumference - (percentage / 100) * circumference
    return f"""
    <svg width="{size}" height="{size}" viewBox="0 0 120 120">
        <circle cx="60" cy="60" r="{radius}" fill="none" stroke="#1A1F2E" stroke-width="12"/>
        <circle cx="60" cy="60" r="{radius}" fill="none" stroke="{color}" stroke-width="12"
                stroke-dasharray="{circumference}" stroke-dashoffset="{offset}"
                stroke-linecap="round" transform="rotate(-90 60 60)"
                style="transition: stroke-dashoffset 1s ease;"/>
        <text x="60" y="65" text-anchor="middle" fill="{color}" font-size="22" font-weight="800">
            {percentage:.0f}%
        </text>
    </svg>
    """

# ============================================================
# 사이드바
# ============================================================
with st.sidebar:
    st.markdown("""
    <div style="text-align:center; padding: 20px 0 10px 0;">
        <span style="font-size: 2.5rem;">📺</span><br>
        <span style="font-size: 1.1rem; font-weight: 700; color: #FF4B4B;">댓글 수집기</span>
    </div>
    """, unsafe_allow_html=True)
    st.divider()
    st.markdown("##### ⚙️ 수집 설정")

    collect_mode = st.radio(
        "수집 범위",
        options=["auto", "custom"],
        format_func=lambda x: "🔄 전체 수집 (자동)" if x == "auto" else "✏️ 수량 직접 지정",
    )
    if collect_mode == "custom":
        custom_max = st.number_input("수집할 댓글 수", min_value=10, max_value=10000, value=200, step=50)

    st.divider()
    st.markdown(
        "<p style='text-align:center; color:#5A6577; font-size:0.75rem;'>YouTube Data API v3</p>",
        unsafe_allow_html=True
    )

# ============================================================
# 메인 UI
# ============================================================
st.markdown('<div class="main-header">유튜브 댓글 수집기</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">영상 링크를 넣으면 댓글을 자동으로 수집합니다</div>', unsafe_allow_html=True)

url_input = st.text_input("링크", placeholder="https://www.youtube.com/watch?v=...", label_visibility="collapsed")
st.markdown(
    "<p style='text-align:center; color:#5A6577; font-size:0.82rem; margin-top:-10px;'>"
    "⬆️ 유튜브 영상 링크를 붙여넣으세요</p>", unsafe_allow_html=True
)

col1, col2, col3 = st.columns([1, 1, 4])
with col1:
    search_button = st.button("🔍 댓글 수집", type="primary", use_container_width=True)
with col2:
    if st.button("🗑️ 초기화", use_container_width=True):
        st.session_state.clear()
        st.rerun()

# ============================================================
# 수집 실행
# ============================================================
if search_button:
    if not url_input:
        st.error("❌ 링크를 입력해주세요.")
        st.stop()
    video_id = extract_video_id(url_input)
    if not video_id:
        st.error("❌ 유효한 유튜브 링크가 아닙니다.")
        st.stop()
    try:
        youtube = build("youtube", "v3", developerKey=YOUTUBE_API_KEY)
    except Exception as e:
        st.error(f"❌ API 연결 실패: {e}")
        st.stop()

    with st.spinner("📡 영상 정보를 불러오는 중..."):
        video_info = get_video_info(youtube, video_id)
    if not video_info:
        st.error("❌ 영상을 찾을 수 없습니다.")
        st.stop()

    st.session_state["video_info"] = video_info
    st.session_state["video_id"] = video_id

    total = video_info["comments_count"]
    if collect_mode == "auto":
        max_to_collect = min(total, 10000)
    else:
        max_to_collect = min(custom_max, total, 10000)

    st.markdown(f"**📊 전체 댓글 {total:,}개 중 최대 {max_to_collect:,}개 수집**")
    progress_bar = st.progress(0)
    status_text = st.empty()
    comments = get_all_comments(youtube, video_id, max_to_collect, progress_bar, status_text)
    st.session_state["comments"] = comments

    # AI 요약
    if OPENAI_API_KEY and comments:
        with st.spinner("🤖 AI가 댓글을 분석하는 중..."):
            summary = summarize_comments(comments, video_info["title"])
            st.session_state["summary"] = summary

# ============================================================
# 결과 표시
# ============================================================
if "video_info" in st.session_state and "comments" in st.session_state:
    video_info = st.session_state["video_info"]
    comments = st.session_state["comments"]

    st.divider()

    # 영상 정보
    col_thumb, col_info = st.columns([1, 2])
    with col_thumb:
        if video_info["thumbnail"]:
            st.image(video_info["thumbnail"], use_container_width=True)
    with col_info:
        st.markdown(f"""
        <div class="video-card">
            <div class="video-title">{video_info['title']}</div>
            <div class="video-channel">📢 {video_info['channel']}  ·  📅 {video_info['published']}</div>
        </div>
        """, unsafe_allow_html=True)
        c1, c2, c3, c4 = st.columns(4)
        for col, (icon, label, value) in zip(
            [c1, c2, c3, c4],
            [("👀","조회수",format_number(video_info['views'])),
             ("👍","좋아요",format_number(video_info['likes'])),
             ("💬","전체 댓글",format_number(video_info['comments_count'])),
             ("📥","수집 완료",f"{len(comments):,}개")]
        ):
            col.markdown(f"""
            <div class="stat-card">
                <div style="font-size:1.5rem;">{icon}</div>
                <div class="stat-number">{value}</div>
                <div class="stat-label">{label}</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # AI 요약
    if "summary" in st.session_state and st.session_state["summary"]:
        st.markdown(f"""
        <div class="ai-summary-card">
            <div class="ai-summary-title">🤖 AI 댓글 분석 요약</div>
            <div class="ai-summary-text">{st.session_state['summary']}</div>
        </div>
        """, unsafe_allow_html=True)

    st.divider()

    if comments:
        st.markdown(f"""
        <div style="text-align:center; margin-bottom: 20px;">
            <span style="font-size: 1.6rem; font-weight: 800; color: #FAFAFA;">💬 수집된 댓글 </span>
            <span style="font-size: 1.6rem; font-weight: 800; color: #FF4B4B;">{len(comments):,}개</span>
        </div>
        """, unsafe_allow_html=True)

        df = pd.DataFrame(comments)
        tab1, tab2, tab3 = st.tabs(["📋 테이블", "💬 카드", "📊 통계"])

        # ===== 테이블 =====
        with tab1:
            search_term = st.text_input("검색", placeholder="🔎 키워드 검색...", key="ts", label_visibility="collapsed")
            if search_term:
                fdf = df[df["댓글"].str.contains(search_term, case=False, na=False)]
                st.markdown(f"<p style='color:#FF8E53; font-weight:600;'>🔎 '{search_term}' → {len(fdf)}개</p>", unsafe_allow_html=True)
            else:
                fdf = df

            ml = int(df["좋아요"].max()) if len(df) > 0 and int(df["좋아요"].max()) > 0 else 1

            st.dataframe(
                fdf,
                use_container_width=True,
                height=600,
                column_config={
                    "좋아요": st.column_config.ProgressColumn("👍 좋아요", format="%d", min_value=0, max_value=ml),
                    "작성자": st.column_config.TextColumn("👤 작성자", width="medium"),
                    "댓글": st.column_config.TextColumn("💬 댓글", width="large"),
                    "작성일": st.column_config.TextColumn("📅 작성일", width="small"),
                    "수정일": st.column_config.TextColumn("✏️ 수정일", width="small"),
                }
            )

        # ===== 카드 =====
        with tab2:
            search_card = st.text_input("검색", placeholder="🔎 키워드 검색...", key="cs", label_visibility="collapsed")
            dc = comments
            if search_card:
                dc = [c for c in comments if search_card.lower() in c["댓글"].lower()]
                st.markdown(f"<p style='color:#FF8E53; font-weight:600;'>🔎 '{search_card}' → {len(dc)}개</p>", unsafe_allow_html=True)

            ipp = 30
            tp = max(1, (len(dc) + ipp - 1) // ipp)
            page = st.selectbox("p", range(1, tp+1), format_func=lambda x: f"📄 {x}/{tp} 페이지", label_visibility="collapsed")
            si = (page-1)*ipp
            for comment in dc[si:si+ipp]:
                badge = "
