from flask import Flask, render_template, request
import time

app = Flask(__name__)

def mock_scrape_jobs(keyword):
    time.sleep(2)
    return [
        {"title": f"Dev {keyword} Jr", "company": "Tech A", "link": "#"},
        {"title": f"Dev {keyword} Mid-Level", "company": "Infinix Tech", "link": "#"},
        {"title": f"QA {keyword}", "company": "Global Corp", "link": "#"},
    ]

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/search', methods=['POST'])
def search():
    keyword = request.form.get('keyword')
    jobs = mock_scrape_jobs(keyword)
    return render_template('partials/job_list.html', jobs=jobs)

if __name__ == '__main__':
    app.run(debug=True)
