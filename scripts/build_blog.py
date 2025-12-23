#!/usr/bin/env python3
"""
ListerPros Blog Builder
Converts markdown posts to SEO-optimized HTML files and generates blog index pages.

Usage:
    python3 build_blog.py              # Build all posts
    python3 build_blog.py --watch      # Watch for changes and rebuild
    python3 build_blog.py --single FILE  # Build a single post

Output:
    ./dist/blog/           - Individual post HTML files
    ./dist/blog/index.html - Blog index page
    ./dist/sitemap.xml     - XML sitemap for SEO

Note: No external dependencies required - uses only Python standard library.
"""

import os
import re
import sys
import json
import hashlib
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
import html

# Configuration
BASE_DIR = Path(__file__).parent.parent
POSTS_DIR = BASE_DIR
TEMPLATES_DIR = BASE_DIR / "templates"
DIST_DIR = BASE_DIR / "dist"
BLOG_DIR = DIST_DIR / "blog"

SITE_URL = "https://listerpros.com"
POSTS_PER_PAGE = 12

# Markdown to HTML conversion (simple implementation - no external deps)
class MarkdownConverter:
    """Simple markdown to HTML converter for blog posts."""

    def __init__(self, content: str):
        self.content = content
        self.toc = []

    def convert(self) -> str:
        """Convert markdown to HTML."""
        lines = self.content.split('\n')
        result = []
        in_list = False
        in_ordered_list = False
        in_code_block = False
        in_blockquote = False
        in_table = False
        table_headers = []
        paragraph_buffer = []

        for line in lines:
            # Code blocks
            if line.startswith('```'):
                if in_code_block:
                    result.append('</code></pre>')
                    in_code_block = False
                else:
                    lang = line[3:].strip()
                    result.append(f'<pre><code class="language-{lang}">' if lang else '<pre><code>')
                    in_code_block = True
                continue

            if in_code_block:
                result.append(html.escape(line))
                continue

            # Blockquotes
            if line.startswith('>'):
                if not in_blockquote:
                    result.append('<blockquote>')
                    in_blockquote = True
                result.append(f'<p>{self._inline_convert(line[1:].strip())}</p>')
                continue
            elif in_blockquote and not line.startswith('>'):
                result.append('</blockquote>')
                in_blockquote = False

            # Tables
            if '|' in line and line.strip().startswith('|'):
                cells = [c.strip() for c in line.strip('|').split('|')]

                if not in_table:
                    in_table = True
                    table_headers = cells
                    result.append('<table>')
                    result.append('<thead><tr>')
                    for cell in cells:
                        result.append(f'<th>{self._inline_convert(cell)}</th>')
                    result.append('</tr></thead>')
                    result.append('<tbody>')
                elif all(set(c.strip()) <= set('-:') for c in cells):
                    # Header separator row, skip
                    continue
                else:
                    result.append('<tr>')
                    for cell in cells:
                        result.append(f'<td>{self._inline_convert(cell)}</td>')
                    result.append('</tr>')
                continue
            elif in_table and not ('|' in line):
                result.append('</tbody></table>')
                in_table = False

            # Headers
            if line.startswith('#'):
                level = len(re.match(r'^#+', line).group())
                text = line[level:].strip()
                slug = self._slugify(text)
                self.toc.append({'level': level, 'text': text, 'slug': slug})
                result.append(f'<h{level} id="{slug}">{self._inline_convert(text)}</h{level}>')
                continue

            # Unordered lists
            if re.match(r'^[\*\-]\s', line.strip()):
                if not in_list:
                    result.append('<ul>')
                    in_list = True
                text = re.sub(r'^[\*\-]\s', '', line.strip())
                result.append(f'<li>{self._inline_convert(text)}</li>')
                continue
            elif in_list and not re.match(r'^[\*\-]\s', line.strip()) and line.strip():
                result.append('</ul>')
                in_list = False

            # Ordered lists
            if re.match(r'^\d+\.\s', line.strip()):
                if not in_ordered_list:
                    result.append('<ol>')
                    in_ordered_list = True
                text = re.sub(r'^\d+\.\s', '', line.strip())
                result.append(f'<li>{self._inline_convert(text)}</li>')
                continue
            elif in_ordered_list and not re.match(r'^\d+\.\s', line.strip()) and line.strip():
                result.append('</ol>')
                in_ordered_list = False

            # Horizontal rules
            if re.match(r'^[\-\*_]{3,}\s*$', line.strip()):
                result.append('<hr>')
                continue

            # Paragraphs
            if line.strip():
                paragraph_buffer.append(self._inline_convert(line))
            else:
                if paragraph_buffer:
                    result.append(f'<p>{" ".join(paragraph_buffer)}</p>')
                    paragraph_buffer = []

        # Close any open elements
        if paragraph_buffer:
            result.append(f'<p>{" ".join(paragraph_buffer)}</p>')
        if in_list:
            result.append('</ul>')
        if in_ordered_list:
            result.append('</ol>')
        if in_blockquote:
            result.append('</blockquote>')
        if in_table:
            result.append('</tbody></table>')

        return '\n'.join(result)

    def _inline_convert(self, text: str) -> str:
        """Convert inline markdown (bold, italic, links, etc.)."""
        # Images
        text = re.sub(r'!\[([^\]]*)\]\(([^\)]+)\)', r'<img src="\2" alt="\1">', text)

        # Links
        text = re.sub(r'\[([^\]]+)\]\(([^\)]+)\)', r'<a href="\2">\1</a>', text)

        # Bold
        text = re.sub(r'\*\*([^\*]+)\*\*', r'<strong>\1</strong>', text)
        text = re.sub(r'__([^_]+)__', r'<strong>\1</strong>', text)

        # Italic
        text = re.sub(r'\*([^\*]+)\*', r'<em>\1</em>', text)
        text = re.sub(r'_([^_]+)_', r'<em>\1</em>', text)

        # Inline code
        text = re.sub(r'`([^`]+)`', r'<code>\1</code>', text)

        return text

    def _slugify(self, text: str) -> str:
        """Convert text to URL-friendly slug."""
        slug = text.lower()
        slug = re.sub(r'[^\w\s-]', '', slug)
        slug = re.sub(r'[\s_]+', '-', slug)
        slug = re.sub(r'-+', '-', slug)
        return slug.strip('-')


