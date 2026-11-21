import os
import requests
from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:5000")


@app.get("/")
def index():
    try:
        tasks = requests.get(f"{BACKEND_URL}/api/tasks", timeout=5).json()
        error = None
    except requests.RequestException:
        tasks, error = [], "Cannot reach the backend."
    return render_template("index.html", tasks=tasks, error=error)


@app.post("/add")
def add():
    title = request.form.get("title", "")
    requests.post(f"{BACKEND_URL}/api/tasks", json={"title": title}, timeout=5)
    return redirect(url_for("index"))


@app.post("/toggle/<int:task_id>")
def toggle(task_id):
    requests.put(f"{BACKEND_URL}/api/tasks/{task_id}/toggle", timeout=5)
    return redirect(url_for("index"))


@app.post("/delete/<int:task_id>")
def delete(task_id):
    requests.delete(f"{BACKEND_URL}/api/tasks/{task_id}", timeout=5)
    return redirect(url_for("index"))


if __name__ == "__main__":
    app.run(
        host=os.getenv("HOST", "127.0.0.1"),
        port=int(os.getenv("PORT", "8000")),
    )