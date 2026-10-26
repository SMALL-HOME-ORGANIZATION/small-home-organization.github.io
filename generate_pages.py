import os
import sys
import urllib.request
import xml.etree.ElementTree as ET
import json
import shutil
import random
from string import Template

sitemap_url = sys.argv[1] if len(sys.argv) > 1 else "https://stylesdays.com/sitemap_index.xml"
print(f"Fetching sitemap from: {sitemap_url}")

def fetch_data(url):
    req = urllib.request.Request(
        url, 
        headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    )
    try:
        with urllib.request.urlopen(req) as response:
            return response.read()
    except Exception as e:
        print(f"Error fetching {url}: {e}")
        return None

def parse_sitemap(url, found_urls=None):
    if found_urls is None:
        found_urls = set()
    xml_data = fetch_data(url)
    if not xml_data:
        return found_urls
    try:
        root = ET.fromstring(xml_data)
        namespace = {'ns': 'http://www.sitemaps.org/schemas/sitemap/0.9'}
        sitemaps = root.findall('ns:sitemap', namespace)
        if sitemaps:
            for sm in sitemaps:
                loc = sm.find('ns:loc', namespace)
                if loc is not None and loc.text:
                    print(f"Found sub-sitemap: {loc.text}")
                    parse_sitemap(loc.text, found_urls)
        else:
            urls = root.findall('ns:url', namespace)
            for u in urls:
                loc = u.find('ns:loc', namespace)
                if loc is not None and loc.text:
                    found_urls.add(loc.text.strip())
    except Exception as e:
        print(f"Error parsing XML for {url}: {e}")
    return found_urls

# 1. Gather all URLs from Sitemap
all_urls = parse_sitemap(sitemap_url)
print(f"Total unique URLs found: {len(all_urls)}")

# 2. Fetch Live WordPress Data (Titles, Excerpts, Images)
posts_data = {}
page = 1
per_page = 100

while True:
    print(f"Fetching WordPress REST API batch {page}...")
    wp_api_url = f"https://stylesdays.com/wp-json/wp/v2/posts?per_page={per_page}&page={page}&_embed=1"
    wp_data = fetch_data(wp_api_url)
    
    if not wp_data:
        break
        
    try:
        posts = json.loads(wp_data.decode('utf-8'))
        if not posts or len(posts) == 0:
            break
            
        for post in posts:
            slug = post.get('slug')
            if not slug:
                continue
            
            title = post.get('title', {}).get('rendered', slug.replace('-', ' ').title())
            excerpt = post.get('excerpt', {}).get('rendered', '')
            
            # Clean HTML tags from excerpt
            import re
            clean_excerpt = re.sub('<[^<]+>', '', excerpt).strip()
            if not clean_excerpt:
                clean_excerpt = f"Explore our complete {title} guide on stylesdays.com. This curated feature breaks down practical room styling ideas and layouts."
            
            # Extract featured image
            image_url = "https://images.unsplash.com/photo-1616594039964-ae9021a400a0?auto=format&fit=crop&w=1200&q=85"
            try:
                embedded = post.get('_embedded', {})
                featured_media = embedded.get('wp:featuredmedia', [{}])[0]
                if 'source_url' in featured_media:
                    image_url = featured_media['source_url']
            except:
                pass

            posts_data[slug] = {
                'title': title,
                'description': clean_excerpt,
                'image': image_url,
                'canonical_url': f"https://stylesdays.com/{slug}/"
            }
            
        page += 1
    except Exception as e:
        print(f"Error parsing JSON on page {page}: {e}")
        break

print(f"Loaded {len(posts_data)} posts with metadata from WordPress REST API.")

