# Algorithm for Fetching AI-Related User Questions from Internet

## Overview

This document describes an algorithm for automatically fetching AI/ML-related user questions from various internet sources and updating the prompts database and prompts files on a weekly basis.

## Algorithm Design

### Phase 1: Data Source Identification

**Sources to Scrape:**

1. **Question-Answer Platforms:**
   - Stack Overflow (API: `api.stackexchange.com`)
   - Reddit (`r/MachineLearning`, `r/learnmachinelearning`, `r/datascience`)
   - Quora (via RSS feeds)
   - Stack Exchange sites (AI, Data Science)

2. **Technical Forums:**
   - GitHub Discussions in ML repositories
   - Kaggle Discussions
   - Medium articles with ML tags

3. **API-Based Sources:**
   - Stack Overflow API (most reliable)
   - Reddit API (PRAW)
   - GitHub Search API

### Phase 2: Query Strategy

**Search Keywords/Tags:**
```python
KEYWORDS = [
    "machine learning", "deep learning", "neural network",
    "classification", "regression", "clustering",
    "natural language processing", "computer vision",
    "reinforcement learning", "algorithm recommendation",
    "which algorithm", "what model", "how to train",
    "best algorithm for", "ai model selection"
]
```

**Time-Based Filtering:**
- Fetch questions from last 7 days
- Prioritize questions with high engagement (votes, answers)
- Filter by tags: `machine-learning`, `artificial-intelligence`, `data-science`

### Phase 3: Data Extraction & Processing

**Extraction Pipeline:**

1. **Fetch raw questions:**
   - Title + Body text
   - Tags/Categories
   - Engagement metrics (votes, answers, views)

2. **Filtering Criteria:**
   - Minimum question length: 20 characters
   - Maximum question length: 500 characters
   - Must contain ML/AI keywords
   - Remove duplicates (fuzzy string matching)
   - Remove questions with code-only content

3. **Categorization:**
   - Use existing `get_algorithm_type_from_algorithm()` function
   - Or classify using keywords matching:
     - Classification → "classify", "predict category"
     - Regression → "predict value", "forecast"
     - Clustering → "group", "cluster", "segment"
     - etc.

4. **Quality Scoring:**
   ```python
   score = (
       vote_score * 0.4 +
       answer_count * 0.3 +
       view_count_normalized * 0.2 +
       recency_score * 0.1
   )
   ```
   - Only keep questions with score > threshold

### Phase 4: Data Storage

**Format:**
```
prompt_text | algorithm_type
```

**Storage Locations:**
1. `prompts.txt` - Append new prompts (deduplicated)
2. Database (if using MongoDB/SQLite):
   - Table: `prompts` or Collection: `prompts`
   - Fields: `prompt`, `algorithm_type`, `source`, `fetched_at`, `score`

**Deduplication:**
- Normalize prompts (lowercase, remove extra spaces)
- Use similarity matching (Levenshtein distance < 0.1)
- Check against existing prompts in database

### Phase 5: Weekly Update Schedule

**Cron Job / Scheduled Task:**
```bash
# Run every Monday at 2 AM
0 2 * * 1 python scripts/fetch_prompts_from_internet.py
```

**Update Strategy:**
1. Fetch new questions from all sources
2. Process and filter
3. Deduplicate against existing database
4. Add new prompts to `prompts.txt`
5. Update database
6. Commit changes (if using git)
7. Send summary email/log report

## Implementation Example

### Stack Overflow API Example

```python
import requests
from datetime import datetime, timedelta

def fetch_stackoverflow_questions(days=7):
    """Fetch ML questions from Stack Overflow."""
    since_date = int((datetime.now() - timedelta(days=days)).timestamp())
    
    url = "https://api.stackexchange.com/2.3/questions"
    params = {
        "fromdate": since_date,
        "order": "desc",
        "sort": "votes",
        "tagged": "machine-learning",
        "site": "stackoverflow",
        "filter": "default",
        "pagesize": 100
    }
    
    response = requests.get(url, params=params)
    data = response.json()
    
    questions = []
    for item in data.get("items", []):
        if item["score"] > 0:  # Only upvoted questions
            questions.append({
                "prompt": item["title"],
                "body": item.get("body", ""),
                "tags": item.get("tags", []),
                "score": item["score"],
                "source": "stackoverflow"
            })
    
    return questions
```

### Reddit API Example (PRAW)

```python
import praw

def fetch_reddit_questions():
    """Fetch ML questions from Reddit."""
    reddit = praw.Reddit(
        client_id="YOUR_CLIENT_ID",
        client_secret="YOUR_CLIENT_SECRET",
        user_agent="ML-Prompt-Fetcher"
    )
    
    questions = []
    subreddits = ["MachineLearning", "learnmachinelearning", "datascience"]
    
    for subreddit_name in subreddits:
        subreddit = reddit.subreddit(subreddit_name)
        for submission in subreddit.top("week", limit=50):
            if submission.score > 5:  # Minimum score threshold
                questions.append({
                    "prompt": submission.title,
                    "score": submission.score,
                    "source": f"reddit/{subreddit_name}"
                })
    
    return questions
```

## Recommended Libraries

1. **`requests`** - HTTP requests for APIs
2. **`praw`** - Reddit API wrapper
3. **`beautifulsoup4`** - HTML parsing (for scraping)
4. **`thefuzz`** - Fuzzy string matching for deduplication
5. **`schedule`** or **`APScheduler`** - Task scheduling

## Rate Limiting & Ethics

**Important Considerations:**

1. **Respect API Rate Limits:**
   - Stack Overflow: 300 requests/day per IP
   - Reddit: 60 requests/minute
   - Add delays between requests

2. **Terms of Service:**
   - Check ToS for each platform
   - Some sites prohibit automated scraping
   - Prefer official APIs when available

3. **Attribution:**
   - Store source URL/ID for attribution
   - Consider adding source metadata

## Weekly Update Script Structure

```python
#!/usr/bin/env python3
"""
Fetch AI/ML questions from internet sources and update prompts database.
Run weekly via cron: 0 2 * * 1
"""

def main():
    # 1. Fetch from all sources
    all_questions = []
    all_questions.extend(fetch_stackoverflow_questions())
    all_questions.extend(fetch_reddit_questions())
    # ... other sources
    
    # 2. Process and filter
    processed = process_questions(all_questions)
    
    # 3. Deduplicate against existing
    new_prompts = deduplicate(processed, existing_prompts)
    
    # 4. Categorize
    categorized = categorize_prompts(new_prompts)
    
    # 5. Update files and database
    update_prompts_file(categorized)
    update_database(categorized)
    
    # 6. Generate report
    generate_report(new_prompts)

if __name__ == "__main__":
    main()
```

## Metrics & Monitoring

Track:
- Number of new prompts fetched per week
- Number of duplicates filtered
- Distribution by algorithm type
- Source distribution
- Update success/failure

## Future Enhancements

1. **Machine Learning Classification:**
   - Train a model to automatically categorize questions
   - Improve accuracy over keyword matching

2. **Quality Improvement:**
   - Use LLM (GPT-4, Claude) to rephrase questions
   - Generate variations of popular questions

3. **Multi-language Support:**
   - Fetch questions in multiple languages
   - Translate and add to database

4. **Community Feedback:**
   - Allow users to submit questions
   - Upvote/downvote prompts for quality

