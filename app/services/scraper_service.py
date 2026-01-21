import os
import re
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright, expect
from dotenv import load_dotenv

load_dotenv()

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

class WorkanaJobs:
    page: any

    def start(self):
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            self.page = browser.new_page()
            projects = {}

            try:
                self.login()
            except Exception as e:
                raise e

            self.page.goto("https://www.workana.com/jobs?category=it-programming&language=en%2Cpt&subcategory=web-development%2Cmobile-development%2Cothers-5")

            try:
                self.page.wait_for_selector('a[href*="/job/"]', timeout=15000)
            except Exception as e:
                raise e

            current_page = 1
            while True:
                soup = BeautifulSoup(self.page.content(), 'html.parser')

                found_projects = self.scrape_common_tech_jobs(soup)

                projects.update(found_projects)

                if len(projects) >= 20:
                    break

                current_page += 1
                self.page.goto(f"https://www.workana.com/jobs?category=it-programming&language=en%2Cpt&subcategory=web-development%2Cmobile-development%2Cothers-5&page={current_page}")

            return projects

    def login(self):
        url = "https://workana.com/login"

        try:
            self.page.goto(url)

            email_input = self.page.locator("#email-input")
            password_input = self.page.locator("#password-input")
            submit_btn = self.page.locator("button:has-text('Login')")
            email_input.fill(os.environ.get("WORKANA_EMAIL", "test@test.com"))
            password_input.fill(os.environ.get("WORKANA_PASS", "A1234wert!@#"))
            submit_btn.click()

            expect(self.page).to_have_url("https://www.workana.com/dashboard")
        except Exception as e:
            raise e

    def scrape_common_tech_jobs(self, soup: BeautifulSoup):
        jobs = {}
        projects_container = soup.find('div', id='projects')

        projects = projects_container.select("div.project-item.js-project")

        for project in projects:
            badge = None
            job = {}

            # Get title, link and badge
            project_header = project.find("div", class_="project-header")
            wrapper = project_header.find("h2", class_="h3 project-title")
            link_element = wrapper.select_one("a")
            link = link_element.get("href")
            title = link_element.find("span").get_text(strip=True)
            badge_validator = wrapper.select_one("span.label.rounded")
            if badge_validator:
                badge = badge_validator.get_text(strip=True)

            # Get Published date and number of proposals
            published_date = project.find("span", class_="date").get_text(strip=True)
            proposals = project.find("span", class_="bids").get_text(strip=True)

            # Get description
            description = project.select_one(
                "div.html-desc.project-details > div > p > span"
            ).get_text(strip=True)

            # Get Budget
            budget = project.select_one("span.values > span").get_text(strip=True)

            job[link] = {
                "title": title,
                "link": link,
                "badge": badge,
                "published_date": published_date,
                "proposals": proposals,
                "description": description,
                "budget": budget
            }

            jobs.update(job)

        return jobs
