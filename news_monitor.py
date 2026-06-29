"""
news_monitor.py
Reuters + AP Tier 1 News Monitor with Telegram Alerts
Filters news by economic/market sensitivity keywords
"""

import requests
import feedparser
import json
import os
import hashlib
from datetime import datetime
import pytz

# ==========================================
# Configuration
# ==========================================

TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID')
TAIWAN_TZ = pytz.timezone('Asia/Taipei')
SENT_NEWS_FILE = 'sent_news.json'

# ==========================================
# Tier 1 RSS Feeds
# ==========================================

RSS_FEEDS = [
    {
        'name': '🔴 Reuters World',
        'url': 'https://feeds.reuters.com/reuters/worldNews',
        'tier': 1
    },
    {
        'name': '🔴 Reuters Business',
        'url': 'https://feeds.reuters.com/reuters/businessNews',
        'tier': 1
    },
    {
        'name': '🔴 Reuters Markets',
        'url': 'https://feeds.reuters.com/reuters/UKmarkets',
        'tier': 1
    },
    {
        'name': '🔵 AP Top News',
        'url': 'https://feeds.apnews.com/rss/apf-topnews',
        'tier': 1
    },
    {
        'name': '🔵 AP Business',
        'url': 'https://feeds.apnews.com/rss/apf-business',
        'tier': 1
    },
    {
        'name': '🔵 AP World News',
        'url': 'https://feeds.apnews.com/rss/apf-worldnews',
        'tier': 1
    },
]

# ==========================================
# Keyword Filters (Your Market Sensitivities)
# ==========================================

HIGH_PRIORITY_KEYWORDS = [
    # Fed / Interest Rates
    'federal reserve', 'fed rate', 'fomc', 'interest rate',
    'rate hike', 'rate cut', 'jerome powell', 'kevin warsh',
    'monetary policy', 'quantitative',

    # Inflation
    'inflation', 'cpi', 'pce', 'consumer price',
    'core inflation', 'deflation',

    # Jobs
    'nonfarm payroll', 'non-farm', 'unemployment rate',
    'jobs report', 'labor market', 'payroll',

    # Taiwan / TSMC / Semiconductors
    'taiwan', 'tsmc', 'taiwan semiconductor',
    'semiconductor', 'chip ban', 'chip export',
    'advanced chip', 'ai chip',

    # Iran / Oil / Middle East
    'iran', 'strait of hormuz', 'ceasefire',
    'oil price', 'crude oil', 'opec',
    'middle east', 'hezbollah', 'israel strike',
    'iran nuclear', 'sanctions iran',

    # Trump Market-Moving
    'trump tariff', 'trump trade',
    'trump fed', 'trump powell',
    'trump china', 'trump taiwan',
    'trump iran', 'trump oil',
]

MEDIUM_PRIORITY_KEYWORDS = [
    # AI / Tech
    'artificial intelligence', 'ai investment',
    'nvidia', 'micron', 'hbm memory',
    'spacex', 'palantir',

    # China
    'china economy', 'china gdp',
    'china trade', 'china export',
    'pmi china', 'yuan',

    # Global Economy
    'recession', 'gdp growth',
    'bank of japan', 'boj rate',
    'ecb rate', 'european central bank',
    'dollar index', 'treasury yield',

    # Commodities
    'gold price', 'oil embargo',
    'energy price', 'natural gas',
]

# ==========================================
# Telegram Functions
# ==========================================

def send_telegram(message, priority='HIGH'):
    """Send message to Telegram"""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("⚠️ Telegram credentials not found")
        return False

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"

    # Add priority emoji
    if priority == 'HIGH':
        prefix = "🚨 BREAKING"
    else:
        prefix = "📰 NEWS"

    full_message = f"{prefix}\n\n{message}"

    payload = {
        'chat_id': TELEGRAM_CHAT_ID,
        'text': full_message,
        'parse_mode': 'HTML',
        'disable_web_page_preview': False
    }

    try:
        response = requests.post(url, json=payload, timeout=10)
        if response.status_code == 200:
            print(f"✅ Telegram sent: {message[:50]}...")
            return True
        else:
            print(f"❌ Telegram failed: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Telegram error: {e}")
        return False


def send_startup_message():
    """Send a startup confirmation message"""
    tw_time = datetime.now(TAIWAN_TZ).strftime('%Y-%m-%d %H:%M')
    message = (
        f"✅ <b>News Monitor Active</b>\n"
        f"🕐 Taiwan Time: {tw_time}\n\n"
        f"Monitoring:\n"
        f"🔴 Reuters (World, Business, Markets)\n"
        f"🔵 AP (Top News, Business, World)\n\n"
        f"🚨 HIGH priority: Fed, Iran, Taiwan, Oil, Jobs\n"
        f"📰 MEDIUM priority: AI, China, Global Economy"
    )
    send_telegram(message, priority='HIGH')


# ==========================================
# News Processing
# ==========================================

def load_sent_news():
    """Load previously sent news IDs"""
    try:
        if os.path.exists(SENT_NEWS_FILE):
            with open(SENT_NEWS_FILE, 'r') as f:
                return set(json.load(f))
    except:
        pass
    return set()


def save_sent_news(sent_ids):
    """Save sent news IDs"""
    # Keep only last 500 to avoid file bloat
    ids_list = list(sent_ids)[-500:]
    with open(SENT_NEWS_FILE, 'w') as f:
        json.dump(ids_list, f)


