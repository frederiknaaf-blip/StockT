"""
Aktien-App mit News-Feed und Fundamentalanalyse
Optimierte Version mit robustem News-Filter
"""

import streamlit as st
import requests
from datetime import datetime
ODER - Schneller Trick:
Füge ganz oben nach Zeile 8 diese eine Zeile ein:
import streamlit as st
import requests
from datetime import datetime

st.cache_data.clear()

# ==================== KONFIGURATION ====================
API_TOKEN = "692c1c76752bd1.25047072"  # Dein API-Key
BASE_URL = "https://eodhd.com/api"
USER_NAME = "Thomas"

# Robuste Quellen-Erkennung (findet auch bloomberg.com, wsj.com etc.)
PREMIUM_SOURCES = {
    'bloomberg': ['bloomberg'],
    'reuters': ['reuters'],
    'cnbc': ['cnbc'],
    'wsj': ['wsj', 'wall street journal', 'wallstreet'],
    'ft': ['financial times', 'ft.com'],
    'marketwatch': ['marketwatch'],
    'barrons': ['barron', 'barrons'],
    'benzinga': ['benzinga'],
    'seekingalpha': ['seeking alpha', 'seekingalpha'],
    'thestreet': ['thestreet'],
    'yahoo': ['yahoo finance', 'yahoo'],
    'businessinsider': ['business insider', 'businessinsider'],
    'forbes': ['forbes']
}