# 3. HTML Template (Using string.Template so Tailwind CSS braces {} don't break Python)
HIGH_CONVERTING_TEMPLATE = Template("""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>$title | stylesdays Editorial Hub</title>
  <meta name="description" content="$description">
  
  <!-- OpenGraph Metadata for Pinterestbot Rich Pin Crawler -->
  <meta property="og:type" content="article">
  <meta property="og:title" content="$title">
  <meta property="og:description" content="$description">
  <meta property="og:image" content="$image">
  <meta property="og:site_name" content="stylesdays Editorial Hub">
  <link rel="canonical" href="$canonical_url" />
  
  <!-- Tailwind CSS CDN -->
  <script src="https://cdn.tailwindcss.com"></script>
  
  <!-- Google Fonts: Inter & Playfair Display -->
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin="">
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Playfair+Display:ital,wght@0,600;0,700;1,400&family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap" rel="stylesheet">
  
  <style>
    body {
      font-family: 'Plus Jakarta Sans', 'Inter', sans-serif;
      -webkit-font-smoothing: antialiased;
      background-color: #F8F9FA;
      color: #1E1E1E;
    }
    .font-serif-title, .font-serif-editorial {
      font-family: 'Playfair Display', Georgia, serif;
    }
    @keyframes subtlePulse {
      0%, 100% { transform: scale(1); box-shadow: 0 10px 25px -5px rgba(230, 0, 35, 0.4); }
      50% { transform: scale(1.015); box-shadow: 0 18px 30px -5px rgba(230, 0, 35, 0.55); }
    }
    .pinterest-cta-pulse {
      animation: subtlePulse 2.8s ease-in-out infinite;
    }
    .pinterest-cta-pulse:hover {
      animation: none;
      transform: scale(1.02);
    }
  </style>
</head>
<body class="min-h-screen flex flex-col selection:bg-[#E60023] selection:text-white">

  <!-- TOP HEADER / BRAND TRUST BAR -->
  <header class="w-full bg-white/95 backdrop-blur-md border-b border-gray-100 sticky top-0 z-40 shadow-sm">
    <div class="max-w-4xl mx-auto px-4 py-3 flex items-center justify-between">
      <div class="flex items-center space-x-2.5">
        <div class="w-8 h-8 rounded-full bg-[#E60023] flex items-center justify-center text-white shadow-sm flex-shrink-0">
          <svg class="w-4 h-4 fill-current" viewBox="0 0 24 24">
            <path d="M12 0C5.373 0 0 5.373 0 12c0 5.084 3.163 9.426 7.627 11.174-.105-.949-.2-2.405.042-3.441.218-.937 1.407-5.965 1.407-5.965s-.359-.719-.359-1.782c0-1.668.967-2.914 2.171-2.914 1.023 0 1.518.769 1.518 1.69 0 1.029-.655 2.568-.994 3.995-.283 1.194.599 2.169 1.777 2.169 2.133 0 3.772-2.249 3.772-5.495 0-2.873-2.064-4.882-5.012-4.882-3.414 0-5.418 2.561-5.418 5.207 0 1.031.397 2.138.893 2.738.098.119.112.224.083.345-.09.375-.291 1.199-.334 1.373-.053.22-.174.267-.402.161-1.499-.698-2.436-2.889-2.436-4.649 0-3.785 2.75-7.262 7.929-7.262 4.163 0 7.398 2.967 7.398 6.931 0 4.136-2.607 7.464-6.227 7.464-1.216 0-2.359-.631-2.75-1.378l-.748 2.853c-.271 1.043-1.002 2.35-1.492 3.146C9.57 23.812 10.763 24 12 24c6.627 0 12-5.373 12-12 0-6.627-5.373-12-12-12z"></path>
          </svg>
        </div>
        <div class="flex flex-col">
          <span class="text-xs font-semibold uppercase tracking-wider text-gray-400">Curated Pin Forwarder</span>
          <span class="text-sm font-medium text-gray-800 flex items-center gap-1">
            Verified Source Link
            <svg class="w-3.5 h-3.5 text-blue-500 fill-current" viewBox="0 0 20 20">
              <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd"></path>
            </svg>
          </span>
        </div>
      </div>
    </div>
  </header>

  <!-- MAIN REDIRECT CONTAINER -->
  <main class="max-w-4xl w-full mx-auto px-4 py-8 md:py-10 flex-grow flex flex-col justify-center">

    <!-- ARTICLE BRIDGE CARD -->
    <article class="bg-white rounded-3xl shadow-[0_15px_35px_-5px_rgba(0,0,0,0.06),0_0_1px_1px_rgba(0,0,0,0.03)] border border-gray-100/80 overflow-hidden flex flex-col">
      
      <!-- Hero Image Container -->
      <div class="relative w-full aspect-[16/10] sm:aspect-[16/9] bg-gray-100 overflow-hidden group cursor-pointer" onclick="window.location.href='$canonical_url'">
        <img src="$image" alt="$title" class="relative z-10 w-full h-full object-cover transition-transform duration-700 ease-out group-hover:scale-105">
        
        <!-- Category Badge -->
        <div class="absolute top-4 left-4 z-20 flex items-center gap-2">
          <span class="bg-white/95 backdrop-blur-md text-stone-900 text-xs font-bold uppercase tracking-wider px-3.5 py-1.5 rounded-full shadow-sm border border-stone-200">$category</span>
        </div>

        <!-- Floating Destination Domain Pill -->
        <div class="absolute bottom-4 right-4 z-20 flex items-center space-x-1.5 bg-black/80 backdrop-blur-md text-white text-xs font-medium px-3.5 py-1.5 rounded-full shadow-lg border border-white/20">
          <span class="text-gray-300">Published on:</span>
          <span class="tracking-wide font-semibold text-white">stylesdays.com</span>
        </div>
        
        <!-- Progress Overlay bar directly on image bottom -->
        <div class="absolute bottom-0 left-0 right-0 h-1.5 bg-black/20 z-20 overflow-hidden">
          <div class="h-full bg-[#E60023] transition-all duration-100 ease-linear" style="width: 100%;"></div>
        </div>
      </div>

      <!-- Content Section -->
      <div class="p-6 sm:p-10 flex flex-col flex-grow">
        
        <!-- Meta row -->
        <div class="flex items-center justify-between text-xs text-gray-500 font-medium mb-4">
          <div class="flex items-center space-x-2">
            <span class="flex items-center gap-1.5 text-stone-800 font-semibold">
              <svg class="w-4 h-4 text-[#15803D]" fill="currentColor" viewBox="0 0 20 20">
                <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd"></path>
              </svg>
              <span>stylesdays Editorial Team</span>
            </span>
            <span class="text-gray-300">•</span>
            <span>5 min full read</span>
          </div>
        </div>

        <!-- Article Title -->
        <h1 class="font-serif-title text-2xl sm:text-4xl font-bold text-gray-900 leading-tight mb-5 hover:text-[#E60023] transition">
          <a href="$canonical_url">$title</a>
        </h1>

        <!-- Article Description / Excerpt -->
        <p class="text-gray-600 text-sm sm:text-lg leading-relaxed mb-6 font-normal">
          $description
        </p>

        <!-- High-Impact Primary Pinterest-Red CTA Button -->
        <a href="$canonical_url" rel="noopener" class="pinterest-cta-pulse w-full bg-[#E60023] hover:bg-[#ad081b] text-white text-base sm:text-lg font-semibold py-4 px-6 rounded-2xl flex items-center justify-center space-x-2.5 transition duration-150 shadow-lg text-center cursor-pointer mb-6">
          <span>Read Full Guide on stylesdays.com</span>
          <svg class="w-5 h-5 transform group-hover:translate-x-1 transition-transform" fill="none" stroke="currentColor" stroke-width="2.5" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" d="M14 5l7 7m0 0l-7 7m7-7H3"></path>
          </svg>
        </a>

        <!-- Social Proof & Trust Badges Section -->
        <div class="flex flex-wrap items-center justify-center gap-4 sm:gap-8 text-xs text-gray-500 font-medium mb-8 bg-gray-50 p-4 rounded-xl border border-gray-100">
          <div class="flex items-center space-x-1.5">
            <svg class="w-4 h-4 text-emerald-500" fill="currentColor" viewBox="0 0 20 20">
              <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd"></path>
            </svg>
            <span>Safe Official Link</span>
          </div>
          <div class="flex items-center space-x-1.5">
            <svg class="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"></path>
            </svg>
            <span>Lightning Fast</span>
          </div>
          <div class="flex items-center space-x-1.5">
            <svg class="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z"></path>
            </svg>
            <span>Direct Connection</span>
          </div>
        </div>
        
        <!-- Category & Spec Links -->
        <div class="pt-6 border-t border-gray-100 flex flex-col sm:flex-row items-center justify-between gap-4">
          <div class="text-xs text-gray-500 text-center sm:text-left">
            <span>Explore more in:</span>
            <a href="https://stylesdays.com/category/$category_slug/" rel="noopener" class="text-[#E60023] hover:underline font-semibold ml-1">$category &rarr;</a>
          </div>
          <div class="text-xs text-gray-400 font-mono truncate max-w-xs">
            $canonical_url
          </div>
        </div>

      </div>
    </article>

    <!-- 7. MORE FROM STYLESDAYS.COM SITEMAP CATALOG -->
    <section class="mt-14 pt-10 border-t border-gray-200">
      <div class="flex flex-wrap items-center justify-between gap-4 mb-8">
        <div>
          <h2 class="font-serif-title text-2xl sm:text-3xl font-bold text-gray-900">Featured Posts</h2>
        </div>
      </div>
      
      <!-- Related Posts Grid -->
      <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
        $related_posts_html
      </div>
    </section>

  </main>
  
  <footer class="w-full border-t border-gray-200/80 bg-white py-6 mt-auto text-center text-xs text-gray-500">
    <div class="max-w-4xl mx-auto px-4 flex flex-col sm:flex-row items-center justify-between gap-3">
      <span>&copy; 2026 StylesDays Partnership Hub.</span>
      <span>100% Pinterest Compliant. Secure Redirect.</span>
    </div>
  </footer>
</body>
</html>
""")