def get_news_id(entry):
    """Generate unique ID for a news entry"""
    text = (entry.get('title', '') + entry.get('link', ''))
    return hashlib.md5(text.encode()).hexdigest()


def check_keywords(text, keywords):
    """Check if text contains any keywords"""
    text_lower = text.lower()
    matched = []
    for keyword in keywords:
        if keyword.lower() in text_lower:
            matched.append(keyword)
    return matched


def format_news_message(entry, source_name, matched_keywords, priority):
    """Format news for Telegram"""
    title = entry.get('title', 'No title')
    link = entry.get('link', '')
    summary = entry.get('summary', '')[:200] if entry.get('summary') else ''

    # Clean summary
    if summary:
        # Remove HTML tags
        import re
        summary = re.sub('<[^<]+?>', '', summary)
        summary = summary[:150] + '...' if len(summary) > 150 else summary

    # Format time
    try:
        pub_time = entry.get('published', '')
        if pub_time:
            from email.utils import parsedate_to_datetime
            dt = parsedate_to_datetime(pub_time)
            tw_time = dt.astimezone(TAIWAN_TZ).strftime('%m/%d %H:%M')
        else:
            tw_time = datetime.now(TAIWAN_TZ).strftime('%m/%d %H:%M')
    except:
        tw_time = datetime.now(TAIWAN_TZ).strftime('%m/%d %H:%M')

    # Keywords display
    keywords_str = ', '.join(matched_keywords[:3])

    message = (
        f"<b>{title}</b>\n\n"
        f"📡 {source_name}\n"
        f"🕐 {tw_time} (Taiwan)\n"
        f"🔑 Keywords: {keywords_str}\n\n"
    )

    if summary:
        message += f"{summary}\n\n"

    message += f"🔗 <a href='{link}'>Read more</a>"

    return message


# ==========================================
# Main Monitor Function
# ==========================================

def monitor_news():
    """Main function to check all feeds and send alerts"""
    print("🚀 Starting news monitor...")
    print(f"🕐 Taiwan time: {datetime.now(TAIWAN_TZ).strftime('%Y-%m-%d %H:%M')}")
    print("=" * 50)

    sent_news = load_sent_news()
    new_alerts = []

    for feed_info in RSS_FEEDS:
        print(f"\n📡 Checking {feed_info['name']}...")

        try:
            feed = feedparser.parse(feed_info['url'])
            entries = feed.entries[:20]  # Check latest 20 articles
            print(f"   Found {len(entries)} articles")

            for entry in entries:
                news_id = get_news_id(entry)

                # Skip if already sent
                if news_id in sent_news:
                    continue

                title = entry.get('title', '')
                summary = entry.get('summary', '')
                full_text = f"{title} {summary}"

                # Check HIGH priority keywords
                high_matches = check_keywords(full_text, HIGH_PRIORITY_KEYWORDS)

                if high_matches:
                    print(f"   🚨 HIGH PRIORITY: {title[:60]}...")
                    print(f"      Keywords: {high_matches}")

                    message = format_news_message(
                        entry,
                        feed_info['name'],
                        high_matches,
                        'HIGH'
                    )

                    new_alerts.append({
                        'message': message,
                        'priority': 'HIGH',
                        'id': news_id,
                        'title': title
                    })
                    continue

                # Check MEDIUM priority keywords
                medium_matches = check_keywords(full_text, MEDIUM_PRIORITY_KEYWORDS)

                if medium_matches:
                    print(f"   📰 MEDIUM: {title[:60]}...")

                    message = format_news_message(
                        entry,
                        feed_info['name'],
                        medium_matches,
                        'MEDIUM'
                    )

                    new_alerts.append({
                        'message': message,
                        'priority': 'MEDIUM',
                        'id': news_id,
                        'title': title
                    })

        except Exception as e:
            print(f"   ❌ Error fetching {feed_info['name']}: {e}")

    # Send alerts (HIGH priority first)
    print(f"\n📊 Found {len(new_alerts)} new relevant articles")

    high_alerts = [a for a in new_alerts if a['priority'] == 'HIGH']
    medium_alerts = [a for a in new_alerts if a['priority'] == 'MEDIUM']

    print(f"   🚨 HIGH: {len(high_alerts)}")
    print(f"   📰 MEDIUM: {len(medium_alerts)}")

    # Send HIGH priority immediately
    for alert in high_alerts[:5]:  # Max 5 HIGH alerts per run
        success = send_telegram(alert['message'], 'HIGH')
        if success:
            sent_news.add(alert['id'])

    # Bundle MEDIUM alerts into digest
    if medium_alerts:
        digest = f"📰 <b>News Digest</b> ({len(medium_alerts)} articles)\n\n"
        for alert in medium_alerts[:5]:  # Max 5 in digest
            digest += f"• {alert['title'][:80]}\n"
            sent_news.add(alert['id'])

        if len(medium_alerts) > 0:
            send_telegram(digest, 'MEDIUM')

    # If nothing found
    if not new_alerts:
        print("✅ No new relevant articles found")

    # Save sent news
    save_sent_news(sent_news)

    print("\n✅ Monitor run complete!")
    return len(new_alerts)


# ==========================================
# Main Entry Point
# ==========================================

if __name__ == '__main__':
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == 'test':
        # Test mode: send startup message
        print("🧪 Test mode: sending startup message...")
        send_startup_message()
    else:
        # Normal mode: monitor news
        monitor_news()
