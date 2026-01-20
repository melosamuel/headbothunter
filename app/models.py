from datetime import datetime
from app import db

class Job(db.Model):
    __tablename__ = 'jobs'

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    title = db.Column(db.String(200), nullable=False)
    company = db.Column(db.String(100), nullable=False)
    link = db.Column(db.String(500), unique=True, nullable=False)
    sector = db.Column(db.String(100))
    remote = db.Column(db.Boolean, default=False)

    found_at = db.Column(db.DateTime, default=datetime.now)
    posted_at = db.Column(db.String(50))

    def to_dict(self):
        return {
            "title": self.title,
            "company": self.company,
            "link": self.link,
            "sector": self.sector,
            "remote": self.remote,
            "posted_at": self.posted_at
        }
