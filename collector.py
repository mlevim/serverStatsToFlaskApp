#!/usr/bin/env python3

import sqlite3
import subprocess
import time
from datetime import datetime

DB_FILE = "cluster_stats.db"

NODES = [
    "node01",
    "node02",
    "node03"
]


def init_db():

    conn = sqlite3.connect(DB_FILE)

    conn.execute("""
    CREATE TABLE IF NOT EXISTS node_stats(
        timestamp TEXT,
        node TEXT,
        cpu_percent REAL,
        mem_percent REAL,
        load1 REAL,
        load5 REAL,
        load15 REAL
    )
    """)

    conn.commit()
    conn.close()


def get_cpu_sample(node):

    cmd = """
grep '^cpu ' /proc/stat
"""

    result = subprocess.run(
        ["ssh", node, cmd],
        capture_output=True,
        text=True
    )

    fields = list(map(int,
                      result.stdout.split()[1:]))

    idle = fields[3]

    total = sum(fields)

    return idle, total


def get_cpu_percent(node):

    idle1, total1 = get_cpu_sample(node)

    time.sleep(1)

    idle2, total2 = get_cpu_sample(node)

    delta_idle = idle2 - idle1
    delta_total = total2 - total1

    return 100.0 * (
        delta_total - delta_idle
    ) / delta_total


def get_memory_percent(node):

    cmd = """
cat /proc/meminfo
"""

    result = subprocess.run(
        ["ssh", node, cmd],
        capture_output=True,
        text=True
    )

    mem_total = 0
    mem_available = 0

    for line in result.stdout.splitlines():

        if line.startswith("MemTotal"):

            mem_total = int(line.split()[1])

        elif line.startswith("MemAvailable"):

            mem_available = int(line.split()[1])

    used = mem_total - mem_available

    return 100.0 * used / mem_total


def get_load(node):

    cmd = """
cat /proc/loadavg
"""

    result = subprocess.run(
        ["ssh", node, cmd],
        capture_output=True,
        text=True
    )

    load1, load5, load15 = map(
        float,
        result.stdout.split()[:3]
    )

    return load1, load5, load15


def collect_node(node):

    cpu = get_cpu_percent(node)

    mem = get_memory_percent(node)

    load1, load5, load15 = get_load(node)

    return (
        cpu,
        mem,
        load1,
        load5,
        load15
    )


def store(node, stats):

    conn = sqlite3.connect(DB_FILE)

    conn.execute("""
    INSERT INTO node_stats
    VALUES(?,?,?,?,?,?,?)
    """, (
        datetime.now().isoformat(),
        node,
        *stats
    ))

    conn.commit()
    conn.close()


def main():

    init_db()

    for node in NODES:

        try:

            stats = collect_node(node)

            store(node, stats)

            print(node, stats)

        except Exception as e:

            print(node, e)


if __name__ == "__main__":
    main()