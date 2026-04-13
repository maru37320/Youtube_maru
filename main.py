import streamlit as st
import pandas as pd
import re
from collections import Counter
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from deep_translator import GoogleTranslator

# ============================================================
# 페이지 설정 및 스타일 (이전과 동일)
# ============================================================
st.set_page_config(page_title="유튜브 댓글 수집기", page_icon="📺", layout="wide")

st.markdown("""
<style>
    .stApp { background: linear-gradient(180deg, #0E1117 0%, #151B28 50%, #1A1F2E 100%); }
    .main-header { font-size: 2.8rem; font-weight: 800; text-align: center; background: linear-gradient(90deg, #FF4B4B, #FF8E53); -webkit-background-clip: text; -webkit-text-fill-color: transparent; margin-bottom: 0.3rem; }
    .sub-header { font-size: 1.05rem; text-align: center; color: #8892A0; margin-bottom: 2rem; }
    .video-card { background: linear-gradient(135deg, #1E2536, #252D40); border: 1px solid #2D3548; border-radius: 16px; padding: 24px; margin-bottom: 20px; }
    .video-title { font-size: 1.3rem; font-weight: 700; color: #FFF; margin-bottom: 8px; }
    .video-channel { color: #8892A0; font-size: 0.95rem; }
    .stat-card { background: linear-gradient(135deg, #1E2536, #2A3350); border: 1px solid #2D3548; border-radius: 14px; padding: 20px; text-align: center; transition: transform 0.2s; }
    .stat-card:hover { transform: translateY(-3px); box-shadow: 0 8px 25px rgba(255,75,75,0.15); }
    .stat-number { font-size: 1.8rem; font-weight: 800; background: linear-gradient(90deg, #FF4B4B, #FF8E53); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
    .stat-label { font-size: 0.85rem; color: #8892A0; margin-top: 4px; }
    .comment-box { background: linear-gradient(135deg, #1A2033, #212944); border: 1px solid #2D3548; border-left: 4px solid #FF4B4B; padding: 16px 20px; margin-bottom: 12px; border-radius: 0 12px 12px 0; transition: transform 0.2s; }
    .comment-box:hover { transform: translateX(4px); box-shadow: 0 4px 20px rgba(255,75,75,0.1); }
    .comment-author { font-weight: 700; color: #E0E0E0; font-size: 0.95rem; }
    .comment-text { color: #B0B8C8; margin-top: 6px; font-size: 0.92rem; line-height: 1.6; white-space: pre-wrap; }
    .comment-meta { color: #5A6577; font-size: 0.78rem; margin-top: 8px; }
    .top-comment-box { background: linear-gradient(135deg, #1E2536, #2A2040); border: 1px solid #3D2D5C; border-left: 4px solid #FF8E53; padding: 16px 20px; margin-bottom: 12px; border-radius: 0 12px 12px 0; }
    .chart-container { background: linear-gradient(135deg, #1A2033, #212944); border: 1px solid #2D3548; border-radius: 16px; padding: 24px; margin: 10px 0; }
    .bar-row { display: flex; align-items: center; margin-bottom: 14px; }
    .bar-label { color: #B0B8C8; font-size: 0.88rem; width: 80px; text-align: right; margin-right: 14px; font-weight: 600; }
    .bar-track { flex: 1; background-color: #1A1F2E; border-radius: 20px; height: 28px; overflow: hidden; }
    .bar-fill { height: 100%; border-radius: 20px; display: flex; align-items: center; padding-left: 12px; font-size: 0.8rem; font-weight: 700; color: white; transition: width 0.8s ease; min-width: 40px; }
    section[data-testid="stSidebar"] { background: linear-gradient(180deg, #141824, #1A2035); border-right: 1px solid #2D3548; }
    section[data-testid="stSidebar"] .stRadio > label { color: #FAFAFA !important; font-weight: 600 !important; }
    section[data-testid="stSidebar"] .stRadio [role="radiogroup"] label { color: #E0E0E0 !important; background-color: #1E2536 !important; border: 1px solid #2D3548 !important; border-radius: 10px !important; padding: 10px 14px !important; margin-bottom: 6px !important; }
    section[data-testid="stSidebar"] .stRadio [role="radiogroup"] label:hover { border-color: #FF4B4B !important; background-color: #252D40 !important; }
    section[data-testid="stSidebar"] h5 { color: #FF8E53 !important; }
    section[data-testid="stSidebar"] .stNumberInput label { color: #E0E0E0 !important; }
    .stTextInput > div > div > input { background-color: #1A2033 !important; border: 1px solid #2D3548 !important; border-radius: 10px !important; color: #FAFAFA !important; padding: 12px 16px !important; font-size: 1rem !important; }
    .stTextInput > div > div > input:focus { border-color: #FF4B4B !important; box-shadow: 0 0 0 2px rgba(255,75,75,0.2) !important; }
    .stDownloadButton > button { background: linear-gradient(90deg, #00C853, #00E676) !important; border: none !important; border-radius: 10px !important; color: #0E1117 !important; font-weight: 700 !important; }
    .stTabs [data-baseweb="tab-list"] { background-color: #1A2033; border-radius: 12px; padding: 4px; gap: 4px; }
    .stTabs [data-baseweb="tab"] { border-radius: 8px; color: #8892A0; font-weight: 600; }
    .stTabs [aria-selected="true"] { background-color: #2A3350 !important; color: #FF4B4B !important; }
    hr { border-color: #2D3548 !important; }
</style>
""", unsafe_allow_html=True)

