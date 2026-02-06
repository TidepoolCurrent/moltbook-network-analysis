#!/usr/bin/env python3
"""
Basic network statistics for Moltbook data.
Day 1: Methods development
"""

import json
from pathlib import Path
from collections import defaultdict, Counter
import statistics

DATA_DIR = Path.home() / ".openclaw/workspace/data/moltbook-sampler"

def load_data():
    """Load posts and comments from JSONL files."""
    posts = []
    comments = []
    
    posts_file = DATA_DIR / "posts.jsonl"
    comments_file = DATA_DIR / "comments.jsonl"
    
    if posts_file.exists():
        with open(posts_file) as f:
            for line in f:
                posts.append(json.loads(line))
    
    if comments_file.exists():
        with open(comments_file) as f:
            for line in f:
                comments.append(json.loads(line))
    
    return posts, comments

def build_comment_network(posts, comments):
    """
    Build directed network: commenter -> post author.
    Returns adjacency dict and edge list.
    """
    # Map post_id to author
    post_authors = {}
    for p in posts:
        author_obj = p.get("author") or {}
        post_authors[p.get("id")] = author_obj.get("name", "unknown") if author_obj else "unknown"
    
    # Build edges
    edges = []
    adjacency = defaultdict(lambda: defaultdict(int))
    
    for c in comments:
        author_obj = c.get("author") or {}
        commenter = author_obj.get("name", "unknown") if author_obj else "unknown"
        post_id = c.get("_post_id") or c.get("post_id")
        post_author = post_authors.get(post_id, "unknown")
        
        if commenter != "unknown" and post_author != "unknown" and commenter != post_author:
            edges.append((commenter, post_author))
            adjacency[commenter][post_author] += 1
    
    return adjacency, edges

def compute_degree_stats(adjacency):
    """Compute in-degree and out-degree statistics."""
    out_degrees = defaultdict(int)
    in_degrees = defaultdict(int)
    
    for src, targets in adjacency.items():
        out_degrees[src] = sum(targets.values())
        for tgt, weight in targets.items():
            in_degrees[tgt] += weight
    
    all_nodes = set(out_degrees.keys()) | set(in_degrees.keys())
    
    out_vals = [out_degrees.get(n, 0) for n in all_nodes]
    in_vals = [in_degrees.get(n, 0) for n in all_nodes]
    
    return {
        "num_nodes": len(all_nodes),
        "num_edges": sum(out_vals),
        "out_degree_mean": statistics.mean(out_vals) if out_vals else 0,
        "out_degree_median": statistics.median(out_vals) if out_vals else 0,
        "out_degree_max": max(out_vals) if out_vals else 0,
        "in_degree_mean": statistics.mean(in_vals) if in_vals else 0,
        "in_degree_median": statistics.median(in_vals) if in_vals else 0,
        "in_degree_max": max(in_vals) if in_vals else 0,
    }

def compute_reciprocity(adjacency):
    """Compute reciprocity: fraction of edges that are reciprocated."""
    reciprocated = 0
    total = 0
    
    for src, targets in adjacency.items():
        for tgt in targets:
            total += 1
            if src in adjacency.get(tgt, {}):
                reciprocated += 1
    
    return reciprocated / total if total > 0 else 0

def compute_submolt_stats(posts, comments):
    """Statistics per submolt."""
    submolt_posts = Counter()
    submolt_comments = Counter()
    submolt_authors = defaultdict(set)
    
    for p in posts:
        submolt = p.get("_submolt", "unknown")
        submolt_posts[submolt] += 1
        author_obj = p.get("author") or {}
        author = author_obj.get("name") if author_obj else None
        if author:
            submolt_authors[submolt].add(author)
    
    for c in comments:
        submolt = c.get("_submolt", "unknown")
        submolt_comments[submolt] += 1
        author_obj = c.get("author") or {}
        author = author_obj.get("name") if author_obj else None
        if author:
            submolt_authors[submolt].add(author)
    
    return {
        "num_submolts": len(submolt_posts),
        "posts_per_submolt_mean": statistics.mean(submolt_posts.values()) if submolt_posts else 0,
        "comments_per_submolt_mean": statistics.mean(submolt_comments.values()) if submolt_comments else 0,
        "authors_per_submolt_mean": statistics.mean(len(v) for v in submolt_authors.values()) if submolt_authors else 0,
        "top_submolts_by_posts": submolt_posts.most_common(10),
        "top_submolts_by_comments": submolt_comments.most_common(10),
    }

def main():
    print("Loading data...")
    posts, comments = load_data()
    print(f"Loaded {len(posts)} posts, {len(comments)} comments\n")
    
    print("Building comment network...")
    adjacency, edges = build_comment_network(posts, comments)
    
    print("\n=== Network Statistics ===")
    degree_stats = compute_degree_stats(adjacency)
    for k, v in degree_stats.items():
        print(f"  {k}: {v:.2f}" if isinstance(v, float) else f"  {k}: {v}")
    
    print(f"\n=== Reciprocity ===")
    recip = compute_reciprocity(adjacency)
    print(f"  Reciprocity rate: {recip:.4f}")
    
    print("\n=== Submolt Statistics ===")
    submolt_stats = compute_submolt_stats(posts, comments)
    for k, v in submolt_stats.items():
        if isinstance(v, list):
            print(f"  {k}:")
            for item in v[:5]:
                print(f"    {item}")
        else:
            print(f"  {k}: {v:.2f}" if isinstance(v, float) else f"  {k}: {v}")

if __name__ == "__main__":
    main()
