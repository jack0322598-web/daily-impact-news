import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import time

yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y.%m.%d")
print(f"--- 🎯 타겟 날짜(어제): {yesterday} ---")

url = "https://www.impacton.net/news/articleList.html"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}
response = requests.get(url, headers=headers)
soup = BeautifulSoup(response.text, 'html.parser')

article_tags = soup.select("a[href*='articleView.html']")
seen_links = set()
count = 0
news_data = []

print("🔍 기사 수집을 시작합니다...\n")

for tag in article_tags:
    if count >= 5:  # 어제 기사를 5개 찾으면 멈춥니다.
        break
        
    title = tag.text.strip()
    if not title or len(title) < 4:
        continue
        
    link = tag["href"]
    if not link.startswith("http"):
        link = "https://www.impacton.net" + link
        
    if link in seen_links:
        continue
    seen_links.add(link)
    
    if "pro" in title.lower() or "유료" in title:
        continue
        
    try:
        article_res = requests.get(link, headers=headers)
        article_soup = BeautifulSoup(article_res.text, 'html.parser')
        
        date_meta = article_soup.select_one('meta[property="article:published_time"]')
        if date_meta:
            article_date = date_meta["content"][:10].replace("-", ".")
        else:
            date_li = article_soup.select("ul.info-text li")
            article_date = "날짜 확인 불가"
            for li in date_li:
                if "승인" in li.text:
                    article_date = li.text.replace("승인", "").strip()[:10]
                    break
        
        # 🌟 핵심 수정 포인트: 어제 날짜가 아니면 바구니에 담지 않고 넘어갑니다!
        if article_date != yesterday:
            print(f"⏩ 패스 (날짜 불일치, 발행일: {article_date}) - {title}")
            continue
            
        print(f"✅ 수집 완료: {title}")
        
        summary = "AI 3줄 요약 기능은 현재 충전 대기 중입니다. 원문 링크를 클릭해 기사를 확인해 주세요! 🚀"
        
        news_data.append({
            "title": title,
            "link": link,
            "date": article_date,
            "summary": summary
        })
        
        count += 1
        time.sleep(1) 
        
    except Exception as e:
        print(f"❌ 기사 크롤링 중 오류 발생: {e}")

print("\n--- 🌐 웹페이지(HTML) 생성 시작 ---")

html_content = f"""
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <title>오늘의 임팩트 비즈니스 뉴스 요약</title>
    <style>
        body {{ font-family: 'Malgun Gothic', sans-serif; max-width: 800px; margin: auto; padding: 20px; background-color: #f4f7f6; }}
        h1 {{ color: #2c3e50; text-align: center; }}
        .date-title {{ text-align: center; color: #7f8c8d; margin-bottom: 30px; }}
        .news-card {{ background: white; padding: 20px; margin-bottom: 20px; border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }}
        .news-title {{ font-size: 1.2em; font-weight: bold; margin-bottom: 10px; }}
        .news-title a {{ color: #2980b9; text-decoration: none; }}
        .news-title a:hover {{ text-decoration: underline; }}
        .news-date {{ font-size: 0.9em; color: #95a5a6; margin-bottom: 15px; }}
        .news-summary {{ line-height: 1.6; color: #34495e; }}
    </style>
</head>
<body>
    <h1>🌱 오늘의 임팩트 뉴스 요약</h1>
    <div class="date-title">최근 업데이트: {yesterday}</div>
"""

for news in news_data:
    html_content += f"""
    <div class="news-card">
        <div class="news-title"><a href="{news['link']}" target="_blank">{news['title']}</a></div>
        <div class="news-date">발행일: {news['date']}</div>
        <div class="news-summary">{news['summary']}</div>
    </div>
    """
    
html_content += "</body></html>"

with open("index.html", "w", encoding="utf-8") as f:
    f.write(html_content)

print("🎉 index.html 파일이 성공적으로 생성되었습니다!")