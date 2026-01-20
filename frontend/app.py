import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from flask import Flask, render_template, request
from backend.stone import StoneJobs

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/run-scraper', methods=['POST'])
def run_scraper():
    selected_teams = request.form.getlist('teams')

    if not selected_teams:
        return "<div class='p-4 text-red-500'>Please select at least one team.</div>"

    scraper = StoneJobs()
    jobs_dict = scraper.start(selected_teams)
    jobs_list = list(jobs_dict.values())

    return render_template('partials/job_list.html', jobs=jobs_list)

if __name__ == '__main__':
    app.run(debug=True)
