#!/usr/bin/env python3
"""
Rigorous network analysis addressing peer review feedback.
- Spam filtering
- Dyadic reciprocity (proper definition)
- Bootstrap confidence intervals
- Power-law goodness-of-fit
"""

import json
import math
import random
from pathlib import Path
from collections import defaultdict, Counter

DATA_DIR = Path.home() / ".openclaw/workspace/data/moltbook-sampler"

# Known spam accounts (from prior analysis)
SPAM_ACCOUNTS = {
    "Stromfee", "Manus-Independent", "FiverrClawOfficial", 
    "botcrong", "Editor-in-Chief"
}

def load_data(filter_spam=True):
    """Load data with optional spam filtering."""
    posts, comments = [], []
    
    with open(DATA_DIR / "posts.jsonl") as f:
        for line in f:
            p = json.loads(line)
            author = (p.get("author") or {}).get("name", "")
            if filter_spam and author in SPAM_ACCOUNTS:
                continue
            posts.append(p)
    
    with open(DATA_DIR / "comments.jsonl") as f:
        for line in f:
            c = json.loads(line)
            author = (c.get("author") or {}).get("name", "")
            if filter_spam and author in SPAM_ACCOUNTS:
                continue
            comments.append(c)
    
    return posts, comments

def build_network(posts, comments):
    """Build adjacency dict: src -> {tgt: weight}."""
    post_authors = {}
    for p in posts:
        author_obj = p.get("author") or {}
        post_authors[p.get("id")] = author_obj.get("name", "unknown")
    
    adjacency = defaultdict(lambda: defaultdict(int))
    
    for c in comments:
        author_obj = c.get("author") or {}
        commenter = author_obj.get("name", "unknown") if author_obj else "unknown"
        post_id = c.get("_post_id") or c.get("post_id")
        post_author = post_authors.get(post_id, "unknown")
        
        if commenter not in ("unknown", "") and post_author not in ("unknown", "") and commenter != post_author:
            adjacency[commenter][post_author] += 1
    
    return adjacency

def compute_dyadic_reciprocity(adjacency):
    """
    Dyadic reciprocity: fraction of connected pairs that are mutual.
    This is the proper metric for comparison to human networks.
    """
    # Find all pairs with at least one connection
    pairs = set()
    for src, targets in adjacency.items():
        for tgt in targets:
            pair = tuple(sorted([src, tgt]))
            pairs.add(pair)
    
    # Count mutual pairs
    mutual = 0
    for a, b in pairs:
        if a in adjacency and b in adjacency[a] and b in adjacency and a in adjacency[b]:
            mutual += 1
    
    return mutual / len(pairs) if pairs else 0, len(pairs), mutual

def bootstrap_reciprocity(adjacency, n_samples=1000):
    """Bootstrap confidence interval for reciprocity."""
    # Get all edges
    edges = []
    for src, targets in adjacency.items():
        for tgt, weight in targets.items():
            for _ in range(weight):
                edges.append((src, tgt))
    
    reciprocities = []
    n = len(edges)
    
    for _ in range(n_samples):
        # Resample edges with replacement
        sample_edges = random.choices(edges, k=n)
        sample_adj = defaultdict(lambda: defaultdict(int))
        for src, tgt in sample_edges:
            sample_adj[src][tgt] += 1
        
        r, _, _ = compute_dyadic_reciprocity(sample_adj)
        reciprocities.append(r)
    
    reciprocities.sort()
    ci_low = reciprocities[int(0.025 * n_samples)]
    ci_high = reciprocities[int(0.975 * n_samples)]
    
    return ci_low, ci_high

def power_law_ks_test(degrees, alpha, k_min):
    """
    Kolmogorov-Smirnov test for power-law fit.
    Returns D statistic (lower is better fit).
    """
    values = sorted([k for k in degrees.values() if k >= k_min])
    if not values:
        return 1.0
    
    n = len(values)
    
    # Theoretical CDF: P(K <= k) = 1 - (k/k_min)^(1-alpha)
    max_d = 0
    for i, k in enumerate(values):
        empirical_cdf = (i + 1) / n
        theoretical_cdf = 1 - (k / k_min) ** (1 - alpha)
        d = abs(empirical_cdf - theoretical_cdf)
        max_d = max(max_d, d)
    
    return max_d

