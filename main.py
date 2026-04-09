import streamlit as st
import pandas as pd
import re
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# ============================================================
# 페이지 설정
# ============================================================
st.set_page_config(
    page_title="유튜브 댓글 수집기",
    page_icon="📺",
    layout="wide"
)

# ============================================================
# 다크 테마 커스텀 스타일
# ============================================================
st.markdown("""
<style>
    /* ─── 전체 배경 ─── */
    .stApp {
        background: linear-gradient(180deg, #0E1117 0%, #151B28 50%, #1A1F2E 100%);
    }

    /* ─── 메인 헤더 ─── */
    .main-header {
        font-size: 2.8rem;
        font-weight: 800;
        text-align: center;
        background: linear-gradient(90deg, #FF4B4B, #FF8E53);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.3rem;
        letter-spacing: -1px;
    }
    .sub-header {
        font-size: 1.05rem;
        text-align: center;
        color: #8892A0;
        margin-bottom: 2rem;
    }

    /* ─── 영상 정보 카드 ─── */
    .video-card {
        background: linear-gradient(135deg, #1E2536 0%, #252D40 100%);
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
        transition: transform 0.2s, box-shadow 0.2s;
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
        background: linear-gradient(135deg, #1A2033 0%, #212944 100%);
        border: 1px solid #2D3548;
        border-left: 4px solid #FF4B4B;
        padding: 16px 20px;
        margin-bottom: 12px;
        border-radius: 0 12px 12px 0;
        transition: transform 0.2s, box-shadow 0.2s;
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

    /* ─── TOP 댓글 카드 ─── */
    .top-comment-box {
        background: linear-gradient(135deg, #1E2536 0%, #2A2040 100%);
        border: 1px solid #3D2D5C;
        border-left: 4px solid #FF8E53;
        padding: 16px 20px;
        margin-bottom: 12px;
        border-radius: 0 12px 12px 0;
    }

    /* ─── 데이터프레임 커스텀 ─── */
    .stDataFrame {
        border-radius: 12px;
        overflow: hidden;
    }
    .stDataFrame [data-testid="stDataFrameResizable"] {
        border: 1px solid #2D3548;
        border-radius: 12px;
    }

    /* ─── 사이드바 ─── */
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #141824 0%, #1A2035 100%);
        border-right: 1px solid #2D3548;
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

    /* ─── 버튼 ─── */
    .stButton > button[kind="primary"] {
        background: linear-gradient(90deg, #FF4B4B, #FF6B6B) !important;
        border: none !important;
        border-radius: 10px !important;
        font-weight: 700 !important;
        letter-spacing: 0.5px;
        transition: all 0.3s !important;
    }
    .stButton > button[kind="primary"]:hover {
        background: linear-gradient(90deg, #FF6B6B, #FF8E53) !important;
        box-shadow: 0 4px 15px rgba(255, 75, 75, 0.4) !important;
    }
    .stButton > button:not([kind="primary"]) {
        background-color: #1A2033 !important;
        border: 1px solid #2D3548 !important;
        border-radius: 10px !important;
        color: #B0B8C8 !important;
    }

    /* ─── 다운로드 버튼 ─── */
    .stDownloadButton > button {
        background: linear-gradient(90deg, #00C853, #00E676) !important;
        border: none !important;
        border-radius: 10px !important;
        color: #0E1117 !important;
        font-weight: 700 !important;
    }
    .stDownloadButton > button:hover {
        box-shadow: 0 4px 15px rgba(0, 200, 83, 0.4) !important;
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
    hr {
        border-color: #2D3548 !important;
    }

    /* ─── 슬라이더 ─── */
    .stSlider [data-baseweb="slider"] [role="slider"] {
        background-color: #FF4B4B !important;
    }

    /* ─── 메트릭 숨기기 (기본 st.metric 대신 커스텀 사용) ─── */
    [data-testid="stMetricValue"] {
        color: #FF4B4B !important;
        font-weight: 800 !important;
    }
</style>
""", unsafe_allow_html=True)

# ============================================================
# API 키
# ============================================================
API_KEY = st.secrets["YOUTUBE_API_KEY"]

# ============================================================
# 유틸리티 함수
# ============================================================
def extract_video_id(url):
    patterns = [
        r'(?:https?://)?(?:www\.)?youtube\.com/watch\?v=([a-zA-Z0-9_-]{11})',
        r'(?:https?://)?youtu\.be/([a-zA-Z0-9_-]{11})',
        r'(?:https?://)?(?:www\.)?youtube\.com/embed/([a-zA-Z0-9_-]{11})',
        r'(?:https?://)?(?:www\.)?youtube\.com/shorts/([a-zA-Z0-9_-]{11})',
        r'^([a-zA-Z0-9_-]{11})$',
    ]
    for pattern in patterns:
        match = re.search(pattern, url.strip())
        if match:
            return match.group(1)
    return None


