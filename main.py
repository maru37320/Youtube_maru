import streamlit as st
import pandas as pd
import re
from collections import Counter
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from deep_translator import GoogleTranslator  # 번역 라이브러리 추가

# ============================================================
# 페이지 설정
# ============================================================
st.set_page_config(page_title="유튜브 댓글 수집기", page_icon="📺", layout="wide")

# ============================================================
# 스타일
# ============================================================
st.markdown("""
<style>
    .stApp {
        background: linear-gradient(180deg, #0E1117 0%, #151B28 50%, #1A1F2E 100%);
    }
    .main-header {
        font-size: 2.8rem; font-weight: 800; text-align: center;
        background: linear-gradient(90deg, #FF4B4B, #FF8E53);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        margin-bottom: 0.3rem;
    }
    .sub-header {
        font-size: 1.05rem; text-align: center; color: #8892A0; margin-bottom: 2rem;
    }
    .video-card {
        background: linear-gradient(135deg, #1E2536, #252D40);
        border: 1px solid #2D3548; border-radius: 16px; padding: 24px; margin-bottom: 20px;
    }
    .video-title { font-size: 1.3rem; font-weight: 700; color: #FFF; margin-bottom: 8px; }
    .video-channel { color: #8892A0; font-size: 0.95rem; }
    .stat-card {
        background: linear-gradient(135deg, #1E2536, #2A3350);
        border: 1px solid #2D3548; border-radius: 14px; padding: 20px;
        text-align: center; transition: transform 0.2s;
    }
    .stat-card:hover { transform: translateY(-3px); box-shadow: 0 8px 25px rgba(255,75,75,0.15); }
    .stat-number {
        font-size: 1.8rem; font-weight: 800;
        background: linear-gradient(90deg, #FF4B4B, #FF8E53);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    }
    .stat-label { font-size: 0.85rem; color: #8892A0; margin-top: 4px; }
    .comment-box {
        background: linear-gradient(135deg, #1A2033, #212944);
        border: 1px solid #2D3548; border-left: 4px solid #FF4B4B;
        padding: 16px 20px; margin-bottom: 12px; border-radius: 0 12px 12px 0;
        transition: transform 0.2s;
    }
    .comment-box:hover { transform: translateX(4px); box-shadow: 0 4px 20px rgba(255,75,75,0.1); }
    .comment-author { font-weight: 700; color: #E0E0E0; font-size: 0.95rem; }
    .comment-text {
        color: #B0B8C8; margin-top: 6px; font-size: 0.92rem;
        line-height: 1.6; white-space: pre-wrap;
    }
    .comment-meta { color: #5A6577; font-size: 0.78rem; margin-top: 8px; }
    .top-comment-box {
        background: linear-gradient(135deg, #1E2536, #2A2040);
        border: 1px solid #3D2D5C; border-left: 4px solid #FF8E53;
        padding: 16px 20px; margin-bottom: 12px; border-radius: 0 12px 12px 0;
    }
    .chart-container {
        background: linear-gradient(135deg, #1A2033, #212944);
        border: 1px solid #2D3548; border-radius: 16px; padding: 24px; margin: 10px 0;
    }
    .bar-row { display: flex; align-items: center; margin-bottom: 14px; }
    .bar-label {
        color: #B0B8C8; font-size: 0.88rem; width: 80px;
        text-align: right; margin-right: 14px; font-weight: 600;
    }
    .bar-track {
        flex: 1; background-color: #1A1F2E; border-radius: 20px;
        height: 28px; overflow: hidden;
    }
    .bar-fill {
        height: 100%; border-radius: 20px; display: flex; align-items: center;
        padding-left: 12px; font-size: 0.8rem; font-weight: 700; color: white;
        transition: width 0.8s ease; min-width: 40px;
    }
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #141824, #1A2035);
        border-right: 1px solid #2D3548;
    }
    section[data-testid="stSidebar"] .stRadio > label { color: #FAFAFA !important; font-weight: 600 !important; }
    section[data-testid="stSidebar"] .stRadio [role="radiogroup"] label {
        color: #E0E0E0 !important; background-color: #1E2536 !important;
        border: 1px solid #2D3548 !important; border-radius: 10px !important;
        padding: 10px 14px !important; margin-bottom: 6px !important;
    }
    section[data-testid="stSidebar"] .stRadio [role="radiogroup"] label:hover {
        border-color: #FF4B4B !important; background-color: #252D40 !important;
    }
    section[data-testid="stSidebar"] h5 { color: #FF8E53 !important; }
    section[data-testid="stSidebar"] .stNumberInput label { color: #E0E0E0 !important; }
    .stTextInput > div > div > input {
        background-color: #1A2033 !important; border: 1px solid #2D3548 !important;
        border-radius: 10px !important; color: #FAFAFA !important;
        padding: 12px 16px !important; font-size: 1rem !important;
    }
    .stTextInput > div > div > input:focus {
        border-color: #FF4B4B !important; box-shadow: 0 0 0 2px rgba(255,75,75,0.2) !important;
    }
    .stDownloadButton > button {
        background: linear-gradient(90deg, #00C853, #00E676) !important;
        border: none !important; border-radius: 10px !important;
        color: #0E1117 !important; font-weight: 700 !important;
    }
    .stTabs [data-baseweb="tab-list"] {
        background-color: #1A2033; border-radius: 12px; padding: 4px; gap: 4px;
    }
    .stTabs [data-baseweb="tab"] { border-radius: 8px; color: #8892A0; font-weight: 600; }
    .stTabs [aria-selected="true"] { background-color: #2A3350 !important; color: #FF4B4B !important; }
    hr { border-color: #2D3548 !important; }
    .stDataFrame [data-testid="stDataFrameResizable"] {
        border: 1px solid #2D3548 !important; border-radius: 12px !important; overflow: hidden;
    }
</style>
""", unsafe_allow_html=True)