# ============================================================
# API 키 및 보조 함수
# ============================================================
YOUTUBE_API_KEY = st.secrets["YOUTUBE_API_KEY"]

@st.cache_data
def get_supported_langs():
    try:
        return GoogleTranslator().get_supported_languages(as_dict=True)
    except Exception:
        return {"korean": "ko", "english": "en", "japanese": "ja"}

def extract_video_id(url):
    patterns = [r'v=([a-zA-Z0-9_-]{11})', r'youtu\.be/([a-zA-Z0-9_-]{11})', r'shorts/([a-zA-Z0-9_-]{11})']
    for p in patterns:
        m = re.search(p, url.strip())
        if m: return m.group(1)
    return None

def get_video_info(youtube, video_id):
    try:
        resp = youtube.videos().list(part="snippet,statistics", id=video_id).execute()
        if resp["items"]:
            s, t = resp["items"][0]["snippet"], resp["items"][0]["statistics"]
            return {"title": s["title"], "channel": s["channelTitle"], "published": s["publishedAt"][:10],
                    "views": int(t.get("viewCount", 0)), "likes": int(t.get("likeCount", 0)),
                    "comments_count": int(t.get("commentCount", 0)), "thumbnail": s["thumbnails"]["high"]["url"]}
    except: pass
    return None

def get_all_comments(youtube, video_id, max_comments, progress_bar, status_text, do_translate, target_lang="ko"):
    comments = []
    npt = None
    translator = GoogleTranslator(source='auto', target=target_lang) if do_translate else None
    try:
        while len(comments) < max_comments:
            resp = youtube.commentThreads().list(part="snippet", videoId=video_id, maxResults=100, order="relevance", pageToken=npt, textFormat="plainText").execute()
            for item in resp.get("items", []):
                if len(comments) >= max_comments: break
                sn = item["snippet"]["topLevelComment"]["snippet"]
                text = sn.get("textDisplay", "")
                is_trans = False
                if do_translate and text:
                    try:
                        trans = translator.translate(text)
                        if trans != text: text, is_trans = trans, True
                    except: pass
                comments.append({"작성자": sn["authorDisplayName"], "댓글": text, "번역여부": "⭕" if is_trans else "❌", "좋아요": sn["likeCount"], "작성일": sn["publishedAt"][:10], "시간": int(sn["publishedAt"][11:13])})
            progress_bar.progress(min(len(comments)/max_comments, 1.0))
            status_text.text(f"💬 {len(comments):,}개 수집 중...")
            npt = resp.get("nextPageToken")
            if not npt: break
    except Exception as e: st.error(f"오류: {e}")
    return comments

