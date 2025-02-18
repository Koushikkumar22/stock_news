import requests

NEWS_API_KEY = "3ddc268bab2c4aebb6806633e8312ac0"

def get_stock_news(stock_symbol):
    url = f"https://newsapi.org/v2/everything?q={stock_symbol}&apiKey={NEWS_API_KEY}"
    response = requests.get(url)
    data = response.json()

    articles = data.get("articles", [])
    news_list = []
    
    for article in articles[:5]:  # Get top 5 news
        title = article["title"]
        url = article["url"]
        news_list.append(f"{title}\n{url}")
    
    return news_list
