#!/usr/bin/env python3
"""
ListerPros Blog Post Generator
Automatically generates SEO-optimized blog posts about real estate photography
using the Grok API, then commits them to the repository for auto-deployment.
"""

import os
import json
import re
import random
from datetime import datetime
from pathlib import Path
import requests
from typing import Optional
import subprocess

# Configuration
GROK_API_KEY = os.environ.get("GROK_API_KEY")
GROK_API_URL = "https://api.x.ai/v1/chat/completions"
POSTS_DIR = Path(__file__).parent.parent / "posts"
TEMPLATES_DIR = Path(__file__).parent.parent / "templates"
POSTS_JSON = Path(__file__).parent.parent / "posts.json"

# Blog topic categories with specific focus areas
TOPIC_CATEGORIES = {
    "photography_tips": [
        "best camera angles for real estate photography",
        "lighting tips for interior property photos",
        "how to photograph small rooms to look bigger",
        "twilight photography for real estate listings",
        "HDR photography techniques for homes",
        "staging tips before a photo shoot",
        "common real estate photography mistakes to avoid",
        "how to photograph pools and outdoor spaces",
        "kitchen photography tips for real estate",
        "bathroom photography best practices",
    ],
    "arizona_market": [
        "Arizona real estate market trends",
        "best neighborhoods in Phoenix for home buyers",
        "Scottsdale luxury real estate market",
        "Gilbert Arizona housing market update",
        "Mesa AZ real estate investment opportunities",
        "Chandler Arizona family-friendly neighborhoods",
        "Tempe real estate near ASU",
        "Arizona desert landscaping for curb appeal",
        "monsoon season home preparation Arizona",
        "pool homes in Arizona real estate",
    ],
    "marketing": [
        "how professional photos help sell homes faster",
        "virtual staging vs physical staging comparison",
        "3D tours and their impact on home sales",
        "social media marketing for real estate agents",
        "MLS listing photo requirements and best practices",
        "drone photography benefits for real estate",
        "video tours vs photo galleries for listings",
        "first impression importance in real estate",
        "how to choose a real estate photographer",
        "ROI of professional real estate photography",
    ],
    "industry_news": [
        "real estate photography technology trends",
        "AI in real estate marketing",
        "virtual reality home tours innovation",
        "sustainable homes photography trends",
        "luxury real estate media trends",
        "commercial real estate photography evolution",
        "mobile photography for real estate agents",
        "real estate marketing automation tools",
        "NAR statistics on professional photography",
        "buyer behavior and online listing photos",
    ],
}

# Stock images for blog posts (using Unsplash direct links)
STOCK_IMAGES = {
    "photography_tips": [
        "https://images.unsplash.com/photo-1560448204-e02f11c3d0e2?w=1200&h=630&fit=crop",
        "https://images.unsplash.com/photo-1600596542815-ffad4c1539a9?w=1200&h=630&fit=crop",
        "https://images.unsplash.com/photo-1600585154340-be6161a56a0c?w=1200&h=630&fit=crop",
    ],
    "arizona_market": [
        "https://images.unsplash.com/photo-1558618666-fcd25c85cd64?w=1200&h=630&fit=crop",
        "https://images.unsplash.com/photo-1512917774080-9991f1c4c750?w=1200&h=630&fit=crop",
        "https://images.unsplash.com/photo-1564013799919-ab600027ffc6?w=1200&h=630&fit=crop",
    ],
    "marketing": [
        "https://images.unsplash.com/photo-1600607687939-ce8a6c25118c?w=1200&h=630&fit=crop",
        "https://images.unsplash.com/photo-1600566753190-17f0baa2a6c3?w=1200&h=630&fit=crop",
        "https://images.unsplash.com/photo-1600573472591-ee6c8e695f3c?w=1200&h=630&fit=crop",
    ],
    "industry_news": [
        "https://images.unsplash.com/photo-1600585154526-990dced4db0d?w=1200&h=630&fit=crop",
        "https://images.unsplash.com/photo-1600047509807-ba8f99d2cdde?w=1200&h=630&fit=crop",
        "https://images.unsplash.com/photo-1600566753086-00f18fb6b3ea?w=1200&h=630&fit=crop",
    ],
}


