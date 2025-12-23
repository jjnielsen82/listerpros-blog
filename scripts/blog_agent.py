#!/usr/bin/env python3
"""
ListerPros Autonomous Blog Agent
================================

An AI-powered blog agent that automatically:
1. Researches trending real estate & photography topics
2. Generates Arizona-focused SEO content
3. Creates markdown blog posts
4. Builds HTML and deploys to Netlify

Configuration:
- Set your API keys in the config section below
- Adjust POSTING_INTERVAL for frequency (default: 6 hours)
- Run once and it will loop forever

Usage:
    python3 blog_agent.py              # Run continuously
    python3 blog_agent.py --once       # Run once and exit
    python3 blog_agent.py --test       # Test without posting

Requirements:
    - Anthropic API key (for Claude)
    - Netlify CLI or API token (for deployment)
"""

import os
import re
import sys
import json
import time
import random
import hashlib
import subprocess
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import urllib.request
import urllib.parse
import ssl

# =============================================================================
# CONFIGURATION - EDIT THESE VALUES
# =============================================================================

# API Keys (set via environment variables or hardcode here)
# Using Grok API (xAI) - cheaper alternative to Anthropic
GROK_API_KEY = os.environ.get("GROK_API_KEY", "your-api-key-here")

# Grok API settings
GROK_API_URL = "https://api.x.ai/v1/chat/completions"
GROK_MODEL = "grok-3"  # Current model (grok-beta deprecated)

# Netlify deployment (optional - can also manually deploy)
NETLIFY_SITE_ID = os.environ.get("NETLIFY_SITE_ID", "")
NETLIFY_AUTH_TOKEN = os.environ.get("NETLIFY_AUTH_TOKEN", "")

# Posting schedule
POSTING_INTERVAL_HOURS = 6  # Post every 6 hours = 4 posts per day
POSTS_PER_RUN = 1  # Number of posts to create each run

# Content focus
PRIMARY_LOCATION = "Arizona"
SECONDARY_LOCATIONS = ["Phoenix", "Scottsdale", "Tucson", "Mesa", "Tempe", "Gilbert", "Chandler", "Glendale", "Peoria", "Sedona", "Flagstaff"]
COMPANY_NAME = "ListerPros"
TARGET_AUDIENCE = "real estate agents"

# Paths
BASE_DIR = Path(__file__).parent.parent
POSTS_DIR = BASE_DIR
DIST_DIR = BASE_DIR / "dist"
LOG_FILE = BASE_DIR / "scripts" / "agent.log"

# =============================================================================
# TOPIC CATEGORIES - Arizona Real Estate Photography Focus
# =============================================================================

