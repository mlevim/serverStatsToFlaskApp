# serverStatsToFlaskApp
A simple proof-of-concept setup to collect server data stats such as CPU and Memory load, and display it in a flask-type database to generate a Grafana Dashboard. 

## Ensure SSH safe connectivity
Generate a keypair on the Grafana/collector host and install the public key on each compute node.

For example, on the Grafana node:

```bash
ssh-keygen -t ed25519
```

Will generate:

```bash
~/.ssh/id_ed25519
~/.ssh/id_ed25519.pub
```

Dedicated Monitoring User (Recommended):

```bash
#For every node:
ssh node01 hostname
useradd monitor 
#Install the same public key in:
/home/monitor/.ssh/authorized_keys
```

Then in the Python code, modify to the `monitor` account:

```Python
subprocess.run(
    ["ssh", "monitor@node01", cmd]
)
```

## Organization:

Here are the key components of the setup:
1. A Python collector script running from the controller/login node every time window (default 15 minutes) via cron.
2. The Python collector is doing the following:
    1. SSH to each compute node (or desired list of nodes)
    2. Collect:
        1. CPU utilization %
        2. Memory utilization %
        3. Load average
        4. Optional: number of running jobs, network traffic, disk usage.
    3. Stores the results in a local SQLite database.
    4. Exposes the data through a Flask API.
3. Using the Grafana Infinity datasource to get the utilization data and display via the different dashboard panels.

### Architecture

```
cron
  |
  v
collector.py
  |
  +--> ssh node01
  +--> ssh node02
  +--> ssh node03
  |
  v
SQLite DB
(cluster_stats.db)
  |
  v
Flask API
  |
  v
Grafana Infinity
```

### Data Model

For this application, a single table is created:

```SQL
CREATE TABLE node_stats (
    timestamp      DATETIME,
    node           TEXT,
    cpu_percent    REAL,
    mem_percent    REAL,
    load1          REAL,
    load5          REAL,
    load15         REAL
);
```

### Collecting CPU and Memory Usage - Collector script

The monitoring is performed by the collector script.

The commands used (might be changed in the future) to collect data from each node:

```bash
#CPU stats collection
cat /proc/loadavg 
#Memory stats collection
free -m
```

However, this is a simplified version. For real CPU utilization there's a need to sample `/proc/stat` twice to get the actual utilization over the interval:

```
CPU% =
(delta_total - delta_idle)
/
delta_total
```

What data could be collected:

```txt
| Metric   | Source        |
| -------- | ------------- |
| CPU %    | /proc/stat    |
| Memory % | /proc/meminfo |
| Load1    | /proc/loadavg |
| Load5    | /proc/loadavg |
| Load15   | /proc/loadavg |
```

Then, it is possible to set up a cron job every 15 minutes:

```bah
*/15 * * * * /usr/bin/python3 collector.py
```

### Flask API

The script `flask-app.py` is a Python script that uses Flask to generate a lightweight web server that reads the database and returns JSON, which then can be read by Grafana.

How to start the server:

```bash
python3 flask-app.py
```

The URL for current data will be available at:
`http://grafana-server:5000/api/current`
The URL for historical data will be available at:
`http://grafana-server:5000/api/history/<node>`

## Grafana Infinity Configuration

Open the Grafana Server and connect the the Infinity Datasource URL: `http://grafana-server:5000/api/current`

Next, create a new dashboard with a few panels. For example, create Gauges - use fields `cpu_percent`, group by `node`.

