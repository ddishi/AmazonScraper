function openModal() {
    const modal = document.getElementById("subscription-modal");
    modal.style.display = "block";
}

function closeModal() {
    const modal = document.getElementById("subscription-modal");
    modal.style.display = "none";
}

// event listener to close the modal when the 'x' button is clicked
document.querySelector(".close").addEventListener("click", closeModal);

// Display price comparison for a specific ASIN and the corresponding data
async function showPriceComparison(asin, data) {

    // Get the comparison table element and clear previous results
    const comparisonTable = document.getElementById("comparison-table");
    comparisonTable.innerHTML = "";
    document.getElementById("search-results").style.display = "none";
    comparisonTable.style.display = "block";
    comparisonTable.style.width = "100%";

    // Create the header row and add header cells
    const headerRow = comparisonTable.insertRow();
    const headers = ["Item", "Rating", "Amazon.com", "Amazon.co.uk", "Amazon.de", "Amazon.ca"];
    headers.forEach(header => {
        const th = document.createElement("th");
        th.appendChild(document.createTextNode(header));
        headerRow.appendChild(th);
    });

    // Add the data row and populate it with data from the input object
    const dataRow = comparisonTable.insertRow();
    const itemNameCell = dataRow.insertCell();
    itemNameCell.appendChild(document.createTextNode(data.item));
    const ratingCell = dataRow.insertCell();
    ratingCell.appendChild(document.createTextNode(data.rating));

    // Iterate through the Amazon domains, prices, and URLs, creating cells with links to each domain's product page
    const amazonDomains = ["amazon.com", "amazon.co.uk", "amazon.de", "amazon.ca"];
    const prices = [data.amazon_com[0], data.amazon_co_uk[0], data.amazon_de[0], data.amazon_ca[0]];
    const urls = [data.amazon_com[1], data.amazon_co_uk[1], data.amazon_de[1], data.amazon_ca[1]];

    for (let i = 0; i < amazonDomains.length; i++) {
        const priceCell = dataRow.insertCell();
        const priceAnchor = document.createElement("a")

        if (!prices[i]) priceAnchor.textContent = "Price Not Found - Search Similar"
        else priceAnchor.textContent = prices[i] + ' $';
        priceAnchor.setAttribute("href", urls[i])
        priceAnchor.setAttribute("target", "_blank")
        priceCell.appendChild(priceAnchor);
    }
}

// Event listeners and functions related to searching and displaying results
document.addEventListener("DOMContentLoaded", () => {
    const searchButton = document.getElementById("search-button");
    const searchResults = document.getElementById("search-results");

    const searchInput = document.getElementById("search-input");
    searchInput.addEventListener("keydown", async (event) => {
        if (event.key === "Enter") {
            event.preventDefault();
            await searchItems();
        }
    });


    async function searchItems() {
        // Clear previous results
        searchResults.innerHTML = "";

        const query = searchInput.value;

        try {
            const response = await fetch("/search", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify({query}),
            });

            // Handle search limit and empty query cases
            if (response.status === 429) {
                openModal();
                return;
            }
            if (response.status === 400) {
                alert("Please enter a search query");

                return;
            }

            if (!response.ok) {
                console.log(response)
                throw new Error(`HTTP error ${response.status}`);
            }

            const data = await response.json();
            // Render the results
            showTenResults(searchResults, data)

        } catch (error) {
            console.error("Failed to fetch search results", error);
        }
    }

    searchButton.addEventListener("click", async (event) => {
        event.preventDefault();
        await searchItems();
    });

    // Event listener and function for retrieving and displaying search history
    const searchHistoryBtn = document.getElementById("search-history-btn");
    searchHistoryBtn.addEventListener("click", getSearchHistory);

    // Easter egg event listener
    document.getElementById("easter-egg-image").addEventListener("click", function () {
        window.open("https://en.wikipedia.org/wiki/Easter_egg");
    });
});


