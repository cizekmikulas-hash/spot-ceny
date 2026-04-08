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

def price_color(ratio):
    """Map ratio 0..1 to green→yellow→red hex color."""
    if ratio < 0.5:
        r = int(255 * ratio * 2)
        g = 200
    else:
        r = 220
        g = int(200 * (1 - (ratio - 0.5) * 2))
    return f"rgb({r},{g},70)"

@app.route("/")
def home():
    response = requests.get(URL)
    data = response.json()

    tz = pytz.timezone("Europe/Prague")
    now = datetime.now(tz).replace(tzinfo=None)
    current_hour = now.hour

    # Pre-compute totals for all items
    all_items = []
    for item in data:
        dt = datetime.strptime(item["timeLocalStart"], "%Y-%m-%d, %H:%M:%S")
        spot = round(item["priceCZK"] / 1000, 2)
        distribuce = get_distribuce(dt.hour)
        total = round((spot + distribuce) * DPH, 2)
        all_items.append((dt, spot, total))

    all_totals = [x[2] for x in all_items]
    min_price = min(all_totals)
    max_price = max(all_totals)

    # Today's stats
    today_items = [(dt, spot, total) for dt, spot, total in all_items if dt.date() == now.date()]
    today_totals = [(dt, total) for dt, _, total in today_items]

    current_total = next((total for dt, total in today_totals if dt.hour == current_hour), None)
    current_time_str = f"{current_hour:02d}:00"

    cheapest_dt, cheapest_price = min(today_totals, key=lambda x: x[1]) if today_totals else (None, None)
    priciest_dt, priciest_price = max(today_totals, key=lambda x: x[1]) if today_totals else (None, None)

    hours = []
    prices_spot = []
    prices_total = []
    day_markers = []
    day_labels = []
    table_data = []

    current_date = None
    current_hour_index = 0
    day_label = ""

    for i, (dt, spot, total) in enumerate(all_items):
        time = dt.strftime("%H:%M")
        is_current = (dt.date() == now.date() and dt.hour == current_hour)
        is_nt = (4 <= dt.hour < 8 or 15 <= dt.hour < 19)
        ratio = (total - min_price) / (max_price - min_price) if max_price != min_price else 0.5
        bar_pct = round(ratio * 100)
        color = price_color(ratio)

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
                "color": color,
                "bar_pct": bar_pct,
            })

        hours.append(time)
        prices_spot.append(spot)
        prices_total.append(total)

    return render_template_string(TEMPLATE,
        hours=hours,
        prices_spot=prices_spot,
        prices_total=prices_total,
        day_markers=day_markers,
        day_labels=day_labels,
        table_data=table_data,
        current_hour_index=current_hour_index,
        current_total=current_total,
        current_time_str=current_time_str,
        cheapest_price=cheapest_price,
        cheapest_time=f"{cheapest_dt.strftime('%H:%M')}" if cheapest_dt else "–",
        priciest_price=priciest_price,
        priciest_time=f"{priciest_dt.strftime('%H:%M')}" if priciest_dt else "–",
    )


