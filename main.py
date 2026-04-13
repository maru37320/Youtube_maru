import streamlit as st
import pandas as pd
import re
from collections import Counter
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from langdetect import detect
from deep_translator import GoogleTranslator
import emoji

# ============================================================
# 페이지 설정
# ============================================================
st.set_page_config(page_title="유튜브 댓글 분석기", page_icon="📈", layout="wide")

# ============================================================
# 스타일 (UI 최적화)
# ============================================================
st.markdown("""
<style>
    .stApp { background: linear-gradient(180deg, #0E1117 0%, #151B28 50%, #1A1F2E 100%); }
    .main-header {
        font-size: 2.8rem; font-weight: 800; text-align: center;
        background: linear-gradient(90deg, #FF4B4B, #FF8E53);
        -webkit-background-clip: text; -webkit-fill-color: transparent;
        margin-bottom: 0.3rem;
    }
    .sub-header { font-size: 1.05rem; text-align: center; color: #8892A0; margin-bottom: 2rem; }
    .stat-card {
        background: linear-gradient(135deg, #1E2536, #2A3350);
        border: 1px solid #2D3548; border-radius: 14px; padding: 20px;
        text-align: center; transition: transform 0.2s;
    }
    .stat-number {
        font-size: 1.8rem; font-weight: 800;
        background: linear-gradient(90deg, #FF4B4B, #FF8E53);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    }
    .stat-label { font-size: 0.85rem; color: #8892A0; margin-top: 4px; }
    .chart-container {
        background: linear-gradient(135deg, #1A2033, #212944);
        border: 1px solid #2D3548; border-radius: 16px; padding: 24px; margin: 10px 0;
    }
    .comment-box {
        background: linear-gradient(135deg, #1A2033, #212944);
        border: 1px solid #2D3548; border-left: 4px solid #FF4B4B;
        padding: 16px 20px; margin-bottom: 12px; border-radius: 0 12px 12px 0;
    }
    .bar-row { display: flex; align-items: center; margin-bottom: 14px; }
    .bar-label { color: #B0B8C8; font-size: 0.88rem; width: 100px; text-align: right; margin-right: 14px; font-weight: 600; }
    .bar-track { flex: 1; background-color: #1A1F2E; border-radius: 20px; height: 24px; overflow: hidden; }
    .bar-fill { height: 100%; border-radius: 20px; display: flex; align-items: center; padding-left: 12px; font-size: 0.75rem; font-weight: 700; color: white; transition: width 0.8s ease; }
</style>
""", unsafe_allow_html=True)

# ============================================================
# API 설정
# ============================================================
try:
    YOUTUBE_API_KEY = st.secrets["YOUTUBE_API_KEY"]
except KeyError:
    st.error("🚨 유튜브 API 키가 설정되지 않았습니다.")
    st.stop()

# ============================================================
# 핵심 기능 함수
# ============================================================
def extract_video_id(url):
    patterns = [r'v=([a-zA-Z0-9_-]{11})', r'youtu\.be/([a-zA-Z0-9_-]{11})', r'shorts/([a-zA-Z0-9_-]{11})']
    for p in patterns:
        m = re.search(p, url)
        if m: return m.group(1)
    return None

def get_video_info(youtube, video_id):
    try:
        resp = youtube.videos().list(part="snippet,statistics", id=video_id).execute()
        if resp["items"]:
            s, t = resp["items"][0]["snippet"], resp["items"][0]["statistics"]
            return {
                "title": s["title"], "channel": s["channelTitle"], "published": s["publishedAt"][:10],
                "views": int(t.get("viewCount", 0)), "likes": int(t.get("likeCount", 0)),
                "comments_count": int(t.get("commentCount", 0)), "thumbnail": s["thumbnails"]["high"]["url"]
            }
    except: return None

def get_all_comments(youtube, video_id, max_comments, pb, st_txt):
    comments = []
    npt = None
    while len(comments) < max_comments:
        try:
            resp = youtube.commentThreads().list(
                part="snippet", videoId=video_id, maxResults=100, pageToken=npt, textFormat="plainText"
            ).execute()
            for item in resp.get("items", []):
                if len(comments) >= max_comments: break
                sn = item["snippet"]["topLevelComment"]["snippet"]
                # 날짜와 시간(HH) 모두 저장
                full_date = sn["publishedAt"] # 2023-10-01T15:30:00Z
                comments.append({
                    "작성자": sn["authorDisplayName"],
                    "댓글": sn["textDisplay"],
                    "좋아요": int(sn["likeCount"]),
                    "작성일시": full_date,
                    "날짜": full_date[:10],
                    "시간": int(full_date[11:13]) 
                })
            npt = resp.get("nextPageToken")
            pb.progress(min(len(comments)/max_comments, 1.0))
            st_txt.text(f"💬 {len(comments):,}개 수집 중...")
            if not npt: break
        except: break
    st_txt.text(f"✅ 수집 완료!")
    return comments

def smart_translate(text, target_lang):
    if target_lang == 'none': return text
    try:
        detected = detect(text)
        if detected == target_lang: return text
        return GoogleTranslator(source='auto', target=target_lang).translate(text)
    except: return text

def extract_top_keywords(comments, top_n=5):
    all_words = []
    stopwords = {"너무", "진짜", "정말", "많이", "이거", "그냥", "영상", "유튜브", "좋아요", "구독"}
    for c in comments:
        words = re.findall(r'[가-힣a-zA-Z]{2,}', c["댓글"])
        all_words.extend([w for w in words if w not in stopwords])
    return dict(Counter(all_words).most_common(top_n))

