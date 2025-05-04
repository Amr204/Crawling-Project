# 🕸️ Web Crawler Project 🕷️

This project is an **asynchronous web crawler** designed to crawl a website, extract key information such as titles, meta descriptions, keywords, and images, and store the results in an SQLite database. Additionally, it provides an interface to visualize and control the crawling process via a **Flask** web application.

---

## 📑 Table of Contents

1. [Installation](#installation)
2. [Dependencies](#dependencies)
3. [Project Structure](#project-structure)
4. [How it Works](#how-it-works)
5. [Configuration](#configuration)
6. [Usage](#usage)
7. [Exporting Results](#exporting-results)
8. [Web Interface](#web-interface)
9. [Logging](#logging)
10. [License](#license)

---

## 📦 Dependencies

The following Python packages are required:

- **argparse**: For command-line argument parsing.
- **aiohttp**: For asynchronous HTTP requests.
- **async_timeout**: For controlling timeouts in asynchronous operations.
- **sqlite3**: To interact with SQLite databases.
- **json**: For handling JSON data.
- **csv**: For exporting data to CSV format.
- **BeautifulSoup (bs4)**: For parsing HTML and extracting structured data.
- **tqdm**: For showing progress bars for long-running tasks.
- **nltk**: For natural language processing, including tokenization and stopword removal.
- **Flask**: For creating the web interface.

---

## 📂 Project Structure

| File/Folder             | Description                                    |
|-------------------------|------------------------------------------------|
| `app.py`                | Main Flask application                        |
| `crawler.py`            | Core crawler functionality                    |
| `crawler.log`           | Log file for tracking the crawl process       |
| `results.csv`           | Exported crawl results in CSV format          |
| `results.json`          | Exported crawl results in JSON format         |
| `requirements.txt`      | List of required Python packages              |
| `templates/`            | Folder containing templates for Flask         |
| `templates/index.html`  | HTML template for the Flask web interface     |

---

## 🔍 How it Works

- **Crawler Initialization**: The `AsyncCrawler` class initializes with a start URL, crawling strategy, and depth limit. It uses an asynchronous queue (`asyncio.PriorityQueue`) to manage URLs to be crawled, and a semaphore (`asyncio.Semaphore`) to control concurrent tasks.

- **Fetching Data**: Using `aiohttp`, the crawler makes asynchronous HTTP requests to the target pages. For each page, it extracts key information like:
  - **Title** 📑
  - **Meta Description** 📝
  - **Keywords** 🔑 (extracted using NLTK)
  - **Images** 🖼️ (URLs of images on the page)

- **Page Processing**: Each page's metadata is saved into an SQLite database. Links to internal pages are added to the queue, while external links are tracked up to a specified limit.

- **Error Handling and Retrying**: The crawler handles HTTP errors (like 429 - Too Many Requests) and retries failed requests, with **exponential backoff**.

- **Stopping the Crawl**: The crawl process is designed to handle interruptions gracefully. **Checkpoints** are saved periodically, allowing the crawl to be resumed from where it left off.

---

## ⚙️ Configuration

The crawler can be configured through command-line arguments and the Flask web interface.

- **Start URL** 🌐: The URL from which the crawler begins.
- **Max Depth** 🔽: The maximum depth of links the crawler will follow.
- **Max Tasks** 🧑‍💻: The maximum number of concurrent requests.
- **Crawl Strategy**:
  - `bfs` 🏃‍♂️: Breadth-First Search.
  - `dfs` 🧗‍♀️: Depth-First Search.
  - `greedy` 🤑: Crawler prioritizes shorter URLs.

Example command to run the crawler:

> ```bash
> python app.py --start_url "https://example.com" --max_depth 3 --max_tasks 5 --strategy 1
> ```


---

## 🖥️ Usage

### Command-Line Usage

You can run the crawler from the command line with the following arguments:

- `--start_url`: The URL from which the crawler begins.
- `--max_depth`: The maximum depth the crawler will follow links.
- `--max_tasks`: The maximum number of concurrent tasks.
- `--strategy`: The crawling strategy (1 for BFS, 2 for greedy, 3 for DFS).

### Web Interface

You can also control the crawling process via a **Flask web application**. Here’s how:

1. **Access the Web Interface**: Once the application is running, navigate to `http://127.0.0.1:5000` in your web browser.
2. **Start a Crawl**: Enter the start URL, max depth, and other parameters in the form and click **Start Crawling** 🚀.
3. **View Logs**: View detailed logs of the crawling process in the browser or in the `crawler.log` file 📜.

---

## 📈 Exporting Results

After the crawl is complete, you can export the results to both **CSV** and **JSON** formats.

The results include:

- **URL** 🌐: The crawled URL.
- **Title** 📑: The title of the page.
- **Meta Description** 📝: The meta description of the page.
- **Keywords** 🔑: The extracted keywords.
- **Response Time** ⏱️: The time it took to fetch the page.
- **Depth** 🔽: The depth at which the page was found.
- **Internal** 🔒: Whether the URL is internal or external.
- **Images** 🖼️: List of image URLs on the page.

To export results manually, call the `export_results()` function in `crawler.py`.


---

## 🌐 Web Interface

The **Flask web interface** allows users to:

- Input the **start URL** 🌐, **max depth** 🔽, and **max tasks** 🧑‍💻.
- Select the **crawl strategy** 🏃‍♂️🧗‍♀️🤑.
- Start the crawl process asynchronously 🚀.
- View **real-time logs** and **status updates** 📜.
- **Download** the crawl results once finished 📂.

---

## 📚 Logging

The crawler maintains a detailed log (`crawler.log`) of its operations. Logs include:

- Crawling **start** and **end times** ⏰.
- **Errors** and **retries** 🔄.
- **URL processing status** (including response times) ⚡.
- **Warnings** for unexpected statuses like 404, 500, or 429 ⚠️.

Logging is set up to output both to the console and to the `crawler.log` file for persistent record-keeping.

---

## 📝 License

This project is licensed under the **MIT License** - see the LICENSE file for details.

---

## 🕷️ Enjoy crawling the web! 🌍