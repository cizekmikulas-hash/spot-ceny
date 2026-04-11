import requests
import pytz
from datetime import datetime
from flask import Flask, render_template_string

app = Flask(__name__)

URL = "https://api.electree.cz/859182400102993847/prices"

DNY_TYDNE = ["Pondělí", "Úterý", "Středa", "Čtvrtek", "Pátek", "Sobota", "Neděle"]

@app.route("/")
def home():
    response = requests.get(URL)
    data = response.json()

    tz = pytz.timezone("Europe/Prague")
    now = datetime.now(tz).replace(tzinfo=None)
    current_hour = now.hour
    current_date_str = now.date().isoformat()

    raw_hours = []
    day_markers = []
    day_labels = []
    current_date = None
    day_label = ""
    current_hour_index = 0

    for i, item in enumerate(data):
        dt = datetime.strptime(item["timeLocalStart"], "%Y-%m-%d, %H:%M:%S")
        spot = round(item["priceCZK"] / 1000, 4)
        date_str = dt.date().isoformat()
        is_today = (dt.date() == now.date())
        is_current = (is_today and dt.hour == current_hour)

        if date_str != current_date:
            current_date = date_str
            day_name = DNY_TYDNE[dt.weekday()]
            day_label = f"{day_name} {dt.strftime('%d.%m.%Y')}"
            day_markers.append(i)
            day_labels.append(day_label)

        if is_current:
            current_hour_index = i

        raw_hours.append({
            "time": dt.strftime("%H:%M"),
            "hour": dt.hour,
            "spot": spot,
            "dateStr": date_str,
            "dayLabel": day_label,
            "isToday": is_today,
            "isCurrent": is_current,
        })

    return render_template_string(TEMPLATE,
        raw_hours=raw_hours,
        current_date_str=current_date_str,
        current_hour=current_hour,
        current_hour_index=current_hour_index,
        day_markers=day_markers,
        day_labels=day_labels,
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

        .page-header {
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 12px;
            margin-bottom: 20px;
        }

        .page-title {
            font-size: 13px;
            font-weight: 600;
            letter-spacing: 0.08em;
            text-transform: uppercase;
            color: #6b7280;
        }

        .settings-btn {
            display: inline-flex;
            align-items: center;
            gap: 6px;
            background: #ffffff;
            border: 1px solid #e5e7eb;
            border-radius: 8px;
            padding: 6px 13px;
            font-size: 12px;
            font-weight: 500;
            color: #374151;
            cursor: pointer;
            font-family: 'Inter', sans-serif;
            transition: background 0.15s, border-color 0.15s;
            flex-shrink: 0;
        }
        .settings-btn:hover {
            background: #f9fafb;
            border-color: #d1d5db;
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

        .chart-toggle {
            display: flex;
            background: #f3f4f6;
            border-radius: 8px;
            padding: 3px;
            gap: 2px;
        }
        .chart-toggle-btn {
            padding: 5px 13px;
            border: none;
            border-radius: 6px;
            font-size: 12px;
            font-weight: 500;
            font-family: 'Inter', sans-serif;
            cursor: pointer;
            background: transparent;
            color: #6b7280;
            transition: background 0.15s, color 0.15s;
            white-space: nowrap;
        }
        .chart-toggle-btn--active {
            background: #ffffff;
            color: #1a1a2e;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }

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

        .price-row--current { background: #fffbeb; }
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

        .bar-cell { padding-right: 16px; }

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

        .price-row--nt { background: #eff6ff; }
        .price-row--nt:hover { background: #dbeafe; }

        .nt-badge {
            display: inline-flex;
            align-items: center;
            padding: 1px 5px;
            background: #3b82f6;
            color: #ffffff;
            border-radius: 4px;
            font-size: 10px;
            font-weight: 700;
            letter-spacing: 0.04em;
            flex-shrink: 0;
        }

        /* ── MODAL ──────────────────────────────────────────── */
        .modal-overlay {
            display: none;
            position: fixed;
            inset: 0;
            background: rgba(0,0,0,0.4);
            z-index: 1000;
            align-items: center;
            justify-content: center;
            padding: 16px;
        }
        .modal-card {
            background: #ffffff;
            border-radius: 16px;
            padding: 28px 24px 24px;
            width: 100%;
            max-width: 420px;
            max-height: 90vh;
            overflow-y: auto;
            box-shadow: 0 8px 32px rgba(0,0,0,0.18);
        }
        .modal-title {
            font-size: 17px;
            font-weight: 700;
            color: #1a1a2e;
            margin-bottom: 20px;
        }
        .form-section { margin-bottom: 16px; }
        .form-section-title {
            font-size: 11px;
            font-weight: 600;
            letter-spacing: 0.07em;
            text-transform: uppercase;
            color: #9ca3af;
            margin-bottom: 8px;
        }
        .form-row {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 10px;
        }
        .form-group {
            display: flex;
            flex-direction: column;
            gap: 5px;
            min-width: 0;
        }
        .form-label {
            font-size: 12px;
            font-weight: 500;
            color: #6b7280;
        }
        .form-input {
            padding: 9px 12px;
            border: 1px solid #e5e7eb;
            border-radius: 8px;
            font-size: 14px;
            font-family: 'Inter', sans-serif;
            color: #1a1a2e;
            outline: none;
            transition: border-color 0.15s;
        }
        .form-input:focus { border-color: #6366f1; }
        .modal-actions {
            display: flex;
            gap: 10px;
            margin-top: 20px;
        }
        .btn-save {
            flex: 1;
            padding: 10px 16px;
            background: #1a1a2e;
            color: white;
            border: none;
            border-radius: 8px;
            font-size: 14px;
            font-weight: 600;
            font-family: 'Inter', sans-serif;
            cursor: pointer;
            transition: background 0.15s;
        }
        .btn-save:hover { background: #2d2d4a; }
        .btn-cancel {
            padding: 10px 16px;
            background: #f3f4f6;
            color: #374151;
            border: none;
            border-radius: 8px;
            font-size: 14px;
            font-weight: 500;
            font-family: 'Inter', sans-serif;
            cursor: pointer;
            transition: background 0.15s;
        }
        .btn-cancel:hover { background: #e5e7eb; }
    </style>
</head>
<body>
    <div class="container">
        <div class="page-header">
            <p class="page-title">Spotové ceny elektřiny</p>
            <button class="settings-btn" onclick="openSettings()">
                <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                    <circle cx="12" cy="12" r="3"></circle>
                    <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83-2.83l.06-.06A1.65 1.65 0 0 0 4.68 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 2.83-2.83l.06.06A1.65 1.65 0 0 0 9 4.68a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 2.83l-.06.06A1.65 1.65 0 0 0 19.4 9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z"></path>
                </svg>
                Nastavení
            </button>
        </div>

        <!-- TOP CARDS -->
        <div class="cards">
            <div class="card card--current">
                <div class="card-label">Nyní &middot; {{ "%02d"|format(current_hour) }}:00</div>
                <div class="card-price" id="card-current-price">–</div>
                <div class="card-unit">Kč/kWh</div>
                <div class="card-sub">vč. distribuce a DPH</div>
            </div>
            <div class="card card--cheapest">
                <div class="card-label">Nejlevnější dnes</div>
                <div class="card-price" id="card-cheapest-price">–</div>
                <div class="card-unit">Kč/kWh</div>
                <div class="card-sub" id="card-cheapest-time">–</div>
            </div>
            <div class="card card--priciest">
                <div class="card-label">Nejdražší dnes</div>
                <div class="card-price" id="card-priciest-price">–</div>
                <div class="card-unit">Kč/kWh</div>
                <div class="card-sub" id="card-priciest-time">–</div>
            </div>
        </div>

        <!-- CHART -->
        <div class="chart-card">
            <div class="chart-header">
                <span class="chart-title">Průběh cen &middot; 48 hodin</span>
                <div class="chart-toggle">
                    <button class="chart-toggle-btn" id="toggle-btn-0" onclick="setDataset(0)">Spot</button>
                    <button class="chart-toggle-btn chart-toggle-btn--active" id="toggle-btn-1" onclick="setDataset(1)">Celkem vč. DPH</button>
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
            <div id="table-body"></div>
        </div>
    </div>

    <!-- SETTINGS MODAL -->
    <div id="settings-modal" class="modal-overlay">
        <div class="modal-card">
            <div class="modal-title">Nastavení cen</div>
            <div class="form-section">
                <div class="form-section-title">Distribuce (Kč/kWh)</div>
                <p style="font-size:12px;color:#6b7280;margin-bottom:10px;line-height:1.5;">Zde vyplň součet ceny distribuce a dalších poplatků nad rámec ceny spotu bez DPH.</p>
                <div class="form-row">
                    <div class="form-group">
                        <label class="form-label">Cena NT</label>
                        <input id="input-nt" class="form-input" type="number" step="0.01">
                    </div>
                    <div class="form-group">
                        <label class="form-label">Cena VT</label>
                        <input id="input-vt" class="form-input" type="number" step="0.01">
                    </div>
                </div>
            </div>
            <div class="form-section">
                <div class="form-section-title">1. NT pásmo (hodiny, od–do)</div>
                <div class="form-row">
                    <div class="form-group">
                        <label class="form-label">Začátek</label>
                        <input id="input-nt1-start" class="form-input" type="number" min="0" max="23" step="1">
                    </div>
                    <div class="form-group">
                        <label class="form-label">Konec</label>
                        <input id="input-nt1-end" class="form-input" type="number" min="0" max="23" step="1">
                    </div>
                </div>
            </div>
            <div class="form-section">
                <div class="form-section-title">2. NT pásmo (hodiny, od–do)</div>
                <div class="form-row">
                    <div class="form-group">
                        <label class="form-label">Začátek</label>
                        <input id="input-nt2-start" class="form-input" type="number" min="0" max="23" step="1">
                    </div>
                    <div class="form-group">
                        <label class="form-label">Konec</label>
                        <input id="input-nt2-end" class="form-input" type="number" min="0" max="23" step="1">
                    </div>
                </div>
            </div>
            <div class="form-section">
                <div class="form-section-title">3. NT pásmo (hodiny, od–do)</div>
                <div class="form-row">
                    <div class="form-group">
                        <label class="form-label">Začátek</label>
                        <input id="input-nt3-start" class="form-input" type="number" min="0" max="23" step="1">
                    </div>
                    <div class="form-group">
                        <label class="form-label">Konec</label>
                        <input id="input-nt3-end" class="form-input" type="number" min="0" max="23" step="1">
                    </div>
                </div>
            </div>
            <div class="form-section">
                <div class="form-section-title">4. NT pásmo (hodiny, od–do)</div>
                <div class="form-row">
                    <div class="form-group">
                        <label class="form-label">Začátek</label>
                        <input id="input-nt4-start" class="form-input" type="number" min="0" max="23" step="1">
                    </div>
                    <div class="form-group">
                        <label class="form-label">Konec</label>
                        <input id="input-nt4-end" class="form-input" type="number" min="0" max="23" step="1">
                    </div>
                </div>
            </div>
            <div class="form-section">
                <div class="form-section-title">5. NT pásmo (hodiny, od–do)</div>
                <div class="form-row">
                    <div class="form-group">
                        <label class="form-label">Začátek</label>
                        <input id="input-nt5-start" class="form-input" type="number" min="0" max="23" step="1">
                    </div>
                    <div class="form-group">
                        <label class="form-label">Konec</label>
                        <input id="input-nt5-end" class="form-input" type="number" min="0" max="23" step="1">
                    </div>
                </div>
            </div>
            <div class="modal-actions">
                <button class="btn-save" onclick="saveAndApply()">Uložit a přepočítat</button>
                <button class="btn-cancel" onclick="closeSettings()">Zrušit</button>
            </div>
        </div>
    </div>

    <script>
        var rawHours        = {{ raw_hours | tojson }};
        var currentDateStr  = {{ current_date_str | tojson }};
        var currentHour     = {{ current_hour }};
        var currentHourIndex = {{ current_hour_index }};
        var dayMarkers      = {{ day_markers | tojson }};
        var dayLabels       = {{ day_labels | tojson }};
        var pricesSpot      = rawHours.map(function(h) { return h.spot; });

        // ── Settings ─────────────────────────────────────────
        var DEFAULTS = { priceNT: 0.76, priceVT: 2.78,
                         nt1Start: 4,  nt1End: 8,
                         nt2Start: 15, nt2End: 19,
                         nt3Start: 0,  nt3End: 0,
                         nt4Start: 0,  nt4End: 0,
                         nt5Start: 0,  nt5End: 0 };

        function getSettings() {
            try {
                var stored = localStorage.getItem('spotSettings');
                return stored ? Object.assign({}, DEFAULTS, JSON.parse(stored)) : Object.assign({}, DEFAULTS);
            } catch(e) { return Object.assign({}, DEFAULTS); }
        }

        function saveSettings(s) {
            localStorage.setItem('spotSettings', JSON.stringify(s));
        }

        // ── Helpers ───────────────────────────────────────────
        function isNT(hour, s) {
            return (s.nt1End > s.nt1Start && hour >= s.nt1Start && hour < s.nt1End) ||
                   (s.nt2End > s.nt2Start && hour >= s.nt2Start && hour < s.nt2End) ||
                   (s.nt3End > s.nt3Start && hour >= s.nt3Start && hour < s.nt3End) ||
                   (s.nt4End > s.nt4Start && hour >= s.nt4Start && hour < s.nt4End) ||
                   (s.nt5End > s.nt5Start && hour >= s.nt5Start && hour < s.nt5End);
        }

        function getDistribuce(hour, s) {
            if ((s.nt1End > s.nt1Start && hour >= s.nt1Start && hour < s.nt1End) ||
                (s.nt2End > s.nt2Start && hour >= s.nt2Start && hour < s.nt2End) ||
                (s.nt3End > s.nt3Start && hour >= s.nt3Start && hour < s.nt3End) ||
                (s.nt4End > s.nt4Start && hour >= s.nt4Start && hour < s.nt4End) ||
                (s.nt5End > s.nt5Start && hour >= s.nt5Start && hour < s.nt5End))
                return s.priceNT;
            return s.priceVT;
        }

        function priceColor(ratio) {
            var r, g;
            if (ratio < 0.5) { r = Math.round(255 * ratio * 2); g = 200; }
            else { r = 220; g = Math.round(200 * (1 - (ratio - 0.5) * 2)); }
            return 'rgb(' + r + ',' + g + ',70)';
        }

        // ── Chart ─────────────────────────────────────────────
        var myChart = null;
        var activeDataset = 1; // 0 = Spot, 1 = Celkem vč. DPH

        function setDataset(idx) {
            activeDataset = idx;
            if (myChart) {
                myChart.data.datasets[0].hidden = (idx !== 0);
                myChart.data.datasets[1].hidden = (idx !== 1);
                myChart.update();
            }
            document.getElementById('toggle-btn-0').classList.toggle('chart-toggle-btn--active', idx === 0);
            document.getElementById('toggle-btn-1').classList.toggle('chart-toggle-btn--active', idx === 1);
        }

        function buildAnnotations() {
            var ann = {};
            dayMarkers.forEach(function(idx, i) {
                if (i === 0) return;
                ann['line' + i] = {
                    type: 'line', xMin: idx - 0.5, xMax: idx - 0.5,
                    borderColor: 'rgba(156,163,175,0.5)', borderWidth: 1.5, borderDash: [5,4],
                    label: {
                        display: true, content: dayLabels[i], position: 'start',
                        backgroundColor: 'rgba(55,65,81,0.85)', color: 'white',
                        font: { size: 11, weight: '600', family: 'Inter' },
                        padding: { x: 8, y: 5 }, borderRadius: 6
                    }
                };
            });
            ann['current'] = {
                type: 'line', xMin: currentHourIndex, xMax: currentHourIndex,
                borderColor: 'rgba(245,158,11,0.9)', borderWidth: 2, borderDash: [4,4],
                label: {
                    display: true, content: 'Nyní', position: 'end',
                    backgroundColor: 'rgba(245,158,11,0.9)', color: '#1a1a2e',
                    font: { size: 11, weight: '700', family: 'Inter' },
                    padding: { x: 8, y: 5 }, borderRadius: 6
                }
            };
            return ann;
        }

        function initChart(allTotals, totalColors) {
            var hours = rawHours.map(function(h) { return h.time; });
            var ctx = document.getElementById('myChart').getContext('2d');
            myChart = new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: hours,
                    datasets: [
                        {
                            label: 'Spot', data: pricesSpot,
                            backgroundColor: 'rgba(91,155,213,0.8)',
                            borderWidth: 0, borderRadius: 2,
                            hidden: true
                        },
                        {
                            label: 'Celkem vč. DPH', data: allTotals,
                            backgroundColor: totalColors,
                            borderWidth: 0, borderRadius: 2,
                            hidden: false
                        }
                    ]
                },
                options: {
                    responsive: true, maintainAspectRatio: false,
                    interaction: { mode: 'index', intersect: false },
                    plugins: {
                        legend: { display: false },
                        annotation: { annotations: buildAnnotations() },
                        tooltip: { enabled: false }
                    },
                    scales: {
                        y: {
                            grid: { color: 'rgba(0,0,0,0.05)', drawBorder: false },
                            border: { display: false },
                            ticks: { font: { family: 'Inter', size: 11 }, color: '#9ca3af',
                                     callback: function(v) { return v.toFixed(1); } }
                        },
                        x: {
                            grid: { display: false }, border: { display: false },
                            ticks: { font: { family: 'Inter', size: 11 }, color: '#9ca3af',
                                     maxTicksLimit: 12, maxRotation: 0 }
                        }
                    }
                }
            });
        }

        // ── Main recalculate ──────────────────────────────────
        function recalculate() {
            var s = getSettings();
            var DPH = 1.21;

            var computed = rawHours.map(function(h) {
                var dist = getDistribuce(h.hour, s);
                var total = Math.round((h.spot + dist) * DPH * 100) / 100;
                return { time: h.time, hour: h.hour, dateStr: h.dateStr,
                         dayLabel: h.dayLabel, isToday: h.isToday, isCurrent: h.isCurrent,
                         dist: dist, total: total, isNT: isNT(h.hour, s) };
            });

            var allTotals = computed.map(function(c) { return c.total; });
            var minTotal = Math.min.apply(null, allTotals);
            var maxTotal = Math.max.apply(null, allTotals);

            var totalColors = allTotals.map(function(v) {
                var ratio = maxTotal !== minTotal ? (v - minTotal) / (maxTotal - minTotal) : 0.5;
                return priceColor(ratio);
            });

            // Today stats
            var currentItem = null, cheapest = null, priciest = null;
            computed.forEach(function(c) {
                if (!c.isToday) return;
                if (c.isCurrent) currentItem = c;
                if (!cheapest || c.total < cheapest.total) cheapest = c;
                if (!priciest || c.total > priciest.total) priciest = c;
            });

            document.getElementById('card-current-price').textContent =
                currentItem ? currentItem.total.toFixed(2) : '–';
            document.getElementById('card-cheapest-price').textContent =
                cheapest ? cheapest.total.toFixed(2) : '–';
            document.getElementById('card-cheapest-time').textContent =
                cheapest ? ('v ' + cheapest.time + ' hod') : '–';
            document.getElementById('card-priciest-price').textContent =
                priciest ? priciest.total.toFixed(2) : '–';
            document.getElementById('card-priciest-time').textContent =
                priciest ? ('v ' + priciest.time + ' hod') : '–';

            // Build table
            var tableRows = computed.filter(function(c) {
                return c.dateStr > currentDateStr ||
                       (c.dateStr === currentDateStr && c.hour >= currentHour);
            });

            var html = '';
            var lastDayLabel = null;
            tableRows.forEach(function(c) {
                if (c.dayLabel !== lastDayLabel) {
                    lastDayLabel = c.dayLabel;
                    html += '<div class="day-header-row"><div class="day-dot"></div>' +
                            '<div class="day-text">' + c.dayLabel + '</div></div>';
                }
                var ratio = maxTotal !== minTotal ? (c.total - minTotal) / (maxTotal - minTotal) : 0.5;
                var barPct = Math.round(ratio * 100);
                var color = priceColor(ratio);
                var rowCls = 'price-row' + (c.isNT ? ' price-row--nt' : '') + (c.isCurrent ? ' price-row--current' : '');
                var valCls = 'value-cell' + (c.isCurrent ? ' value-cell--current' : '');
                var hourHtml = (c.isCurrent ? '<span class="play-icon">&#9654;</span>' : '') +
                               c.time +
                               (c.isCurrent ? '<span class="hour-now">nyní</span>' : '') +
                               '';

                html += '<div class="' + rowCls + '">' +
                        '<div class="hour-cell">' + hourHtml + '</div>' +
                        '<div class="bar-cell"><div class="bar-track">' +
                        '<div class="bar-fill" style="width:' + barPct + '%;background:' + color + ';"></div>' +
                        '</div></div>' +
                        '<div class="' + valCls + '">' + c.total.toFixed(2) + ' Kč/kWh</div>' +
                        '</div>';
            });
            document.getElementById('table-body').innerHTML = html;

            // Chart
            if (myChart === null) {
                initChart(allTotals, totalColors);
            } else {
                myChart.data.datasets[1].data = allTotals;
                myChart.data.datasets[1].backgroundColor = totalColors;
                myChart.data.datasets[0].hidden = (activeDataset !== 0);
                myChart.data.datasets[1].hidden = (activeDataset !== 1);
                myChart.update();
            }
        }

        // ── Modal ─────────────────────────────────────────────
        function openSettings() {
            var s = getSettings();
            document.getElementById('input-nt').value        = s.priceNT;
            document.getElementById('input-vt').value        = s.priceVT;
            document.getElementById('input-nt1-start').value = s.nt1Start;
            document.getElementById('input-nt1-end').value   = s.nt1End;
            document.getElementById('input-nt2-start').value = s.nt2Start;
            document.getElementById('input-nt2-end').value   = s.nt2End;
            document.getElementById('input-nt3-start').value = s.nt3Start;
            document.getElementById('input-nt3-end').value   = s.nt3End;
            document.getElementById('input-nt4-start').value = s.nt4Start;
            document.getElementById('input-nt4-end').value   = s.nt4End;
            document.getElementById('input-nt5-start').value = s.nt5Start;
            document.getElementById('input-nt5-end').value   = s.nt5End;
            document.getElementById('settings-modal').style.display = 'flex';
        }

        function closeSettings() {
            document.getElementById('settings-modal').style.display = 'none';
        }

        function saveAndApply() {
            function fi(id, fb) { var v = parseInt(document.getElementById(id).value, 10); return isNaN(v) ? fb : v; }
            function ff(id, fb) { var v = parseFloat(document.getElementById(id).value); return isNaN(v) ? fb : v; }
            saveSettings({
                priceNT: ff('input-nt', 0.76),
                priceVT: ff('input-vt', 2.78),
                nt1Start: fi('input-nt1-start', 4),
                nt1End:   fi('input-nt1-end',   8),
                nt2Start: fi('input-nt2-start', 15),
                nt2End:   fi('input-nt2-end',   19),
                nt3Start: fi('input-nt3-start', 0),
                nt3End:   fi('input-nt3-end',   0),
                nt4Start: fi('input-nt4-start', 0),
                nt4End:   fi('input-nt4-end',   0),
                nt5Start: fi('input-nt5-start', 0),
                nt5End:   fi('input-nt5-end',   0),
            });
            closeSettings();
            recalculate();
        }

        document.getElementById('settings-modal').addEventListener('click', function(e) {
            if (e.target === this) closeSettings();
        });

        recalculate();
    </script>
</body>
</html>
"""


if __name__ == "__main__":
    app.run(debug=True)
