import base64
import json
import math
import os
import statistics
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

import requests
from flask import Flask, session, request, redirect, url_for, render_template_string

app = Flask(__name__)

APP_PASSWORD = os.environ.get("APP_PASSWORD", "")
SECRET_KEY = os.environ.get("SECRET_KEY", "change-this-key")
ICU_API_KEY = os.environ.get("ICU_API_KEY", "")
ICU_ATHLETE_ID = os.environ.get("ICU_ATHLETE_ID", "")
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
ATHLETE_CONTEXT = os.environ.get(
    "ATHLETE_CONTEXT",
    "The athlete trains indoors on Zwift twice a day, every day: a Zone 2 session "
    "in the morning, and in the evening alternates VO2max sessions with Zone 2 "
    "sessions. They race outdoors from March to September.",
)

app.secret_key = SECRET_KEY

DAYS_BACK = 20          # recent health / freshness window
SEASON_DAYS_BACK = 90   # longer window for periodization / polarization analysis

APP_VERSION = "THE LAB · V4 VISUAL REBUILD · WEEK MEMORY"
ROME_TZ = ZoneInfo("Europe/Rome")

LOGO_B64 = (
    "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"
    "SUVORK5CYII="
)

FAVICON_B64 = (
    "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"
    "YII="
)

# ---------------------------------------------------------------------------
# Shared CSS
# ---------------------------------------------------------------------------
BASE_CSS = """
@import url('https://fonts.googleapis.com/css2?family=Amatic+SC:wght@400;700&family=Parkinsans:wght@400;500;600;700&display=swap');

:root {
  --bg:#08090b;
  --panel:#111318;
  --panel-2:#151820;
  --panel-3:#0d0f13;
  --line:rgba(255,255,255,.105);
  --line-strong:rgba(255,255,255,.18);
  --text:#f5f7fa;
  --muted:#a6adb8;
  --muted-2:#727a87;
  --cyan:#45d7e8;
  --green:#25d47a;
  --orange:#ffab2e;
  --red:#ff4254;
  --purple:#9b7cff;
  --grey:#9098a4;
  --radius:24px;
  --radius-sm:16px;
  --font:'Parkinsans','Trebuchet MS',Arial,sans-serif;
  --brand:'Amatic SC','Segoe Print','Bradley Hand',cursive;
}

* { box-sizing:border-box; }
html { background:var(--bg); }
body {
  margin:0;
  min-height:100vh;
  color:var(--text);
  background:
    radial-gradient(circle at 13% 0%, rgba(69,215,232,.075), transparent 27%),
    radial-gradient(circle at 87% 0%, rgba(255,66,84,.075), transparent 28%),
    var(--bg);
  font-family:var(--font);
  font-size:15px;
  line-height:1.55;
  -webkit-font-smoothing:antialiased;
}
a { color:inherit; text-decoration:none; }
button,input { font:inherit; }
button { cursor:pointer; }

.v4-shell { width:min(1440px, calc(100% - 32px)); margin:0 auto; padding:22px 0 70px; }
.v4-topbar { display:flex; align-items:center; justify-content:space-between; gap:20px; margin-bottom:18px; }
.v4-brand { font-family:var(--brand); font-size:38px; line-height:1; font-weight:400; letter-spacing:.02em; }
.v4-top-actions { display:flex; align-items:center; gap:10px; }
.v4-pill, .v4-logout {
  display:inline-flex; align-items:center; justify-content:center; min-height:40px; padding:0 15px;
  border:1px solid var(--line); border-radius:999px; background:rgba(255,255,255,.025);
  font-size:12px; font-weight:600;
}
.v4-pill { color:#c7f8fc; border-color:rgba(69,215,232,.18); }
.v4-logout { transition:.18s ease; }
.v4-logout:hover { border-color:rgba(255,66,84,.45); background:rgba(255,66,84,.08); transform:translateY(-1px); }

.v4-card {
  border:1px solid var(--line); border-radius:var(--radius); background:linear-gradient(180deg, rgba(255,255,255,.025), rgba(255,255,255,.008)), var(--panel);
  box-shadow:0 18px 50px rgba(0,0,0,.24); overflow:hidden;
}
.v4-hero { position:relative; text-align:center; padding:26px 24px 28px; margin-bottom:18px; }
.v4-hero::before { content:''; position:absolute; width:500px; height:240px; left:50%; top:-185px; transform:translateX(-50%); border-radius:50%; background:rgba(69,215,232,.12); filter:blur(58px); }
.v4-logo { position:relative; width:205px; max-width:55vw; display:block; margin:0 auto 12px; filter:drop-shadow(0 14px 24px rgba(0,0,0,.38)); }
.v4-title { position:relative; margin:0; font-size:clamp(42px,5.5vw,72px); line-height:.98; font-weight:600; letter-spacing:-.055em; }
.v4-kicker { position:relative; margin-top:11px; color:var(--cyan); font-size:12px; font-weight:700; letter-spacing:.17em; text-transform:uppercase; }
.v4-subtitle { position:relative; margin:8px auto 0; color:var(--muted); font-size:13px; }
.v4-preview-banner { margin:0 0 18px; padding:11px 15px; border:1px solid rgba(69,215,232,.22); border-radius:16px; background:rgba(69,215,232,.055); color:#c9f8fc; font-size:13px; text-align:center; }
.v4-preview-banner a { display:inline-flex; margin-left:10px; padding:4px 9px; border:1px solid rgba(255,255,255,.14); border-radius:999px; color:#fff; font-size:10px; font-weight:700; }

.v4-controls { display:grid; grid-template-columns:1.05fr 1.25fr 1fr; gap:16px; margin-bottom:26px; }
.v4-control { min-height:310px; padding:22px; display:flex; flex-direction:column; }
.v4-control-head { display:flex; align-items:center; gap:11px; margin-bottom:8px; }
.v4-icon { width:38px; height:38px; flex:0 0 38px; display:grid; place-items:center; border-radius:13px; border:1px solid var(--line); background:rgba(255,255,255,.035); font-size:17px; }
.v4-control-title { margin:0; font-size:24px; line-height:1.1; font-weight:600; letter-spacing:-.035em; }
.v4-copy { margin:0 0 18px; color:#c1c6ce; font-size:14px; line-height:1.6; }
.v4-chat-form { display:grid; grid-template-columns:1fr auto; gap:10px; }
.v4-input { width:100%; height:54px; border:1px solid var(--line); border-radius:14px; background:#090b0e; color:var(--text); padding:0 15px; outline:none; }
.v4-input:focus { border-color:rgba(69,215,232,.5); box-shadow:0 0 0 4px rgba(69,215,232,.07); }
.v4-btn { min-height:46px; border:1px solid transparent; border-radius:14px; padding:0 18px; font-weight:700; transition:.18s ease; }
.v4-btn:hover { transform:translateY(-1px); filter:brightness(1.04); }
.v4-btn-cyan { background:linear-gradient(135deg,#57dfec,#28b8ca); color:#071013; }
.v4-btn-orange { background:linear-gradient(135deg,#ffbc43,var(--orange)); color:#1b1207; }
.v4-btn-ghost { border-color:var(--line); background:rgba(255,255,255,.035); color:var(--text); }
.v4-notes { margin-top:16px; max-height:105px; overflow:auto; border-top:1px solid rgba(255,255,255,.065); padding-top:10px; }
.v4-note { margin:4px 0; color:var(--muted); font-size:11px; }
.v4-note-date { color:var(--cyan); margin-right:5px; }
.v4-chat-ok { margin-top:12px; color:var(--green); font-size:13px; }
.v4-error { margin:14px 0; padding:12px 14px; border:1px solid rgba(255,66,84,.3); border-radius:14px; background:rgba(255,66,84,.06); color:#ff9ba6; font-size:13px; }

.v4-feeling-latest { display:flex; align-items:center; gap:9px; min-height:28px; color:var(--muted); font-size:12px; margin-bottom:11px; }
.v4-feeling-dot { width:8px; height:8px; border-radius:50%; background:var(--green); box-shadow:0 0 12px rgba(37,212,122,.45); }
.v4-feeling-grid { display:grid; grid-template-columns:repeat(10,1fr); gap:6px; }
.v4-feeling-btn { aspect-ratio:1; min-width:0; border:1px solid var(--line); border-radius:12px; background:rgba(255,255,255,.025); color:var(--text); font-weight:600; font-size:12px; transition:.16s ease; }
.v4-feeling-btn:hover { border-color:rgba(155,124,255,.55); background:rgba(155,124,255,.12); transform:translateY(-1px); }
.v4-feeling-scale { display:flex; justify-content:space-between; gap:12px; margin-top:14px; padding-top:12px; border-top:1px solid rgba(255,255,255,.06); font-size:10px; color:var(--muted); }
.v4-feeling-scale span:first-child { color:#ff8a97; }
.v4-feeling-scale span:last-child { color:#72e7aa; }

.v4-status-box { flex:1; display:flex; flex-direction:column; justify-content:center; gap:12px; padding:18px; border:1px solid rgba(255,171,46,.18); border-radius:18px; background:radial-gradient(circle at 50% -5%,rgba(255,171,46,.11),transparent 42%),#0d0f12; text-align:center; }
.v4-ready-row { display:flex; align-items:center; justify-content:center; gap:9px; }
.v4-live-dot { width:10px; height:10px; border-radius:50%; background:var(--green); box-shadow:0 0 0 5px rgba(37,212,122,.08),0 0 18px rgba(37,212,122,.35); }
.v4-ready { font-size:27px; font-weight:600; letter-spacing:-.035em; }
.v4-clock-preview { display:grid; grid-template-columns:auto auto 1fr; align-items:center; gap:9px; padding:11px 12px; border:1px solid rgba(69,215,232,.16); border-radius:14px; background:rgba(69,215,232,.045); text-align:left; }
.v4-clock-preview span { color:#c7f8fc; font-size:10px; font-weight:700; letter-spacing:.12em; }
.v4-clock-preview strong { font-size:23px; letter-spacing:-.04em; }
.v4-clock-preview small { justify-self:end; color:var(--muted); font-size:9px; text-align:right; line-height:1.3; }
.v4-status-actions { display:grid; grid-template-columns:1fr; gap:9px; }
.v4-preview-link { display:flex; min-height:44px; align-items:center; justify-content:center; border:1px solid var(--line); border-radius:13px; background:rgba(255,255,255,.035); font-size:12px; font-weight:650; }
.loading-track { display:none; height:7px; border-radius:999px; overflow:hidden; background:rgba(255,255,255,.07); }
.loading-fill { width:0; height:100%; border-radius:999px; background:linear-gradient(90deg,var(--orange),var(--cyan)); }
.loading-label { display:none; margin:0; color:var(--muted); font-size:10px; }

.v4-dashboard { display:grid; gap:18px; }
.v4-section-card { padding:24px; }
.v4-section-head { display:flex; align-items:flex-end; justify-content:space-between; gap:16px; margin-bottom:18px; }
.v4-section-title { margin:0; font-size:27px; line-height:1; font-weight:600; letter-spacing:-.04em; }
.v4-section-note { margin:0; color:var(--muted); font-size:12px; }

.v4-hero-grid { display:grid; grid-template-columns:1.15fr .85fr; gap:18px; }
.v4-clock-card { padding:24px; display:grid; grid-template-columns:220px 1fr; gap:24px; align-items:center; }
.v4-clock-visual { position:relative; width:200px; aspect-ratio:1; margin:auto; }
.v4-clock-svg { width:100%; height:100%; display:block; }
.v4-clock-track { fill:none; stroke:#282d35; stroke-width:13; }
.v4-clock-am,.v4-clock-mid,.v4-clock-pm { fill:none; stroke-width:13; stroke-linecap:round; transform:rotate(-90deg); transform-origin:90px 90px; }
.v4-clock-am { stroke:var(--cyan); stroke-dasharray:48.8 51.2; }
.v4-clock-mid { stroke:#59616d; stroke-dasharray:19.6 80.4; stroke-dashoffset:-50.6; }
.v4-clock-pm { stroke:var(--orange); stroke-dasharray:27.8 72.2; stroke-dashoffset:-72.2; }
.v4-clock-marker { fill:#fff; stroke:#0b0d10; stroke-width:3; filter:drop-shadow(0 0 6px rgba(255,255,255,.45)); }
.v4-clock-center { position:absolute; inset:33px; border-radius:50%; background:#0b0d10; display:flex; flex-direction:column; align-items:center; justify-content:center; text-align:center; border:1px solid rgba(255,255,255,.055); }
.v4-clock-time { font-size:38px; font-weight:600; line-height:.95; letter-spacing:-.055em; }
.v4-clock-phase { margin-top:7px; color:var(--cyan); font-size:9px; font-weight:700; letter-spacing:.12em; text-transform:uppercase; }
.v4-clock-date { margin-top:4px; color:var(--muted); font-size:9px; }
.v4-clock-copy h3 { margin:0 0 8px; font-size:29px; line-height:1.08; font-weight:600; letter-spacing:-.045em; }
.v4-clock-copy p { margin:0; color:#c3c8d0; font-size:13px; line-height:1.62; }
.v4-slot-grid { display:grid; grid-template-columns:1fr 1fr; gap:10px; margin-top:15px; }
.v4-slot { padding:12px 13px; border:1px solid var(--line); border-radius:14px; background:rgba(255,255,255,.025); }
.v4-slot span { display:block; color:var(--muted); font-size:9px; text-transform:uppercase; letter-spacing:.11em; }
.v4-slot strong { display:block; margin-top:3px; font-size:17px; }
.v4-slot.done strong { color:var(--green); }.v4-slot.open strong { color:var(--cyan); }.v4-slot.upcoming strong { color:var(--orange); }.v4-slot.missed strong { color:var(--grey); }
.v4-next-slot { margin-top:10px; padding:11px 13px; border:1px solid rgba(255,171,46,.18); border-radius:14px; background:rgba(255,171,46,.055); display:flex; justify-content:space-between; gap:12px; font-size:11px; }
.v4-next-slot span { color:var(--muted); }.v4-next-slot strong { color:var(--orange); }
.v4-today { margin-top:9px; color:var(--muted-2); font-size:10px; }

.v4-energy-card { padding:24px; text-align:center; }
.v4-energy-card h3 { margin:0; font-size:27px; font-weight:600; letter-spacing:-.04em; }
.v4-energy-card > p { margin:7px auto 0; max-width:470px; color:var(--muted); font-size:12px; }
.v4-energy-gauge { position:relative; width:min(390px,100%); margin:12px auto 0; }
.v4-energy-svg { display:block; width:100%; height:auto; }
.v4-energy-seg { fill:none; stroke-width:13; stroke-linecap:round; }
.v4-energy-s1 { stroke:var(--red); }.v4-energy-s2 { stroke:var(--orange); }.v4-energy-s3 { stroke:#89919d; }.v4-energy-s4 { stroke:var(--green); }.v4-energy-s5 { stroke:var(--cyan); }
.v4-energy-halo { fill:rgba(255,255,255,.14); }.v4-energy-marker { fill:#fff; stroke:#08090b; stroke-width:2.2; }
.v4-energy-score { position:absolute; left:50%; bottom:5px; transform:translateX(-50%); text-align:center; }
.v4-energy-score strong { display:block; font-size:51px; line-height:.9; letter-spacing:-.06em; }
.v4-energy-score span { display:block; margin-top:5px; color:var(--muted); font-size:10px; }
.v4-badge { display:inline-flex; align-items:center; justify-content:center; min-height:28px; padding:0 11px; margin-top:10px; border-radius:999px; border:1px solid var(--line); font-size:10px; font-weight:700; text-transform:uppercase; letter-spacing:.08em; }
.v4-badge.green { color:#79eaaa; border-color:rgba(37,212,122,.4); background:rgba(37,212,122,.07); }.v4-badge.red { color:#ff8995; border-color:rgba(255,66,84,.38); background:rgba(255,66,84,.06); }.v4-badge.grey { color:#c4c9d0; }
.v4-wearables { display:flex; justify-content:center; flex-wrap:wrap; gap:10px 16px; margin-top:9px; color:var(--muted); font-size:10px; }.v4-wearables strong{color:var(--text);}

.v4-trend { margin-top:19px; padding-top:17px; border-top:1px solid rgba(255,255,255,.065); }
.v4-trend-head { display:flex; justify-content:space-between; align-items:center; gap:12px; margin-bottom:10px; }.v4-trend-head strong{font-size:12px}.v4-trend-head span{color:var(--muted);font-size:9px}
.v4-trend-grid { display:grid; grid-template-columns:repeat(5,1fr); gap:8px; align-items:end; }
.v4-trend-item { text-align:center; }
.v4-trend-track { width:11px; height:42px; margin:0 auto 5px; border-radius:999px; background:#272c33; overflow:hidden; display:flex; align-items:flex-end; }
.v4-trend-fill { width:100%; min-height:5px; border-radius:999px; }.v4-trend-fill.green{background:var(--green)}.v4-trend-fill.red{background:var(--red)}.v4-trend-fill.grey{background:var(--grey)}
.v4-trend-delta { font-size:10px; font-weight:700; }.v4-trend-day{color:var(--muted);font-size:9px}

.v4-metric-grid { display:grid; grid-template-columns:repeat(4,1fr); gap:14px; }
.v4-metric { padding:18px; text-align:center; }
.v4-metric-label { color:#cbd0d7; font-size:10px; font-weight:700; letter-spacing:.1em; text-transform:uppercase; }
.v4-ring { position:relative; width:94px; aspect-ratio:1; margin:12px auto 8px; }
.v4-ring svg { width:100%; height:100%; transform:rotate(-90deg); }
.v4-ring-track,.v4-ring-progress { fill:none; stroke-width:9; }
.v4-ring-track { stroke:#272c33; }.v4-ring-progress { stroke-linecap:round; }
.v4-ring-progress.green{stroke:var(--green)}.v4-ring-progress.red{stroke:var(--red)}.v4-ring-progress.grey{stroke:var(--grey)}.v4-ring-progress.cyan{stroke:var(--cyan)}.v4-ring-progress.orange{stroke:var(--orange)}
.v4-ring-center { position:absolute; inset:0; display:flex; align-items:center; justify-content:center; flex-direction:column; }
.v4-ring-value { font-size:24px; font-weight:600; letter-spacing:-.04em; }.v4-ring-sub{color:var(--muted);font-size:8px;margin-top:1px}
.v4-metric-status { font-size:10px; font-weight:700; text-transform:uppercase; letter-spacing:.07em; }.v4-metric-status.green{color:var(--green)}.v4-metric-status.red{color:var(--red)}.v4-metric-status.grey{color:var(--grey)}
.v4-sleep-quality { font-size:32px; font-weight:600; letter-spacing:-.05em; }.v4-quality-copy{color:var(--muted);font-size:10px}.v4-score-bar{height:6px;border-radius:999px;background:#272c33;overflow:hidden;margin:10px 8px 0}.v4-score-fill{height:100%;border-radius:999px;background:linear-gradient(90deg,var(--cyan),var(--green));}

.v4-readiness-grid { display:grid; grid-template-columns:1.15fr .85fr; gap:14px; }
.v4-readiness-card { padding:20px; display:flex; align-items:center; gap:18px; }
.v4-readiness-card .v4-ring { width:116px; flex:0 0 116px; margin:0; }
.v4-readiness-card .v4-ring-value { font-size:31px; }
.v4-readiness-copy h3 { margin:0; font-size:22px; font-weight:600; letter-spacing:-.035em; }.v4-readiness-copy strong{display:block;margin-top:4px;font-size:24px}.v4-readiness-copy p{margin:6px 0 0;color:var(--muted);font-size:11px;line-height:1.55}
.v4-last-night { padding:20px; display:flex; flex-direction:column; justify-content:center; }.v4-last-night span{color:var(--muted);font-size:10px;text-transform:uppercase;letter-spacing:.1em}.v4-last-night strong{font-size:31px;letter-spacing:-.045em;margin-top:4px}.v4-last-night p{margin:4px 0 0;color:var(--muted);font-size:11px}

.v4-coach-call { padding:24px; border-color:rgba(69,215,232,.16); background:radial-gradient(circle at 0 0,rgba(69,215,232,.08),transparent 34%),var(--panel); }
.v4-coach-kicker { color:var(--cyan); font-size:10px; font-weight:700; letter-spacing:.13em; text-transform:uppercase; }.v4-coach-call h2{margin:5px 0 9px;font-size:30px;letter-spacing:-.045em}.v4-coach-call p{margin:0;max-width:1080px;color:#d0d4da;font-size:14px;line-height:1.68}

.v4-week { padding:24px; }
.v4-week-memory { display:flex; align-items:flex-start; gap:12px; margin-bottom:15px; padding:12px 14px; border:1px solid var(--line); border-radius:16px; background:rgba(255,255,255,.02); }
.v4-week-label { color:var(--muted); font-size:9px; font-weight:700; text-transform:uppercase; letter-spacing:.1em; padding-top:5px; flex:0 0 auto; }
.v4-week-chips { display:flex; gap:7px; flex-wrap:wrap; flex:1; }.v4-week-chip{display:inline-flex;gap:5px;align-items:center;padding:5px 8px;border:1px solid var(--line);border-radius:999px;font-size:9px;color:#c7ccd3}.v4-week-chip.hard{border-color:rgba(255,171,46,.25);color:#ffd083}.v4-week-note{color:var(--muted);font-size:9px;align-self:center}
.v4-session-grid { display:grid; grid-template-columns:repeat(3,1fr); gap:14px; }
.v4-session { padding:19px; position:relative; }
.v4-session::before { content:''; position:absolute; left:0; top:0; bottom:0; width:3px; background:var(--cyan); }.v4-session.vo2::before{background:var(--red)}.v4-session.threshold::before{background:var(--purple)}.v4-session.tempo::before{background:var(--orange)}.v4-session.recovery::before{background:var(--green)}
.v4-session-slot { color:var(--cyan); font-size:9px; font-weight:700; letter-spacing:.1em; text-transform:uppercase; }.v4-session h3{margin:5px 0 8px;font-size:21px;line-height:1.16;letter-spacing:-.035em}.v4-session-meta{display:flex;gap:6px;flex-wrap:wrap}.v4-session-pill{padding:4px 7px;border:1px solid var(--line);border-radius:999px;color:var(--muted);font-size:8px}.v4-session-main{margin-top:11px;padding-top:10px;border-top:1px solid rgba(255,255,255,.055);font-size:11px;line-height:1.55;color:#d3d7dc}.v4-session-why{margin-top:10px;color:var(--muted);font-size:10px;line-height:1.55}.v4-session-why strong{color:var(--text)}

.v4-stat-grid { display:grid; grid-template-columns:repeat(4,1fr); gap:12px; }
.v4-stat { padding:17px; border:1px solid var(--line); border-radius:18px; background:rgba(255,255,255,.018); text-align:center; }
.v4-stat-label { color:var(--muted); font-size:9px; font-weight:700; letter-spacing:.1em; text-transform:uppercase; }.v4-stat-value{margin-top:5px;font-size:29px;font-weight:600;letter-spacing:-.045em}.v4-stat-sub{margin-top:4px;color:var(--muted-2);font-size:8px}
.v4-zone { display:inline-flex;margin-top:6px;padding:3px 7px;border-radius:999px;border:1px solid var(--line);font-size:8px;font-weight:700;text-transform:uppercase;letter-spacing:.07em}.v4-zone.green{color:var(--green);border-color:rgba(37,212,122,.35)}.v4-zone.red{color:var(--red);border-color:rgba(255,66,84,.35)}.v4-zone.grey{color:#c2c7ce}
.v4-details { margin-top:13px; border:1px solid var(--line); border-radius:16px; background:rgba(255,255,255,.015); overflow:hidden; }
.v4-details summary { list-style:none; cursor:pointer; padding:13px 15px; font-size:12px; font-weight:650; display:flex; justify-content:space-between; align-items:center; }.v4-details summary::-webkit-details-marker{display:none}.v4-details summary::after{content:'+';color:var(--muted);font-size:18px}.v4-details[open] summary::after{content:'–'}.v4-details p{margin:0;padding:0 15px 15px;color:#c2c7ce;font-size:12px;line-height:1.65}

.v4-health-detail { display:grid; grid-template-columns:repeat(4,1fr); gap:12px; }
.v4-health-cell { padding:16px;border:1px solid var(--line);border-radius:18px;background:rgba(255,255,255,.018); }.v4-health-cell span{display:block;color:var(--muted);font-size:9px;text-transform:uppercase;letter-spacing:.1em}.v4-health-cell strong{display:block;margin-top:4px;font-size:25px;letter-spacing:-.04em}

.v4-power-list { display:grid; gap:10px; }.v4-power-row{display:grid;grid-template-columns:55px 1fr 64px;gap:10px;align-items:center}.v4-power-label{color:var(--muted);font-size:9px}.v4-power-track{height:10px;border-radius:999px;background:#272c33;overflow:hidden}.v4-power-fill{height:100%;border-radius:999px;background:linear-gradient(90deg,var(--cyan),var(--purple));width:0;transition:width 1s ease}.v4-power-value{text-align:right;font-size:11px;font-weight:650}

.v4-season-grid { display:grid; grid-template-columns:.7fr 1.3fr; gap:18px; align-items:center; }
.v4-season-donut { position:relative; width:180px; aspect-ratio:1; margin:auto; }.v4-season-donut svg{width:100%;height:100%;transform:rotate(-90deg)}.v4-season-track,.v4-season-low,.v4-season-mod,.v4-season-high{fill:none;stroke-width:15}.v4-season-track{stroke:#272c33}.v4-season-low{stroke:var(--green);stroke-linecap:round}.v4-season-mod{stroke:var(--orange)}.v4-season-high{stroke:var(--red)}.v4-season-center{position:absolute;inset:0;display:flex;align-items:center;justify-content:center;flex-direction:column}.v4-season-center strong{font-size:34px;letter-spacing:-.05em}.v4-season-center span{color:var(--muted);font-size:8px;text-transform:uppercase;letter-spacing:.1em}
.v4-zonebar { display:flex;height:14px;border-radius:999px;overflow:hidden;background:#272c33;margin-bottom:12px }.v4-zonebar > span:nth-child(1){background:var(--green)}.v4-zonebar > span:nth-child(2){background:var(--orange)}.v4-zonebar > span:nth-child(3){background:var(--red)}
.v4-season-legend { display:grid; gap:7px; }.v4-season-line{display:flex;justify-content:space-between;gap:12px;padding:8px 10px;border:1px solid var(--line);border-radius:12px;font-size:10px}.v4-season-line span{color:var(--muted)}

.v4-export { display:flex; justify-content:flex-end; gap:10px; margin-top:18px; }
.v4-build { position:fixed; right:10px; bottom:7px; color:rgba(255,255,255,.25); font-family:var(--brand); font-size:15px; line-height:1; pointer-events:none; z-index:30; }
.no-print {}

.v4-login-shell { min-height:100vh; display:grid; place-items:center; padding:24px; }
.v4-login-card { width:min(390px,100%); padding:28px; text-align:center; }
.v4-login-logo { width:180px; display:block; margin:0 auto 12px; }.v4-login-card h1{margin:0 0 16px;font-size:28px;letter-spacing:-.04em}.v4-login-card input{width:100%;height:52px;border:1px solid var(--line);border-radius:14px;background:#090b0e;color:var(--text);padding:0 14px;outline:none}.v4-login-card button{width:100%;height:50px;margin-top:10px;background:linear-gradient(135deg,#57dfec,#28b8ca);color:#071013;border:none;border-radius:14px;font-weight:700}

@media (max-width:1100px) {
  .v4-controls{grid-template-columns:1fr 1fr}.v4-control:last-child{grid-column:1/-1;min-height:auto}.v4-hero-grid{grid-template-columns:1fr}.v4-clock-card{grid-template-columns:200px 1fr}.v4-metric-grid{grid-template-columns:repeat(2,1fr)}.v4-session-grid{grid-template-columns:1fr 1fr}.v4-session:last-child{grid-column:1/-1}.v4-stat-grid,.v4-health-detail{grid-template-columns:repeat(2,1fr)}
}
@media (max-width:720px) {
  .v4-shell{width:min(100% - 20px,1440px);padding-top:12px}.v4-topbar{align-items:flex-start}.v4-brand{font-size:31px}.v4-top-actions{gap:6px}.v4-pill{display:none}.v4-hero{padding:20px 15px 22px}.v4-logo{width:175px}.v4-title{font-size:43px}.v4-controls{grid-template-columns:1fr}.v4-control{min-height:0;padding:18px}.v4-feeling-grid{grid-template-columns:repeat(5,1fr)}.v4-feeling-btn{aspect-ratio:auto;height:42px}.v4-clock-card{grid-template-columns:1fr;padding:19px}.v4-clock-visual{width:185px}.v4-slot-grid{grid-template-columns:1fr}.v4-next-slot{flex-direction:column}.v4-metric-grid,.v4-readiness-grid,.v4-session-grid,.v4-stat-grid,.v4-health-detail,.v4-season-grid{grid-template-columns:1fr}.v4-session:last-child{grid-column:auto}.v4-readiness-card{align-items:flex-start}.v4-week-memory{flex-direction:column}.v4-section-card,.v4-energy-card,.v4-coach-call,.v4-week{padding:18px}.v4-section-head{align-items:flex-start;flex-direction:column;gap:5px}.v4-export{justify-content:stretch}.v4-export .v4-btn{flex:1}.v4-clock-preview{grid-template-columns:auto auto}.v4-clock-preview small{grid-column:1/-1;justify-self:start;text-align:left}.v4-chat-form{grid-template-columns:1fr}.v4-season-donut{width:160px}
}

@media print {
  @page { size:A4; margin:10mm; }
  * { -webkit-print-color-adjust:exact !important; print-color-adjust:exact !important; }
  html,body { background:#08090b !important; color:#f5f7fa !important; }
  body { font-size:10pt; }
  .v4-shell { width:100%; max-width:none; padding:0; margin:0; }
  .no-print,.v4-controls,.v4-top-actions,.v4-preview-banner,.v4-export,.v4-build { display:none !important; }
  .v4-topbar { margin-bottom:6mm; }
  .v4-brand { font-size:24pt; }
  .v4-hero { padding:7mm; margin-bottom:6mm; box-shadow:none; background:#111318 !important; }
  .v4-logo { width:42mm; }
  .v4-title { font-size:30pt; }
  .v4-dashboard { gap:5mm; }
  .v4-card,.v4-section-card,.v4-session,.v4-metric,.v4-stat,.v4-health-cell,.v4-details { break-inside:avoid; page-break-inside:avoid; box-shadow:none !important; background:#111318 !important; border-color:#3b414b !important; }
  .v4-hero-grid,.v4-readiness-grid,.v4-season-grid { grid-template-columns:1fr 1fr; }
  .v4-clock-card { grid-template-columns:45mm 1fr; padding:5mm; }
  .v4-clock-visual { width:42mm; }
  .v4-energy-card { padding:5mm; }
  .v4-energy-gauge { width:72mm; }
  .v4-metric-grid { grid-template-columns:repeat(4,1fr); gap:3mm; }
  .v4-metric { padding:3mm; }
  .v4-ring { width:20mm; }
  .v4-session-grid { grid-template-columns:repeat(3,1fr); gap:3mm; }
  .v4-session { padding:4mm; }
  .v4-stat-grid,.v4-health-detail { grid-template-columns:repeat(4,1fr); gap:3mm; }
  .v4-section-card,.v4-coach-call,.v4-week { padding:5mm; }
  .v4-details p { display:block !important; }
  a[href]::after { content:none !important; }
}
"""

