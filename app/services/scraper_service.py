import re
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

class StoneJobs:
    def start(self):
        url = f"https://jornada.stone.com.br/vagas-abertas?times=Tecnologia#top"

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(url)

            try:
                page.wait_for_selector('a[href*="/oportunidades/"]', timeout=15000)
            except Exception:
                browser.close()
                return {}

            jobs = {}

            page_count = 0
            while page_count < 5:
                page.wait_for_selector('a[href*="/oportunidades/"]', timeout=10000)
                soup = BeautifulSoup(page.content(), 'html.parser')

                found_jobs = self.scrape_jobs(soup)
                jobs.update(found_jobs)

                try:
                    next_button = page.query_selector("button:has-text('→')")
                    if next_button.is_disabled():
                        break

                    next_button.click()
                    page.wait_for_timeout(1000)
                    page_count += 1
                except Exception:
                    break

            browser.close()
            return jobs

    def scrape_jobs(self, soup):
        jobs = {}
        cards = soup.find_all('a', href=lambda href: href and '/oportunidades/' in href)

        for card in cards:
            link = card['href']
            title = card.find('h3').get_text(strip=True)
            details_wrapper = card.find_all('div', class_="flex items-center gap-1")

            remote = details_wrapper[0].find("span").get_text(strip=True) == "Brasil - BR"
            sector = details_wrapper[1].find("span").get_text(strip=True)
            posted_date_text = details_wrapper[2].find("span").get_text(strip=True)
            match = re.search(r'\d+', posted_date_text)
            posted_date = int(match.group()) if match else None
            posted_at = datetime.now() - timedelta(days=posted_date) if posted_date else "N/A"

            jobs[link] = {
                "title": title,
                "remote": remote,
                "sector": sector,
                "posted_at": posted_at,
                "link": link
            }

        return jobs
