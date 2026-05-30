from flask import Flask
from flask import jsonify

import sqlite3

DB_FILE = "cluster_stats.db"

app = Flask(__name__)

@app.route("/api/current")
def current():

    conn = sqlite3.connect(DB_FILE)

    query = """
    SELECT *
    FROM node_stats
    WHERE (node,timestamp) IN
    (
        SELECT node,
               MAX(timestamp)
        FROM node_stats
        GROUP BY node
    )
    """

    rows = conn.execute(query).fetchall()

    conn.close()

    return jsonify([
        {
            "timestamp": r[0],
            "node": r[1],
            "cpu_percent": r[2],
            "mem_percent": r[3],
            "load1": r[4],
            "load5": r[5],
            "load15": r[6]
        }
        for r in rows
    ])

@app.route("/api/history/<node>")
def history(node):

    conn = sqlite3.connect(DB_FILE)

    rows = conn.execute("""
    SELECT *
    FROM node_stats
    WHERE node=?
    ORDER BY timestamp
    """, (node,)).fetchall()

    conn.close()

    return jsonify([
        {
            "timestamp": r[0],
            "cpu_percent": r[2],
            "mem_percent": r[3]
        }
        for r in rows
    ])

if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=5000
    )