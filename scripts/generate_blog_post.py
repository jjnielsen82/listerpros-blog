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
POSTS_DIR = Path(__file__).parent.parent  # Save posts to root directory
TEMPLATES_DIR = Path(__file__).parent.parent / "templates"
POSTS_JSON = Path(__file__).parent.parent / "posts.json"

# =============================================================================
# LISTERPROS BRAND GUIDELINES
# =============================================================================
BRAND_GUIDELINES = """
ABOUT LISTERPROS:
- ListerPros is Arizona's premier real estate photography company, founded in 2013 and headquartered in Mesa, AZ
- We serve the entire Phoenix metro area including Phoenix, Scottsdale, Mesa, Gilbert, Chandler, Tempe, Glendale, Peoria, and surrounding areas
- We also serve Tucson and Southern Arizona markets
- We've photographed over 150,000 properties and served 5,000+ real estate agents
- We maintain a 4.9-star rating with 97%+ satisfaction rate

OUR SERVICES:
- Professional HDR Photography (with 5-HOUR SAME-DAY DELIVERY included - this is our key differentiator!)
- Cinematic Video Tours
- 3D Virtual Tours (Matterport & Zillow 3D)
- Virtual Staging
- Aerial Drone Photography & Video (FAA-certified pilots)
- Floor Plans with dimensions
- Twilight/Dusk Photography
- FREE Community Photos (we have a library of 1,000+ Arizona communities)

KEY SELLING POINTS TO WEAVE IN NATURALLY:
- 5-hour photo delivery included on all shoots (fastest in Arizona)
- Book online in 60 seconds - no phone calls needed
- 20+ local Arizona photographers
- All-in-one provider (photo, video, 3D, drone, staging)
- Competitive pricing with transparent online quotes

BRAND VOICE:
- Professional yet approachable
- Confident and authoritative on real estate photography topics
- Helpful and educational (we want to genuinely help agents succeed)
- Arizona-proud (we're local, we know the market)
- Data-driven when possible (use statistics to back up claims)

SEO TARGET KEYWORDS (incorporate naturally):
- real estate photography Arizona
- real estate photographer Phoenix
- real estate photography Scottsdale
- real estate photographer Tucson
- real estate photography Tucson
- professional real estate photos
- real estate media services Arizona
- property photography Phoenix
- property photography Tucson
- listing photography Arizona
- real estate video tours Phoenix
- drone photography real estate Arizona
- virtual staging Arizona
- Tucson real estate photography

WHAT TO AVOID:
- Don't be salesy or pushy - educate first, soft-sell second
- Don't make claims we can't back up
- Don't disparage competitors
- Don't use AI-generated images (we use our own portfolio)
- Don't write generic content - always tie to Arizona/Phoenix when possible
"""

