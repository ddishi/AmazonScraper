import urllib
from threading import Thread

from fuzzywuzzy import fuzz
import aiohttp
import asyncio
import requests
from aiohttp import ClientSession
from bs4 import BeautifulSoup
from requests import Response
from currency_converter import CurrencyConverter
from my_db import create_connection, save_search_history

conn = create_connection()

# Add headers to mimic a browser
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0",
    "Accept-Language": "en-US,en;q=0.5",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
    "TE": "Trailers",
}


async def fetch_html(url: str) -> Response:
    """
    Fetches the HTML content of the given URL.

    :param url: The URL to fetch the HTML content from.
    :return: The Response object containing the HTML content.
    """
    response = requests.get(url, headers=headers)
    return response


async def get_top_10_results(query, user_id=None):
    """
    Retrieves the top 10 search results for a given query on Amazon.com.

    :param query: The search query.
    :param user_id: The user ID (optional).
    :return: A list of dictionaries containing information about the top 10 search results.
    """

    # Encode the query for use in a URL
    encoded_query = urllib.parse.quote(query)

    url = f"https://www.amazon.com/s?field-keywords={encoded_query}"

    # Fetch the HTML content for the search query
    response = await fetch_html(url)

    if response.status_code != 200:
        return []

    # Parse the HTML content with BeautifulSoup
    soup = BeautifulSoup(response.content, "html.parser")
    results = []
    max_search = 100

    # Iterate through the search results, extracting relevant information
    for idx, result in enumerate(soup.select(".s-result-item")[1:max_search]):
        try:
            title = result.select_one(".a-text-normal").text

            image_url = result.select_one(".s-image")["src"]
            asin = result["data-asin"]
            product_url = f"https://www.amazon.com/dp/{asin}"

            # If all the information is available, add it to the results list
            if title and image_url and asin and product_url:
                results.append({
                    "title": title,
                    "image_url": image_url,
                    "asin": asin,
                    "product_url": product_url,
                })

            if len(results) == 10:
                break
        except Exception as e:
            print(e)

    # Save the search history to the database
    save_search_history(conn, user_id, query)

    # print_results(results)
    return results


def print_results(results):
    """
    Prints the search results in a readable format.

    :param results: A list of dictionaries containing information about the search results.
    """
    print(f"Extracted results:")
    for index, result in enumerate(results, start=1):
        print(f"Result {index}:")
        print(f"  Title: {result['title']}")
        print(f"  Image URL: {result['image_url']}")
        print(f"  ASIN: {result['asin']}")
        print(f"  Product URL: {result['product_url']}")
        print()


async def get_product_details(asin):
    """
    Retrieves the details of a product with the given ASIN from Amazon.com.

    :param asin: The ASIN of the product.
    :return: A dictionary containing the product details.
    """
    url = f"https://www.amazon.com/dp/{asin}"
    response = await fetch_html(url)

    if response.status_code != 200:
        return []

    soup = BeautifulSoup(response.content, "html.parser")
    title = soup.select_one("#productTitle").text.strip()
    price = await get_price(soup)
    rating = float(soup.select_one(".a-icon-star .a-icon-alt").text.strip().split(" ")[0])
    return {"title": title, "price": price, "rating": rating, "product_url": url}


async def get_price(soup):
    """
    Extracts the price of a product from the BeautifulSoup object.

    :param soup: The BeautifulSoup object containing the product's HTML.
    :return: The price of the product as a string, or None if not found.
    """
    price_element = soup.select_one(".a-price .a-offscreen")
    price = None
    if price_element:
        price = price_element.text.replace(",", "").strip()[1:]
    return price


async def get_product_price_from_other_amazon(asin, domain):
    """
    Retrieves the price of a product with the given ASIN from another Amazon domain.

    :param asin: The ASIN of the product.
    :param domain: The domain of the Amazon website to search for the product price.
    :return: The price and the product URL as a tuple, or None if not found.
    """

    url = f"https://{domain}/dp/{asin}"

    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as response:

            content = await response.text()
            soup = BeautifulSoup(content, "html.parser")
            price = await get_price(soup)

            if not price:
                title_dict = await get_product_details(asin)
                title = urllib.parse.quote(title_dict["title"])
                url = f"https://{domain}/s?field-keywords={title}"

                # search similar item
                similar_item = await search_similar(domain, title, url)

                if similar_item:
                    price = similar_item["price"]
                    url = similar_item["product_url"]

            return price, url


async def search_similar(domain, title, url, similarity_threshold=60, max_results=20):
    """
    Searches for a similar product with the given title on an Amazon domain.

    :param domain: The domain of the Amazon website to search for a similar product.
    :param title: The title of the product to search for.
    :param url: The URL of the search results page.
    :param similarity_threshold: The minimum similarity score to consider a product similar.
    :param max_results: The maximum number of search results to process.
    :return: A dictionary containing the similar product's details, or None if not found.
    """

    response = await fetch_html(url)
    soup = BeautifulSoup(response.content, "html.parser")

    # Extract the product elements from the search result page
    products = soup.select(".s-result-item")[:max_results]

    # Iterate through the products and find the ones with a similar title
    for product in products:
        try:
            asin = product.get("data-asin")
            if not asin:
                continue
            product_title_element = product.select_one(".a-text-normal")

            # Compare the similarity between titles using the fuzz.token_set_ratio method
            if product_title_element:
                product_title = product_title_element.text.strip()
                similarity = fuzz.token_set_ratio(title, product_title)

                # If the similarity is greater than or equal to the threshold, get the price
                if similarity >= similarity_threshold:
                    price = await get_price(product)
                    if price:
                        product_url = f"https://{domain}/dp/{asin}"
                        return {"title": product_title, "price": float(price), "product_url": product_url}
        except Exception as e:
            print(e)

    return None


c = CurrencyConverter()


def convert_to_usd(amount, currency_code):
    """
    Converts the given amount in a foreign currency to USD.

    :param amount: The amount to convert.
    :param currency_code: The 3-letter currency code of the foreign currency.
    :return: The converted amount in USD.
    """
    if currency_code == "USD":
        return amount
    try:
        converted_amount = c.convert(amount, currency_code, 'USD')
        return round(converted_amount, 2)
    except ValueError:
        raise Exception("Failed to fetch exchange rates")


async def fetch_product_price(asin, domain, session):
    """
    Fetches the product price and URL for a given ASIN and domain.

    :param asin: The ASIN of the product.
    :param domain: The domain of the Amazon website to search for the product price.
    :param session: The aiohttp ClientSession object.
    :return: A tuple containing the domain, price, and product URL.
    """
    price, url = await get_product_price_from_other_amazon(asin, domain)
    return domain, price, url


async def get_prices_concurrently(asin, domains):
    """
    Retrieves the prices of a product with the given ASIN from multiple Amazon domains concurrently.

    :param asin: The ASIN of the product.
    :param domains: A list of Amazon domains to search for the product price.
    :return: A dictionary with domain keys and (price, URL) tuple values.
    """
    async with ClientSession() as session:
        tasks = [fetch_product_price(asin, domain, session) for domain in domains]
        results = await asyncio.gather(*tasks)
        dict_results = {t[0]: (t[1], t[2]) for t in results}

        return dict_results

