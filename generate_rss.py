from openai import OpenAI
from feedgen.feed import FeedGenerator
from datetime import datetime, timezone
import os
import json
import random

# 디렉토리가 없으면 생성
os.makedirs("docs", exist_ok=True)

# OpenAI API 클라이언트 초기화
client = OpenAI()

# 파일 경로 설정
rss_file = "docs/rss.xml"
dream_keywords_file = "dream_keywords.json"
used_keywords_file = "used_keywords.json"

# 오늘 날짜 (한국 시간대 고려)
today = datetime.now().strftime('%Y-%m-%d')
today_rfc822 = datetime.now(timezone.utc).strftime('%a, %d %b %Y %H:%M:%S +0000')

print(f"🔄 꿈해몽 RSS 피드 업데이트 시작 ({today})")

# 키워드 목록 로드
try:
    with open(dream_keywords_file, "r", encoding="utf-8") as f:
        all_keywords = json.load(f)
    print(f"✅ 총 {len(all_keywords)}개의 키워드를 로드했습니다.")
except Exception as e:
    print(f"❌ 키워드 파일 로드 실패: {e}")
    all_keywords = []
    exit(1)

# 사용된 키워드 로드
used_keywords = []
if os.path.exists(used_keywords_file):
    try:
        with open(used_keywords_file, "r", encoding="utf-8") as f:
            used_keywords = json.load(f)
        print(f"ℹ️ 지금까지 {len(used_keywords)}개의 키워드가 사용되었습니다.")
    except Exception as e:
        print(f"⚠️ 사용된 키워드 파일 로드 실패, 새로 시작합니다: {e}")
        used_keywords = []

# 미사용 키워드 필터링
unused_keywords = [kw for kw in all_keywords if kw not in used_keywords]
if len(unused_keywords) < 3:
    print("ℹ️ 미사용 키워드가 부족하여 모든 키워드를 재사용합니다.")
    used_keywords = []  # 초기화
    unused_keywords = all_keywords.copy()

# 3개 키워드 선택
picked = random.sample(unused_keywords, 3)
print(f"🎲 오늘의 선택 키워드: {', '.join(picked)}")

# 키워드 별 꿈해몽 생성
dreams = []
for i, keyword in enumerate(picked, 1):
    try:
        prompt = f"'{keyword}' 꿈에 대한 해몽을 3~4문장으로 앞에 스레드 감성으로 반말로 잘풀어서 설명해줘."
        print(f"📝 '{keyword}' 키워드에 대한 해몽 생성 중...")
        
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}]
        )
        
        text = response.choices[0].message.content.strip()
        dreams.append((keyword, text))
        used_keywords.append(keyword)
        print(f"✅ 생성 완료 ({i}/3)")
    except Exception as e:
        print(f"❌ '{keyword}' 해몽 생성 실패: {e}")

# RSS 피드 생성
try:
    fg = FeedGenerator()
    fg.title('겐이츠의 꿈해몽 피드')
    fg.link(href='https://shyunki.github.io/dream-rss-feed/rss.xml')
    fg.description('매일 3개의 꿈 키워드에 대한 풍부한 해몽을 제공합니다.')
    fg.language('ko-kr')
    fg.pubDate(today_rfc822)
    
    # 이전 RSS 파일에서 기존 항목 로드 (선택적)
    existing_items = []
    if os.path.exists(rss_file):
        try:
            import xml.etree.ElementTree as ET
            tree = ET.parse(rss_file)
            root = tree.getroot()
            for item in root.findall('.//item'):
                title_elem = item.find('title')
                if title_elem is not None and not title_elem.text.startswith(today):
                    existing_items.append(item)
        except Exception as e:
            print(f"⚠️ 기존 RSS 항목 로드 실패: {e}")
    
    # 새 항목 추가
    for i, (kw, desc) in enumerate(dreams, 1):
        fe = fg.add_entry()
        fe.title(f"{today} 🌙 {kw} 꿈")
        fe.link(href=f'https://shyunki.github.io/dream-rss-feed/rss.xml#{i}')
        fe.description(desc)
        fe.pubDate(today_rfc822)
    
    # RSS 파일 저장
    fg.rss_file(rss_file)
    print(f"✅ RSS 피드가 {rss_file}에 저장되었습니다.")
    
    # 사용된 키워드 저장
    with open(used_keywords_file, "w", encoding="utf-8") as f:
        json.dump(used_keywords, f, ensure_ascii=False, indent=2)
    print(f"✅ 사용된 키워드 목록이 업데이트되었습니다 (총 {len(used_keywords)}개)")
    
    print("🎉 모든 작업이 성공적으로 완료되었습니다!")
except Exception as e:
    print(f"❌ RSS 피드 생성 중 오류 발생: {e}")
