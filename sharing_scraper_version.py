import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime, timedelta
import time
import random
import xml.etree.ElementTree as ET
from urllib.parse import quote_plus, unquote
import re
import os

class ComprehensiveGoogleNewsScraper:
    def __init__(self, output_directory=None):
        self.session = requests.Session()
        # Set output directory (defaults to Desktop if not specified)
        if output_directory:
            self.output_directory = output_directory
        else:
            # Default to Desktop - works on most systems
            self.output_directory = os.path.join(os.path.expanduser("~"), "Desktop")
        
        # Create output directory if it doesn't exist
        os.makedirs(self.output_directory, exist_ok=True)
        
        # Generic headers - no personal browser fingerprinting
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Cache-Control': 'max-age=0'
        })
    
    def search_google_news_rss(self, query, max_results=50):
        """
        Search Google News using RSS feed - reliable but limited results
        """
        encoded_query = quote_plus(query)
        rss_url = f"https://news.google.com/rss/search?q={encoded_query}&hl=en&gl=US&ceid=US:en"
        
        try:
            print(f"Fetching RSS feed for '{query}'...")
            response = self.session.get(rss_url, timeout=10)
            response.raise_for_status()
            
            root = ET.fromstring(response.content)
            news_items = []
            items = root.findall('.//item')
            
            for i, item in enumerate(items[:max_results]):
                try:
                    title_elem = item.find('title')
                    title = title_elem.text if title_elem is not None else 'No title'
                    
                    link_elem = item.find('link')
                    link = link_elem.text if link_elem is not None else 'No link'
                    
                    desc_elem = item.find('description')
                    description = desc_elem.text if desc_elem is not None else 'No description'
                    
                    pubdate_elem = item.find('pubDate')
                    pub_date = pubdate_elem.text if pubdate_elem is not None else 'Unknown'
                    
                    is_recent = self.is_recent_article(pub_date)
                    
                    news_items.append({
                        'title': title,
                        'link': link,
                        'publish_time': pub_date,
                        'query': query,
                        'is_recent_24h': is_recent
                    })
                    
                except Exception as e:
                    print(f"Error processing RSS item {i+1}: {e}")
                    continue
            
            print(f"RSS: Found {len(news_items)} articles for '{query}'")
            return news_items
            
        except Exception as e:
            print(f"Error fetching RSS for {query}: {e}")
            return []
    
    def search_google_news_html(self, query, max_pages=5):
        """
        Search Google News using HTML scraping - more results but less reliable
        """
        all_news = []
        
        for page in range(max_pages):
            try:
                # Google News search URL with pagination
                base_url = "https://www.google.com/search"
                params = {
                    'q': query,
                    'tbm': 'nws',  # News search
                    'tbs': 'qdr:d1',  # Past 24 hours
                    'start': page * 10,  # Pagination
                    'num': 10
                }
                
                print(f"Scraping page {page + 1} for '{query}'...")
                
                response = self.session.get(base_url, params=params, timeout=15)
                response.raise_for_status()
                
                # Check if we're being blocked
                if "unusual traffic" in response.text.lower() or "captcha" in response.text.lower():
                    print(f"Google is blocking requests on page {page + 1}. Stopping pagination.")
                    break
                
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Find news articles using multiple selectors
                articles = []
                selectors = [
                    'div.SoaBEf',
                    'div.dbsr',
                    'div.g',
                    'div.MjjYud',
                    'div[data-sokoban-container]',
                    'article'
                ]
                
                for selector in selectors:
                    found_articles = soup.select(selector)
                    articles.extend(found_articles)
                    if found_articles:
                        break  # Use the first selector that finds articles
                
                if not articles:
                    print(f"No articles found on page {page + 1}")
                    break
                
                page_news = []
                for article in articles:
                    try:
                        # Extract title
                        title_elem = article.select_one('h3, .DKV0Md, .LC20lb, .JheGif, .n0jPhd')
                        if not title_elem:
                            continue
                        title = title_elem.get_text(strip=True)
                        
                        # Extract link
                        link_elem = article.select_one('a[href]')
                        if not link_elem:
                            continue
                        link = link_elem.get('href')
                        
                        # Clean up Google redirect URLs
                        if link.startswith('/url?q='):
                            link = unquote(link.split('/url?q=')[1].split('&')[0])
                        elif link.startswith('/search?q='):
                            continue
                        elif link.startswith('/'):
                            link = 'https://www.google.com' + link
                        
                        # Extract publish time
                        time_elem = article.select_one('.LfVVr, .f, .OSrXXb, .WG9SHd, .ZE0LJd')
                        publish_time = time_elem.get_text(strip=True) if time_elem else 'Unknown'
                        
                        if title and link and 'javascript:' not in link:
                            page_news.append({
                                'title': title,
                                'link': link,
                                'publish_time': publish_time,
                                'query': query,
                                'is_recent_24h': True  # Since we're filtering by past 24h
                            })
                    
                    except Exception as e:
                        continue
                
                all_news.extend(page_news)
                print(f"Page {page + 1}: Found {len(page_news)} articles")
                
                # If we got fewer than 5 articles, probably reached the end
                if len(page_news) < 5:
                    print(f"Few articles found on page {page + 1}, stopping pagination")
                    break
                
                # Random delay between pages to avoid being blocked
                if page < max_pages - 1:
                    delay = random.uniform(3, 7)
                    print(f"Waiting {delay:.1f} seconds before next page...")
                    time.sleep(delay)
                
            except Exception as e:
                print(f"Error scraping page {page + 1} for {query}: {e}")
                break
        
        print(f"HTML: Found {len(all_news)} articles for '{query}'")
        return all_news
    
    def search_comprehensive(self, query, max_html_pages=5):
        """
        Combine RSS and HTML scraping for comprehensive results
        """
        print(f"\n=== Starting comprehensive search for '{query}' ===")
        
        # Method 1: RSS Feed (reliable but limited)
        rss_news = self.search_google_news_rss(query)
        
        # Method 2: HTML Scraping (more results but less reliable)
        html_news = self.search_google_news_html(query, max_html_pages)
        
        # Combine results
        all_news = rss_news + html_news
        
        # Remove duplicates based on link
        seen_links = set()
        unique_news = []
        for item in all_news:
            if item['link'] not in seen_links:
                seen_links.add(item['link'])
                unique_news.append(item)
        
        print(f"Combined: {len(unique_news)} unique articles for '{query}'")
        return unique_news
    
    def is_recent_article(self, pub_date_str):
        """
        Check if article is from the last 24 hours
        """
        try:
            formats = [
                '%a, %d %b %Y %H:%M:%S %Z',
                '%a, %d %b %Y %H:%M:%S GMT',
                '%a, %d %b %Y %H:%M:%S +0000',
                '%Y-%m-%dT%H:%M:%SZ',
                '%Y-%m-%d %H:%M:%S'
            ]
            
            pub_date = None
            for fmt in formats:
                try:
                    pub_date = datetime.strptime(pub_date_str, fmt)
                    break
                except ValueError:
                    continue
            
            if pub_date is None:
                return False
            
            now = datetime.now()
            twenty_four_hours_ago = now - timedelta(hours=24)
            return pub_date.replace(tzinfo=None) >= twenty_four_hours_ago
            
        except Exception:
            return False
    
    def scrape_all_keywords(self, keywords, max_html_pages=5):
        """
        Scrape news for all keywords using comprehensive approach
        """
        all_news = []
        
        for i, keyword in enumerate(keywords):
            print(f"\n{'='*60}")
            print(f"Processing keyword {i+1}/{len(keywords)}: '{keyword}'")
            print(f"{'='*60}")
            
            news_items = self.search_comprehensive(keyword, max_html_pages)
            all_news.extend(news_items)
            
            print(f"Total articles found for '{keyword}': {len(news_items)}")
            
            # Add delay between keywords
            if i < len(keywords) - 1:
                delay = random.uniform(5, 10)
                print(f"Waiting {delay:.1f} seconds before next keyword...")
                time.sleep(delay)
        
        return all_news
    
    def save_to_excel(self, news_data, filename=None):
        """
        Save news data to Excel file with comprehensive formatting
        """
        if not news_data:
            print("No news data to save!")
            return None
            
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"google_news_{timestamp}.xlsx"
        
        # Create full path
        full_path = os.path.join(self.output_directory, filename)
        
        # Create DataFrame
        df = pd.DataFrame(news_data)
        
        # Add scraped timestamp
        df['scraped_at'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Keep only the desired columns
        column_order = ['title', 'link', 'publish_time', 'query', 'is_recent_24h', 'scraped_at']
        df = df[column_order]
        
        # Save to Excel with multiple sheets
        with pd.ExcelWriter(full_path, engine='openpyxl') as writer:
            # Sheet 1: All articles
            df.to_excel(writer, sheet_name='All_Articles', index=False)
            
            # Sheet 2: Summary by keyword
            summary_data = []
            for keyword in df['query'].unique():
                keyword_df = df[df['query'] == keyword]
                summary_data.append({
                    'Keyword': keyword,
                    'Total_Articles': len(keyword_df),
                    'Recent_24h': len(keyword_df[keyword_df['is_recent_24h'] == True])
                })
            
            summary_df = pd.DataFrame(summary_data)
            summary_df.to_excel(writer, sheet_name='Summary', index=False)
            
            # Auto-adjust column widths
            for sheet_name in writer.sheets:
                worksheet = writer.sheets[sheet_name]
                for column in worksheet.columns:
                    max_length = 0
                    column_letter = column[0].column_letter
                    for cell in column:
                        try:
                            if len(str(cell.value)) > max_length:
                                max_length = len(str(cell.value))
                        except:
                            pass
                    adjusted_width = min(max_length + 2, 80)
                    worksheet.column_dimensions[column_letter].width = adjusted_width
        
        print(f"\nResults saved to: {full_path}")
        print(f"Total unique articles: {len(df)}")
        
        return full_path

def main():
    # =============================================
    # CONFIGURATION SECTION
    # =============================================
    
    # EXAMPLE KEYWORDS - REPLACE WITH YOUR OWN
    keywords = ["Technology", "Science", "Business"]
    
    # OUTPUT DIRECTORY OPTIONS:
    # None = Desktop (recommended for sharing)
    # "Downloads" = Downloads folder
    # Custom path = specify your own location
    output_directory = None
    
    # SCRAPING SETTINGS
    max_html_pages = 5  # Number of pages to scrape per keyword
    
    # =============================================
    # END OF CONFIGURATION
    # =============================================
    
    print("=" * 80)
    print("GOOGLE NEWS SCRAPER")
    print("=" * 80)
    print("⚠️  DISCLAIMER: This script is for educational purposes only.")
    print("   Please ensure compliance with Google's Terms of Service.")
    print("   Use responsibly and respect rate limits.")
    print("=" * 80)
    print(f"Keywords: {', '.join(keywords)}")
    print(f"Max HTML pages per keyword: {max_html_pages}")
    print(f"Output directory: {output_directory if output_directory else 'Desktop'}")
    print("=" * 80)
    
    # Initialize scraper
    scraper = ComprehensiveGoogleNewsScraper(output_directory)
    
    # Scrape news
    all_news = scraper.scrape_all_keywords(keywords, max_html_pages)
    
    if all_news:
        # Save results
        filename = scraper.save_to_excel(all_news)
        print(f"\n✅ Scraping completed successfully!")
        print(f"📊 Results saved to: {filename}")
        
        # Summary
        print(f"\n📈 SUMMARY:")
        print(f"   • Total articles: {len(all_news)}")
        print(f"   • Keywords processed: {len(keywords)}")
        print(f"   • Average per keyword: {len(all_news) // len(keywords) if keywords else 0}")
        
    else:
        print("❌ No news articles found.")

if __name__ == "__main__":
    main()
