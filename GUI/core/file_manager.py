import json
import os

from .settings import DEFAULT_DATA

class FileManager():
    """
    Context manager for file operations.
    
    Attributes:
        - file_path (str): Path to the file.
        - encoding (str): Encoding format for the file.
    """
    file_path: str
    encoding: str

    def __init__(self, file_path, encoding='utf-8'):
        self.file_path = file_path
        self.encoding = encoding

    def save(self, data):
        """Save data to the JSON file."""
        with open(self.file_path, 'w', encoding=self.encoding) as f:
            json.dump(
                data,
                f,
                ensure_ascii=False,
                indent=4
            )

    def open(self):
        """
        Load data from the JSON file.
        
        Returns:
            dict: The data loaded from the file.
        """
        with open(self.file_path, 'r', encoding=self.encoding) as f:
            return json.load(f)

    def load(self):
        """Load data from the JSON file. If the file doesn't exist, create it with default data."""
        json_file = self.file_path
        if not os.path.exists(json_file):
            self.save(DEFAULT_DATA)
            return DEFAULT_DATA

        try:
            data = self.open()
            return data
        except json.JSONDecodeError:
            return DEFAULT_DATA

    def get_link(self, company_name: str) -> str | None:
        """
        Retrieve the job URL for a given company name.

        Args:
            company_name (str): The name of the company.

        Returns:
            str | None: The job URL if found, otherwise None.
        """

        data = self.load()
        companies = data.get("companies", [])

        for company in companies:
            if company.get("name") == company_name:
                return company.get("url")
        return None