TOPIC_CATEGORIES = {
    "arizona_market": [
        "Arizona real estate market trends for agents",
        "Phoenix housing market update for listing agents",
        "Scottsdale luxury home selling tips",
        "Tucson home selling strategies",
        "How to price listings in competitive Arizona markets",
        "Why Arizona homes sell faster with professional photos",
        "Snowbird season strategies for Arizona agents",
        "Attracting out-of-state buyers to Arizona listings",
        "Arizona relocation buyer trends",
        "First-time homebuyer market in Phoenix",
        "Move-up buyer trends in Scottsdale",
        "Arizona new construction vs resale market",
    ],
    "seasonal_arizona": [
        "Summer listing strategies for Arizona agents",
        "Selling homes during Arizona monsoon season",
        "Winter selling season tips for Arizona",
        "Spring market preparation for Arizona agents",
        "Holiday staging tips for Arizona homes",
        "Best months to list homes in Arizona",
        "Seasonal curb appeal tips for desert homes",
        "How to photograph pools in Arizona summer",
    ],
    "listing_photography": [
        "Why professional photos help Arizona listings sell faster",
        "Preparing homes for real estate photography",
        "Best time of day for Arizona listing photos",
        "How to photograph Arizona pool homes",
        "Desert landscaping photography tips",
        "Capturing Arizona mountain views in listings",
        "Interior photography tips for Arizona homes",
        "Photographing open floor plans",
        "Kitchen and bathroom photography that sells",
        "Outdoor living space photography Arizona",
        "Twilight photography for Arizona listings",
        "How many photos your Arizona listing needs",
    ],
    "video_and_tours": [
        "Video tours that sell Arizona homes",
        "3D virtual tours for Arizona listings",
        "Drone photography for Arizona properties",
        "Creating walkthrough videos buyers love",
        "Video marketing for real estate agents",
        "How video tours attract out-of-state buyers",
        "Social media video tips for agents",
        "Reels and TikTok strategies for Arizona agents",
    ],
    "agent_marketing": [
        "Building your personal brand as an Arizona agent",
        "Social media strategies for real estate agents",
        "How to stand out in competitive Arizona markets",
        "Getting more listings with professional photography",
        "Client communication tips for agents",
        "Open house strategies for Arizona homes",
        "How to win listing presentations",
        "Marketing luxury homes in Scottsdale",
        "Working with first-time home sellers",
        "Building referral business in Arizona",
        "Sphere of influence marketing tips",
        "Geographic farming strategies Arizona",
    ],
    "home_prep_staging": [
        "Preparing homes for the Arizona market",
        "Staging tips for Arizona desert homes",
        "Decluttering tips for home sellers",
        "Virtual staging benefits for vacant homes",
        "Curb appeal tips for Arizona properties",
        "How to stage outdoor living spaces",
        "Staging Arizona homes for photography",
        "Budget-friendly staging ideas for sellers",
        "Pet-friendly home showing tips",
        "Quick fixes that help homes sell faster",
    ],
    "buyer_psychology": [
        "What Arizona home buyers look for in photos",
        "First impressions in real estate listings",
        "Features that sell homes in Arizona",
        "Pool homes and buyer preferences",
        "What makes buyers click on listings",
        "Kitchen features Arizona buyers want",
        "Outdoor living trends Arizona buyers love",
        "Home office appeal for modern buyers",
        "Energy efficiency features that sell",
        "Smart home features buyers want",
    ],
    "pricing_and_selling": [
        "Pricing strategies for Arizona homes",
        "How professional photos affect sale price",
        "Reducing days on market in Arizona",
        "Multiple offer strategies for listing agents",
        "Preparing sellers for the Arizona market",
        "Setting realistic expectations with sellers",
        "Pre-listing checklist for Arizona agents",
        "How to handle price reductions",
        "Expired listing strategies Arizona",
        "Relisting with better photography",
    ],
}

# =============================================================================
# LOGGING
# =============================================================================