# =============================================================================
# EXPANDED TOPIC CATEGORIES (100+ topics)
# =============================================================================
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
        "photographing homes with dark interiors",
        "window pull technique in real estate photography",
        "best time of day to photograph homes",
        "wide angle lens tips for real estate",
        "editing tips for real estate photos",
        "how to photograph luxury homes",
        "capturing outdoor living spaces Arizona",
        "photographing desert landscaping",
        "real estate photography composition rules",
        "how to make listings stand out with photos",
        "photographing open floor plans",
        "real estate photo checklist for agents",
        "preparing a home for professional photos",
        "exterior photography curb appeal tips",
        "how weather affects real estate photography",
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
        "Phoenix housing market forecast",
        "best golf communities in Scottsdale",
        "Peoria Arizona real estate guide",
        "Glendale AZ housing market trends",
        "Queen Creek new home developments",
        "Surprise Arizona growth and real estate",
        "Fountain Hills luxury homes market",
        "Paradise Valley real estate trends",
        "Ahwatukee neighborhood guide Phoenix",
        "Cave Creek horse property market",
        "Sun City retirement communities",
        "Arizona snowbird real estate market",
        "best school districts Phoenix metro",
        "Arizona vacation rental investment",
        "Phoenix downtown condo market",
        "Arcadia neighborhood Phoenix real estate",
        "Biltmore area homes Phoenix",
        "North Scottsdale vs South Scottsdale",
        "East Valley vs West Valley Arizona",
        "Arizona new construction homes trends",
        "Tucson real estate market trends",
        "Tucson vs Phoenix housing market comparison",
        "best neighborhoods in Tucson for home buyers",
        "Tucson luxury real estate market",
        "Oro Valley Arizona real estate guide",
        "Marana Arizona housing market",
        "Tucson foothills homes market",
        "Southern Arizona retirement communities",
        "Tucson investment property opportunities",
        "Sahuarita Arizona real estate trends",
        "University of Arizona area real estate Tucson",
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
        "Instagram marketing for real estate agents",
        "Facebook ads for real estate listings",
        "creating listing videos that sell",
        "real estate photography for luxury listings",
        "how many photos for MLS listing",
        "photo order for real estate listings",
        "floor plans increase buyer interest",
        "virtual tours for out of state buyers",
        "real estate marketing budget allocation",
        "branded vs unbranded listing photos",
        "single property websites benefits",
        "real estate email marketing with photos",
        "Pinterest for real estate marketing",
        "TikTok real estate marketing trends",
        "YouTube for real estate agents",
        "Google Business Profile for realtors",
        "real estate photography for new agents",
        "building a real estate brand with visuals",
        "before and after virtual staging examples",
        "real estate marketing during slow seasons",
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
        "Zillow 3D home tours adoption",
        "Matterport real estate trends",
        "drone regulations for real estate",
        "smartphone vs professional real estate photos",
        "real estate photography pricing trends",
        "video marketing statistics real estate",
        "virtual staging technology advances",
        "real estate CRM integration with media",
        "AI virtual staging developments",
        "360 photography for real estate",
        "real estate photography business trends",
        "millennial home buyer preferences",
        "Gen Z real estate expectations",
        "remote home buying trends",
        "international buyer real estate trends",
    ],
    "agent_success": [
        "how top producing agents use photography",
        "building a listing presentation with media",
        "winning more listings with professional photos",
        "real estate agent productivity tips",
        "time management for busy agents",
        "client communication best practices",
        "handling multiple listings efficiently",
        "real estate team photography workflows",
        "pricing strategies for competitive markets",
        "open house photography tips",
        "real estate CMA presentation visuals",
        "farming neighborhoods as a realtor",
        "real estate referral generation strategies",
        "building client relationships long term",
        "real estate agent personal branding",
        "leveraging testimonials in marketing",
        "real estate coaching and mentorship",
        "staying motivated in real estate",
        "work life balance for realtors",
        "real estate continuing education value",
    ],
    "seller_guides": [
        "preparing your home for photography",
        "decluttering tips before listing photos",
        "curb appeal improvements that photograph well",
        "staging on a budget for home sellers",
        "what to expect during a photo shoot",
        "why professional photos matter for sellers",
        "timing your listing for best results",
        "home improvements that increase value",
        "Arizona specific home selling tips",
        "selling a pool home in Arizona",
        "selling during Arizona summer",
        "relocating from Arizona guide",
        "selling a luxury home guide",
        "FSBO vs agent for home sales",
        "understanding days on market metrics",
        "selling a home in Tucson guide",
        "Tucson home photography tips",
    ],
}

# Portfolio images directory (your own photos)
BLOG_IMAGES_DIR = Path(__file__).parent.parent / "images" / "blog"


def get_random_blog_image() -> str:
    """Get a random image from the blog images folder."""
    if BLOG_IMAGES_DIR.exists():
        images = list(BLOG_IMAGES_DIR.glob("*.jpg")) + \
                 list(BLOG_IMAGES_DIR.glob("*.jpeg")) + \
                 list(BLOG_IMAGES_DIR.glob("*.png")) + \
                 list(BLOG_IMAGES_DIR.glob("*.webp"))
        if images:
            selected = random.choice(images)
            return f"images/blog/{selected.name}"
    # Fallback - should not happen if images are added
    return "images/blog/ListerPros-001.jpg"


