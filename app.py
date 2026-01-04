import streamlit as st
import tweepy
import os
import re
import csv
import time
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import plotly.express as px
from collections import Counter

# ---------------- CONFIG ----------------
st.set_page_config(
    layout="wide",
    page_title="LeapScholar Brand Monitor",
    page_icon="📢"
)

# ---------------- TWITTER AUTH ----------------
bearer_token = os.getenv("TWITTER_BEARER_TOKEN")
client = tweepy.Client(bearer_token=bearer_token)

# ---------------- DATA FOLDER ----------------
os.makedirs("data_validation", exist_ok=True)

# ---------------- CLEAN TEXT ----------------
def clean_text(text):
    text = re.sub(r"http\S+", "", text)
    text = re.sub(r"@\w+", "", text)
    text = re.sub(r"#", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text

# ---------------- VALIDATION RULES ----------------
def validate_brand_text(text):
    text_lower = text.lower()

    # Too short → reject
    if len(text_lower.split()) < 2:
        return "Flagged", "Too vague"

    # Spam / repetition
    if len(set(text_lower.split())) <= 2:
        return "Flagged", "Spam or repetition"

    opinion_words = [
        "good", "bad", "helped", "support", "issue",
        "problem", "delay", "slow", "experience",
        "review", "service", "counselling", "process",
        "visa", "college", "application"
    ]

    if not any(w in text_lower for w in opinion_words):
        return "Flagged", "No clear feedback"

    return "Approved", None

# ---------------- SENTIMENT ----------------
def classify_sentiment(text):
    analyzer = SentimentIntensityAnalyzer()
    score = analyzer.polarity_scores(text)

    if score["compound"] >= 0.05:
        return "Positive"
    elif score["compound"] <= -0.05:
        return "Negative"
    else:
        return "Neutral"

# ---------------- FETCH FROM TWITTER ----------------
@st.cache_data(ttl=900)
def get_tweets(query="LeapScholar", max_results=25):

    raw_rows = []
    reviewed_rows = []
    approved_tweets = []

    try:
        response = client.search_recent_tweets(
            # IMPORTANT: relaxed query (no retweet exclusion)
            query=query,
            max_results=max_results,
            tweet_fields=["text", "created_at", "id"]
        )

        if not response.data:
            return [], [], []

        for tweet in response.data:
            text = clean_text(tweet.text)

            raw_rows.append([tweet.id, "Twitter", text])

            status, issue = validate_brand_text(text)

            reviewed_rows.append([
                tweet.id, "Twitter", text, issue, status
            ])

            if status != "Approved":
                continue

            sentiment = classify_sentiment(text)
            created = tweet.created_at.strftime("%d %b %Y, %H:%M")
            url = f"https://twitter.com/i/web/status/{tweet.id}"

            approved_tweets.append((text, sentiment, created, url))

        # ---- CSV OUTPUTS ----
        with open("data_validation/raw_brand_data.csv", "w", newline="", encoding="utf-8") as f:
            csv.writer(f).writerows(
                [["id", "source", "text"]] + raw_rows
            )

        with open("data_validation/reviewed_brand_data.csv", "w", newline="", encoding="utf-8") as f:
            csv.writer(f).writerows(
                [["id", "source", "text", "issue_found", "final_status"]] + reviewed_rows
            )

        return approved_tweets, raw_rows, reviewed_rows

    except tweepy.TooManyRequests:
        st.warning("Twitter API rate limit reached. Please wait and retry.")
        return [], [], []

    except Exception as e:
        st.error(f"Unexpected error: {e}")
        return [], [], []

# ---------------- UI ----------------
st.title("📢 LeapScholar Brand Monitor Dashboard")

query = st.text_input("Brand name", value="LeapScholar")

if st.button("Fetch Twitter reviews"):
    with st.spinner("Fetching tweets from Twitter API..."):
        tweets, raw_rows, reviewed_rows = get_tweets(query)
else:
    st.stop()

st.info(f"Total tweets fetched: {len(raw_rows)}")
st.info(f"Approved tweets after validation: {len(tweets)}")

if not tweets:
    st.warning("No approved tweets available after validation.")
    st.stop()

# ---------------- SENTIMENT COUNTS ----------------
sentiments = [s for _, s, _, _ in tweets]
sentiment_counts = dict(Counter(sentiments))
for s in ["Positive", "Neutral", "Negative"]:
    sentiment_counts.setdefault(s, 0)

# ---------------- METRICS ----------------
c1, c2, c3 = st.columns(3)
c1.metric("😊 Positive", sentiment_counts["Positive"])
c2.metric("😐 Neutral", sentiment_counts["Neutral"])
c3.metric("😡 Negative", sentiment_counts["Negative"])

st.markdown("---")

# ---------------- CHARTS ----------------
left, right = st.columns(2)

left.plotly_chart(
    px.pie(
        names=sentiment_counts.keys(),
        values=sentiment_counts.values(),
        title="Sentiment Distribution"
    ),
    use_container_width=True
)

right.plotly_chart(
    px.bar(
        x=list(sentiment_counts.keys()),
        y=list(sentiment_counts.values()),
        title="Sentiment Counts",
        labels={"x": "Sentiment", "y": "Count"}
    ),
    use_container_width=True
)

st.markdown("---")

# ---------------- DISPLAY TWEETS ----------------
st.subheader("🗣️ Approved Twitter Mentions")

emoji = {"Positive": "😊", "Neutral": "😐", "Negative": "😡"}
bg = {"Positive": "#d4edda", "Neutral": "#f8f9fa", "Negative": "#f8d7da"}

col1, col2 = st.columns(2)

for i, (text, sentiment, created, url) in enumerate(tweets):
    card = f"""
    <div style="background:{bg[sentiment]};
                padding:15px;
                border-radius:10px;
                margin-bottom:20px;">
        <b>{emoji[sentiment]} {sentiment}</b> • <i>{created}</i>
        <p style="font-size:16px;">{text}</p>
        <a href="{url}" target="_blank">🔗 View Tweet</a>
    </div>
    """

    if i % 2 == 0:
        col1.markdown(card, unsafe_allow_html=True)
    else:
        col2.markdown(card, unsafe_allow_html=True)