def search_trending_topics() -> dict:
    """
    Use Grok to find current trending topics related to real estate photography.
    Returns a dict with topic, category, and search context.
    """
    # Select a random category and topic as base
    category = random.choice(list(TOPIC_CATEGORIES.keys()))
    base_topic = random.choice(TOPIC_CATEGORIES[category])

    prompt = f"""You are a real estate photography content strategist.

Based on the topic area "{base_topic}", generate a specific, timely blog post topic that would be valuable for real estate agents in Arizona.

The topic should be:
1. Specific and actionable (not too broad)
2. SEO-friendly with clear search intent
3. Relevant to current trends or seasonal considerations
4. Focused on Arizona/Phoenix metro area when applicable

Respond with ONLY a JSON object in this exact format:
{{
    "title": "The complete blog post title (60-70 characters ideal)",
    "search_query": "A search query to find current information on this topic",
    "angle": "The unique angle or hook for this article",
    "target_keywords": ["keyword1", "keyword2", "keyword3"]
}}"""

    try:
        response = requests.post(
            GROK_API_URL,
            headers={
                "Authorization": f"Bearer {GROK_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": "grok-4-latest",
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.8,
            },
            timeout=60,
        )
        response.raise_for_status()
        content = response.json()["choices"][0]["message"]["content"]

        # Parse JSON from response
        json_match = re.search(r'\{[\s\S]*\}', content)
        if json_match:
            topic_data = json.loads(json_match.group())
            topic_data["category"] = category
            return topic_data
    except Exception as e:
        print(f"Error getting trending topic: {e}")

    # Fallback to base topic
    return {
        "title": base_topic.title(),
        "search_query": base_topic,
        "angle": "comprehensive guide",
        "target_keywords": base_topic.split()[:3],
        "category": category,
    }


def research_topic(topic_data: dict) -> str:
    """
    Use Grok's search capability to research the topic and gather current information.
    """
    search_query = topic_data.get("search_query", topic_data["title"])

    prompt = f"""Research the following topic for a blog post: "{topic_data['title']}"

Search query: {search_query}

Provide:
1. Key facts and statistics (with approximate timeframes if available)
2. Current trends and developments
3. Practical tips and actionable advice
4. Arizona/Phoenix specific information if relevant

Format as bullet points that can be used to write a comprehensive blog post."""

    try:
        response = requests.post(
            GROK_API_URL,
            headers={
                "Authorization": f"Bearer {GROK_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": "grok-4-latest",
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.7,
            },
            timeout=90,
        )
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]
    except Exception as e:
        print(f"Error researching topic: {e}")
        return ""


def generate_blog_content(topic_data: dict, research: str) -> dict:
    """
    Generate the full blog post content using Grok.
    """
    prompt = f"""Write a comprehensive, SEO-optimized blog post for ListerPros, a professional real estate photography company based in Arizona.

TOPIC: {topic_data['title']}
ANGLE: {topic_data.get('angle', 'comprehensive guide')}
TARGET KEYWORDS: {', '.join(topic_data.get('target_keywords', []))}

RESEARCH NOTES:
{research}

REQUIREMENTS:
1. Write 1200-1500 words
2. Use a professional but friendly tone
3. Include practical, actionable advice
4. Reference Arizona/Phoenix when relevant
5. Naturally incorporate target keywords
6. Include a compelling introduction that hooks the reader
7. Use H2 and H3 subheadings for structure
8. End with a conclusion that ties back to professional photography services

FORMAT YOUR RESPONSE AS JSON:
{{
    "title": "The blog post title",
    "meta_description": "155 character meta description for SEO",
    "content": "The full HTML content with <h2>, <h3>, <p>, <ul>, <li> tags",
    "excerpt": "A 2-3 sentence excerpt for the blog index",
    "tags": ["tag1", "tag2", "tag3", "tag4", "tag5"]
}}

Write the content section as valid HTML using only these tags: h2, h3, p, ul, ol, li, strong, em, blockquote.
Do NOT include the title in the content - it will be added separately."""

    try:
        response = requests.post(
            GROK_API_URL,
            headers={
                "Authorization": f"Bearer {GROK_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": "grok-4-latest",
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.7,
                "max_tokens": 4000,
            },
            timeout=120,
        )
        response.raise_for_status()
        content = response.json()["choices"][0]["message"]["content"]

        # Parse JSON from response
        json_match = re.search(r'\{[\s\S]*\}', content)
        if json_match:
            blog_data = json.loads(json_match.group())
            blog_data["category"] = topic_data["category"]
            blog_data["keywords"] = topic_data.get("target_keywords", [])
            return blog_data
    except Exception as e:
        print(f"Error generating blog content: {e}")

    return None


def create_slug(title: str) -> str:
    """Convert title to URL-friendly slug."""
    slug = title.lower()
    slug = re.sub(r'[^a-z0-9\s-]', '', slug)
    slug = re.sub(r'[\s_]+', '-', slug)
    slug = re.sub(r'-+', '-', slug)
    slug = slug.strip('-')
    return slug[:60]  # Limit length


def calculate_read_time(content: str) -> int:
    """Calculate estimated read time in minutes."""
    # Strip HTML tags and count words
    text = re.sub(r'<[^>]+>', '', content)
    word_count = len(text.split())
    # Average reading speed: 200 words per minute
    return max(1, round(word_count / 200))