TEMPLATE = """<!DOCTYPE html>
<html lang="cs">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Spotové ceny elektřiny</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/chartjs-plugin-annotation@3"></script>
    <style>
        *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

        body {
            font-family: 'Inter', sans-serif;
            background: #f0f2f5;
            color: #1a1a2e;
            min-height: 100vh;
            padding: 24px 16px 40px;
        }

        .page-title {
            font-size: 13px;
            font-weight: 600;
            letter-spacing: 0.08em;
            text-transform: uppercase;
            color: #6b7280;
            text-align: center;
            margin-bottom: 20px;
        }

        .container {
            max-width: 860px;
            margin: 0 auto;
        }

        /* ── TOP CARDS ─────────────────────────────────────── */
        .cards {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 12px;
            margin-bottom: 16px;
        }

        @media (max-width: 560px) {
            .cards { grid-template-columns: 1fr; gap: 10px; }
        }

        .card {
            background: #ffffff;
            border-radius: 14px;
            padding: 18px 20px 16px;
            box-shadow: 0 1px 4px rgba(0,0,0,0.07), 0 4px 16px rgba(0,0,0,0.06);
            border-left: 4px solid #d1d5db;
            position: relative;
        }

        .card--current  { border-left-color: #1a1a2e; }
        .card--cheapest { border-left-color: #16a34a; }
        .card--priciest { border-left-color: #dc2626; }

        .card-label {
            font-size: 11px;
            font-weight: 600;
            letter-spacing: 0.07em;
            text-transform: uppercase;
            color: #9ca3af;
            margin-bottom: 8px;
        }

        .card-price {
            font-size: clamp(32px, 7vw, 48px);
            font-weight: 700;
            letter-spacing: -0.03em;
            line-height: 1;
            color: #1a1a2e;
        }

        .card--cheapest .card-price { color: #16a34a; }
        .card--priciest .card-price { color: #dc2626; }

        .card-unit {
            font-size: 13px;
            font-weight: 500;
            color: #6b7280;
            margin-top: 5px;
        }

        .card-sub {
            font-size: 12px;
            color: #9ca3af;
            margin-top: 3px;
        }

        /* ── CHART CARD ────────────────────────────────────── */
        .chart-card {
            background: #ffffff;
            border-radius: 14px;
            padding: 20px 20px 16px;
            box-shadow: 0 1px 4px rgba(0,0,0,0.07), 0 4px 16px rgba(0,0,0,0.06);
            margin-bottom: 16px;
        }

        .chart-header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 16px;
            flex-wrap: wrap;
            gap: 8px;
        }

        .chart-title {
            font-size: 15px;
            font-weight: 600;
            color: #1a1a2e;
        }

        .chart-legend {
            display: flex;
            gap: 14px;
        }

        .legend-item {
            display: flex;
            align-items: center;
            gap: 6px;
            font-size: 12px;
            color: #6b7280;
            font-weight: 500;
        }

        .legend-dot {
            width: 10px;
            height: 10px;
            border-radius: 50%;
            flex-shrink: 0;
        }

        .legend-dot--spot  { background: #60a5fa; }
        .legend-dot--total { background: #f97316; }

        .chart-wrapper {
            position: relative;
            width: 100%;
            height: 280px;
        }

        @media (max-width: 480px) {
            .chart-wrapper { height: 200px; }
        }

        /* ── TABLE CARD ────────────────────────────────────── */
        .table-card {
            background: #ffffff;
            border-radius: 14px;
            overflow: hidden;
            box-shadow: 0 1px 4px rgba(0,0,0,0.07), 0 4px 16px rgba(0,0,0,0.06);
        }

        .table-head {
            display: grid;
            grid-template-columns: 90px 1fr 110px;
            padding: 10px 20px;
            border-bottom: 1px solid #f3f4f6;
        }

        .table-head-cell {
            font-size: 11px;
            font-weight: 600;
            letter-spacing: 0.07em;
            text-transform: uppercase;
            color: #9ca3af;
        }

        .table-head-cell:last-child { text-align: right; }

        .day-header-row {
            display: flex;
            align-items: center;
            gap: 8px;
            padding: 10px 20px 8px;
            background: #f9fafb;
            border-top: 1px solid #f3f4f6;
            border-bottom: 1px solid #f3f4f6;
        }

        .day-dot {
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background: #22c55e;
            flex-shrink: 0;
        }

        .day-text {
            font-size: 12px;
            font-weight: 600;
            letter-spacing: 0.05em;
            text-transform: uppercase;
            color: #6b7280;
        }

        .price-row {
            display: grid;
            grid-template-columns: 90px 1fr 110px;
            align-items: center;
            padding: 11px 20px;
            border-bottom: 1px solid #f9fafb;
            transition: background 0.15s;
        }

        .price-row:last-child { border-bottom: none; }
        .price-row:hover { background: #fafafa; }

        .price-row--current {
            background: #fffbeb;
        }
        .price-row--current:hover { background: #fef3c7; }

        .hour-cell {
            font-size: 14px;
            font-weight: 500;
            color: #374151;
            display: flex;
            align-items: center;
            gap: 6px;
        }

        .hour-now {
            font-size: 11px;
            font-weight: 600;
            color: #f59e0b;
            letter-spacing: 0.03em;
        }

        .play-icon {
            color: #f59e0b;
            font-size: 10px;
        }

        .bar-cell {
            padding-right: 16px;
        }

        .bar-track {
            height: 6px;
            background: #f3f4f6;
            border-radius: 99px;
            overflow: hidden;
        }

        .bar-fill {
            height: 100%;
            border-radius: 99px;
            min-width: 4px;
        }

        .value-cell {
            text-align: right;
            font-size: 14px;
            font-weight: 600;
            font-variant-numeric: tabular-nums;
        }

        .value-cell--current { color: #f59e0b; }
    </style>
</head>
<body>
    <div class="container">
        <p class="page-title">Spotové ceny elektřiny</p>

        <!-- TOP CARDS -->
        <div class="cards">
            <div class="card card--current">
                <div class="card-label">Nyní &middot; {{ current_time_str }}</div>
                <div class="card-price">{{ "%.2f"|format(current_total) if current_total is not none else "–" }}</div>
                <div class="card-unit">Kč/kWh</div>
                <div class="card-sub">vč. distribuce a DPH</div>
            </div>

            <div class="card card--cheapest">
                <div class="card-label">Nejlevnější dnes</div>
                <div class="card-price">{{ "%.2f"|format(cheapest_price) if cheapest_price is not none else "–" }}</div>
                <div class="card-unit">Kč/kWh</div>
                <div class="card-sub">v {{ cheapest_time }} hod</div>
            </div>

            <div class="card card--priciest">
                <div class="card-label">Nejdražší dnes</div>
                <div class="card-price">{{ "%.2f"|format(priciest_price) if priciest_price is not none else "–" }}</div>
                <div class="card-unit">Kč/kWh</div>
                <div class="card-sub">v {{ priciest_time }} hod</div>
            </div>
        </div>

        <!-- CHART -->
        <div class="chart-card">
            <div class="chart-header">
                <span class="chart-title">Průběh cen &middot; 48 hodin</span>
                <div class="chart-legend">
                    <div class="legend-item">
                        <div class="legend-dot legend-dot--spot"></div>
                        Spot
                    </div>
                    <div class="legend-item">
                        <div class="legend-dot legend-dot--total"></div>
                        Celkem vč. DPH
                    </div>
                </div>
            </div>
            <div class="chart-wrapper">
                <canvas id="myChart"></canvas>
            </div>
        </div>

        <!-- TABLE -->
        <div class="table-card">
            <div class="table-head">
                <div class="table-head-cell">Hodina</div>
                <div class="table-head-cell">Cena</div>
                <div class="table-head-cell" style="text-align:right">Kč/kWh</div>
            </div>

            {% for row in table_data %}
                {% if row.type == "header" %}
                    <div class="day-header-row">
                        <div class="day-dot"></div>
                        <div class="day-text">{{ row.label }}</div>
                    </div>
                {% else %}
                    <div class="price-row {{ 'price-row--current' if row.is_current else '' }}">
                        <div class="hour-cell">
                            {% if row.is_current %}
                                <span class="play-icon">&#9654;</span>
                                {{ row.time }}
                                <span class="hour-now">nyní</span>
                            {% else %}
                                {{ row.time }}
                            {% endif %}
                        </div>
                        <div class="bar-cell">
                            <div class="bar-track">
                                <div class="bar-fill" style="width:{{ row.bar_pct }}%; background:{{ row.color }};"></div>
                            </div>
                        </div>
                        <div class="value-cell {{ 'value-cell--current' if row.is_current else '' }}">
                            {{ "%.2f"|format(row.total) }} Kč/kWh
                        </div>
                    </div>
                {% endif %}
            {% endfor %}
        </div>
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
            if (i === 0) return; // skip first, it's just the start
            annotations['line' + i] = {
                type: 'line',
                xMin: idx - 0.5,
                xMax: idx - 0.5,
                borderColor: 'rgba(156, 163, 175, 0.5)',
                borderWidth: 1.5,
                borderDash: [5, 4],
                label: {
                    display: true,
                    content: day_labels[i],
                    position: 'start',
                    backgroundColor: 'rgba(55, 65, 81, 0.85)',
                    color: 'white',
                    font: { size: 11, weight: '600', family: 'Inter' },
                    padding: { x: 8, y: 5 },
                    borderRadius: 6
                }
            };
        });

        annotations['current'] = {
            type: 'line',
            xMin: current_hour_index,
            xMax: current_hour_index,
            borderColor: 'rgba(245, 158, 11, 0.9)',
            borderWidth: 2,
            borderDash: [4, 4],
            label: {
                display: true,
                content: 'Nyní',
                position: 'end',
                backgroundColor: 'rgba(245, 158, 11, 0.9)',
                color: '#1a1a2e',
                font: { size: 11, weight: '700', family: 'Inter' },
                padding: { x: 8, y: 5 },
                borderRadius: 6
            }
        };

        const ctx = document.getElementById('myChart').getContext('2d');

        new Chart(ctx, {
            type: 'line',
            data: {
                labels: hours,
                datasets: [
                    {
                        label: 'Spot',
                        data: prices_spot,
                        borderColor: '#60a5fa',
                        backgroundColor: 'rgba(96, 165, 250, 0.12)',
                        borderWidth: 2,
                        fill: true,
                        tension: 0.4,
                        pointRadius: 0,
                        pointHoverRadius: 4,
                    },
                    {
                        label: 'Celkem vč. DPH',
                        data: prices_total,
                        borderColor: '#f97316',
                        backgroundColor: 'rgba(249, 115, 22, 0.10)',
                        borderWidth: 2,
                        fill: true,
                        tension: 0.4,
                        pointRadius: 0,
                        pointHoverRadius: 4,
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                interaction: { mode: 'index', intersect: false },
                plugins: {
                    legend: { display: false },
                    annotation: { annotations },
                    tooltip: {
                        backgroundColor: 'rgba(255,255,255,0.97)',
                        titleColor: '#374151',
                        bodyColor: '#6b7280',
                        borderColor: '#e5e7eb',
                        borderWidth: 1,
                        padding: 10,
                        cornerRadius: 10,
                        titleFont: { family: 'Inter', weight: '600', size: 12 },
                        bodyFont:  { family: 'Inter', size: 12 },
                        callbacks: {
                            title: function(context) {
                                const idx = context[0].dataIndex;
                                let dayLabel = day_labels[0];
                                for (let i = 0; i < day_markers.length; i++) {
                                    if (idx >= day_markers[i]) dayLabel = day_labels[i];
                                }
                                return dayLabel + '  ' + hours[idx];
                            },
                            label: function(context) {
                                return ' ' + context.dataset.label + ': ' + context.parsed.y.toFixed(2) + ' Kč/kWh';
                            }
                        }
                    }
                },
                scales: {
                    y: {
                        grid: { color: 'rgba(0,0,0,0.05)', drawBorder: false },
                        border: { display: false },
                        ticks: {
                            font: { family: 'Inter', size: 11 },
                            color: '#9ca3af',
                            callback: v => v.toFixed(1)
                        }
                    },
                    x: {
                        grid: { display: false },
                        border: { display: false },
                        ticks: {
                            font: { family: 'Inter', size: 11 },
                            color: '#9ca3af',
                            maxTicksLimit: 12,
                            maxRotation: 0,
                        }
                    }
                }
            }
        });
    </script>
</body>
</html>
"""


if __name__ == "__main__":
    app.run(debug=True)
