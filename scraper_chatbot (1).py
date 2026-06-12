"""
Crawler for hobbygames.ru.
"""

import json
import pathlib
import random
import re
import shutil
import time
from typing import Dict, List, Optional, Tuple
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

ASSETS_PATH = pathlib.Path("./board_games_data")
CONFIG_PATH = pathlib.Path("config_chatbot.json")


class Config:
    """
    Class for working with configuration.
    """
    
    def __init__(self, path_to_config: pathlib.Path) -> None:
        with open(path_to_config, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        self.seed_urls = config.get('seed_urls', [])
        self.total_articles = config.get('total_articles_to_find_and_parse', 50)
        self.headers = config.get('headers', {})
        self.timeout = config.get('timeout', 30)
        self.request_delay = config.get('request_delay', {'min': 1.0, 'max': 2.5})
        self.max_retries = config.get('max_retries', 3)
    
    def get_seed_urls(self) -> list:
        return self.seed_urls
    
    def get_num_articles(self) -> int:
        return self.total_articles
    
    def get_headers(self) -> dict:
        return self.headers
    
    def get_timeout(self) -> int:
        return self.timeout
    
    def get_delay(self) -> Tuple[float, float]:
        return (self.request_delay.get('min', 1.0), self.request_delay.get('max', 2.5))
    
    def get_max_retries(self) -> int:
        return self.max_retries


def make_request(url: str, config: Config) -> Optional[requests.Response]:
    """
    Performs an HTTP request with delay and retries.
    """
    delay_min, delay_max = config.get_delay()
    time.sleep(random.uniform(delay_min, delay_max))
    
    headers = config.get_headers().copy()
    user_agents = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/119.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36'
    ]
    headers['User-Agent'] = random.choice(user_agents)
    
    for attempt in range(config.get_max_retries()):
        try:
            response = requests.get(url, headers=headers, timeout=config.get_timeout(), verify=False)
            if response.status_code == 200:
                return response
            elif response.status_code == 404:
                return None
            else:
                if attempt < config.get_max_retries() - 1:
                    time.sleep(2)
        except Exception as e:
            if attempt == config.get_max_retries() - 1:
                print(f"Error after {config.get_max_retries()} tries: {e}")
            else:
                time.sleep(2)
    return None


def is_game_url(url: str) -> bool:
    """
    Checks if the URL is a link to a game page.
    """
    parsed = urlparse(url)
    path = parsed.path.strip('/')
    
    skip_words = [
        'nastolnie', 'catalog', 'category', 'cart', 'login',
        'register', 'personal', 'search', 'about', 'delivery',
        'contacts', 'news', 'blog', 'page', 'ajax', 'api',
        'skidki', 'podarochnie', 'nabori', 'akcii', 'sale',
        'brand', 'manufacturer', 'review', 'otzivi'
    ]
    
    path_lower = path.lower()
    for word in skip_words:
        if word in path_lower:
            return False
    
    if '/' in path or len(path) < 3 or len(path) > 60:
        return False
    
    return True


def extract_game_links_from_page(page_url: str, config: Config) -> List[str]:
    """
    Extracts game links from a catalog page.
    """
    print(f"Processing: {page_url}")
    response = make_request(page_url, config)
    
    if not response:
        return []
    
    soup = BeautifulSoup(response.text, 'lxml')
    found_links = set()
    
    link_selectors = [
        'a.title',
        'a.product__title',
        'a.card__title',
        'a[itemprop="url"]',
        '.product-card a',
        '.catalog-card a',
        'a.product-link',
        'a[href*="/product/"]',
        'a[href*="/igra/"]'
    ]
    
    for selector in link_selectors:
        elements = soup.select(selector)
        for el in elements:
            href = el.get('href', '')
            if href:
                if href.startswith('/'):
                    full_url = urljoin('https://hobbygames.ru', href)
                elif href.startswith('http'):
                    full_url = href
                else:
                    continue
                
                full_url = full_url.split('?')[0].split('#')[0]
                
                if is_game_url(full_url):
                    found_links.add(full_url)
    
    result = list(found_links)
    print(f"Found games: {len(result)}")
    return result


def extract_next_page_url(current_url: str, config: Config) -> Optional[str]:
    """
    Finds the URL of the next page in the catalog.
    """
    response = make_request(current_url, config)
    if not response:
        return None
    
    soup = BeautifulSoup(response.text, 'lxml')
    
    next_selectors = [
        'a.next',
        'a.pagination__next',
        'a[rel="next"]',
        'a.pagination-link--next',
        'li.next a'
    ]
    
    for selector in next_selectors:
        next_link = soup.select_one(selector)
        if next_link and next_link.get('href'):
            href = next_link.get('href')
            if href.startswith('/'):
                return urljoin('https://hobbygames.ru', href)
            elif href.startswith('http'):
                return href
    
    return None


