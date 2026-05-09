"""
GreenDevOps Build Optimizer — Comparison Dashboard
Flask backend with SQLite storage for pipeline metrics.
"""

import json
import sqlite3
import os
from datetime import datetime
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

DB_PATH = os.environ.get("DASHBOARD_DB", os.path.join(os.path.dirname(__file__), "dashboard.db"))

# ── Database helpers ──────────────────────────────────────────────────────────

def get_db():
    """Get a database connection with row factory."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def init_db():
    """Create tables if they don't exist."""
    conn = get_db()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS builds (
            id                  INTEGER PRIMARY KEY AUTOINCREMENT,
            job_name            TEXT NOT NULL,
            build_number        INTEGER NOT NULL,
            pipeline_type       TEXT NOT NULL DEFAULT 'unknown',
            commit_sha          TEXT,
            commit_message      TEXT,
            status              TEXT DEFAULT 'UNKNOWN',
            total_duration_s    REAL,
            build_duration_s    REAL,
            test_duration_s     REAL,
            docker_duration_s   REAL,
            deploy_duration_s   REAL,
            optimizer_duration_s REAL,
            modules_built       TEXT,
            modules_tested      TEXT,
            tests_executed      INTEGER DEFAULT 0,
            tests_skipped       INTEGER DEFAULT 0,
            affected_modules    TEXT,
            module_details      TEXT,
            build_command       TEXT,
            test_command        TEXT,
            created_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(job_name, build_number)
        );
    """)
    conn.commit()
    conn.close()


def row_to_dict(row):
    """Convert a sqlite3.Row to a plain dict."""
    return dict(row) if row else None


# ── API Routes ────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    """Serve the dashboard frontend."""
    return render_template("index.html")


@app.route("/api/builds", methods=["POST"])
def record_build():
    """Record a new build from a Jenkins pipeline."""
    data = request.get_json(force=True)
    if not data:
        return jsonify({"error": "No JSON body"}), 400

    required = ["job_name", "build_number", "pipeline_type"]
    for field in required:
        if field not in data:
            return jsonify({"error": f"Missing required field: {field}"}), 400

    conn = get_db()
    try:
        conn.execute("""
            INSERT INTO builds (
                job_name, build_number, pipeline_type,
                commit_sha, commit_message, status,
                total_duration_s, build_duration_s, test_duration_s,
                docker_duration_s, deploy_duration_s, optimizer_duration_s,
                modules_built, modules_tested,
                tests_executed, tests_skipped,
                affected_modules, module_details, build_command, test_command
            ) VALUES (
                :job_name, :build_number, :pipeline_type,
                :commit_sha, :commit_message, :status,
                :total_duration_s, :build_duration_s, :test_duration_s,
                :docker_duration_s, :deploy_duration_s, :optimizer_duration_s,
                :modules_built, :modules_tested,
                :tests_executed, :tests_skipped,
                :affected_modules, :module_details, :build_command, :test_command
            )
        """, {
            "job_name":             data["job_name"],
            "build_number":        int(data["build_number"]),
            "pipeline_type":        data["pipeline_type"],
            "commit_sha":           data.get("commit_sha"),
            "commit_message":       data.get("commit_message"),
            "status":               data.get("status", "UNKNOWN"),
            "total_duration_s":     data.get("total_duration_s"),
            "build_duration_s":     data.get("build_duration_s"),
            "test_duration_s":      data.get("test_duration_s"),
            "docker_duration_s":    data.get("docker_duration_s"),
            "deploy_duration_s":    data.get("deploy_duration_s"),
            "optimizer_duration_s": data.get("optimizer_duration_s"),
            "modules_built":        data.get("modules_built"),
            "modules_tested":       data.get("modules_tested"),
            "tests_executed":       data.get("tests_executed", 0),
            "tests_skipped":        data.get("tests_skipped", 0),
            "affected_modules":     data.get("affected_modules"),
            "module_details":       data.get("module_details"),
            "build_command":        data.get("build_command"),
            "test_command":         data.get("test_command"),
        })
        conn.commit()
        return jsonify({"ok": True, "message": "Build recorded"}), 201
    except sqlite3.IntegrityError:
        # Update existing record (e.g., when end data arrives)
        conn.execute("""
            UPDATE builds SET
                pipeline_type       = :pipeline_type,
                commit_sha          = COALESCE(:commit_sha, commit_sha),
                commit_message      = COALESCE(:commit_message, commit_message),
                status              = COALESCE(:status, status),
                total_duration_s    = COALESCE(:total_duration_s, total_duration_s),
                build_duration_s    = COALESCE(:build_duration_s, build_duration_s),
                test_duration_s     = COALESCE(:test_duration_s, test_duration_s),
                docker_duration_s   = COALESCE(:docker_duration_s, docker_duration_s),
                deploy_duration_s   = COALESCE(:deploy_duration_s, deploy_duration_s),
                optimizer_duration_s = COALESCE(:optimizer_duration_s, optimizer_duration_s),
                modules_built       = COALESCE(:modules_built, modules_built),
                modules_tested      = COALESCE(:modules_tested, modules_tested),
                tests_executed      = COALESCE(:tests_executed, tests_executed),
                tests_skipped       = COALESCE(:tests_skipped, tests_skipped),
                affected_modules    = COALESCE(:affected_modules, affected_modules),
                module_details      = COALESCE(:module_details, module_details),
                build_command       = COALESCE(:build_command, build_command),
                test_command        = COALESCE(:test_command, test_command)
            WHERE job_name = :job_name AND build_number = :build_number
        """, {
            "job_name":             data["job_name"],
            "build_number":        int(data["build_number"]),
            "pipeline_type":        data["pipeline_type"],
            "commit_sha":           data.get("commit_sha"),
            "commit_message":       data.get("commit_message"),
            "status":               data.get("status"),
            "total_duration_s":     data.get("total_duration_s"),
            "build_duration_s":     data.get("build_duration_s"),
            "test_duration_s":      data.get("test_duration_s"),
            "docker_duration_s":    data.get("docker_duration_s"),
            "deploy_duration_s":    data.get("deploy_duration_s"),
            "optimizer_duration_s": data.get("optimizer_duration_s"),
            "modules_built":        data.get("modules_built"),
            "modules_tested":       data.get("modules_tested"),
            "tests_executed":       data.get("tests_executed"),
            "tests_skipped":        data.get("tests_skipped"),
            "affected_modules":     data.get("affected_modules"),
            "module_details":       data.get("module_details"),
            "build_command":        data.get("build_command"),
            "test_command":         data.get("test_command"),
        })
        conn.commit()
        return jsonify({"ok": True, "message": "Build updated"}), 200
    finally:
        conn.close()


@app.route("/api/builds", methods=["GET"])
def list_builds():
    """List builds with optional filters."""
    pipeline_type = request.args.get("pipeline")
    limit = int(request.args.get("limit", 50))

    conn = get_db()
    if pipeline_type:
        rows = conn.execute(
            "SELECT * FROM builds WHERE pipeline_type = ? ORDER BY created_at DESC LIMIT ?",
            (pipeline_type, limit)
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT * FROM builds ORDER BY created_at DESC LIMIT ?",
            (limit,)
        ).fetchall()
    conn.close()

    return jsonify([row_to_dict(r) for r in rows])


@app.route("/api/comparison", methods=["GET"])
def comparison():
    """
    Return paired builds for comparison.
    Pairs optimized and unoptimized builds by proximity (build order).
    """
    limit = int(request.args.get("limit", 20))
    conn = get_db()

    optimized = conn.execute(
        "SELECT * FROM builds WHERE pipeline_type = 'optimized' ORDER BY created_at DESC LIMIT ?",
        (limit,)
    ).fetchall()

    unoptimized = conn.execute(
        "SELECT * FROM builds WHERE pipeline_type = 'unoptimized' ORDER BY created_at DESC LIMIT ?",
        (limit,)
    ).fetchall()
    conn.close()

    return jsonify({
        "optimized": [row_to_dict(r) for r in optimized],
        "unoptimized": [row_to_dict(r) for r in unoptimized],
    })


@app.route("/api/stats", methods=["GET"])
def stats():
    """Return aggregate statistics for the dashboard summary cards."""
    conn = get_db()

    opt = conn.execute("""
        SELECT
            COUNT(*)                    AS total_builds,
            AVG(total_duration_s)       AS avg_total_s,
            AVG(build_duration_s)       AS avg_build_s,
            AVG(test_duration_s)        AS avg_test_s,
            SUM(tests_executed)         AS total_tests_run,
            SUM(tests_skipped)          AS total_tests_skipped
        FROM builds WHERE pipeline_type = 'optimized' AND status = 'SUCCESS'
    """).fetchone()

    unopt = conn.execute("""
        SELECT
            COUNT(*)                    AS total_builds,
            AVG(total_duration_s)       AS avg_total_s,
            AVG(build_duration_s)       AS avg_build_s,
            AVG(test_duration_s)        AS avg_test_s,
            SUM(tests_executed)         AS total_tests_run,
            SUM(tests_skipped)          AS total_tests_skipped
        FROM builds WHERE pipeline_type = 'unoptimized' AND status = 'SUCCESS'
    """).fetchone()
    conn.close()

    opt_d = row_to_dict(opt)
    unopt_d = row_to_dict(unopt)

    # Calculate savings
    time_saved_pct = 0
    if unopt_d["avg_total_s"] and opt_d["avg_total_s"] and unopt_d["avg_total_s"] > 0:
        time_saved_pct = round(
            (1 - opt_d["avg_total_s"] / unopt_d["avg_total_s"]) * 100, 1
        )

    # Simple energy estimation: CI server ~65W TDP, convert seconds to kWh
    WATTS = 65
    total_seconds_saved = 0
    if unopt_d["avg_total_s"] and opt_d["avg_total_s"]:
        avg_saved_per_build = unopt_d["avg_total_s"] - opt_d["avg_total_s"]
        total_seconds_saved = avg_saved_per_build * (opt_d["total_builds"] or 0)
    energy_saved_kwh = round((total_seconds_saved * WATTS) / 3_600_000, 4)

    return jsonify({
        "optimized": opt_d,
        "unoptimized": unopt_d,
        "time_saved_pct": time_saved_pct,
        "total_tests_skipped": opt_d.get("total_tests_skipped") or 0,
        "energy_saved_kwh": energy_saved_kwh,
        "total_builds": (opt_d["total_builds"] or 0) + (unopt_d["total_builds"] or 0),
    })


# ── Startup ───────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    init_db()
    port = int(os.environ.get("PORT", 5050))
    print(f"GreenDevOps Dashboard running on http://0.0.0.0:{port}")
    app.run(host="0.0.0.0", port=port, debug=True)