def parse_simple_yaml(yaml_str: str) -> dict:
    """Simple YAML parser for frontmatter (handles basic key: value and lists)."""
    result = {}
    lines = yaml_str.strip().split('\n')
    current_key = None

    for line in lines:
        # Skip empty lines
        if not line.strip():
            continue

        # Check for key: value pattern
        match = re.match(r'^(\w+):\s*(.*)$', line)
        if match:
            key = match.group(1)
            value = match.group(2).strip()

            # Handle quoted strings
            if value.startswith('"') and value.endswith('"'):
                value = value[1:-1]
            elif value.startswith("'") and value.endswith("'"):
                value = value[1:-1]

            # Handle arrays like ["tag1", "tag2"]
            if value.startswith('[') and value.endswith(']'):
                # Parse JSON-style array
                try:
                    items = re.findall(r'"([^"]*)"', value)
                    if not items:
                        items = re.findall(r"'([^']*)'", value)
                    value = items
                except:
                    value = []

            # Handle empty value (might be start of list)
            if value == '':
                current_key = key
                result[key] = []
                continue

            result[key] = value
            current_key = key

        # Handle list items (  - value)
        elif line.strip().startswith('-') and current_key:
            item = line.strip()[1:].strip()
            if item.startswith('"') and item.endswith('"'):
                item = item[1:-1]
            elif item.startswith("'") and item.endswith("'"):
                item = item[1:-1]
            if isinstance(result.get(current_key), list):
                result[current_key].append(item)

    return result


def parse_frontmatter(content: str) -> tuple:
    """Parse YAML frontmatter from markdown file."""
    if content.startswith('---'):
        parts = content.split('---', 2)
        if len(parts) >= 3:
            try:
                metadata = parse_simple_yaml(parts[1])
                body = parts[2].strip()
                return metadata, body
            except Exception as e:
                print(f"    Warning: Failed to parse frontmatter: {e}")
                pass
    return {}, content


def format_date(date_val) -> str:
    """Format date for display."""
    if isinstance(date_val, str):
        try:
            date_obj = datetime.strptime(date_val, '%Y-%m-%d')
        except ValueError:
            return date_val
    elif isinstance(date_val, datetime):
        date_obj = date_val
    else:
        date_obj = datetime.now()

    return date_obj.strftime('%B %d, %Y')


