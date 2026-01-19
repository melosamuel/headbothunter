class RPA():
    company: str

    def __init__(self, company: str):
        self.company = company

    def scrape_stone(self):
        import Scraper.companies.stoneco as stoneco
        return stoneco.start()