# ============================================================
# 키워드 분석 함수 (불용어 처리 강화)
# ============================================================
def extract_top_keywords(comments, custom_stopwords_str, top_n=5):
    all_words = []
    # 1. 기본 불용어 리스트 (한국어 + 영어)
    default_stopwords = {
        "너무", "진짜", "정말", "많이", "이거", "그냥", "영상", "유튜브", "좋아요", "구독", "있는", "이런", "저런", "그리고",
        "the", "to", "and", "of", "is", "it", "that", "you", "for", "on", "was", "with", "as", "at", "be", "this", "have", "in"
    }
    
    # 2. 사용자가 입력한 추가 불용어 처리
    if custom_stopwords_str:
        user_stops = {s.strip().lower() for s in custom_stopwords_str.split(",") if s.strip()}
        default_stopwords.update(user_stops)

    for c in comments:
        # 단어 추출 (2글자 이상의 한글, 영어)
        words = re.findall(r'[가-힣a-zA-Z]{2,}', c["댓글"])
        # 불용어 제외 및 소문자화
        all_words.extend([w.lower() for w in words if w.lower() not in default_stopwords])
    
    return dict(Counter(all_words).most_common(top_n))

# (기타 유틸 함수)
def format_number(n):
    if n >= 10000: return f"{n/10000:.1f}만"
    return f"{n:,}"

def make_bar_chart_html(data_dict, colors, title):
    if not data_dict: return ""
    max_val = max(data_dict.values()) if max(data_dict.values()) > 0 else 1
    bars_html = "".join([f'<div class="bar-row"><div class="bar-label">{k}</div><div class="bar-track"><div class="bar-fill" style="width:{max((v/max_val)*100,8)}%;background:linear-gradient(90deg,{colors[i%len(colors)]},{colors[i%len(colors)]}dd);">{v:,}</div></div></div>' for i, (k, v) in enumerate(data_dict.items())])
    return f'<div class="chart-container"><div style="color:#E0E0E0;font-weight:700;font-size:1.05rem;margin-bottom:18px;">{title}</div>{bars_html}</div>'

def make_donut_svg(pct, color, label):
    r = 45; circ = 2 * 3.14159 * r; offset = circ - (pct / 100) * circ
    return f'<div style="text-align:center;"><svg width="130" height="130" viewBox="0 0 120 120"><circle cx="60" cy="60" r="{r}" fill="none" stroke="#1A1F2E" stroke-width="12"/><circle cx="60" cy="60" r="{r}" fill="none" stroke="{color}" stroke-width="12" stroke-dasharray="{circ}" stroke-dashoffset="{offset}" stroke-linecap="round" transform="rotate(-90 60 60)"/><text x="60" y="65" text-anchor="middle" fill="{color}" font-size="20" font-weight="800">{pct:.0f}%</text></svg><div style="color:#8892A0;font-size:0.82rem;margin-top:4px;">{label}</div></div>'

# ============================================================
# 사이드바 UI
# ============================================================
with st.sidebar:
    st.markdown('<div style="text-align:center; padding:20px 0;"><h3>📺 댓글 수집기</h3></div>', unsafe_allow_html=True)
    st.divider()
    
    st.markdown("##### ⚙️ 수집 설정")
    collect_mode = st.radio("범위", ["자동", "수동"])
    custom_max = 200
    if collect_mode == "수동":
        custom_max = st.number_input("수집량", 10, 10000, 200, 50)
    
    st.divider()
    
    st.markdown("##### 🌐 번역 설정")
    enable_translation = st.toggle("번역 켜기", False)
    target_lang = "ko"
    if enable_translation:
        langs = get_supported_langs()
        target_lang = langs[st.selectbox("언어 선택", list(langs.keys()), index=list(langs.keys()).index("korean") if "korean" in langs else 0)]

    st.divider()
    
    # 불용어 설정 섹션 추가
    st.markdown("##### 🚫 분석 제외 단어 (불용어)")
    user_stops_input = st.text_area("제외할 단어 (쉼표로 구분)", placeholder="예: 진짜, 너무, the, is", help="분석 차트에서 보고 싶지 않은 단어를 입력하세요.")

