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

# 블룸버그/USTR 등 영문 날짜 포맷 대응 (예: May 27)
month_map = {
    1: "Jan", 2: "Feb", 3: "Mar", 4: "Apr", 5: "May", 6: "Jun",
    7: "Jul", 8: "Aug", 9: "Sep", 10: "Oct", 11: "Nov", 12: "Dec"
}
yesterday_en_short = f"{month_map[target_dt.month]} {target_dt.day}"

print(f"--- 🎯 타겟 날짜(어제): {yesterday_dot} ({yesterday_en_short}) ---")

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8"
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
# 1. 🌱 임팩트온 스크랩 섹션 (기존 성공 로직)
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
            
            # 어제 날짜 기사만 수집
            if article_date == yesterday_dot:
                print(f"✅ 임팩트온 수집 완료: {title}")
                impact_news_data.append({"title": title, "link": link, "date": f"{article_date}"})
                count += 1
            time.sleep(0.5)
        except Exception as e:
            pass
except Exception as e:
    print(f"❌ 임팩트온 메인 페이지 접속 실패: {e}")


# ==========================================
# 2. 🎯 미국 거시경제 스크랩 섹션 (🌟 어제 날짜 필터링 강화)
# ==========================================
print("\n🎯 2. 미국 거시경제 카테고리별 스크랩 시작...")

# --- 2-A. USTR (미국 무역대표부) ---
print("🔍 USTR 보도자료 분석 중...")
try:
    ustr_url = "https://ustr.gov/about-us/policy-offices/press-office/press-releases"
    res = requests.get(ustr_url, headers=headers, timeout=15)
    soup = BeautifulSoup(res.text, 'html.parser')
    
    items = soup.select(".views-row")
    for item in items:
        title_tag = item.select_one("a")
        date_tag = item.select_one(".date-display-single, .post-date, .views-field-created")
        
        if not title_tag: continue
        title_en = title_tag.text.strip()
        link = "https://ustr.gov" + title_tag["href"] if not title_tag["href"].startswith("http") else title_tag["href"]
        
        # 🌟 날짜 검사 로직 추가 (USTR)
        item_date_text = date_tag.text.strip() if date_tag else ""
        # 웹페이지에 표시된 날짜가 어제 날짜 문구(예: May 27)를 포함하는지 검사
        if yesterday_en_short not in item_date_text and yesterday_dash not in item_date_text:
            continue  # 어제 기사가 아니면 패스!
            
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
    pass

# --- 2-B. 블룸버그 Politics ---
print("🔍 블룸버그 경제/정치 피드 분석 중...")
try:
    bb_url = "https://www.bloomberg.com/politics"
    res = requests.get(bb_url, headers=headers, timeout=15)
    soup = BeautifulSoup(res.text, 'html.parser')
    
    story_tags = soup.find_all("a", href=True)
    for tag in story_tags:
        href = tag["href"]
        title_text = tag.text.strip()
        
        if "/news/articles/" not in href or len(title_text) < 15: continue
        link = href if href.startswith("http") else "https://www.bloomberg.com" + href
        if link in seen_links: continue
        
        # 🌟 날짜 검사 로직 추가 (블룸버그)
        # 블룸버그 기사 주소창 구조에 포함된 날짜 패턴 분석 (예: /news/articles/2026-05-27/...)
        if yesterday_dash not in href:
            continue  # 주소에 어제 날짜(YYYY-MM-DD)가 적혀있지 않다면 최신 기사가 아니므로 패스!
            
        title_lower = title_text.lower()
        category_assigned = None
        
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
    pass


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
        .sub-category {{ font-size: 1.2em; color: #34495e; margin: 20px 0 10px 5px; font-weight: bold; background: #e8ecef; padding: 5px 10px; border-radius: 4