def log(message: str, level: str = "INFO"):
    """Log message to file and console."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_line = f"[{timestamp}] [{level}] {message}"
    print(log_line)

    try:
        with open(LOG_FILE, "a") as f:
            f.write(log_line + "\n")
    except Exception as e:
        print(f"Warning: Could not write to log file: {e}")

# =============================================================================
# TOPIC GENERATION
# =============================================================================

def get_current_context() -> Dict:
    """Get current date/time context for relevant content."""
    now = datetime.now()

    # Determine season
    month = now.month
    if month in [12, 1, 2]:
        season = "winter"
        arizona_context = "snowbird season, mild weather, peak selling time"
    elif month in [3, 4, 5]:
        season = "spring"
        arizona_context = "wildflower blooms, perfect weather, busy market"
    elif month in [6, 7, 8]:
        season = "summer"
        arizona_context = "extreme heat, monsoon season, pool focus, early morning shoots"
    else:
        season = "fall"
        arizona_context = "cooling temps, returning snowbirds, market pickup"

    # Check for holidays/events
    events = []
    if month == 12:
        events.append("holiday season")
    if month == 1:
        events.append("new year, fresh start")
    if month == 2:
        events.append("Super Bowl (if in Arizona), Valentine's")
    if month == 3:
        events.append("spring training baseball, March Madness")
    if month == 4:
        events.append("tax season ending")
    if month == 11:
        events.append("Thanksgiving, year-end push")

    return {
        "date": now.strftime("%Y-%m-%d"),
        "month": now.strftime("%B"),
        "year": now.year,
        "day_of_week": now.strftime("%A"),
        "season": season,
        "arizona_context": arizona_context,
        "events": events,
        "is_weekend": now.weekday() >= 5,
    }


def select_topic() -> Tuple[str, str]:
    """Select a topic category and specific topic."""
    context = get_current_context()

    # Weight categories - focused on residential real estate agents
    weights = {
        "arizona_market": 15,
        "seasonal_arizona": 20 if context["season"] in ["summer", "winter"] else 10,
        "listing_photography": 20,  # Core service - high weight
        "video_and_tours": 15,
        "agent_marketing": 15,
        "home_prep_staging": 15,
        "buyer_psychology": 10,
        "pricing_and_selling": 10,
    }

    # Build weighted list
    weighted_categories = []
    for cat, weight in weights.items():
        weighted_categories.extend([cat] * weight)

    # Select category
    category = random.choice(weighted_categories)

    # Select topic from category
    topic = random.choice(TOPIC_CATEGORIES[category])

    return category, topic


def generate_unique_angle(base_topic: str, context: Dict) -> str:
    """Generate a unique angle for the topic based on current context."""
    angles = [
        f"{base_topic} - {context['month']} {context['year']} Update",
        f"How {context['season'].title()} Affects {base_topic}",
        f"{base_topic}: What Arizona Agents Need to Know in {context['year']}",
        f"The Complete Guide to {base_topic} for {context['month']}",
        f"{base_topic} Tips for {random.choice(SECONDARY_LOCATIONS)} Agents",
        f"Why {base_topic} Matters More Than Ever in Arizona",
        f"{base_topic}: {context['year']} Best Practices",
        f"Mastering {base_topic} in the Arizona Market",
    ]

    return random.choice(angles)

# =============================================================================
# CONTENT GENERATION (Grok API - xAI)
# =============================================================================

def call_grok_api(prompt: str, max_tokens: int = 4000) -> Optional[str]:
    """Call Grok API to generate content using curl (more reliable than urllib)."""
    if GROK_API_KEY == "your-api-key-here":
        log("ERROR: Grok API key not set!", "ERROR")
        log("Get your key at: https://console.x.ai/", "ERROR")
        return None

    data = {
        "model": GROK_MODEL,
        "max_tokens": max_tokens,
        "stream": False,
        "messages": [
            {
                "role": "system",
                "content": "You are an expert content writer specializing in real estate photography and marketing. You write SEO-optimized blog posts for ListerPros, a real estate photography company in Arizona."
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        "temperature": 0.7,
    }

    try:
        # Use curl via subprocess (bypasses Cloudflare issues with Python urllib)
        result = subprocess.run(
            [
                "curl", "-s",
                GROK_API_URL,
                "-H", "Content-Type: application/json",
                "-H", f"Authorization: Bearer {GROK_API_KEY}",
                "-d", json.dumps(data)
            ],
            capture_output=True,
            text=True,
            timeout=300
        )

        if result.returncode != 0:
            log(f"Curl error: {result.stderr}", "ERROR")
            return None

        response = json.loads(result.stdout)

        if "error" in response:
            log(f"API Error: {response['error']}", "ERROR")
            return None

        return response["choices"][0]["message"]["content"]

    except subprocess.TimeoutExpired:
        log("API request timed out", "ERROR")
        return None
    except json.JSONDecodeError as e:
        log(f"Failed to parse API response: {e}", "ERROR")
        return None
    except Exception as e:
        log(f"Grok API Error: {e}", "ERROR")
        return None


def generate_blog_post(topic: str, context: Dict) -> Optional[Dict]:
    """Generate a complete blog post using Grok API."""

    city = random.choice(SECONDARY_LOCATIONS)

    prompt = f"""Write a comprehensive, SEO-optimized blog post about: {topic}

