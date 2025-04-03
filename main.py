import argparse
import asyncio
import aiohttp
import async_timeout
import sqlite3
import json
import csv
import os
import random
import time
import logging
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
from tqdm.asyncio import tqdm_asyncio
import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
import threading

from flask import Flask, render_template, request, redirect, url_for, flash

# تأكد من تنزيل الموارد اللازمة من NLTK (شغّل السطرين التاليين مرة واحدة إذا لم تقم بذلك مسبقًا)
# nltk.download('punkt')
# nltk.download('stopwords')

# إعداد تسجيل الأحداث
logging.basicConfig(
    level=logging.INFO,
    format='[%(levelname)s] %(asctime)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    handlers=[
        logging.FileHandler("crawler.log", encoding="utf-8"),
        logging.StreamHandler()
    ]
)

# قائمة user-agent عشوائية لتدويرها
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/90.0.4430.93 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 Safari/14.0.3",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/88.0.4324.96 Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15 Mobile/15A372 Safari/604.1"
]

# أنواع الملفات غير المرغوب فيها
DISALLOWED_EXTENSIONS = (
    '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.pdf',
    '.doc', '.docx', '.xls', '.xlsx', '.zip', '.rar'
)

# إعداد قاعدة البيانات SQLite لتخزين نتائج الزحف
DB_NAME = "crawler_results.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute('''
        CREATE TABLE IF NOT EXISTS pages (
            url TEXT PRIMARY KEY,
            title TEXT,
            meta_description TEXT,
            keywords TEXT,
            response_time REAL,
            depth INTEGER,
            internal INTEGER,
            images TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

def save_page_to_db(data):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    try:
        cur.execute('''
            INSERT OR REPLACE INTO pages (url, title, meta_description, keywords, response_time, depth, internal, images)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            data['url'],
            data.get('title'),
            data.get('meta_description'),
            data.get('keywords'),
            data.get('response_time'),
            data.get('depth'),
            1 if data.get('internal') else 0,
            json.dumps(data.get('images'))
        ))
        conn.commit()
    except Exception as e:
        logging.error(f"خطأ أثناء حفظ الصفحة {data['url']} في قاعدة البيانات: {e}")
    finally:
        conn.close()

def export_results():
    """
    تصدير النتائج إلى ملفات CSV و JSON.
    """
    try:
        for filename in ["results.csv", "results.json"]:
            if os.path.exists(filename):
                os.remove(filename)
    except Exception as e:
        logging.error(f"خطأ أثناء حذف الملفات السابقة: {e}")

    try:
        conn = sqlite3.connect(DB_NAME)
        cur = conn.cursor()
        cur.execute("SELECT * FROM pages")
        rows = cur.fetchall()
        columns = [desc[0] for desc in cur.description]
        with open("results.csv", "w", newline="", encoding="utf-8") as f_csv:
            writer = csv.writer(f_csv)
            writer.writerow(columns)
            writer.writerows(rows)
        results = [dict(zip(columns, row)) for row in rows]
        with open("results.json", "w", encoding="utf-8") as f_json:
            json.dump(results, f_json, ensure_ascii=False, indent=4)
        conn.close()
        logging.info("تم تصدير النتائج بنجاح إلى results.csv و results.json")
    except Exception as e:
        logging.error(f"خطأ أثناء تصدير النتائج: {e}")

def save_checkpoint(visited, filename="checkpoint.txt"):
    """حفظ قائمة الروابط التي تمت زيارتها لاستئناف الزحف لاحقًا"""
    try:
        with open(filename, "w", encoding="utf-8") as f:
            for url in visited:
                f.write(url + "\n")
    except Exception as e:
        logging.error(f"خطأ أثناء حفظ نقطة التوقف: {e}")

def load_checkpoint(filename="checkpoint.txt"):
    """تحميل قائمة الروابط التي تمت زيارتها من نقطة التوقف"""
    if not os.path.exists(filename):
        return set()
    try:
        with open(filename, "r", encoding="utf-8") as f:
            return set(line.strip() for line in f if line.strip())
    except Exception as e:
        logging.error(f"خطأ أثناء تحميل نقطة التوقف: {e}")
        return set()

def extract_structured_data(html, url):
    """استخراج العنوان والوصف والصور من الصفحة"""
    soup = BeautifulSoup(html, "html.parser")
    title = soup.title.get_text().strip() if soup.title else ""
    meta_desc = ""
    meta = soup.find("meta", attrs={"name": "description"})
    if meta and meta.get("content"):
        meta_desc = meta.get("content").strip()
    images = [urljoin(url, img.get("src").strip()) for img in soup.find_all("img", src=True)]
    return title, meta_desc, images

def analyze_text(text):
    """تحليل نص لاستخراج كلمات مفتاحية باستخدام NLTK"""
    try:
        tokens = word_tokenize(text.lower())
        filtered = [w for w in tokens if w.isalnum() and w not in stopwords.words('english')]
        freq = {}
        for word in filtered:
            freq[word] = freq.get(word, 0) + 1
        keywords = sorted(freq, key=freq.get, reverse=True)[:5]
        return ", ".join(keywords)
    except Exception as e:
        logging.error(f"خطأ أثناء تحليل النص: {e}")
        return ""

def is_allowed_url(url):
    """التأكد من عدم انتهاء الرابط بامتداد غير مرغوب فيه"""
    return not url.lower().endswith(DISALLOWED_EXTENSIONS)

def is_internal(url, base_netloc):
    """تصنيف الرابط إذا كان داخليًا بالنسبة للنطاق الأساسي"""
    try:
        return urlparse(url).netloc.endswith(base_netloc)
    except Exception:
        return False

class AsyncCrawler:
    def __init__(self, start_url, strategy="bfs", max_depth=2, max_tasks=10, checkpoint_file="checkpoint.txt", ext_limit=500, err429_limit=5):
        self.start_url = start_url
        self.base_netloc = urlparse(start_url).netloc.replace("www.", "")
        self.strategy = strategy  # "bfs", "dfs" أو "greedy"
        self.max_depth = max_depth
        self.max_tasks = max_tasks
        self.visited = load_checkpoint(checkpoint_file)
        self.checkpoint_file = checkpoint_file
        self.queue = asyncio.PriorityQueue()
        # إضافة الصفحة الابتدائية مع أولوية محسوبة بحسب الاستراتيجية
        self.queue.put_nowait((self.get_priority(start_url, 0), start_url, 0))
        self.sem = asyncio.Semaphore(max_tasks)
        # عداد للروابط الخارجية مع حد أقصى
        self.external_links_count = 0
        self.external_links_limit = ext_limit
        # عداد خاص بحالة 429 وحدها
        self.error_429_count = 0
        self.error_429_limit = err429_limit

    def get_priority(self, url, depth):
        """
        حساب أولوية الرابط بناءً على الاستراتيجية المختارة.
        - BFS: الأولوية تساوي العمق.
        - DFS: الأولوية تساوي -العمق.
        - Greedy: الأولوية تعتمد على طول الرابط.
        """
        if self.strategy == "bfs":
            return depth
        elif self.strategy == "dfs":
            return -depth
        elif self.strategy == "greedy":
            return len(url)
        else:
            return depth

    async def fetch(self, session, url):
        """
        جلب الصفحة مع إعادة المحاولة وتأخير ديناميكي.
        """
        retries = 3
        backoff = 1
        for attempt in range(retries):
            try:
                headers = {"User-Agent": random.choice(USER_AGENTS)}
                start_time = time.monotonic()
                async with async_timeout.timeout(15):
                    async with session.get(url, headers=headers) as response:
                        if response.status != 200:
                            logging.warning(f"الرابط {url} أعاد الحالة {response.status}")
                            if response.status == 429:
                                self.error_429_count += 1
                                if self.error_429_count >= self.error_429_limit:
                                    logging.error(f"تم تجاوز حد أخطاء 429 ({self.error_429_count} مرة). إيقاف معالجة الرابط.")
                                    return None, None
                            await asyncio.sleep(backoff)
                            backoff *= 2
                            continue
                        html = await response.text()
                        return html, time.monotonic() - start_time
            except Exception as e:
                logging.error(f"خطأ أثناء جلب {url} (محاولة {attempt+1}/3): {e}")
                await asyncio.sleep(backoff)
                backoff *= 2
        return None, None

    async def process_url(self, priority, url, depth, session):
        """
        معالجة الرابط: جلب الصفحة، استخراج البيانات وتخزينها، واستخراج الروابط الجديدة.
        """
        if url in self.visited:
            return
        async with self.sem:
            html, response_time = await self.fetch(session, url)
        if html is None:
            return
        self.visited.add(url)
        title, meta_desc, images = extract_structured_data(html, url)
        keywords = analyze_text(f"{title} {meta_desc}")
        internal = is_internal(url, self.base_netloc)
        page_data = {
            "url": url,
            "title": title,
            "meta_description": meta_desc,
            "keywords": keywords,
            "response_time": response_time,
            "depth": depth,
            "internal": internal,
            "images": images
        }
        save_page_to_db(page_data)
        logging.info(f"تمت معالجة: {url} [عمق: {depth}, زمن الاستجابة: {response_time:.2f} ثواني]")
        await asyncio.sleep(min(response_time, 2))
        if depth < self.max_depth:
            soup = BeautifulSoup(html, "html.parser")
            for a in soup.find_all("a", href=True):
                link = a["href"].strip()
                if not link:
                    continue
                link = urljoin(url, link).split("#")[0]
                if not is_allowed_url(link):
                    continue
                if is_internal(link, self.base_netloc):
                    await self.queue.put((self.get_priority(link, depth + 1), link, depth + 1))
                else:
                    if self.external_links_count < self.external_links_limit:
                        self.external_links_count += 1
                        logging.info(f"رابط خارجي تم اكتشافه: {link}")
                    else:
                        logging.debug(f"تم تجاوز حد الروابط الخارجية؛ تم تجاهل الرابط: {link}")

    async def worker(self, session):
        """عامل يقوم بمعالجة الروابط من قائمة الانتظار."""
        while True:
            try:
                priority, url, depth = await asyncio.wait_for(self.queue.get(), timeout=30)
            except asyncio.TimeoutError:
                break
            await self.process_url(priority, url, depth, session)
            self.queue.task_done()
            if len(self.visited) % 10 == 0:
                save_checkpoint(self.visited, self.checkpoint_file)

    async def crawl(self):
        """الدالة الرئيسية لتنفيذ الزحف."""
        connector = aiohttp.TCPConnector(limit=self.max_tasks)
        async with aiohttp.ClientSession(connector=connector) as session:
            tasks = [asyncio.create_task(self.worker(session)) for _ in range(self.max_tasks)]
            with tqdm_asyncio(total=self.queue.qsize(), desc="روابط قيد المعالجة") as pbar:
                while not self.queue.empty():
                    await asyncio.sleep(1)
                    pbar.update(0)
            await self.queue.join()
            for task in tasks:
                task.cancel()

async def main(args):
    init_db()
    strategy_map = {1: "bfs", 2: "greedy", 3: "dfs"}
    strategy = strategy_map.get(args.strategy, "bfs")
    logging.info(f"بدأ الزحف باستخدام الاستراتيجية: {strategy.upper()}")
    crawler = AsyncCrawler(
        start_url=args.start_url,
        strategy=strategy,
        max_depth=args.max_depth,
        max_tasks=args.max_tasks,
        checkpoint_file="checkpoint.txt",
        ext_limit=500,
        err429_limit=5
    )
    await crawler.crawl()
    save_checkpoint(crawler.visited, crawler.checkpoint_file)
    export_results()
    logging.info(f"انتهى الزحف. تمت زيارة {len(crawler.visited)} رابط.")

# --------------------- إنشاء تطبيق  ---------------------

app = Flask(__name__)
app.secret_key = "your_secret_key_here"  # تأكد من استبداله بمفتاح سري آمن

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        # قراءة البيانات من النموذج
        start_url = request.form.get('start_url', 'https://ust.edu.ye')
        try:
            max_depth = int(request.form.get('max_depth', 1))
            max_tasks = int(request.form.get('max_tasks', 10))
            strategy_val = int(request.form.get('strategy', 1))
        except ValueError:
            flash("يرجى التأكد من إدخال قيم رقمية صحيحة.", "danger")
            return redirect(url_for('index'))
        # إنشاء كائن args لتوافق الدالة main
        args = argparse.Namespace(start_url=start_url, max_depth=max_depth, max_tasks=max_tasks, strategy=strategy_val)
        # تشغيل عملية الزحف في خيط منفصل
        threading.Thread(target=lambda: asyncio.run(main(args)), daemon=True).start()
        flash("تم بدء عملية الزحف. راجع ملف السجل (crawler.log) لمزيد من التفاصيل.", "success")
        return redirect(url_for('index'))
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)