def extract_price(soup: BeautifulSoup, title: str) -> str:
    """
    Price parsing.
    """

    meta_price = soup.find('meta', {'itemprop': 'price'})
    if meta_price:
        price = meta_price.get('content', '')
        if price:
            price = re.sub(r'[^\d]', '', price)
            if price:
                return price

    data_price = soup.find(attrs={'data-price': True})
    if data_price:
        price = data_price.get('data-price', '')
        price = re.sub(r'[^\d]', '', price)
        if price:
            return price

    price_blocks = soup.find_all(['span', 'div'], class_=re.compile(r'price', re.I))
    
    for block in price_blocks:
        check_elem = block
        is_breadcrumb = False
        for _ in range(5):
            if check_elem.get('class'):
                classes = ' '.join(check_elem.get('class', [])).lower()
                if 'breadcrumb' in classes or 'breadcrumbs' in classes:
                    is_breadcrumb = True
                    break
            check_elem = check_elem.parent
            if not check_elem:
                break
        
        if is_breadcrumb:
            continue
        
        text = block.get_text(strip=True)
        match = re.search(r'(\d{1,3}(?:[\s\xa0]?\d{3})*)\s*[₽руб]', text)
        if match:
            price = match.group(1).replace(' ', '').replace('\xa0', '')
            if 'товар' not in text.lower():
                return price

    json_ld = soup.find('script', type='application/ld+json')
    if json_ld and json_ld.string:
        try:
            data = json.loads(json_ld.string)
            
            def find_price(obj):
                if isinstance(obj, dict):
                    if 'offers' in obj:
                        offers = obj['offers']
                        if isinstance(offers, dict):
                            return offers.get('price')
                        elif isinstance(offers, list) and offers:
                            return offers[0].get('price')
                    if 'price' in obj:
                        return obj['price']
                    for v in obj.values():
                        result = find_price(v)
                        if result:
                            return result
                return None
            
            price = find_price(data)
            if price:
                price = re.sub(r'[^\d]', '', str(price))
                if price:
                    return price
        except:
            pass
    
    return ""


def extract_description(soup: BeautifulSoup) -> str:
    """
    Takes the text from the 'Description' block and trims it to 'Packaging'.
    """

    for header in soup.find_all(['h2', 'h3', 'div', 'p']):
        header_text = header.get_text(strip=True)
        
        if header_text == "Описание" or header_text == "Описание игры":
            content_div = header.find_next_sibling()
            if content_div:
                description_text = content_div.get_text(strip=True)
                
                if 'Комплектация' in description_text:
                    description_text = description_text.split('Комплектация')[0]
                
                description_text = re.sub(r'\s+', ' ', description_text).strip()
                
                if len(description_text) > 50:
                    return description_text

    desc_block = soup.find('div', class_=re.compile(r'description', re.I))
    if desc_block:
        text = desc_block.get_text(strip=True)
        if 'Комплектация' in text:
            text = text.split('Комплектация')[0]
        text = re.sub(r'\s+', ' ', text).strip()
        if len(text) > 50:
            return text
    
    return ""


def extract_game_tags(soup: BeautifulSoup) -> Tuple[str, str, str]:
    """
    Extracts the number of players, duration, and age from product-tag blocks.
    """
    
    players = ""
    duration = ""
    age = ""

    tags = soup.find_all('div', class_='product-tag')
    
    for tag in tags:
        label = tag.find('div', class_='product-tag__label')
        if not label:
            continue
        
        label_text = label.get_text(strip=True)

        icon = tag.find('div', class_=re.compile(r'icon-mask', re.I))
        
        if icon:
            icon_class = ' '.join(icon.get('class', []))
            
            if 'member' in icon_class or 'player' in icon_class:
                players = label_text
            elif 'time' in icon_class or 'clock' in icon_class:
                duration = label_text
            elif 'age' in icon_class or '+' in label_text:
                age = label_text
        else:
            if '-' in label_text and re.match(r'\d+\s*-\s*\d+', label_text):
                players = label_text
            elif '+' in label_text:
                age = label_text
            elif label_text.isdigit() and not players and not duration:
                duration = label_text
    
    return players, duration, age


