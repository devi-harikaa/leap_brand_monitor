# 📢 LeapScholar Brand Perception Monitor

A real-time Twitter sentiment analysis tool that tracks public perception of the LeapScholar brand using **Natural Language Processing (NLP)**, **VADER Sentiment Analyzer**, and a dynamic **Streamlit dashboard**.

## 🎯 Objective

To monitor and analyze public sentiment about the LeapScholar brand from Twitter in real-time, helping the team:

- Track positive, neutral, and negative opinions dynamically
- Identify praise or criticism instantly
- Understand emotional tone and trending topics
- Improve decision-making in branding and customer experience

---

## 💡 Why This Project?

In the digital era, platforms like Twitter heavily influence a brand’s reputation. For a study-abroad leader like **LeapScholar**, real-time sentiment monitoring is crucial.

This project demonstrates:

- ✅ Real-world use of NLP and Machine Learning
- ✅ Twitter API integration for live data
- ✅ Interactive web dashboard with Streamlit
- ✅ A practical brand-monitoring tool for digital PR teams

---

## 🛠️ Tech Stack

| Tool/Library       | Purpose                                                         |
|--------------------|-----------------------------------------------------------------|
| **Tweepy**         | Connects to Twitter API v2 for real-time tweet fetching         |
| **VADER**          | Performs sentiment analysis (positive, neutral, negative)       |
| **Streamlit**      | Builds interactive web UI and visualizes sentiment data         |
| **Regex (re)**     | Cleans tweet text (removes URLs, mentions, emojis)              |
| **wordcloud**      | Generates trending topic visualization                          |
| **Python**         | Core logic, data processing, and sentiment classification       |

---

## 📁 Project Structure

```
leap_brand_monitor/
│
├── app.py              # Main Streamlit app
├── requirements.txt    # Python dependencies
└── venv/               # Virtual environment (excluded from version control)
```

---

## 🚀 How It Works

### ✅ Step 1: Twitter API Setup

- Configured Twitter Developer credentials and Bearer Token.
- Used Tweepy client for API connection.

```python
query = '(LeapScholar OR "Leap Scholar") -is:retweet lang:en'
```

---

### ✅ Step 2: Tweet Collection

- Real-time fetching of tweets mentioning "LeapScholar"
- Filters out retweets, non-English tweets, and duplicates

---

### ✅ Step 3: Sentiment Analysis

- Cleans tweet text using Regex
- Uses VADER to classify sentiment:
  - 😊 Positive
  - 😐 Neutral
  - 😡 Negative

---

### ✅ Step 4: Dashboard Display

- Count of sentiment categories using Streamlit metrics
- Word cloud of trending words
- Tweets displayed in a two-column grid with:
  - Sentiment tags
  - Timestamps
  - Links to original tweets

---

### ✅ Step 5: Error Handling

- Gracefully handles:
  - Twitter API rate limits
  - No available tweet data

---

## 📸 Features Overview

- 🧠 NLP-powered sentiment detection
- 📈 Real-time updates and metrics
- 💬 Clean display of tweets with sentiment highlighting
- 🌐 Word cloud of popular keywords
- ⚡ Lightweight, interactive, and responsive UI

---

## 🔧 Setup Instructions

1. **Clone this repo:**
   ```bash
   git clone https://github.com/your-username/leap-brand-monitor.git
   cd leap-brand-monitor
   ```

2. **Create virtual environment (optional):**
   ```bash
   python -m venv venv
   source venv/bin/activate  # on Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the app:**
   ```bash
   streamlit run app.py
   ```

---

## 📃 License

This project is for educational and academic purposes only.

---