def get_video_info(youtube, video_id):
    try:
        response = youtube.videos().list(
            part="snippet,statistics",
            id=video_id
        ).execute()

        if response["items"]:
            item = response["items"][0]
            snippet = item["snippet"]
            stats = item["statistics"]
            return {
                "title": snippet.get("title", ""),
                "channel": snippet.get("channelTitle", ""),
                "published": snippet.get("publishedAt", "")[:10],
                "views": int(stats.get("viewCount", 0)),
                "likes": int(stats.get("likeCount", 0)),
                "comments_count": int(stats.get("commentCount", 0)),
                "thumbnail": snippet.get("thumbnails", {}).get("high", {}).get("url", ""),
            }
    except HttpError as e:
        st.error(f"영상 정보 오류: {e}")
    return None


def get_all_comments(youtube, video_id, max_comments, progress_bar, status_text):
    """영상의 댓글을 최대한 수집합니다."""
    comments = []
    next_page_token = None

    try:
        while len(comments) < max_comments:
            request = youtube.commentThreads().list(
                part="snippet",
                videoId=video_id,
                maxResults=100,
                order="relevance",
                pageToken=next_page_token,
                textFormat="plainText"
            )
            response = request.execute()

            for item in response.get("items", []):
                if len(comments) >= max_comments:
                    break
                snippet = item["snippet"]["topLevelComment"]["snippet"]
                comments.append({
                    "작성자": snippet.get("authorDisplayName", ""),
                    "댓글": snippet.get("textDisplay", ""),
                    "좋아요": snippet.get("likeCount", 0),
                    "작성일": snippet.get("publishedAt", "")[:10],
                    "수정일": snippet.get("updatedAt", "")[:10],
                })

            # 프로그레스 바 업데이트
            progress = min(len(comments) / max_comments, 1.0)
            progress_bar.progress(progress)
            status_text.text(f"💬 {len(comments):,}개 수집 중...")

            next_page_token = response.get("nextPageToken")
            if not next_page_token:
                break

    except HttpError as e:
        error_reason = ""
        if e.error_details:
            error_reason = e.error_details[0].get("reason", "")
        if error_reason == "commentsDisabled":
            st.warning("⚠️ 이 영상은 댓글이 비활성화되어 있습니다.")
        elif error_reason == "forbidden":
            st.error("🚫 API 키 권한 오류입니다.")
        else:
            st.error(f"댓글 수집 오류: {e}")

    progress_bar.progress(1.0)
    status_text.text(f"✅ 총 {len(comments):,}개 수집 완료!")
    return comments


def format_number(n):
    if n >= 100000000:
        return f"{n / 100000000:.1f}억"
    elif n >= 10000:
        return f"{n / 10000:.1f}만"
    elif n >= 1000:
        return f"{n / 1000:.1f}천"
    return f"{n:,}"

# ============================================================
# 사이드바 (간결하게)
# ============================================================
with st.sidebar:
    st.markdown("""
    <div style="text-align:center; padding: 20px 0 10px 0;">
        <span style="font-size: 2.5rem;">📺</span>
        <br>
        <span style="font-size: 1.1rem; font-weight: 700; color: #FF4B4B;">댓글 수집기</span>
    </div>
    """, unsafe_allow_html=True)

    st.divider()

    st.markdown("##### ⚙️ 수집 설정")

    collect_mode = st.radio(
        "수집 범위",
        options=["auto", "custom"],
        format_func=lambda x: "🔄 전체 수집 (자동)" if x == "auto" else "✏️ 수량 직접 지정",
        help="전체 수집: 영상의 모든 댓글을 수집합니다."
    )

    if collect_mode == "custom":
        custom_max = st.number_input(
            "수집할 댓글 수",
            min_value=10,
            max_value=10000,
            value=200,
            step=50
        )

    st.divider()
    st.markdown(
        "<p style='text-align:center; color:#5A6577; font-size:0.75rem;'>"
        "YouTube Data API v3"
        "</p>",
        unsafe_allow_html=True
    )

# ============================================================
# 메인 UI
# ============================================================
st.markdown('<div class="main-header">유튜브 댓글 수집기</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">영상 링크를 넣으면 댓글을 자동으로 수집합니다</div>', unsafe_allow_html=True)

# 링크 입력
url_input = st.text_input(
    "🔗 유튜브 영상 링크",
    placeholder="https://www.youtube.com/watch?v=...",
    label_visibility="collapsed"
)