# ============================================================
# API 키
# ============================================================
YOUTUBE_API_KEY = st.secrets["YOUTUBE_API_KEY"]

# ============================================================
# 함수
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
    except HttpError:
        pass
    return None

def get_all_comments(youtube, video_id, max_comments, progress_bar, status_text, do_translate):
    comments = []
    npt = None
    translator = GoogleTranslator(source='auto', target='ko') if do_translate else None
    
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
                full_date = sn.get("publishedAt", "")
                
                # 댓글 텍스트 및 번역 처리
                comment_text = sn.get("textDisplay", "")
                is_translated = False
                if do_translate and comment_text:
                    try:
                        translated_text = translator.translate(comment_text)
                        if translated_text != comment_text:
                            comment_text = translated_text
                            is_translated = True
                    except Exception:
                        pass # 번역 실패 시 원본 유지
                
                comments.append({
                    "작성자": sn.get("authorDisplayName", ""),
                    "댓글": comment_text,
                    "번역여부": "⭕" if is_translated else "❌",
                    "좋아요": sn.get("likeCount", 0),
                    "작성일시": full_date,
                    "작성일": full_date[:10] if full_date else "",
                    "시간": int(full_date[11:13]) if len(full_date) >= 13 else 0,
                    "수정일": sn.get("updatedAt", "")[:10],
                })
            prog = min(len(comments) / max_comments, 1.0)
            progress_bar.progress(prog)
            status_text.text(f"💬 {len(comments):,}개 수집 중... {'(번역 진행 중 🌐)' if do_translate else ''}")
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
            st.error(f"오류: {e}")
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

def extract_top_keywords(comments, top_n=5):
    all_words = []
    stopwords = {"너무", "진짜", "정말", "많이", "이거", "그냥", "영상", "유튜브", "좋아요", "구독", "있는", "이런", "저런", "그리고"}
    for c in comments:
        words = re.findall(r'[가-힣a-zA-Z]{2,}', c["댓글"])
        all_words.extend([w for w in words if w not in stopwords])
    return dict(Counter(all_words).most_common(top_n))

def make_bar_chart_html(data_dict, colors, title):
    if not data_dict:
        return ""
    max_val = max(data_dict.values()) if max(data_dict.values()) > 0 else 1
    bars_html = ""
    for i, (label, value) in enumerate(data_dict.items()):
        pct = (value / max_val) * 100
        c = colors[i % len(colors)]
        bars_html += f'<div class="bar-row"><div class="bar-label">{label}</div><div class="bar-track"><div class="bar-fill" style="width:{max(pct,8)}%;background:linear-gradient(90deg,{c},{c}dd);">{value:,}</div></div></div>'
    return f'<div class="chart-container"><div style="color:#E0E0E0;font-weight:700;font-size:1.05rem;margin-bottom:18px;">{title}</div>{bars_html}</div>'

