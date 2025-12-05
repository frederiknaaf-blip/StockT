"""
Aktien-App mit News-Feed und Fundamentalanalyse
Autor: Claude
Verwendung: streamlit run app.py
"""

import streamlit as st
import requests
from datetime import datetime
import time

# ==================== KONFIGURATION ====================
# HIER DEINEN API-KEY EINTRAGEN:
API_TOKEN = "692c1c76752bd1.25047072"  # <-- Trage hier deinen API-Key ein
BASE_URL = "https://eodhd.com/api"
USER_NAME = "Thomas"  # <-- Dein Name für die Begrüßung

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
        border-radius: 12px;
        padding: 20px;
        margin: 15px 0;
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        border-left: 5px solid;
        cursor: pointer;
        transition: all 0.3s ease;
    }
    .news-card:hover {
        transform: translateY(-3px);
        box-shadow: 0 6px 20px rgba(0,0,0,0.15);
    }
    .news-card.positive { border-left-color: #10b981; }
    .news-card.neutral { border-left-color: #f59e0b; }
    .news-card.negative { border-left-color: #ef4444; }
    .ticker-name {
        font-size: 1.8em;
        font-weight: 700;
        color: #1e293b;
        margin-bottom: 5px;
    }
    .news-source {
        font-size: 0.85em;
        color: #94a3b8;
        margin-bottom: 10px;
    }
    .news-summary {
        font-size: 1em;
        color: #475569;
        line-height: 1.6;
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
    .rating-stars {
        font-size: 2em;
        margin: 10px 0;
    }
</style>
""", unsafe_allow_html=True)

# ==================== HILFSFUNKTIONEN ====================

def fetch_news(limit=10):
    """Holt aktuelle Aktien-News"""
    try:
        url = f"{BASE_URL}/news"
        params = {
            "api_token": API_TOKEN,
            "limit": limit,
            "offset": 0
        }
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.error(f"Fehler beim Laden der News: {e}")
        return []

def fetch_fundamentals(ticker):
    """Holt Fundamentaldaten für einen Ticker"""
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
        st.error(f"Fehler beim Laden der Daten für {ticker}: {e}")
        return None

def classify_news_sentiment(title, content=""):
    """Klassifiziert News-Sentiment"""
    text = (title + " " + content).lower()
    positive = ['beats', 'surge', 'soars', 'rallies', 'gains', 'profit', 'growth', 
                'upgrade', 'bullish', 'record', 'high', 'success', 'strong', 'buy']
    negative = ['falls', 'drops', 'plunges', 'crash', 'loss', 'decline', 'warning',
                'risk', 'bearish', 'downgrade', 'sell', 'weak', 'miss', 'concern']
    
    pos_count = sum(1 for word in positive if word in text)
    neg_count = sum(1 for word in negative if word in text)
    
    if pos_count > neg_count:
        return 'positive', '🟢'
    elif neg_count > pos_count:
        return 'negative', '🔴'
    else:
        return 'neutral', '🟡'

def classify_metric(metric_name, value):
    """Klassifiziert eine Kennzahl"""
    if value is None or (isinstance(value, str) and value in ['N/A', '-', '']):
        return 'red', 'Wert nicht verfügbar'
    
    try:
        val = float(value)
    except:
        return 'red', 'Ungültiger Wert'
    
    classifications = {
        'P/E Ratio': [
            (lambda v: v > 30, 'red', 'Sehr hoch (>30). Potenziell überbewertet.'),
            (lambda v: v >= 15, 'yellow', 'Normal (15-30). Fair bewertet.'),
            (lambda v: v > 0, 'green', 'Niedrig (<15). Potenziell unterbewertet.'),
            (lambda v: True, 'red', 'Negativ. Unternehmen macht Verluste.')
        ],
        'PEG Ratio': [
            (lambda v: v > 2, 'red', 'Hoch (>2). Wachstum zu teuer.'),
            (lambda v: v >= 1, 'yellow', 'Moderat (1-2). Fair.'),
            (lambda v: v > 0, 'green', 'Gering (<1). Unterbewertet.')
        ],
        'Debt/Equity': [
            (lambda v: v > 1.5, 'red', 'Hoch (>1.5). Hohes Risiko.'),
            (lambda v: v > 0.5, 'yellow', 'Moderat (0.5-1.5). Akzeptabel.'),
            (lambda v: v >= 0, 'green', 'Gering (<0.5). Solide.')
        ],
        'ROE': [
            (lambda v: v >= 15, 'green', 'Sehr gut (>15%). Effizient.'),
            (lambda v: v >= 5, 'yellow', 'Moderat (5-15%). Solide.'),
            (lambda v: True, 'red', 'Gering (<5%). Ineffizient.')
        ],
        'Profit Margin': [
            (lambda v: v >= 15, 'green', 'Hoch (>15%). Stark profitabel.'),
            (lambda v: v >= 5, 'yellow', 'Solide (5-15%). Profitabel.'),
            (lambda v: True, 'red', 'Niedrig (<5%). Schwach.')
        ],
        'Current Ratio': [
            (lambda v: v >= 2, 'green', 'Sehr gut (>2). Exzellente Liquidität.'),
            (lambda v: v >= 1, 'yellow', 'Gut (1-2). Ausreichend.'),
            (lambda v: True, 'red', 'Problematisch (<1). Liquiditätsprobleme.')
        ],
        'Dividend Yield': [
            (lambda v: v > 6, 'red', 'Sehr hoch (>6%). Möglicherweise nicht nachhaltig.'),
            (lambda v: v > 3, 'green', 'Attraktiv (3-6%). Gut.'),
            (lambda v: v > 0, 'yellow', 'Solide (0-3%). Angemessen.')
        ],
        'Beta': [
            (lambda v: v > 1.2, 'red', 'Hoch (>1.2). Hohe Volatilität.'),
            (lambda v: v > 0.8, 'yellow', 'Moderat (0.8-1.2). Normal.'),
            (lambda v: v >= 0, 'green', 'Gering (<0.8). Stabil.')
        ]
    }
    
    if metric_name in classifications:
        for condition, color, explanation in classifications[metric_name]:
            if condition(val):
                return color, explanation
    
    return 'yellow', 'Keine Bewertung verfügbar'

def calculate_overall_rating(data):
    """Berechnet Gesamt-Rating 1-10"""
    if not data or 'Highlights' not in data:
        return 5.0, "Unzureichende Daten"
    
    highlights = data.get('Highlights', {})
    valuation = data.get('Valuation', {})
    
    score = 0
    weights = 0
    
    # P/E Ratio
    pe = highlights.get('PERatio')
    if pe and pe > 0:
        if pe < 15: score += 9 * 1.5
        elif pe <= 25: score += 6 * 1.5
        elif pe <= 35: score += 4 * 1.5
        else: score += 2 * 1.5
        weights += 1.5
    
    # ROE
    roe = highlights.get('ReturnOnEquityTTM')
    if roe:
        roe_pct = roe * 100
        if roe_pct >= 20: score += 10 * 2.0
        elif roe_pct >= 15: score += 8 * 2.0
        elif roe_pct >= 10: score += 6 * 2.0
        elif roe_pct >= 5: score += 4 * 2.0
        else: score += 2 * 2.0
        weights += 2.0
    
    # Profit Margin
    profit_margin = highlights.get('ProfitMargin')
    if profit_margin:
        pm_pct = profit_margin * 100
        if pm_pct >= 20: score += 10 * 1.5
        elif pm_pct >= 15: score += 8 * 1.5
        elif pm_pct >= 10: score += 6 * 1.5
        elif pm_pct >= 5: score += 4 * 1.5
        else: score += 2 * 1.5
        weights += 1.5
    
    # Debt/Equity
    debt_equity = highlights.get('DebtEquityMRQ')
    if debt_equity is not None:
        if debt_equity < 0.3: score += 10 * 1.0
        elif debt_equity < 0.7: score += 8 * 1.0
        elif debt_equity < 1.2: score += 6 * 1.0
        elif debt_equity < 2.0: score += 4 * 1.0
        else: score += 2 * 1.0
        weights += 1.0
    
    if weights == 0:
        return 5.0, "Nicht genügend Daten"
    
    final_rating = score / weights
    
    if final_rating >= 8:
        explanation = "🚀 Exzellente Aktie! Starke Fundamentals."
    elif final_rating >= 6.5:
        explanation = "✅ Gute Aktie. Solide Kennzahlen."
    elif final_rating >= 5:
        explanation = "⚖️ Durchschnittlich. Gemischte Signale."
    elif final_rating >= 3.5:
        explanation = "⚠️ Schwach. Mehrere Warnsignale."
    else:
        explanation = "🔴 Kritisch. Hohes Risiko."
    
    return final_rating, explanation

def get_star_rating(rating):
    """Konvertiert Rating in Sterne"""
    full_stars = int(rating)
    half_star = 1 if (rating - full_stars) >= 0.5 else 0
    empty_stars = 10 - full_stars - half_star
    stars = "⭐" * full_stars
    if half_star: stars += "✨"
    stars += "☆" * empty_stars
    return stars

# ==================== SESSION STATE ====================
if 'view' not in st.session_state:
    st.session_state.view = 'news'
if 'selected_ticker' not in st.session_state:
    st.session_state.selected_ticker = None

# ==================== NEWS VIEW ====================
def show_news_view():
    st.markdown(f'<h1 class="main-header">👋 Hallo {USER_NAME}</h1>', unsafe_allow_html=True)
    st.markdown("### 📰 Aktuelle Aktien-News")
    
    with st.spinner('Lade aktuelle News...'):
        news_data = fetch_news(limit=15)
    
    if not news_data:
        st.warning("Keine News verfügbar")
        return
    
    for article in news_data:
        title = article.get('title', 'Kein Titel')
        symbols = article.get('symbols', '')
        
        # FIX: Robuste Ticker-Extraktion
        if symbols and symbols.strip():
            ticker = symbols.split(',')[0].strip()
        else:
            ticker = 'N/A'
            
        source = article.get('source', 'Unbekannt')
        date = article.get('date', '')
        
        sentiment, emoji = classify_news_sentiment(title)
        
        # Kurze Zusammenfassung (erster Satz aus Titel)
        summary = title.split('.')[0] + '.' if '.' in title else title[:150] + '...'
        
        col1, col2 = st.columns([0.95, 0.05])
        
        with col1:
            st.markdown(f"""
            <div class="news-card {sentiment}">
                <div class="ticker-name">{emoji} {ticker}</div>
                <div class="news-source">{source} • {date[:10]}</div>
                <div class="news-summary">{summary}</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            if ticker != 'N/A':
                if st.button("→", key=f"btn_{ticker}_{date}", help="Analysieren"):
                    st.session_state.selected_ticker = ticker
                    st.session_state.view = 'analysis'
                    st.rerun()

# ==================== ANALYSIS VIEW ====================
def show_analysis_view():
    ticker = st.session_state.selected_ticker
    
    col1, col2 = st.columns([0.1, 0.9])
    with col1:
        if st.button("← Zurück"):
            st.session_state.view = 'news'
            st.rerun()
    
    with col2:
        st.markdown(f'<h1 class="main-header">📊 Analyse: {ticker}</h1>', unsafe_allow_html=True)
    
    with st.spinner(f'Lade Daten für {ticker}...'):
        data = fetch_fundamentals(ticker)
    
    if not data or 'General' not in data:
        st.error(f"Keine Daten für {ticker} verfügbar")
        return
    
    general = data.get('General', {})
    highlights = data.get('Highlights', {})
    valuation = data.get('Valuation', {})
    technicals = data.get('Technicals', {})
    
    # Company Info
    st.markdown(f"""
    <div style="text-align: center; background: linear-gradient(135deg, #ec4899 0%, #f43f5e 100%); 
                color: white; padding: 25px; border-radius: 16px; margin-bottom: 25px;">
        <h2 style="margin: 0; font-size: 2em; font-weight: 800;">{general.get('Name', 'N/A')}</h2>
        <div style="font-size: 1.1em; margin-top: 10px;">
            <strong>{general.get('Code', 'N/A')}</strong> • 
            {general.get('Exchange', 'N/A')} • 
            {general.get('Sector', 'N/A')}
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Rating
    rating, rating_explanation = calculate_overall_rating(data)
    stars = get_star_rating(rating)
    
    st.markdown(f"""
    <div class="rating-box">
        <div style="font-size: 1.2em; font-weight: 600; text-transform: uppercase; letter-spacing: 2px;">
            Gesamt-Rating
        </div>
        <div class="rating-score">{rating:.1f}/10</div>
        <div class="rating-stars">{stars}</div>
        <div style="font-size: 1.1em; margin-top: 15px;">{rating_explanation}</div>
    </div>
    """, unsafe_allow_html=True)
    
    # Kennzahlen
    st.markdown("### 💰 Fundamentale Kennzahlen")
    
    metrics = {
        'P/E Ratio': highlights.get('PERatio'),
        'PEG Ratio': highlights.get('PEGRatio'),
        'Debt/Equity': highlights.get('DebtEquityMRQ'),
        'ROE': highlights.get('ReturnOnEquityTTM', 0) * 100 if highlights.get('ReturnOnEquityTTM') else None,
        'Profit Margin': highlights.get('ProfitMargin', 0) * 100 if highlights.get('ProfitMargin') else None,
        'Current Ratio': valuation.get('CurrentRatio'),
        'Dividend Yield': highlights.get('DividendYield', 0) * 100 if highlights.get('DividendYield') else None,
        'Beta': technicals.get('Beta'),
        'EPS (TTM)': highlights.get('EarningsShare'),
        'Revenue Growth': highlights.get('RevenuePerShareTTM'),
        'Free Cash Flow': highlights.get('OperatingCashFlowTTM'),
        'Market Cap': general.get('MarketCapitalization')
    }
    
    cols = st.columns(3)
    for idx, (metric_name, value) in enumerate(metrics.items()):
        color, explanation = classify_metric(metric_name, value)
        
        if value is not None:
            if metric_name in ['ROE', 'Profit Margin', 'Dividend Yield']:
                formatted_value = f"{float(value):.2f}%"
            elif metric_name in ['Market Cap', 'Free Cash Flow']:
                formatted_value = f"${float(value)/1e9:.2f}B" if value else 'N/A'
            else:
                try:
                    formatted_value = f"{float(value):.2f}"
                except:
                    formatted_value = str(value)
        else:
            formatted_value = 'N/A'
        
        with cols[idx % 3]:
            st.markdown(f"""
            <div class="metric-card {color}">
                <div style="font-size: 1.1em; font-weight: 700; color: #1e293b; margin-bottom: 10px;">
                    {metric_name}
                </div>
                <div style="font-size: 2.2em; font-weight: 800; color: #0f172a; margin: 10px 0;">
                    {formatted_value}
                </div>
                <div style="font-size: 0.9em; color: #64748b;">
                    {explanation}
                </div>
            </div>
            """, unsafe_allow_html=True)

# ==================== MAIN APP ====================
def main():
    if st.session_state.view == 'news':
        show_news_view()
    else:
        show_analysis_view()

if __name__ == "__main__":
    main()