def extract_characteristics(soup: BeautifulSoup) -> Dict[str, str]:
    """
    Retrieves game characteristics from a table (fallback).
    """
    chars = {
        'players': '',
        'age': '',
        'duration': '',
        'type': ''
    }
    
    char_table = soup.find('table', class_=re.compile(r'characteristics|specs|params', re.I))
    if not char_table:
        char_table = soup.find('div', class_=re.compile(r'characteristics|specifications', re.I))
        if char_table:
            char_table = char_table.find('table')
    
    if char_table:
        rows = char_table.find_all('tr')
        for row in rows:
            cells = row.find_all('td')
            if len(cells) >= 2:
                param = cells[0].get_text(strip=True).lower()
                value = cells[1].get_text(strip=True)
                
                if 'игрок' in param:
                    chars['players'] = value
                elif 'возраст' in param:
                    chars['age'] = value
                elif 'время' in param or 'партия' in param:
                    chars['duration'] = value
                elif 'тип' in param or 'жанр' in param:
                    chars['type'] = value
    
    return chars


def get_genre_by_description(description: str, title: str) -> str:
    """
    Determines the game genre based on the description and title.
    """
    text = (description + ' ' + title).lower()
    
    genres = {
        'Стратегия': ['стратег', 'тактик', 'экономик', 'ресурс', 'развити', 'войн', 'битв', 'план'],
        'Логическая': ['логик', 'головоломк', 'пазл', 'ребус', 'мышлени'],
        'Карточная': ['карточн', 'карты', 'колод', 'покер', 'дурак'],
        'Приключение': ['приключен', 'квест', 'сюжет', 'путешеств', 'поход'],
        'Детектив': ['детектив', 'расследован', 'преступлен', 'улик', 'сыщик'],
        'Фэнтези': ['фэнтези', 'маги', 'волшеб', 'дракон', 'эльф', 'орк', 'маг', 'чародей'],
        'Хоррор': ['хоррор', 'ужас', 'мистик', 'зомби', 'страшн', 'тьм'],
        'Вечеринка': ['вечеринк', 'party', 'компани', 'весел', 'игр для компании'],
        'Экономическая': ['экономик', 'бизнес', 'денег', 'финанс', 'рынок', 'торговл'],
        'Научная': ['науч', 'образов', 'познават', 'энциклопед']
    }
    
    genre_scores = {}
    for genre, keywords in genres.items():
        score = sum(1 for keyword in keywords if keyword in text)
        if score > 0:
            genre_scores[genre] = score
    
    if genre_scores:
        return max(genre_scores, key=genre_scores.get)
    
    return 'Семейная'


