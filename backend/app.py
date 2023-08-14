from typing import Optional, Tuple
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from scraper import *
from fastapi.middleware.cors import CORSMiddleware
import logging
from my_db import save_price_comparison, get_searches_count_last_24_hours, get_user_search_history

# Set constants
DAILY_SEARCH_LIMIT = 10
USER_ID = 0  # default user_id is set to 0 before implementing users management.

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
app = FastAPI()

# CORS configuration for allowing specific origins
origins = [
    "http://localhost:8000",
    "http://127.0.0.1:8000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files and templates
app.mount("/static", StaticFiles(directory="../frontend/static"), name="static")
templates = Jinja2Templates(directory="../frontend/templates")


@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


class SearchResult(BaseModel):
    title: str
    image_url: str
    asin: str
    product_url: str


class ProductDetails(BaseModel):
    title: str
    price: float
    rating: float
    product_url: str


class PriceComparison(BaseModel):
    item: str
    rating: float
    amazon_com: Tuple[Optional[float], str]
    amazon_co_uk: Tuple[Optional[float], str]
    amazon_de: Tuple[Optional[float], str]
    amazon_ca: Tuple[Optional[float], str]


@app.post("/search", response_class=JSONResponse)
async def search_item(search_query: dict, user_id=USER_ID):
    query = search_query['query']

    # Check the daily search count
    search_count = 0
    search_count = get_searches_count_last_24_hours(conn, user_id)
    if search_count >= DAILY_SEARCH_LIMIT:
        raise HTTPException(status_code=429,
                            detail="You have reached the daily search limit of 10. To make more searches today, "
                                   "please subscribe.")

    if not query:
        raise HTTPException(status_code=400, detail="Search query must not be empty.")
    try:
        results = await get_top_10_results(query, user_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to fetch search results")

    if not results:
        raise HTTPException(status_code=404, detail="No results found")

    return results


@app.get("/product/{asin}", response_model=ProductDetails)
async def get_details(asin: str):
    try:
        details = get_product_details(asin)
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to fetch product details")

    if not details:
        raise HTTPException(status_code=404, detail="Product not found")
    return details


@app.get("/search_history", response_class=JSONResponse)
async def get_search_history(user_id: int):
    try:
        search_history = get_user_search_history(conn, user_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to fetch search history")

    if not search_history:
        raise HTTPException(status_code=404, detail="No search history found")

    return search_history


@app.get("/price-comparison/{asin}", response_model=PriceComparison)
async def get_price_comparison(asin: str):
    print("Comparing Prices...")
    try:
        product_details = await get_product_details(asin)
        if not product_details:
            raise HTTPException(status_code=404, detail="Product not found")

        domain_to_currency = {
            "amazon.co.uk": "GBP",
            "amazon.de": "EUR",
            "amazon.ca": "CAD",
        }

        domains = ["amazon.co.uk", "amazon.de", "amazon.ca"]
        prices = {"USD": product_details["price"]}
        fetched_prices = await get_prices_concurrently(asin, domains)
        for domain, data in fetched_prices.items():
            price = data[0]
            currency = domain_to_currency[domain]
            if price is not None:
                prices[currency] = price
            else:
                prices[currency] = None

        converted_prices = {}
        for key, value in prices.items():
            if value is not None:
                converted_prices[key] = convert_to_usd(value, key)
            else:
                converted_prices[key] = None

    except Exception as e:
        logger.exception("Error in get_price_comparison")
        raise HTTPException(status_code=500, detail="Failed to fetch price comparison")

    price_comparison = PriceComparison(
        item=product_details["title"],
        rating=product_details["rating"],
        amazon_com=(converted_prices["USD"], product_details["product_url"]),
        amazon_co_uk=(converted_prices["GBP"], fetched_prices["amazon.co.uk"][1]),
        amazon_de=(converted_prices["EUR"], fetched_prices["amazon.de"][1]),
        amazon_ca=(converted_prices["CAD"], fetched_prices["amazon.ca"][1])
    )

    save_price_comparison(conn, price_comparison.item, tuple(converted_prices.values()), USER_ID)

    return price_comparison


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)
