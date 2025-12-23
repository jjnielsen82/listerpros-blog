#!/usr/bin/env python3
"""
Redistribute blog post dates to create a natural-looking publication history.
- 505 existing posts spread from July 2022 to December 2024
- Varies posts per day (1-3) to look organic
- Avoids weekends having too many posts
- Creates realistic publishing patterns
"""

import os
import re
import random
from datetime import datetime, timedelta
from pathlib import Path

# Configuration
POSTS_DIR = Path(__file__).parent.parent
START_DATE = datetime(2022, 7, 1)  # Start mid-2022 for established look
END_DATE = datetime(2024, 12, 31)  # End of 2024

def get_all_markdown_files():
    """Get all markdown files in the posts directory."""
    files = []
    for f in POSTS_DIR.glob("*.md"):
        if f.name != ".processed_sources.json":
            files.append(f)
    return sorted(files, key=lambda x: x.name)

def generate_date_distribution(num_posts, start_date, end_date):
    """
    Generate a realistic date distribution for blog posts.
    - More posts on weekdays
    - Occasional gaps (vacations, holidays)
    - Gradually increasing frequency (blog growth pattern)
    """
    dates = []
    total_days = (end_date - start_date).days

    # Create weighted day pool - more recent = more posts (simulates growth)
    current_date = start_date
    day_weights = []

    while current_date <= end_date:
        # Base weight
        weight = 1.0

        # Reduce weekend weight
        if current_date.weekday() >= 5:  # Saturday, Sunday
            weight *= 0.3

        # Increase weight over time (blog growth)
        days_in = (current_date - start_date).days
        growth_factor = 0.5 + (days_in / total_days) * 1.5  # 0.5x to 2x
        weight *= growth_factor

        # Reduce weight around major holidays
        if (current_date.month == 12 and current_date.day >= 23) or \
           (current_date.month == 1 and current_date.day <= 3) or \
           (current_date.month == 7 and current_date.day == 4) or \
           (current_date.month == 11 and current_date.day >= 22 and current_date.day <= 28):
            weight *= 0.2

        day_weights.append((current_date, weight))
        current_date += timedelta(days=1)

    # Normalize weights
    total_weight = sum(w for _, w in day_weights)
    normalized = [(d, w/total_weight) for d, w in day_weights]

    # Sample dates based on weights
    dates_only = [d for d, _ in normalized]
    weights_only = [w for _, w in normalized]

    # Use weighted random selection
    selected_dates = random.choices(dates_only, weights=weights_only, k=num_posts)

    # Sort dates
    selected_dates.sort()

    return selected_dates

def update_post_date(file_path, new_date):
    """Update the date in a markdown file's frontmatter."""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Match the date line in frontmatter
    date_pattern = r'^date:\s*\d{4}-\d{2}-\d{2}$'
    new_date_str = new_date.strftime('%Y-%m-%d')

    # Replace the date
    updated_content = re.sub(
        date_pattern,
        f'date: {new_date_str}',
        content,
        flags=re.MULTILINE
    )

    if updated_content != content:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(updated_content)
        return True
    return False

def main():
    print("=" * 60)
    print("Blog Post Date Redistributor")
    print("=" * 60)

    # Get all markdown files
    files = get_all_markdown_files()
    print(f"\nFound {len(files)} markdown files")

    # Generate date distribution
    print(f"\nGenerating dates from {START_DATE.strftime('%Y-%m-%d')} to {END_DATE.strftime('%Y-%m-%d')}")
    dates = generate_date_distribution(len(files), START_DATE, END_DATE)

    # Shuffle files to randomize which posts get which dates
    # (so it's not alphabetically sorted by date)
    shuffled_files = files.copy()
    random.shuffle(shuffled_files)

    # Update each file
    print("\nUpdating post dates...")
    updated_count = 0

    for file_path, new_date in zip(shuffled_files, dates):
        if update_post_date(file_path, new_date):
            updated_count += 1
            if updated_count % 50 == 0:
                print(f"  Updated {updated_count} files...")

    print(f"\nComplete! Updated {updated_count} files")

    # Show date distribution summary
    print("\n" + "=" * 60)
    print("Date Distribution Summary")
    print("=" * 60)

    by_year_month = {}
    for d in dates:
        key = d.strftime('%Y-%m')
        by_year_month[key] = by_year_month.get(key, 0) + 1

    for ym in sorted(by_year_month.keys()):
        bar = '█' * (by_year_month[ym] // 2)
        print(f"{ym}: {by_year_month[ym]:3d} {bar}")

if __name__ == "__main__":
    random.seed(42)  # For reproducibility, remove for true random
    main()
