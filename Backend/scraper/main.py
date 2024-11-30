import asyncio
from playwright.async_api import async_playwright
import json
import os
from amazon import get_product as get_amazon_product
from requests import post
import random

AMAZON = "https://www.amazon.com"

URLS = {
    "https://www.amazon.com": {
        "search_field_query": 'input[name="field-keywords"]',
        "search_button_query": 'input[value="Go"]',
        "product_selector": "div.s-card-container"
    },
    "https://www.amazon.ca": {
        "search_field_query": 'input[name="field-keywords"]',
        "search_button_query": 'input[value="Go"]',
        "product_selector": "div.s-card-container"
    }
}

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0"
]

def load_auth():
    FILE = os.path.join("scraper", "auth.json")
    with open(FILE, "r") as f:
        return json.load(f)

def save_results(results):
    """Save results to a JSON file"""
    data = {"results": results}
    FILE = os.path.join("scraper", "results.json")
    with open(FILE, "w") as f:
        json.dump(data, f)

def post_results(results, endpoint, search_text, source):
    """Post results to the specified endpoint"""
    try:
        headers = {
            "Content-Type": "application/json"
        }
        data = {
            "data": results,
            "search_text": search_text,
            "source": source
        }

        print(f"Sending {len(results)} results to {endpoint}")
        response = post(
            f"http://localhost:5000{endpoint}",
            headers=headers,
            json=data,
            timeout=30  # Added timeout
        )
        print(f"Status code: {response.status_code}")
        
        if response.status_code != 200:
            print(f"Error response: {response.text}")
            # Backup save results if API call fails
            save_results(results)
            
    except Exception as e:
        print(f"Error posting results: {str(e)}")
        # Backup save results if API call fails
        save_results(results)
        raise

cred = load_auth()
auth = f'{cred["username"]}:{cred["password"]}'
browser_url = f'wss://{auth}@{cred["host"]}'

async def handle_dialog(dialog):
    print(f"Dialog appeared: {dialog.message}")
    await dialog.accept()

async def wait_for_navigation(page):
    try:
        await page.wait_for_load_state("networkidle", timeout=30000)
    except Exception as e:
        print(f"Navigation timeout: {str(e)}")

async def setup_page(browser):
    context = await browser.new_context(
        bypass_csp=True,
        ignore_https_errors=True,
        user_agent=random.choice(USER_AGENTS),
        viewport={'width': 1920, 'height': 1080},
        device_scale_factor=1,
    )
    
    page = await context.new_page()
    page.on("dialog", handle_dialog)
    
    await page.set_extra_http_headers({
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "gzip, deflate, br",
        "DNT": "1",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1"
    })
    
    return context, page

async def navigate_to_page(page, url, max_retries=3):
    for attempt in range(max_retries):
        try:
            if attempt > 0:
                await asyncio.sleep(random.uniform(2, 5))
            
            response = await page.goto(
                url,
                timeout=60000,
                wait_until="domcontentloaded"
            )
            
            if response and response.ok:
                await wait_for_navigation(page)
                return True
                
        except Exception as e:
            print(f"Navigation attempt {attempt + 1} failed: {str(e)}")
            if attempt == max_retries - 1:
                raise Exception(f"Failed to navigate to {url} after {max_retries} attempts")
            
    return False

async def search(metadata, page, search_text):
    print(f"Searching for {search_text} on {page.url}")
    await asyncio.sleep(random.uniform(1, 3))
    
    search_field_query = metadata.get("search_field_query")
    search_button_query = metadata.get("search_button_query")

    if search_field_query and search_button_query:
        print("Waiting for search field...")
        search_box = await page.wait_for_selector(search_field_query, timeout=30000)
        
        await search_box.click()
        for char in search_text:
            await page.keyboard.type(char)
            await asyncio.sleep(random.uniform(0.1, 0.3))
        
        print("Pressing search button")
        button = await page.wait_for_selector(search_button_query, timeout=30000)
        await button.click()
        
        await wait_for_navigation(page)
    else:
        raise Exception("Could not search.")

    return page

async def get_products(page, search_text, selector, get_product):
    print("Retrieving products.")
    
    await page.wait_for_selector(selector, timeout=30000)
    product_divs = await page.query_selector_all(selector)
    
    valid_products = []
    words = search_text.split(" ")

    async with asyncio.TaskGroup() as tg:
        for div in product_divs:
            async def task(p_div):
                try:
                    product = await get_product(p_div)
                    if not product["price"] or not product["url"]:
                        return

                    for word in words:
                        if not product["name"] or word.lower() not in product["name"].lower():
                            break
                    else:
                        valid_products.append(product)
                except Exception as e:
                    print(f"Error processing product: {str(e)}")
                    
            tg.create_task(task(div))

    return valid_products

def normalize_url(url):
    url = url.lower().strip()
    if "amazon.ca" in url:
        return "https://www.amazon.ca"
    if "amazon.com" in url:
        return "https://www.amazon.com"
    raise ValueError(f"Unsupported URL: {url}")


async def main(url, search_text, response_route):
    url = normalize_url(url)
    print(f"Provided URL: {url}")
    metadata = URLS.get(url)
    if not metadata:
        print("Invalid URL.")
        return

    async with async_playwright() as pw:
        try:
            browser = await pw.chromium.connect_over_cdp(
                browser_url,
                timeout=60000
            )
            
            context, page = await setup_page(browser)
            print("Browser and page set up completed.")
            
            try:
                success = await navigate_to_page(page, url)
                if not success:
                    raise Exception("Failed to navigate to the page")
                
                print("Initial page loaded successfully.")
                
                search_page = await search(metadata, page, search_text)
                
                if "amazon.com" in url.lower() or "amazon.ca" in url.lower():
                    func = get_amazon_product
                else:
                    raise Exception('Unsupported URL')

                results = await get_products(search_page, search_text, metadata["product_selector"], func)
                print(f"Found {len(results)} valid products.")
                
                # If no results found, save empty results
                if not results:
                    print("No products found matching the search criteria.")
                    post_results([], response_route, search_text, url)
                else:
                    post_results(results, response_route, search_text, url)
                
            except Exception as e:
                print(f"Error during scraping: {str(e)}")
                raise e
            finally:
                print("Cleaning up...")
                await context.close()
                await browser.close()
                
        except Exception as e:
            print(f"Critical error: {str(e)}")
            raise e

if __name__ == "__main__":
    # Test script
    asyncio.run(main(AMAZON, "ryzen 9 3950x", "/api/products"))