// Function to fetch and display search history
async function getSearchHistory() {
    const user_id = 0;  // DEFAULT - Replace this with the actual user_id from your frontend
    try {
        const response = await fetch(`/search_history?user_id=${user_id}`);
        if (response.ok) {
            const searchHistory = await response.json();

            displaySearchHistory(searchHistory);

        }
        if (response.status === 404) {
            alert("No search history found");
        }

    } catch (error) {
        console.error("Failed to fetch search history");
    }
}


// Function to process and display the search history data
function displaySearchHistory(searchHistory) {
    const searchResults = document.getElementById("search-results");
    searchResults.innerHTML = "";
    searchResults.style.display = "block";
    document.getElementById("comparison-table").style.display = "none";

    // Create the header row and add header cells
    const headerRow = searchResults.insertRow();
    const headers = ["Query", "Time", "Item", "Amazon.com", "Amazon.co.uk", "Amazon.de", "Amazon.ca"];
    headers.forEach(header => {
        const th = document.createElement("th");
        th.appendChild(document.createTextNode(header));
        headerRow.appendChild(th);
    });

    // Iterate through the search history records and create rows with cells for each data field
    for (const record of searchHistory) {
        const newRow = searchResults.insertRow();

        insertTextCellToRow(newRow, record.Query)
        insertTextCellToRow(newRow, record.Time)

        let itemCompared = record.Item_name;
        let itemName = itemCompared ?? "Comparison Incomplete";
        insertTextCellToRow(newRow, itemName)

        // Iterate through the Amazon domains and display the corresponding price information
        const amazonDomains = ["Amazon_US", "Amazon_UK", "Amazon_DE", "Amazon_CA"];

        for (const domain of amazonDomains) {
            let hasPrice = itemCompared ? (record[domain] ?? "Price Not Found") : "-";
            let num = parseFloat(hasPrice).toLocaleString('en-US', {
                minimumFractionDigits: 0,
                maximumFractionDigits: 2
            });
            hasPrice = (num === "NaN") ? hasPrice : num + ' $';
            insertTextCellToRow(newRow, hasPrice)
        }
    }

}


// Function to insert a text cell into a table row
function insertTextCellToRow(row, text) {
    const cell = row.insertCell()
    cell.appendChild(document.createTextNode(text))
}


// Display the top 10 search results in the specified table using the provided data
function showTenResults(table, data) {
    // Creating table header
    const header = table.createTHead();
    const headerRow = header.insertRow();
    let headers = ["Name", "image", ""];
    for (let text of headers) {
        let th = document.createElement("th");
        th.appendChild(document.createTextNode(text));
        headerRow.appendChild(th);
    }

    // Display the search results and hide the comparison table
    table.style.display = "block";
    document.getElementById("comparison-table").style.display = "none";

    // Iterate through the search and create table rows with cells for the product name, image, and a "Compare Prices!" button
    for (const result of data) {
        const newRow = table.insertRow();
        insertTextCellToRow(newRow, result.title);

        // Add an image cell with the product image
        const imageCell = newRow.insertCell();
        const imageElement = document.createElement("img");
        imageElement.src = result.image_url;
        imageElement.alt = result.title;
        imageElement.style.width = '64px';
        imageElement.style.height = '64px';
        imageCell.appendChild(imageElement);

        // Add a button cell with the "Compare Prices!" button
        const buttonCell = newRow.insertCell();
        const buttonElement = document.createElement("button");
        buttonElement.textContent = "Compare Prices!";
        buttonElement.id = result.asin;

        // Add an event listener to fetch price comparison data when the button is clicked
        buttonElement.addEventListener("click", async function () {
            const response = await fetch(`/price-comparison/${result.asin}`);
            if (response.ok) {
                const data = await response.json();
                await showPriceComparison(result.asin, data);
            } else {
                console.error(`Failed to fetch data: ${response.statusText}`);
            }
        });

        // Append the button element to the button cell
        buttonCell.appendChild(buttonElement);
    }
}