LOGIN_PAGE = """
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Amatic+SC:wght@400;700&family=Parkinsans:wght@400;500;600;700&display=swap" rel="stylesheet">
  <title>The Gluten Free Cyclist · The Lab</title>
  <link rel="icon" type="image/png" href="data:image/png;base64,{{ favicon }}">
  <style>{{ css }}</style>
</head>
<body>
  <main class="v4-login-shell">
    <section class="v4-card v4-login-card">
      <img class="v4-login-logo" src="data:image/png;base64,{{ logo }}" alt="The Gluten Free Cyclist Lab">
      <h1>Welcome back</h1>
      <form method="post">
        <input type="password" name="password" placeholder="Password" autofocus required>
        <button type="submit">Enter The Lab</button>
      </form>
      {% if error %}<div class="v4-error">{{ error }}</div>{% endif %}
    </section>
  </main>
</body>
</html>
"""

HOME_PAGE = """
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Amatic+SC:wght@400;700&family=Parkinsans:wght@400;500;600;700&display=swap" rel="stylesheet">
  <title>The Gluten Free Cyclist · The Lab</title>
  <link rel="icon" type="image/png" href="data:image/png;base64,{{ favicon }}">
  <style>{{ css }}</style>
</head>
<body>
  <main class="v4-shell">
    <header class="v4-topbar">
      <div class="v4-brand">The Gluten Free Cyclist</div>
      <div class="v4-top-actions no-print">
        <span class="v4-pill">Live · Europe/Rome</span>
        <a class="v4-logout" href="{{ url_for('logout') }}">Log out</a>
      </div>
    </header>

    <section class="v4-card v4-hero">
      <img class="v4-logo" src="data:image/png;base64,{{ logo }}" alt="The Gluten Free Cyclist Lab">
      <h1 class="v4-title">Health Snapshot</h1>
      <div class="v4-kicker">YOUR DAILY TRAINING DESK</div>
      <p class="v4-subtitle">Last {{ days }} days for recovery · {{ season_days }} days for training context · Intervals.icu + AI coach</p>
    </section>

    {% if is_preview %}
    <div class="v4-preview-banner">UI PREVIEW · sample data only · no Intervals.icu request · no Claude call <a href="{{ url_for('home') }}">Back to live home</a></div>
    {% endif %}

    <section class="v4-controls no-print">
      <article class="v4-card v4-control">
        <div class="v4-control-head"><span class="v4-icon">💬</span><h2 class="v4-control-title">Coach Chat</h2></div>
        <p class="v4-copy">Tell the coach anything that should change today’s interpretation or the next sessions.</p>
        <form method="post" action="{{ url_for('ask') }}" id="chat-form" class="v4-chat-form">
          <input class="v4-input" type="text" name="question" placeholder="e.g. Legs feel unusually heavy today" required {% if is_preview %}disabled{% endif %}>
          <button class="v4-btn v4-btn-cyan" type="submit" id="chat-btn" {% if is_preview %}disabled{% endif %}>Send</button>
        </form>
        {% if chat_error %}<div class="v4-error">{{ chat_error }}</div>{% endif %}
        {% if chat_answer %}<div class="v4-chat-ok">{{ chat_answer }}</div>{% endif %}
        {% if notes %}<div class="v4-notes">{% for n in notes|reverse %}<p class="v4-note"><span class="v4-note-date">{{ n.date }}</span>{{ n.text }}</p>{% endfor %}</div>{% endif %}
      </article>

      <article class="v4-card v4-control">
        <div class="v4-control-head"><span class="v4-icon">📋</span><h2 class="v4-control-title">Daily Check-In</h2></div>
        <p class="v4-copy">How do you feel right now? Your own signal sits beside the wearable data.</p>
        {% if latest_feeling %}<div class="v4-feeling-latest"><span class="v4-feeling-dot"></span>Latest check-in: <strong>{{ latest_feeling.value }}/10</strong></div>{% endif %}
        <form method="post" action="{{ url_for('log_feeling') }}" class="v4-feeling-grid">
          {% for n in range(1,11) %}<button class="v4-feeling-btn" type="submit" name="feeling" value="{{ n }}" {% if is_preview %}disabled{% endif %}>{{ n }}</button>{% endfor %}
        </form>
        <div class="v4-feeling-scale"><span>1 · terrible</span><span>5–6 · neutral</span><span>10 · amazing</span></div>
      </article>

      <article class="v4-card v4-control" id="snapshot-card">
        <div class="v4-control-head"><span class="v4-icon">⚡</span><h2 class="v4-control-title">Snapshot Status</h2></div>
        <div class="v4-status-box">
          <div class="v4-ready-row"><span class="v4-live-dot"></span><span class="v4-ready">Ready</span></div>
          <div class="v4-copy" style="margin:0;">Pull fresh Intervals.icu data, then let the coach decide what comes next.</div>
          <div class="v4-clock-preview"><span>COACH CLOCK</span><strong>{{ clock_preview.time }}</strong><small>{{ clock_preview.phase }}</small></div>
          <div class="v4-status-actions">
            {% if is_preview %}
            <a class="v4-preview-link" href="{{ url_for('home') }}">Back to live home</a>
            <button class="v4-btn v4-btn-orange" style="width:100%;opacity:.55;cursor:not-allowed;" type="button" disabled>Generate Snapshot · disabled in preview</button>
            {% else %}
            <a class="v4-preview-link" href="{{ url_for('preview') }}">UI Preview · free</a>
            <form method="post" action="{{ url_for('analyze') }}" id="snapshot-form">
              <button class="v4-btn v4-btn-orange" style="width:100%;" type="submit" id="snapshot-btn">Generate Snapshot</button>
              <div class="loading-track" id="loading-track"><div class="loading-fill"></div></div>
              <p class="loading-label" id="loading-label"></p>
            </form>
            {% endif %}
          </div>
        </div>
      </article>
    </section>

    {% if error %}<div class="v4-error">{{ error }}</div>{% endif %}

    {% if data %}
    <section class="v4-dashboard">
      <div class="v4-hero-grid">
        <article class="v4-card v4-clock-card">
          <div class="v4-clock-visual">
            <svg class="v4-clock-svg" viewBox="0 0 180 180" aria-label="Coach Clock">
              <circle class="v4-clock-track" cx="90" cy="90" r="68" pathLength="100"/>
              <circle class="v4-clock-am" cx="90" cy="90" r="68" pathLength="100"/>
              <circle class="v4-clock-mid" cx="90" cy="90" r="68" pathLength="100"/>
              <circle class="v4-clock-pm" cx="90" cy="90" r="68" pathLength="100"/>
              <circle class="v4-clock-marker" cx="{{ data.coach_clock.marker_x }}" cy="{{ data.coach_clock.marker_y }}" r="6"/>
            </svg>
            <div class="v4-clock-center"><div class="v4-clock-time">{{ data.coach_clock.time }}</div><div class="v4-clock-phase">{{ data.coach_clock.phase }}</div><div class="v4-clock-date">{{ data.coach_clock.date_label }}</div></div>
          </div>
          <div class="v4-clock-copy">
            <div class="v4-kicker" style="margin:0 0 7px;">COACH CLOCK · EUROPE/ROME</div>
            <h3>{{ data.coach_clock.headline }}</h3>
            <p>{{ data.coach_clock.explanation }}</p>
            <div class="v4-slot-grid">
              <div class="v4-slot {{ data.coach_clock.am_status_class }}"><span>Morning · before 12</span><strong>{{ data.coach_clock.am_status }}</strong></div>
              <div class="v4-slot {{ data.coach_clock.pm_status_class }}"><span>Evening · after 17</span><strong>{{ data.coach_clock.pm_status }}</strong></div>
            </div>
            <div class="v4-next-slot"><span>Next decision slot</span><strong>{{ data.coach_clock.next_slot_label }}</strong></div>
            {% if data.coach_clock.today_activities_text %}<div class="v4-today">Logged today: {{ data.coach_clock.today_activities_text }}</div>{% endif %}
          </div>
        </article>

        <article class="v4-card v4-energy-card">
          <h3>Energy Bank</h3>
          <p>Readiness from Form, Fatigue and recent sleep. Deterministic: Claude does not choose this score.</p>
          <div class="v4-energy-gauge">
            <svg class="v4-energy-svg" viewBox="0 0 200 112" aria-label="Energy Bank gauge">
              <path class="v4-energy-seg v4-energy-s1" d="M18 94 A82 82 0 0 1 39 39"/>
              <path class="v4-energy-seg v4-energy-s2" d="M48 31 A82 82 0 0 1 78 16"/>
              <path class="v4-energy-seg v4-energy-s3" d="M89 13 A82 82 0 0 1 111 13"/>
              <path class="v4-energy-seg v4-energy-s4" d="M122 16 A82 82 0 0 1 152 31"/>
              <path class="v4-energy-seg v4-energy-s5" d="M161 39 A82 82 0 0 1 182 94"/>
              <circle class="v4-energy-halo" cx="{{ data.marker_x }}" cy="{{ data.marker_y }}" r="7"/>
              <circle class="v4-energy-marker" cx="{{ data.marker_x }}" cy="{{ data.marker_y }}" r="4.3"/>
            </svg>
            <div class="v4-energy-score"><strong>{{ data.energy_score }}</strong><span>/ 100</span></div>
          </div>
          <div class="v4-badge {{ data.energy_zone }}">{{ data.energy_label }}</div>
          <div class="v4-wearables">{% if data.latest_readiness is not none %}<span>Wearable readiness <strong>{{ data.latest_readiness }}</strong></span>{% endif %}{% if data.latest_spo2 is not none %}<span>SpO₂ <strong>{{ data.latest_spo2 }}%</strong></span>{% endif %}</div>
          {% if data.recent_trend %}
          <div class="v4-trend"><div class="v4-trend-head"><strong>Last 5 days · Form vs your norm</strong><span>Near zero = normal for you</span></div><div class="v4-trend-grid">{% for d in data.recent_trend %}<div class="v4-trend-item"><div class="v4-trend-track"><div class="v4-trend-fill {{ d.zone }}" data-height="{{ [((d.tsb + 30) / 60 * 100), 7]|max }}" style="height:7%;"></div></div><div class="v4-trend-delta">{% if d.delta is not none %}{{ "%+d"|format(d.delta) }}{% else %}{{ d.tsb }}{% endif %}</div><div class="v4-trend-day">{{ d.weekday }}</div></div>{% endfor %}</div></div>
          {% endif %}
        </article>
      </div>

      <div class="v4-metric-grid">
        <article class="v4-card v4-metric"><div class="v4-metric-label">Resting HR</div>{% if data.health_rings.rhr %}<div class="v4-ring"><svg viewBox="0 0 100 100"><circle class="v4-ring-track" cx="50" cy="50" r="40" pathLength="100"/><circle class="v4-ring-progress {{ data.health_rings.rhr.color }}" cx="50" cy="50" r="40" pathLength="100" stroke-dasharray="{{ data.health_rings.rhr.pct }} 100"/></svg><div class="v4-ring-center"><div class="v4-ring-value">{{ data.latest_rhr }}</div><div class="v4-ring-sub">bpm</div></div></div><div class="v4-metric-status {{ data.health_rings.rhr.color }}">{{ data.health_rings.rhr.status }}</div>{% else %}<div class="v4-ring-value" style="margin-top:28px;">{{ data.latest_rhr }}</div>{% endif %}</article>
        <article class="v4-card v4-metric"><div class="v4-metric-label">HRV</div>{% if data.health_rings.hrv %}<div class="v4-ring"><svg viewBox="0 0 100 100"><circle class="v4-ring-track" cx="50" cy="50" r="40" pathLength="100"/><circle class="v4-ring-progress {{ data.health_rings.hrv.color }}" cx="50" cy="50" r="40" pathLength="100" stroke-dasharray="{{ data.health_rings.hrv.pct }} 100"/></svg><div class="v4-ring-center"><div class="v4-ring-value">{{ data.latest_hrv }}</div><div class="v4-ring-sub">ms</div></div></div><div class="v4-metric-status {{ data.health_rings.hrv.color }}">{{ data.health_rings.hrv.status }}</div>{% else %}<div class="v4-ring-value" style="margin-top:28px;">{{ data.latest_hrv }}</div>{% endif %}</article>
        <article class="v4-card v4-metric"><div class="v4-metric-label">Sleep</div>{% if data.health_rings.sleep %}<div class="v4-ring"><svg viewBox="0 0 100 100"><circle class="v4-ring-track" cx="50" cy="50" r="40" pathLength="100"/><circle class="v4-ring-progress {{ data.health_rings.sleep.color }}" cx="50" cy="50" r="40" pathLength="100" stroke-dasharray="{{ data.health_rings.sleep.pct }} 100"/></svg><div class="v4-ring-center"><div class="v4-ring-value">{{ data.avg_sleep }}</div></div></div><div class="v4-metric-status {{ data.health_rings.sleep.color }}">{{ data.health_rings.sleep.status }}</div>{% else %}<div class="v4-ring-value" style="margin-top:28px;">{{ data.avg_sleep }}</div>{% endif %}</article>
        <article class="v4-card v4-metric"><div class="v4-metric-label">Sleep Quality</div><div class="v4-ring"><svg viewBox="0 0 100 100"><circle class="v4-ring-track" cx="50" cy="50" r="40" pathLength="100"/><circle class="v4-ring-progress cyan" cx="50" cy="50" r="40" pathLength="100" stroke-dasharray="{{ data.latest_sleep_score if data.latest_sleep_score is not none else 0 }} 100"/></svg><div class="v4-ring-center"><div class="v4-sleep-quality">{{ data.sleep_quality_label }}</div><div class="v4-quality-copy">{{ data.sleep_quality_text }}</div></div></div>{% if data.latest_sleep_score is not none %}<div class="v4-quality-copy">Sleep score {{ data.latest_sleep_score }}</div>{% endif %}</article>
      </div>

      <div class="v4-readiness-grid">
        <article class="v4-card v4-readiness-card"><div class="v4-ring"><svg viewBox="0 0 100 100"><circle class="v4-ring-track" cx="50" cy="50" r="40" pathLength="100"/><circle class="v4-ring-progress {{ data.race_readiness_zone }}" cx="50" cy="50" r="40" pathLength="100" stroke-dasharray="{{ data.race_readiness_score }} 100"/></svg><div class="v4-ring-center"><div class="v4-ring-value">{{ data.race_readiness_score }}</div><div class="v4-ring-sub">/100</div></div></div><div class="v4-readiness-copy"><h3>Race Readiness</h3><strong>{{ data.race_readiness_label }}</strong><p>{{ data.race_readiness_reason }}</p></div></article>
        <article class="v4-card v4-last-night"><span>Last night</span><strong>{{ data.latest_sleep_duration }}</strong><p>Sleep {{ data.sleep_quality_label }}{% if data.latest_sleep_score is not none %} · score {{ data.latest_sleep_score }}{% endif %}{% if data.latest_sleeping_hr is not none %} · sleeping HR {{ data.latest_sleeping_hr }} bpm{% endif %}</p></article>
      </div>

      <article class="v4-card v4-coach-call"><div class="v4-coach-kicker">COACH CALL</div><h2>What I would do from here</h2><p>{{ data.recommendation }}</p></article>

      <article class="v4-card v4-week">
        <div class="v4-section-head"><div><h2 class="v4-section-title">Next 3 Sessions</h2><p class="v4-section-note">Built from snapshot time, today’s activities and what you already completed this week.</p></div></div>
        <div class="v4-week-memory"><div class="v4-week-label">This week</div><div class="v4-week-chips">{% if data.week_memory and data.week_memory.activities %}{% for a in data.week_memory.activities %}<span class="v4-week-chip {{ 'hard' if a.hard else '' }}"><strong>{{ a.day_short }}</strong> {{ a.family_short }}</span>{% endfor %}{% else %}<span class="v4-week-chip">No completed sessions found yet.</span>{% endif %}</div>{% if data.week_memory and data.week_memory.hard_summary %}<div class="v4-week-note">Quality: {{ data.week_memory.hard_summary }}</div>{% endif %}</div>
        <div class="v4-session-grid">{% for s in data.next_sessions %}<article class="v4-card v4-session {{ s.intensity_class }}"><div class="v4-session-slot">{{ s.slot }}</div><h3>{{ s.title }}</h3><div class="v4-session-meta"><span class="v4-session-pill">{{ s.duration }}</span><span class="v4-session-pill">{{ s.intensity }}</span></div><div class="v4-session-main">{{ s.main_set }}</div><div class="v4-session-why"><strong>Why:</strong> {{ s.why }}</div></article>{% endfor %}</div>
      </article>

      <article class="v4-card v4-section-card">
        <div class="v4-section-head"><div><h2 class="v4-section-title">Training</h2><p class="v4-section-note">Last {{ days }} days</p></div></div>
        <div class="v4-stat-grid">
          <div class="v4-stat"><div class="v4-stat-label">Fitness · CTL</div><div class="v4-stat-value">{{ data.ctl }}</div><div class="v4-zone {{ data.fitness_zone }}">{{ data.fitness_zone }}</div></div>
          <div class="v4-stat"><div class="v4-stat-label">Fatigue · ATL</div><div class="v4-stat-value">{{ data.atl }}</div><div class="v4-zone {{ data.fatigue_zone }}">{{ data.fatigue_zone }}</div></div>
          <div class="v4-stat"><div class="v4-stat-label">Form · TSB</div><div class="v4-stat-value">{{ data.tsb }}</div><div class="v4-zone {{ data.form_zone }}">{{ data.form_zone }}</div></div>
          <div class="v4-stat"><div class="v4-stat-label">Avg Training Calories</div><div class="v4-stat-value">{{ data.avg_daily_calories }}</div><div class="v4-stat-sub">kcal / training day</div></div>
        </div>
        <details class="v4-details"><summary>Training Load</summary><p>{{ data.training_load }}</p></details>
      </article>

      <article class="v4-card v4-section-card">
        <div class="v4-section-head"><div><h2 class="v4-section-title">Health</h2><p class="v4-section-note">Most recent readings</p></div></div>
        <div class="v4-health-detail">
          <div class="v4-health-cell"><span>Resting HR</span><strong>{{ data.latest_rhr }}{% if data.trend_arrows.rhr %} {{ data.trend_arrows.rhr.arrow }}{% endif %}</strong></div>
          <div class="v4-health-cell"><span>HRV</span><strong>{{ data.latest_hrv }}{% if data.trend_arrows.hrv %} {{ data.trend_arrows.hrv.arrow }}{% endif %}</strong></div>
          <div class="v4-health-cell"><span>Avg Sleep</span><strong>{{ data.avg_sleep }}{% if data.trend_arrows.sleep %} {{ data.trend_arrows.sleep.arrow }}{% endif %}</strong></div>
          <div class="v4-health-cell"><span>Weight</span><strong>{{ data.latest_weight }}{% if data.trend_arrows.weight %} {{ data.trend_arrows.weight.arrow }}{% endif %}</strong></div>
        </div>
        <details class="v4-details"><summary>Fatigue Signals</summary><p>{{ data.fatigue_signals }}</p></details>
      </article>

      <article class="v4-card v4-section-card">
        <div class="v4-section-head"><div><h2 class="v4-section-title">Power Curve</h2><p class="v4-section-note">Best efforts · last 42 days</p></div></div>
        {% if data.best_watts %}<div class="v4-power-list">{% for p in data.best_watts %}<div class="v4-power-row"><div class="v4-power-label">{{ p.label }}</div><div class="v4-power-track"><div class="v4-power-fill" data-width="{{ p.pct }}"></div></div><div class="v4-power-value">{{ p.watts }} W</div></div>{% endfor %}</div>{% else %}<p class="v4-section-note">Power curve data is unavailable right now.</p>{% endif %}
      </article>

      <article class="v4-card v4-section-card">
        <div class="v4-section-head"><div><h2 class="v4-section-title">Season</h2><p class="v4-section-note">Last {{ season_days }} days</p></div><div class="v4-section-note">{{ data.season_hours }} h · load {{ data.season_total_load }}</div></div>
        <div class="v4-season-grid">
          {% if data.zone_low_pct != 'n/a' %}<div class="v4-season-donut"><svg viewBox="0 0 100 100"><circle class="v4-season-track" cx="50" cy="50" r="38" pathLength="100"/><circle class="v4-season-low" cx="50" cy="50" r="38" pathLength="100" stroke-dasharray="{{ data.zone_low_pct }} 100"/><circle class="v4-season-mod" cx="50" cy="50" r="38" pathLength="100" stroke-dasharray="{{ data.zone_mod_pct }} 100" stroke-dashoffset="-{{ data.zone_low_pct }}"/><circle class="v4-season-high" cx="50" cy="50" r="38" pathLength="100" stroke-dasharray="{{ data.zone_high_pct }} 100" stroke-dashoffset="-{{ data.zone_low_pct + data.zone_mod_pct }}"/></svg><div class="v4-season-center"><strong>{{ data.zone_low_pct }}%</strong><span>low intensity</span></div></div>{% endif %}
          <div><div class="v4-zonebar"><span style="width:{{ data.zone_low_pct }}%;"></span><span style="width:{{ data.zone_mod_pct }}%;"></span><span style="width:{{ data.zone_high_pct }}%;"></span></div><div class="v4-season-legend"><div class="v4-season-line"><span>Low intensity</span><strong style="color:var(--green)">{{ data.zone_low_pct }}%</strong></div><div class="v4-season-line"><span>Moderate</span><strong style="color:var(--orange)">{{ data.zone_mod_pct }}%</strong></div><div class="v4-season-line"><span>High intensity</span><strong style="color:var(--red)">{{ data.zone_high_pct }}%</strong></div></div></div>
        </div>
        <details class="v4-details"><summary>Training Distribution</summary><p>{{ data.season_distribution }}</p></details>
        <details class="v4-details"><summary>Seasonal Outlook</summary><p>{{ data.season_outlook }}</p></details>
      </article>

      <div class="v4-export no-print"><a class="v4-btn v4-btn-ghost" href="{{ url_for('preview') }}">UI Preview</a><button class="v4-btn v4-btn-cyan" type="button" id="pdf-btn">Print / Save PDF</button></div>
    </section>
    {% endif %}
  </main>
  <div class="v4-build">{{ app_version }}</div>

  <script>
  (function(){
    document.querySelectorAll('.v4-power-fill[data-width]').forEach(function(el){ setTimeout(function(){ el.style.width = el.getAttribute('data-width') + '%'; },120); });
    document.querySelectorAll('.v4-trend-fill[data-height]').forEach(function(el){ setTimeout(function(){ el.style.height = Math.min(100, parseFloat(el.getAttribute('data-height')) || 7) + '%'; },120); });
    var pdf=document.getElementById('pdf-btn'); if(pdf){ pdf.addEventListener('click',function(){ window.print(); }); }
    var form=document.getElementById('snapshot-form'); if(form){ form.addEventListener('submit',function(){ var btn=document.getElementById('snapshot-btn'), track=document.getElementById('loading-track'), fill=track?track.querySelector('.loading-fill'):null, label=document.getElementById('loading-label'); if(btn){btn.disabled=true;btn.textContent='Analyzing…';} if(track)track.style.display='block'; if(label){label.style.display='block';label.textContent='Pulling Intervals.icu data…';} var pct=5; if(fill){fill.style.width=pct+'%'; setInterval(function(){ if(pct<92){pct+=(92-pct)*.08;fill.style.width=pct+'%';}},250);} }); }
    var chat=document.getElementById('chat-form'); if(chat){ chat.addEventListener('submit',function(){ var b=document.getElementById('chat-btn'); if(b){b.disabled=true;b.textContent='Thinking…';} }); }
  })();
  </script>
</body>
</html>
"""

