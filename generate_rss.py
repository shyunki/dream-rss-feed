from openai import OpenAI
from feedgen.feed import FeedGenerator
from datetime import datetime, timezone, timedelta
import os
import json
import random
import sys
import traceback
import uuid
import time

# 디버깅 함수
def log(message):
    """로그 출력 함수"""
    timestamp = datetime.now().strftime('%H:%M:%S')
    print(f"[{timestamp}] {message}")
    sys.stdout.flush()  # 즉시 출력 보장

# 스크립트 시작
log("🚀 꿈해몽 RSS 생성 스크립트 시작")

# 디렉토리가 없으면 생성
os.makedirs("docs", exist_ok=True)
log("✅ docs 디렉토리 확인 완료")

# 현재 작업 디렉토리 확인
log(f"📂 현재 작업 디렉토리: {os.getcwd()}")
log(f"📂 디렉토리 내용: {os.listdir('.')}")

# OpenAI API 클라이언트 초기화
try:
    client = OpenAI()
    log("✅ OpenAI API 클라이언트 초기화 완료")
    # API 키 설정 확인
    key_set = os.environ.get("OPENAI_API_KEY") is not None
    log(f"🔑 API 키 설정 상태: {'설정됨' if key_set else '설정되지 않음'}")
except Exception as e:
    log(f"❌ OpenAI API 클라이언트 초기화 실패: {e}")
    traceback.print_exc()
    sys.exit(1)

# 파일 경로 설정
rss_file = "docs/rss.xml"
dream_keywords_file = "dream_keywords.json"
used_keywords_file = "used_keywords.json"

log(f"📁 RSS 파일 경로: {rss_file}")
log(f"📁 키워드 파일 경로: {dream_keywords_file}")
log(f"📁 사용된 키워드 파일 경로: {used_keywords_file}")

# 오늘 날짜 (한국 시간대 고려)
KST = timezone(timedelta(hours=9))
now = datetime.now(KST)
today = now.strftime('%Y-%m-%d')
today_rfc822 = now.strftime('%a, %d %b %Y %H:%M:%S +0900')
timestamp = int(time.time())  # Unix 타임스탬프 (캐시 방지용)

log(f"📅 오늘 날짜: {today} (KST)")
log(f"⏱️ 타임스탬프: {timestamp}")

# 캐시 방지용 고유 ID 생성
cache_buster = str(uuid.uuid4())[:8]
log(f"🔄 캐시 방지 ID: {cache_buster}")

# 키워드 목록 로드
try:
    with open(dream_keywords_file, "r", encoding="utf-8") as f:
        all_keywords = json.load(f)
    log(f"✅ 총 {len(all_keywords)}개의 키워드를 로드했습니다.")
except Exception as e:
    log(f"❌ 키워드 파일 로드 실패: {e}")
    traceback.print_exc()
    log(f"현재 디렉토리: {os.getcwd()}")
    log(f"파일 목록: {os.listdir('.')}")
    sys.exit(1)

# 사용된 키워드 로드
used_keywords = []
if os.path.exists(used_keywords_file):
    try:
        with open(used_keywords_file, "r", encoding="utf-8") as f:
            content = f.read().strip()
            if content:  # 내용이 있는 경우에만 파싱
                used_keywords = json.loads(content)
            else:
                log("⚠️ 사용된 키워드 파일이 비어 있습니다. 새로 시작합니다.")
        log(f"ℹ️ 지금까지 {len(used_keywords)}개의 키워드가 사용되었습니다.")
    except json.JSONDecodeError as e:
        log(f"⚠️ 사용된 키워드 파일 JSON 파싱 실패: {e}")
        log(f"파일 내용: {open(used_keywords_file, 'r').read()}")
        used_keywords = []
    except Exception as e:
        log(f"⚠️ 사용된 키워드 파일 로드 실패, 새로 시작합니다: {e}")
        used_keywords = []
else:
    log("ℹ️ 사용된 키워드 파일이 없습니다. 새로 생성합니다.")

