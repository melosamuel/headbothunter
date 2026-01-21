import json
from datetime import datetime
from flask import Blueprint, render_template, request
from app.extensions import db, redis_client
from app.models import BlockedJob
from app.services.scraper_service import StoneJobs
from config import CACHE_KEY_JOBS, CACHE_TTL

main_bp = Blueprint('main', __name__)

@main_bp.route("/")
def index():
    return render_template('index.html')

@main_bp.route('/run-scraper', methods=['POST'])
def run_scraper():
    force_refresh = request.args.get('force') == 'true'

    jobs_data = []
    from_cache = False
    last_updated = "Recente"
    cache_key = CACHE_KEY_JOBS

    if not force_refresh:
        cached_result = redis_client.get(cache_key)
        if cached_result:
            try:
                payload = json.loads(cached_result)
                jobs_data = payload['data']
                last_updated = payload['updated_at']
                from_cache = True
            except Exception:
                pass

    if not jobs_data:
        scraper = StoneJobs()
        found_jobs_dict = scraper.start()

        for link, job_info in found_jobs_dict.items():
            formatted_date = job_info['posted_at'].strftime('%d/%m/%Y')

            jobs_data.append({
                "title": job_info['title'],
                "company": "Stone",
                "link": link,
                "sector": job_info['sector'],
                "remote": job_info['remote'],
                "posted_at": formatted_date
            })

        db.session.commit()

        now_str = datetime.now().strftime("%H:%M:%S")
        last_updated = now_str

        payload = {
            "data": jobs_data,
            "updated_at": now_str
        }
        redis_client.setex(cache_key, CACHE_TTL, json.dumps(payload, default=str))

    if jobs_data:
        blocked_entries = BlockedJob.query.with_entities(
            BlockedJob.title,
            BlockedJob.posted_at
        ).all()
        blocked_set = set(blocked_entries)

        jobs_data = [
            j for j in jobs_data
            if (j['title'], j['posted_at']) not in blocked_set
        ]

        jobs_data.sort(key=lambda x: x['posted_at'], reverse=True)

    return render_template(
        'partials/job_list.html',
        jobs=jobs_data,
        from_cache=from_cache,
        last_updated=last_updated
    )

@main_bp.route('/block-job', methods=['POST'])
def block_job():
    title = request.form.get('title')
    posted_at = request.form.get('posted_at')

    if title and posted_at:
        new_blocked = BlockedJob(title=title, posted_at=posted_at)
        db.session.add(new_blocked)
        db.session.commit()

        redis_client.delete(CACHE_KEY_JOBS)

    return ""
