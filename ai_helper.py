from urllib.parse import quote_plus
from dotenv import load_dotenv
from google import genai
from concurrent.futures import ThreadPoolExecutor
import json
import requests
from bs4 import BeautifulSoup

load_dotenv()
client = genai.Client()

TRUSTED_SITES = {
    "Sally's Baking Addiction": "https://sallysbakingaddiction.com/",
    "The Cafe Suisse Farine": "https://thecafesucrefarine.com",
    "Bigger Bolder Baking": "https://www.biggerbolderbaking.com",
    "My Cake School": "https://www.mycakeschool.com",
    "Handle The Heat": "https://handletheheat.com",
    "Broma Bakery": "https://bromabakery.com",
    "Recipe Tin Eats": "https://www.recipetineats.com",
    "Sugar and Sparrow": "https://sugarandsparrow.com",
    "Life, Love, and Sugar": "https://www.lifeloveandsugar.com",
    "Once Upon a Chef": "https://www.onceuponachef.com",
    "Preppy Kitchen": "https://preppykitchen.com",
    "Cloudy Kitchen": "https://cloudykitchen.com",
    "Two Peas and Their Pod": "https://www.twopeasandtheirpod.com",
    "Pastries Like a Pro": "https://pastrieslikeapro.com",
    "Mel's Kitchen Cafe": "https://www.melskitchencafe.com",
    "Sugarspun Run": "https://sugarspunrun.com",
    "Diva Can Cook": "https://divascancook.com",
    "Rasa Malaysia": "https://rasamalaysia.com",
    "Kathleen Ashmore": "https://kathleenashmore.com",
    "Jane's Patisserie": "https://www.janespatisserie.com",
}

def clean_domain(address):
    domain = address.replace("https://", "").replace("http://", "")
    return domain.replace("www.", "").rstrip("/")

def get_site_posts(domain, query, how_many=3):
    url = "https://" + domain + "/wp-json/wp/v2/posts"
    try:
        response = requests.get(
            url,
            params={"search": query, "per_page": how_many, "_fields": "link"},
            headers={"User-Agent": "Mozilla/5.0"},
            timeout=8,
        )
        if response.status_code != 200:
            return []
        return [post["link"] for post in response.json()]
    except (requests.RequestException, ValueError, KeyError, TypeError):
        return []

def get_candidate_urls(ingredients, per_site=8):
    items = [i.strip() for i in ingredients.split(",") if i.strip()]
    domains = [clean_domain(a) for a in TRUSTED_SITES.values()]

    urls = []
    while items:
        query = " ".join(items)
        with ThreadPoolExecutor(max_workers=8) as pool:
            results = pool.map(lambda d: get_site_posts(d, query, per_site), domains)
        urls = []
        for site_urls in results:
            for u in site_urls:
                if u not in urls:
                    urls.append(u)
        if len(urls) >= 10 or len(items) == 1:
            break
        items = items[:-1]   # too few results, so retry without the last ingredient
    return urls

def find_key(data, key):
    # Look through the structured data for the first value stored under this key
    if isinstance(data, dict):
        if key in data:
            return data[key]
        for value in data.values():
            found = find_key(value, key)
            if found:
                return found
    elif isinstance(data, list):
        for item in data:
            found = find_key(item, key)
            if found:
                return found
    return None


def get_recipe_info(url):
    try:
        page = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=8)
        if page.status_code != 200:
            return None
        soup = BeautifulSoup(page.text, "html.parser")
        raw_title = soup.title.get_text().strip() if soup.title else url
        title = raw_title.lower()

        stars, count, ingredients = None, 0, []
        for script in soup.find_all("script", type="application/ld+json"):
            try:
                data = json.loads(script.get_text())
            except json.JSONDecodeError:
                continue
            rating = find_key(data, "aggregateRating")
            if isinstance(rating, dict) and stars is None:
                stars = float(rating.get("ratingValue", 0))
                count = int(float(rating.get("ratingCount") or rating.get("reviewCount") or 0))
            found = find_key(data, "recipeIngredient")
            if isinstance(found, list):
                ingredients = found

        if stars is None:
            return None
        text = title + " " + " ".join(str(i) for i in ingredients).lower()
        return {"stars": stars, "count": count, "text": text, "title": raw_title}
    except (requests.RequestException, ValueError):
        return None

def has_all_ingredients(text, items):
    # True only if every word the user typed appears in the recipe's text
    for item in items:
        for word in item.lower().split():
            if word.rstrip("s") not in text:   # rstrip("s") lets "thighs" match "thigh"
                return False
    return True


def score(stars, count):
    average = 4.2   # typical rating, adjust later
    weight = 50     # how many reviews it takes to trust a rating
    return (count / (count + weight)) * stars + (weight / (count + weight)) * average

def get_top_recipes(ingredients, how_many=5):
    items = [i.strip() for i in ingredients.split(",") if i.strip()]
    urls = get_candidate_urls(ingredients)
    with ThreadPoolExecutor(max_workers=8) as pool:
        infos = list(pool.map(get_recipe_info, urls))

    recipes = []
    for url, info in zip(urls, infos):
        if info and has_all_ingredients(info["text"], items):
            recipes.append({
                "url": url,
                "title": info["title"],
                "stars": info["stars"],
                "reviews": info["count"],
                "score": score(info["stars"], info["count"]),
            })
    recipes.sort(key=lambda r: r["score"], reverse=True)
    return recipes[:how_many]

if __name__ == "__main__":
    for r in get_top_recipes("chocolate, peanut butter"):
        print(r["stars"], r["reviews"], r["url"])