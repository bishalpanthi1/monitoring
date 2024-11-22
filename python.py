from flask import Flask, render_template_string
import requests

app = Flask(__name__)

# Function to fetch the metrics from the URL
def get_metrics():
    url = "http://***:****metrics"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            return response.text, response.headers.get('Content-Type', 'Unknown')
        else:
            return f"Error: Unable to fetch metrics, status code {response.status_code}", None
    except requests.exceptions.RequestException as e:
        return f"Error: {e}", None

# Function to parse and convert metrics
def parse_metrics(raw_metrics):
    parsed_data = []
    for line in raw_metrics.splitlines():
        # Skip lines that are comments, empty, or contain Content-Type header
        if line.startswith('#') or not line.strip() or "Content-Type" in line:
            continue
        # Assume each metric line has a format: metric_name{labels} value
        parts = line.split(' ', 1)
        if len(parts) == 2:
            name_and_labels, value = parts
            # Convert the value to GB if it's numeric, or append 'GB' otherwise
            try:
                value_in_bytes = float(value)
                value_in_gb = value_in_bytes / (1024 ** 3)  # Convert bytes to GB
                formatted_value = f"{value_in_gb:.2f} GB"  # Format to 2 decimal places
            except ValueError:
                formatted_value = f"{value} GB"  # If not numeric, append 'GB' directly
            parsed_data.append({
                'metric': name_and_labels,
                'value': formatted_value,
                'status': 'OK'  # Add the status column with "OK"
            })
    return parsed_data

@app.route('/')
def index():
    # Fetch and parse metrics
    raw_metrics, content_type = get_metrics()
    if "Error" in raw_metrics:  # Handle errors gracefully
        return raw_metrics
    metrics = parse_metrics(raw_metrics)

    # Render the metrics in a tabular format
    return render_template_string("""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Metrics Table</title>
            <style>
                body { font-family: Arial, sans-serif; padding: 20px; }
                table { width: 100%; border-collapse: collapse; margin-top: 20px; }
                th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
                th { background-color: #f4f4f4; color: #333; }
                h1 { color: #333; }
            </style>
        </head>
        <body>
            <h1>PreProd Backup</h1>
            <p><strong>Content-Type:</strong> {{ content_type }}</p> <!-- Display Content-Type header -->
            <table>
                <thead>
                    <tr>
                        <th>Metric</th>
                        <th>Value</th>
                        <th>Status</th>
                    </tr>
                </thead>
                <tbody>
                    {% for metric in metrics %}
                    <tr>
                        <td>{{ metric.metric }}</td>
                        <td>{{ metric.value }}</td>
                        <td>{{ metric.status }}</td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </body>
        </html>
    """, metrics=metrics, content_type=content_type)

@app.route('/metrics')
def metrics():
    # Endpoint to provide raw metrics data
    raw_metrics, _ = get_metrics()
    return raw_metrics

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8080)