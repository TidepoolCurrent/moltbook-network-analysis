#!/usr/bin/env python3
"""
Temporal analysis for Moltbook network.
Analyzes time-based patterns in agent activity.
"""

import json
from pathlib import Path
from collections import defaultdict, Counter
from datetime import datetime, timezone
import statistics

DATA_DIR = Path.home() / ".openclaw/workspace/data/moltbook-sampler"

def parse_timestamp(ts_str):
    """Parse ISO timestamp to datetime."""
    if not ts_str:
        return None
    try:
        # Handle various formats
        ts_str = ts_str.replace('Z', '+00:00')
        return datetime.fromisoformat(ts_str)
    except:
        return None

def load_data_with_times():
    """Load posts and comments with timestamps."""
    posts = []
    comments = []
    
    posts_file = DATA_DIR / "posts.jsonl"
    comments_file = DATA_DIR / "comments.jsonl"
    
    if posts_file.exists():
        with open(posts_file) as f:
            for line in f:
                p = json.loads(line)
                p['_parsed_time'] = parse_timestamp(p.get('created_at'))
                if p['_parsed_time']:
                    posts.append(p)
    
    if comments_file.exists():
        with open(comments_file) as f:
            for line in f:
                c = json.loads(line)
                c['_parsed_time'] = parse_timestamp(c.get('created_at'))
                if c['_parsed_time']:
                    comments.append(c)
    
    return posts, comments

def analyze_time_distribution(items, label="items"):
    """Analyze temporal distribution of items."""
    if not items:
        return {}
    
    times = [i['_parsed_time'] for i in items if i.get('_parsed_time')]
    if not times:
        return {}
    
    # Sort by time
    times.sort()
    
    # Time range
    earliest = min(times)
    latest = max(times)
    span_days = (latest - earliest).total_seconds() / 86400
    
    # Hour of day distribution (UTC)
    hours = Counter(t.hour for t in times)
    
    # Day of week distribution
    days = Counter(t.strftime('%A') for t in times)
    
    # Daily activity
    daily = Counter(t.strftime('%Y-%m-%d') for t in times)
    
    return {
        "count": len(times),
        "earliest": earliest.isoformat(),
        "latest": latest.isoformat(),
        "span_days": round(span_days, 2),
        "items_per_day": round(len(times) / max(span_days, 1), 2),
        "peak_hour_utc": hours.most_common(1)[0] if hours else None,
        "peak_day": days.most_common(1)[0] if days else None,
        "hour_distribution": dict(sorted(hours.items())),
        "daily_counts": dict(sorted(daily.items())[-7:]),  # Last 7 days
    }

def analyze_activity_patterns(posts, comments):
    """Analyze 24/7 vs human-like patterns."""
    all_items = posts + comments
    times = [i['_parsed_time'] for i in all_items if i.get('_parsed_time')]
    
    if not times:
        return {}
    
    hours = Counter(t.hour for t in times)
    total = sum(hours.values())
    
    # Check if activity is uniform (24/7) or has peaks (human-like)
    hour_fractions = [hours.get(h, 0) / total for h in range(24)]
    
    # Expected uniform: 1/24 = 0.0417 per hour
    # Calculate variance from uniform
    expected = 1/24
    variance = sum((f - expected)**2 for f in hour_fractions) / 24
    
    # Coefficient of variation
    mean_frac = statistics.mean(hour_fractions)
    std_frac = statistics.stdev(hour_fractions) if len(hour_fractions) > 1 else 0
    cv = std_frac / mean_frac if mean_frac > 0 else 0
    
    # Find quiet hours (< 50% of mean)
    quiet_hours = [h for h in range(24) if hour_fractions[h] < mean_frac * 0.5]
    busy_hours = [h for h in range(24) if hour_fractions[h] > mean_frac * 1.5]
    
    return {
        "variance_from_uniform": round(variance, 6),
        "coefficient_of_variation": round(cv, 3),
        "pattern": "24/7 uniform" if cv < 0.3 else "human-like peaks",
        "quiet_hours_utc": quiet_hours,
        "busy_hours_utc": busy_hours,
        "busiest_hour_utc": max(range(24), key=lambda h: hours.get(h, 0)),
        "quietest_hour_utc": min(range(24), key=lambda h: hours.get(h, 0)),
    }

def analyze_growth_curve(posts, comments):
    """Analyze cumulative growth over time."""
    all_items = [(i['_parsed_time'], 'post' if 'title' in i else 'comment') 
                 for i in posts + comments if i.get('_parsed_time')]
    all_items.sort()
    
    if not all_items:
        return {}
    
    # Cumulative counts by day
    daily_cumulative = {}
    post_count = 0
    comment_count = 0
    
    for ts, typ in all_items:
        day = ts.strftime('%Y-%m-%d')
        if typ == 'post':
            post_count += 1
        else:
            comment_count += 1
        daily_cumulative[day] = {'posts': post_count, 'comments': comment_count}
    
    # Growth rate (items per day over last 7 days vs first 7 days)
    days = sorted(daily_cumulative.keys())
    if len(days) >= 14:
        first_week = [daily_cumulative[d]['posts'] + daily_cumulative[d]['comments'] for d in days[:7]]
        last_week = [daily_cumulative[d]['posts'] + daily_cumulative[d]['comments'] for d in days[-7:]]
        first_rate = (first_week[-1] - first_week[0]) / 7 if len(first_week) > 1 else 0
        last_rate = (last_week[-1] - last_week[0]) / 7 if len(last_week) > 1 else 0
        acceleration = last_rate - first_rate
    else:
        first_rate = last_rate = acceleration = None
    
    return {
        "total_days": len(days),
        "first_day": days[0] if days else None,
        "last_day": days[-1] if days else None,
        "final_posts": post_count,
        "final_comments": comment_count,
        "first_week_rate": round(first_rate, 2) if first_rate else None,
        "last_week_rate": round(last_rate, 2) if last_rate else None,
        "acceleration": round(acceleration, 2) if acceleration else None,
    }

def main():
    print("Loading data with timestamps...")
    posts, comments = load_data_with_times()
    print(f"Loaded {len(posts)} posts, {len(comments)} comments with valid timestamps\n")
    
    print("=== Post Temporal Distribution ===")
    post_stats = analyze_time_distribution(posts, "posts")
    for k, v in post_stats.items():
        if k not in ['hour_distribution', 'daily_counts']:
            print(f"  {k}: {v}")
    
    print("\n=== Comment Temporal Distribution ===")
    comment_stats = analyze_time_distribution(comments, "comments")
    for k, v in comment_stats.items():
        if k not in ['hour_distribution', 'daily_counts']:
            print(f"  {k}: {v}")
    
    print("\n=== Activity Pattern Analysis ===")
    patterns = analyze_activity_patterns(posts, comments)
    for k, v in patterns.items():
        print(f"  {k}: {v}")
    
    print("\n=== Growth Curve ===")
    growth = analyze_growth_curve(posts, comments)
    for k, v in growth.items():
        print(f"  {k}: {v}")

if __name__ == "__main__":
    main()
