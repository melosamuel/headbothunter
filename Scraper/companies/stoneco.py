import time
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

def start():
    url = "https://jornada.stone.com.br/vagas-abertas?times=Tecnologia"

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=["--no-sandbox"])
        page = browser.new_page()
        page.goto(url)

        try:
            page.wait_for_selector('a[href*="/oportunidades/"]', timeout=15000)
        except:
            print("Timeout: As vagas demoraram demais para aparecer.")
            browser.close()
            return []

        html_content = page.content()
        browser.close()
        
        return parse_rendered_html(html_content)

def parse_rendered_html(html):
    soup = BeautifulSoup(html, 'html.parser')
    jobs = []

    for link in soup.find_all('a', href=True):
        if '/oportunidades/' in link['href']:
            title_tag = link.find(['h2', 'h3', 'h4', 'span'])
            title = title_tag.get_text(strip=True) if title_tag else link.get_text(strip=True)
            
            if len(title) > 5 and title not in [j['title'] for j in jobs]:
                jobs.append({
                    "title": title,
                    "date": "Ver no site",
                    "desc": "Vaga encontrada via Renderização Dinâmica",
                    "link": f"https://jornada.stone.com.br{link['href']}" if link['href'].startswith('/') else link['href']
                })
    
    return jobs
