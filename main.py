import streamlit as st
import google.generativeai as genai
from googleapiclient.discovery import build
from langdetect import detect
from deep_translator import GoogleTranslator
import urllib.parse as p
import re

# ==========================================
# 1. API 키 설정 (st.secrets 활용)
# ==========================================
try:
    YOUTUBE_API_KEY = st.secrets["YOUTUBE_API_KEY"]
    GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=GEMINI_API_KEY)
except KeyError:
    st.error("🚨 API 키가 설정되지 않았습니다. GitHub Secrets 또는 `.streamlit/secrets.toml` 파일을 확인해주세요.")
    st.stop()

# ==========================================
# 2. 핵심 함수 정의
# ==========================================

def get_video_id(url):
    """유튜브 URL에서 Video ID를 추출하는 함수"""
    parsed_url = p.urlparse(url)
    if parsed_url.hostname == 'youtu.be':
        return parsed_url.path[1:]
    if parsed_url.hostname in ('www.youtube.com', 'youtube.com'):
        if parsed_url.path == '/watch':
            return p.parse_qs(parsed_url.query)['v'][0]
    return None

def fetch_youtube_comments(video_id, max_results=774):
    """유튜브 댓글을 수집하는 함수"""
    youtube = build('youtube', 'v3', developerKey=YOUTUBE_API_KEY)
    comments = []
    
    try:
        request = youtube.commentThreads().list(
            part="snippet",
            videoId=video_id,
            maxResults=100, # 한 번에 가져올 최대 개수 (API 제한 100)
            textFormat="plainText"
        )
        
        while request and len(comments) < max_results:
            response = request.execute()
            
            for item in response['items']:
                comment_data = item['snippet']['topLevelComment']['snippet']
                comments.append({
                    'author': comment_data['authorDisplayName'],
                    'text': comment_data['textDisplay'],
                    'likes': comment_data['likeCount'],
                    'date': comment_data['publishedAt'][:10]
                })
                
            request = youtube.commentThreads().list_next(request, response)
            
    except Exception as e:
        st.error(f"댓글 수집 중 오류 발생: {e}")
        
    return comments

def summarize_comments_with_gemini(comments):
    """좋아요 상위 50개 댓글을 추출하여 Gemini로 요약하는 함수"""
    if not comments:
        return "수집된 댓글이 없습니다."
        
    # 1. 좋아요(likes) 순으로 내림차순 정렬 후 상위 50개 슬라이싱
    sorted_comments = sorted(comments, key=lambda x: x['likes'], reverse=True)
    top_50_comments = sorted_comments[:50]
    
    # 2. 텍스트 합치기
    text_to_summarize = "\n---\n".join([c['text'] for c in top_50_comments])
    
    # 3. 프롬프트 작성
    prompt = f"""
    다음은 유튜브 영상의 베스트 댓글 상위 50개입니다.
    이 댓글들의 전반적인 분위기, 긍정/부정 반응, 그리고 사람들이 주로 언급하는 핵심 주제 3가지를 깔끔하게 요약해 주세요.
    
    댓글 내용:
    {text_to_summarize}
    """
    
    # 4. Gemini API 호출 (최신 Flash 모델 사용)
    try:
        model = genai.GenerativeModel('gemini-2.0-flash')
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"요약 생성 실패 (API 한도 초과 또는 오류): {e}"

def smart_translate(text, target_lang='ko'):
    """언어를 감지하고 목표 언어와 다를 때만 번역하는 함수"""
    try:
        # 이모티콘만 있거나 텍스트가 비어있으면 그대로 반환
        if not text or not re.search('[a-zA-Z가-힣]', text):
            return text
            
        detected_lang = detect(text)
        
        # langdetect의 결과와 deep-translator의 타겟 코드 매칭 로직
        # langdetect는 중국어를 'zh-cn'으로 잡고, 번역기는 'zh-CN'을 씁니다.
        if detected_lang == target_lang or (detected_lang == 'zh-cn' and target_lang == 'zh-CN'):
            return text 
            
        translated = GoogleTranslator(source='auto', target=target_lang).translate(text)
        return translated
    except:
        # 언어 감지 실패 시 원문 반환
        return text

