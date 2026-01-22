import json
from datetime import datetime
from flask import Blueprint, render_template, request
from app.extensions import db, redis_client
from app.models import Job
from app.services.scraper_service import StoneJobs
from config import CACHE_KEY_JOBS, CACHE_TTL

main_bp = Blueprint('main', __name__)

@main_bp.route("/")
def index():
    return render_template('index.html')

@main_bp.route('/run-scraper', methods=['POST'])
def run_scraper(): # pylint: disable=too-many-locals,too-many-branches,too-many-statements
    force_refresh = request.args.get('force') == 'true'

    jobs_data = []
    from_cache = False
    from_db = False
    last_updated = "Recente"

    if not force_refresh:
        cached_result = redis_client.get(CACHE_KEY_JOBS)
        if cached_result:
            try:
                payload = json.loads(cached_result)
                jobs_data = payload['data']
                last_updated = payload['updated_at']
                from_cache = True
            except Exception:
                pass

    if not jobs_data and not force_refresh:
        saved_jobs = Job.query.filter(Job.status != "blocked").order_by(Job.found_at.desc()).all()

        if saved_jobs:
            jobs_data = [j.to_dict() for j in saved_jobs]
            from_db = True
            last_updated = datetime.now().strftime("%H:%M:%S")

            payload = {
                "data": jobs_data,
                "updated_at": last_updated
            }
            redis_client.setex(CACHE_KEY_JOBS, CACHE_TTL, json.dumps(payload, default=str))

    if not jobs_data:
        scraper = StoneJobs()
        found_jobs_dict = scraper.start()

        existing_jobs_query = db.session.query(Job.link, Job.status).all()
        existing_map = {row.link: row.status for row in existing_jobs_query}

        clean_display_list = []

        for link, job_info in found_jobs_dict.items():
            status = existing_map.get(status)

            if status == 'blocked':
                continue

            formatted_date = job_info['posted_at'].strftime('%d/%m/%Y')

            job = {
                "title": job_info['title'],
                "company": "Stone",
                "link": link,
                "sector": job_info['sector'],
                "remote": job_info['remote'],
                "posted_at": formatted_date,
                "status": "new"
            }

            if status is None:
                new_db_job = Job(
                    title=job_info['title'],
                    company="Stone",
                    link=link,
                    sector=job_info['sector'],
                    remote=job_info['remote'],
                    posted_at=formatted_date,
                    status="new"
                )
                db.session.add(new_db_job)
                clean_display_list.append(job)
            else:
                clean_display_list.append(job)
        try:
            db.session.commit()
            jobs_data = clean_display_list
        except Exception:
            db.session.rollback()
            jobs_data = clean_display_list

        last_updated = datetime.now().strftime("%H:%M:%S")

        payload = {
            "data": jobs_data,
            "updated_at": last_updated
        }
        redis_client.setex(CACHE_KEY_JOBS, CACHE_TTL, json.dumps(payload, default=str))

    if jobs_data:
        try:
            jobs_data.sort(
                key=lambda x: datetime.strptime(x['posted_at'], '%d/%m/%Y'),
                reverse=True
            )
        except Exception:
            pass

    return render_template(
        'partials/job_list.html',
        jobs=jobs_data,
        from_cache=from_cache,
        from_db=from_db,
        last_updated=last_updated
    )

@main_bp.route('/block-job', methods=['POST'])
def block_job():
    return ""