def make_donut_svg(pct, color, label, size=130):
    r = 45
    circ = 2 * 3.14159 * r
    offset = circ - (pct / 100) * circ
    return f'<div style="text-align:center;"><svg width="{size}" height="{size}" viewBox="0 0 120 120"><circle cx="60" cy="60" r="{r}" fill="none" stroke="#1A1F2E" stroke-width="12"/><circle cx="60" cy="60" r="{r}" fill="none" stroke="{color}" stroke-width="12" stroke-dasharray="{circ}" stroke-dashoffset="{offset}" stroke-linecap="round" transform="rotate(-90 60 60)"/><text x="60" y="65" text-anchor="middle" fill="{color}" font-size="20" font-weight="800">{pct:.0f}%</text></svg><div style="color:#8892A0;font-size:0.82rem;margin-top:4px;">{label}</div></div>'

# ============================================================
# 사이드바
# ============================================================
with st.sidebar:
    st.markdown("""
    <div style="text-align:center; padding:20px 0 10px 0;">
        <span style="font-size:2.5rem;">📺</span><br>
        <span style="font-size:1.1rem;font-weight:700;color:#FF4B4B;">댓글 수집기</span>
    </div>""", unsafe_allow_html=True)
    
    st.divider()
    
    st.markdown("##### ⚙️ 수집 설정")
    collect_mode = st.radio(
        "수집 범위", options=["auto", "custom"],
        format_func=lambda x: "🔄 전체 수집 (자동)" if x == "auto" else "✏️ 수량 직접 지정",
    )
    custom_max = 200
    if collect_mode == "custom":
        custom_max = st.number_input(
            "수집할 댓글 수", min_value=10, max_value=10000, value=200, step=50
        )
        
    st.divider()
    
    # 번역 기능 토글 추가
    st.markdown("##### 🌐 번역 설정")
    enable_translation = st.toggle("외국어 댓글 한국어로 번역하기", value=False)
    if enable_translation:
        st.info("💡 번역을 켜면 수집 속도가 조금 느려질 수 있습니다.")
        
    st.divider()
    st.markdown(
        "<p style='text-align:center;color:#5A6577;font-size:0.75rem;'>"
        "YouTube Data API v3</p>",
        unsafe_allow_html=True
    )

# ============================================================
# 메인 UI
# ============================================================
st.markdown('<div class="main-header">유튜브 댓글 수집기</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">영상 링크를 넣으면 댓글을 자동으로 수집하고 분석합니다</div>', unsafe_allow_html=True)

url_input = st.text_input("링크", placeholder="https://www.youtube.com/watch?v=...", label_visibility="collapsed")
st.markdown("<p style='text-align:center;color:#5A6577;font-size:0.82rem;margin-top:-10px;'>⬆️ 유튜브 영상 링크를 붙여넣으세요</p>", unsafe_allow_html=True)

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
        mtc = min(total, 10000)
    else:
        mtc = min(custom_max, total, 10000)

    st.markdown(f"**📊 전체 댓글 {total:,}개 중 최대 {mtc:,}개 수집**")
    pb = st.progress(0)
    st_txt = st.empty()
    
    # 번역 여부(enable_translation)를 인자로 넘겨 수집
    comments = get_all_comments(youtube, video_id, mtc, pb, st_txt, enable_translation)
    st.session_state["comments"] = comments