def format_category(category: str) -> str:
    """Format category name for display."""
    return category.replace("_", " ").title()


def generate_tags_html(tags: list) -> str:
    """Generate HTML for tags."""
    return "\n".join([
        f'<a href="/blog/tag/{create_slug(tag)}" class="inline-block bg-gray-100 text-gray-700 px-3 py-1 rounded-full text-sm hover:bg-gray-200 transition">{tag}</a>'
        for tag in tags
    ])


def save_blog_post(blog_data: dict) -> Optional[str]:
    """
    Save the blog post as an HTML file and update the posts index.
    Returns the slug of the created post.
    """
    # Read the template
    template_path = TEMPLATES_DIR / "post_template.html"
    with open(template_path, "r") as f:
        template = f.read()

    # Generate metadata
    now = datetime.now()
    slug = create_slug(blog_data["title"])
    date_str = now.strftime("%Y-%m-%d")
    formatted_date = now.strftime("%B %d, %Y")
    category = blog_data.get("category", "photography_tips")

    # Select a random image for this category
    featured_image = random.choice(STOCK_IMAGES.get(category, STOCK_IMAGES["photography_tips"]))

    # Calculate read time
    read_time = calculate_read_time(blog_data["content"])

    # Replace placeholders
    html = template.replace("{{TITLE}}", blog_data["title"])
    html = html.replace("{{META_DESCRIPTION}}", blog_data["meta_description"])
    html = html.replace("{{KEYWORDS}}", ", ".join(blog_data.get("keywords", [])))
    html = html.replace("{{SLUG}}", slug)
    html = html.replace("{{CATEGORY}}", format_category(category))
    html = html.replace("{{PUBLISH_DATE}}", date_str)
    html = html.replace("{{FORMATTED_DATE}}", formatted_date)
    html = html.replace("{{READ_TIME}}", str(read_time))
    html = html.replace("{{FEATURED_IMAGE}}", featured_image)
    html = html.replace("{{OG_IMAGE}}", featured_image)
    html = html.replace("{{CONTENT}}", blog_data["content"])
    html = html.replace("{{TAGS}}", generate_tags_html(blog_data.get("tags", [])))
    html = html.replace("{{RELATED_POSTS}}", "")  # Will be populated by index generator

    # Ensure posts directory exists
    POSTS_DIR.mkdir(parents=True, exist_ok=True)

    # Save the HTML file
    post_filename = f"{date_str}-{slug}.html"
    post_path = POSTS_DIR / post_filename
    with open(post_path, "w") as f:
        f.write(html)

    print(f"Created post: {post_path}")

    # Update posts.json index
    post_entry = {
        "slug": slug,
        "title": blog_data["title"],
        "excerpt": blog_data.get("excerpt", blog_data["meta_description"]),
        "category": category,
        "date": date_str,
        "formatted_date": formatted_date,
        "read_time": read_time,
        "featured_image": featured_image,
        "tags": blog_data.get("tags", []),
        "filename": post_filename,
    }

    # Load existing posts or create new list
    posts = []
    if POSTS_JSON.exists():
        with open(POSTS_JSON, "r") as f:
            posts = json.load(f)

    # Add new post at the beginning
    posts.insert(0, post_entry)

    # Save updated index
    with open(POSTS_JSON, "w") as f:
        json.dump(posts, f, indent=2)

    print(f"Updated posts index: {POSTS_JSON}")

    return slug


