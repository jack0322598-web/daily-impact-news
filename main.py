import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import time

# ==========================================
# 📅 기준 날짜 설정 (한국 시간 기준 어제)
# ==========================================
target_dt = datetime.now() - timedelta(days=1)
yesterday_dot = target_dt.strftime("%Y.%m.%d")
yesterday_dash = target_dt.strftime("%Y-%m-%d")

# 블룸버그/USTR 등 영문 날짜 포맷 대응 (예: May 27 또는 27 May)
month_map = {
    1: "Jan", 2: "Feb", 3: "Mar", 4: "Apr", 5: "May", 6: "Jun",
    7: "Jul", 8: "Aug", 9: "Sep", 10: "Oct", 11: "Nov", 12: "Dec"
}
yesterday_en_short = f"{month_map[target_dt.month]} {target_dt.day}"

print(f"--- 🎯 타겟 날짜(어제): {yesterday_dot} ({yesterday_en_short}) ---")

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
# 1. 🌱 임팩트온 스크랩 섹션 (검증 완료)
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
            
            if article_date == yesterday_dot:
                print(f"✅ 임팩트온 수집 완료: {title}")
                impact_news_data.append({"title": title, "link": link, "date": f"{article_date}"})
                count += 1
            time.sleep(0.3)
        except Exception:
            pass
except Exception as e:
    print(f"⚠️ 임팩트온 메인 페이지 일시 오류: {e}")


# ==========================================
# 2. 🎯 미국 거시경제 스크랩 섹션 (공식 RSS/XML 돌파 방식)
# ==========================================
print("\n🎯 2. 미국 거시경제 카테고리별 스크랩 시작...")

# --- 2-A. USTR (미국 무역대표부) 공식 뉴스 피드 ---
print("🔍 USTR 보도자료 분석 중...")
try