def search_trending_topics() -> dict:
    """
    Use Grok to find current trending topics related to real estate photography.
    Returns a dict with topic, category, and search context.
    """
    # Select a random category and topic as base
    category = random.choice(list(TOPIC_CATEGORIES.keys()))
    base_topic = random.choice(TOPIC_CATEGORIES[category])

    prompt = f"""You are a senior content strategist for ListerPros, Arizona's premier real estate photography company.

{BRAND_GUIDELINES}

Based on the topic seed "{base_topic}", generate a specific, timely blog post topic that would:
1. Provide genuine value to real estate agents in Arizona
2. Help ListerPros rank for relevant SEO keywords
3. Position ListerPros as the authority on real estate photography in Arizona
4. Be specific enough to write a comprehensive, actionable article

The topic should:
- Have clear search intent (someone would actually Google this)
- Be specific and actionable (not too broad)
- Connect to Arizona/Phoenix when possible
- Be timely or evergreen (consider seasonal relevance)

Respond with ONLY a JSON object in this exact format:
{{
    "title": "The complete blog post title (50-65 characters ideal for SEO)",
    "search_query": "A search query to research current information on this topic",
    "angle": "The unique angle or hook that makes this article valuable",
    "target_keywords": ["primary keyword", "secondary keyword", "long-tail keyword"],
    "search_intent": "informational/transactional/navigational"
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
    Use Grok to research the topic and gather current information.
    """
    search_query = topic_data.get("search_query", topic_data["title"])

    prompt = f"""You are researching for a blog post for ListerPros, Arizona's premier real estate photography company.

Topic: "{topic_data['title']}"
Search query: {search_query}

Research and provide:
1. KEY FACTS & STATISTICS - Current data points that support the topic (include sources/timeframes when available)
2. CURRENT TRENDS - What's happening now in this space
3. ARIZONA-SPECIFIC INSIGHTS - Information relevant to Phoenix/Arizona market
4. ACTIONABLE TIPS - Practical advice readers can implement
5. EXPERT PERSPECTIVES - Industry viewpoints or best practices
6. COMMON MISTAKES - What to avoid

Format as detailed bullet points. Include specific numbers, percentages, and data when available.
Focus on accuracy - don't make up statistics."""

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
    prompt = f"""You are a professional blog writer for ListerPros. Write an authoritative, SEO-optimized blog post.

{BRAND_GUIDELINES}

=== ARTICLE DETAILS ===
TOPIC: {topic_data['title']}
ANGLE: {topic_data.get('angle', 'comprehensive guide')}
TARGET KEYWORDS: {', '.join(topic_data.get('target_keywords', []))}
SEARCH INTENT: {topic_data.get('search_intent', 'informational')}

=== RESEARCH NOTES ===
{research}

=== WRITING REQUIREMENTS ===

STRUCTURE:
1. HOOK - Start with a compelling opening that addresses the reader's pain point or goal
2. INTRODUCTION - Set up the value they'll get from reading (2-3 paragraphs)
3. BODY - Comprehensive coverage with H2 and H3 subheadings (main content)
4. ARIZONA CONNECTION - Tie the topic to Arizona/Phoenix market when relevant
5. CONCLUSION - Summarize key takeaways and soft CTA

CONTENT GUIDELINES:
- Write 1,400-1,800 words (comprehensive but not padded)
- Use data and statistics from the research to support points
- Include practical, actionable advice readers can implement today
- Write in second person ("you") to engage the reader
- Break up text with subheadings every 200-300 words
- Use bullet points and numbered lists for scanability
- Include relevant internal context about professional photography benefits

SEO REQUIREMENTS:
- Include primary keyword in first 100 words naturally
- Use target keywords 3-5 times throughout (naturally, not stuffed)
- Write a compelling meta description (150-155 characters) that includes primary keyword
- Create an excerpt that makes people want to click

TONE:
- Professional and authoritative (we're the experts)
- Helpful and educational (genuinely trying to help)
- Conversational but not casual
- Confident without being arrogant
- Arizona-local perspective when relevant

SOFT SELL (weave in naturally, don't force):
- Mention that professional photography makes a difference
- Reference Arizona-specific context that ListerPros understands
- The CTA should feel like helpful advice, not a sales pitch

=== OUTPUT FORMAT ===
Respond with ONLY a JSON object:
{{
    "title": "SEO-optimized title (50-65 characters)",
    "meta_description": "Compelling meta description with keyword (150-155 characters exactly)",
    "content": "Full HTML content using h2, h3, p, ul, ol, li, strong, em, blockquote tags only",
    "excerpt": "2-3 sentence excerpt that hooks readers and includes value proposition",
    "tags": ["tag1", "tag2", "tag3", "tag4", "tag5"]
}}

IMPORTANT:
- Do NOT include the title in the content (it's added separately)
- Use proper HTML formatting
- Make it genuinely valuable - this should be content people want to read and share"""

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
                "max_tokens": 6000,
            },
            timeout=180,
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

    # Select a random image from your portfolio
    featured_image = get_random_blog_image()

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

    # Save the HTML file (slug only, no date prefix for cleaner URLs)
    post_filename = f"{slug}.html"
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

    # Check if post with same slug already exists (avoid duplicates)
    existing_slugs = [p["slug"] for p in posts]
    if slug in existing_slugs:
        print(f"Post with slug '{slug}' already exists, skipping...")
        return None

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
    print(f"   Keywords: {topic_data.get('target_keywords', [])}")

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
        print("ERROR: Failed to save blog post (may be duplicate)")
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