# ============================================================
# 메인 로직
# ============================================================
st.markdown('<div class="main-header">유튜브 댓글 수집기</div>', unsafe_allow_html=True)
url_input = st.text_input("유튜브 링크", placeholder="https://www.youtube.com/watch?v=...")

col1, col2, _ = st.columns([1, 1, 4])
if col1.button("🔍 수집", type="primary", use_container_width=True):
    vid = extract_video_id(url_input)
    if vid:
        youtube = build("youtube", "v3", developerKey=YOUTUBE_API_KEY)
        v_info = get_video_info(youtube, vid)
        if v_info:
            st.session_state["video_info"] = v_info
            st.session_state["video_id"] = vid
            limit = min(v_info["comments_count"], 10000) if collect_mode == "자동" else custom_max
            pb = st.progress(0); st_txt = st.empty()
            comments = get_all_comments(youtube, vid, limit, pb, st_txt, enable_translation, target_lang)
            st.session_state["comments"] = comments
            st.rerun()

if "video_info" in st.session_state:
    v = st.session_state["video_info"]; c = st.session_state["comments"]
    df = pd.DataFrame(c)
    
    # 상단 요약 정보
    st.markdown(f'<div class="video-card"><div class="video-title">{v["title"]}</div><div class="video-channel">📢 {v["channel"]} | 📅 {v["published"]}</div></div>', unsafe_allow_html=True)
    
    tab1, tab2, tab3 = st.tabs(["📋 데이터", "💬 카드", "📊 분석"])
    
    with tab1: st.dataframe(df, use_container_width=True)
    
    with tab2:
        for item in c[:30]:
            st.markdown(f'<div class="comment-box"><div class="comment-author">👤 {item["작성자"]}</div><div class="comment-text">{item["댓글"]}</div><div class="comment-meta">👍 {item["좋아요"]} | {item["작성일"]}</div></div>', unsafe_allow_html=True)
            
    with tab3:
        # 통계 카드
        s1, s2, s3, s4 = st.columns(4)
        s1.metric("총 수집", f"{len(c)}개")
        s2.metric("평균 좋아요", f"{df['좋아요'].mean():.1f}")
        s3.metric("최다 좋아요", f"{df['좋아요'].max()}")
        s4.metric("평균 글자수", f"{df['댓글'].str.len().mean():.0f}자")
        
        # 키워드 분석 (강화된 불용어 함수 적용)
        st.markdown("<br>", unsafe_allow_html=True)
        kw_col, lk_col = st.columns(2)
        with kw_col:
            top_k = extract_top_keywords(c, user_stops_input, 7) # 사용자 입력을 함수로 전달
            st.markdown(make_bar_chart_html(top_k, ["#4ECDC4", "#45B7D1", "#667eea", "#FF8E53", "#FF4B4B"], "🔥 주요 키워드 (불용어 제외)"), unsafe_allow_html=True)
        with lk_col:
            st.markdown('<div class="chart-container"><p style="font-weight:700;color:white;">⏰ 시간대별 작성 분포</p>', unsafe_allow_html=True)
            st.bar_chart(df.groupby("시간").size().reindex(range(24), fill_value=0), color="#FF8E53")
            st.markdown('</div>', unsafe_allow_html=True)

    csv = df.to_csv(index=False, encoding="utf-8-sig")
    st.download_button("📥 CSV 다운로드", csv, f"youtube_{st.session_state['video_id']}.csv", "text/csv", use_container_width=True)