# 미사용 키워드 필터링
unused_keywords = [kw for kw in all_keywords if kw not in used_keywords]
log(f"ℹ️ 미사용 키워드 수: {len(unused_keywords)}")

if len(unused_keywords) < 3:
    log("ℹ️ 미사용 키워드가 부족하여 모든 키워드를 재사용합니다.")
    used_keywords = []  # 초기화
    unused_keywords = all_keywords.copy()

# 3개 키워드 선택
picked = random.sample(unused_keywords, 3)
log(f"🎲 오늘의 선택 키워드: {', '.join(picked)}")

# 키워드 별 꿈해몽 생성
dreams = []
for i, keyword in enumerate(picked, 1):
    try:
        prompt = f"'{keyword}' 꿈에 대한 해몽을 3~4문장으로 앞에 스레드 감성으로 반말로 잘풀어서 설명해줘."
        log(f"📝 '{keyword}' 키워드에 대한 해몽 생성 중...")
        
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=300
        )
        
        text = response.choices[0].message.content.strip()
        dreams.append((keyword, text))
        used_keywords.append(keyword)
        log(f"✅ 생성 완료 ({i}/3): {text[:50]}...")
    except Exception as e:
        log(f"❌ '{keyword}' 해몽 생성 실패: {e}")
        traceback.print_exc()

# 기존 RSS 항목 로드
existing_entries = []
try:
    if os.path.exists(rss_file):
        log("📂 기존 RSS 파일 읽기 시도 중...")
        import xml.etree.ElementTree as ET
        
        try:
            tree = ET.parse(rss_file)
            root = tree.getroot()
            channel = root.find('channel')
            
            if channel is not None:
                items = channel.findall('item')
                log(f"🔍 기존 항목 {len(items)}개 발견")
                
                for item in items:
                    title = item.find('title')
                    if title is not None and not title.text.startswith(today):
                        link = item.find('link')
                        desc = item.find('description')
                        pubdate = item.find('pubDate')
                        
                        if all([title, link, desc, pubdate]):
                            existing_entries.append({
                                'title': title.text,
                                'link': link.text,
                                'description': desc.text,
                                'pubDate': pubdate.text
                            })
                            
                log(f"✅ {len(existing_entries)}개의 이전 항목을 유지합니다.")
        except ET.ParseError as e:
            log(f"⚠️ XML 파싱 실패: {e}")
            log("⚠️ 기존 RSS 파일 내용을 읽어 오류 확인:")
            with open(rss_file, 'r', encoding='utf-8') as f:
                log(f.read()[:500] + "...")  # 처음 500자만 표시
    else:
        log("📂 기존 RSS 파일이 없습니다. 새로 생성합니다.")
except Exception as e:
    log(f"⚠️ 기존 RSS 파일 처리 중 오류 발생: {e}")
    traceback.print_exc()
    log("⚠️ 새 파일을 생성합니다.")

