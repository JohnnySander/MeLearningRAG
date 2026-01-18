import asyncio
import logging
import pathlib

from crawl4ai import RateLimiter, CrawlerRunConfig, CacheMode
from crawl4ai import BrowserConfig, CrawlResult, AsyncWebCrawler
from crawl4ai import MemoryAdaptiveDispatcher, AsyncUrlSeeder, SeedingConfig

from db_sqlite import _init_site_db
from chunker import vec_process_content
from logger import setup_logger

if __name__ == "__main__":
    logger = setup_logger(__name__, logging.INFO)
else:
    logger = logging.getLogger(__name__)

SAVEFOLDER = './res_folder'

rate_limiter = RateLimiter(
    base_delay=(2.0, 4.0),  # Random delay between 2-4 seconds
    max_delay=30.0,         # Cap delay at 30 seconds
    max_retries=5,          # Retry up to 5 times on rate-limiting errors
    rate_limit_codes=[429, 503]  # Handle these HTTP status codes
)

dispatcher = MemoryAdaptiveDispatcher(
    memory_threshold_percent=90.0,  # Pause if memory exceeds this
    check_interval=1.0,             # How often to check memory
    max_session_permit=10,          # Maximum concurrent tasks
    rate_limiter=rate_limiter,      # Optional rate limiting
    )

browser_config = BrowserConfig(headless=True, verbose=False)
run_config = CrawlerRunConfig(
    cache_mode=CacheMode.BYPASS,
    stream=False,  # Default: get all results at once
    css_selector=None,
)


def page_file_name(url: str) -> str:
    """
        Generate a file name from web page URL.
    """
    name = url.replace('https://', '').replace('/', '_')
    if name[-1] == '_':
        name = name[:-1]

    return name


def process_result(result: CrawlResult, site: str) -> None:
    """
        Save web page scraping result to text file.
    """
    site_path = pathlib.Path(f'{SAVEFOLDER}/{site}')
    site_path.mkdir(parents=True, exist_ok=True)
    try:
        conn = _init_site_db(site_path)
        try:
            with conn:
                conn.execute(
                    'INSERT OR REPLACE INTO pages (site, url, content) VALUES (?, ?, ?)',
                    (site, result.url, result.markdown),
                )
        finally:
            conn.close()
    except Exception:
        logger.exception('Failed to write page to sqlite database for %s', result.url)


async def crawl_pages(urls: list[str], site: str) -> list[tuple[CrawlResult, str]]:
    """
        Crawl pages from sitemap.xml file
    """

    async with AsyncWebCrawler(config=browser_config) as crawler:
        results: list[CrawlResult] = await crawler.arun_many(urls=urls,
                                                             config=run_config,
                                                             dispatcher=dispatcher)

        return_results: list[tuple[CrawlResult, str]] = []
        faulty: int = 0
        for result in results:
            if not result.success:
                logger.error(
                    f'Failed url: {result.url} - {result.error_message}')
                faulty += 1
                continue

            if not result.markdown:
                logger.warning(f'No content found at {result.url}.')
                continue
            logger.debug(f'Size {result.url}: {len(result.markdown)}.')
            if __name__ == "__main__":
                # Script run directly, save files
                process_result(result, site)
            else:
                # Script run as a module, return results for further processing
                return_results.append((result, site))

        logger.info(f'Crawling completed for {urls}. {len(return_results)-faulty} pages processed successfully.')
        if faulty:
            logger.info(f'{faulty} pages failed to crawl.')

    return return_results


async def fetch_url_list(site_url: str, pattern: str) -> list[str]:
    """
        Get urls to crawl from site map file.
    """

    seeder = AsyncUrlSeeder()
    seed_config = SeedingConfig(
        # source="cc",
        source="sitemap",
        extract_head=False,
        pattern=pattern,
        live_check=True,
    )

    # Get ALL documentation URLs instantly
    sitemap = await seeder.urls(site_url, seed_config)
    logger.info(f'{len(sitemap)} stycken URLer funna.')
    with open(f'{SAVEFOLDER}/sitemap.txt', 'w', encoding='utf-8') as f:
        url_list = []
        for u in sitemap:
            url_list.append(u['url'])
            f.write(str(u) + '\n')

    return url_list


def main(site: str | None = None, url: str = "", pattern: str = "*") -> None:
    if site is None and not url:
        site = 'PydanticAI'
        url = 'https://ai.pydantic.dev'
    elif site is None or not url:
        raise ValueError("Both 'site' and 'url' must be provided together.")

    if __name__ != "__main__":
        logger.info(f'Starting crawl for site: {site}, URL: {url}, Pattern: {pattern}')
    crawl_setup = (site, url)
    urls = asyncio.run(fetch_url_list(crawl_setup[1], pattern))
    content = asyncio.run(crawl_pages(urls, crawl_setup[0]))
    logger.debug(f'Returned content count: {len(content)}')
    if content:
        vec_process_content(url, content)


if __name__ == "__main__":
    setup_logger(__name__, logging.INFO)
    main('StreamLit', 'https://docs.streamlit.io/', '*.io/d*')