def get_related_posts(current_post: dict, all_posts: List[dict], count: int = 3) -> List[dict]:
    """Find related posts based on matching tags."""
    current_tags = set(current_post.get('tags', []))
    current_slug = current_post.get('slug', '')

    scored = []
    for post in all_posts:
        if post.get('slug') == current_slug:
            continue
        post_tags = set(post.get('tags', []))
        score = len(current_tags & post_tags)
        if score > 0:
            scored.append((score, post))

    scored.sort(key=lambda x: x[0], reverse=True)
    return [p for _, p in scored[:count]]


def build_post(md_path: Path, template: str, all_posts: List[dict]) -> Optional[str]:
    """Build a single post from markdown to HTML."""
    content = md_path.read_text(encoding='utf-8')
    metadata, body = parse_frontmatter(content)

    if not metadata:
        print(f"  Warning: No frontmatter found in {md_path.name}")
        return None

    # Convert markdown to HTML
    converter = MarkdownConverter(body)
    html_content = converter.convert()

    # Generate tags HTML
    tags = metadata.get('tags', [])
    tags_html = '\n'.join([f'<a href="/blog/tag/{t}" class="tag">{t}</a>' for t in tags])

    # Get related posts
    related = get_related_posts(metadata, all_posts)
    related_html = ''
    for post in related:
        related_html += f'''
            <article class="related-card">
                <div class="blog-card-image">
                    <img src="/blog/images/{post.get('slug', 'default')}.jpg" alt="{html.escape(post.get('title', ''))}">
                </div>
                <div class="related-card-content">
                    <h3><a href="/blog/{post.get('slug', '')}">{html.escape(post.get('title', ''))}</a></h3>
                    <p>{html.escape(post.get('excerpt', '')[:120])}...</p>
                </div>
            </article>
        '''

    # Build the HTML
    html_output = template
    replacements = {
        '{{title}}': html.escape(metadata.get('title', 'Untitled')),
        '{{description}}': html.escape(metadata.get('description', '')),
        '{{excerpt}}': html.escape(metadata.get('excerpt', '')),
        '{{author}}': html.escape(metadata.get('author', 'ListerPros Team')),
        '{{date}}': str(metadata.get('date', '')),
        '{{formatted_date}}': format_date(metadata.get('date')),
        '{{slug}}': metadata.get('slug', md_path.stem),
        '{{readingTime}}': metadata.get('readingTime', '5 min read'),
        '{{tags_html}}': tags_html,
        '{{content}}': html_content,
        '{{related_posts}}': related_html,
        '{{year}}': str(datetime.now().year),
    }

    for key, value in replacements.items():
        html_output = html_output.replace(key, str(value))

    return html_output


def build_index(posts: List[dict], template: str, page: int = 1) -> str:
    """Build the blog index page."""
    # Sort by date descending
    sorted_posts = sorted(posts, key=lambda x: str(x.get('date', '')), reverse=True)

    # Paginate
    start = (page - 1) * POSTS_PER_PAGE
    end = start + POSTS_PER_PAGE
    page_posts = sorted_posts[start:end]

    # Featured post (most recent)
    featured = sorted_posts[0] if sorted_posts else {}

    # Generate post cards HTML
    cards_html = ''
    for post in page_posts[1:] if page == 1 else page_posts:  # Skip featured on page 1
        tags_html = ''.join([f'<span class="card-tag">{t}</span>' for t in post.get('tags', [])[:3]])
        cards_html += f'''
            <article class="blog-card">
                <div class="blog-card-image">
                    <img src="/blog/images/{post.get('slug', 'default')}.jpg" alt="{html.escape(post.get('title', ''))}">
                </div>
                <div class="blog-card-content">
                    <div class="blog-card-meta">
                        <span>{format_date(post.get('date'))}</span>
                        <span>{post.get('readingTime', '5 min read')}</span>
                    </div>
                    <h3><a href="/blog/{post.get('slug', '')}">{html.escape(post.get('title', ''))}</a></h3>
                    <p>{html.escape(post.get('excerpt', '')[:150])}...</p>
                    <div class="blog-card-tags">
                        {tags_html}
                    </div>
                </div>
            </article>
        '''

    # Replace placeholders
    html_output = template
    replacements = {
        '{{featured_title}}': html.escape(featured.get('title', '')),
        '{{featured_excerpt}}': html.escape(featured.get('excerpt', '')),
        '{{featured_date}}': format_date(featured.get('date')),
        '{{featured_reading_time}}': featured.get('readingTime', '5 min read'),
        '{{blog_posts}}': cards_html,
        '{{year}}': str(datetime.now().year),
    }

    for key, value in replacements.items():
        html_output = html_output.replace(key, str(value))

    return html_output