# RSS 피드 생성
try:
    if len(dreams) == 0:
        log("⚠️ 생성된 꿈해몽이 없습니다. RSS 피드를 업데이트하지 않습니다.")
        sys.exit(1)
        
    log("🔄 RSS 피드 생성 시작...")
    fg = FeedGenerator()
    fg.title('겐이츠의 꿈해몽 피드')
    
    # 캐시 방지를 위한 쿼리 파라미터가 포함된 링크
    fg.link(href=f'https://shyunki.github.io/dream-rss-feed/rss.xml?v={timestamp}')
    
    # 타임스탬프로 설명에 변경사항 추가
    fg.description(f'매일 3개의 꿈 키워드에 대한 풍부한 해몽을 제공합니다. (업데이트: {today})')
    fg.language('ko-kr')
    
    # 매번 업데이트되는 pubDate
    fg.pubDate(today_rfc822)
    
    # 캐시 방지용 고유 태그 추가
    fg.generator(f'Dream RSS Generator {cache_buster}')
    
    # 새 항목 추가
    for i, (kw, desc) in enumerate(dreams, 1):
        fe = fg.add_entry()
        fe.title(f"{today} 🌙 {kw} 꿈")
        # 캐시 방지를 위해 타임스탬프 추가
        fe.link(href=f'https://shyunki.github.io/dream-rss-feed/rss.xml#{i}_{timestamp}')
        fe.description(desc)
        fe.pubDate(today_rfc822)
        # 고유 ID 추가
        fe.id(f'https://shyunki.github.io/dream-rss-feed/dream/{kw}_{timestamp}_{cache_buster}')
        log(f"➕ RSS 항목 추가: {kw}")
    
    # 기존 항목 추가 (최대 30개만 유지)
    max_old_entries = 30 - len(dreams)
    for i, entry in enumerate(existing_entries[:max_old_entries]):
        fe = fg.add_entry()
        fe.title(entry['title'])
        fe.link(href=entry['link'])
        fe.description(entry['description'])
        fe.pubDate(entry['pubDate'])
        log(f"➕ 기존 RSS 항목 유지: {entry['title'][:30]}...")
    
    # RSS 파일 저장
    fg.rss_file(rss_file)
    log(f"✅ RSS 피드가 {rss_file}에 저장되었습니다.")
    
    # HTML 리다이렉트 페이지 생성 (선택적)
    html_file = "docs/index.html"
    with open(html_file, "w", encoding="utf-8") as f:
        f.write(f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta http-equiv="refresh" content="0;url=./rss.xml?v={timestamp}">
    <title>겐이츠의 꿈해몽 피드</title>
</head>
<body>
    <h1>겐이츠의 꿈해몽 피드</h1>
    <p>RSS 피드로 리다이렉트됩니다. 자동으로 이동하지 않으면 <a href="./rss.xml?v={timestamp}">여기</a>를 클릭하세요.</p>
    <p>마지막 업데이트: {today}</p>
</body>
</html>""")
    log(f"✅ HTML 리다이렉트 페이지가 {html_file}에 생성되었습니다.")
    
    # RSS 파일 내용 확인
    if os.path.exists(rss_file):
        file_size = os.path.getsize(rss_file)
        log(f"📄 RSS 파일 크기: {file_size} 바이트")
        if file_size > 0:
            with open(rss_file, 'r', encoding='utf-8') as f:
                content = f.read(200)  # 처음 200자만 표시
                log(f"📄 RSS 파일 시작 부분: {content}...")
        else:
            log("⚠️ RSS 파일이 비어 있습니다!")
    
    # 사용된 키워드 저장
    try:
        with open(used_keywords_file, "w", encoding="utf-8") as f:
            # 중복 제거하여 저장
            unique_used_keywords = list(set(used_keywords))
            json.dump(unique_used_keywords, f, ensure_ascii=False, indent=2)
        log(f"✅ 사용된 키워드 목록이 업데이트되었습니다 (총 {len(set(used_keywords))}개)")
        
        # 파일 내용 확인
        with open(used_keywords_file, "r", encoding="utf-8") as f:
            content = f.read()
        log(f"📄 사용된 키워드 파일 내용 확인: {content[:100]}...")
    except Exception as e:
        log(f"❌ 사용된 키워드 저장 실패: {e}")
        traceback.print_exc()
    
    # 항상 변경사항이 있도록 더미 파일 생성
    dummy_file = "docs/last_update.txt"
    with open(dummy_file, "w", encoding="utf-8") as f:
        f.write(f"Last updated: {today} {datetime.now().strftime('%H:%M:%S')}\nCache buster: {cache_buster}\n")
    log(f"✅ 업데이트 타임스탬프 파일 생성 완료")
    
    log("🎉 모든 작업이 성공적으로 완료되었습니다!")
except Exception as e:
    log(f"❌ RSS 피드 생성 중 오류 발생: {e}")
    traceback.print_exc()
    sys.exit(1)
