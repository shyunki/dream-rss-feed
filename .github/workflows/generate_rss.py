import json
import os
import openai
from feedgen.feed import FeedGenerator
from datetime import datetime

# OpenAI API 키 설정
openai.api_key = os.getenv('OPENAI_API_KEY')

# 파일 경로 설정
keywords_file = 'dream_keywords.json'
used_keywords_file = 'used_keywords.json'
rss_file = 'docs/rss.xml'

# 꿈 키워드 로드
with open(keywords_file, 'r', encoding='utf-8') as f:
    keywords = json.load(f)

# 사용된 키워드 로드
if os.path.exists(used_keywords_file):
    with open(used_keywords_file, 'r', encoding='utf-8') as f:
        used_keywords = json.load(f)
else:
    used_keywords = []

# 사용되지 않은 키워드 필터링
unused_keywords = [kw for kw in keywords if kw not in used_keywords]

# 모든 키워드를 사용했다면, 사용된 키워드 목록 초기화
if len(unused_keywords) < 3:
    used_keywords = []
    unused_keywords = keywords

# 랜덤하게 3개의 키워드 선택
selected_keywords = unused_keywords[:3]

# 선택된 키워드에 대한 해몽 생성
dream_interpretations = []
for keyword in selected_keywords:
    prompt = f"'{keyword}' 꿈에 대한 해몽을 자세히 설명해줘."
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}]
    )
    interpretation = response.choices[0].message['content'].strip()
    dream_interpretations.append((keyword, interpretation))
    used_keywords.append(keyword)

# RSS 피드 생성
fg = FeedGenerator()
fg.title('꿈해몽 RSS 피드')
fg.link(href='https://shyunki.github.io/dream-rss-feed/rss.xml')
fg.description('매일 새로운 꿈해몽을 제공합니다.')
fg.language('ko')

for keyword, interpretation in dream_interpretations:
    fe = fg.add_entry()
    fe.title(f"{datetime.now().strftime('%Y-%m-%d')} - {keyword} 꿈 해몽")
    fe.link(href=f'https://shyunki.github.io/dream-rss-feed/rss.xml#{keyword}')
    fe.description(interpretation)
    fe.pubDate(datetime.now())

# RSS 파일 저장
fg.rss_file(rss_file)

# 사용된 키워드 목록 업데이트
with open(used_keywords_file, 'w', encoding='utf-8') as f:
    json.dump(used_keywords, f, ensure_ascii=False, indent=2)