class HobbyGamesCrawler:
    """
    The main crawler class for collecting games.
    """
    
    def __init__(self, config: Config):
        self.config = config
        self.games = []
        self.processed_urls = set()
    
    def parse_game(self, game_url: str) -> Optional[Dict]:
        """
        Parses the page of one game.
        """
        print(f"Parsing: {game_url}")
        response = make_request(game_url, self.config)
        
        if not response:
            return None
        
        soup = BeautifulSoup(response.text, 'lxml')

        title_tag = soup.find('h1')
        title = title_tag.get_text(strip=True) if title_tag else "Unknown"
        
        players_from_tags, duration_from_tags, age_from_tags = extract_game_tags(soup)

        description = extract_description(soup)

        if not description or len(description) < 100:
            print(f"No description: {title}")
            return None

        chars = extract_characteristics(soup)

        players = players_from_tags if players_from_tags else chars.get('players', '')
        age = age_from_tags if age_from_tags else chars.get('age', '')
        duration = duration_from_tags if duration_from_tags else chars.get('duration', '')

        price = extract_price(soup, title)

        genre = get_genre_by_description(description, title)

        game = {
            'url': game_url,
            'title': title,
            'players': players,
            'age': age,
            'duration': duration,
            'type': chars.get('type', ''),
            'price': price,
            'description': description,
            'genre': genre,
            'parsed_at': time.strftime('%Y-%m-%d %H:%M:%S')
        }
        
        print(f"{title}")
        print(f"Price: {price if price else '-'} rub")
        print(f"Genre: {genre}")
        print(f"Players: {players if players else '-'}")
        print(f"Age: {age if age else '-'}")
        print(f"Duration: {duration if duration else '-'}")
        print(f"Description: {description[:80]}...")
        
        return game
    
    def crawl(self) -> List[Dict]:
        """
        Basic method of collecting games.
        """
        print()
        print("Collecting from hobbygames.ru")
        print()

        if ASSETS_PATH.exists():
            shutil.rmtree(ASSETS_PATH)
        ASSETS_PATH.mkdir(parents=True)
        
        all_game_links = []
        pages_to_visit = list(self.config.get_seed_urls())
        
        print("\nCollecting")
        print("-" * 50)
        
        while pages_to_visit and len(all_game_links) < self.config.get_num_articles() * 2:
            current_page = pages_to_visit.pop(0)
            
            if current_page in self.processed_urls:
                continue
            
            self.processed_urls.add(current_page)
            game_links = extract_game_links_from_page(current_page, self.config)
            
            for link in game_links:
                if link not in all_game_links:
                    all_game_links.append(link)
                    print(f"Added link: {link}")
            
            next_page = extract_next_page_url(current_page, self.config)
            if next_page and next_page not in self.processed_urls:
                pages_to_visit.append(next_page)
            
            print(f"Found {len(all_game_links)} links")
        
        all_game_links = all_game_links[:self.config.get_num_articles() * 2]
        print(f"\nTotally found links: {len(all_game_links)}")
        
        print("\nParsing")
        print("-" * 50)
        
        for idx, game_url in enumerate(all_game_links, 1):
            if len(self.games) >= self.config.get_num_articles():
                break
            
            print(f"\n[{idx}/{len(all_game_links)}] Games collected: {len(self.games)}/{self.config.get_num_articles()}")
            game = self.parse_game(game_url)
            
            if game:
                self.games.append(game)
                
                json_path = ASSETS_PATH / f"game_{len(self.games)}.json"
                with open(json_path, 'w', encoding='utf-8') as f:
                    json.dump(game, f, ensure_ascii=False, indent=2)
                
                txt_path = ASSETS_PATH / f"game_{len(self.games)}_description.txt"
                with open(txt_path, 'w', encoding='utf-8') as f:
                    f.write(f"Title: {game['title']}\n")
                    f.write(f"URL: {game['url']}\n")
                    f.write(f"Genre: {game['genre']}\n")
                    f.write(f"Players: {game['players']}\n")
                    f.write(f"Age: {game['age']}\n")
                    f.write(f"Duration: {game['duration']}\n")
                    f.write(f"Type: {game['type']}\n")
                    f.write(f"Price: {game['price']} rub\n")
                    f.write(f"\n{'='*60}\n")
                    f.write(f"Game description:\n")
                    f.write(game['description'])
        
        print("\nSaving")
        print("-" * 50)
        
        all_games_path = ASSETS_PATH / "all_games.json"
        with open(all_games_path, 'w', encoding='utf-8') as f:
            json.dump(self.games, f, ensure_ascii=False, indent=2)
        print(f"Saved: {all_games_path}")

        simple_games = []
        for g in self.games:
            simple_games.append({
                'title': g['title'],
                'players': g['players'],
                'age': g['age'],
                'price': g['price'],
                'type': g['type'],
                'genre': g['genre'],
                'duration': g['duration'],
                'url': g['url'],
                'description': g.get('description', '')
            })
        
        bot_games_path = ASSETS_PATH / "games_for_bot.json"
        with open(bot_games_path, 'w', encoding='utf-8') as f:
            json.dump(simple_games, f, ensure_ascii=False, indent=2)
        print(f"Saved file: {bot_games_path}")
        
        return self.games


def main():
    """
    Main function.
    """
    import urllib3
    urllib3.disable_warnings()
    
    print()
    print("Launching games collection crawler")
    print()
    
    try:
        config = Config(CONFIG_PATH)
        print(f"- Target number of games: {config.get_num_articles()}")
        print(f"- Start URL: {len(config.get_seed_urls())} p")
        print(f"- Timeout: {config.get_timeout()} s")
        
        crawler = HobbyGamesCrawler(config)
        games = crawler.crawl()
        
        print()
        print("Overall stats")
        print()
        print(f"Collected games: {len(games)}")
        
        if games:
            genres = {}
            prices = []
            for game in games:
                genre = game.get('genre', 'Unknown')
                genres[genre] = genres.get(genre, 0) + 1
                
                price = game.get('price', '')
                if price and price.isdigit():
                    prices.append(int(price))
            
            print(f"\nGenres:")
            for genre, count in sorted(genres.items(), key=lambda x: x[1], reverse=True):
                print(f"   - {genre}: {count} games")
            
            if prices:
                print(f"\nPrices info:")
                print(f"- Average price: {sum(prices)//len(prices)} rub")
                print(f"- Min: {min(prices)} rub")
                print(f"- Max: {max(prices)} rub")
        
        print(f"\nSaved in: {ASSETS_PATH}")
        print()
        print("Completed")
        print()
        
    except FileNotFoundError:
        print(f"Config file not found - {CONFIG_PATH}")
    except Exception as e:
        print(f"Unexpected error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
