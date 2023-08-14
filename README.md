# Amazon Price Comparison Tool

This Amazon Price Comparison Tool is a web application that allows users to search for products on Amazon and compare their prices across different Amazon domains (US, UK, DE, and CA). The app also maintains a search history for each user, displaying the search queries and results.

---
## Features

- Search for products on Amazon.com
- Display the top 10 search results
- Compare product prices across Amazon.com, Amazon.co.uk, Amazon.de, and Amazon.ca
- Save search history for each user
- Hidden Easter egg somewhere :)
- **TODO**: User management.
---

## Getting Started

To run the Amazon Price Comparison Tool, follow these steps:

1. Ensure you have Python 3.7+ installed.
2. Install the required packages by running `pip install -r requirements.txt`.
3. Running the app you can choose to:
   - Run the application from `python app.py` file (line 166).
   - Run `uvicorn app:app --reload` command from the terminal and `ctrl + C` to terminate. Make sure you are inside the `bcakend` directory.
4. Access the web application in your browser at "http://localhost:8000" or at "http://127.0.0.1:8000".
5. If you want to restart the DB you can run `python my_db.py`.
    - The DB is initialized empty.

---
## How to Use

1. Enter a search query in the search bar and click the "Search" button or press Enter.
2. The application will display the top 10 search results. To compare the product prices across different Amazon domains, click the "Compare Prices!" button next to a product.
3. The price comparison table will display the product's price in $ each Amazon domain and the rating from Amazon.com. Click on the price to visit the product page on the respective Amazon website.
    - If price wasn't found you can click the link to search similar results in the specific domain.
4. There is a limitation of 10 searches a day.
   - If you want to ignore the limit for extra testing, **comment line 173** 
5. Try to find the Easter egg.

---
## Tech Stack

- Frontend: HTML, CSS, JavaScript
- Backend: Python (FastAPI)
- Web scraping: Beautiful Soup, aiohttp
- Concurrency: Asynchronous Programming with `asyncio`

---
## Notes

- This application uses web scraping to retrieve product information from Amazon websites. As a result, it may stop working if Amazon changes its website structure or implements measures to prevent web scraping.
- The application does not store any user information or share it with third parties. It only saves the search history locally in the browser.
- No AI was harm during the creation of the project.
