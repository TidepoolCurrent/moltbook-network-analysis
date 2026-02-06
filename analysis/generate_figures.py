#!/usr/bin/env python3
"""
Generate figures for the paper.
"""

import json
from collections import Counter, defaultdict
from pathlib import Path
import math

DATA_DIR = Path.home() / ".openclaw/workspace/data/moltbook-fast"
OUT_DIR = Path.home() / ".openclaw/workspace/moltbook-paper/figures"

def load_data():
    posts = [json.loads(l) for l in open(DATA_DIR / "posts.jsonl")]
    comments = [json.loads(l) for l in open(DATA_DIR / "comments.jsonl")]
    return posts, comments

def build_network(posts, comments):
    post_authors = {}
    for p in posts:
        author = (p.get('author') or {}).get('name', 'unknown')
        post_authors[p.get('id')] = author
    
    out_degrees = defaultdict(int)
    in_degrees = defaultdict(int)
    
    for c in comments:
        commenter = (c.get('author') or {}).get('name', 'unknown')
        post_id = c.get('_post_id') or c.get('post_id')
        post_author = post_authors.get(post_id, 'unknown')
        
        if commenter != 'unknown' and post_author != 'unknown' and commenter != post_author:
            out_degrees[commenter] += 1
            in_degrees[post_author] += 1
    
    return out_degrees, in_degrees

def generate_degree_distribution_data(degrees, filename):
    """Generate data for degree distribution plot (log-log)."""
    counts = Counter(degrees.values())
    total = sum(counts.values())
    
    with open(OUT_DIR / filename, 'w') as f:
        f.write("degree,count,probability\n")
        for deg in sorted(counts.keys()):
            if deg > 0:
                f.write(f"{deg},{counts[deg]},{counts[deg]/total}\n")
    
    return counts

def generate_latex_table(posts, comments, out_degrees, in_degrees):
    """Generate LaTeX table for paper."""
    all_nodes = set(out_degrees.keys()) | set(in_degrees.keys())
    out_vals = [out_degrees.get(n, 0) for n in all_nodes]
    in_vals = [in_degrees.get(n, 0) for n in all_nodes]
    
    # Calculate stats
    n_submolts = len(set(p.get('_submolt') for p in posts))
    n_agents = len(all_nodes)
    n_posts = len(posts)
    n_comments = len(comments)
    
    mean_out = sum(out_vals) / len(out_vals) if out_vals else 0
    median_out = sorted(out_vals)[len(out_vals)//2] if out_vals else 0
    max_out = max(out_vals) if out_vals else 0
    
    latex = f"""
\\begin{{table}}[h]
\\centering
\\caption{{Dataset Summary}}
\\label{{tab:dataset}}
\\begin{{tabular}}{{lr}}
\\toprule
\\textbf{{Metric}} & \\textbf{{Value}} \\\\
\\midrule
Submolts sampled & {n_submolts} \\\\
Unique agents & {n_agents:,} \\\\
Posts & {n_posts:,} \\\\
Comments & {n_comments:,} \\\\
\\midrule
Mean out-degree & {mean_out:.2f} \\\\
Median out-degree & {median_out} \\\\
Max out-degree & {max_out} \\\\
\\bottomrule
\\end{{tabular}}
\\end{{table}}
"""
    
    with open(OUT_DIR / "table_dataset.tex", 'w') as f:
        f.write(latex)
    
    return latex

def generate_top_agents_table(out_degrees, in_degrees):
    """Generate table of top agents."""
    top_out = sorted(out_degrees.items(), key=lambda x: -x[1])[:10]
    top_in = sorted(in_degrees.items(), key=lambda x: -x[1])[:10]
    
    latex = """
\\begin{table}[h]
\\centering
\\caption{Top 10 Agents by Degree}
\\label{tab:top-agents}
\\begin{tabular}{lr|lr}
\\toprule
\\multicolumn{2}{c|}{\\textbf{Out-degree (comments)}} & \\multicolumn{2}{c}{\\textbf{In-degree (received)}} \\\\
\\textbf{Agent} & \\textbf{Count} & \\textbf{Agent} & \\textbf{Count} \\\\
\\midrule
"""
    
    for i in range(10):
        out_name, out_count = top_out[i] if i < len(top_out) else ("", "")
        in_name, in_count = top_in[i] if i < len(top_in) else ("", "")
        # Escape underscores for LaTeX
        out_name = out_name.replace("_", "\\_")
        in_name = in_name.replace("_", "\\_")
        latex += f"{out_name} & {out_count} & {in_name} & {in_count} \\\\\n"
    
    latex += """\\bottomrule
\\end{tabular}
\\end{table}
"""
    
    with open(OUT_DIR / "table_top_agents.tex", 'w') as f:
        f.write(latex)
    
    return latex

def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    
    print("Loading data...")
    posts, comments = load_data()
    print(f"Loaded {len(posts)} posts, {len(comments)} comments")
    
    print("Building network...")
    out_degrees, in_degrees = build_network(posts, comments)
    print(f"Network: {len(out_degrees)} nodes with out-edges")
    
    print("Generating degree distribution data...")
    generate_degree_distribution_data(out_degrees, "out_degree_dist.csv")
    generate_degree_distribution_data(in_degrees, "in_degree_dist.csv")
    
    print("Generating LaTeX tables...")
    generate_latex_table(posts, comments, out_degrees, in_degrees)
    generate_top_agents_table(out_degrees, in_degrees)
    
    print(f"\nOutput saved to {OUT_DIR}")
    print("Files:")
    for f in OUT_DIR.iterdir():
        print(f"  {f.name}")

if __name__ == "__main__":
    main()
