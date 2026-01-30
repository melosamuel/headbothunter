import json
from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for
from app.extensions import db, redis_client
from app.models import Job, Project
from app.services.scraper_service import StoneJobs, WorkanaProjects
from config import CACHE_KEY_JOBS, CACHE_KEY_PROJECTS, CACHE_TTL

main_bp = Blueprint('main', __name__)

def render_next_card():
    next_project = Project.query.filter_by(status="new").first()

    if next_project:
        return render_template('partials/workana_card.html', project=next_project)

    return ""

@main_bp.route("/")
def index():
    return render_template('index.html')

@main_bp.route('/run-scraper', methods=['POST'])
def run_scraper(): # pylint: disable=too-many-locals,too-many-branches,too-many-statements
    force_refresh = request.args.get('force') == 'true'

    jobs_data = []
    from_cache = False
    from_db = False
    last_updated = "Recently"

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
        saved_jobs = Job.query.order_by(Job.found_at.desc()).all()

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
            status = existing_map.get(link)

            formatted_date = job_info['posted_at'].strftime('%d/%m/%Y')

            job = {
                "title": job_info['title'],
                "company": "Stone",
                "link": link,
                "sector": job_info['sector'],
                "remote": job_info['remote'],
                "posted_at": formatted_date,
                "status": status if status else "new"
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
        try:
            db.session.commit()
        except Exception:
            db.session.rollback()
        finally:
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
    job_link = request.form.get('link')

    if job_link:
        job = Job.query.filter_by(link=job_link).first()

        if job:
            job.status = 'blocked'
            db.session.commit()

            redis_client.delete(CACHE_KEY_JOBS)

    return ""

@main_bp.route('/mark-applied', methods=['POST'])
def mark_applied():
    job_link = request.form.get('link')

    if job_link:
        job = Job.query.filter_by(link=job_link).first()

        if job:
            job.status = 'applied'
            db.session.commit()

            redis_client.delete(CACHE_KEY_JOBS)

    return redirect(url_for('main.index'))

@main_bp.route('/workana')
def workana_hunt():
    current_project = Project.query.filter_by(status='new').first()
    saved_projects = Project.query.filter_by(status='saved').order_by(Project.created_at.desc()).all() # pylint: disable=line-too-long

    return render_template(
        'workana.html',
        current_project=current_project,
        saved_projects=saved_projects
    )

@main_bp.route('/workana/refresh', methods=['POST'])
def workana_refresh(): # pylint: disable=too-many-locals
    refresh = request.args.get('force') == 'true'

    projects_data = []
    last_updated = "Recently"

    if not refresh:
        cached_result = redis_client.get(CACHE_KEY_PROJECTS)
        if cached_result:
            try:
                payload = json.loads(cached_result)
                projects_data = payload['data']
                last_updated = payload['updated_at']
            except Exception:
                pass

    if not projects_data and not refresh:
        saved_projects = Project.query.filter(Project.status != "blocked").order_by(Project.created_at.desc()).all() # pylint: disable=line-too-long

        if saved_projects:
            projects_data = [p.to_dict() for p in saved_projects]
            last_updated = datetime.now().strftime("%H:%M:%S")

            payload = {
                "data": projects_data,
                "updated_at": last_updated
            }
            redis_client.setex(CACHE_KEY_PROJECTS, CACHE_TTL, json.dumps(payload, default=str))

    if not projects_data:
        scraper = WorkanaProjects()
        found_projects_dict = scraper.start()

        existing_projects_query = db.session.query(Project.link, Project.status).all()
        existing_map = {row.link: row.status for row in existing_projects_query}

        clean_display_list = []

        for link, project_info in found_projects_dict.items():
            status = existing_map.get(link)

            if status == "blocked":
                continue

            formatted_date = project_info['published_date']

            project = {
                "title": project_info['title'],
                "link": link,
                "badge": project_info['badge'],
                "published_date": formatted_date,
                "proposals": project_info['proposals'],
                "description": project_info['description'],
                "budget": project_info['budget'],
                "status": status if status else "new"
            }

            if status is None:
                new_db_project = Project(
                    title=project_info['title'],
                    link=link,
                    badge=project_info['badge'],
                    published_date=formatted_date,
                    proposals=project_info['proposals'],
                    description=project_info['description'],
                    budget=project_info['budget'],
                    status="new"
                )
                db.session.add(new_db_project)

            clean_display_list.append(project)
        try:
            db.session.commit()
        except Exception:
            db.session.rollback()
        finally:
            projects_data = clean_display_list

        last_updated = datetime.now().strftime("%H:%M:%S")

        payload = {
            "data": projects_data,
            "updated_at": last_updated
        }
        redis_client.setex(CACHE_KEY_PROJECTS, CACHE_TTL,json.dumps(payload, default=str))

    return render_next_card()

@main_bp.route('/workana/interact/<int:project_id>/<action>', methods=['POST'])
def block_project(project_id, action):
    project = Project.query.get_or_404(project_id)

    if action == "block":
        project.status = "blocked"
    elif action == "save":
        project.status = "saved"

    db.session.commit()

    saved_item_html = ""
    if action == "save":
        saved_item_html = render_template(
            'partials/workana_saved_item.html',
            project=project,
            oob=True
        )

    return f"{render_next_card()}{saved_item_html}"