def get_related_posts_html(current_slug, posts_data):
    """Pick 3 random posts (excluding the current one) to display in the bottom grid."""
    available_slugs = [s for s in posts_data.keys() if s != current_slug]
    
    if not available_slugs:
        return ""
        
    selected_slugs = random.sample(available_slugs, min(3, len(available_slugs)))
    cards_html = ""
    
    for s in selected_slugs:
        p = posts_data[s]
        img = p.get('image', 'https://images.unsplash.com/photo-1600210492486-724fe5c67fb0?auto=format&fit=crop&w=800&q=80')
        title = p.get('title', 'StylesDays Guide')
        summary = p.get('description', '')
        if len(summary) > 120:
            summary = summary[:117] + '...'
            
        # Determine Category for the card
        cat = "Home Decor"
        if "hack" in s: cat = "IKEA Hacks"
        elif "storage" in s or "pax" in s: cat = "IKEA Storage"
        elif "bedroom" in s: cat = "IKEA Bedroom"
        
        card = f"""
        <div class="bg-white rounded-2xl border border-gray-200/80 overflow-hidden shadow-sm hover:shadow-lg transition-all duration-300 flex flex-col justify-between cursor-pointer group" onclick="window.location.href='/{s}/'">
          <div>
            <div class="aspect-[16/10] bg-gray-100 overflow-hidden relative">
              <img src="{img}" alt="{title}" class="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500">
              <span class="absolute top-3 left-3 bg-white/95 backdrop-blur-sm text-gray-900 text-[10px] font-bold uppercase tracking-wider px-2.5 py-1 rounded-full shadow-sm">
                {cat}
              </span>
            </div>
            <div class="p-5">
              <h3 class="font-serif-title text-lg font-bold text-gray-900 group-hover:text-[#E60023] transition-colors leading-snug mb-2">
                {title}
              </h3>
              <p class="text-xs text-gray-600 line-clamp-2 leading-relaxed">
                {summary}
              </p>
            </div>
          </div>
          <div class="px-5 py-3 bg-gray-50 border-t border-gray-100 flex items-center justify-between text-[11px] text-gray-500 font-medium">
            <span><strong class="text-gray-700">stylesdays.com</strong></span>
            <span class="text-[#E60023] font-bold group-hover:underline">Read Guide &rarr;</span>
          </div>
        </div>
        """
        cards_html += card
        
    return cards_html