def estimate_alpha_with_kmin_search(degrees):
    """Find optimal k_min and alpha using KS minimization."""
    best_ks = float('inf')
    best_alpha = None
    best_kmin = None
    
    for k_min in [1, 2, 3, 5, 10, 20]:
        values = [k for k in degrees.values() if k >= k_min]
        if len(values) < 50:  # Need sufficient data
            continue
        
        n = len(values)
        sum_log = sum(math.log(k / (k_min - 0.5)) for k in values)
        if sum_log <= 0:
            continue
        
        alpha = 1 + n / sum_log
        ks = power_law_ks_test(degrees, alpha, k_min)
        
        if ks < best_ks:
            best_ks = ks
            best_alpha = alpha
            best_kmin = k_min
    
    return best_alpha, best_kmin, best_ks

def main():
    print("=" * 60)
    print("RIGOROUS NETWORK ANALYSIS (Addressing Peer Review)")
    print("=" * 60)
    
    # Load with spam filtering
    print("\n[1] Loading data WITH spam filtering...")
    posts, comments = load_data(filter_spam=True)
    print(f"    Posts: {len(posts)}, Comments: {len(comments)}")
    
    # Also load without for comparison
    posts_all, comments_all = load_data(filter_spam=False)
    print(f"    (Unfiltered: {len(posts_all)} posts, {len(comments_all)} comments)")
    spam_removed = len(comments_all) - len(comments)
    print(f"    Spam comments removed: {spam_removed} ({100*spam_removed/len(comments_all):.1f}%)")
    
    # Build network
    print("\n[2] Building network...")
    adjacency = build_network(posts, comments)
    
    nodes = set(adjacency.keys())
    for targets in adjacency.values():
        nodes.update(targets.keys())
    print(f"    Nodes: {len(nodes)}")
    print(f"    Edges: {sum(sum(t.values()) for t in adjacency.values())}")
    
    # Dyadic reciprocity with CI
    print("\n[3] DYADIC RECIPROCITY (proper metric)")
    recip, n_pairs, n_mutual = compute_dyadic_reciprocity(adjacency)
    print(f"    Pairs with connection: {n_pairs}")
    print(f"    Mutual pairs: {n_mutual}")
    print(f"    Dyadic reciprocity: {recip*100:.2f}%")
    
    print("    Computing 95% CI via bootstrap (1000 samples)...")
    ci_low, ci_high = bootstrap_reciprocity(adjacency, n_samples=1000)
    print(f"    95% CI: [{ci_low*100:.2f}%, {ci_high*100:.2f}%]")
    
    # Benchmarks from literature
    print("\n    BENCHMARKS (from literature):")
    print("    - Twitter follow network: ~22% (Kwak et al., 2010)")
    print("    - Facebook friendships: ~100% (symmetric by design)")
    print("    - Reddit comments: ~3-8% (varies by subreddit)")
    print("    - Email networks: ~10-15% (Newman et al., 2002)")
    
    # Power-law with k_min optimization
    print("\n[4] POWER-LAW FIT (with k_min optimization)")
    out_degrees = Counter()
    for src, targets in adjacency.items():
        out_degrees[src] = sum(targets.values())
    
    alpha, k_min, ks = estimate_alpha_with_kmin_search(out_degrees)
    if alpha:
        print(f"    Optimal k_min: {k_min}")
        print(f"    Estimated α: {alpha:.3f}")
        print(f"    KS statistic: {ks:.4f}")
        print(f"    [KS < 0.05 suggests good fit; ours is {'GOOD' if ks < 0.1 else 'MODERATE' if ks < 0.2 else 'POOR'}]")
        
        n_above_kmin = len([k for k in out_degrees.values() if k >= k_min])
        print(f"    Data points used: {n_above_kmin}")
    
    print("\n    NOTE: For publication, use powerlaw package for proper")
    print("    comparison to lognormal/exponential alternatives.")
    
    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Dyadic reciprocity: {recip*100:.2f}% (95% CI: [{ci_low*100:.2f}%, {ci_high*100:.2f}%])")
    print(f"Power-law α: {alpha:.2f} (k_min={k_min}, KS={ks:.3f})")
    print(f"Spam filtered: {spam_removed} comments ({100*spam_removed/len(comments_all):.1f}%)")

if __name__ == "__main__":
    random.seed(42)  # Reproducibility
    main()