# ============================================================
# 결과 표시
# ============================================================
if "video_info" in st.session_state and "comments" in st.session_state:
    video_info = st.session_state["video_info"]
    comments = st.session_state["comments"]

    st.divider()

    ct, ci = st.columns([1, 2])
    with ct:
        if video_info["thumbnail"]:
            st.image(video_info["thumbnail"], use_container_width=True)
    with ci:
        st.markdown(
            f'<div class="video-card">'
            f'<div class="video-title">{video_info["title"]}</div>'
            f'<div class="video-channel">'
            f'📢 {video_info["channel"]}  ·  📅 {video_info["published"]}'
            f'</div></div>',
            unsafe_allow_html=True
        )
        c1, c2, c3, c4 = st.columns(4)
        info_list = [
            ("👀", "조회수", format_number(video_info["views"])),
            ("👍", "좋아요", format_number(video_info["likes"])),
            ("💬", "전체 댓글", format_number(video_info["comments_count"])),
            ("📥", "수집 완료", f"{len(comments):,}개"),
        ]
        for col, (icon, label, value) in zip([c1, c2, c3, c4], info_list):
            col.markdown(
                f'<div class="stat-card">'
                f'<div style="font-size:1.5rem;">{icon}</div>'
                f'<div class="stat-number">{value}</div>'
                f'<div class="stat-label">{label}</div>'
                f'</div>',
                unsafe_allow_html=True
            )

    st.markdown("<br>", unsafe_allow_html=True)
    st.divider()

    if not comments:
        st.warning("수집된 댓글이 없습니다.")
        st.stop()

    st.markdown(
        f'<div style="text-align:center;margin-bottom:20px;">'
        f'<span style="font-size:1.6rem;font-weight:800;color:#FAFAFA;">'
        f'💬 수집된 댓글 </span>'
        f'<span style="font-size:1.6rem;font-weight:800;color:#FF4B4B;">'
        f'{len(comments):,}개</span></div>',
        unsafe_allow_html=True
    )

    df = pd.DataFrame(comments)
    tab1, tab2, tab3 = st.tabs(["📋 테이블", "💬 카드", "📊 통계"])

    with tab1:
        search_t = st.text_input("검색", placeholder="🔎 키워드 검색...", key="ts1", label_visibility="collapsed")
        if search_t:
            fdf = df[df["댓글"].str.contains(search_t, case=False, na=False)]
            st.markdown(f"<p style='color:#FF8E53;font-weight:600;'>🔎 '{search_t}' → {len(fdf)}개</p>", unsafe_allow_html=True)
        else:
            fdf = df

        max_l = int(df["좋아요"].max())
        if max_l <= 0: max_l = 1

        st.dataframe(
            fdf,
            use_container_width=True,
            height=600,
            column_config={
                "좋아요": st.column_config.ProgressColumn("👍 좋아요", format="%d", min_value=0, max_value=max_l),
                "작성자": st.column_config.TextColumn("👤 작성자", width="medium"),
                "댓글": st.column_config.TextColumn("💬 댓글", width="large"),
                "번역여부": st.column_config.TextColumn("🌐 번역", width="small"),
                "작성일": st.column_config.TextColumn("📅 작성일", width="small"),
            }
        )

    with tab2:
        search_c = st.text_input("검색", placeholder="🔎 키워드 검색...", key="cs1", label_visibility="collapsed")
        dc = comments
        if search_c:
            dc = [c for c in comments if search_c.lower() in c["댓글"].lower()]
            st.markdown(f"<p style='color:#FF8E53;font-weight:600;'>🔎 '{search_c}' → {len(dc)}개</p>", unsafe_allow_html=True)

        ipp = 30
        tp = max(1, (len(dc) + ipp - 1) // ipp)
        page = st.selectbox("페이지", range(1, tp + 1), format_func=lambda x: f"📄 {x}/{tp} 페이지", label_visibility="collapsed")
        start = (page - 1) * ipp

        for comment in dc[start:start + ipp]:
            badge = " 🔥" if comment["좋아요"] >= 100 else (" ⭐" if comment["좋아요"] >= 10 else "")
            trans_badge = " (🌐 번역됨)" if comment.get("번역여부") == "⭕" else ""
            safe_text = comment["댓글"].replace("<", "&lt;").replace(">", "&gt;")
            safe_author = comment["작성자"].replace("<", "&lt;").replace(">", "&gt;")
            st.markdown(
                f'<div class="comment-box">'
                f'<div class="comment-author">👤 {safe_author}{badge}</div>'
                f'<div class="comment-text">{safe_text}{trans_badge}</div>'
                f'<div class="comment-meta">👍 {comment["좋아요"]:,} &nbsp;|&nbsp; 📅 {comment["작성일"]}</div></div>',
                unsafe_allow_html=True
            )

    with tab3:
        st.markdown("<br>", unsafe_allow_html=True)
        total_c = len(comments)
        avg_likes = sum(c["좋아요"] for c in comments) / total_c if total_c else 0
        max_likes = max(c["좋아요"] for c in comments) if total_c else 0
        avg_len = sum(len(c["댓글"]) for c in comments) / total_c if total_c else 0

        s1, s2, s3, s4 = st.columns(4)
        stat_items = [
            ("📝", "총 수집", f"{total_c:,}개"),
            ("👍", "평균 좋아요", f"{avg_likes:.1f}"),
            ("🔥", "최대 좋아요", f"{max_likes:,}"),
            ("📏", "평균 글자수", f"{avg_len:.0f}자"),
        ]
        for col, (icon, label, val) in zip([s1, s2, s3, s4], stat_items):
            col.markdown(
                f'<div class="stat-card"><div style="font-size:1.5rem;">{icon}</div>'
                f'<div class="stat-number">{val}</div><div class="stat-label">{label}</div></div>',
                unsafe_allow_html=True
            )

        st.markdown("<br>", unsafe_allow_html=True)

        st.markdown('<h4 style="color:#FFF;">📈 날짜 및 시간별 화력 트렌드</h4>', unsafe_allow_html=True)
        t_col1, t_col2 = st.columns(2)
        with t_col1:
            st.markdown('<div class="chart-container"><p style="font-weight:700;color:white;margin-bottom:10px;">📅 날짜별 댓글 수 추이</p>', unsafe_allow_html=True)
            st.line_chart(df.groupby("작성일").size(), color="#FF4B4B")
            st.markdown('</div>', unsafe_allow_html=True)
        
        with t_col2:
            st.markdown('<div class="chart-container"><p style="font-weight:700;color:white;margin-bottom:10px;">⏰ 시간대별 작성 분포 (0~23시)</p>', unsafe_allow_html=True)
            st.bar_chart(df.groupby("시간").size().reindex(range(24), fill_value=0), color="#FF8E53")
            st.markdown('</div>', unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        has_likes = sum(1 for c in comments if c["좋아요"] > 0)
        pct_likes = (has_likes / total_c * 100) if total_c else 0
        pct_short = (sum(1 for c in comments if len(c["댓글"]) <= 30) / total_c * 100) if total_c else 0
        pct_long = (sum(1 for c in comments if len(c["댓글"]) > 100) / total_c * 100) if total_c else 0

        d1, d2, d3 = st.columns(3)
        with d1: st.markdown(make_donut_svg(pct_likes, "#FF4B4B", "좋아요 받은 댓글"), unsafe_allow_html=True)
        with d2: st.markdown(make_donut_svg(pct_short, "#4ECDC4", "짧은 댓글 (30자 이하)"), unsafe_allow_html=True)
        with d3: st.markdown(make_donut_svg(pct_long, "#FF8E53", "긴 댓글 (100자 이상)"), unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        kw_col, lk_col = st.columns(2)
        with kw_col:
            top_k = extract_top_keywords(comments, 5)
            st.markdown(make_bar_chart_html(top_k, ["#4ECDC4", "#45B7D1", "#667eea", "#f093fb", "#FF8E53"], "🔥 가장 많이 언급된 단어"), unsafe_allow_html=True)

        with lk_col:
            like_ranges = {"0": 0, "1~5": 0, "6~20": 0, "21~100": 0, "100+": 0}
            for c in comments:
                lk = c["좋아요"]
                if lk == 0: like_ranges["0"] += 1
                elif lk <= 5: like_ranges["1~5"] += 1
                elif lk <= 20: like_ranges["6~20"] += 1
                elif lk <= 100: like_ranges["21~100"] += 1
                else: like_ranges["100+"] += 1
            st.markdown(make_bar_chart_html(like_ranges, ["#5A6577", "#4ECDC4", "#45B7D1", "#FF8E53", "#FF4B4B"], "👍 좋아요 분포"), unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        len_ranges = {"~10자": 0, "11~30자": 0, "31~100자": 0, "101~300자": 0, "300자+": 0}
        for c in comments:
            cl = len(c["댓글"])
            if cl <= 10: len_ranges["~10자"] += 1
            elif cl <= 30: len_ranges["11~30자"] += 1
            elif cl <= 100: len_ranges["31~100자"] += 1
            elif cl <= 300: len_ranges["101~300자"] += 1
            else: len_ranges["300자+"] += 1
        st.markdown(make_bar_chart_html(len_ranges, ["#667eea", "#764ba2", "#f093fb", "#FF8E53", "#FF4B4B"], "📏 댓글 길이 분포"), unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        st.markdown('<div style="color:#E0E0E0;font-weight:700;font-size:1.05rem;margin-bottom:14px;">🏆 좋아요 TOP 5</div>', unsafe_allow_html=True)
        medals = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣"]
        top5 = sorted(comments, key=lambda x: x["좋아요"], reverse=True)[:5]
        for i, c in enumerate(top5):
            safe_t = c["댓글"].replace("<", "&lt;").replace(">", "&gt;")
            safe_a = c["작성자"].replace("<", "&lt;").replace(">", "&gt;")
            st.markdown(
                f'<div class="top-comment-box"><div class="comment-author">{medals[i]} 👤 {safe_a} &nbsp;(👍 {c["좋아요"]:,})</div>'
                f'<div class="comment-text">{safe_t}</div></div>',
                unsafe_allow_html=True
            )

    st.divider()

    csv_data = df.to_csv(index=False, encoding="utf-8-sig")
    vid = st.session_state.get("video_id", "video")
    st.download_button(
        label="📥 CSV 파일 다운로드", data=csv_data,
        file_name=f"youtube_comments_{vid}.csv", mime="text/csv",
        use_container_width=True
    )