def make_bar_chart_html(data_dict, color, title):
    if not data_dict: return ""
    max_val = max(data_dict.values())
    bars = ""
    for label, val in data_dict.items():
        pct = (val / max_val) * 100
        bars += f"""
        <div class="bar-row">
            <div class="bar-label">{label}</div>
            <div class="bar-track"><div class="bar-fill" style="width:{pct}%; background:{color};">{val}</div></div>
        </div>"""
    return f'<div class="chart-container"><div style="color:#FFF;font-weight:700;margin-bottom:15px;">{title}</div>{bars}</div>'

# ============================================================
# 사이드바 & 메인 UI
# ============================================================
with st.sidebar:
    st.markdown("### ⚙️ 설정")
    collect_mode = st.radio("수집 수량", ["자동 (최대 1000개)", "수동 지정"])
    max_c = 1000
    if collect_mode == "수동 지정":
        max_c = st.number_input("수량", 10, 10000, 200)
    
    st.divider()
    lang_map = {'한국어': 'ko', '영어': 'en', '일본어': 'ja', '원문': 'none'}
    target_lang = lang_map[st.selectbox("번역 언어", list(lang_map.keys()))]

st.markdown('<div class="main-header">유튜브 댓글 분석기</div>', unsafe_allow_html=True)
url_input = st.text_input("유튜브 링크 입력", placeholder="https://www.youtube.com/watch?v=...")

if st.button("🔍 데이터 분석 시작", type="primary", use_container_width=True):
    if not url_input: st.stop()
    video_id = extract_video_id(url_input)
    youtube = build("youtube", "v3", developerKey=YOUTUBE_API_KEY)
    
    with st.spinner("🎥 영상 정보 로드 중..."):
        v_info = get_video_info(youtube, video_id)
    
    if v_info:
        st.session_state["v_info"] = v_info
        pb = st.progress(0)
        st_txt = st.empty()
        comments = get_all_comments(youtube, video_id, max_c, pb, st_txt)
        
        if target_lang != 'none':
            with st.spinner("🌐 번역 진행 중..."):
                for c in comments: c["댓글"] = smart_translate(c["댓글"], target_lang)
        
        st.session_state["comments"] = comments
        st.rerun()

# ============================================================
# 결과 화면
# ============================================================
if "comments" in st.session_state:
    v = st.session_state["v_info"]
    c_list = st.session_state["comments"]
    df = pd.DataFrame(c_list)

    # 상단 요약 정보
    col_img, col_info = st.columns([1, 2])
    with col_img: st.image(v["thumbnail"], use_container_width=True)
    with col_info:
        st.markdown(f"### {v['title']}")
        st.caption(f"📢 {v['channel']} | 📅 {v['published']}")
        s1, s2, s3 = st.columns(3)
        s1.markdown(f'<div class="stat-card"><div class="stat-number">{v["views"]:,}</div><div class="stat-label">조회수</div></div>', unsafe_allow_html=True)
        s2.markdown(f'<div class="stat-card"><div class="stat-number">{v["likes"]:,}</div><div class="stat-label">좋아요</div></div>', unsafe_allow_html=True)
        s3.markdown(f'<div class="stat-card"><div class="stat-number">{len(c_list):,}</div><div class="stat-label">분석 댓글</div></div>', unsafe_allow_html=True)

    tab_stat, tab_list = st.tabs(["📊 데이터 통계", "💬 댓글 목록"])

    with tab_stat:
        st.markdown("#### 📈 2번 기능: 댓글 화력(활동량) 트력 분석")
        
        c1, c2 = st.columns(2)
        with c1:
            # 날짜별 트렌드 (선 그래프)
            st.markdown('<div class="chart-container"><p style="font-weight:700;color:white;margin-bottom:10px;">📅 날짜별 댓글 수 추이</p>', unsafe_allow_html=True)
            daily_counts = df.groupby("날짜").size()
            st.line_chart(daily_counts, color="#FF4B4B")
            st.markdown('</div>', unsafe_allow_html=True)
        
        with c2:
            # 시간대별 트렌드 (바 차트)
            st.markdown('<div class="chart-container"><p style="font-weight:700;color:white;margin-bottom:10px;">⏰ 시간대별 작성 분포 (0-23시)</p>', unsafe_allow_html=True)
            hourly_counts = df.groupby("시간").size().reindex(range(24), fill_value=0)
            st.bar_chart(hourly_counts, color="#FF8E53")
            st.markdown('</div>', unsafe_allow_html=True)

        st.divider()
        
        c3, c4 = st.columns(2)
        with c3:
            # 키워드 TOP 5
            top_k = extract_top_keywords(c_list, 5)
            st.markdown(make_bar_chart_html(top_k, "#4ECDC4", "🔥 가장 많이 언급된 단어"), unsafe_allow_html=True)
        with c4:
            # 좋아요 분포
            like_dist = {"0개": (df["좋아요"]==0).sum(), "1-10개": ((df["좋아요"]>0)&(df["좋아요"]<=10)).sum(), "10개+": (df["좋아요"]>10).sum()}
            st.markdown(make_bar_chart_html(like_dist, "#FF4B4B", "👍 좋아요 반응 분포"), unsafe_allow_html=True)

    with tab_list:
        st.dataframe(df[["작성자", "댓글", "좋아요", "날짜"]], use_container_width=True, height=500)
