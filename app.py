import streamlit as st
import tweepy
import re
import csv
import time
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import plotly.express as px
from tweepy.errors import TooManyRequests
from collections import Counter
from datetime import datetime
import os

# ---------- CONFIG ----------
st.set_page_config(
    layout="wide",
    page_title="LeapScholar Brand Monitor",
    page_icon="📊"
)

# ---------- TWITTER AUTH ----------
bearer_token = "AAAAAAAAAAAAAAAAAAAAACrm3QEAAAAAyRzo%2F2Z0UuzmncOvP%2F76JhgMHgU%3DSprfOQ8bMtwjLSHIfRk378wkaO1ICbnii6dUGlySzIfO44VJiS"  # 🔴 MOVE TO ENV VARIABLE IN REAL USE
client = tweepy.Client(bearer_token=bearer_token)

# ---------- ENSURE DATA FOLDER ----------
os.makedirs("data_validation", exist_ok=True)

# ---------- CLEAN TWEET ----------
def clean_tweet(tweet):
    tweet = re.sub(r"http\S+", "", tweet)
    tweet = re.sub(r"@\w+", "", tweet)
    tweet = re.sub(r"#", "", tweet)
    tweet = re.sub(r"\s+", " ", tweet).strip()
    return tweet

# ---------- VALIDATION RULES (HUMAN-IN-THE-LOOP LOGIC) ----------
def validate_brand_text(text):
    text_lower = text.lower()

    # Rule 1: Too short / vague
    if len(text_lower.split()) < 3:
        return "Flagged", "Too vague"

    # Rule 2: Spam / repetition
    if len(set(text_lower.split())) <= 2:
        return "Flagged", "Spam or repetition"

    # Rule 3: Must contain feedback signal
    opinion_keywords = [
        "helped", "support", "problem", "issue", "delay",
        "bad", "good", "great", "not satisfied",
        "refund", "slow", "response", "experience"
    ]
    if not any(word in text_lower for word in opinion_keywords):
        return "Flagged", "No clear feedback"

    return "Approved", None

# ---------- SENTIMENT CLASSIFIER ----------
def classify_sentiment(text):
    analyzer = SentimentIntensityAnalyzer()
    score = analyzer.polarity_scores(text)

    if score["compound"] >= 0.05:
        return "Positive"
    elif score["compound"] <= -0.05:
        return "Negative"
    else:
        return "Neutral"

# ---------- FETCH, VALIDATE & ANALYZE ----------
@st.cache_data(ttl=900)
def get_tweets(query="LeapScholar", max_results=50):

    raw_rows = []
    reviewed_rows = []
    analyzed = []

    while True:
        try:
            response = client.search_recent_tweets(
                query=query + " -is:retweet",
                max_results=max_results,
                tweet_fields=["text", "lang", "created_at", "id"]
            )

            if response.data:
                for tweet in response.data:
                    if tweet.lang != "en":
                        continue

                    text = clean_tweet(tweet.text)

                    # ---- RAW DATA CAPTURE ----
                    raw_rows.append([
                        tweet.id,
                        "Twitter",
                        text
                    ])

                    # ---- VALIDATION ----
                    status, issue = validate_brand_text(text)

                    reviewed_rows.append([
                        tweet.id,
                        "Twitter",
                        text,
                        issue,
                        status
                    ])

                    # ---- ONLY APPROVED DATA GOES FOR ANALYSIS ----
                    if status != "Approved":
                        continue

                    sentiment = classify_sentiment(text)
                    created = tweet.created_at.strftime("%d %b %Y, %H:%M")
                    url = f"https://twitter.com/i/web/status/{tweet.id}"

                    analyzed.append((text, sentiment, created, url))

            # ---------- WRITE CSV OUTPUTS ----------
            with open("data_validation/raw_brand_data.csv", "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(["id", "source", "text"])
                writer.writerows(raw_rows)

            with open("data_validation/reviewed_brand_data.csv", "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(["id", "source", "text", "issue_found", "final_status"])
                writer.writerows(reviewed_rows)

            return analyzed

        except TooManyRequests as e:
            reset_time = int(e.response.headers.get("x-rate-limit-reset", 0))
            wait_time = max(reset_time - int(time.time()), 60)
            st.warning(f"Rate limit reached. Waiting {wait_time} seconds...")
            time.sleep(wait_time)

        except Exception as e:
            st.error(f"Unexpected error: {e}")
            return []

# ---------- DASHBOARD ----------
st.title("📢 LeapScholar Brand Monitor Dashboard")

tweets = get_tweets()

if not tweets:
    st.warning("No approved tweets available after validation.")
    st.stop()

# ---------- SENTIMENT COUNTS ----------
sentiments = [s for _, s, _, _ in tweets]
sentiment_counts = dict(Counter(sentiments))
for s in ["Positive", "Neutral", "Negative"]:
    sentiment_counts.setdefault(s, 0)

# ---------- SUMMARY BLOCKS ----------
col1, col2, col3 = st.columns(3)

with col1:
    st.metric("😊 Positive", sentiment_counts["Positive"])
with col2:
    st.metric("😐 Neutral", sentiment_counts["Neutral"])
with col3:
    st.metric("😡 Negative", sentiment_counts["Negative"])

st.markdown("---")

# ---------- CHARTS ----------
left_col, right_col = st.columns(2)

with left_col:
    st.plotly_chart(
        px.pie(
            names=sentiment_counts.keys(),
            values=sentiment_counts.values(),
            title="Sentiment Distribution"
        ),
        use_container_width=True
    )

with right_col:
    st.plotly_chart(
        px.bar(
            x=list(sentiment_counts.keys()),
            y=list(sentiment_counts.values()),
            title="Sentiment Counts",
            labels={"x": "Sentiment", "y": "Count"}
        ),
        use_container_width=True
    )

st.markdown("---")

# ---------- TWEET DISPLAY ----------
st.subheader("🗣️ Approved Brand Mentions")

emoji_map = {
    "Positive": "😊",
    "Neutral": "😐",
    "Negative": "😡"
}

bg_colors = {
    "Positive": "#d4edda",
    "Neutral": "#f8f9fa",
    "Negative": "#f8d7da"
}

left_col, right_col = st.columns(2)

for i, (text, sentiment, created, url) in enumerate(tweets):
    card = f"""
    <div style="background:{bg_colors[sentiment]};
                padding:15px;
                border-radius:10px;
                margin-bottom:20px;">
        <b>{emoji_map[sentiment]} {sentiment}</b> • <i>{created}</i>
        <p style="font-size:16px;">{text}</p>
        <a href="{url}" target="_blank">🔗 View Tweet</a>
    </div>
    """

    if i % 2 == 0:
        left_col.markdown(card, unsafe_allow_html=True)
    else:
        right_col.markdown(card, unsafe_allow_html=True)
