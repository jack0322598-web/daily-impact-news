import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import time
import urllib.parse

# 타겟 날짜 설정 (어제 날짜)
yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y.%m.%d")
print(f"--- 🎯 타겟 날짜(어제): {yesterday} ---")

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

impact_news_data = []
macro_news_data = []
seen_links = set()

# ==========================================
# 1. 임팩트온 스크랩 섹션 (기존 성공 코드)
# ==========================================
print("\n🌱 1. 임팩트온 뉴스 스크랩 시작...")
try:
    impact_url = "https://www.impacton.net/news/articleList.html"
    response = requests.get(impact_url, headers=headers, timeout=10)
    soup = BeautifulSoup(response.text, 'html.parser')
    article_tags = soup.select("a[href*='articleView.html']")
    
    count = 0
    for tag in article_tags:
        if count >= 5:
            break
        title = tag.text.strip()
        if not title or len(title) < 4: continue
        
        href = tag.get("href", "")
        if not href: continue
        link = href if href.startswith("http") else "https://www.impacton.net" + href
        
        if link in seen_links: continue
        seen_links.add(link)
        if "pro" in title.lower() or "유료" in title: continue
        
        try:
            article_res = requests.get(link, headers=headers, timeout=10)
            article_soup = BeautifulSoup(article_res.text, 'html.parser')
            date_meta = article_soup.select_one('meta[property="article:published_time"]')
            
            if date_meta and date_meta.get("content"):
                article_date = date_meta["content"][:10].replace("-", ".")
            else:
                date_li = article_soup.select("ul.info-text li")
                article_date = "날짜 확인 불가"
                for li in date_li:
                    if "승인" in li.text:
                        article_date = li.text.replace("승인", "").strip()[:10]
                        break
            
            if article_date == yesterday:
                print(f"✅ 임팩트온 수집 완료: {title}")
                impact_news_data.append({
                    "title": title,
                    "link": link,
                    "date": f"{article_date} (임팩트온)"
                })
                count += 1
            time.sleep(1)
        except Exception as e:
            print(f"⏩ 임팩트온 개별 기사 건너뜀 (오류): {e}")
except Exception as e:
    print(f"❌ 임팩트온 메인 페이지 접속 실패: {e}")


# ==========================================
# 2. 구글 뉴스 거시경제 스크랩 섹션 (🌟 무적 RSS 방식으로 전면 수정)
# ==========================================
print("\n🎯 2. 거시경제 구글 뉴스 스크랩 시작...")
keywords = ["미국 관세", "글로벌 외교", "금리 인상"]

for keyword in keywords:
    print(f"🔍 키워드 [{keyword}] 검색 중...")
    try:
        encoded_keyword = urllib.parse.quote(keyword)
        # 🌟 구글 뉴스 RSS 피드 주소를 사용하여 보안망과 태그 변경 문제를 원천 봉쇄합니다.
        google_rss_url = f"https://news.google.com/rss/search?q={encoded_keyword}%20when%3A1d&hl=ko&gl=KR&ceid=KR%3Ako"
        
        response = requests.get(google_rss_url, headers=headers, timeout=10)
        # XML 구조이므로 xml 또는 html.parser로 파싱합니다.
        soup = BeautifulSoup(response.text, 'xml')
        
        # RSS 방식에서는 기사 하나하나가 <item> 태그 안에 들어가 있습니다.
        items = soup.select("item")
        
        count = 0
        for item in items:
            if count >= 3: # 키워드당 3개씩만
                break
                
            title = item.title.text.strip() if item.title else ""
            link = item.link.text.strip() if item.link else ""
            publisher = item.source.text.strip() if item.source else "언론사"
            
            # 제목에서 뒤에 붙는 ' - 언론사명' 제거해서 깔끔하게 만들기
            if " - " in title:
                title = title.rsplit(" - ", 1)[0]
                
            if not title or not link: continue
            if link in seen_links: continue
            seen_links.add(link)
            
            print(f"✅ 구글 뉴스(RSS) 수집 완료: [{publisher}] {title}")
            macro_news_data.append({
                "title": f"[{keyword}] {title}",
                "link": link,
                "date": f"{yesterday} ({publisher})"
            })
            count += 1
            
    except Exception as e:
        print(f"⏩ 구글 뉴스 키워드 [{keyword}] 건너뜀 (오류): {e}")


# ==========================================
# 3. 통합 웹페이지(HTML) 생성 섹션
# ==========================================
print("\n--- 🌐 통합 웹페이지(HTML) 생성 시작 ---")

html_content = f"""
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <title>📰 오늘의 비즈니스 & 거시경제 뉴스 스크랩</title>
    <style>
        body {{ font-family: 'Malgun Gothic', sans-serif; max-width: 900px; margin: auto; padding: 20px; background-color: #f4f7f6; }}
        h1 {{ color: #2c3e50; text-align: center; margin-bottom: 5px; }}
        .date-title {{ text-align: center; color: #7f8c8d; margin-bottom: 40px; font-size: 1.1em; }}
        .section-title {{ font-size: 1.5em; color: #2c3e50; border-left: 5px solid #2ecc71; padding-left: 10px; margin-top: 40px; margin-bottom: 20px; font-weight: bold; }}
        .section-title.macro {{ border-left-color: #3498db; }}
        .news-card {{ background: white; padding: 20px; margin-bottom: 15px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }}
        .news-title {{ font-size: 1.15em; font-weight: bold; margin-bottom: 8px; }}
        .news-title a {{ color: #333; text-decoration: none; }}
        .news-title a:hover {{ color: #2980b9; text-decoration: underline; }}
        .news-date {{ font-size: 0.85em; color: #95a5a6; }}
        .no-news {{ color: #95a5a6; font-style: italic; padding: 10px; }}
    </style>
</head>
<body>
    <h1>📋 오늘의 종합 뉴스 브리핑</h1>
    <div class="date-title">업데이트 날짜: {yesterday}</div>

    <div class="section-title">🌱 오늘의 임팩트 비즈니스 뉴스</div>
"""

if not impact_news_data:
    html_content += "<div class='no-news'>어제자 발행된 임팩트 뉴스가 없습니다.</div>"
else:
    for news in impact_news_data:
        html_content += f"""
        <div class="news-card">
            <div class="news-title"><a href="{news['link']}" target="_blank">{news['title']}</a></div>
            <div class="news-date">발행일: {news['date']}</div>
        </div>
        """

html_content += """
    <div class="section-title macro">🎯 오늘의 거시경제 핵심 뉴스</div>
"""

if not macro_news_data:
    html_content += "<div class='no-news'>수집된 거시경제 뉴스가 없습니다.</div>"
else:
    for news in macro_news_data:
        html_content += f"""
        <div class="news-card">
            <div class="news-title"><a href="{news['link']}" target="_blank">{news['title']}</a></div>
            <div class="news-date">발행일: {news['date']}</div>
        </div>
        """
        
html_content += "</body></html>"

with open("index.html", "w", encoding="utf-8") as f:
    f.write(html_content)

print("🎉 통합 index.html 파일이 성공적으로 생성되었습니다!")
