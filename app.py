import json
import queue
import threading
import uuid

from flask import Flask, Response, render_template, request, jsonify

from services.csv_parser import parse_watched_csv, parse_letterboxd_zip
from services.scraper import scrape_user_films
from services.aggregator import aggregate_countries

app = Flask(__name__)

# In-memory store for background jobs: job_id -> {status, result, error, queue}
_jobs: dict[str, dict] = {}


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/upload", methods=["POST"])
def upload_csv():
    """Accept a Letterboxd CSV or ZIP upload and start processing."""
    f = request.files.get("file")
    if not f or not f.filename:
        return jsonify(error="No file uploaded."), 400

    filename = f.filename.lower()
    try:
        if filename.endswith(".zip"):
            films = parse_letterboxd_zip(f.stream)
        elif filename.endswith(".csv"):
            films = parse_watched_csv(f.stream)
        else:
            return jsonify(error="Please upload a .csv or .zip file."), 400
    except ValueError as e:
        return jsonify(error=str(e)), 400

    if not films:
        return jsonify(error="No watched films found in the uploaded file."), 400

    job_id = _start_aggregation_job(films)
    return jsonify(job_id=job_id, total_films=len(films))


@app.route("/api/scrape", methods=["POST"])
def scrape_username():
    """Accept a Letterboxd username and start processing."""
    data = request.get_json(silent=True) or {}
    username = data.get("username", "").strip()
    if not username:
        return jsonify(error="Please provide a Letterboxd username."), 400

    try:
        films = scrape_user_films(username)
    except Exception as e:
        return jsonify(error=f"Could not scrape user '{username}': {e}"), 400

    if not films:
        return jsonify(error=f"No watched films found for user '{username}'."), 400

    job_id = _start_aggregation_job(films)
    return jsonify(job_id=job_id, total_films=len(films))


@app.route("/api/progress/<job_id>")
def job_progress(job_id):
    """SSE stream that sends progress events and the final result."""
    job = _jobs.get(job_id)
    if not job:
        return jsonify(error="Unknown job ID."), 404

    def event_stream():
        q = job["queue"]
        while True:
            try:
                msg = q.get(timeout=60)
            except queue.Empty:
                yield "event: ping\ndata: {}\n\n"
                continue

            yield f"data: {json.dumps(msg)}\n\n"

            if msg.get("type") in ("done", "error"):
                break

    return Response(event_stream(), mimetype="text/event-stream")


def _start_aggregation_job(films: list[dict]) -> str:
    """Spin up a background thread to aggregate countries and stream progress."""
    job_id = uuid.uuid4().hex[:12]
    q: queue.Queue = queue.Queue()
    _jobs[job_id] = {"queue": q}

    def run():
        def on_progress(current, total, title):
            q.put({
                "type": "progress",
                "current": current,
                "total": total,
                "title": title,
            })

        try:
            result = aggregate_countries(films, progress_callback=on_progress)
            q.put({"type": "done", "data": result})
        except Exception as e:
            q.put({"type": "error", "error": str(e)})

    threading.Thread(target=run, daemon=True).start()
    return job_id


if __name__ == "__main__":
    app.run(debug=True, threaded=True)