# ==========================================
# 3. Streamlit 웹 UI 구현
# ==========================================

st.set_page_config(page_title="유튜브 댓글 수집 및 AI 분석", page_icon="📊", layout="wide")

st.title("📊 유튜브 댓글 수집기 & AI 분석")
st.markdown("영상 링크를 넣으면 댓글을 자동으로 수집하고 **Gemini AI**가 분석합니다.")

# 사용자 입력 영역
youtube_url = st.text_input("⬆️ 유튜브 영상 링크를 붙여넣으세요", placeholder="https://youtu.be/...")

# 번역 언어 선택
lang_options = {'한국어': 'ko', '영어': 'en', '일본어': 'ja', '중국어': 'zh-CN'}
selected_lang_name = st.selectbox("🌐 번역할 언어를 선택하세요 (원문과 같으면 번역 생략)", list(lang_options.keys()))
target_lang_code = lang_options[selected_lang_name]

if st.button("댓글 수집 및 분석 시작", type="primary"):
    if not youtube_url:
        st.warning("유튜브 링크를 입력해주세요.")
    else:
        video_id = get_video_id(youtube_url)
        if not video_id:
            st.error("유효하지 않은 유튜브 링크입니다.")
        else:
            with st.spinner('댓글을 수집하고 AI가 분석 중입니다... 잠시만 기다려주세요!'):
                # 1. 댓글 수집
                comments = fetch_youtube_comments(video_id)
                total_comments = len(comments)
                
                if total_comments > 0:
                    st.success(f"✅ 총 {total_comments}개 수집 완료!")
                    
                    st.divider()
                    
                    # 2. AI 요약 (상위 50개)
                    st.subheader("🤖 Gemini AI 댓글 요약 (좋아요 상위 50개 기준)")
                    summary_result = summarize_comments_with_gemini(comments)
                    st.info(summary_result)
                    
                    st.divider()
                    
                    # 3. 댓글 목록 및 스마트 번역
                    st.subheader(f"💬 수집된 댓글 목록 ({selected_lang_name} 번역 모드)")
                    
                    # 너무 많으면 화면이 길어지므로 100개까지만 화면에 출력
                    display_limit = min(100, total_comments)
                    st.caption(f"화면에는 최대 100개까지만 표시됩니다.")
                    
                    # 좋아요 순으로 정렬하여 출력
                    sorted_comments = sorted(comments, key=lambda x: x['likes'], reverse=True)
                    
                    for i, comment in enumerate(sorted_comments[:display_limit]):
                        # 스마트 번역 실행
                        translated_text = smart_translate(comment['text'], target_lang=target_lang_code)
                        
                        with st.container():
                            st.markdown(f"**{comment['author']}** (👍 {comment['likes']} | 📅 {comment['date']})")
                            st.write(translated_text)
                            st.divider()
                else:
                    st.warning("댓글이 없거나 수집할 수 없는 영상입니다 (댓글 사용 중지 등).")    }
    section[data-testid="stSidebar"] .stRadio > label { color: #FAFAFA !important; font-weight: 600 !important; }
    
    /* 라디오 버튼 글씨색 흰색으로 변경 */
    section[data-testid="stSidebar"] .stRadio [role="radiogroup"] label,
    section[data-testid="stSidebar"] .stRadio [role="radiogroup"] label p,
    section[data-testid="stSidebar"] .stRadio [role="radiogroup"] label div {
        color: #FFFFFF !important; 
    }
    section[data-testid="stSidebar"] .stRadio [role="radiogroup"] label {
        background-color: #1E2536 !important;
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
try:
    YOUTUBE_API_KEY = st.secrets["YOUTUBE_API_KEY"]
except KeyError:
    st.error("secrets.toml 파일에 YOUTUBE_API_KEY가 없습니다.")
    st.stop()
    
GEMINI_API_KEY = st.secrets.get("GEMINI_API_KEY", "")

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
            prog = min(len(comments) / max_comments, 1.0)
            progress_bar.progress(prog)
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


def summarize_with_gemini(comments_list, video_title):
    if not GEMINI_API_KEY:
        return "❌ Gemini API 키가 설정되지 않아 요약을 생성할 수 없습니다."
    if not GEMINI_AVAILABLE:
        return "❌ google-generativeai 모듈이 설치되지 않았습니다."
        
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        model = genai.GenerativeModel("gemini-2.0-flash")
        sample = comments_list[:200]
        text = "\n".join([f"- {c['댓글']}" for c in sample])
        prompt = f"""다음은 유튜브 영상 '{video_title}'의 댓글들이야.

{text}

아래 형식으로 분석해줘:

🗣️ **전체 분위기**: (댓글들의 전반적인 분위기를 2~3줄로)

📌 **자주 언급되는 주제 TOP 3**:
1. ...
2. ...
3. ...

💬 **대표 의견 요약**: (시청자들이 공통적으로 하는 말을 3~4줄로)

😊 **긍정 vs 부정 비율**: (대략적인 비율과 한줄 설명)"""
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"요약 생성 실패: {e}"

# 마크다운 코드 블록으로 렌더링되는 것을 방지하기 위해 HTML 문자열의 들여쓰기를 제거
def make_bar_chart_html(data_dict, colors, title):
    if not data_dict: return ""
    max_val = max(data_dict.values()) if max(data_dict.values()) > 0 else 1
    bars = ""
    for i, (label, value) in enumerate(data_dict.items()):
        pct = (value / max_val) * 100
        c = colors[i % len(colors)]
        bars += f'<div class="bar-row"><div class="bar-label">{label}</div><div class="bar-track"><div class="bar-fill" style="width:{max(pct,8)}%;background:linear-gradient(90deg,{c},{c}dd);">{value:,}</div></div></div>'
    return f'<div class="chart-container"><div style="color:#E0E0E0;font-weight:700;font-size:1.05rem;margin-bottom:18px;">{title}</div>{bars}</div>'

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
    st.markdown(
        "<p style='text-align:center;color:#5A6577;font-size:0.75rem;'>"
        "YouTube Data API v3 + Gemini AI</p>",
        unsafe_allow_html=True
    )

# ============================================================
# 메인 UI
# ============================================================
st.markdown(
    '<div class="main-header">유튜브 댓글 수집기</div>',
    unsafe_allow_html=True
)
st.markdown(
    '<div class="sub-header">영상 링크를 넣으면 댓글을 자동으로 수집하고 AI가 분석합니다</div>',
    unsafe_allow_html=True
)

url_input = st.text_input(
    "링크",
    placeholder="https://www.youtube.com/watch?v=...",
    label_visibility="collapsed"
)
st.markdown(
    "<p style='text-align:center;color:#5A6577;font-size:0.82rem;"
    "margin-top:-10px;'>⬆️ 유튜브 영상 링크를 붙여넣으세요</p>",
    unsafe_allow_html=True
)

col1, col2, col3 = st.columns([1, 1, 4])
with col1:
    search_button = st.button(
        "🔍 댓글 수집", type="primary", use_container_width=True
    )
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

    st.markdown(
        f"**📊 전체 댓글 {total:,}개 중 최대 {mtc:,}개 수집**"
    )
    pb = st.progress(0)
    st_txt = st.empty()
    comments = get_all_comments(youtube, video_id, mtc, pb, st_txt)
    st.session_state["comments"] = comments

    if comments:
        with st.spinner("🤖 Gemini AI가 댓글을 분석하는 중..."):
            summary = summarize_with_gemini(
                comments, video_info["title"]
            )
            st.session_state["summary"] = summary

# ============================================================
# 결과 표시
# ============================================================
if "video_info" in st.session_state and "comments" in st.session_state:
    video_info = st.session_state["video_info"]
    comments = st.session_state["comments"]

    st.divider()

    # 영상 정보
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

    # AI 요약 (마크다운 형식을 유지하기 위해 HTML 구조 개선)
    if "summary" in st.session_state and st.session_state["summary"]:
        # 마크다운의 굵은 글씨(**)를 HTML <b> 태그로 변환
        summary_html = re.sub(r'\*\*(.*?)\*\*', r'<b style="color: #FFF;">\1</b>', st.session_state["summary"])
        # 줄바꿈 변환
        summary_html = summary_html.replace("\n", "<br>")
        
        st.markdown(
            f'<div class="ai-card">'
            f'<div class="ai-title">🤖 Gemini AI 댓글 분석</div>'
            f'<div class="ai-text">{summary_html}</div>'
            f'</div>',
            unsafe_allow_html=True
        )

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

    # ===== 테이블 탭 =====
    with tab1:
        search_t = st.text_input(
            "검색", placeholder="🔎 키워드 검색...",
            key="ts1", label_visibility="collapsed"
        )
        if search_t:
            fdf = df[df["댓글"].str.contains(search_t, case=False, na=False)]
            st.markdown(
                f"<p style='color:#FF8E53;font-weight:600;'>"
                f"🔎 '{search_t}' → {len(fdf)}개</p>",
                unsafe_allow_html=True
            )
        else:
            fdf = df

        max_l = int(df["좋아요"].max())
        if max_l <= 0:
            max_l = 1

        st.dataframe(
            fdf,
            use_container_width=True,
            height=600,
            column_config={
                "좋아요": st.column_config.ProgressColumn(
                    "👍 좋아요", format="%d",
                    min_value=0, max_value=max_l
                ),
                "작성자": st.column_config.TextColumn(
                    "👤 작성자", width="medium"
                ),
                "댓글": st.column_config.TextColumn(
                    "💬 댓글", width="large"
                ),
                "작성일": st.column_config.TextColumn(
                    "📅 작성일", width="small"
                ),
                "수정일": st.column_config.TextColumn(
                    "✏️ 수정일", width="small"
                ),
            }
        )

    # ===== 카드 탭 =====
    with tab2:
        search_c = st.text_input(
            "검색", placeholder="🔎 키워드 검색...",
            key="cs1", label_visibility="collapsed"
        )
        dc = comments
        if search_c:
            dc = [
                c for c in comments
                if search_c.lower() in c["댓글"].lower()
            ]
            st.markdown(
                f"<p style='color:#FF8E53;font-weight:600;'>"
                f"🔎 '{search_c}' → {len(dc)}개</p>",
                unsafe_allow_html=True
            )

        ipp = 30
        tp = max(1, (len(dc) + ipp - 1) // ipp)
        page = st.selectbox(
            "페이지", range(1, tp + 1),
            format_func=lambda x: f"📄 {x}/{tp} 페이지",
            label_visibility="collapsed"
        )
        start = (page - 1) * ipp

        for comment in dc[start:start + ipp]:
            badge = ""
            if comment["좋아요"] >= 100:
                badge = " 🔥"
            elif comment["좋아요"] >= 10:
                badge = " ⭐"
            safe_text = comment["댓글"].replace("<", "&lt;").replace(">", "&gt;")
            safe_author = comment["작성자"].replace("<", "&lt;").replace(">", "&gt;")
            st.markdown(
                f'<div class="comment-box">'
                f'<div class="comment-author">👤 {safe_author}{badge}</div>'
                f'<div class="comment-text">{safe_text}</div>'
                f'<div class="comment-meta">'
                f'👍 {comment["좋아요"]:,} &nbsp;|&nbsp; '
                f'📅 {comment["작성일"]}</div></div>',
                unsafe_allow_html=True
            )

    # ===== 통계 탭 =====
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
                f'<div class="stat-card">'
                f'<div style="font-size:1.5rem;">{icon}</div>'
                f'<div class="stat-number">{val}</div>'
                f'<div class="stat-label">{label}</div></div>',
                unsafe_allow_html=True
            )

        st.markdown("<br>", unsafe_allow_html=True)

        # 도넛 차트 - 좋아요 있는 댓글 비율
        has_likes = sum(1 for c in comments if c["좋아요"] > 0)
        no_likes = total_c - has_likes
        pct_likes = (has_likes / total_c * 100) if total_c else 0

        short_c = sum(1 for c in comments if len(c["댓글"]) <= 30)
        pct_short = (short_c / total_c * 100) if total_c else 0

        long_c = sum(1 for c in comments if len(c["댓글"]) > 100)
        pct_long = (long_c / total_c * 100) if total_c else 0

        d1, d2, d3 = st.columns(3)
        with d1:
            st.markdown(
                make_donut_svg(pct_likes, "#FF4B4B", "좋아요 받은 댓글"),
                unsafe_allow_html=True
            )
        with d2:
            st.markdown(
                make_donut_svg(pct_short, "#4ECDC4", "짧은 댓글 (30자 이하)"),
                unsafe_allow_html=True
            )
        with d3:
            st.markdown(
                make_donut_svg(pct_long, "#FF8E53", "긴 댓글 (100자 이상)"),
                unsafe_allow_html=True
            )

        st.markdown("<br>", unsafe_allow_html=True)

        # 둥근 바 차트 - 좋아요 분포
        like_ranges = {
            "0": 0, "1~5": 0, "6~20": 0, "21~100": 0, "100+": 0
        }
        for c in comments:
            lk = c["좋아요"]
            if lk == 0:
                like_ranges["0"] += 1
            elif lk <= 5:
                like_ranges["1~5"] += 1
            elif lk <= 20:
                like_ranges["6~20"] += 1
            elif lk <= 100:
                like_ranges["21~100"] += 1
            else:
                like_ranges["100+"] += 1

        like_colors = ["#5A6577", "#4ECDC4", "#45B7D1", "#FF8E53", "#FF4B4B"]
        st.markdown(
            make_bar_chart_html(like_ranges, like_colors, "👍 좋아요 분포"),
            unsafe_allow_html=True
        )

        st.markdown("<br>", unsafe_allow_html=True)

        # 둥근 바 차트 - 댓글 길이 분포
        len_ranges = {
            "~10자": 0, "11~30자": 0, "31~100자": 0,
            "101~300자": 0, "300자+": 0
        }
        for c in comments:
            cl = len(c["댓글"])
            if cl <= 10:
                len_ranges["~10자"] += 1
            elif cl <= 30:
                len_ranges["11~30자"] += 1
            elif cl <= 100:
                len_ranges["31~100자"] += 1
            elif cl <= 300:
                len_ranges["101~300자"] += 1
            else:
                len_ranges["300자+"] += 1

        len_colors = ["#667eea", "#764ba2", "#f093fb", "#FF8E53", "#FF4B4B"]
        st.markdown(
            make_bar_chart_html(len_ranges, len_colors, "📏 댓글 길이 분포"),
            unsafe_allow_html=True
        )

        st.markdown("<br>", unsafe_allow_html=True)

        # 좋아요 TOP 5
        st.markdown(
            '<div style="color:#E0E0E0;font-weight:700;'
            'font-size:1.05rem;margin-bottom:14px;">'
            '🏆 좋아요 TOP 5</div>',
            unsafe_allow_html=True
        )
        medals = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣"]
        top5 = sorted(comments, key=lambda x: x["좋아요"], reverse=True)[:5]
        for i, c in enumerate(top5):
            safe_t = c["댓글"].replace("<", "&lt;").replace(">", "&gt;")
            safe_a = c["작성자"].replace("<", "&lt;").replace(">", "&gt;")
            st.markdown(
                f'<div class="top-comment-box">'
                f'<div class="comment-author">'
                f'{medals[i]} 👤 {safe_a} &nbsp;(👍 {c["좋아요"]:,})</div>'
                f'<div class="comment-text">{safe_t}</div>'
                f'</div>',
                unsafe_allow_html=True
            )

    st.divider()

    # CSV 다운로드
    csv_data = df.to_csv(index=False, encoding="utf-8-sig")
    vid = st.session_state.get("video_id", "video")
    st.download_button(
        label="📥 CSV 파일 다운로드",
        data=csv_data,
        file_name=f"youtube_comments_{vid}.csv",
        mime="text/csv",
        use_container_width=True
    )
