from .file_manager import FileManager
from .settings import DATA_FILE

class DataManager(FileManager):
    title: str
    date_str: str
    data: dict

    def __init__(self, title, date_str):
        super().__init__(file_path=DATA_FILE)
        self.title = title
        self.date_str = date_str
        self.data = super().load()

    def is_banned(self):
        banned = self.data.get("banned_titles", [])
        return (
            self.title in banned
            or self.date_str in banned
        )
