import streamlit as st
import tweepy
import re
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import plotly.express as px
import time
from tweepy.errors import TooManyRequests
from collections import Counter
from datetime import datetime

# ---------- CONFIG ----------
st.set_page_config(layout="wide", page_title="LeapScholar Brand Monitor", page_icon="📊")

# ---------- TWITTER AUTH ----------
bearer_token = "AAAAAAAAAAAAAAAAAAAAACrm3QEAAAAAyRzo%2F2Z0UuzmncOvP%2F76JhgMHgU%3DSprfOQ8bMtwjLSHIfRk378wkaO1ICbnii6dUGlySzIfO44VJiS"  # Replace with your actual token securely
client = tweepy.Client(bearer_token=bearer_token)

# ---------- CLEAN TWEETS ----------
def clean_tweet(tweet):
    tweet = re.sub(r"http\S+", "", tweet)  # Remove URLs
    tweet = re.sub(r"@\w+", "", tweet)     # Remove mentions
    tweet = re.sub(r"#", "", tweet)        # Remove hashtags
    tweet = re.sub(r"\s+", " ", tweet).strip()  # Normalize whitespace
    return tweet

# ---------- HYBRID SENTIMENT CLASSIFIER ----------
def classify_sentiment(text):
    complaint_keywords = [
        "complaint", "unsolicited", "problem", "issue", "not satisfied",
        "bad", "poor", "refund", "cancel", "delay", "disappointed", "complain"
    ]
    analyzer = SentimentIntensityAnalyzer()
    score = analyzer.polarity_scores(text)
    lower_text = text.lower()

    if any(word in lower_text for word in complaint_keywords):
        return "Negative"
    if score['compound'] >= 0.05:
        return "Positive"
    elif score['compound'] <= -0.05:
        return "Negative"
    else:
        return "Neutral"

# ---------- FETCH AND ANALYZE ----------
@st.cache_data(ttl=900)
def get_tweets(query="LeapScholar", max_results=50):
    while True:
        try:
            tweets_response = client.search_recent_tweets(
                query=query + " -is:retweet",
                max_results=max_results,
                tweet_fields=["text", "lang", "created_at", "id", "author_id"]
            )

            analyzed = []
            if tweets_response.data:
                for tweet in tweets_response.data:
                    if tweet.lang == "en":
                        text = clean_tweet(tweet.text)
                        sentiment = classify_sentiment(text)
                        created = tweet.created_at.strftime("%d %b %Y, %H:%M")
                        url = f"https://twitter.com/i/web/status/{tweet.id}"
                        analyzed.append((text, sentiment, created, url))
            return analyzed

        except TooManyRequests as e:
            reset_time = int(e.response.headers.get("x-rate-limit-reset", 0))
            current_time = int(time.time())
            wait_time = max(reset_time - current_time, 60)
            st.warning(f"Rate limit reached. Waiting {wait_time} seconds before retrying...")
            time.sleep(wait_time)
        except Exception as e:
            st.error(f"Unexpected error: {e}")
            return []

# ---------- MAIN DASHBOARD ----------
st.title("📢 LeapScholar Brand Monitor Dashboard")

tweets = get_tweets()

if not tweets:
    st.warning("No recent tweets found or API limit reached.")
    st.stop()

# ---------- SENTIMENT COUNTS ----------
sentiments = [sentiment for _, sentiment, _, _ in tweets]
sentiment_counts = dict(Counter(sentiments))
for s in ["Positive", "Neutral", "Negative"]:
    sentiment_counts.setdefault(s, 0)

# ---------- SENTIMENT BLOCKS ----------
col1, col2, col3 = st.columns(3)

with col1:
    st.markdown(f"""
        <div style="background-color:#90EE90; padding:30px; border-radius:10px; text-align:center;">
            <h3 style="color:black;">😊 Positive</h3>
            <h2 style="color:black;">{sentiment_counts["Positive"]}</h2>
        </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown(f"""
        <div style="background-color:#D3D3D3; padding:30px; border-radius:10px; text-align:center;">
            <h3 style="color:black;">😐 Neutral</h3>
            <h2 style="color:black;">{sentiment_counts["Neutral"]}</h2>
        </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown(f"""
        <div style="background-color:#FF7F7F; padding:30px; border-radius:10px; text-align:center;">
            <h3 style="color:black;">😡 Negative</h3>
            <h2 style="color:black;">{sentiment_counts["Negative"]}</h2>
        </div>
    """, unsafe_allow_html=True)

st.markdown("---")

# ---------- PIE + BAR CHARTS ----------
left_col, right_col = st.columns(2)

with left_col:
    pie_fig = px.pie(
        names=list(sentiment_counts.keys()),
        values=list(sentiment_counts.values()),
        color=list(sentiment_counts.keys()),
        title="Sentiment Distribution",
        color_discrete_map={
            "Positive": "lightgreen",
            "Neutral": "lightgray",
            "Negative": "lightcoral"
        }
    )
    st.plotly_chart(pie_fig, use_container_width=True)

with right_col:
    bar_fig = px.bar(
        x=list(sentiment_counts.keys()),
        y=list(sentiment_counts.values()),
        color=list(sentiment_counts.keys()),
        title="Sentiment Counts",
        labels={"x": "Sentiment", "y": "Count"},
        color_discrete_map={
            "Positive": "lightgreen",
            "Neutral": "lightgray",
            "Negative": "lightcoral"
        }
    )
    st.plotly_chart(bar_fig, use_container_width=True)

st.markdown("---")

# ---------- TWEET DISPLAY ----------
st.subheader("🗣️ Recent Mentions of 'LeapScholar'")

sentiment_colors = {
    "Positive": "#d4edda",
    "Neutral": "#f8f9fa",
    "Negative": "#f8d7da"
}

emoji_map = {
    "Positive": "😊",
    "Neutral": "😐",
    "Negative": "😡"
}

# Show tweets in two-column grid
left_col, right_col = st.columns(2)
for i, (text, sentiment, created, url) in enumerate(tweets):
    emoji = emoji_map.get(sentiment, "")
    bg_color = sentiment_colors.get(sentiment, "#ffffff")

    tweet_html = f"""
        <div style="background-color:{bg_color}; padding:15px; border-radius:10px; margin-bottom:20px; 
                    box-shadow: 0 0 5px rgba(0,0,0,0.1); color:#222222;">
            <p style="font-size:14px; margin-bottom:8px;">
                <b>{emoji} {sentiment}</b> • <i>{created}</i>
            </p>
            <p style="font-size:16px; margin-bottom:10px;">{text}</p>
            <a href="{url}" target="_blank" style="color:#1a73e8;">🔗 View on Twitter</a>
        </div>
    """

    if i % 2 == 0:
        left_col.markdown(tweet_html, unsafe_allow_html=True)
    else:
        right_col.markdown(tweet_html, unsafe_allow_html=True)
