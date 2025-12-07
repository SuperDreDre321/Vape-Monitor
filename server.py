from flask import Flask, request, jsonify, render_template_string
from datetime import datetime

app = Flask(__name__)

# In-memory storage for now
data_points = []  # each: {"time": "...", "mq_raw": 0.123}
MAX_POINTS = 3600  # keep last 3600 seconds (~1 hour)

HTML_PAGE = """
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <title>MQ Live Monitor</title>
  <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
  <style>
    body { font-family: sans-serif; margin: 20px; }
    #container { max-width: 900px; margin: 0 auto; }
    canvas { width: 100% !important; height: 400px !important; }
  </style>
</head>
<body>
<div id="container">
  <h2>MQ_raw Live Graph</h2>
  <p>Live data pushed from Raspberry Pi</p>
  <canvas id="mqChart"></canvas>
</div>

<script>
  let labels = [];
  let values = [];

  const ctx = document.getElementById('mqChart').getContext('2d');
  const mqChart = new Chart(ctx, {
    type: 'line',
    data: {
      labels: labels,
      datasets: [{
        label: 'MQ_raw',
        data: values,
        borderWidth: 2,
        pointRadius: 0,
        fill: false,
      }]
    },
    options: {
      animation: false,
      scales: {
        y: {
          suggestedMin: 0,
          suggestedMax: 1
        }
      }
    }
  });

  async function fetchData() {
    const resp = await fetch('/data');
    const json = await resp.json();

    labels.length = 0;
    values.length = 0;

    json.forEach(p => {
      labels.push(p.time);
      values.push(p.mq_raw);
    });

    mqChart.update();
  }

  // Fetch every second
  setInterval(fetchData, 1000);
  fetchData();
</script>
</body>
</html>
"""

@app.route("/")
def index():
    return render_template_string(HTML_PAGE)


@app.route("/data")
def get_data():
    return jsonify(data_points)


@app.route("/ingest", methods=["POST"])
def ingest():
    # Expect JSON: {"mq_raw": float, "time": optional string}
    payload = request.get_json(silent=True) or {}

    mq_raw = payload.get("mq_raw")
    t = payload.get("time")

    if mq_raw is None:
        return jsonify({"error": "mq_raw required"}), 400

    if t is None:
        t = datetime.utcnow().strftime("%H:%M:%S")

    data_points.append({"time": t, "mq_raw": float(mq_raw)})

    # Limit memory
    if len(data_points) > MAX_POINTS:
        data_points.pop(0)

    return jsonify({"status": "ok"}), 200


if __name__ == "__main__":
    app.run()
