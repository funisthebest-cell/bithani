#!/usr/bin/env python3
"""
빛한의원 자동 블로그 포스팅 생성기
-----------------------------------
GitHub Actions에서 매일 1회 실행되어 한 개의 블로그 포스트를 자동 생성합니다.
- Claude API로 본문 작성
- blog/posts/YYYY-MM-DD.html 파일 생성
- blog/manifest.json 업데이트
- blog/index.html 재생성
"""

import anthropic
import json
import datetime
import os
import re
import sys

# Windows 콘솔 UTF-8 출력 설정
if sys.stdout.encoding and sys.stdout.encoding.lower() not in ('utf-8', 'utf8'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# ─── 한의원 기본 정보 ────────────────────────────────────
CLINIC_NAME     = "빛한의원"
DOCTOR          = "이상진 원장"
LOCATION        = "서울 동대문구 약령중앙로 9, 2층"
PHONE           = "02-966-6669"
NAVER_BOOKING   = "https://naver.me/5If4IVqY"
KAKAO_CHANNEL   = "http://pf.kakao.com/_bxbUxfG"
SITE_URL        = "https://bithani.netlify.app"

# ─── 블로그 주제 풀 (순환 사용) ─────────────────────────
TOPICS = [
    "목 디스크 증상과 한방 치료법",
    "허리 디스크, 수술 없이 추나요법으로 치료하기",
    "오십견(어깨 통증) 침 치료 효과와 회복 기간",
    "무릎 관절염 한의원에서 치료하는 방법",
    "만성 두통 한방 치료로 해결하기",
    "불면증과 침 치료 – 한방 수면 개선법",
    "소화불량과 위장 질환 한방 치료",
    "좌골신경통 한의원 치료 안내",
    "목 결림·경추 통증 한의원 치료법",
    "약침 치료란 무엇인가 – 효과와 적용 범위",
    "추나요법 건강보험 적용 완벽 안내",
    "부항 치료의 효과와 주의사항",
    "한방 미용침으로 피부 탄력 개선하기",
    "온열치료 효능과 적용 질환",
    "물리치료와 침치료 병행 치료의 장점",
    "동대문구 한의원 빛한의원을 선택하는 이유",
    "약령시장 한의원 – 전통과 현대 한의학의 만남",
    "한의원 처음 방문 시 알아야 할 것들",
    "침 치료는 아픈가요? 한의원 침 치료 Q&A",
    "한방 치료 부작용, 안전한가요?",
    "추나요법 몇 번 받으면 효과를 볼 수 있나요",
    "약침과 일반 침의 차이점",
    "봄철 알레르기 비염 한방 치료법",
    "여름철 냉방병 한의원에서 치료하기",
    "가을 환절기 면역력 강화 한방 방법",
    "겨울철 관절 통증 악화 이유와 한방 치료",
    "체형 불균형 교정 – 추나요법과 침 치료",
    "스트레스성 통증과 근육 긴장 한방 치료",
    "산후 한방 치료와 몸 회복 방법",
    "직장인 목·허리 통증 한방 솔루션",
    "척추측만증 한의원 치료 안내",
    "발목 염좌 후 한방 치료로 빠른 회복",
    "테니스엘보(팔꿈치 통증) 한의원 치료법",
    "두통과 어지럼증 한방 치료",
    "갱년기 증상 한방 치료로 완화하기",
    "한의원에서 면역력 높이는 방법",
    "만성 피로 회복 침 치료 효과",
    "손목 터널 증후군 한방 치료",
    "고관절 통증 한의원 치료",
    "족저근막염 한방 치료법",
]

# ─── 경로 설정 ────────────────────────────────────────────
SCRIPT_DIR  = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR    = os.path.join(SCRIPT_DIR, '..')
BLOG_DIR    = os.path.join(ROOT_DIR, 'blog')
POSTS_DIR   = os.path.join(BLOG_DIR, 'posts')
MANIFEST    = os.path.join(BLOG_DIR, 'manifest.json')


# ─── 유틸 함수 ───────────────────────────────────────────
def load_manifest():
    if os.path.exists(MANIFEST):
        with open(MANIFEST, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []

def save_manifest(data):
    with open(MANIFEST, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def get_topic(manifest):
    return TOPICS[len(manifest) % len(TOPICS)]

def date_ko(date_str):
    """'2024-01-15' → '2024년 1월 15일'"""
    d = datetime.date.fromisoformat(date_str)
    return f"{d.year}년 {d.month}월 {d.day}일"


# ─── Claude API 본문 생성 ─────────────────────────────────
def generate_content(topic, client):
    prompt = f"""당신은 {CLINIC_NAME}의 블로그 작가입니다. 아래 주제로 블로그 포스팅을 작성해주세요.

주제: {topic}

작성 조건:
1. 환자 관점에서 실질적으로 도움이 되는 정보 중심
2. "{DOCTOR}"을 자연스럽게 1~2회 언급
3. "서울 동대문구 약령시장 인근 {CLINIC_NAME}" 위치를 글 안에 자연스럽게 포함
4. 글 마지막 단락에 예약/상담 안내 문구 포함 (전화 {PHONE} 또는 네이버 예약)
5. 친근하면서도 전문적인 톤, 한국어 작성
6. 분량: 800~1000자 내외
7. h2, h3 소제목으로 구조화하여 읽기 쉽게
8. 의학적 내용은 과장 없이 신뢰감 있게
9. HTML 태그에 속성(class, id, style 등) 절대 사용 금지 — JSON 파싱 오류 방지

반드시 아래 JSON 형식으로만 응답하세요. 마크다운 코드블록, 설명 텍스트 없이 순수 JSON만 출력하세요:
{{
  "title": "검색 친화적 블로그 제목 (40자 이내)",
  "description": "SEO 메타 디스크립션 (80~120자, 핵심 정보 포함)",
  "keywords": "키워드1, 키워드2, 키워드3, 키워드4, 키워드5",
  "content_html": "<h2>소제목</h2><p>본문 HTML (h2, h3, p, ul, li 태그 사용)</p>"
}}"""

    msg = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=8000,
        messages=[{"role": "user", "content": prompt}]
    )

    raw = msg.content[0].text.strip()
    # 마크다운 코드블록 제거
    raw = re.sub(r'^```(?:json)?\s*', '', raw, flags=re.MULTILINE)
    raw = re.sub(r'```\s*$', '', raw, flags=re.MULTILINE)
    raw = raw.strip()

    json_m = re.search(r'\{[\s\S]*\}', raw)
    target = json_m.group() if json_m else raw
    try:
        return json.loads(target)
    except json.JSONDecodeError:
        # content_html 내 따옴표로 JSON이 깨지는 경우 필드별로 직접 추출
        def extract_field(text, key):
            m = re.search(rf'"{key}"\s*:\s*"((?:[^"\\]|\\.)*)"', text)
            return m.group(1) if m else ''
        # content_html은 마지막 필드이므로 끝까지 추출
        content_m = re.search(r'"content_html"\s*:\s*"([\s\S]*?)"\s*\}\s*$', target)
        if not content_m:
            content_m = re.search(r'"content_html"\s*:\s*"([\s\S]*)', target)
        return {
            'title':       extract_field(target, 'title'),
            'description': extract_field(target, 'description'),
            'keywords':    extract_field(target, 'keywords'),
            'content_html': content_m.group(1).rstrip('"}').strip() if content_m else '',
        }


# ─── 포스트 HTML 생성 ─────────────────────────────────────
def build_post_html(post_data, date_str, prev_entry):
    title       = post_data["title"]
    description = post_data["description"]
    keywords    = post_data["keywords"]
    content     = post_data["content_html"]
    date_str_ko = date_ko(date_str)

    prev_nav = ""
    if prev_entry:
        prev_nav = (
            f'<a href="{prev_entry["filename"]}" class="post-nav-link prev">'
            f'← {prev_entry["title"]}</a>'
        )

    return f"""<!DOCTYPE html>
<html lang="ko">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <meta name="description" content="{description}">
  <meta name="keywords" content="{keywords}">
  <meta name="robots" content="index, follow">
  <meta name="author" content="{CLINIC_NAME} {DOCTOR}">

  <meta property="og:type"        content="article">
  <meta property="og:title"       content="{title} | {CLINIC_NAME}">
  <meta property="og:description" content="{description}">
  <meta property="og:url"         content="{SITE_URL}/blog/posts/{date_str}.html">
  <meta property="og:site_name"   content="{CLINIC_NAME}">

  <title>{title} | {CLINIC_NAME}</title>

  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Noto+Serif+KR:wght@300;400;600;700&family=Noto+Sans+KR:wght@300;400;500&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="../../style.css">

  <script type="application/ld+json">
  {{
    "@context": "https://schema.org",
    "@type": "BlogPosting",
    "headline": "{title}",
    "description": "{description}",
    "datePublished": "{date_str}",
    "author": {{
      "@type": "Person",
      "name": "{DOCTOR}",
      "worksFor": {{
        "@type": "MedicalBusiness",
        "name": "{CLINIC_NAME}",
        "telephone": "{PHONE}",
        "address": {{
          "@type": "PostalAddress",
          "streetAddress": "약령중앙로 9, 2층",
          "addressLocality": "동대문구",
          "addressRegion": "서울특별시",
          "addressCountry": "KR"
        }}
      }}
    }},
    "publisher": {{
      "@type": "Organization",
      "name": "{CLINIC_NAME}",
      "url": "{SITE_URL}"
    }},
    "mainEntityOfPage": "{SITE_URL}/blog/posts/{date_str}.html"
  }}
  </script>
</head>
<body>

  <!-- 네비게이션 -->
  <nav class="navbar" role="navigation">
    <div class="container">
      <a href="../../index.html" class="logo">
        <span class="logo-main">빛한의원</span>
        <span class="logo-sub">Bit Korean Medicine Clinic</span>
      </a>
      <div class="nav-menu">
        <ul class="nav-links">
          <li><a href="../../about.html">소개</a></li>
          <li><a href="../../programs.html">진료안내</a></li>
          <li><a href="../index.html" class="active">블로그</a></li>
          <li><a href="../../location.html">오시는 길</a></li>
        </ul>
        <div class="nav-cta" style="display:flex; align-items:center; gap:14px;">
          <div style="font-size:0.8rem; display:flex; gap:6px; align-items:center; letter-spacing:0.02em;">
            <a href="../../en/blog/" style="color:inherit; text-decoration:none; opacity:0.7;">EN</a>
            <span style="opacity:0.3;">|</span>
            <a href="../../zh/blog/" style="color:inherit; text-decoration:none; opacity:0.7;">中</a>
            <span style="opacity:0.3;">|</span>
            <a href="../../ja/blog/" style="color:inherit; text-decoration:none; opacity:0.7;">日</a>
          </div>
          <a href="{NAVER_BOOKING}" class="btn btn-primary" target="_blank" rel="noopener">네이버 예약</a>
        </div>
      </div>
      <button class="hamburger" aria-label="메뉴 열기"><span></span><span></span><span></span></button>
    </div>
  </nav>
  <div class="mobile-menu">
    <ul class="nav-links">
      <li><a href="../../index.html">홈</a></li>
      <li><a href="../../about.html">소개</a></li>
      <li><a href="../../programs.html">진료안내</a></li>
      <li><a href="../index.html">블로그</a></li>
      <li><a href="../../location.html">오시는 길</a></li>
    </ul>
    <a href="{NAVER_BOOKING}" class="btn btn-primary" target="_blank" rel="noopener">네이버 예약하기</a>
  </div>

  <main>
    <div class="blog-post-wrap">
      <div class="container">
        <div class="blog-post-inner">

          <header class="post-header">
            <a href="../index.html" class="back-to-blog">← 블로그 목록으로</a>
            <h1 class="post-title">{title}</h1>
            <div class="post-meta">
              <span class="post-date">📅 {date_str_ko}</span>
              <span class="post-author">✍️ {DOCTOR}</span>
              <span class="post-clinic">🏥 {CLINIC_NAME}</span>
            </div>
          </header>

          <article class="post-body">
            {content}
          </article>

          <div class="post-cta-box">
            <p>📍 <strong>{CLINIC_NAME}</strong> — {LOCATION}</p>
            <p>진료 예약 및 궁금한 점은 편하게 문의해 주세요.</p>
            <div class="post-cta-buttons">
              <a href="{NAVER_BOOKING}" class="btn btn-primary" target="_blank" rel="noopener">📅 네이버 예약하기</a>
              <a href="{KAKAO_CHANNEL}" class="btn btn-kakao" target="_blank" rel="noopener">💬 카카오톡 상담</a>
              <a href="tel:{PHONE}" class="btn btn-outline">📞 {PHONE}</a>
            </div>
          </div>

          <nav class="post-nav">
            {prev_nav}
          </nav>

        </div>
      </div>
    </div>
  </main>

  <footer>
    <div class="container">
      <div class="footer-inner">
        <div class="footer-brand">
          <span class="logo-main">빛한의원</span>
          <span class="logo-sub">Bit Korean Medicine Clinic</span>
          <p>마음까지 따뜻해지는 푸근한 손길<br>서울 동대문구에서 여러분의 건강을 함께합니다.</p>
        </div>
        <div class="footer-col">
          <h4>바로가기</h4>
          <ul>
            <li><a href="../../index.html">홈</a></li>
            <li><a href="../../about.html">소개</a></li>
            <li><a href="../../programs.html">진료안내</a></li>
            <li><a href="../index.html">블로그</a></li>
            <li><a href="../../location.html">오시는 길</a></li>
          </ul>
        </div>
        <div class="footer-col">
          <h4>진료 정보</h4>
          <ul>
            <li><span>전화: {PHONE}</span></li>
            <li><span>평일 09:00 – 17:00</span></li>
            <li><span>주말·공휴일 09:00 – 16:00</span></li>
            <li><span>점심 13:00 – 14:00</span></li>
          </ul>
        </div>
      </div>
      <div class="footer-bottom">
        <p>서울특별시 동대문구 약령중앙로 9, 2층 &nbsp;|&nbsp; 대표: 이상진 &nbsp;|&nbsp; 대표번호: {PHONE}</p>
        <p>© 2025 빛한의원. All rights reserved.</p>
      </div>
    </div>
  </footer>

  <script src="../../main.js"></script>
</body>
</html>"""


# ─── 블로그 인덱스 재생성 ─────────────────────────────────
def rebuild_index(manifest):
    cards = ""
    for i, p in enumerate(manifest):
        badge = '<span class="post-badge">최신</span>' if i == 0 else ''
        cards += f"""
        <article class="blog-card fade-in">
          <a href="posts/{p['filename']}" class="blog-card-link">
            <div class="blog-card-body">
              <div class="blog-card-meta">
                <span class="blog-date">{date_ko(p['date'])}</span>
                {badge}
              </div>
              <h2 class="blog-card-title">{p['title']}</h2>
              <p class="blog-card-desc">{p['description']}</p>
              <span class="blog-more">자세히 읽기 →</span>
            </div>
          </a>
        </article>"""

    if not cards:
        cards = '<p class="no-posts">아직 게시글이 없습니다. 곧 첫 번째 포스팅이 업로드됩니다! 😊</p>'

    count = len(manifest)

    html = f"""<!DOCTYPE html>
<html lang="ko">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <meta name="description" content="빛한의원 건강 블로그 — 침 치료, 추나요법, 약침 등 한방 건강 정보와 치료 이야기를 소개합니다. 서울 동대문구 빛한의원 이상진 원장이 직접 작성합니다.">
  <meta name="keywords" content="빛한의원 블로그, 한의원 건강정보, 침 치료, 추나요법, 동대문구 한의원, 한방 치료">
  <meta name="robots" content="index, follow">
  <meta property="og:type"        content="website">
  <meta property="og:title"       content="건강 블로그 | 빛한의원">
  <meta property="og:description" content="빛한의원 이상진 원장이 전하는 한방 건강 정보와 치료 이야기">
  <meta property="og:url"         content="https://bithani.netlify.app/blog/">
  <meta property="og:site_name"   content="빛한의원">
  <title>건강 블로그 | 빛한의원</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Noto+Serif+KR:wght@300;400;600;700&family=Noto+Sans+KR:wght@300;400;500&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="../style.css">
</head>
<body>

  <nav class="navbar" role="navigation">
    <div class="container">
      <a href="../index.html" class="logo">
        <span class="logo-main">빛한의원</span>
        <span class="logo-sub">Bit Korean Medicine Clinic</span>
      </a>
      <div class="nav-menu">
        <ul class="nav-links">
          <li><a href="../about.html">소개</a></li>
          <li><a href="../programs.html">진료안내</a></li>
          <li><a href="index.html" class="active">블로그</a></li>
          <li><a href="../location.html">오시는 길</a></li>
        </ul>
        <div class="nav-cta" style="display:flex; align-items:center; gap:14px;">
          <div style="font-size:0.8rem; display:flex; gap:6px; align-items:center; letter-spacing:0.02em;">
            <a href="../en/blog/" style="color:inherit; text-decoration:none; opacity:0.7;">EN</a>
            <span style="opacity:0.3;">|</span>
            <a href="../zh/blog/" style="color:inherit; text-decoration:none; opacity:0.7;">中</a>
            <span style="opacity:0.3;">|</span>
            <a href="../ja/blog/" style="color:inherit; text-decoration:none; opacity:0.7;">日</a>
          </div>
          <a href="https://naver.me/5If4IVqY" class="btn btn-primary" target="_blank" rel="noopener">네이버 예약</a>
        </div>
      </div>
      <button class="hamburger" aria-label="메뉴 열기"><span></span><span></span><span></span></button>
    </div>
  </nav>
  <div class="mobile-menu">
    <ul class="nav-links">
      <li><a href="../index.html">홈</a></li>
      <li><a href="../about.html">소개</a></li>
      <li><a href="../programs.html">진료안내</a></li>
      <li><a href="index.html">블로그</a></li>
      <li><a href="../location.html">오시는 길</a></li>
    </ul>
    <a href="https://naver.me/5If4IVqY" class="btn btn-primary" target="_blank" rel="noopener">네이버 예약하기</a>
  </div>

  <main>
    <header class="page-header">
      <span class="section-label">Health Blog</span>
      <h1>건강 블로그</h1>
      <p>빛한의원 이상진 원장이 전하는<br>한방 건강 정보와 치료 이야기</p>
    </header>

    <section class="blog-section">
      <div class="container">
        <div class="blog-stats fade-in">
          총 <strong>{count}</strong>개의 포스팅
        </div>
        <div class="blog-grid">
          {cards}
        </div>
      </div>
    </section>

    <section class="cta-banner">
      <div class="container">
        <h2 class="fade-in">직접 상담받고 싶으신가요?</h2>
        <p class="fade-in">카카오톡으로 간단히 증상을 알려주시면 원장님이 직접 답변드립니다.</p>
        <div class="cta-buttons fade-in">
          <a href="https://naver.me/5If4IVqY" class="btn btn-white" target="_blank" rel="noopener">📅 네이버 예약하기</a>
          <a href="http://pf.kakao.com/_bxbUxfG" class="btn btn-kakao" target="_blank" rel="noopener">💬 카카오톡 상담</a>
        </div>
      </div>
    </section>
  </main>

  <footer>
    <div class="container">
      <div class="footer-inner">
        <div class="footer-brand">
          <span class="logo-main">빛한의원</span>
          <span class="logo-sub">Bit Korean Medicine Clinic</span>
          <p>마음까지 따뜻해지는 푸근한 손길<br>서울 동대문구에서 여러분의 건강을 함께합니다.</p>
        </div>
        <div class="footer-col">
          <h4>바로가기</h4>
          <ul>
            <li><a href="../index.html">홈</a></li>
            <li><a href="../about.html">소개</a></li>
            <li><a href="../programs.html">진료안내</a></li>
            <li><a href="index.html">블로그</a></li>
            <li><a href="../location.html">오시는 길</a></li>
          </ul>
        </div>
        <div class="footer-col">
          <h4>진료 정보</h4>
          <ul>
            <li><span>전화: 02-966-6669</span></li>
            <li><span>평일 09:00 – 17:00</span></li>
            <li><span>주말·공휴일 09:00 – 16:00</span></li>
            <li><span>점심 13:00 – 14:00</span></li>
          </ul>
        </div>
      </div>
      <div class="footer-bottom">
        <p>서울특별시 동대문구 약령중앙로 9, 2층 &nbsp;|&nbsp; 대표: 이상진 &nbsp;|&nbsp; 대표번호: 02-966-6669</p>
        <p>© 2025 빛한의원. All rights reserved.</p>
      </div>
    </div>
  </footer>

  <script src="../main.js"></script>
</body>
</html>"""

    idx_path = os.path.join(BLOG_DIR, 'index.html')
    with open(idx_path, 'w', encoding='utf-8') as f:
        f.write(html)
    print(f"  ✅ blog/index.html 재생성 완료 (총 {count}개)")


# ─── 메인 ─────────────────────────────────────────────────
def main():
    os.makedirs(POSTS_DIR, exist_ok=True)

    manifest = load_manifest()
    today    = datetime.date.today()
    date_str = today.strftime('%Y-%m-%d')

    # 오늘 이미 포스팅된 경우 스킵
    if manifest and manifest[0]['date'] == date_str:
        print(f"⏭️  오늘({date_str}) 이미 포스팅됨. 종료.")
        sys.exit(0)

    topic = get_topic(manifest)
    print(f"📌 오늘의 주제: {topic}")

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("❌ ANTHROPIC_API_KEY 환경변수가 없습니다.")
        sys.exit(1)

    client = anthropic.Anthropic(api_key=api_key)

    print("✍️  Claude API로 본문 생성 중...")
    post_data = generate_content(topic, client)
    print(f"  제목: {post_data['title']}")

    # 포스트 HTML 저장
    prev_entry = manifest[0] if manifest else None
    post_html  = build_post_html(post_data, date_str, prev_entry)
    post_path  = os.path.join(POSTS_DIR, f"{date_str}.html")
    with open(post_path, 'w', encoding='utf-8') as f:
        f.write(post_html)
    print(f"  ✅ blog/posts/{date_str}.html 생성 완료")

    # 매니페스트 업데이트 (최신 글이 앞)
    manifest.insert(0, {
        "date":        date_str,
        "filename":    f"{date_str}.html",
        "title":       post_data["title"],
        "description": post_data["description"],
        "keywords":    post_data["keywords"],
        "topic":       topic,
    })
    save_manifest(manifest)
    print(f"  ✅ blog/manifest.json 업데이트 완료")

    # 블로그 인덱스 재생성
    rebuild_index(manifest)

    print(f"\n🎉 포스팅 완료! ({date_str})")


if __name__ == '__main__':
    main()
