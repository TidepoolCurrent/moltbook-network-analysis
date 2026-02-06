#!/usr/bin/env python3
"""
Run network analysis on exhaustive m/introductions archive.
Day 2 analysis for paper.
"""

import json
from pathlib import Path
from collections import defaultdict, Counter
import statistics
import sys

DATA_DIR = Path.home() / ".openclaw/workspace/data/moltbook-archive-v2"

# Stream loading for large files
def stream_load(filepath, limit=None):
    """Stream load JSONL, optionally with limit."""
    count = 0
    with open(filepath) as f:
        for line in f:
            if limit and count >= limit:
                break
            yield json.loads(line)
            count += 1

def main():
    posts_file = DATA_DIR / "posts_introductions.jsonl"
    comments_file = DATA_DIR / "comments_introductions.jsonl"
    
    print(f"Analyzing exhaustive m/introductions archive")
    print(f"Posts file: {posts_file}")
    print(f"Comments file: {comments_file}")
    
    # Count records
    print("\nCounting records...")
    post_count = sum(1 for _ in open(posts_file))
    comment_count = sum(1 for _ in open(comments_file))
    print(f"Posts: {post_count:,}")
    print(f"Comments: {comment_count:,}")
    print(f"Total: {post_count + comment_count:,}")
    
    # Load posts to map post_id -> author
    print("\nLoading posts...")
    post_authors = {}
    post_authors_set = set()
    for p in stream_load(posts_file):
        author_obj = p.get("author") or {}
        author = author_obj.get("name", "unknown") if author_obj else "unknown"
        post_authors[p.get("id")] = author
        if author != "unknown":
            post_authors_set.add(author)
    print(f"Unique post authors: {len(post_authors_set):,}")
    
    # Build network from comments
    print("\nBuilding comment network (streaming)...")
    adjacency = defaultdict(lambda: defaultdict(int))
    commenters = set()
    edge_count = 0
    
    for i, c in enumerate(stream_load(comments_file)):
        if i % 500000 == 0 and i > 0:
            print(f"  Processed {i:,} comments...")
        
        author_obj = c.get("author") or {}
        commenter = author_obj.get("name", "unknown") if author_obj else "unknown"
        post_id = c.get("_post_id") or c.get("post_id")
        post_author = post_authors.get(post_id, "unknown")
        
        if commenter != "unknown" and post_author != "unknown" and commenter != post_author:
            adjacency[commenter][post_author] += 1
            commenters.add(commenter)
            edge_count += 1
    
    all_nodes = post_authors_set | commenters
    print(f"Total unique agents: {len(all_nodes):,}")
    print(f"Total edges: {edge_count:,}")
    
    # Degree distributions
    print("\n=== Degree Statistics ===")
    out_degrees = defaultdict(int)
    in_degrees = defaultdict(int)
    
    for src, targets in adjacency.items():
        out_degrees[src] = sum(targets.values())
        for tgt, weight in targets.items():
            in_degrees[tgt] += weight
    
    out_vals = [out_degrees.get(n, 0) for n in all_nodes]
    in_vals = [in_degrees.get(n, 0) for n in all_nodes]
    
    print(f"Out-degree (comments given):")
    print(f"  Mean: {statistics.mean(out_vals):.2f}")
    print(f"  Median: {statistics.median(out_vals):.2f}")
    print(f"  Max: {max(out_vals)}")
    print(f"In-degree (comments received):")
    print(f"  Mean: {statistics.mean(in_vals):.2f}")
    print(f"  Median: {statistics.median(in_vals):.2f}")
    print(f"  Max: {max(in_vals)}")
    
    # Top commenters
    print("\n=== Top 10 Commenters (out-degree) ===")
    top_out = sorted(out_degrees.items(), key=lambda x: -x[1])[:10]
    for name, deg in top_out:
        print(f"  {name}: {deg:,}")
    
    # Most commented-on (in-degree)
    print("\n=== Top 10 Most Commented-On (in-degree) ===")
    top_in = sorted(in_degrees.items(), key=lambda x: -x[1])[:10]
    for name, deg in top_in:
        print(f"  {name}: {deg:,}")
    
    # Reciprocity
    print("\n=== Reciprocity ===")
    reciprocated = 0
    total = 0
    for src, targets in adjacency.items():
        for tgt in targets:
            total += 1
            if src in adjacency.get(tgt, {}):
                reciprocated += 1
    recip_rate = reciprocated / total if total > 0 else 0
    print(f"Reciprocated edges: {reciprocated:,} / {total:,}")
    print(f"Reciprocity rate: {recip_rate:.4f} ({recip_rate*100:.2f}%)")
    
    # Gini coefficient for out-degree
    print("\n=== Inequality (Gini) ===")
    sorted_out = sorted(out_vals)
    n = len(sorted_out)
    if n > 0:
        cumsum = sum((i + 1) * v for i, v in enumerate(sorted_out))
        gini = (2 * cumsum) / (n * sum(sorted_out)) - (n + 1) / n if sum(sorted_out) > 0 else 0
        print(f"Gini coefficient (out-degree): {gini:.4f}")
    
    # One-time engagers
    one_timers = sum(1 for v in out_vals if v == 1)
    print(f"\nOne-time commenters: {one_timers:,} ({one_timers/len(out_vals)*100:.1f}%)")
    
    # Power law exponent estimate (via MLE)
    print("\n=== Power Law Analysis ===")
    nonzero_out = [v for v in out_vals if v > 0]
    if nonzero_out:
        xmin = 1
        alpha = 1 + len(nonzero_out) / sum(log(v / xmin) for v in nonzero_out if v >= xmin)
        print(f"Estimated power-law exponent (α): {alpha:.2f}")
    
    print("\n=== Summary for Paper ===")
    print(f"Dataset: m/introductions (exhaustive)")
    print(f"Records: {post_count + comment_count:,}")
    print(f"Unique agents: {len(all_nodes):,}")
    print(f"Network edges: {edge_count:,}")
    print(f"Reciprocity: {recip_rate*100:.2f}%")
    print(f"Gini: {gini:.4f}")
    print(f"One-time commenters: {one_timers/len(out_vals)*100:.1f}%")

from math import log

if __name__ == "__main__":
    main()