IMPORTANT REQUIREMENTS:
1. Focus on Arizona and specifically mention cities like {city}, Phoenix, Scottsdale when relevant
2. Target audience: Real estate agents in Arizona
3. Current context: It's {context['month']} {context['year']}, {context['season']} season
4. Arizona context: {context['arizona_context']}
5. Include practical, actionable advice
6. Naturally mention ListerPros services where appropriate (but don't be salesy)
7. Include local Arizona references (desert landscape, heat considerations, pool homes, etc.)
8. Length: 1200-1500 words
9. Use headers (##) to break up sections
10. Include a compelling introduction and conclusion

OUTPUT FORMAT - Return ONLY valid markdown with this exact frontmatter structure:

---
title: "Your SEO-Optimized Title Here"
date: {context['date']}
description: "A compelling 150-160 character meta description for SEO"
author: "ListerPros Team"
tags: ["arizona", "real-estate-photography", "tag3", "tag4", "tag5"]
excerpt: "A 2-3 sentence excerpt summarizing the post"
slug: "url-friendly-slug-here"
readingTime: "X min read"
---

[Your full blog post content here with ## headers, bullet points, etc.]

Remember:
- Make the title compelling and include "Arizona" or an Arizona city
- The slug should be lowercase with hyphens
- Include 5 relevant tags (always include "arizona" and "real-estate-photography")
- Calculate approximate reading time (average 200 words per minute)
- End with a call-to-action mentioning ListerPros services

Write the complete blog post now:"""

    log(f"Generating content for: {topic}")

    content = call_grok_api(prompt)

    if not content:
        return None

    # Parse the response
    if not content.strip().startswith("---"):
        log("Generated content missing frontmatter", "WARNING")
        return None

    # Extract frontmatter and body
    parts = content.split("---", 2)
    if len(parts) < 3:
        log("Could not parse frontmatter", "WARNING")
        return None

    try:
        # Simple frontmatter parsing
        frontmatter = {}
        for line in parts[1].strip().split("\n"):
            if ":" in line:
                key = line.split(":")[0].strip()
                value = ":".join(line.split(":")[1:]).strip()
                # Remove quotes
                if value.startswith('"') and value.endswith('"'):
                    value = value[1:-1]
                elif value.startswith("'") and value.endswith("'"):
                    value = value[1:-1]
                # Handle arrays
                if value.startswith("["):
                    value = re.findall(r'"([^"]*)"', value)
                frontmatter[key] = value

        body = parts[2].strip()

        return {
            "frontmatter": frontmatter,
            "body": body,
            "full_content": content.strip()
        }

    except Exception as e:
        log(f"Error parsing content: {e}", "ERROR")
        return None

# =============================================================================
# FILE OPERATIONS
# =============================================================================

def save_blog_post(post_data: Dict) -> Optional[Path]:
    """Save the blog post as a markdown file."""
    try:
        slug = post_data["frontmatter"].get("slug", "untitled")
        # Clean slug
        slug = re.sub(r'[^a-z0-9-]', '', slug.lower())
        slug = re.sub(r'-+', '-', slug).strip('-')

        if not slug:
            slug = f"post-{datetime.now().strftime('%Y%m%d%H%M%S')}"

        filename = f"{slug}.md"
        filepath = POSTS_DIR / filename

        # Check if file already exists
        if filepath.exists():
            slug = f"{slug}-{datetime.now().strftime('%H%M%S')}"
            filename = f"{slug}.md"
            filepath = POSTS_DIR / filename

        # Write file
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(post_data["full_content"])

        log(f"Saved post: {filename}")
        return filepath

    except Exception as e:
        log(f"Error saving post: {e}", "ERROR")
        return None

# =============================================================================
# BUILD AND DEPLOY
# =============================================================================

def build_blog() -> bool:
    """Run the blog build script."""
    try:
        build_script = BASE_DIR / "scripts" / "build_blog.py"
        result = subprocess.run(
            ["python3", str(build_script)],
            cwd=str(BASE_DIR),
            capture_output=True,
            text=True,
            timeout=300
        )

        if result.returncode == 0:
            log("Blog build successful")
            return True
        else:
            log(f"Build failed: {result.stderr}", "ERROR")
            return False

    except Exception as e:
        log(f"Build error: {e}", "ERROR")
        return False


def git_push_to_github() -> bool:
    """Commit and push changes to GitHub (triggers Netlify auto-deploy)."""
    try:
        # Check if we're in a git repo
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=str(BASE_DIR),
            capture_output=True,
            text=True,
            timeout=30
        )

        if result.returncode != 0:
            log("Not a git repository - skipping push", "WARNING")
            return False

        # Check if there are changes to commit
        if not result.stdout.strip():
            log("No changes to commit")
            return True

        # Add all changes
        subprocess.run(
            ["git", "add", "-A"],
            cwd=str(BASE_DIR),
            capture_output=True,
            timeout=30
        )

        # Commit with timestamp
        commit_msg = f"Auto-post: {datetime.now().strftime('%Y-%m-%d %H:%M')} - New blog content"
        subprocess.run(
            ["git", "commit", "-m", commit_msg],
            cwd=str(BASE_DIR),
            capture_output=True,
            timeout=30
        )

        # Push to origin
        result = subprocess.run(
            ["git", "push", "origin", "main"],
            cwd=str(BASE_DIR),
            capture_output=True,
            text=True,
            timeout=60
        )

        if result.returncode == 0:
            log("Pushed to GitHub - Netlify will auto-deploy")
            return True
        else:
            # Try 'master' branch if 'main' fails
            result = subprocess.run(
                ["git", "push", "origin", "master"],
                cwd=str(BASE_DIR),
                capture_output=True,
                text=True,
                timeout=60
            )
            if result.returncode == 0:
                log("Pushed to GitHub (master) - Netlify will auto-deploy")
                return True
            else:
                log(f"Git push failed: {result.stderr}", "WARNING")
                return False

    except subprocess.TimeoutExpired:
        log("Git operation timed out", "WARNING")
        return False
    except Exception as e:
        log(f"Git error: {e}", "WARNING")
        return False


def deploy_to_netlify() -> bool:
    """Deploy via GitHub push (triggers Netlify auto-deploy)."""
    return git_push_to_github()

# =============================================================================
# MAIN AGENT LOOP
# =============================================================================

def run_once() -> bool:
    """Run the agent once to create and publish a post."""
    log("=" * 60)
    log("Starting blog agent run")
    log("=" * 60)

    # Get context
    context = get_current_context()
    log(f"Context: {context['month']} {context['year']}, {context['season']} season")

    # Select topic
    category, base_topic = select_topic()
    topic = generate_unique_angle(base_topic, context)
    log(f"Selected topic: {topic} (category: {category})")

    # Generate content
    post_data = generate_blog_post(topic, context)
    if not post_data:
        log("Failed to generate content", "ERROR")
        return False

    log(f"Generated: {post_data['frontmatter'].get('title', 'Untitled')}")

    # Save post
    filepath = save_blog_post(post_data)
    if not filepath:
        log("Failed to save post", "ERROR")
        return False

    # Build blog
    if not build_blog():
        log("Failed to build blog", "ERROR")
        return False

    # Deploy (optional)
    deploy_to_netlify()

    log("Agent run completed successfully")
    return True


def run_continuous():
    """Run the agent continuously on a schedule."""
    log("=" * 60)
    log(f"Starting continuous blog agent")
    log(f"Posting interval: {POSTING_INTERVAL_HOURS} hours")
    log(f"Posts per run: {POSTS_PER_RUN}")
    log("=" * 60)

    while True:
        try:
            for i in range(POSTS_PER_RUN):
                success = run_once()
                if not success:
                    log(f"Post {i+1}/{POSTS_PER_RUN} failed", "WARNING")

                # Small delay between posts if doing multiple
                if i < POSTS_PER_RUN - 1:
                    time.sleep(60)

            # Calculate next run time
            next_run = datetime.now() + timedelta(hours=POSTING_INTERVAL_HOURS)
            log(f"Next run scheduled for: {next_run.strftime('%Y-%m-%d %H:%M:%S')}")

            # Sleep until next run
            time.sleep(POSTING_INTERVAL_HOURS * 3600)

        except KeyboardInterrupt:
            log("Agent stopped by user")
            break
        except Exception as e:
            log(f"Unexpected error: {e}", "ERROR")
            # Wait a bit before retrying
            time.sleep(300)


def main():
    """Main entry point."""
    # Parse arguments
    args = sys.argv[1:]

    if "--test" in args:
        log("TEST MODE - Generating content without saving")
        context = get_current_context()
        category, base_topic = select_topic()
        topic = generate_unique_angle(base_topic, context)
        print(f"\nSelected Topic: {topic}")
        print(f"Category: {category}")
        print(f"Context: {context}")

        if GROK_API_KEY != "your-api-key-here":
            print("\nGenerating content with Grok API...")
            post_data = generate_blog_post(topic, context)
            if post_data:
                print("\n" + "=" * 60)
                print("GENERATED CONTENT:")
                print("=" * 60)
                print(post_data["full_content"][:2000] + "...")
        else:
            print("\nSet GROK_API_KEY to test content generation")
            print("Get your key at: https://console.x.ai/")
        return

    if "--once" in args:
        run_once()
        return

    # Default: run continuously
    run_continuous()


if __name__ == "__main__":
    main()