def generate_index_page():
    """
    Regenerate the blog index page from posts.json.
    """
    if not POSTS_JSON.exists():
        print("No posts.json found, skipping index generation")
        return

    with open(POSTS_JSON, "r") as f:
        posts = json.load(f)

    # Read the index template
    template_path = TEMPLATES_DIR / "index_template.html"
    with open(template_path, "r") as f:
        template = f.read()

    # Generate featured post (most recent)
    featured_html = ""
    if posts:
        p = posts[0]
        featured_html = f'''
    <section class="py-12">
        <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <a href="/blog/{p['slug']}" class="group block">
                <div class="grid lg:grid-cols-2 gap-8 items-center bg-gray-50 rounded-3xl overflow-hidden card-lift">
                    <div class="aspect-video overflow-hidden">
                        <img src="{p['featured_image']}" alt="{p['title']}" class="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500">
                    </div>
                    <div class="p-8">
                        <span class="inline-block bg-primary/10 text-primary px-3 py-1 rounded-full text-sm font-semibold mb-4">{format_category(p['category'])}</span>
                        <h2 class="text-2xl md:text-3xl font-bold mb-4 group-hover:text-primary transition">{p['title']}</h2>
                        <p class="text-gray-600 mb-4">{p['excerpt']}</p>
                        <div class="flex items-center gap-4 text-sm text-gray-500">
                            <span>{p['formatted_date']}</span>
                            <span>&bull;</span>
                            <span>{p['read_time']} min read</span>
                        </div>
                    </div>
                </div>
            </a>
        </div>
    </section>'''

    # Generate post cards (skip first since it's featured)
    cards_html = ""
    for p in posts[1:21]:  # Show up to 20 posts
        cards_html += f'''
                <a href="/blog/{p['slug']}" class="group block bg-white rounded-2xl overflow-hidden shadow-sm hover:shadow-xl transition card-lift">
                    <div class="aspect-video overflow-hidden">
                        <img src="{p['featured_image']}" alt="{p['title']}" class="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500">
                    </div>
                    <div class="p-6">
                        <span class="inline-block bg-primary/10 text-primary px-2 py-0.5 rounded text-xs font-semibold mb-2">{format_category(p['category'])}</span>
                        <h3 class="font-bold text-lg mb-2 group-hover:text-primary transition line-clamp-2">{p['title']}</h3>
                        <p class="text-gray-600 text-sm mb-4 line-clamp-2">{p['excerpt']}</p>
                        <div class="flex items-center gap-3 text-xs text-gray-500">
                            <span>{p['formatted_date']}</span>
                            <span>&bull;</span>
                            <span>{p['read_time']} min read</span>
                        </div>
                    </div>
                </a>'''

    # Simple pagination (just showing page 1 for now)
    pagination_html = '<span class="px-4 py-2 bg-primary text-white rounded-lg">1</span>'
    if len(posts) > 21:
        pagination_html += '<a href="/blog/page/2" class="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition">2</a>'

    # Replace placeholders
    html = template.replace("{{FEATURED_POST}}", featured_html)
    html = html.replace("{{POST_CARDS}}", cards_html)
    html = html.replace("{{PAGINATION}}", pagination_html)

    # Save the index page
    index_path = Path(__file__).parent.parent / "index.html"
    with open(index_path, "w") as f:
        f.write(html)

    print(f"Generated index page: {index_path}")


def git_commit_and_push():
    """Commit changes and push to trigger Netlify deploy."""
    try:
        repo_root = Path(__file__).parent.parent

        # Add all changes
        subprocess.run(["git", "add", "."], cwd=repo_root, check=True)

        # Create commit
        now = datetime.now().strftime("%Y-%m-%d %H:%M")
        commit_msg = f"Auto-publish blog post - {now}"
        subprocess.run(["git", "commit", "-m", commit_msg], cwd=repo_root, check=True)

        # Push to origin
        subprocess.run(["git", "push"], cwd=repo_root, check=True)

        print("Successfully committed and pushed to GitHub")
    except subprocess.CalledProcessError as e:
        print(f"Git operation failed: {e}")
    except Exception as e:
        print(f"Error in git operations: {e}")


def main():
    """Main function to generate a blog post."""
    if not GROK_API_KEY:
        print("ERROR: GROK_API_KEY environment variable not set")
        print("Please set it with: export GROK_API_KEY='your-api-key'")
        return

    print("=" * 60)
    print("ListerPros Blog Generator")
    print("=" * 60)

    # Step 1: Find a trending topic
    print("\n1. Finding trending topic...")
    topic_data = search_trending_topics()
    print(f"   Topic: {topic_data['title']}")
    print(f"   Category: {topic_data['category']}")

    # Step 2: Research the topic
    print("\n2. Researching topic...")
    research = research_topic(topic_data)
    if research:
        print(f"   Gathered {len(research)} characters of research")

    # Step 3: Generate the blog content
    print("\n3. Generating blog content...")
    blog_data = generate_blog_content(topic_data, research)

    if not blog_data:
        print("ERROR: Failed to generate blog content")
        return

    print(f"   Title: {blog_data['title']}")
    print(f"   Content length: {len(blog_data['content'])} characters")

    # Step 4: Save the blog post
    print("\n4. Saving blog post...")
    slug = save_blog_post(blog_data)

    if not slug:
        print("ERROR: Failed to save blog post")
        return

    # Step 5: Regenerate index page
    print("\n5. Regenerating index page...")
    generate_index_page()

    # Step 6: Commit and push (only in CI environment)
    if os.environ.get("CI") or os.environ.get("GITHUB_ACTIONS"):
        print("\n6. Committing and pushing to GitHub...")
        git_commit_and_push()
    else:
        print("\n6. Skipping git push (not in CI environment)")
        print("   Run 'git add . && git commit && git push' manually to deploy")

    print("\n" + "=" * 60)
    print("SUCCESS! Blog post generated")
    print(f"View at: https://listerpros.com/blog/{slug}")
    print("=" * 60)


if __name__ == "__main__":
    main()
