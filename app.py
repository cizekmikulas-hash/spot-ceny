import requests
import pytz
from datetime import datetime
from flask import Flask, render_template_string

app = Flask(__name__)

URL = "https://api.electree.cz/859182400102993847/prices"

DISTRIBUCE_NT = 0.78
DISTRIBUCE_VT = 2.78
DPH = 1.21

DNY_TYDNE = ["Pondělí", "Úterý", "Středa", "Čtvrtek", "Pátek", "Sobota", "Neděle"]

def get_distribuce(hour):
    if 4 <= hour < 8 or 15 <= hour < 19:
        return DISTRIBUCE_NT
    return DISTRIBUCE_VT

def get_color(value, min_val, max_val):
    if max_val == min_val:
        ratio = 0.5
    else:
        ratio = (value - min_val) / (max_val - min_val)
    r = int(255 * ratio)
    g = int(255 * (1 - ratio))
    return f"rgb({r}, {g}, 80)"

@app.route("/")
def home():
    response = requests.get(URL)
    data = response.json()

    tz = pytz.timezone("Europe/Prague")
    now = datetime.now(tz).replace(tzinfo=None)
    current_hour = now.hour

    # předvýpočet min/max pro celou škálu
    all_totals = []
    for item in data:
        dt = datetime.strptime(item["timeLocalStart"], "%Y-%m-%d, %H:%M:%S")
        spot = round(item["priceCZK"] / 1000, 2)
        total = round((spot + get_distribuce(dt.hour)) * DPH, 2)
        all_totals.append(total)
    min_price = min(all_totals)
    max_price = max(all_totals)

    hours = []
    prices_spot = []
    prices_total = []
    day_markers = []
    day_labels = []
    table_data = []

    current_date = None
    current_hour_index = 0

    for i, item in enumerate(data):
        dt = datetime.strptime(item["timeLocalStart"], "%Y-%m-%d, %H:%M:%S")
        time = dt.strftime("%H:%M")
        spot = round(item["priceCZK"] / 1000, 2)
        distribuce = get_distribuce(dt.hour)
        total = round((spot + distribuce) * DPH, 2)
        is_current = (dt.date() == now.date() and dt.hour == current_hour)
        is_nt = (4 <= dt.hour < 8 or 15 <= dt.hour < 19)
        color = get_color(total, min_price, max_price)

        if is_current:
            current_hour_index = i

        date_str = dt.date()
        if date_str != current_date:
            current_date = date_str
            day_name = DNY_TYDNE[dt.weekday()]
            day_label = f"{day_name} {dt.strftime('%d.%m.%Y')}"
            day_markers.append(i)
            day_labels.append(day_label)

        if dt.date() > now.date() or (dt.date() == now.date() and dt.hour >= current_hour):
            if not table_data or table_data[-1].get("day_label") != day_label:
                table_data.append({"type": "header", "label": day_label, "day_label": day_label})
            table_data.append({
                "type": "row",
                "time": time,
                "total": total,
                "is_current": is_current,
                "is_nt": is_nt,
                "day_label": day_label,
                "color": color
            })

        hours.append(time)
        prices_spot.append(spot)
        prices_total.append(total)

    return render_template_string("""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>Spotové ceny</title>
        <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
        <script src="https://cdn.jsdelivr.net/npm/chartjs-plugin-annotation@3"></script>
        <style>
            body { font-family: Arial, sans-serif; text-align: center; background: #f5f5f5; margin: 0; padding: 20px; }
            h1 { color: #333; }

            canvas {
                max-width: 95%;
                margin: 20px auto;
                background: white;
                border-radius: 8px;
                padding: 10px;
            }

            .table-wrapper {
                max-width: 500px;
                margin: 30px auto;
                background: white;
                border-radius: 8px;
                overflow: hidden;
                box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            }

            table {
                width: 100%;
                border-collapse: collapse;
            }

            th {
                background: #333;
                color: white;
                padding: 12px;
                font-size: 14px;
            }

            td {
                padding: 10px 16px;
                font-size: 14px;
                border-bottom: 1px solid rgba(0,0,0,0.07);
                color: #222;
            }

            tr:last-child td { border-bottom: none; }

            .day-header td {
                background: #2a7a7a !important;
                color: white;
                font-weight: bold;
                font-size: 14px;
                text-align: left;
                padding: 10px 16px;
            }

            .current-row td {
                font-weight: bold;
                border-top: 2px solid #f0b400;
                border-bottom: 2px solid #f0b400;
            }

            .current-row td:first-child::before {
                content: "▶ ";
            }
        </style>
    </head>
    <body>
        <h1>Spotové ceny elektřiny (Kč/kWh)</h1>

        <canvas id="myChart" width="800" height="400"></canvas>

        <div class="table-wrapper">
            <table>
                <thead>
                    <tr>
                        <th>Hodina</th>
                        <th>Cena vč. distribuce a DPH</th>
                    </tr>
                </thead>
                <tbody>
                    {% for row in table_data %}
                        {% if row.type == "header" %}
                            <tr class="day-header">
                                <td colspan="2">{{ row.label }}</td>
                            </tr>
                        {% else %}
                            <tr class="{{ 'current-row' if row.is_current else '' }}"
                                style="background:{{ row.color }}">
                                <td>{{ row.time }}</td>
                                <td>{{ "%.2f"|format(row.total) }} Kč/kWh</td>
                            </tr>
                        {% endif %}
                    {% endfor %}
                </tbody>
            </table>
        </div>

        <script>
            const hours = {{ hours | tojson }};
            const prices_spot = {{ prices_spot | tojson }};
            const prices_total = {{ prices_total | tojson }};
            const day_markers = {{ day_markers | tojson }};
            const day_labels = {{ day_labels | tojson }};
            const current_hour_index = {{ current_hour_index }};

            const annotations = {};

            day_markers.forEach((idx, i) => {
                annotations['line' + i] = {
                    type: 'line',
                    xMin: idx,
                    xMax: idx,
                    borderColor: 'rgba(100, 100, 100, 0.6)',
                    borderWidth: 2,
                    borderDash: [6, 3],
                    label: {
                        display: true,
                        content: day_labels[i],
                        position: 'start',
                        backgroundColor: 'rgba(50, 50, 50, 0.75)',
                        color: 'white',
                        font: { size: 12, weight: 'bold' },
                        padding: 6,
                        borderRadius: 4
                    }
                };
            });

            annotations['current'] = {
                type: 'line',
                xMin: current_hour_index,
                xMax: current_hour_index,
                borderColor: 'rgba(255, 180, 0, 0.9)',
                borderWidth: 2,
                borderDash: [4, 4],
                label: {
                    display: true,
                    content: 'Nyní',
                    position: 'end',
                    backgroundColor: 'rgba(255, 180, 0, 0.85)',
                    color: '#333',
                    font: { size: 12, weight: 'bold' },
                    padding: 6,
                    borderRadius: 4
                }
            };

            const ctx = document.getElementById('myChart').getContext('2d');

            new Chart(ctx, {
                type: 'line',
                data: {
                    labels: hours,
                    datasets: [
                        {
                            label: 'Spot (Kč/kWh)',
                            data: prices_spot,
                            borderColor: 'rgba(75, 192, 192, 1)',
                            backgroundColor: 'rgba(75, 192, 192, 0.1)',
                            borderWidth: 2,
                            fill: true,
                            tension: 0.3
                        },
                        {
                            label: 'Celkem vč. distribuce a DPH (Kč/kWh)',
                            data: prices_total,
                            borderColor: 'rgba(255, 99, 132, 1)',
                            backgroundColor: 'rgba(255, 99, 132, 0.1)',
                            borderWidth: 2,
                            fill: true,
                            tension: 0.3
                        }
                    ]
                },
                options: {
                    responsive: true,
                    plugins: {
                        legend: { position: 'top' },
                        annotation: { annotations },
                        tooltip: {
                            callbacks: {
                                title: function(context) {
                                    const idx = context[0].dataIndex;
                                    let dayLabel = day_labels[0];
                                    for (let i = 0; i < day_markers.length; i++) {
                                        if (idx >= day_markers[i]) dayLabel = day_labels[i];
                                    }
                                    return dayLabel + ' – ' + hours[idx];
                                },
                                label: function(context) {
                                    return context.dataset.label + ': ' + context.parsed.y.toFixed(2) + ' Kč/kWh';
                                }
                            }
                        }
                    },
                    scales: {
                        y: {
                            beginAtZero: true,
                            title: { display: true, text: 'Kč/kWh' }
                        },
                        x: {
                            title: { display: true, text: 'Hodina' }
                        }
                    }
                }
            });
        </script>
    </body>
    </html>
    """, hours=hours, prices_spot=prices_spot, prices_total=prices_total,
         day_markers=day_markers, day_labels=day_labels,
         table_data=table_data, current_hour_index=current_hour_index)

if __name__ == "__main__":
    app.run(debug=True)