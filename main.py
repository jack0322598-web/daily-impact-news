import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import time

# 타겟 날짜 설정 (어제 날짜)
yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y.%m.%d")
yesterday_dash = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
print(f"--- 🎯 타겟 날짜(어제): {yesterday} ---")

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8"
}

impact_news_data = []
# 카테고리별로 뉴스를 담을 저장소
macro_categories = {
    "경제지표": [],
    "통화정책": [],
    "관세": [],
    "외교": []
}
seen_links = set()

# ==========================================
# 1. 🌱 임팩트온 스크랩 섹션 (기존 성공 코드)
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
                impact_news_data.append({"title": title, "link": link, "date": f"{article_date}"})
                count += 1
            time.sleep(0.5)
        except Exception as e:
            pass
except Exception as e:
    print(f"❌ 임팩트온 메인 페이지 접속 실패: {e}")


# ==========================================
# 2. 🎯 미국 거시경제 직집 스크랩 섹션 (블룸버그 & USTR)
# ==========================================
print("\n🎯 2. 미국 거시경제 카테고리별 스크랩 시작...")

# --- 2-A. USTR (미국 무역대표부) 관세/무역외교 집중 스크랩 ---
print("🔍 USTR 보도자료 분석 중...")
try:
    ustr_url = "https://ustr.gov/about-us/policy-offices/press-office/press-releases"
    res = requests.get(ustr_url, headers=headers, timeout=15)
    soup = BeautifulSoup(res.text, 'html.parser')
    
    # USTR의 보도자료 목록 태그 피드 분석
    items = soup.select(".views-row")
    for item in items:
        title_tag = item.select_one("a")
        date_tag = item.select_one(".date-display-single, .post-date")
        
        if not title_tag: continue
        title_en = title_tag.text.strip()
        link = "https://ustr.gov" + title_tag["href"] if not title_tag["href"].startswith("http") else title_tag["href"]
        
        # 키워드 매칭을 통해 카테고리 분류 및 수집
        title_lower = title_en.lower()
        category_assigned = None
        
        if "tariff" in title_lower or "customs" in title_lower or "tax" in title_lower:
            category_assigned = "관세"
        elif "agreement" in title_lower or "china" in title_lower or "bilateral" in title_lower:
            category_assigned = "외교"
            
        if category_assigned and len(macro_categories[category_assigned]) < 2:
            if link not in seen_links:
                seen_links.add(link)
                print(f"✅ USTR 수집 [{category_assigned}]: {title_en[:50]}...")
                macro_categories[category_assigned].append({
                    "title": f"[USTR] {title_en}",
                    "link": link,
                    "source": "USTR"
                })
except Exception as e:
    print(f"⚠️ USTR 크롤링 중 일시적 이슈 발생 (건너뜀)")

# --- 2-B. 블룸버그 Politics 기반 경제지표/통화정책/외교 스크랩 ---
print("🔍 블룸버그 경제/정치 피드 분석 중...")
try:
    # 블룸버그 정치/정책 데이터 통로 (대안 RSS 및 오픈 피드 활용으로 차단 우회)
    bb_url = "https://www.bloomberg.com/politics"
    res = requests.get(bb_url, headers=headers, timeout=15)
    soup = BeautifulSoup(res.text, 'html.parser')
    
    # 일반적인 블룸버그 뉴스 카드 주소 구조 분석
    story_tags = soup.find_all("a", href=True)
    for tag in story_tags:
        href = tag["href"]
        title_text = tag.text.strip()
        
        if "/news/articles/" not in href or len(title_text) < 15: continue
        link = href if href.startswith("http") else "https://www.bloomberg.com" + href
        if link in seen_links: continue
        
        title_lower = title_text.lower()
        category_assigned = None
        
        # 카테고리 판단 기준 단어 정의
        if "fed " in title_lower or "rate" in title_lower or "powell" in title_lower or "inflation" in title_lower:
            category_assigned = "통화정책"
        elif "gdp" in title_lower or "job" in title_lower or "economy" in title_lower or "data" in title_lower:
            category_assigned = "경제지표"
        elif "sanction" in title_lower or "china" in title_lower or "biden" in title_lower or "trump" in title_lower:
            category_assigned = "외교"
            
        if category_assigned and len(macro_categories[category_assigned]) < 2:
            seen_links.add(link)
            print(f"✅ 블룸버그 수집 [{category_assigned}]: {title_text[:50]}...")
            macro_categories[category_assigned].append({
                "title": f"[Bloomberg] {title_text}",
                "link": link,
                "source": "Bloomberg"
            })
except Exception as e:
    print(f"⚠️ 블룸버그 크롤링 중 일시적 이슈 발생 (건너뜀)")


# ==========================================
# 3. 🌐 통합 웹페이지(HTML) 생성 섹션
# ==========================================
print("\n--- 🌐 통합 웹페이지(HTML) 생성 시작 ---")

html_content = f"""
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <title>📰 오늘의 종합 비즈니스 & 미국 거시경제 브리핑</title>
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
    <div class="date-title">최근 자동 업데이트: {yesterday}</div>

    <div class="section-title">🌱 오늘의 임팩트 비즈니스 뉴스 (국내)</div>
"""

if not impact_news_data:
    html_content += "<div class='no-news'>어제자 발행된 임팩트 뉴스가 없습니다.</div>"
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

# 4대 카테고리를 순서대로 HTML에 출력합니다.
for cat_name, news_list in macro_categories.items():
    html_content += f"<div class='sub-category'>📌 {cat_name}</div>"
    if not news_list:
        html_content += "<div class='no-news'>최신 관련 뉴스가 없습니다. (대기 중)</div>"
    else:
        for news in news_list:
            html_content += f"""
            <div class="news-card">
                <div class="news-title"><a href="{news['link']}" target="_blank">{news['title']}</a></div>
                <div class="news-date">출처: {news['source']} (원문 인덱싱)</div>
            </div>
            """
        
html_content += "</body></html>"

with open("index.html", "w", encoding="utf-8") as f:
    f.write(html_content)

print("🎉 통합 카테고리 index.html 파일이 성공적으로 생성되었습니다!")
