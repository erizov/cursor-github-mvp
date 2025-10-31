#!/usr/bin/env python3
"""
Fetch AI/ML questions from internet sources and update prompts database.

This script fetches questions from Stack Overflow, Reddit, and other sources,
processes them, and adds new prompts to prompts.txt and the database.

Run weekly via cron: 0 2 * * 1 (every Monday at 2 AM)
"""

from __future__ import annotations

import os
import sys
import re
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Tuple
import time

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    import requests
except ImportError:
    print("Error: requests library not installed. Install with: pip install requests")
    sys.exit(1)

from backend.services import get_algorithm_type_from_algorithm


# Configuration
STACKOVERFLOW_API_BASE = "https://api.stackexchange.com/2.3"
MAX_QUESTIONS_PER_SOURCE = 100
MIN_QUESTION_LENGTH = 20
MAX_QUESTION_LENGTH = 500
DAYS_TO_FETCH = 7
MAX_TOTAL_PROMPTS = 30000  # Maximum total prompts to keep


def normalize_prompt(text: str) -> str:
    """Normalize prompt text for deduplication."""
    # Remove HTML tags
    text = re.sub(r'<[^>]+>', '', text)
    # Normalize whitespace
    text = ' '.join(text.split())
    # Lowercase
    return text.lower().strip()


def is_valid_question(text: str) -> bool:
    """Check if question is valid for our purposes."""
    normalized = normalize_prompt(text)
    
    # Length check
    if len(normalized) < MIN_QUESTION_LENGTH or len(normalized) > MAX_QUESTION_LENGTH:
        return False
    
    # Must contain ML/AI keywords
    keywords = [
        'machine learning', 'ml', 'algorithm', 'model', 'neural',
        'classify', 'predict', 'cluster', 'regression', 'classification',
        'deep learning', 'ai', 'data science', 'training'
    ]
    
    if not any(keyword in normalized for keyword in keywords):
        return False
    
    # Should be a question (contains question words or ends with ?)
    question_words = ['how', 'what', 'which', 'why', 'when', 'where', '?']
    if not any(word in normalized for word in question_words):
        return False
    
    return True


def fetch_stackoverflow_questions(days: int = DAYS_TO_FETCH) -> List[Dict]:
    """Fetch ML questions from Stack Overflow."""
    since_date = int((datetime.now() - timedelta(days=days)).timestamp())
    
    questions = []
    page = 1
    max_pages = 10
    
    ml_tags = ['machine-learning', 'artificial-intelligence', 'data-science']
    
    for tag in ml_tags:
        if len(questions) >= MAX_QUESTIONS_PER_SOURCE:
            break
        
        while page <= max_pages and len(questions) < MAX_QUESTIONS_PER_SOURCE:
            url = f"{STACKOVERFLOW_API_BASE}/questions"
            params = {
                "fromdate": since_date,
                "order": "desc",
                "sort": "votes",
                "tagged": tag,
                "site": "stackoverflow",
                "filter": "default",
                "pagesize": 100,
                "page": page
            }
            
            try:
                response = requests.get(url, params=params, timeout=10)
                response.raise_for_status()
                data = response.json()
                
                items = data.get("items", [])
                if not items:
                    break
                
                for item in items:
                    title = item.get("title", "")
                    body = item.get("body", "")
                    full_text = f"{title} {body}"
                    
                    if is_valid_question(full_text):
                        questions.append({
                            "prompt": title[:MAX_QUESTION_LENGTH],
                            "score": item.get("score", 0),
                            "source": f"stackoverflow/{tag}",
                            "url": item.get("link", "")
                        })
                
                # Respect rate limits
                if data.get("has_more", False):
                    time.sleep(0.1)  # Small delay between requests
                    page += 1
                else:
                    break
                    
            except requests.RequestException as e:
                print(f"Error fetching Stack Overflow questions: {e}")
                break
    
    return questions


def categorize_prompt(prompt: str) -> str:
    """Categorize a prompt using existing algorithm type function."""
    # Try to extract algorithm name from prompt, or use the prompt itself
    # This is a simplified version - you might want to enhance it
    prompt_lower = prompt.lower()
    
    # Try common algorithm mentions
    algorithm_map = {
        'classification': 'Classification',
        'classify': 'Classification',
        'regression': 'Regression',
        'predict': 'Regression',
        'cluster': 'Clustering',
        'clustering': 'Clustering',
        'neural network': 'Deep Learning',
        'deep learning': 'Deep Learning',
        'nlp': 'NLP',
        'natural language': 'NLP',
        'computer vision': 'Vision',
        'reinforcement': 'Reinforcement Learning',
    }
    
    for key, alg_type in algorithm_map.items():
        if key in prompt_lower:
            return alg_type
    
    # Use the service function with a dummy algorithm name
    # We'll try to infer from the prompt text
    return get_algorithm_type_from_algorithm(prompt)


