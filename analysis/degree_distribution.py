#!/usr/bin/env python3
"""
Degree distribution analysis with power-law fitting.
Tests if Moltbook network follows scale-free properties.
"""

import json
import math
from pathlib import Path
from collections import defaultdict, Counter

DATA_DIR = Path.home() / ".openclaw/workspace/data/moltbook-sampler"

def load_data():
    """Load posts and comments."""
    posts, comments = [], []
    
    with open(DATA_DIR / "posts.jsonl") as f:
        for line in f:
            posts.append(json.loads(line))
    
    with open(DATA_DIR / "comments.jsonl") as f:
        for line in f:
            comments.append(json.loads(line))
    
    return posts, comments

def build_network(posts, comments):
    """Build comment network: commenter -> post author."""
    post_authors = {}
    for p in posts:
        author_obj = p.get("author") or {}
        post_authors[p.get("id")] = author_obj.get("name", "unknown")
    
    out_degree = Counter()
    in_degree = Counter()
    
    for c in comments:
        author_obj = c.get("author") or {}
        commenter = author_obj.get("name", "unknown") if author_obj else "unknown"
        post_id = c.get("_post_id") or c.get("post_id")
        post_author = post_authors.get(post_id, "unknown")
        
        if commenter != "unknown" and post_author != "unknown" and commenter != post_author:
            out_degree[commenter] += 1
            in_degree[post_author] += 1
    
    return out_degree, in_degree

def degree_distribution(degrees):
    """Compute P(k) - fraction of nodes with degree k."""
    counts = Counter(degrees.values())
    total = len(degrees)
    return {k: count / total for k, count in sorted(counts.items())}

def estimate_power_law_exponent(degrees, k_min=1):
    """
    Estimate power-law exponent using MLE (Newman 2005).
    P(k) ~ k^(-alpha)
    alpha = 1 + n * (sum(ln(k_i / k_min)))^(-1)
    """
    values = [k for k in degrees.values() if k >= k_min]
    if not values:
        return None, 0
    
    n = len(values)
    sum_log = sum(math.log(k / (k_min - 0.5)) for k in values)
    
    if sum_log == 0:
        return None, n
    
    alpha = 1 + n / sum_log
    return alpha, n

def compute_gini(degrees):
    """Compute Gini coefficient for degree inequality."""
    values = sorted(degrees.values())
    n = len(values)
    if n == 0:
        return 0
    
    cumsum = 0
    for i, v in enumerate(values):
        cumsum += (2 * (i + 1) - n - 1) * v
    
    return cumsum / (n * sum(values)) if sum(values) > 0 else 0

def main():
    print("Loading data...")
    posts, comments = load_data()
    print(f"Loaded {len(posts)} posts, {len(comments)} comments\n")
    
    print("Building network...")
    out_degree, in_degree = build_network(posts, comments)
    
    print(f"\n=== Degree Statistics ===")
    print(f"Unique nodes (out): {len(out_degree)}")
    print(f"Unique nodes (in): {len(in_degree)}")
    
    # Out-degree analysis
    print(f"\n=== Out-Degree (commenting activity) ===")
    out_vals = list(out_degree.values())
    print(f"  Mean: {sum(out_vals)/len(out_vals):.2f}")
    print(f"  Median: {sorted(out_vals)[len(out_vals)//2]}")
    print(f"  Max: {max(out_vals)}")
    
    alpha_out, n_out = estimate_power_law_exponent(out_degree, k_min=2)
    if alpha_out:
        print(f"  Power-law exponent (α): {alpha_out:.3f} (n={n_out})")
        print(f"  [Typical range: 2-3 for social networks]")
    
    gini_out = compute_gini(out_degree)
    print(f"  Gini coefficient: {gini_out:.3f}")
    
    # In-degree analysis
    print(f"\n=== In-Degree (attention received) ===")
    in_vals = list(in_degree.values())
    print(f"  Mean: {sum(in_vals)/len(in_vals):.2f}")
    print(f"  Median: {sorted(in_vals)[len(in_vals)//2]}")
    print(f"  Max: {max(in_vals)}")
    
    alpha_in, n_in = estimate_power_law_exponent(in_degree, k_min=2)
    if alpha_in:
        print(f"  Power-law exponent (α): {alpha_in:.3f} (n={n_in})")
    
    gini_in = compute_gini(in_degree)
    print(f"  Gini coefficient: {gini_in:.3f}")
    
    # Top nodes
    print(f"\n=== Top 10 by Out-Degree (most active commenters) ===")
    for name, deg in out_degree.most_common(10):
        print(f"  {name}: {deg}")
    
    print(f"\n=== Top 10 by In-Degree (most attention) ===")
    for name, deg in in_degree.most_common(10):
        print(f"  {name}: {deg}")
    
    # Distribution tail
    print(f"\n=== Distribution Shape ===")
    out_dist = degree_distribution(out_degree)
    k1_frac = out_dist.get(1, 0)
    k_gt10 = sum(v for k, v in out_dist.items() if k > 10)
    print(f"  Nodes with out-degree=1: {k1_frac*100:.1f}%")
    print(f"  Nodes with out-degree>10: {k_gt10*100:.1f}%")

if __name__ == "__main__":
    main()
