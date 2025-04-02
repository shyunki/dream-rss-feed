# 겐이츠의 꿈해몽 RSS 피드

GitHub Actions를 통해 자동으로 생성되는 꿈해몽 RSS 피드입니다.

## 기능

- 매일 00:00 UTC에 자동으로 꿈해몽 생성
- 50개의 꿈 키워드 중 무작위로 3개 선택
- OpenAI API를 사용하여 해몽 생성
- RSS 피드로 배포 (GitHub Pages)

## 사용 방법

RSS 리더에서 다음 URL을 구독하세요:
```
https://shyunki.github.io/dream-rss-feed/rss.xml
```

## 사용 키워드

사용된 키워드는 `used_keywords.json` 파일에 저장되며, 모든 키워드가 사용된 후에 초기화됩니다.