# ==================== PAGE CONFIG ====================
st.set_page_config(
    page_title="Aktien Analyzer",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ==================== CUSTOM CSS ====================
st.markdown("""
<style>
    .main-header {
        font-size: 3em;
        font-weight: 800;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 20px;
    }
    .news-card {
        background: white;
        border-radius: 16px;
        padding: 24px;
        margin: 20px 0;
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        border-left: 6px solid;
        cursor: pointer;
        transition: all 0.3s ease;
    }
    .news-card:hover {
        transform: translateY(-4px);
        box-shadow: 0 8px 24px rgba(0,0,0,0.15);
    }
    .news-card.positive { 
        border-left-color: #10b981;
        background: linear-gradient(135deg, #fff 0%, #ecfdf5 100%);
    }
    .news-card.negative { 
        border-left-color: #ef4444;
        background: linear-gradient(135deg, #fff 0%, #fef2f2 100%);
    }
    .ticker-badge {
        display: inline-block;
        background: #667eea;
        color: white;
        padding: 8px 16px;
        border-radius: 20px;
        font-size: 1.1em;
        font-weight: 700;
        margin-bottom: 12px;
        cursor: pointer;
    }
    .ticker-badge:hover {
        background: #5568d3;
        transform: scale(1.05);
    }
    .news-source {
        font-size: 0.9em;
        color: #64748b;
        font-weight: 600;
        margin-bottom: 12px;
    }
    .news-summary {
        font-size: 1.05em;
        color: #1e293b;
        line-height: 1.7;
        margin: 15px 0;
    }
    .sentiment-badge {
        display: inline-block;
        padding: 6px 14px;
        border-radius: 12px;
        font-size: 0.9em;
        font-weight: 600;
        margin: 10px 0;
    }
    .sentiment-badge.positive {
        background: #dcfce7;
        color: #166534;
    }
    .sentiment-badge.negative {
        background: #fee2e2;
        color: #991b1b;
    }
    .article-link {
        display: inline-block;
        color: #667eea;
        text-decoration: none;
        font-weight: 600;
        font-size: 0.95em;
        margin-top: 12px;
        padding: 8px 16px;
        border: 2px solid #667eea;
        border-radius: 8px;
        transition: all 0.2s;
    }
    .article-link:hover {
        background: #667eea;
        color: white;
        transform: translateX(4px);
    }
    .metric-card {
        background: white;
        border-radius: 16px;
        padding: 20px;
        margin: 10px 0;
        box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        border: 2px solid;
    }
    .metric-card.red { border-color: #fca5a5; background: linear-gradient(135deg, #fff 0%, #ffe0e0 100%); }
    .metric-card.yellow { border-color: #fcd34d; background: linear-gradient(135deg, #fff 0%, #fff9e0 100%); }
    .metric-card.green { border-color: #86efac; background: linear-gradient(135deg, #fff 0%, #e0ffe6 100%); }
    .rating-box {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 20px;
        padding: 30px;
        text-align: center;
        color: white;
        margin: 20px 0;
    }
    .rating-score {
        font-size: 4em;
        font-weight: 800;
        margin: 15px 0;
    }
</style>
""", unsafe_allow_html=True)

# ==================== HILFSFUNKTIONEN ====================

def is_premium_source(article):
    """Prüft ob Artikel von Premium-Quelle stammt (robust)"""
    # Prüfe source, link und tags
    source = article.get('source', '').lower()
    link = article.get('link', '').lower()
    tags = ' '.join(article.get('tags', [])).lower()
    
    search_text = f"{source} {link} {tags}"
    
    # Prüfe gegen alle Premium-Quellen
    for source_name, keywords in PREMIUM_SOURCES.items():
        for keyword in keywords:
            if keyword in search_text:
                return True, source_name.capitalize()
    
    return False, None

def fetch_news(limit=100):
    """Holt aktuelle News mit robustem Premium-Filter"""
    try:
        url = f"{BASE_URL}/news"
        params = {"api_token": API_TOKEN, "limit": limit, "offset": 0}
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        all_news = response.json()
        
        # Filter 1: Premium-Quellen
        premium_news = []
        for news in all_news:
            is_premium, source_name = is_premium_source(news)
            if is_premium:
                news['detected_source'] = source_name  # Speichere erkannte Quelle
                premium_news.append(news)
        
        # Filter 2: Nur News mit klarem Sentiment
        filtered_news = []
        for news in premium_news:
            title = news.get('title', '')
            content = news.get('content', '')
            sentiment, _, _ = analyze_news_sentiment(title, content)
            
            if sentiment:  # Nur positive oder negative News
                filtered_news.append(news)
        
        return filtered_news[:20]  # Top 20 relevante Premium-News
        
    except Exception as e:
        st.error(f"Fehler beim Laden der News: {e}")
        return []

def get_company_name(ticker):
    """Holt Firmenname für Ticker"""
    try:
        ticker_clean = ticker.strip().upper()
        if '.' not in ticker_clean:
            ticker_clean = f"{ticker_clean}.US"
        
        url = f"{BASE_URL}/fundamentals/{ticker_clean}"
        params = {"api_token": API_TOKEN, "fmt": "json"}
        response = requests.get(url, params=params, timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            return data.get('General', {}).get('Name', ticker)
    except:
        pass
    return ticker

def analyze_news_sentiment(title, content=""):
    """Analysiert News-Sentiment und gibt Begründung"""
    text = (title + " " + content).lower()
    
    strong_positive = ['beats expectations', 'soars', 'record high', 'surges', 'skyrockets', 
                      'strong growth', 'upgraded', 'breakthrough', 'exceeds', 'stellar']
    positive = ['gains', 'rises', 'bullish', 'profit', 'success', 'positive', 'rally', 
               'upbeat', 'optimistic', 'buy']
    
    strong_negative = ['plunges', 'crashes', 'collapses', 'plummets', 'warning', 'crisis',
                      'downgraded', 'miss badly', 'disaster', 'fails']
    negative = ['falls', 'drops', 'bearish', 'loss', 'decline', 'concern', 'weak', 
               'disappoints', 'struggles', 'down']
    
    strong_pos_count = sum(1 for word in strong_positive if word in text)
    pos_count = sum(1 for word in positive if word in text)
    strong_neg_count = sum(1 for word in strong_negative if word in text)
    neg_count = sum(1 for word in negative if word in text)
    
    total_positive = strong_pos_count * 2 + pos_count
    total_negative = strong_neg_count * 2 + neg_count
    
    if total_positive > total_negative + 1:
        reason = "Positive Signale: "
        if strong_pos_count > 0:
            reason += "Übertrifft Erwartungen oder zeigt starkes Wachstum. "
        else:
            reason += "Gute Nachrichten für das Unternehmen. "
        return 'positive', '🟢', reason
    elif total_negative > total_positive + 1:
        reason = "Negative Signale: "
        if strong_neg_count > 0:
            reason += "Deutliche Rückgänge oder Warnungen erkennbar. "
        else:
            reason += "Herausforderungen oder Schwächen zeigen sich. "
        return 'negative', '🔴', reason
    else:
        return None, None, None

def create_summary(title, content, company_name):
    """Erstellt kurze Zusammenfassung mit Firmenname"""
    if content and len(content) > 50:
        summary = content.split('.')[0] + '.'
        if len(summary) > 200:
            summary = summary[:200] + '...'
    else:
        summary = title
    
    if company_name.lower() not in summary.lower():
        summary = f"{company_name}: {summary}"
    
    return summary

def fetch_fundamentals(ticker):
    """Holt Fundamentaldaten"""
    try:
        ticker = ticker.strip().upper()
        if '.' not in ticker:
            ticker = f"{ticker}.US"
        
        url = f"{BASE_URL}/fundamentals/{ticker}"
        params = {"api_token": API_TOKEN, "fmt": "json"}
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.error(f"Fehler: {e}")
        return None

def classify_metric(metric_name, value):
    """Klassifiziert Kennzahl"""
    if value is None:
        return 'red', 'Wert nicht verfügbar'
    
    try:
        val = float(value)
    except:
        return 'red', 'Ungültiger Wert'
    
    classifications = {
        'P/E Ratio': [
            (lambda v: v > 30, 'red', 'Sehr hoch (>30). Überbewertet.'),
            (lambda v: v >= 15, 'yellow', 'Normal (15-30). Fair.'),
            (lambda v: v > 0, 'green', 'Niedrig (<15). Unterbewertet.'),
        ],
        'ROE': [
            (lambda v: v >= 15, 'green', 'Sehr gut (>15%). Effizient.'),
            (lambda v: v >= 5, 'yellow', 'Moderat (5-15%). Solide.'),
            (lambda v: True, 'red', 'Gering (<5%). Ineffizient.')
        ],
        'Debt/Equity': [
            (lambda v: v > 1.5, 'red', 'Hoch (>1.5). Risiko.'),
            (lambda v: v > 0.5, 'yellow', 'Moderat (0.5-1.5).'),
            (lambda v: v >= 0, 'green', 'Gering (<0.5). Solide.')
        ],
    }
    
    if metric_name in classifications:
        for condition, color, explanation in classifications[metric_name]:
            if condition(val):
                return color, explanation
    
    return 'yellow', 'Keine Bewertung'

def calculate_rating(data):
    """Berechnet Rating 1-10"""
    if not data or 'Highlights' not in data:
        return 5.0, "Unzureichende Daten"
    
    highlights = data.get('Highlights', {})
    score = 0
    weights = 0
    
    pe = highlights.get('PERatio')
    if pe and pe > 0:
        if pe < 15: score += 9 * 1.5
        elif pe <= 25: score += 6 * 1.5
        else: score += 3 * 1.5
        weights += 1.5
    
    roe = highlights.get('ReturnOnEquityTTM')
    if roe:
        roe_pct = roe * 100
        if roe_pct >= 15: score += 9 * 2.0
        elif roe_pct >= 5: score += 5 * 2.0
        else: score += 2 * 2.0
        weights += 2.0
    
    if weights == 0:
        return 5.0, "Nicht genug Daten"
    
    final = score / weights
    
    if final >= 8:
        return final, "🚀 Exzellent! Starke Fundamentals."
    elif final >= 6:
        return final, "✅ Gut. Solide Kennzahlen."
    elif final >= 4:
        return final, "⚖️ Durchschnittlich."
    else:
        return final, "⚠️ Schwach. Vorsicht."

def get_stars(rating):
    """Sterne für Rating"""
    full = int(rating)
    half = 1 if (rating - full) >= 0.5 else 0
    empty = 10 - full - half
    return "⭐" * full + ("✨" if half else "") + "☆" * empty

# ==================== SESSION STATE ====================
if 'view' not in st.session_state:
    st.session_state.view = 'news'
if 'selected_ticker' not in st.session_state:
    st.session_state.selected_ticker = None

# ==================== NEWS VIEW ====================
def show_news_view():
    st.markdown(f'<h1 class="main-header">👋 Hallo {USER_NAME}</h1>', unsafe_allow_html=True)
    st.markdown("### 📰 Premium News (Bloomberg, Reuters, WSJ & mehr)")
    
    with st.spinner('Lade Premium-News...'):
        news_data = fetch_news()
    
    if not news_data:
        st.warning("⚠️ Aktuell keine relevanten Premium-News verfügbar")
        st.info("💡 Tipp: Die App zeigt nur News von Top-Quellen mit klaren Trading-Signalen")
        return
    
    st.success(f"✅ {len(news_data)} relevante Premium-Artikel gefunden")
    
    for article in news_data:
        title = article.get('title', 'Kein Titel')
        content = article.get('content', '')
        symbols = article.get('symbols', '')
        
        # FIX: Symbols kann Liste oder String sein
        if isinstance(symbols, list):
            ticker = symbols[0] if symbols else None
        elif isinstance(symbols, str):
            ticker = symbols.split(',')[0] if symbols else None
        else:
            ticker = None
        
        source = article.get('detected_source', article.get('source', 'Premium Source'))
        date = article.get('date', '')
        link = article.get('link', '#')
        
        if not ticker:
            continue
        
        sentiment, emoji, reason = analyze_news_sentiment(title, content)
        
        if not sentiment:
            continue
        
        company_name = get_company_name(ticker)
        summary = create_summary(title, content, company_name)
        
        st.markdown(f"""
        <div class="news-card {sentiment}">
            <span class="ticker-badge" onclick="location.reload()">{ticker}</span>
            <div class="news-source">🏆 {source} • {date[:10]}</div>
            <div class="news-summary">{summary}</div>
            <div class="sentiment-badge {sentiment}">{emoji} {reason}</div>
            <br>
            <a href="{link}" target="_blank" class="article-link">→ Zum Artikel</a>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button(f"📊 Analysiere {ticker}", key=f"btn_{ticker}_{date}"):
            st.session_state.selected_ticker = ticker
            st.session_state.view = 'analysis'
            st.rerun()

# ==================== ANALYSIS VIEW ====================
def show_analysis_view():
    ticker = st.session_state.selected_ticker
    
    if st.button("← Zurück zu News"):
        st.session_state.view = 'news'
        st.rerun()
    
    st.markdown(f'<h1 class="main-header">📊 Analyse: {ticker}</h1>', unsafe_allow_html=True)
    
    with st.spinner(f'Lade Daten...'):
        data = fetch_fundamentals(ticker)
    
    if not data or 'General' not in data:
        st.error(f"Keine Daten für {ticker}")
        return
    
    general = data.get('General', {})
    highlights = data.get('Highlights', {})
    valuation = data.get('Valuation', {})
    
    st.markdown(f"""
    <div style="text-align: center; background: linear-gradient(135deg, #ec4899 0%, #f43f5e 100%); 
                color: white; padding: 25px; border-radius: 16px; margin-bottom: 25px;">
        <h2 style="margin: 0; font-size: 2em; font-weight: 800;">{general.get('Name', 'N/A')}</h2>
        <div style="font-size: 1.1em; margin-top: 10px;">
            {general.get('Code', 'N/A')} • {general.get('Sector', 'N/A')}
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    rating, explanation = calculate_rating(data)
    stars = get_stars(rating)
    
    st.markdown(f"""
    <div class="rating-box">
        <div style="font-size: 1.2em; font-weight: 600;">GESAMT-RATING</div>
        <div class="rating-score">{rating:.1f}/10</div>
        <div style="font-size: 2em;">{stars}</div>
        <div style="font-size: 1.1em; margin-top: 15px;">{explanation}</div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("### 💰 Kennzahlen")
    
    metrics = {
        'P/E Ratio': highlights.get('PERatio'),
        'ROE': highlights.get('ReturnOnEquityTTM', 0) * 100 if highlights.get('ReturnOnEquityTTM') else None,
        'Debt/Equity': highlights.get('DebtEquityMRQ'),
    }
    
    cols = st.columns(3)
    for idx, (name, value) in enumerate(metrics.items()):
        color, explanation = classify_metric(name, value)
        formatted = f"{float(value):.2f}" if value else 'N/A'
        
        with cols[idx % 3]:
            st.markdown(f"""
            <div class="metric-card {color}">
                <div style="font-weight: 700; margin-bottom: 10px;">{name}</div>
                <div style="font-size: 2.2em; font-weight: 800; margin: 10px 0;">{formatted}</div>
                <div style="font-size: 0.9em; color: #64748b;">{explanation}</div>
            </div>
            """, unsafe_allow_html=True)

# ==================== MAIN ====================
def main():
    if st.session_state.view == 'news':
        show_news_view()
    else:
        show_analysis_view()

if __name__ == "__main__":
    main()