def deduplicate_prompts(
    new_prompts: List[Dict],
    existing_prompts_path: Path
) -> List[Dict]:
    """Remove duplicates by checking against existing prompts file."""
    if not existing_prompts_path.exists():
        return new_prompts
    
    # Load existing prompts
    existing_normalized = set()
    try:
        with open(existing_prompts_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if '|' in line:
                    prompt = line.split('|')[0].strip()
                    existing_normalized.add(normalize_prompt(prompt))
    except Exception as e:
        print(f"Warning: Could not read existing prompts: {e}")
    
    # Filter out duplicates
    unique_new = []
    seen_normalized = set(existing_normalized)
    
    for prompt_data in new_prompts:
        normalized = normalize_prompt(prompt_data["prompt"])
        if normalized not in seen_normalized:
            unique_new.append(prompt_data)
            seen_normalized.add(normalized)
    
    return unique_new


def get_current_prompt_count(prompts_path: Path) -> int:
    """Get current number of prompts in file."""
    if not prompts_path.exists():
        return 0
    
    try:
        count = 0
        with open(prompts_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and '|' in line:
                    count += 1
        return count
    except Exception as e:
        print(f"Warning: Could not count existing prompts: {e}")
        return 0


def update_prompts_file(
    prompts: List[Dict],
    prompts_path: Path,
    max_total: int = MAX_TOTAL_PROMPTS
) -> None:
    """Add new prompts to prompts.txt file, keeping total under max_total."""
    if not prompts:
        return
    
    current_count = get_current_prompt_count(prompts_path)
    
    if current_count >= max_total:
        print(f"Already at max prompts ({current_count}/{max_total}). Skipping addition.")
        return
    
    # Calculate how many we can add
    available_slots = max_total - current_count
    prompts_to_add = prompts[:available_slots]
    
    if len(prompts_to_add) < len(prompts):
        print(f"Limited additions to {len(prompts_to_add)} prompts to stay under {max_total} limit.")
    
    try:
        # Append new prompts
        with open(prompts_path, 'a', encoding='utf-8') as f:
            for prompt_data in prompts_to_add:
                prompt = prompt_data["prompt"]
                # Skip prompts with "Other" category
                algo_type = prompt_data.get("algorithm_type", "Other")
                if algo_type == "Other":
                    continue
                algorithm_type = algo_type
                f.write(f"{prompt}|{algorithm_type}\n")
        
        new_count = get_current_prompt_count(prompts_path)
        print(f"Added {len(prompts_to_add)} new prompts to {prompts_path}")
        print(f"Total prompts: {current_count} -> {new_count} (max: {max_total})")
    except Exception as e:
        print(f"Error writing to prompts file: {e}")


def main():
    """Main function to fetch and process prompts."""
    project_root = Path(__file__).parent.parent
    prompts_path = project_root / "prompts.txt"
    
    print(f"Fetching AI/ML questions from last {DAYS_TO_FETCH} days...")
    print("=" * 60)
    
    # Fetch from all sources
    all_questions = []
    
    print("\n1. Fetching from Stack Overflow...")
    so_questions = fetch_stackoverflow_questions()
    all_questions.extend(so_questions)
    print(f"   Fetched {len(so_questions)} questions from Stack Overflow")
    
    # TODO: Add other sources (Reddit, etc.)
    # print("\n2. Fetching from Reddit...")
    # reddit_questions = fetch_reddit_questions()
    # all_questions.extend(reddit_questions)
    
    print(f"\nTotal questions fetched: {len(all_questions)}")
    
    # Filter valid questions
    print("\n2. Filtering valid questions...")
    valid_questions = [q for q in all_questions if is_valid_question(q["prompt"])]
    print(f"   Valid questions: {len(valid_questions)}")
    
    # Deduplicate
    print("\n3. Deduplicating against existing prompts...")
    unique_questions = deduplicate_prompts(valid_questions, prompts_path)
    print(f"   New unique questions: {len(unique_questions)}")
    
    if not unique_questions:
        print("\nNo new prompts to add. Exiting.")
        return
    
    # Categorize and filter out "Other"
    print("\n4. Categorizing prompts and filtering out 'Other' category...")
    categorized = []
    for q in unique_questions:
        algo_type = categorize_prompt(q["prompt"])
        # Exclude "Other" category
        if algo_type != "Other":
            q["algorithm_type"] = algo_type
            categorized.append(q)
    
    # Show distribution
    from collections import Counter
    category_counts = Counter(q["algorithm_type"] for q in categorized)
    print("\n   Category distribution:")
    for cat, count in category_counts.most_common():
        print(f"      {cat}: {count}")
    
    # Update prompts file
    print("\n5. Updating prompts.txt...")
    update_prompts_file(categorized, prompts_path, MAX_TOTAL_PROMPTS)
    
    # TODO: Update database if using MongoDB/SQLite
    # print("\n6. Updating database...")
    # update_database(categorized)
    
    print("\n" + "=" * 60)
    print(f"✓ Successfully added {len(categorized)} new prompts!")
    print(f"  Total prompts in file: {sum(1 for _ in open(prompts_path)) if prompts_path.exists() else 0}")


if __name__ == "__main__":
    main()

