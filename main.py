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
# 스타일
# ============================================================
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        text-align: center;
        color: #FF0000;
        margin-bottom: 0.5rem;
    }
    .sub-header {
        font-size: 1.1rem;
        text-align: center;
        color: #666;
        margin-bottom: 2rem;
    }
    .comment-box {
        background-color: #f9f9f9;
        border-left: 4px solid #FF0000;
        padding: 12px 16px;
        margin-bottom: 10px;
        border-radius: 0 8px 8px 0;
    }
    .comment-author {
        font-weight: bold;
        color: #333;
        font-size: 0.95rem;
    }
    .comment-text {
        color: #555;
        margin-top: 4px;
        font-size: 0.9rem;
    }
    .comment-meta {
        color: #999;
        font-size: 0.8rem;
        margin-top: 4px;
    }
    .stat-card {
        background: linear-gradient(135deg, #FF0000, #cc0000);
        color: white;
        padding: 20px;
        border-radius: 12px;
        text-align: center;
    }
</style>
""", unsafe_allow_html=True)

# ============================================================
# YouTube API 키 가져오기
# ============================================================
def get_api_key():
    """Streamlit secrets 또는 사이드바 입력에서 API 키를 가져옵니다."""
    # 1순위: secrets.toml에서 가져오기
    try:
        api_key = st.secrets["YOUTUBE_API_KEY"]
        if api_key:
            return api_key
    except (KeyError, FileNotFoundError):
        pass

    # 2순위: 사이드바에서 직접 입력
    return None


# ============================================================
# 유튜브 영상 ID 추출
# ============================================================
def extract_video_id(url):
    """다양한 유튜브 URL 형식에서 영상 ID를 추출합니다."""
    patterns = [
        # 표준 URL: https://www.youtube.com/watch?v=VIDEO_ID
        r'(?:https?://)?(?:www\.)?youtube\.com/watch\?v=([a-zA-Z0-9_-]{11})',
        # 짧은 URL: https://youtu.be/VIDEO_ID
        r'(?:https?://)?youtu\.be/([a-zA-Z0-9_-]{11})',
        # 임베드 URL: https://www.youtube.com/embed/VIDEO_ID
        r'(?:https?://)?(?:www\.)?youtube\.com/embed/([a-zA-Z0-9_-]{11})',
        # shorts URL: https://www.youtube.com/shorts/VIDEO_ID
        r'(?:https?://)?(?:www\.)?youtube\.com/shorts/([a-zA-Z0-9_-]{11})',
        # 단독 VIDEO_ID
        r'^([a-zA-Z0-9_-]{11})$',
    ]
    for pattern in patterns:
        match = re.search(pattern, url.strip())
        if match:
            return match.group(1)
    return None


# ============================================================
# 영상 정보 가져오기
# ============================================================
def get_video_info(youtube, video_id):
    """영상의 기본 정보를 가져옵니다."""
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
                "description": snippet.get("description", "")[:300],
                "views": int(stats.get("viewCount", 0)),
                "likes": int(stats.get("likeCount", 0)),
                "comments_count": int(stats.get("commentCount", 0)),
                "thumbnail": snippet.get("thumbnails", {}).get("high", {}).get("url", ""),
            }
    except HttpError as e:
        st.error(f"영상 정보를 가져오는 중 오류 발생: {e}")
    return None


# ============================================================
# 댓글 가져오기
# ============================================================
def get_comments(youtube, video_id, max_comments=100, order="relevance"):
    """영상의 댓글을 가져옵니다."""
    comments = []
    next_page_token = None

    try:
        while len(comments) < max_comments:
            request = youtube.commentThreads().list(
                part="snippet",
                videoId=video_id,
                maxResults=min(100, max_comments - len(comments)),
                order=order,
                pageToken=next_page_token,
                textFormat="plainText"
            )
            response = request.execute()

            for item in response.get("items", []):
                snippet = item["snippet"]["topLevelComment"]["snippet"]
                comments.append({
                    "작성자": snippet.get("authorDisplayName", ""),
                    "댓글": snippet.get("textDisplay", ""),
                    "좋아요": snippet.get("likeCount", 0),
                    "작성일": snippet.get("publishedAt", "")[:10],
                    "수정일": snippet.get("updatedAt", "")[:10],
                })

            next_page_token = response.get("nextPageToken")
            if not next_page_token:
                break

    except HttpError as e:
        error_reason = e.error_details[0]["reason"] if e.error_details else ""
        if error_reason == "commentsDisabled":
            st.warning("⚠️ 이 영상은 댓글이 비활성화되어 있습니다.")
        elif error_reason == "forbidden":
            st.error("🚫 API 키에 YouTube Data API v3 권한이 없습니다. Google Cloud Console에서 활성화하세요.")
        else:
            st.error(f"댓글을 가져오는 중 오류 발생: {e}")

    return comments


# ============================================================
# 메인 UI
# ============================================================
st.markdown('<div class="main-header">📺 유튜브 댓글 수집기</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">유튜브 영상 링크를 입력하면 댓글을 수집하고 분석합니다</div>', unsafe_allow_html=True)

# ----- 사이드바 설정 -----
with st.sidebar:
    st.header("⚙️ 설정")

    api_key = get_api_key()
    if not api_key:
        st.warning("API 키가 secrets에 등록되지 않았습니다. 아래에 직접 입력하세요.")
        api_key = st.text_input(
            "YouTube Data API v3 키",
            type="password",
            help="Google Cloud Console에서 발급받은 API 키를 입력하세요."
        )

    st.divider()

    max_comments = st.slider(
        "최대 수집 댓글 수",
        min_value=10,
        max_value=500,
        value=100,
        step=10,
        help="한 번에 수집할 최대 댓글 수입니다."
    )

    order = st.radio(
        "정렬 기준",
        options=["relevance", "time"],
        format_func=lambda x: "관련성순" if x == "relevance" else "최신순",
        help="댓글 정렬 방식을 선택하세요."
    )

    st.divider()
    st.markdown("### 📖 사용 방법")
    st.markdown("""
    1. **YouTube Data API v3** 키를 준비합니다.
    2. 유튜브 영상 링크를 입력합니다.
    3. **댓글 수집** 버튼을 클릭합니다.
    4. 결과를 확인하고 CSV로 다운로드합니다.
    """)

    st.divider()
    st.markdown("### 🔑 API 키 발급 방법")
    st.markdown("""
    1. [Google Cloud Console](https://console.cloud.google.com/) 접속
    2. 새 프로젝트 생성
    3. **YouTube Data API v3** 활성화
    4. 사용자 인증 정보 → API 키 생성
    """)

# ----- 메인 영역 -----
url_input = st.text_input(
    "🔗 유튜브 영상 링크를 입력하세요",
    placeholder="https://www.youtube.com/watch?v=...",
    help="유튜브 영상의 URL을 붙여넣으세요. youtu.be 형식도 지원합니다."
)

col_btn1, col_btn2, col_btn3 = st.columns([1, 1, 3])
with col_btn1:
    search_button = st.button("🔍 댓글 수집", type="primary", use_container_width=True)
with col_btn2:
    clear_button = st.button("🗑️ 초기화", use_container_width=True)

if clear_button:
    st.session_state.clear()
    st.rerun()

# ----- 댓글 수집 실행 -----
if search_button:
    # API 키 확인
    if not api_key:
        st.error("❌ YouTube API 키를 입력해주세요. (사이드바에서 입력 가능)")
        st.stop()

    # URL 확인
    if not url_input:
        st.error("❌ 유튜브 영상 링크를 입력해주세요.")
        st.stop()

    # 영상 ID 추출
    video_id = extract_video_id(url_input)
    if not video_id:
        st.error("❌ 유효한 유튜브 링크가 아닙니다. 다시 확인해주세요.")
        st.stop()

    # YouTube API 클라이언트 생성
    try:
        youtube = build("youtube", "v3", developerKey=api_key)
    except Exception as e:
        st.error(f"❌ API 클라이언트 생성 실패: {e}")
        st.stop()

    # 영상 정보 가져오기
    with st.spinner("📡 영상 정보를 불러오는 중..."):
        video_info = get_video_info(youtube, video_id)

    if not video_info:
        st.error("❌ 영상 정보를 찾을 수 없습니다. 링크를 확인해주세요.")
        st.stop()

    # 세션에 영상 정보 저장
    st.session_state["video_info"] = video_info
    st.session_state["video_id"] = video_id

    # 댓글 가져오기
    with st.spinner(f"💬 댓글을 수집하는 중... (최대 {max_comments}개)"):
        comments = get_comments(youtube, video_id, max_comments=max_comments, order=order)

    st.session_state["comments"] = comments

# ----- 결과 표시 -----
if "video_info" in st.session_state and "comments" in st.session_state:
    video_info = st.session_state["video_info"]
    comments = st.session_state["comments"]

    st.divider()

    # 영상 정보 표시
    st.markdown("## 🎬 영상 정보")
    col_thumb, col_info = st.columns([1, 2])

    with col_thumb:
        if video_info["thumbnail"]:
            st.image(video_info["thumbnail"], use_container_width=True)

    with col_info:
        st.markdown(f"### {video_info['title']}")
        st.markdown(f"**채널:** {video_info['channel']}")
        st.markdown(f"**업로드일:** {video_info['published']}")

        stat1, stat2, stat3 = st.columns(3)
        with stat1:
            st.metric("👀 조회수", f"{video_info['views']:,}")
        with stat2:
            st.metric("👍 좋아요", f"{video_info['likes']:,}")
        with stat3:
            st.metric("💬 전체 댓글", f"{video_info['comments_count']:,}")

    st.divider()

    # 댓글 결과
    if comments:
        st.markdown(f"## 💬 수집된 댓글 ({len(comments)}개)")

        df = pd.DataFrame(comments)

        # 탭 구성
        tab1, tab2 = st.tabs(["📋 테이블 보기", "💬 카드 보기"])

        with tab1:
            # 검색 필터
            search_term = st.text_input("🔎 댓글 내 검색", placeholder="검색어를 입력하세요...")

            if search_term:
                filtered_df = df[df["댓글"].str.contains(search_term, case=False, na=False)]
                st.info(f"'{search_term}' 검색 결과: {len(filtered_df)}개")
            else:
                filtered_df = df

            st.dataframe(
                filtered_df,
                use_container_width=True,
                height=500,
                column_config={
                    "좋아요": st.column_config.NumberColumn("👍 좋아요", format="%d"),
                    "작성자": st.column_config.TextColumn("작성자", width="medium"),
                    "댓글": st.column_config.TextColumn("댓글", width="large"),
                    "작성일": st.column_config.TextColumn("작성일", width="small"),
                    "수정일": st.column_config.TextColumn("수정일", width="small"),
                }
            )

        with tab2:
            search_term_card = st.text_input("🔎 댓글 내 검색 ", placeholder="검색어를 입력하세요...", key="card_search")

            display_comments = comments
            if search_term_card:
                display_comments = [c for c in comments if search_term_card.lower() in c["댓글"].lower()]
                st.info(f"'{search_term_card}' 검색 결과: {len(display_comments)}개")

            for i, comment in enumerate(display_comments):
                st.markdown(f"""
                <div class="comment-box">
                    <div class="comment-author">👤 {comment['작성자']}</div>
                    <div class="comment-text">{comment['댓글']}</div>
                    <div class="comment-meta">👍 {comment['좋아요']} &nbsp;|&nbsp; 📅 {comment['작성일']}</div>
                </div>
                """, unsafe_allow_html=True)

                if i >= 49:
                    st.info(f"카드 보기는 최대 50개까지 표시됩니다. 전체 {len(display_comments)}개는 테이블 보기를 이용하세요.")
                    break

        st.divider()

        # 간단한 통계
        st.markdown("## 📊 간단한 통계")
        stat_col1, stat_col2, stat_col3, stat_col4 = st.columns(4)

        with stat_col1:
            st.metric("총 수집 댓글", f"{len(comments)}개")
        with stat_col2:
            avg_likes = sum(c["좋아요"] for c in comments) / len(comments) if comments else 0
            st.metric("평균 좋아요", f"{avg_likes:.1f}")
        with stat_col3:
            max_likes = max(c["좋아요"] for c in comments) if comments else 0
            st.metric("최대 좋아요", f"{max_likes}")
        with stat_col4:
            avg_len = sum(len(c["댓글"]) for c in comments) / len(comments) if comments else 0
            st.metric("평균 댓글 길이", f"{avg_len:.0f}자")

        # 좋아요 TOP 5
        st.markdown("### 🏆 좋아요 TOP 5 댓글")
        top_comments = sorted(comments, key=lambda x: x["좋아요"], reverse=True)[:5]
        for i, comment in enumerate(top_comments, 1):
            st.markdown(f"""
            <div class="comment-box">
                <div class="comment-author">🥇 #{i} &nbsp; 👤 {comment['작성자']} &nbsp; (👍 {comment['좋아요']})</div>
                <div class="comment-text">{comment['댓글']}</div>
            </div>
            """, unsafe_allow_html=True)

        st.divider()

        # CSV 다운로드
        csv_data = df.to_csv(index=False, encoding="utf-8-sig")
        st.download_button(
            label="📥 CSV 파일 다운로드",
            data=csv_data,
            file_name=f"youtube_comments_{st.session_state.get('video_id', 'video')}.csv",
            mime="text/csv",
            use_container_width=True
        )

    else:
        st.warning("수집된 댓글이 없습니다.")

# ----- 푸터 -----
st.divider()
st.markdown(
    "<p style='text-align:center; color:#aaa; font-size:0.85rem;'>"
    "당곡고등학교 학습용 유튜브 댓글 수집기 | YouTube Data API v3 활용"
    "</p>",
    unsafe_allow_html=True
)
