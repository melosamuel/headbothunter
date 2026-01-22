from datetime import datetime
from app.extensions import db

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
    status = db.Column(db.String(20), default="new")

    def to_dict(self):
        return {
            "title": self.title,
            "company": self.company,
            "link": self.link,
            "sector": self.sector,
            "remote": self.remote,
            "posted_at": self.posted_at,
            "status": self.status
        }

class Project(db.Model):
    __tablename__ = "projects"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    link = db.Column(db.String(200), nullable=False)
    badge = db.Column(db.String(50), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.now)
    proposals = db.Column(db.Integer, nullable=False)
    description = db.Column(db.String(400), nullable=False)
    budget = db.Column(db.String(50), nullable=False)
    status = db.Column(db.String(20), default="new")

    def to_dict(self):
        return {
            "title": self.title,
            "link": self.link,
            "badge": self.badge,
            "description": self.description,
            "proposals": self.proposals,
            "budget": self.budget,
            "status": self.status,
            "created_at": self.created_at
        }
