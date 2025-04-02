from openai import OpenAI
from feedgen.feed import FeedGenerator
from datetime import datetime, timezone
import os, json, random

client = OpenAI()
rss_file = "docs/rss.xml"

# Load keyword list
with open("dream_keywords.json", "r", encoding="utf-8") as f:
    all_keywords = json.load(f)

# Load used keywords
used_keywords = []
if os.path.exists("used_keywords.json"):
    with open("used_keywords.json", "r", encoding="utf-8") as f:
        used_keywords = json.load(f)

# Filter unused
unused_keywords = [kw for kw in all_keywords if kw not in used_keywords]
if len(unused_keywords) < 3:
    used_keywords = []
    unused_keywords = all_keywords.copy()

# Pick 3
picked = random.sample(unused_keywords, 3)
dreams = []

for keyword in picked:
    prompt = f"'{keyword}' 꿈에 대한 해몽을 3~4문장으로 설명해줘."
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}]
    )
    text = response.choices[0].message.content.strip()
    dreams.append((keyword, text))
    used_keywords.append(keyword)

# Generate RSS
fg = FeedGenerator()
fg.title('겐이츠 꿈해몽 RSS')
fg.link(href='https://shyunki.github.io/dream-rss-feed/rss.xml')
fg.description('매일 자동 생성되는 3개의 꿈 해몽 피드입니다.')
fg.language('ko')

for kw, desc in dreams:
    fe = fg.add_entry()
    fe.title(f"{datetime.now().strftime('%Y-%m-%d')} - {kw} 꿈 해몽")
    fe.link(href='https://shyunki.github.io/dream-rss-feed/rss.xml')
    fe.description(desc)
    fe.pubDate(datetime.now(timezone.utc))
# 저장
fg.rss_file(rss_file)

with open("used_keywords.json", "w", encoding="utf-8") as f:
    json.dump(used_keywords, f, ensure_ascii=False, indent=2)