print("\nCleaning up old generated slug folders and generating new pages...")

for slug, data in posts_data.items():
    # Detect specific categories for the template
    category = "Home Decor"
    category_slug = "home-decor"
    
    if "hack" in slug:
        category = "IKEA Hacks"
        category_slug = "ikea-hacks"
    elif "storage" in slug or "pax" in slug or "closet" in slug:
        category = "IKEA Storage"
        category_slug = "ikea-storage"
    elif "daybed" in slug or "guest" in slug:
        category = "Guest Bedroom & Daybeds"
        category_slug = "guest-bedroom-ideas-daybed"
    elif "bedroom" in slug:
        category = "Bedroom Design"
        category_slug = "bedroom"

    # Generate the 3 dynamic related posts
    related_posts_html = get_related_posts_html(slug, posts_data)
    
    # 1. Purge the existing folder if it exists (prevents orphaned files)
    shutil.rmtree(slug, ignore_errors=True)
    
    # 2. Create fresh folder
    os.makedirs(slug, exist_ok=True)
    file_path = os.path.join(slug, 'index.html')
    
    # 3. Inject variables safely into the HTML string
    page_content = HIGH_CONVERTING_TEMPLATE.safe_substitute(
        title=data['title'],
        description=data['description'],
        canonical_url=data['canonical_url'],
        image=data['image'],
        category=category,
        category_slug=category_slug,
        related_posts_html=related_posts_html
    )
    
    # 4. Write to disk
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(page_content)

print("\nAll highly-converting editorial hub pages successfully generated with dynamic related posts and active CTAs!")
