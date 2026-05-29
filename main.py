import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
import urllib.parse
import time

# ==========================================
# 📅 기준 날짜 설정 (🌟 무조건 한국 시간 기준 🌟)
# ==========================================
KST = timezone(timedelta(hours=9))
now_kst = datetime.now(KST)
yesterday_dt = now_kst - timedelta(days=1)
yesterday_dot = yesterday_dt.strftime("%Y.%m.%d")

print(f"--- 🎯 타겟 날짜(어제, 한국시간 기준): {yesterday_dot} ---")

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

impact_news_data = []
macro_categories = {
    "경제지표": [],
    "통화정책": [],
    "관세": [],
    "외교": []
}
seen_links = set()

# ==========================================
# 1. 🌱 임팩트온 스크랩 섹션 
# ==========================================
print("\n🌱 1. 임팩트온 뉴스 스크랩 시작...")
try:
    impact_url = "https://www.impacton.net/news/articleList.html"
    response = requests.get(impact_url, headers=headers, timeout=15)
    soup = BeautifulSoup(response.text, 'html.parser')
    article_tags = soup.select("a[href*='articleView.html']")
    
    count = 0
    for tag in article_tags:
        if count >= 5: break
        title = tag.text.strip()
        if not title or len(title) < 4: continue
        
        href = tag.get("href", "")
        if not href: continue
        link = href if href.startswith("http") else "https://www.impacton.net" + href
        if link in seen_links: continue
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
            
            if article_date == yesterday_dot:
                seen_links.add(link)
                print(f"✅ 임팩트온 수집: {title}")
                impact_news_data.append({"title": title, "link": link, "date": f"{article_date}"})
                count += 1
            time.sleep(0.5)
        except Exception:
            pass
except Exception as e:
    print(f"⚠️ 임팩트온 에러: {e}")


# ==========================================
# 2. 🎯 구글 뉴스 4대 카테고리 스크랩 (전체 대상)
# ==========================================
print("\n🎯 2. 구글 뉴스 미국 거시경제 카테고리 스크랩 시작...")

# 🌟 RSS가 더 잘 알아듣도록 키워드 조합을 직관적으로 풀었습니다.
search_queries = {
    "경제지표": "미국 경제지표 OR 미국 GDP OR 미국 고용 OR 미국 물가",
    "통화정책": "미국 통화정책 OR 미국 연준 OR 미국 금리 OR 파월",
    "관세": "미국 관세 OR 미국 무역대표부 OR USTR",
    "외교": "미국 외교 OR 미국 제재 OR 바이든 OR 트럼프"
}

for cat_name, query in search_queries.items():
    print(f"🔍 [{cat_name}] 검색 중...")
    try:
        encoded_query = urllib.parse.quote(query)
        # 🌟 핵심 수정: when:1d -> when:2d 로 변경하여 누락되는 어제 기사가 없게 투망을 넓혔습니다.
        rss_url = f"https://news.google.com/rss/search?q={encoded_query}%20when%3A2d&hl=ko&gl=KR&ceid=KR%3Ako"
        
        res = requests.get(rss_url, headers=headers, timeout=15)
        soup = BeautifulSoup(res.text, 'html.parser')
        items = soup.find_all("item")
        
        for item in items:
            if len(macro_categories[cat_name]) >= 2: 
                break
                
            title_text = item.title.text.strip() if item.title else ""
            link = item.link.text.strip() if item.link else ""
            pub_date_str = item.pubdate.text.strip() if item.pubdate else ""
            
            if not title_text or not link or link in seen_links: continue
            
            try:
                pub_dt = parsedate_to_datetime(pub_date_str).astimezone(KST)
                pub_date_dot = pub_dt.strftime("%Y.%m.%d")
                
                # 어제 날짜가 아니면 (오늘이거나 그저께면) 버립니다!
                if pub_date_dot != yesterday_dot:
                    continue
            except Exception:
                continue
                
            publisher = "구글 뉴스"
            if " - " in title_text:
                parts = title_text.rsplit(" - ", 1)
                title_text = parts[0]
                publisher = parts[1]

            seen_links.add(link)
            print(f"✅ [{cat_name}] 수집 완료!")
            macro_categories[cat_name].append({
                "title": title_text,
                "link": link,
                "source": publisher
            })
            
    except Exception as e:
        print(f"⚠️ [{cat_name}] 스크랩 에러: {e}")


