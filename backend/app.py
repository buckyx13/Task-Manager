import os
import psycopg2
import psycopg2.extras
from flask import Flask, jsonify, request

app = Flask(__name__)


def get_conn():
    return psycopg2.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=os.getenv("DB_PORT", "5432"),
        user=os.environ["DB_USER"],
        dbname=os.environ["DB_NAME"],
        password=os.environ["DB_PASSWORD"],
        # dbname=os.getenv("DB_NAME", "taskdb"),
        # user=os.getenv("DB_USER", "taskuser"),
        # password=os.getenv("DB_PASSWORD", "taskpass"),
    )


@app.get("/health")
def health():
    return jsonify(status="ok")


@app.get("/api/tasks")
def list_tasks():
    with get_conn() as conn, conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute("SELECT id, title, done, created_at FROM tasks ORDER BY id DESC")
        return jsonify(cur.fetchall())


@app.post("/api/tasks")
def add_task():
    title = (request.get_json(silent=True) or {}).get("title", "").strip()
    if not title:
        return jsonify(error="title is required"), 400
    with get_conn() as conn, conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute("INSERT INTO tasks (title) VALUES (%s) RETURNING id, title, done", (title,))
        return jsonify(cur.fetchone()), 201


@app.put("/api/tasks/<int:task_id>/toggle")
def toggle_task(task_id):
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute("UPDATE tasks SET done = NOT done WHERE id = %s", (task_id,))
    return jsonify(status="updated")


@app.delete("/api/tasks/<int:task_id>")
def delete_task(task_id):
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute("DELETE FROM tasks WHERE id = %s", (task_id,))
    return jsonify(status="deleted")


if __name__ == "__main__":
    app.run(
        host=os.getenv("HOST", "127.0.0.1"),
        port=int(os.getenv("PORT", "5000")),
    )
