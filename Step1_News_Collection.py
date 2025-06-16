import feedparser
from datetime import datetime
from common_utils import get_gsheet, client

# 카테고리별 구글 뉴스 RSS 주소 (국내/글로벌)
RSS_FEEDS = {
    "국내_경제": "https://news.google.com/rss/search?q=경제&hl=ko&gl=KR&ceid=KR:ko",
    "국내_IT": "https://news.google.com/rss/search?q=IT&hl=ko&gl=KR&ceid=KR:ko",
    "국내_정치": "https://news.google.com/rss/search?q=정치&hl=ko&gl=KR&ceid=KR:ko",
    "국내_과학": "https://news.google.com/rss/search?q=과학&hl=ko&gl=KR&ceid=KR:ko",
    "국내_건강": "https://news.google.com/rss/search?q=건강&hl=ko&gl=KR&ceid=KR:ko",
    "국내_스포츠": "https://news.google.com/rss/search?q=스포츠&hl=ko&gl=KR&ceid=KR:ko",
    "국내_트렌드": "https://news.google.com/rss?hl=ko&gl=KR&ceid=KR:ko",
    "글로벌_경제": "https://news.google.com/rss/search?q=세계+경제&hl=ko&gl=KR&ceid=KR:ko",
    "글로벌_IT": "https://news.google.com/rss/search?q=글로벌+IT&hl=ko&gl=KR&ceid=KR:ko",
    "글로벌_정치": "https://news.google.com/rss/search?q=국제+정치&hl=ko&gl=KR&ceid=KR:ko",
    "글로벌_과학": "https://news.google.com/rss/search?q=국제+과학&hl=ko&gl=KR&ceid=KR:ko",
    "글로벌_건강": "https://news.google.com/rss/search?q=국제+건강&hl=ko&gl=KR&ceid=KR:ko",
    "글로벌_스포츠": "https://news.google.com/rss/search?q=국제+스포츠&hl=ko&gl=KR&ceid=KR:ko",
    "글로벌_트렌드": "https://news.google.com/rss/search?q=글로벌+트렌드&hl=ko&gl=KR&ceid=KR:ko",
}

SHEET_NAME = 'morning_news'

def summarize_for_cardnews(news_text):
    prompt = f"""
아래 뉴스 내용을 카드뉴스에 들어갈 수 있도록
2~3줄, 각 줄 15~25자 이내로 아주 간결하게 요약해줘.

뉴스:
{news_text}
"""
    response = client.chat.completions.create(
        model="gpt-4o-2024-05-13",
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content.strip()

def fetch_news(rss_url, category, max_count=10):
    print(f"  - [{category}] 카테고리 뉴스 수집 및 요약 중...")
    feed = feedparser.parse(rss_url)
    news_list = []
    for entry in feed.entries[:max_count]:
        title = entry.title
        summary = entry.summary if hasattr(entry, 'summary') else ''
        published = entry.published if hasattr(entry, 'published') else datetime.now().strftime('%Y-%m-%d %H:%M')
        url = entry.link if hasattr(entry, 'link') else ''
        # 카드뉴스용 요약 생성
        if summary and len(summary) <= 60:
            cardnews_summary = summary
        else:
            cardnews_summary = summarize_for_cardnews(title)
        news_list.append([
            title,  # title
            cardnews_summary,  # card_summary
            published,  # date
            url,  # source_url
            summary,  # original_html
            category  # category
        ])
    return news_list

def save_to_gsheet(news_rows):
    sheet = get_gsheet(SHEET_NAME)
    # 기존 데이터(2행 이하) 모두 삭제
    if sheet.row_count > 1:
        sheet.delete_rows(2, sheet.row_count)
    # 헤더가 없으면 추가
    if sheet.row_count < 1 or sheet.row_values(1) != ['title', 'card_summary', 'date', 'source_url', 'original_html', 'category']:
        sheet.insert_row(['title', 'card_summary', 'date', 'source_url', 'original_html', 'category'], 1)
    for row in news_rows:
        sheet.append_row(row)

if __name__ == "__main__":
    print("[1/4] 국내/글로벌 뉴스 수집 시작...")
    domestic_news = []
    global_news = []
    for cat, url in RSS_FEEDS.items():
        news = fetch_news(url, cat, max_count=10)
        if cat.startswith("국내_"):
            domestic_news.extend(news)
        else:
            global_news.extend(news)
    print("[2/4] 뉴스 카테고리 분류 및 중요도/키워드 선별 중...")
    domestic_news = domestic_news[:30]
    global_news = global_news[:20]
    all_news = domestic_news + global_news
    print("[3/4] 구글시트 저장 중...")
    save_to_gsheet(all_news)
    print(f"[4/4] 국내 {len(domestic_news)}건, 글로벌 {len(global_news)}건, 총 {len(all_news)}건의 뉴스가 구글시트에 저장되었습니다.") 