# ==========================================
# 3. 🌐 통합 웹페이지(HTML) 생성
# ==========================================
print("\n--- 🌐 통합 웹페이지(HTML) 생성 시작 ---")

html_content = f"""
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <title>📰 오늘의 종합 비즈니스 & 거시경제 브리핑</title>
    <style>
        body {{ font-family: 'Malgun Gothic', sans-serif; max-width: 900px; margin: auto; padding: 20px; background-color: #f4f7f6; }}
        h1 {{ color: #2c3e50; text-align: center; margin-bottom: 5px; }}
        .date-title {{ text-align: center; color: #7f8c8d; margin-bottom: 40px; font-size: 1.1em; }}
        .section-title {{ font-size: 1.6em; color: #2c3e50; border-left: 6px solid #2ecc71; padding-left: 12px; margin-top: 40px; margin-bottom: 20px; font-weight: bold; }}
        .section-title.macro {{ border-left-color: #e74c3c; }}
        .sub-category {{ font-size: 1.2em; color: #34495e; margin: 20px 0 10px 5px; font-weight: bold; background: #e8ecef; padding: 5px 10px; border-radius: 4px; display: inline-block; }}
        .news-card {{ background: white; padding: 20px; margin-bottom: 12px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }}
        .news-title {{ font-size: 1.1em; font-weight: bold; margin-bottom: 8px; line-height: 1.4; }}
        .news-title a {{ color: #333; text-decoration: none; }}
        .news-title a:hover {{ color: #2980b9; text-decoration: underline; }}
        .news-date {{ font-size: 0.85em; color: #95a5a6; }}
        .no-news {{ color: #95a5a6; font-style: italic; padding: 10px 20px; }}
    </style>
</head>
<body>
    <h1>📋 오늘의 종합 뉴스 브리핑</h1>
    <div class="date-title">자동 업데이트 기준일: {yesterday_dot} (전일 기사)</div>

    <div class="section-title">🌱 오늘의 임팩트 비즈니스 뉴스 (국내)</div>
"""

if not impact_news_data:
    html_content += f"<div class='no-news'>{yesterday_dot} 자에 발행된 임팩트온 뉴스가 없습니다.</div>"
else:
    for news in impact_news_data:
        html_content += f"""
        <div class="news-card">
            <div class="news-title"><a href="{news['link']}" target="_blank">{news['title']}</a></div>
            <div class="news-date">발행일: {news['date']} (임팩트온)</div>
        </div>
        """

html_content += """
    <div class="section-title macro">🇺🇸 오늘의 미국 거시경제 브리핑 (글로벌)</div>
"""

for cat_name, news_list in macro_categories.items():
    html_content += f"<div class='sub-category'>📌 {cat_name}</div>"
    if not news_list:
        html_content += f"<div class='no-news'>{yesterday_dot} 자 뉴스가 없습니다.</div>"
    else:
        for news in news_list:
            html_content += f"""
            <div class="news-card">
                <div class="news-title"><a href="{news['link']}" target="_blank">{news['title']}</a></div>
                <div class="news-date">출처: {news['source']} (발행: {yesterday_dot})</div>
            </div>
            """
        
html_content += "</body></html>"

with open("index.html", "w", encoding="utf-8") as f:
    f.write(html_content)

print("🎉 시간 오류 해결! 통합 index.html 파일 생성이 끝났습니다.")
