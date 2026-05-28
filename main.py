import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import time
import google.generativeai as genai # 🌟 구글 Gemini 라이브러리로 변경

# 🌟 여기에 발급받은 구글 Gemini API 키를 붙여넣으세요! (AIza... 로 시작)
genai.configure(api_key="AQ.Ab8RN6KKahZGfO1WCrhNVt0d6ZAJIB9oVTHlarw2l7IdxysM5w")
model = genai.GenerativeModel('gemini-1.5-flash')

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

print("🔍 기사 수집 및 AI 요약을 시작합니다...\n")

for tag in article_tags:
    if count >= 5: 
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
        
        if article_date != yesterday:
            continue
            
        # 본문 가져오기
        content_div = article_soup.select_one("#article-view-content-div")
        content = content_div.text.strip().replace("\n", " ")[:1500] if content_div else ""
        
        # 🌟 완전 무료! Gemini 3줄 요약 실행
        print(f"🤖 Gemini가 '{title}' 요약 중...")
        try:
            if content:
                prompt = f"다음 뉴스 기사를 정확히 3줄로 요약해 줘. 각 줄은 불릿 포인트(-)로 시작해:\n\n{content}"
                ai_response = model.generate_content(prompt)
                summary = ai_response.text.strip()
                # HTML 줄바꿈 태그로 변환
                summary = summary.replace('\n', '<br>')
            else:
                summary = "본문을 불러올 수 없어 요약하지 못했습니다."
        except Exception as ai_e:
            summary = f"요약 중 오류 발생: {ai_e}"
            print(f"🚫 [요약 실패] {ai_e}")
            
        news_data.append({
            "title": title,
            "link": link,
            "date": article_date,
            "summary": summary
        })
        
        count += 1
        time.sleep(2) # 무료 API 보호를 위해 2초씩 대기
        
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
