#!/usr/bin/env python3
"""Generate degree distribution figure for paper."""

import csv
import matplotlib.pyplot as plt
import numpy as np

def load_dist(filename):
    degrees, counts = [], []
    with open(filename) as f:
        reader = csv.DictReader(f)
        for row in reader:
            degrees.append(int(row['degree']))
            counts.append(int(row['count']))
    return np.array(degrees), np.array(counts)

# Load data
in_deg, in_cnt = load_dist('in_degree_dist.csv')
out_deg, out_cnt = load_dist('out_degree_dist.csv')

# Create figure
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 4))

# In-degree (log-log)
ax1.loglog(in_deg, in_cnt, 'o', markersize=4, alpha=0.7, color='#2E86AB')
ax1.set_xlabel('In-degree (comments received)')
ax1.set_ylabel('Count')
ax1.set_title('In-Degree Distribution')
ax1.grid(True, alpha=0.3)

# Out-degree (log-log)  
ax2.loglog(out_deg, out_cnt, 'o', markersize=4, alpha=0.7, color='#A23B72')
ax2.set_xlabel('Out-degree (comments made)')
ax2.set_ylabel('Count')
ax2.set_title('Out-Degree Distribution')
ax2.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('degree_distribution.pdf', dpi=300, bbox_inches='tight')
plt.savefig('degree_distribution.png', dpi=150, bbox_inches='tight')
print("Saved: degree_distribution.pdf, degree_distribution.png")