def build_sitemap(posts: List[dict]) -> str:
    """Generate XML sitemap for SEO."""
    urls = []

    # Main pages
    main_pages = ['', '/services', '/portfolio', '/blog', '/about', '/contact']
    for page in main_pages:
        urls.append(f'''
    <url>
        <loc>{SITE_URL}{page}</loc>
        <changefreq>weekly</changefreq>
        <priority>{'1.0' if page == '' else '0.8'}</priority>
    </url>''')

    # Blog posts
    for post in posts:
        date = post.get('date', '')
        if isinstance(date, datetime):
            date = date.strftime('%Y-%m-%d')
        urls.append(f'''
    <url>
        <loc>{SITE_URL}/blog/{post.get('slug', '')}</loc>
        <lastmod>{date}</lastmod>
        <changefreq>monthly</changefreq>
        <priority>0.6</priority>
    </url>''')

    return f'''<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
{''.join(urls)}
</urlset>'''


def main():
    """Main build function."""
    print("=" * 60)
    print("ListerPros Blog Builder")
    print("=" * 60)

    # Create output directories
    BLOG_DIR.mkdir(parents=True, exist_ok=True)

    # Load templates
    post_template = (TEMPLATES_DIR / "blog-post.html").read_text(encoding='utf-8')
    index_template = (TEMPLATES_DIR / "blog-index.html").read_text(encoding='utf-8')

    # Get all markdown files
    md_files = list(POSTS_DIR.glob("*.md"))
    md_files = [f for f in md_files if not f.name.startswith('.') and f.name != '2025-blog-topics.md']

    print(f"\nFound {len(md_files)} markdown files")

    # First pass: collect all post metadata
    all_posts = []
    for md_file in md_files:
        content = md_file.read_text(encoding='utf-8')
        metadata, _ = parse_frontmatter(content)
        if metadata:
            metadata['source_file'] = md_file
            all_posts.append(metadata)

    print(f"Parsed {len(all_posts)} posts with valid frontmatter")

    # Second pass: build all posts
    print("\nBuilding posts...")
    built_count = 0
    for post in all_posts:
        md_file = post['source_file']
        html_content = build_post(md_file, post_template, all_posts)

        if html_content:
            slug = post.get('slug', md_file.stem)
            output_path = BLOG_DIR / f"{slug}.html"
            output_path.write_text(html_content, encoding='utf-8')
            built_count += 1

            if built_count % 100 == 0:
                print(f"  Built {built_count} posts...")

    print(f"  Built {built_count} post HTML files")

    # Build index pages
    print("\nBuilding index pages...")
    total_pages = (len(all_posts) + POSTS_PER_PAGE - 1) // POSTS_PER_PAGE

    index_html = build_index(all_posts, index_template, page=1)
    (BLOG_DIR / "index.html").write_text(index_html, encoding='utf-8')

    for page in range(2, total_pages + 1):
        page_html = build_index(all_posts, index_template, page=page)
        (BLOG_DIR / f"page-{page}.html").write_text(page_html, encoding='utf-8')

    print(f"  Built {total_pages} index pages")

    # Build sitemap
    print("\nBuilding sitemap...")
    sitemap = build_sitemap(all_posts)
    (DIST_DIR / "sitemap.xml").write_text(sitemap, encoding='utf-8')
    print("  Built sitemap.xml")

    # Summary
    print("\n" + "=" * 60)
    print("Build Complete!")
    print("=" * 60)
    print(f"\nOutput directory: {DIST_DIR}")
    print(f"  - {built_count} blog post HTML files")
    print(f"  - {total_pages} index pages")
    print(f"  - 1 sitemap.xml")
    print(f"\nTo deploy: Upload the 'dist' folder to Netlify")


if __name__ == "__main__":
    main()