# 안내 문구
st.markdown(
    "<p style='text-align:center; color:#5A6577; font-size:0.82rem; margin-top:-10px;'>"
    "⬆️ 위에 유튜브 영상 링크를 붙여넣으세요 (youtu.be, shorts 등 모든 형식 지원)"
    "</p>",
    unsafe_allow_html=True
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
        st.error("❌ 유튜브 영상 링크를 입력해주세요.")
        st.stop()

    video_id = extract_video_id(url_input)
    if not video_id:
        st.error("❌ 유효한 유튜브 링크가 아닙니다.")
        st.stop()

    try:
        youtube = build("youtube", "v3", developerKey=API_KEY)
    except Exception as e:
        st.error(f"❌ API 연결 실패: {e}")
        st.stop()

    # 영상 정보
    with st.spinner("📡 영상 정보를 불러오는 중..."):
        video_info = get_video_info(youtube, video_id)

    if not video_info:
        st.error("❌ 영상을 찾을 수 없습니다.")
        st.stop()

    st.session_state["video_info"] = video_info
    st.session_state["video_id"] = video_id

    # 수집할 댓글 수 결정
    total_comments = video_info["comments_count"]

    if collect_mode == "auto":
        # 전체 수집 (API 제한 고려하여 최대 10,000개)
        max_to_collect = min(total_comments, 10000)
    else:
        max_to_collect = min(custom_max, total_comments, 10000)

    # 댓글 수집 (프로그레스 바)
    st.markdown(f"**📊 전체 댓글 {total_comments:,}개 중 최대 {max_to_collect:,}개 수집**")
    progress_bar = st.progress(0)
    status_text = st.empty()

    comments = get_all_comments(youtube, video_id, max_to_collect, progress_bar, status_text)
    st.session_state["comments"] = comments

# ============================================================
# 결과 표시
# ============================================================
if "video_info" in st.session_state and "comments" in st.session_state:
    video_info = st.session_state["video_info"]
    comments = st.session_state["comments"]

    st.divider()

    # ───── 영상 정보 카드 ─────
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

        # 통계 카드
        c1, c2, c3, c4 = st.columns(4)
        stats = [
            ("👀", "조회수", format_number(video_info['views'])),
            ("👍", "좋아요", format_number(video_info['likes'])),
            ("💬", "전체 댓글", format_number(video_info['comments_count'])),
            ("📥", "수집 완료", f"{len(comments):,}개"),
        ]
        for col, (icon, label, value) in zip([c1, c2, c3, c4], stats):
            col.markdown(f"""
            <div class="stat-card">
                <div style="font-size:1.5rem;">{icon}</div>
                <div class="stat-number">{value}</div>
                <div class="stat-label">{label}</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    st.divider()

    # ───── 댓글 결과 ─────
    if comments:
        st.markdown(f"""
        <div style="text-align:center; margin-bottom: 20px;">
            <span style="font-size: 1.6rem; font-weight: 800; color: #FAFAFA;">
                💬 수집된 댓글 
            </span>
            <span style="font-size: 1.6rem; font-weight: 800; color: #FF4B4B;">
                {len(comments):,}개
            </span>
        </div>
        """, unsafe_allow_html=True)

        df = pd.DataFrame(comments)

        tab1, tab2, tab3 = st.tabs(["📋 테이블", "💬 카드", "📊 통계"])

        # ===== 테이블 탭 =====
        with tab1:
            search_term = st.text_input(
                "검색",
                placeholder="🔎 댓글에서 검색할 키워드를 입력하세요...",
                key="table_search",
                label_visibility="collapsed"
            )

            if search_term:
                filtered_df = df[df["댓글"].str.contains(search_term, case=False, na=False)]
                st.markdown(
                    f"<p style='color:#FF8E53; font-weight:600;'>"
                    f"🔎 '{search_term}' 검색 결과: {len(filtered_df)}개</p>",
                    unsafe_allow_html=True
                )
            else:
                filtered_df = df

            # 스타일링된 데이터프레임
            styled_df = filtered_df.style.set_properties(**{
                'background-color': '#1A2033',
                'color': '#C8D0DC',
                'border-color': '#2D3548',
                'font-size': '0.9rem',
            }).set_properties(
                subset=['댓글'],
                **{'text-align': 'left', 'max-width': '600px'}
            ).set_properties(
                subset=['좋아요'],
                **{'text-align': 'center', 'font-weight': 'bold', 'color': '#FF8E53'}
            ).set_properties(
                subset=['작성자'],
                **{'font-weight': 'bold', 'color': '#E0E0E0'}
            ).background_gradient(
                subset=['좋아요'],
                cmap='YlOrRd',
                low=0.3,
                high=0.9
            )

            st.dataframe(
                styled_df,
                use_container_width=True,
                height=600,
                column_config={
                    "좋아요": st.column_config.ProgressColumn(
                        "👍 좋아요",
                        format="%d",
                        min_value=0,
                        max_value=max(df["좋아요"]) if max(df["좋아요"]) > 0 else 1,
                    ),
                    "작성자": st.column_config.TextColumn("👤 작성자", width="medium"),
                    "댓글": st.column_config.TextColumn("💬 댓글", width="large"),
                    "작성일": st.column_config.TextColumn("📅 작성일", width="small"),
                    "수정일": st.column_config.TextColumn("✏️ 수정일", width="small"),
                }
            )

        # ===== 카드 탭 =====
        with tab2:
            search_card = st.text_input(
                "검색",
                placeholder="🔎 댓글에서 검색할 키워드를 입력하세요...",
                key="card_search",
                label_visibility="collapsed"
            )

            display_comments = comments
            if search_card:
                display_comments = [c for c in comments if search_card.lower() in c["댓글"].lower()]
                st.markdown(
                    f"<p style='color:#FF8E53; font-weight:600;'>"
                    f"🔎 '{search_card}' 검색 결과: {len(display_comments)}개</p>",
                    unsafe_allow_html=True
                )

            # 페이지네이션
            items_per_page = 30
            total_pages = max(1, (len(display_comments) + items_per_page - 1) // items_per_page)

            page = st.selectbox(
                "페이지",
                range(1, total_pages + 1),
                format_func=lambda x: f"📄 {x} / {total_pages} 페이지",
                label_visibility="collapsed"
            )

            start_idx = (page - 1) * items_per_page
            end_idx = start_idx + items_per_page
            page_comments = display_comments[start_idx:end_idx]

            for comment in page_comments:
                like_badge = ""
                if comment['좋아요'] >= 100:
                    like_badge = "🔥"
                elif comment['좋아요'] >= 10:
                    like_badge = "⭐"

                st.markdown(f"""
                <div class="comment-box">
                    <div class="comment-author">👤 {comment['작성자']} {like_badge}</div>
                    <div class="comment-text">{comment['댓글']}</div>
                    <div class="comment-meta">👍 {comment['좋아요']:,} &nbsp;|&nbsp; 📅 {comment['작성일']}</div>
                </div>
                """, unsafe_allow_html=True)

        # ===== 통계 탭 =====
        with tab3:
            st.markdown("<br>", unsafe_allow_html=True)

            # 기본 통계
            s1, s2, s3, s4 = st.columns(4)
            total = len(comments)
            avg_likes = sum(c["좋아요"] for c in comments) / total if total else 0
            max_likes = max(c["좋아요"] for c in comments) if total else 0
            avg_len = sum(len(c["댓글"]) for c in comments) / total if total else 0

            stats_data = [
                ("📝", "총 수집 댓글", f"{total:,}개"),
                ("👍", "평균 좋아요", f"{avg_likes:.1f}"),
                ("🔥", "최대 좋아요", f"{max_likes:,}"),
                ("📏", "평균 글자 수", f"{avg_len:.0f}자"),
            ]
            for col, (icon, label, value) in zip([s1, s2, s3, s4], stats_data):
                col.markdown(f"""
                <div class="stat-card">
                    <div style="font-size:1.5rem;">{icon}</div>
                    <div class="stat-number">{value}</div>
                    <div class="stat-label">{label}</div>
                </div>
                """, unsafe_allow_html=True)

            st.markdown("<br>", unsafe_allow_html=True)

            # 좋아요 분포
            st.markdown("#### 👍 좋아요 분포")
            like_ranges = {"0": 0, "1~5": 0, "6~20": 0, "21~100": 0, "100+": 0}
            for c in comments:
                likes = c["좋아요"]
                if likes == 0:
                    like_ranges["0"] += 1
                elif likes <= 5:
                    like_ranges["1~5"] += 1
                elif likes <= 20:
                    like_ranges["6~20"] += 1
                elif likes <= 100:
                    like_ranges["21~100"] += 1
                else:
                    like_ranges["100+"] += 1

            like_df = pd.DataFrame({
                "좋아요 범위": like_ranges.keys(),
                "댓글 수": like_ranges.values()
            })
            st.bar_chart(like_df.set_index("좋아요 범위"), color="#FF4B4B")

            # 댓글 길이 분포
            st.markdown("#### 📏 댓글 길이 분포")
            len_ranges = {"~10자": 0, "11~30자": 0, "31~100자": 0, "101~300자": 0, "300자+": 0}
            for c in comments:
                clen = len(c["댓글"])
                if clen <= 10:
                    len_ranges["~10자"] += 1
                elif clen <= 30:
                    len_ranges["11~30자"] += 1
                elif clen <= 100:
                    len_ranges["31~100자"] += 1
                elif clen <= 300:
                    len_ranges["101~300자"] += 1
                else:
                    len_ranges["300자+"] += 1

            len_df = pd.DataFrame({
                "댓글 길이": len_ranges.keys(),
                "댓글 수": len_ranges.values()
            })
            st.bar_chart(len_df.set_index("댓글 길이"), color="#