NOTES_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "coach_notes.json")
MAX_NOTES = 30  # keep the file small; oldest notes drop off


def load_notes():
    if not os.path.exists(NOTES_FILE):
        return []
    try:
        with open(NOTES_FILE, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return []


def save_note(text):
    notes = load_notes()
    notes.append({"date": date.today().isoformat(), "text": text})
    notes = notes[-MAX_NOTES:]
    try:
        with open(NOTES_FILE, "w") as f:
            json.dump(notes, f)
    except OSError:
        pass
    return notes


FEELING_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "daily_feeling.json")
MAX_FEELINGS = 30


def load_feelings():
    if not os.path.exists(FEELING_FILE):
        return []
    try:
        with open(FEELING_FILE, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return []


def save_feeling(value):
    feelings = [f for f in load_feelings() if f.get("date") != date.today().isoformat()]
    feelings.append({"date": date.today().isoformat(), "value": value})
    feelings = feelings[-MAX_FEELINGS:]
    try:
        with open(FEELING_FILE, "w") as f:
            json.dump(feelings, f)
    except OSError:
        pass
    return feelings


def classify_feeling(value):
    if value >= 8:
        return "green"
    if value <= 3:
        return "red"
    return "grey"


def get_latest_feeling():
    feelings = load_feelings()
    if not feelings:
        return None
    latest = feelings[-1]
    return {"value": latest["value"], "color": classify_feeling(latest["value"])}


def require_login():
    return session.get("logged_in") is True


@app.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        if not APP_PASSWORD:
            error = "APP_PASSWORD is not configured on the server."
        elif request.form.get("password") == APP_PASSWORD:
            session["logged_in"] = True
            return redirect(url_for("home"))
        else:
            error = "Incorrect password."
    return render_template_string(LOGIN_PAGE, error=error, css=BASE_CSS, logo=LOGO_B64, favicon=FAVICON_B64)


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.route("/")
def home():
    if not require_login():
        return redirect(url_for("login"))
    return render_template_string(
        HOME_PAGE, days=DAYS_BACK, season_days=SEASON_DAYS_BACK,
        data=None, error=None, css=BASE_CSS, logo=LOGO_B64, favicon=FAVICON_B64,
        notes=load_notes(), chat_answer=None, chat_error=None,
        feelings=load_feelings(), latest_feeling=get_latest_feeling(),
        app_version=APP_VERSION, clock_preview=get_clock_preview(), is_preview=False,
    )


def get_intervals_headers():
    credentials = f"API_KEY:{ICU_API_KEY}"
    encoded = base64.b64encode(credentials.encode("utf-8")).decode("utf-8")
    return {"Authorization": f"Basic {encoded}"}


def fetch_power_curve_payload():
    headers = get_intervals_headers()
    url = (
        f"https://intervals.icu/api/v1/athlete/{ICU_ATHLETE_ID}/power-curves.json"
        f"?type=Ride&curves=42d"
    )
    resp = requests.get(url, headers=headers, timeout=30)
    resp.raise_for_status()
    return resp.json()


def extract_power_curve_points(payload):
    """The exact shape of this endpoint's response isn't officially documented.
    The real shape turned out to be a curve object with PARALLEL ARRAYS -
    e.g. {"secs": [5, 10, 15, ...], "watts": [900, 850, ...]} - rather than a
    list of {secs, watts} point dicts. Handle that first, and keep the
    point-list shape as a fallback in case a different curve type (e.g. "all")
    is structured differently."""
    array_results = []
    point_list_results = []

    def walk(node):
        if isinstance(node, dict):
            secs = node.get("secs")
            watts = node.get("watts")
            if watts is None:
                watts = node.get("power")
            if (
                isinstance(secs, list) and isinstance(watts, list)
                and len(secs) == len(watts) and len(secs) > 0
                and isinstance(secs[0], (int, float))
            ):
                array_results.append(
                    [{"secs": s, "watts": w} for s, w in zip(secs, watts) if w]
                )
            for v in node.values():
                walk(v)
        elif isinstance(node, list):
            if node and all(isinstance(i, dict) for i in node):
                keys0 = set(node[0].keys())
                if "secs" in keys0 and ("watts" in keys0 or "power" in keys0):
                    if isinstance(node[0].get("secs"), (int, float)):
                        point_list_results.append(node)
            for item in node:
                walk(item)

    walk(payload)
    if array_results:
        return max(array_results, key=len)
    return point_list_results[0] if point_list_results else None


def format_duration_label(secs):
    if secs < 60:
        return f"{secs}s"
    if secs < 3600:
        return f"{secs // 60}min"
    return f"{secs // 3600}h"


def best_watts_for_durations(points, target_secs_list):
    if not points:
        return []
    sorted_points = sorted(points, key=lambda p: p.get("secs", 0))
    results = []
    for target in target_secs_list:
        best = None
        for p in sorted_points:
            if p.get("secs", 0) <= target:
                best = p
            else:
                break
        if best is None:
            best = sorted_points[0]
        watts = best.get("watts") or best.get("power")
        if watts:
            results.append({"label": format_duration_label(target), "watts": round(watts)})

    if results:
        max_watts = max(r["watts"] for r in results)
        for r in results:
            r["pct"] = round(100 * r["watts"] / max_watts) if max_watts else 0
    return results


def get_best_watts():
    try:
        payload = fetch_power_curve_payload()
        points = extract_power_curve_points(payload)
        result = best_watts_for_durations(points, [5, 15, 60, 300, 1200, 3600])
        debug = None
        if not result:
            preview = json.dumps(payload)[:500]
            debug = "Power curve payload preview: {}".format(preview)
        return result, debug
    except requests.HTTPError as e:
        return [], "Power curve request failed: {}".format(e)
    except Exception as e:
        return [], "Power curve error: {}".format(e)


def fetch_intervals_data():
    """Fetch SEASON_DAYS_BACK days of activities (with zone times) AND
    wellness. Wellness needs the longer window too now, so we can learn the
    athlete's own normal range for Form/Fatigue instead of judging them
    against generic fixed thresholds. The recent-window subsets are simply
    the tail end of these season-length lists."""
    season_oldest = (date.today() - timedelta(days=SEASON_DAYS_BACK)).isoformat()
    recent_oldest = (date.today() - timedelta(days=DAYS_BACK)).isoformat()
    newest = date.today().isoformat()
    headers = get_intervals_headers()

    activities_fields = (
        "id,name,type,start_date_local,moving_time,elapsed_time,distance,"
        "icu_training_load,icu_weighted_avg_watts,average_watts,average_heartrate,"
        "icu_zone_times,calories"
    )
    activities_url = (
        f"https://intervals.icu/api/v1/athlete/{ICU_ATHLETE_ID}/activities"
        f"?oldest={season_oldest}&newest={newest}&fields={activities_fields}"
    )

    wellness_fields = "id,restingHR,hrv,sleepSecs,sleepScore,sleepQuality,avgSleepingHR,weight,ctl,atl,rampRate,comments,readiness,spO2"
    wellness_url = (
        f"https://intervals.icu/api/v1/athlete/{ICU_ATHLETE_ID}/wellness"
        f"?oldest={season_oldest}&newest={newest}&fields={wellness_fields}"
    )

    act_resp = requests.get(activities_url, headers=headers, timeout=30)
    act_resp.raise_for_status()
    wel_resp = requests.get(wellness_url, headers=headers, timeout=30)
    wel_resp.raise_for_status()

    season_activities = act_resp.json()
    season_activities = [
        a for a in season_activities if a.get("start_date_local", "")[:10] >= season_oldest
    ]
    recent_activities = [
        a for a in season_activities if a.get("start_date_local", "")[:10] >= recent_oldest
    ]

    season_wellness = wel_resp.json()
    season_wellness = [
        w for w in season_wellness if w.get("id", "") >= season_oldest
    ]
    recent_wellness = [w for w in season_wellness if w.get("id", "") >= recent_oldest]

    return recent_activities, season_activities, recent_wellness, season_wellness


def percentile(sorted_values, pct):
    """Simple linear-interpolation percentile, no numpy dependency."""
    if not sorted_values:
        return None
    if len(sorted_values) == 1:
        return sorted_values[0]
    k = (len(sorted_values) - 1) * pct
    f, c = int(k), min(int(k) + 1, len(sorted_values) - 1)
    if f == c:
        return sorted_values[f]
    return sorted_values[f] + (sorted_values[c] - sorted_values[f]) * (k - f)


def personal_form_thresholds(season_wellness, min_points=14):
    """The athlete's own p33/p67 TSB range over the season window, so Form is
    judged against their normal baseline instead of a generic cutoff."""
    tsb_values = sorted(
        w["ctl"] - w["atl"] for w in season_wellness
        if w.get("ctl") is not None and w.get("atl") is not None
    )
    if len(tsb_values) < min_points:
        return None
    return percentile(tsb_values, 0.33), percentile(tsb_values, 0.67)


def personal_form_median(season_wellness, min_points=14):
    """The athlete's own typical TSB, so day-to-day form can be shown as a
    small delta from what's normal FOR THEM instead of a scary absolute
    number that's just a side effect of training at chronic high load."""
    tsb_values = sorted(
        w["ctl"] - w["atl"] for w in season_wellness
        if w.get("ctl") is not None and w.get("atl") is not None
    )
    if len(tsb_values) < min_points:
        return None
    return percentile(tsb_values, 0.5)


def personal_fatigue_thresholds(season_wellness, min_points=14):
    """The athlete's own p33/p67 ATL:CTL ratio range over the season window."""
    ratios = sorted(
        w["atl"] / w["ctl"] for w in season_wellness
        if w.get("ctl") not in (None, 0) and w.get("atl") is not None
    )
    if len(ratios) < min_points:
        return None
    return percentile(ratios, 0.33), percentile(ratios, 0.67)


def classify_form(tsb, personal_thresholds=None):
    if tsb is None:
        return "grey"
    if personal_thresholds:
        p33, p67 = personal_thresholds
        if tsb >= p67:
            return "green"
        if tsb <= p33:
            return "red"
        return "grey"
    # Fallback generic thresholds - only used when there isn't enough
    # history yet to learn the athlete's own normal range.
    if tsb >= 5:
        return "green"
    if tsb <= -10:
        return "red"
    return "grey"


def classify_fatigue(atl, ctl, personal_thresholds=None):
    if atl is None or ctl is None or ctl == 0:
        return "grey"
    ratio = atl / ctl
    if personal_thresholds:
        p33, p67 = personal_thresholds
        if ratio <= p33:
            return "green"
        if ratio >= p67:
            return "red"
        return "grey"
    if ratio >= 1.15:
        return "red"
    if ratio <= 0.95:
        return "green"
    return "grey"


def classify_fitness_trend(wellness):
    ctl_values = [(w.get("id"), w.get("ctl")) for w in wellness if w.get("ctl") is not None]
    ctl_values.sort(key=lambda x: x[0])
    if len(ctl_values) < 2:
        return "grey"
    change = ctl_values[-1][1] - ctl_values[0][1]
    if change >= 2:
        return "green"
    if change <= -2:
        return "red"
    return "grey"


def bucket_zone_seconds(zone_seconds):
    """Given an ordered list of seconds-per-zone (easiest to hardest), bucket
    into Low / Moderate / High using common Coggan-style zone groupings."""
    n = len(zone_seconds)
    if n == 0:
        return 0, 0, 0
    if n == 3:
        low, mod, high = zone_seconds[0], zone_seconds[1], zone_seconds[2]
    elif n in (5, 6):
        low = sum(zone_seconds[0:2])
        mod = zone_seconds[2] if n == 5 else sum(zone_seconds[2:4])
        high = sum(zone_seconds[3:]) if n == 5 else sum(zone_seconds[4:])
    elif n == 7:
        low = sum(zone_seconds[0:2])
        mod = sum(zone_seconds[2:4])
        high = sum(zone_seconds[4:])
    else:
        third = max(1, n // 3)
        low = sum(zone_seconds[0:third])
        mod = sum(zone_seconds[third:2 * third])
        high = sum(zone_seconds[2 * third:])
    return low, mod, high


def compute_season_stats(season_activities):
    total_secs = 0
    low_secs = mod_secs = high_secs = 0
    total_load = 0

    for a in season_activities:
        total_secs += a.get("moving_time") or a.get("elapsed_time") or 0
        total_load += a.get("icu_training_load") or 0
        zt = a.get("icu_zone_times")
        if zt:
            secs_list = [z.get("secs", 0) for z in zt]
            low, mod, high = bucket_zone_seconds(secs_list)
            low_secs += low
            mod_secs += mod
            high_secs += high

    zone_total = low_secs + mod_secs + high_secs
    if zone_total > 0:
        low_pct = round(100 * low_secs / zone_total)
        mod_pct = round(100 * mod_secs / zone_total)
        high_pct = round(100 * high_secs / zone_total)
    else:
        low_pct = mod_pct = high_pct = None

    return {
        "season_hours": round(total_secs / 3600, 1),
        "season_total_load": round(total_load),
        "zone_low_pct": low_pct if low_pct is not None else "n/a",
        "zone_mod_pct": mod_pct if mod_pct is not None else "n/a",
        "zone_high_pct": high_pct if high_pct is not None else "n/a",
    }


def last_two_values(wellness, field):
    vals = [
        w[field] for w in sorted(wellness, key=lambda x: x.get("id", ""))
        if w.get(field) is not None
    ]
    if len(vals) < 2:
        return None, None
    return vals[-1], vals[-2]


def trend_arrow(current, previous, higher_is_better):
    """higher_is_better: True/False for a directional judgement, or None for
    a neutral metric where up/down isn't inherently good or bad."""
    if current is None or previous is None or current == previous:
        return None
    up = current > previous
    arrow = "▲" if up else "▼"
    if higher_is_better is None:
        color = "grey"
    else:
        good = up if higher_is_better else not up
        color = "green" if good else "red"
    return {"arrow": arrow, "color": color}


def compute_health_rings(latest_rhr, latest_hrv, avg_sleep_hours, trend_arrows):
    """Rough 0-100 fill percentages for the small Garmin-style ring gauges.
    These are visual approximations over sensible physiological ranges, not
    personalized thresholds."""

    def clamp(v):
        return max(0, min(100, v))

    def status_word(color):
        return {"green": "Good", "grey": "Typical", "red": "Low"}.get(color, "Typical")

    rings = {}

    if isinstance(latest_rhr, (int, float)):
        pct = clamp(round(100 - (latest_rhr - 40) / (80 - 40) * 100))
        arrow = trend_arrows.get("rhr")
        color = arrow["color"] if arrow else "grey"
        rings["rhr"] = {"pct": pct, "color": color, "status": status_word(color)}

    if isinstance(latest_hrv, (int, float)):
        pct = clamp(round((latest_hrv - 20) / (120 - 20) * 100))
        arrow = trend_arrows.get("hrv")
        color = arrow["color"] if arrow else "grey"
        rings["hrv"] = {"pct": pct, "color": color, "status": status_word(color)}

    if isinstance(avg_sleep_hours, (int, float)):
        pct = clamp(round(avg_sleep_hours / 9 * 100))
        arrow = trend_arrows.get("sleep")
        color = arrow["color"] if arrow else "grey"
        rings["sleep"] = {"pct": pct, "color": color, "status": status_word(color)}

    return rings


def compute_trend_arrows(wellness):
    rhr_latest, rhr_prev = last_two_values(wellness, "restingHR")
    hrv_latest, hrv_prev = last_two_values(wellness, "hrv")
    sleep_latest, sleep_prev = last_two_values(wellness, "sleepSecs")
    weight_latest, weight_prev = last_two_values(wellness, "weight")
    return {
        "rhr": trend_arrow(rhr_latest, rhr_prev, higher_is_better=False),
        "hrv": trend_arrow(hrv_latest, hrv_prev, higher_is_better=True),
        "sleep": trend_arrow(sleep_latest, sleep_prev, higher_is_better=True),
        "weight": trend_arrow(weight_latest, weight_prev, higher_is_better=None),
    }


def compute_recent_trend(wellness, n=5, form_thresholds=None, form_median=None):
    """Daily Form (TSB) for the last n days that have both CTL and ATL, for a
    quick at-a-glance trend next to the Energy Bank. Shown primarily as a
    delta from the athlete's own typical TSB, not the raw absolute number -
    for someone who trains at chronic high load, the raw number is nearly
    always a scary-looking double-digit negative even on a completely
    ordinary day."""
    daily = []
    for w in sorted(wellness, key=lambda x: x.get("id", "")):
        ctl, atl = w.get("ctl"), w.get("atl")
        if ctl is None or atl is None:
            continue
        tsb = round(ctl - atl, 1)
        try:
            weekday = date.fromisoformat(w["id"]).strftime("%a")
        except (ValueError, KeyError):
            weekday = w.get("id", "")[-2:]
        delta = round(tsb - form_median, 1) if form_median is not None else None
        daily.append({
            "date": w.get("id", ""), "weekday": weekday, "tsb": tsb, "delta": delta,
            "zone": classify_form(tsb, form_thresholds),
        })
    return daily[-n:]


def compute_energy_bank(form_zone, fatigue_zone, avg_sleep_hours):
    """A single 0-100 composite score combining Form, Fatigue and recent sleep.
    Deterministic, not AI-guessed, so it stays consistent snapshot to snapshot."""
    score = 50

    score += {"green": 25, "grey": 0, "red": -25}.get(form_zone, 0)
    score += {"green": 15, "grey": 0, "red": -15}.get(fatigue_zone, 0)

    if avg_sleep_hours is not None:
        if avg_sleep_hours >= 7.5:
            score += 10
        elif avg_sleep_hours < 6.5:
            score -= 10

    score = max(0, min(100, score))

    if score >= 65:
        label, zone = "Charged", "green"
    elif score >= 35:
        label, zone = "Balanced", "grey"
    else:
        label, zone = "Drained", "red"

    # Stable marker coordinates on the same semicircle used by the SVG gauge.
    # score 0 = left edge, score 100 = right edge.
    theta = math.pi - (score / 100.0) * math.pi
    marker_radius = 87
    marker_x = round(100 + marker_radius * math.cos(theta), 1)
    marker_y = round(95 - marker_radius * math.sin(theta), 1)

    return {
        "energy_score": score, "energy_label": label, "energy_zone": zone,
        "marker_x": marker_x, "marker_y": marker_y,
    }


def sleep_quality_details(value):
    """Intervals.icu sleepQuality: 1=Excellent, 2=Good, 3=Average, 4=Poor."""
    try:
        q = int(float(value))
    except (TypeError, ValueError):
        return "Q–", "No quality data", "qna"
    labels = {1: "Excellent", 2: "Good", 3: "Average", 4: "Poor"}
    q = max(1, min(4, q))
    return f"Q{q}", labels[q], f"q{q}"


def compute_race_readiness(form_zone, fatigue_zone, sleep_quality, latest_hrv, wellness):
    """Transparent 0-100 readiness widget based on the athlete's own signals; not a medical metric."""
    score = 50
    reasons = []
    score += {"green": 18, "grey": 0, "red": -18}.get(form_zone, 0)
    score += {"green": 15, "grey": 0, "red": -15}.get(fatigue_zone, 0)
    if sleep_quality == 1:
        score += 12; reasons.append("sleep quality is excellent")
    elif sleep_quality == 2:
        score += 6; reasons.append("sleep quality is good")
    elif sleep_quality == 3:
        score -= 5; reasons.append("sleep quality is average")
    elif sleep_quality == 4:
        score -= 12; reasons.append("sleep quality is poor")
    hrv_vals = [w.get("hrv") for w in sorted(wellness, key=lambda x: x.get("id", ""))[:-1] if isinstance(w.get("hrv"), (int, float))]
    if isinstance(latest_hrv, (int, float)) and len(hrv_vals) >= 5:
        baseline = statistics.median(hrv_vals[-14:])
        if latest_hrv >= baseline * 1.05:
            score += 8; reasons.append("HRV is above your recent baseline")
        elif latest_hrv <= baseline * 0.90:
            score -= 8; reasons.append("HRV is below your recent baseline")
        else:
            reasons.append("HRV is close to your recent baseline")
    score = max(0, min(100, round(score)))
    if score >= 70:
        return score, "Race Ready", "green", "; ".join(reasons) or "Recovery and training signals are favourable versus your own baseline."
    if score <= 40:
        return score, "Recovery Bias", "red", "; ".join(reasons) or "Current recovery signals are unusually strained for you."
    return score, "Train Smart", "grey", "; ".join(reasons) or "Signals are mixed or close to your normal range."


def compute_metrics(wellness, form_thresholds=None, fatigue_thresholds=None):
    sorted_wellness = sorted(wellness, key=lambda w: w.get("id", ""))
    latest = sorted_wellness[-1] if sorted_wellness else {}

    ctl = latest.get("ctl")
    atl = latest.get("atl")
    sleep_quality = latest.get("sleepQuality")
    sleep_quality_label, sleep_quality_text, sleep_quality_class = sleep_quality_details(sleep_quality)
    latest_sleep_score = latest.get("sleepScore")
    latest_sleep_secs = latest.get("sleepSecs")
    latest_sleep_duration = f"{latest_sleep_secs / 3600:.1f}h" if latest_sleep_secs else "n/a"
    latest_sleeping_hr = latest.get("avgSleepingHR")
    tsb = round(ctl - atl, 1) if (ctl is not None and atl is not None) else None

    sleep_values = [w["sleepSecs"] / 3600 for w in wellness if w.get("sleepSecs")]
    avg_sleep = round(statistics.mean(sleep_values), 1) if sleep_values else None

    # Weight isn't logged every day - use the most recent day it IS present, not
    # necessarily the very latest wellness entry.
    weight_entries = [w for w in sorted_wellness if w.get("weight")]
    latest_weight = weight_entries[-1]["weight"] if weight_entries else None

    # Readiness/SpO2 only exist if synced from a compatible wearable (Oura,
    # HRV4Training, some Garmins) - look back for the most recent value, same
    # as weight, and leave None (not shown) if the athlete doesn't sync these.
    readiness_entries = [w for w in sorted_wellness if w.get("readiness") is not None]
    latest_readiness = readiness_entries[-1]["readiness"] if readiness_entries else None

    spo2_entries = [w for w in sorted_wellness if w.get("spO2") is not None]
    latest_spo2 = spo2_entries[-1]["spO2"] if spo2_entries else None

    form_zone = classify_form(tsb, form_thresholds)
    fatigue_zone = classify_fatigue(atl, ctl, fatigue_thresholds)
    race_score, race_label, race_zone, race_reason = compute_race_readiness(
        form_zone, fatigue_zone, sleep_quality, latest.get("hrv"), wellness
    )

    return {
        "ctl": round(ctl, 1) if ctl is not None else "n/a",
        "atl": round(atl, 1) if atl is not None else "n/a",
        "tsb": tsb if tsb is not None else "n/a",
        "fitness_zone": classify_fitness_trend(wellness),
        "fatigue_zone": fatigue_zone,
        "form_zone": form_zone,
        "latest_rhr": latest.get("restingHR", "n/a"),
        "latest_hrv": latest.get("hrv", "n/a"),
        "avg_sleep": f"{avg_sleep}h" if avg_sleep is not None else "n/a",
        "avg_sleep_hours": avg_sleep,
        "latest_weight": f"{round(latest_weight, 1)}kg" if latest_weight is not None else "n/a",
        "latest_readiness": round(latest_readiness) if latest_readiness is not None else None,
        "latest_spo2": round(latest_spo2, 1) if latest_spo2 is not None else None,
        "sleep_quality": sleep_quality,
        "sleep_quality_label": sleep_quality_label,
        "sleep_quality_text": sleep_quality_text,
        "sleep_quality_class": sleep_quality_class,
        "latest_sleep_score": round(latest_sleep_score) if latest_sleep_score is not None else None,
        "latest_sleep_duration": latest_sleep_duration,
        "latest_sleeping_hr": round(latest_sleeping_hr) if latest_sleeping_hr is not None else None,
        "race_readiness_score": race_score,
        "race_readiness_label": race_label,
        "race_readiness_zone": race_zone,
        "race_readiness_css_color": {"green": "green", "red": "red", "grey": "grey-zone"}.get(race_zone, "grey-zone"),
        "race_readiness_reason": race_reason,
    }


def build_data_text(recent_activities, wellness, season_stats, notes=None, feelings=None, best_watts=None):
    lines = ["RECENT ACTIVITIES (last {} days):".format(DAYS_BACK)]
    if not recent_activities:
        lines.append("(no activities found on Intervals.icu for this period)")
    for a in recent_activities:
        duration_sec = a.get("moving_time") or a.get("elapsed_time") or 0
        power = a.get("icu_weighted_avg_watts") or a.get("average_watts") or "n/a"
        lines.append(
            "- {date} | {name} | {type} | {dur} min | load {load} | "
            "power {pwr} | HR {hr} | calories {cal}".format(
                date=a.get("start_date_local", "").replace("T", " ")[:16],
                name=a.get("name", ""),
                type=a.get("type", ""),
                dur=round(duration_sec / 60),
                load=a.get("icu_training_load", "n/a"),
                pwr=power,
                hr=a.get("average_heartrate", "n/a"),
                cal=a.get("calories", "n/a"),
            )
        )

    lines.append("\nSEASON SUMMARY (last {} days, time-in-zone based):".format(SEASON_DAYS_BACK))
    lines.append(
        "- Total training time: {}h | Total load: {} | "
        "Low intensity: {}% | Moderate intensity: {}% | High intensity: {}%".format(
            season_stats["season_hours"], season_stats["season_total_load"],
            season_stats["zone_low_pct"], season_stats["zone_mod_pct"], season_stats["zone_high_pct"],
        )
    )

    if best_watts:
        lines.append("\nREAL POWER CURVE (actual best efforts, last 42 days - use these as the "
                     "ceiling for any power target you prescribe, never exceed them for that "
                     "duration or shorter):")
        for p in best_watts:
            lines.append("- {}: {}W".format(p["label"], p["watts"]))

    lines.append("\nWELLNESS (last {} days):".format(DAYS_BACK))
    for w in sorted(wellness, key=lambda x: x.get("id", "")):
        line = (
            "- {date} | RHR {rhr} | HRV {hrv} | sleep {sleep}h | CTL {ctl} | ATL {atl}".format(
                date=w.get("id", ""),
                rhr=w.get("restingHR", "n/a"),
                hrv=w.get("hrv", "n/a"),
                sleep=round(w["sleepSecs"] / 3600, 1) if w.get("sleepSecs") else "n/a",
                ctl=round(w["ctl"], 1) if w.get("ctl") is not None else "n/a",
                atl=round(w["atl"], 1) if w.get("atl") is not None else "n/a",
            )
            + " | sleepQ {} | sleepScore {}".format(
                ("Q" + str(w.get("sleepQuality"))) if w.get("sleepQuality") is not None else "n/a",
                round(w.get("sleepScore")) if w.get("sleepScore") is not None else "n/a"
            )
        )
        if w.get("weight"):
            line += " | weight {}kg".format(round(w["weight"], 1))
        if w.get("comments"):
            line += " | note: {}".format(w["comments"])
        lines.append(line)

    if notes:
        lines.append("\nCOACH NOTES (things the athlete has told you before, most recent last):")
        for n in notes:
            lines.append("- {date}: {text}".format(date=n.get("date", ""), text=n.get("text", "")))

    if feelings:
        lines.append("\nSELF-REPORTED DAILY FEELING (1=terrible, 10=amazing):")
        for f in feelings:
            lines.append("- {date}: {value}/10".format(date=f.get("date", ""), value=f.get("value", "")))

    return "\n".join(lines)



def get_rome_now():
    """Current wall-clock time for the athlete/coach, independent of Render's server timezone."""
    return datetime.now(ROME_TZ)


def parse_local_activity_datetime(value):
    if not value:
        return None
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00")).replace(tzinfo=None)
    except (ValueError, TypeError):
        return None


def get_clock_preview(now=None):
    now = now or get_rome_now()
    hour = now.hour
    if hour < 12:
        phase = "Morning window · before 12:00"
    elif hour < 17:
        phase = "Between sessions · 12:00–17:00"
    else:
        phase = "Evening window · after 17:00"
    return {"time": now.strftime("%H:%M"), "phase": phase}


def build_coach_clock(recent_activities, now=None):
    """Build deterministic session-awareness before Claude is called.

    Activities already present in Intervals.icu always beat the theoretical clock:
    a logged AM or PM activity is treated as done and is never recommended again.
    """
    now = now or get_rome_now()
    today = now.date()
    today_iso = today.isoformat()
    today_acts = []
    for activity in recent_activities:
        start_raw = activity.get("start_date_local") or ""
        if start_raw[:10] != today_iso:
            continue
        dt = parse_local_activity_datetime(start_raw)
        hour = dt.hour if dt else None
        today_acts.append({
            "name": activity.get("name") or activity.get("type") or "Activity",
            "hour": hour,
            "time": dt.strftime("%H:%M") if dt else "time n/a",
        })

    am_done = any(a["hour"] is not None and a["hour"] < 12 for a in today_acts)
    pm_done = any(a["hour"] is not None and a["hour"] >= 17 for a in today_acts)

    if now.hour < 12:
        phase = "AM WINDOW"
        headline = "Morning session decision"
        explanation = "The morning training window is still open. A logged Intervals.icu activity counts as completed immediately; otherwise the coach may still prescribe the AM session."
        am_status = "DONE" if am_done else "OPEN"
        am_class = "done" if am_done else "open"
        pm_status = "DONE" if pm_done else "UPCOMING"
        pm_class = "done" if pm_done else "upcoming"
    elif now.hour < 17:
        phase = "BETWEEN SESSIONS"
        headline = "Morning checked · evening next"
        explanation = "The morning window has passed. The coach checks whether an AM activity was actually logged, then plans from the evening slot onward instead of prescribing a session that is already over."
        am_status = "DONE" if am_done else "NO ACTIVITY"
        am_class = "done" if am_done else "missed"
        pm_status = "DONE" if pm_done else "UPCOMING"
        pm_class = "done" if pm_done else "upcoming"
    else:
        if pm_done:
            phase = "DAY COMPLETE"
            headline = "Today's two-a-day is closed"
            explanation = "The evening activity is already on Intervals.icu, so the coach moves directly to tomorrow rather than repeating today's work."
        else:
            phase = "PM WINDOW"
            headline = "Evening session decision"
            explanation = "It is after 17:00. If no PM activity is logged yet, the current evening slot is the next decision; any activity already present on Intervals.icu is treated as completed."
        am_status = "DONE" if am_done else "NO ACTIVITY"
        am_class = "done" if am_done else "missed"
        pm_status = "DONE" if pm_done else "OPEN"
        pm_class = "done" if pm_done else "open"

    candidates = []
    # Today AM is only a valid future/active slot before noon and only when not already done.
    if now.hour < 12 and not am_done:
        candidates.append((today, "AM"))
    # Today's PM remains the next live slot until it is logged; after it is done we move on.
    if not pm_done:
        candidates.append((today, "PM"))

    d = today + timedelta(days=1)
    while len(candidates) < 3:
        candidates.append((d, "AM"))
        if len(candidates) < 3:
            candidates.append((d, "PM"))
        d += timedelta(days=1)

    next_slots = []
    for slot_date, period in candidates[:3]:
        if slot_date == today:
            day_word = "Today"
        elif slot_date == today + timedelta(days=1):
            day_word = "Tomorrow"
        else:
            day_word = slot_date.strftime("%A")
        window = "before 12:00" if period == "AM" else "after 17:00"
        next_slots.append({
            "date": slot_date.isoformat(),
            "period": period,
            "window": window,
            "label": f"{day_word} · {period} · {window}",
        })

    acts_text = ", ".join(f'{a["time"]} {a["name"]}' for a in today_acts)
    minutes = now.hour * 60 + now.minute
    day_progress = round(minutes / 1440 * 100, 1)
    clock_angle = (day_progress / 100.0) * 2 * math.pi - (math.pi / 2)
    clock_marker_x = round(90 + 68 * math.cos(clock_angle), 1)
    clock_marker_y = round(90 + 68 * math.sin(clock_angle), 1)
    return {
        "iso": now.isoformat(),
        "time": now.strftime("%H:%M"),
        "timezone": now.tzname() or "Europe/Rome",
        "date_label": now.strftime("%A %d %B"),
        "phase": phase,
        "headline": headline,
        "explanation": explanation,
        "am_done": am_done,
        "pm_done": pm_done,
        "am_status": am_status,
        "pm_status": pm_status,
        "am_status_class": am_class,
        "pm_status_class": pm_class,
        "today_activity_count": len(today_acts),
        "today_activities_text": acts_text,
        "next_slots": next_slots,
        "next_slot_label": next_slots[0]["label"],
        "day_progress": day_progress,
        "marker_x": clock_marker_x,
        "marker_y": clock_marker_y,
    }


def coach_clock_text(clock):
    slots = "\n".join(f'{i+1}. {s["label"]} ({s["date"]})' for i, s in enumerate(clock["next_slots"]))
    activities = clock["today_activities_text"] or "none logged yet"
    return (
        "COACH CLOCK (authoritative timing context):\n"
        f'- Snapshot requested at {clock["time"]} {clock["timezone"]} on {clock["date_label"]}.\n'
        f'- Current phase: {clock["phase"]}.\n'
        f'- Morning slot status: {clock["am_status"]}. Evening slot status: {clock["pm_status"]}.\n'
        f'- Activities already logged today: {activities}.\n'
        "- The next three valid training decision slots are:\n"
        f"{slots}\n"
        "Never prescribe a session for a slot already marked DONE or for a morning slot that has already passed. Intervals.icu activity evidence overrides the theoretical daily schedule."
    )



def classify_training_family(activity):
    """Classify a completed activity into a coaching family using its title first,
    then time-in-zone as a conservative fallback. This is intentionally broad: the
    goal is to stop Claude from accidentally repeating the same quality stimulus,
    not to pretend we can perfectly reverse-engineer every Zwift workout."""
    name = str(activity.get("name") or "").lower()
    compact = name.replace("-", " ").replace("_", " ")

    keyword_groups = [
        ("Recovery", ("recovery", "recuper", "easy spin", "scarico")),
        ("Sprint / Neuromuscular", ("sprint", "neuromus", "anaerobic", "anaerobico")),
        ("VO2max", ("vo2", "vo₂", "vo 2", "max aerobic")),
        ("Over-Under", ("over under", "overunder", "o&u", "over / under")),
        ("Threshold / TTE", ("tte", "threshold", "soglia", "ftp", "time to exhaustion")),
        ("Sweet Spot", ("sweet spot", "sweetspot")),
        ("Tempo", ("tempo", "z3", "zone 3")),
        ("Endurance / Z2", ("z2", "zone 2", "endurance", "aerobic", "endurance ride")),
    ]
    for label, keys in keyword_groups:
        if any(k in compact for k in keys):
            return label

    zone_times = activity.get("icu_zone_times") or []
    if zone_times:
        try:
            secs = [float(z.get("secs") or 0) for z in zone_times]
            low, mod, high = bucket_zone_seconds(secs)
            total = low + mod + high
            if total > 0:
                high_pct = 100 * high / total
                mod_pct = 100 * mod / total
                if high_pct >= 15:
                    return "High Intensity / Mixed"
                if mod_pct >= 30:
                    return "Tempo / Threshold Mixed"
                if low / total >= 0.75:
                    return "Endurance / Z2"
        except (TypeError, ValueError):
            pass
    return "Other / Mixed"


def is_hard_training_family(family):
    f = (family or "").lower()
    return any(k in f for k in (
        "vo2", "threshold", "tte", "over-under", "sprint", "neuromuscular",
        "high intensity", "tempo / threshold"
    ))


def build_week_memory(recent_activities, now=None):
    """Reconstruct the current Monday→now training week directly from Intervals.icu.

    This is fresh on every snapshot, so it survives deploys and does not rely on
    Claude remembering what happened yesterday.
    """
    now = now or get_rome_now()
    today = now.date()
    monday = today - timedelta(days=today.weekday())
    items = []

    for activity in recent_activities:
        raw = activity.get("start_date_local") or ""
        dt = parse_local_activity_datetime(raw)
        if not dt:
            continue
        d = dt.date()
        if d < monday or d > today:
            continue
        # If an activity is timestamped later today than the snapshot, ignore it.
        if d == today and dt.time() > now.replace(tzinfo=None).time():
            continue

        family = classify_training_family(activity)
        duration_sec = activity.get("moving_time") or activity.get("elapsed_time") or 0
        item = {
            "date": d.isoformat(),
            "day": d.strftime("%A"),
            "day_short": d.strftime("%a"),
            "time": dt.strftime("%H:%M"),
            "name": activity.get("name") or activity.get("type") or "Activity",
            "family": family,
            "family_short": family.replace("Endurance / ", "").replace(" / Mixed", ""),
            "duration_min": round(duration_sec / 60) if duration_sec else None,
            "load": activity.get("icu_training_load"),
            "hard": is_hard_training_family(family),
        }
        items.append(item)

    items.sort(key=lambda x: (x["date"], x["time"]))
    hard_items = [x for x in items if x["hard"]]
    hard_families = []
    for x in hard_items:
        if x["family"] not in hard_families:
            hard_families.append(x["family"])

    # Days since the most recent hard session is useful spacing information for Claude.
    last_hard = hard_items[-1] if hard_items else None
    days_since_last_hard = None
    if last_hard:
        days_since_last_hard = (today - date.fromisoformat(last_hard["date"])).days

    return {
        "week_start": monday.isoformat(),
        "week_end": today.isoformat(),
        "activities": items,
        "hard_count": len(hard_items),
        "hard_families": hard_families,
        "hard_summary": ", ".join(hard_families),
        "last_hard": last_hard,
        "days_since_last_hard": days_since_last_hard,
    }


def week_memory_text(memory):
    if not memory or not memory.get("activities"):
        return (
            "CURRENT WEEK TRAINING HISTORY (Monday to snapshot time):\n"
            "- No completed activities found yet this week."
        )

    lines = ["CURRENT WEEK TRAINING HISTORY (Monday to snapshot time — authoritative):"]
    for a in memory["activities"]:
        dur = f'{a["duration_min"]} min' if a.get("duration_min") is not None else "duration n/a"
        load = a.get("load") if a.get("load") is not None else "n/a"
        quality = "HARD/QUALITY" if a.get("hard") else "easy/moderate"
        lines.append(
            f'- {a["day"]} {a["date"]} {a["time"]} | {a["family"]} | {quality} | '
            f'{dur} | load {load} | {a["name"]}'
        )
    if memory.get("last_hard"):
        lh = memory["last_hard"]
        lines.append(
            f'- Most recent hard/quality stimulus: {lh["family"]} on {lh["day"]} {lh["date"]} '
            f'({memory.get("days_since_last_hard")} day(s) ago).'
        )
    lines.append(
        "Use this history before prescribing the next sessions. Do not repeat the same hard workout family "
        "simply because it fits the next slot. In particular, avoid another TTE/threshold, VO2max, Over-Under "
        "or sprint/neuromuscular stimulus too close to the same family already completed. Prefer complementary "
        "work and adequate spacing. A repeat is allowed only when there is a clear coaching reason, and that "
        "reason must be stated explicitly in the session rationale."
    )
    return "\n".join(lines)


def intensity_class(value):
    v = (value or "").lower()
    if "vo2" in v or "vo₂" in v or "anaer" in v:
        return "vo2"
    if "threshold" in v or "soglia" in v:
        return "threshold"
    if "tempo" in v or "sweet" in v:
        return "tempo"
    if "recover" in v or "easy" in v:
        return "recovery"
    return "endurance"


def normalize_next_sessions(raw_sessions, clock):
    raw_sessions = raw_sessions if isinstance(raw_sessions, list) else []
    normalized = []
    for idx, slot in enumerate(clock["next_slots"]):
        raw = raw_sessions[idx] if idx < len(raw_sessions) and isinstance(raw_sessions[idx], dict) else {}
        intensity = str(raw.get("intensity") or ("Endurance" if slot["period"] == "AM" else "Training"))
        normalized.append({
            # Slot comes from Python, not Claude, so the displayed timing cannot drift/hallucinate.
            "slot": slot["label"],
            "title": str(raw.get("title") or ("Aerobic endurance" if slot["period"] == "AM" else "Coach-selected session")),
            "duration": str(raw.get("duration") or "Up to 60 min"),
            "intensity": intensity,
            "intensity_class": intensity_class(intensity),
            "main_set": str(raw.get("main_set") or "See coach recommendation."),
            "why": str(raw.get("why") or "Selected from the current recovery, load and timing context."),
        })
    return normalized



def ask_claude(data_text, metrics, coach_clock, week_memory):
    now = get_rome_now()
    slot_lines = "\n".join(
        f'{i+1}. {slot["label"]} | date {slot["date"]}'
        for i, slot in enumerate(coach_clock["next_slots"])
    )
    prompt = (
        "You are an expert cycling coach inside THE LAB. The athlete may train twice per day: "
        "a morning session before 12:00 and an evening session after 17:00. Your first job is temporal awareness. "
        "The COACH CLOCK below is authoritative. Activities already logged on Intervals.icu are completed; never prescribe them again. "
        "If the morning window has passed, do not suggest a morning workout for today. If both sessions are already logged, move to tomorrow. "
        "Morning sessions are usually the natural place for aerobic/easy volume; evening is the natural place for quality, but recovery data can override that pattern. "
        "Do not force intensity just because an evening slot exists.\n\n"
        "{clock_context}\n\n"
        "{week_context}\n\n"
        "ATHLETE CONTEXT:\n{athlete_context}\n\n"
        "Current metrics: Fitness (CTL) {ctl} [{fitness_zone}], Fatigue (ATL) {atl} [{fatigue_zone}], "
        "Form (TSB) {tsb} [{form_zone}]. The zones are calibrated against this athlete's own baseline. "
        "Use the season summary's time-in-zone percentages when discussing distribution. Consider any injury/illness/soreness notes explicitly.\n\n"
        "WEEK-MEMORY RULES: training already completed this week is part of the prescription decision, not background trivia. "
        "Do not prescribe a duplicate quality stimulus by habit. If Threshold/TTE was completed yesterday, another Threshold/TTE tomorrow is normally inappropriate; "
        "choose recovery/endurance or a complementary quality family depending on recovery and spacing. Apply the same principle to VO2max, Over-Under and sprint work. "
        "Hard sessions should generally have meaningful recovery between them, especially when they stress the same physiological system. "
        "If you intentionally repeat a hard family within 72 hours, explicitly justify why in that session's 'why' field.\n\n"
        "Writing style: this dashboard is visual. Do not write a paragraph where a gauge already tells the story. "
        "training_load, season_distribution and fatigue_signals should normally be 1-2 useful sentences each. "
        "season_outlook may be 2-3 sentences. recommendation is the place where you may properly coach: use 3-5 clear sentences when the decision needs explanation. "
        "For each session card, give a concise but specific prescription and 1-2 sentences of rationale.\n\n"
        "Return ONLY valid JSON with exactly these keys:\n"
        '- "training_load": string\n'
        '- "season_distribution": string\n'
        '- "season_outlook": string\n'
        '- "fatigue_signals": string\n'
        '- "recommendation": string\n'
        '- "next_sessions": array of exactly 3 objects, in the SAME ORDER as the valid slots below. Each object must contain '
        '"title", "duration", "intensity", "main_set", "why". Do not invent or change the slot/date; Python will display the slot separately. '
        'Each session must fit within 60 minutes total. Use the REAL POWER CURVE as a hard physiological reference and do not prescribe unrealistic seated power.\n\n'
        "VALID NEXT SLOTS:\n{slot_lines}\n\n"
        "DATA:\n{data_text}"
    ).format(
        clock_context=coach_clock_text(coach_clock),
        week_context=week_memory_text(week_memory),
        athlete_context=ATHLETE_CONTEXT,
        ctl=metrics["ctl"], fitness_zone=metrics["fitness_zone"],
        atl=metrics["atl"], fatigue_zone=metrics["fatigue_zone"],
        tsb=metrics["tsb"], form_zone=metrics["form_zone"],
        slot_lines=slot_lines, data_text=data_text,
    )

    resp = requests.post(
        "https://api.anthropic.com/v1/messages",
        headers={
            "x-api-key": ANTHROPIC_API_KEY,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        },
        json={
            "model": "claude-sonnet-4-6",
            "max_tokens": 2600,
            "messages": [{"role": "user", "content": prompt}],
        },
        timeout=60,
    )
    resp.raise_for_status()
    resp_data = resp.json()
    text = "".join(block.get("text", "") for block in resp_data.get("content", []))
    text = text.strip()
    if text.startswith("```"):
        text = text.strip("`")
        if text.startswith("json"):
            text = text[4:]
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError as e:
        preview = text[:300].replace("\n", " ")
        raise json.JSONDecodeError(f"{e.msg} | raw response preview: {preview}", e.doc, e.pos)

    parsed["next_sessions"] = normalize_next_sessions(parsed.get("next_sessions"), coach_clock)
    return parsed


def ask_claude_chat(question, notes, current_data):
    now = get_rome_now()
    today = now.date()
    notes_text = "\n".join(
        "- {}: {}".format(n.get("date", ""), n.get("text", "")) for n in notes
    ) or "(none yet)"

    snapshot_text = "(no snapshot generated yet this session)"
    if current_data:
        snapshot_text = (
            "Fitness (CTL) = {ctl} [{fz}], Fatigue (ATL) = {atl} [{gz}], "
            "Form (TSB) = {tsb} [{fmz}], Energy Bank = {es}/100 ({el})."
        ).format(
            ctl=current_data.get("ctl"), fz=current_data.get("fitness_zone"),
            atl=current_data.get("atl"), gz=current_data.get("fatigue_zone"),
            tsb=current_data.get("tsb"), fmz=current_data.get("form_zone"),
            es=current_data.get("energy_score"), el=current_data.get("energy_label"),
        )

    prompt = (
        "You are the athlete's cycling coach, embedded as a chat box in their personal "
        "dashboard. The current local time is {today_time} Europe/Rome on {today_date} ({today_weekday}). {athlete_context} "
        "Notes the athlete has shared with you before:\n{notes_text}\n\n"
        "Their most recent snapshot: {snapshot_text}\n\n"
        "The athlete just wrote: \"{question}\"\n\n"
        "Respond ONLY with valid JSON (no markdown fences, no extra text) with exactly these "
        "keys:\n"
        '- "answer": a helpful, conversational reply (2-4 sentences, plain prose, no markdown)\n'
        '- "remember": if the athlete\'s message contains a specific, durable fact worth '
        "remembering for future sessions (an injury, an upcoming race, a life event affecting "
        "training, a stated preference or goal), a short factual sentence capturing it in the "
        "third person (e.g. \"Reported mild left knee pain starting July 30\"). If there is "
        "nothing durable worth remembering, use exactly null."
    ).format(
        today_date=today.isoformat(), today_weekday=today.strftime("%A"), today_time=now.strftime("%H:%M"),
        athlete_context=ATHLETE_CONTEXT, notes_text=notes_text,
        snapshot_text=snapshot_text, question=question,
    )

    resp = requests.post(
        "https://api.anthropic.com/v1/messages",
        headers={
            "x-api-key": ANTHROPIC_API_KEY,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        },
        json={
            "model": "claude-sonnet-4-6",
            "max_tokens": 400,
            "messages": [{"role": "user", "content": prompt}],
        },
        timeout=60,
    )
    resp.raise_for_status()
    resp_data = resp.json()
    text = "".join(block.get("text", "") for block in resp_data.get("content", []))
    text = text.strip()
    if text.startswith("```"):
        text = text.strip("`")
        if text.startswith("json"):
            text = text[4:]
    parsed = json.loads(text)
    return parsed.get("answer", ""), parsed.get("remember")



def build_preview_data():
    """Complete sample dashboard for visual testing. No external API calls."""
    now = get_rome_now()
    today = now.date()
    monday = today - timedelta(days=today.weekday())
    sample_activities = [
        {"start_date_local": f"{monday.isoformat()}T06:20:00", "name": "Zwift Z2 Endurance", "moving_time": 3600, "icu_training_load": 42, "icu_zone_times": [{"secs": 3000},{"secs": 400},{"secs": 200}]},
        {"start_date_local": f"{(monday + timedelta(days=1)).isoformat()}T18:10:00", "name": "TTE Threshold 4x4", "moving_time": 3300, "icu_training_load": 76, "icu_zone_times": [{"secs": 1700},{"secs": 700},{"secs": 900}]},
    ]
    if now.hour >= 7:
        sample_activities.append({"start_date_local": f"{today.isoformat()}T06:15:00", "name": "Zwift Z2 Morning", "moving_time": 3600, "icu_training_load": 38, "icu_zone_times": [{"secs": 3200},{"secs": 300},{"secs": 100}]})
    clock = build_coach_clock(sample_activities, now=now)
    week = build_week_memory(sample_activities, now=now)
    energy = compute_energy_bank("green", "grey", 7.8)
    return {
        **energy,
        "coach_clock": clock,
        "week_memory": week,
        "ctl": 106.3, "atl": 98.4, "tsb": 7.9,
        "fitness_zone": "grey", "fatigue_zone": "grey", "form_zone": "green",
        "latest_rhr": 38, "latest_hrv": 74, "avg_sleep": "7.8h", "latest_weight": "56.0kg",
        "latest_readiness": 84, "latest_spo2": 98.0,
        "sleep_quality_label": "Q2", "sleep_quality_text": "Good", "sleep_quality_class": "q2",
        "latest_sleep_score": 82, "latest_sleep_duration": "7.6h", "latest_sleeping_hr": 41,
        "race_readiness_score": 84, "race_readiness_label": "Race Ready", "race_readiness_zone": "green",
        "race_readiness_css_color": "green", "race_readiness_reason": "Sleep is good, Form is favourable and HRV is close to your recent baseline.",
        "health_rings": {
            "rhr": {"pct": 82, "color": "green", "status": "Typical"},
            "hrv": {"pct": 78, "color": "green", "status": "Good"},
            "sleep": {"pct": 87, "color": "green", "status": "Good"},
        },
        "trend_arrows": {
            "rhr": {"arrow": "▼", "color": "green"}, "hrv": {"arrow": "▲", "color": "green"},
            "sleep": {"arrow": "▲", "color": "green"}, "weight": None,
        },
        "recent_trend": [
            {"weekday":"Thu","tsb":-4,"delta":-2,"zone":"red"}, {"weekday":"Fri","tsb":0,"delta":0,"zone":"grey"},
            {"weekday":"Sat","tsb":3,"delta":2,"zone":"green"}, {"weekday":"Sun","tsb":1,"delta":0,"zone":"grey"},
            {"weekday":"Mon","tsb":8,"delta":7,"zone":"green"},
        ],
        "avg_daily_calories": 1488,
        "training_load": "Load is high but stable relative to your current fitness. Today looks suitable for aerobic work while preserving room for the next quality stimulus.",
        "fatigue_signals": "Resting HR is typical, HRV is near baseline and sleep is supportive. No single recovery signal is currently asking for a hard stop.",
        "recommendation": "Keep the next session easy and aerobic. The week already contains a threshold/TTE stimulus, so the next quality session should be complementary rather than another threshold repeat. If recovery remains stable tomorrow, progress with controlled sweet spot or VO₂ work depending on how the legs respond.",
        "next_sessions": [
            {"slot": clock["next_slots"][0]["label"], "title":"Easy Aerobic / Active Recovery", "duration":"55 min", "intensity":"Recovery", "intensity_class":"recovery", "main_set":"10 min easy, then 40 min steady Z1/low Z2, 5 min cool-down.", "why":"Reduce residual fatigue and avoid duplicating the threshold/TTE work already completed this week."},
            {"slot": clock["next_slots"][1]["label"], "title":"Aerobic Endurance / Z2 Steady", "duration":"55 min", "intensity":"Endurance", "intensity_class":"endurance", "main_set":"5 min warm-up, 45 min continuous Z2, 5 min easy cool-down.", "why":"Adds useful volume without competing with the next quality window."},
            {"slot": clock["next_slots"][2]["label"], "title":"Sweet Spot Blocks", "duration":"60 min", "intensity":"Sweet Spot", "intensity_class":"tempo", "main_set":"10 min warm-up, 3 × 10 min controlled sweet spot with 4 min easy between, cool down to 60 min.", "why":"A complementary stimulus after adequate spacing from this week’s TTE session."},
        ],
        "best_watts": [
            {"label":"5s","watts":930,"pct":100},{"label":"15s","watts":720,"pct":77},{"label":"1min","watts":455,"pct":49},{"label":"5min","watts":350,"pct":38},{"label":"20min","watts":303,"pct":33},{"label":"1h","watts":265,"pct":28},
        ],
        "best_watts_debug": None,
        "season_hours": 142.6, "season_total_load": 7350,
        "zone_low_pct": 84, "zone_mod_pct": 8, "zone_high_pct": 8,
        "season_distribution": "The last 90 days are strongly low-intensity dominant with small, deliberate doses of moderate and high intensity. The overall shape is close to polarized.",
        "season_outlook": "The distribution supports endurance development while leaving room for race-specific quality. Keep the hard work purposeful and avoid adding threshold volume simply because freshness is high.",
    }


@app.route("/preview")
def preview():
    if not require_login():
        return redirect(url_for("login"))
    return render_template_string(
        HOME_PAGE, days=DAYS_BACK, season_days=SEASON_DAYS_BACK,
        data=build_preview_data(), error=None, css=BASE_CSS, logo=LOGO_B64, favicon=FAVICON_B64,
        notes=load_notes(), chat_answer=None, chat_error=None,
        feelings=load_feelings(), latest_feeling=get_latest_feeling(),
        app_version=APP_VERSION, clock_preview=get_clock_preview(), is_preview=True,
    )


@app.route("/analyze", methods=["POST"])
def analyze():
    if not require_login():
        return redirect(url_for("login"))

    error = None
    data = None
    try:
        recent_activities, season_activities, wellness, season_wellness = fetch_intervals_data()
        form_thresholds = personal_form_thresholds(season_wellness)
        form_median = personal_form_median(season_wellness)
        fatigue_thresholds = personal_fatigue_thresholds(season_wellness)
        metrics = compute_metrics(wellness, form_thresholds, fatigue_thresholds)
        season_stats = compute_season_stats(season_activities)
        energy_bank = compute_energy_bank(
            metrics["form_zone"], metrics["fatigue_zone"], metrics["avg_sleep_hours"]
        )
        recent_trend = compute_recent_trend(wellness, n=5, form_thresholds=form_thresholds, form_median=form_median)
        trend_arrows = compute_trend_arrows(wellness)
        health_rings = compute_health_rings(
            metrics["latest_rhr"], metrics["latest_hrv"], metrics["avg_sleep_hours"], trend_arrows
        )
        best_watts, best_watts_debug = get_best_watts()
        recent_calories = sum(a.get("calories") or 0 for a in recent_activities)
        avg_daily_calories = round(recent_calories / DAYS_BACK) if DAYS_BACK else 0
        notes = load_notes()
        feelings = load_feelings()
        coach_clock = build_coach_clock(recent_activities)
        week_memory = build_week_memory(recent_activities)
        data_text = build_data_text(recent_activities, wellness, season_stats, notes, feelings, best_watts)
        data_text += "\n\n" + coach_clock_text(coach_clock)
        data_text += "\n\n" + week_memory_text(week_memory)
        analysis = ask_claude(data_text, metrics, coach_clock, week_memory)
        data = {
            **metrics, **season_stats, **analysis, **energy_bank,
            "coach_clock": coach_clock,
            "week_memory": week_memory,
            "avg_daily_calories": avg_daily_calories,
            "recent_trend": recent_trend,
            "trend_arrows": trend_arrows,
            "health_rings": health_rings,
            "best_watts": best_watts,
            "best_watts_debug": best_watts_debug,
        }
        session["last_data"] = data
    except requests.HTTPError as e:
        error = f"Error calling an external service: {e}"
    except (json.JSONDecodeError, KeyError) as e:
        error = f"The AI response could not be parsed: {e}"
    except Exception as e:
        error = f"Unexpected error: {e}"

    return render_template_string(
        HOME_PAGE, days=DAYS_BACK, season_days=SEASON_DAYS_BACK,
        data=data, error=error, css=BASE_CSS, logo=LOGO_B64, favicon=FAVICON_B64,
        notes=load_notes(), chat_answer=None, chat_error=None,
        feelings=load_feelings(), latest_feeling=get_latest_feeling(),
        app_version=APP_VERSION, clock_preview=get_clock_preview(), is_preview=False,
    )


@app.route("/ask", methods=["POST"])
def ask():
    if not require_login():
        return redirect(url_for("login"))

    question = (request.form.get("question") or "").strip()
    chat_answer = None
    chat_error = None
    current_data = session.get("last_data")

    if question:
        try:
            notes = load_notes()
            _ai_reply, remember = ask_claude_chat(question, notes, current_data)
            if remember:
                notes = save_note(remember)
            else:
                # nothing the AI flagged as durable - save the raw note anyway so
                # it's still available as context, verbatim, for the next snapshot
                notes = save_note(question)
            chat_answer = "Noted ✅ — I'll factor this into your next snapshot."
        except requests.HTTPError as e:
            chat_error = f"Error calling an external service: {e}"
        except (json.JSONDecodeError, KeyError) as e:
            chat_error = f"The AI response could not be parsed: {e}"
        except Exception as e:
            chat_error = f"Unexpected error: {e}"

    return render_template_string(
        HOME_PAGE, days=DAYS_BACK, season_days=SEASON_DAYS_BACK,
        data=current_data, error=None, css=BASE_CSS, logo=LOGO_B64, favicon=FAVICON_B64,
        notes=load_notes(), chat_answer=chat_answer, chat_error=chat_error,
        feelings=load_feelings(), latest_feeling=get_latest_feeling(),
        app_version=APP_VERSION, clock_preview=get_clock_preview(), is_preview=False,
    )


@app.route("/log-feeling", methods=["POST"])
def log_feeling():
    if not require_login():
        return redirect(url_for("login"))

    error = None
    try:
        value = int(request.form.get("feeling", ""))
        if not 1 <= value <= 10:
            raise ValueError
        save_feeling(value)
    except (ValueError, TypeError):
        error = "Please pick a value between 1 and 10."

    return render_template_string(
        HOME_PAGE, days=DAYS_BACK, season_days=SEASON_DAYS_BACK,
        data=session.get("last_data"), error=error, css=BASE_CSS, logo=LOGO_B64, favicon=FAVICON_B64,
        notes=load_notes(), chat_answer=None, chat_error=None,
        feelings=load_feelings(), latest_feeling=get_latest_feeling(),
        app_version=APP_VERSION, clock_preview=get_clock_preview(), is_preview=False,
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=True)
