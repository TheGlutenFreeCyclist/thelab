import base64
import json
import os
import statistics
from datetime import date, timedelta

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
@import url('https://fonts.googleapis.com/css2?family=Bayon&family=Inter:wght@400;500;600;700&display=swap');

:root {
  --black: #0a0a0a;
  --panel: #141414;
  --white: #f5f5f5;
  --red: #ff3b4f;
  --red-dim: #9d1d2a;
  --green: #25d47a;
  --grey-zone: #8e949d;
  --cyan: #45d7e8;
  --orange: #ff9f1c;
  --magenta: #e83e9c;
  --purple: #8b5cf6;
  --blue: #4da3ff;
  --panel-2: #191919;
}

* { box-sizing: border-box; }

body {
  background: radial-gradient(circle at 50% -20%, #211116 0, var(--black) 34%, #070707 100%);
  color: var(--white);
  font-family: 'Inter', sans-serif;
  margin: 0;
  padding: 0;
  min-height: 100vh;
}

.display {
  font-family: 'Bayon', sans-serif;
  letter-spacing: 0.03em;
  text-transform: uppercase;
}

a { color: var(--white); }

.center-screen {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
  padding: 24px;
}

.logo-img {
  width: 180px;
  height: auto;
  margin: 0 auto 18px auto;
  display: block;
}

.header-center {
  text-align: center;
}

.home-logo {
  width: 220px;
  height: auto;
  display: block;
  margin: 4px auto 16px auto;
}

.login-box {
  background: var(--panel);
  border: 1px solid var(--white);
  padding: 36px 32px;
  width: 100%;
  max-width: 360px;
  text-align: center;
}

.login-box h1 {
  font-size: 22px;
  margin: 0 0 24px 0;
  color: var(--white);
  font-weight: 400;
  letter-spacing: 0.04em;
}

.login-box input {
  width: 100%;
  padding: 14px;
  margin-top: 16px;
  border: 1px solid var(--white);
  background: var(--black);
  color: var(--white);
  font-family: 'Inter', sans-serif;
  font-size: 16px;
}

.login-box button, .btn {
  width: 100%;
  padding: 14px;
  margin-top: 20px;
  border: 1px solid var(--red);
  border-radius: 8px;
  background: var(--red);
  color: var(--white);
  font-family: 'Bayon', sans-serif;
  letter-spacing: 0.05em;
  text-transform: uppercase;
  font-size: 16px;
  cursor: pointer;
  transition: background 0.2s ease;
}

.login-box button:hover, .btn:hover { background: var(--red-dim); }

.error-msg {
  color: var(--red);
  margin-top: 14px;
  font-size: 14px;
}

.wrap {
  max-width: 760px;
  margin: 0 auto;
  padding: 32px 20px 64px 20px;
}

.top-bar {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  margin-bottom: 8px;
}

.eyebrow {
  font-size: 13px;
  letter-spacing: 0.15em;
  color: var(--grey-zone);
  text-transform: uppercase;
}

.logout-link {
  font-size: 13px;
  color: var(--grey-zone);
  text-decoration: none;
}

h1.page-title {
  font-size: 46px;
  color: var(--red);
  margin: 4px 0 2px 0;
  line-height: 1;
}

.powered-by {
  font-style: italic;
  color: var(--white);
  font-size: 14px;
  margin: 0 0 4px 0;
}

.subtitle {
  color: var(--grey-zone);
  margin-bottom: 28px;
  font-size: 13px;
}

.section {
  border: 1px solid var(--white);
  padding: 24px;
  margin-bottom: 24px;
}

.section-title {
  color: var(--red);
  font-size: 22px;
  margin: 0 0 18px 0;
}

.stat-row {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(130px, 1fr));
  gap: 14px;
  margin-bottom: 20px;
}

@media (max-width: 560px) {
  .stat-row { grid-template-columns: repeat(2, 1fr); }
}

.stat-card {
  border: 1px solid var(--white);
  padding: 16px;
  text-align: center;
}

.stat-label {
  font-size: 12px;
  letter-spacing: 0.1em;
  color: var(--grey-zone);
  text-transform: uppercase;
  margin-bottom: 6px;
}

.stat-value {
  font-family: 'Bayon', sans-serif;
  font-size: 32px;
  line-height: 1;
}

.stat-sub {
  font-size: 11px;
  color: var(--grey-zone);
  margin-top: 4px;
}

.zone-badge {
  display: inline-block;
  margin-top: 8px;
  padding: 4px 12px;
  font-size: 11px;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  font-family: 'Bayon', sans-serif;
  border-radius: 999px;
  font-weight: 400;
}

.zone-green { background: rgba(63,185,95,0.15); color: var(--green); border: 1px solid var(--green); box-shadow: 0 0 8px rgba(63,185,95,0.5); }
.zone-grey  { background: rgba(138,138,138,0.15); color: var(--grey-zone); border: 1px solid var(--grey-zone); }
.zone-red   { background: rgba(216,30,44,0.15); color: var(--red); border: 1px solid var(--red); box-shadow: 0 0 8px rgba(216,30,44,0.5); }

.prose-card {
  border: 1px solid var(--white);
  padding: 18px;
  margin-bottom: 14px;
}

.prose-card:last-child { margin-bottom: 0; }

.prose-card summary,
.recommendation-box summary,
.training-tips-box summary {
  cursor: pointer;
  list-style: none;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.prose-card summary::-webkit-details-marker,
.recommendation-box summary::-webkit-details-marker,
.training-tips-box summary::-webkit-details-marker {
  display: none;
}

.prose-card summary::after,
.recommendation-box summary::after,
.training-tips-box summary::after {
  content: '\25B8';
  font-size: 16px;
  color: var(--grey-zone);
  margin-left: 12px;
  flex-shrink: 0;
  transition: transform 0.2s ease;
  transform: rotate(0deg);
  display: inline-block;
}

.prose-card[open] summary::after,
.recommendation-box[open] summary::after,
.training-tips-box[open] summary::after {
  transform: rotate(90deg);
}

.prose-card h3 {
  font-family: 'Bayon', sans-serif;
  color: var(--red);
  font-size: 16px;
  margin: 0;
  letter-spacing: 0.05em;
  text-transform: uppercase;
}

.prose-card p {
  margin: 12px 0 0 0;
  line-height: 1.6;
  font-size: 15px;
}

.recommendation-box {
  border: 2px solid var(--red);
  padding: 22px;
}

.recommendation-box h3 {
  font-family: 'Bayon', sans-serif;
  color: var(--red);
  font-size: 20px;
  margin: 0;
  letter-spacing: 0.05em;
  text-transform: uppercase;
}

.recommendation-box p {
  margin: 14px 0 0 0;
  line-height: 1.65;
  font-size: 15px;
  white-space: pre-line;
}

.training-tips-box {
  border: 1px solid var(--red);
  border-radius: 10px;
  padding: 22px;
  margin-top: 20px;
  margin-bottom: 24px;
}

.training-tips-box h3 {
  font-family: 'Bayon', sans-serif;
  color: var(--red);
  font-size: 20px;
  margin: 0;
  letter-spacing: 0.05em;
  text-transform: uppercase;
}

.training-tips-text {
  margin: 14px 0 0 0;
  line-height: 1.65;
  font-size: 15px;
  white-space: pre-line;
}

.error-panel {
  border: 1px solid var(--red);
  color: var(--red);
  padding: 18px;
  margin-bottom: 20px;
  font-size: 14px;
}

.zone-bar-wrap {
  margin-bottom: 20px;
}

.zone-bar {
  display: flex;
  height: 22px;
  border: 1px solid var(--white);
  border-radius: 999px;
  overflow: hidden;
  box-shadow: 0 2px 8px rgba(0,0,0,0.4);
}

.zone-seg {
  height: 100%;
  transition: width 1.1s ease-out;
}

.zone-seg-low  { background: var(--green); }
.zone-seg-mod  { background: var(--grey-zone); }
.zone-seg-high { background: var(--red); }

.zone-bar-labels {
  display: flex;
  justify-content: space-between;
  font-size: 12px;
  color: var(--grey-zone);
  margin-top: 8px;
  flex-wrap: wrap;
  gap: 6px;
}

.zone-dot {
  display: inline-block;
  width: 8px;
  height: 8px;
  margin-right: 6px;
  border-radius: 50%;
  vertical-align: middle;
}

.zone-dot-low  { background: var(--green); }
.zone-dot-mod  { background: var(--grey-zone); }
.zone-dot-high { background: var(--red); }

.loading-track {
  display: none;
  width: 100%;
  height: 10px;
  border: 1px solid var(--white);
  border-radius: 999px;
  margin-top: 14px;
  overflow: hidden;
  position: relative;
}

.loading-fill {
  height: 100%;
  width: 0%;
  background: linear-gradient(90deg, var(--red-dim), var(--red));
  border-radius: 999px;
  transition: width 0.3s ease;
}

.loading-label {
  display: none;
  text-align: center;
  font-size: 13px;
  color: var(--grey-zone);
  margin-top: 8px;
}

@keyframes fadeInUp {
  from { opacity: 0; transform: translateY(10px); }
  to   { opacity: 1; transform: translateY(0); }
}

.dashboard-section { opacity: 0; animation: fadeInUp 0.5s ease-out forwards; animation-delay: 0s; }
.recommendation-box { opacity: 0; animation: fadeInUp 0.5s ease-out forwards; animation-delay: 0.15s; }
.training-tips-box { opacity: 0; animation: fadeInUp 0.5s ease-out forwards; animation-delay: 0.25s; }
.training-section { opacity: 0; animation: fadeInUp 0.5s ease-out forwards; animation-delay: 0.35s; }
.health-section   { opacity: 0; animation: fadeInUp 0.5s ease-out forwards; animation-delay: 0.5s; }
.power-section    { opacity: 0; animation: fadeInUp 0.5s ease-out forwards; animation-delay: 0.65s; }
.season-section   { opacity: 0; animation: fadeInUp 0.5s ease-out forwards; animation-delay: 0.8s; }

.energy-bank-card {
  border: 1px solid var(--white);
  border-radius: 20px;
  padding: 26px 24px;
  margin-bottom: 24px;
  text-align: center;
  opacity: 0;
  animation: fadeInUp 0.5s ease-out forwards;
  animation-delay: 0s;
  box-shadow: 0 4px 24px rgba(0,0,0,0.55);
  position: relative;
  overflow: hidden;
}

.energy-bank-card.zone-glow-green {
  background: radial-gradient(ellipse 120% 100% at 50% -10%, rgba(63,185,95,0.18), transparent 65%), var(--panel);
}
.energy-bank-card.zone-glow-grey {
  background: radial-gradient(ellipse 120% 100% at 50% -10%, rgba(160,160,160,0.14), transparent 65%), var(--panel);
}
.energy-bank-card.zone-glow-red {
  background: radial-gradient(ellipse 120% 100% at 50% -10%, rgba(216,30,44,0.20), transparent 65%), var(--panel);
}

.energy-bank-label {
  font-size: 15px;
  color: var(--grey-zone);
  margin-bottom: 12px;
  letter-spacing: 0.08em;
  position: relative;
}

.energy-bank-explainer {
  font-size: 13px;
  color: var(--grey-zone);
  line-height: 1.5;
  max-width: 480px;
  margin: 0 auto 18px auto;
  position: relative;
}

.trend-arrow {
  font-size: 16px;
  margin-left: 4px;
  vertical-align: middle;
}

.trend-green { color: var(--green); }
.trend-red   { color: var(--red); }
.trend-grey  { color: var(--grey-zone); }

.chat-noted {
  margin-top: 16px;
  color: var(--green);
  font-size: 15px;
}

.wearable-row {
  margin-top: 14px;
  display: flex;
  justify-content: center;
  gap: 18px;
  flex-wrap: wrap;
}

.wearable-stat {
  font-size: 13px;
  color: var(--grey-zone);
}

.wearable-stat strong {
  color: var(--white);
  font-family: 'Bayon', sans-serif;
  font-weight: 400;
}

.energy-ring {
  width: 148px;
  height: 148px;
  border-radius: 50%;
  margin: 0 auto 18px auto;
  padding: 9px;
  position: relative;
  background: conic-gradient(var(--ring-color) calc(var(--pct) * 1%), rgba(255,255,255,0.09) 0);
  box-shadow: 0 0 30px -4px var(--ring-glow);
}

.zone-ring-green { --ring-color: var(--green); --ring-glow: rgba(63,185,95,0.55); }
.zone-ring-grey  { --ring-color: var(--grey-zone); --ring-glow: rgba(160,160,160,0.4); }
.zone-ring-red   { --ring-color: var(--red); --ring-glow: rgba(216,30,44,0.55); }

.energy-ring-inner {
  width: 100%;
  height: 100%;
  border-radius: 50%;
  background: var(--panel);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
}

.energy-bank-score {
  font-size: 42px;
  line-height: 1;
}

.energy-ring-sub {
  font-size: 11px;
  color: var(--grey-zone);
  letter-spacing: 0.08em;
  margin-top: 4px;
}

.gauge-wrap {
  position: relative;
  width: 240px;
  max-width: 100%;
  margin: 0 auto 6px auto;
}

.gauge-svg {
  width: 100%;
  height: auto;
  display: block;
}

.gauge-needle {
  transition: transform 0.6s ease-out;
}

.gauge-score-wrap {
  position: absolute;
  left: 50%;
  bottom: 2%;
  transform: translateX(-50%);
  text-align: center;
}

.mini-ring {
  width: 64px;
  height: 64px;
  border-radius: 50%;
  margin: 8px auto 0 auto;
  padding: 5px;
  background: conic-gradient(var(--ring-color) calc(var(--pct) * 1%), rgba(255,255,255,0.09) 0);
  box-shadow: 0 0 14px -3px var(--ring-glow);
}

.mini-ring-inner {
  width: 100%;
  height: 100%;
  border-radius: 50%;
  background: var(--panel);
  display: flex;
  align-items: center;
  justify-content: center;
}

.mini-ring-value {
  font-family: 'Bayon', sans-serif;
  font-size: 17px;
  color: var(--white);
}

.dashboard-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
  gap: 14px;
  margin-top: 20px;
}

.gauge-card {
  border: 1px solid var(--white);
  border-radius: 12px;
  padding: 16px 12px;
  text-align: center;
  background: var(--panel);
}

.gauge-card-header {
  font-size: 12px;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--grey-zone);
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
}

.gauge-card-icon {
  font-size: 14px;
}

.gauge-card-status {
  font-family: 'Bayon', sans-serif;
  font-size: 12px;
  letter-spacing: 0.05em;
  text-transform: uppercase;
  margin-top: 6px;
}


/* LAB PERFORMANCE UI v2.1 ------------------------------------------------
   Visual-only redesign. Backend routes, API calls and existing functionality
   remain unchanged. The literal label below is also rendered in the page so
   you can verify the deployed version before generating a paid snapshot. */
.performance-kicker {
  color: var(--red);
  font-size: 11px;
  letter-spacing: .22em;
  margin: 10px 0 4px;
  text-transform: uppercase;
  font-weight: 700;
}

/* Wider desktop canvas for the dashboard-style layout */
.wrap { max-width: 1180px; }
.header-center { margin-bottom: 28px; }
.dashboard-section .section-title { margin-bottom: 18px; }

/* PRE-SNAPSHOT CONTROL DECK */
.control-deck {
  display: grid;
  grid-template-columns: 1.15fr 1fr 1fr;
  gap: 16px;
  margin: 26px 0 22px;
  align-items: stretch;
}
.control-card {
  border: 1px solid rgba(255,255,255,.18);
  border-radius: 16px;
  padding: 22px;
  background:
    radial-gradient(circle at 20% 0%, rgba(255,59,79,.08), transparent 38%),
    linear-gradient(180deg, rgba(255,255,255,.035), rgba(255,255,255,.012)),
    var(--panel);
  box-shadow: 0 16px 38px rgba(0,0,0,.28);
  min-width: 0;
}
.control-card .section-title { margin: 0 0 10px; font-size: 24px; }
.control-icon { margin-right: 7px; font-size: .85em; }
.control-card .subtitle { line-height: 1.5; margin-bottom: 16px; }

.control-chat-form { display: grid; gap: 10px; }
.control-chat-form .chat-input {
  width: 100%;
  min-width: 0;
  height: 52px;
  border-radius: 9px;
  border-color: rgba(255,255,255,.28);
  background: rgba(0,0,0,.30);
}
.control-chat-form .btn { margin-top: 0; }
.control-card .notes-list {
  max-height: 135px;
  overflow: auto;
  margin-top: 14px;
  padding-right: 4px;
}

.checkin-card .checkin-row { display: block; }
.checkin-card .mini-ring { margin: 0 auto 14px; }
.checkin-card .checkin-buttons {
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: 10px;
  width: 100%;
}
.checkin-card .checkin-btn {
  width: 42px;
  height: 42px;
  margin: auto;
  transition: border-color .18s ease, color .18s ease, transform .18s ease, box-shadow .18s ease;
}
.checkin-card .checkin-btn:hover {
  border-color: var(--red);
  color: var(--red);
  transform: translateY(-1px);
  box-shadow: 0 0 12px rgba(255,59,79,.18);
}
.checkin-scale {
  display: flex;
  justify-content: space-between;
  gap: 8px;
  padding-top: 14px;
  margin-top: 14px;
  border-top: 1px solid rgba(255,255,255,.08);
  font-size: 10px;
  color: var(--grey-zone);
}
.checkin-scale span:first-child { color: var(--red); }
.checkin-scale span:last-child { color: var(--green); }

.snapshot-card { display: flex; flex-direction: column; }
.snapshot-status-box {
  flex: 1;
  border: 1px solid rgba(255,59,79,.28);
  border-radius: 12px;
  padding: 18px 16px 16px;
  background: linear-gradient(180deg, rgba(255,59,79,.10), rgba(255,59,79,.025));
  display: flex;
  flex-direction: column;
  justify-content: center;
  text-align: center;
  min-height: 178px;
}
.snapshot-status-title {
  font-family: 'Bayon', sans-serif;
  font-size: 25px;
  color: var(--red);
  letter-spacing: .05em;
  text-transform: uppercase;
  margin-bottom: 4px;
}
.snapshot-status-copy { font-size: 12px; color: var(--grey-zone); line-height: 1.45; }
.snapshot-card #snapshot-form { margin-top: 12px; }
.snapshot-card #snapshot-btn { margin-top: 0; }
.snapshot-card .loading-track { margin-top: 12px; }
.snapshot-card .loading-label { margin-bottom: 0; }
.status-pulse {
  width: 34px; height: 34px; border-radius: 50%; margin: 0 auto 12px;
  border: 3px solid rgba(255,59,79,.24); border-top-color: var(--red);
  opacity: .35;
}
.snapshot-card.is-loading .status-pulse { opacity: 1; animation: statusSpin 1s linear infinite; }
@keyframes statusSpin { to { transform: rotate(360deg); } }

/* ENERGY BANK */
.energy-bank-card {
  position: relative;
  overflow: hidden;
  border-color: rgba(255,255,255,.16) !important;
  background: linear-gradient(180deg, rgba(255,255,255,.035), rgba(255,255,255,.012)), var(--panel) !important;
}
.energy-bank-card:before {
  content:""; position:absolute; inset:0; pointer-events:none;
  background:radial-gradient(circle at 50% 0%, rgba(255,59,79,.12), transparent 48%);
}
.gauge-wrap { width: 320px; }
.gauge-svg { filter: drop-shadow(0 12px 24px rgba(0,0,0,.5)); overflow: visible; }
.gauge-segment { fill:none; stroke-width:13; stroke-linecap:round; }
.gauge-segment.s1 { stroke:var(--red); }
.gauge-segment.s2 { stroke:var(--orange); }
.gauge-segment.s3 { stroke:var(--grey-zone); }
.gauge-segment.s4 { stroke:var(--green); }
.gauge-segment.s5 { stroke:var(--cyan); }
.gauge-pointer {
  /* Tip sits just outside the arc; the wider base stays farther out, so the triangle points inward at the live score. */
  fill: var(--white);
  filter: drop-shadow(0 0 5px rgba(255,255,255,.75)) drop-shadow(0 3px 6px rgba(0,0,0,.7));
  transform-origin: 100px 95px;
  transition: transform .65s cubic-bezier(.2,.8,.2,1);
}
.gauge-score-wrap { bottom: 3%; }
.energy-bank-score { font-size: 48px; line-height: .92; }
.energy-ring-sub { margin-top: 7px; }
.dashboard-grid { grid-template-columns: repeat(4, minmax(0,1fr)); }
.gauge-card {
  border-color:rgba(255,255,255,.12);
  background:linear-gradient(180deg, rgba(255,255,255,.035), rgba(255,255,255,.012)), var(--panel);
  box-shadow:0 12px 30px rgba(0,0,0,.22);
}

.sleep-quality-card { position:relative; overflow:hidden; }
.sleep-quality-card:before { content:""; position:absolute; width:100px; height:100px; border-radius:50%; right:-45px; top:-45px; background:var(--sleep-accent); opacity:.13; }
.sleep-q { font-family:'Bayon',sans-serif; font-size:38px; line-height:1; margin:13px 0 5px; color:var(--sleep-accent); }
.sleep-q-label { font-size:11px; color:var(--grey-zone); letter-spacing:.08em; text-transform:uppercase; }
.sleep-score-line { font-size:12px; margin-top:8px; color:var(--white); }
.sleep-score-track { height:5px; border-radius:99px; background:rgba(255,255,255,.09); margin:8px auto 0; overflow:hidden; max-width:110px; }
.sleep-score-fill { height:100%; border-radius:inherit; background:var(--sleep-accent); }
.q1 { --sleep-accent: var(--green); } .q2 { --sleep-accent:#a8d95b; } .q3 { --sleep-accent:var(--orange); } .q4 { --sleep-accent:var(--red); } .qna { --sleep-accent:var(--grey-zone); }
.readiness-strip { display:grid; grid-template-columns:1.15fr .85fr; gap:14px; margin:18px 0 0; }
.readiness-panel { border:1px solid rgba(255,255,255,.12); border-radius:14px; padding:16px; background:rgba(255,255,255,.025); text-align:left; }
.readiness-title { font-size:11px; letter-spacing:.12em; text-transform:uppercase; color:var(--grey-zone); }
.readiness-value { font-family:'Bayon',sans-serif; font-size:28px; margin-top:3px; }
.readiness-reason { font-size:12px; color:var(--grey-zone); line-height:1.45; margin-top:3px; }

.polarization-card { display:grid; grid-template-columns:150px 1fr; gap:22px; align-items:center; margin-top:18px; padding:18px; border:1px solid rgba(255,255,255,.12); border-radius:16px; background:rgba(255,255,255,.02); }
.polar-donut { width:130px; height:130px; border-radius:50%; margin:auto; display:grid; place-items:center; background:conic-gradient(var(--green) 0 calc(var(--low) * 1%), var(--orange) 0 calc((var(--low) + var(--mod)) * 1%), var(--red) 0 100%); box-shadow:0 0 28px rgba(37,212,122,.10); position:relative; }
.polar-donut:after { content:""; width:92px; height:92px; border-radius:50%; background:var(--panel); position:absolute; }
.polar-center { position:relative; z-index:1; text-align:center; font-family:'Bayon',sans-serif; font-size:25px; line-height:1; }
.polar-center small { display:block; font-family:'Inter',sans-serif; font-size:8px; color:var(--grey-zone); letter-spacing:.10em; margin-top:5px; }
.polar-legend { display:grid; gap:8px; font-size:13px; }
.polar-legend-row { display:flex; justify-content:space-between; border-bottom:1px solid rgba(255,255,255,.06); padding-bottom:7px; }

/* TABLET */
@media (max-width: 980px) {
  .wrap { max-width: 780px; }
  .control-deck { grid-template-columns: 1fr 1fr; }
  .snapshot-card { grid-column: 1 / -1; }
  .snapshot-status-box { min-height: 130px; }
}

/* SMARTPHONE */
@media (max-width: 650px) {
  .wrap { padding: 20px 12px 46px; }
  .top-bar { align-items: center; }
  .eyebrow { font-size: 10px; letter-spacing: .12em; }
  .logout-link { font-size: 11px; }
  .home-logo { width: 180px; }
  h1.page-title { font-size: 38px; line-height: 1; }
  .header-center .subtitle { font-size: 11px; line-height: 1.45; }
  .performance-kicker { font-size: 9px; letter-spacing: .18em; }
  .control-deck { grid-template-columns: 1fr; gap: 12px; margin-top: 20px; }
  .control-card { padding: 17px 15px; border-radius: 13px; }
  .control-card .section-title { font-size: 21px; }
  .checkin-card .checkin-buttons { gap: 8px 5px; }
  .checkin-card .checkin-btn { width: 38px; height: 38px; font-size: 13px; }
  .snapshot-status-box { min-height: 125px; }
  .dashboard-grid { grid-template-columns:repeat(2,1fr); gap: 9px; }
  .gauge-card { padding: 13px 7px; }
  .gauge-wrap { width: min(300px, 92vw); }
  .readiness-strip { grid-template-columns:1fr; }
  .polarization-card { grid-template-columns:1fr; }
  .polar-donut { width: 118px; height: 118px; }
  .polar-donut:after { width: 84px; height: 84px; }
  .energy-bank-card { padding-left: 12px; padding-right: 12px; }
  .energy-bank-explainer { max-width: 290px; margin-left:auto; margin-right:auto; }
  .trend-bars { gap: 5px; }
  .trend-bar-value { font-size: 12px; }
  .trend-bar-raw, .trend-bar-day { font-size: 9px; }
}

@media (max-width: 390px) {
  h1.page-title { font-size: 34px; }
  .home-logo { width: 165px; }
  .control-card { padding: 15px 12px; }
  .checkin-card .checkin-btn { width: 35px; height: 35px; }
  .gauge-wrap { width: 276px; }
  .energy-bank-score { font-size: 43px; }
  .dashboard-grid { gap: 7px; }
  .gauge-card-header { font-size: 10px; }
}

.checkin-row {
  display: flex;
  align-items: center;
  gap: 18px;
  flex-wrap: wrap;
}

.checkin-buttons {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  flex: 1;
}

.checkin-btn {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  border: 1px solid var(--white);
  background: transparent;
  color: var(--white);
  font-size: 14px;
  cursor: pointer;
}

.checkin-btn:hover {
  background: var(--red);
  border-color: var(--red);
}

.zone-fill-green { background: linear-gradient(90deg, #2c8f47, var(--green)); color: var(--green); }
.zone-fill-grey  { background: linear-gradient(90deg, #6a6a6a, var(--grey-zone)); color: var(--grey-zone); }
.zone-fill-red   { background: linear-gradient(90deg, #8f1c26, var(--red)); color: var(--red); }

.energy-bank-card .zone-badge {
  margin-top: 12px;
  position: relative;
}

.chat-section form {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}

.chat-input {
  flex: 1;
  min-width: 200px;
  padding: 14px;
  border: 1px solid var(--white);
  background: var(--black);
  color: var(--white);
  font-family: 'Inter', sans-serif;
  font-size: 15px;
}

.chat-section .btn {
  width: auto;
  margin-top: 0;
  padding: 14px 22px;
}

.notes-list {
  margin-top: 20px;
  border-top: 1px solid var(--white);
  padding-top: 16px;
}

.note-line {
  font-size: 13px;
  color: var(--grey-zone);
  margin: 0 0 8px 0;
  line-height: 1.5;
}

.note-date {
  color: var(--white);
  font-weight: 600;
  margin-right: 8px;
}

.trend-row {
  margin-top: 20px;
  border-top: 1px solid var(--white);
  padding-top: 16px;
}

.trend-bars {
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
  gap: 8px;
  height: 70px;
}

.trend-bar-col {
  display: flex;
  flex-direction: column;
  align-items: center;
  flex: 1;
  height: 100%;
  justify-content: flex-end;
}

.trend-bar-track {
  width: 100%;
  max-width: 26px;
  height: 48px;
  display: flex;
  align-items: flex-end;
  border-radius: 999px;
  background: rgba(255,255,255,0.07);
  overflow: hidden;
}

.trend-bar-fill {
  width: 100%;
  border-radius: 999px;
  transition: height 1s ease-out;
  box-shadow: 0 0 10px -1px currentColor;
}

.trend-bar-value {
  font-size: 13px;
  font-family: 'Bayon', sans-serif;
  margin-top: 6px;
}

.trend-bar-raw {
  font-size: 9px;
  color: var(--grey-zone);
  margin-top: 1px;
}

.trend-bar-day {
  font-size: 10px;
  color: var(--grey-zone);
  text-transform: uppercase;
}

.generate-section {
  text-align: center;
}

.pdf-btn {
  width: 100%;
  margin-top: 8px;
  background: transparent;
  color: var(--white);
}

.pdf-btn:hover {
  background: var(--panel);
}

.power-bars {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.power-bar-row {
  display: flex;
  align-items: center;
  gap: 10px;
}

.power-bar-label {
  width: 44px;
  font-size: 12px;
  color: var(--grey-zone);
  text-align: right;
  flex-shrink: 0;
}

.power-bar-track {
  flex: 1;
  height: 16px;
  border: 1px solid var(--white);
  border-radius: 999px;
  overflow: hidden;
  background: var(--panel);
}

.power-bar-fill {
  height: 100%;
  background: linear-gradient(90deg, var(--red-dim), var(--red));
  transition: width 1.1s ease-out;
}

.power-bar-value {
  width: 56px;
  font-size: 13px;
  font-family: 'Bayon', sans-serif;
  flex-shrink: 0;
}

@media print {
  .no-print, .top-bar, .chat-section, .generate-section, .pdf-btn {
    display: none !important;
  }
  body {
    background: white;
    color: black;
  }
  .section, .recommendation-box, .training-tips-box, .energy-bank-card, .stat-card, .prose-card {
    border-color: black !important;
    box-shadow: none !important;
    opacity: 1 !important;
    animation: none !important;
    break-inside: avoid;
  }
  .section-title, .page-title, .recommendation-box h3, .training-tips-box h3, .energy-bank-label,
  .zone-badge, .prose-card h3 {
    color: black !important;
  }
  .subtitle, .stat-label, .stat-sub { color: #444 !important; }
  .prose-card summary::after, .recommendation-box summary::after, .training-tips-box summary::after {
    display: none !important;
  }
  .prose-card p, .recommendation-box p, .training-tips-text {
    display: block !important;
  }
  .prose-card summary, .recommendation-box summary, .training-tips-box summary {
    pointer-events: none;
  }
}
"""

LOGIN_PAGE = """
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>The Gluten Free Cyclist - Health Snapshot</title>
  <link rel="icon" type="image/png" href="data:image/png;base64,{{ favicon }}">
  <style>{{ css }}</style>
</head>
<body>
  <div class="center-screen">
    <img class="logo-img" src="data:image/png;base64,{{ logo }}" alt="The Gluten Free Cyclist">
    <div class="login-box">
      <h1>Please Log In</h1>
      <form method="post">
        <input type="password" name="password" placeholder="Password" autofocus required>
        <button type="submit" class="display">Enter</button>
      </form>
      {% if error %}<div class="error-msg">{{ error }}</div>{% endif %}
    </div>
  </div>
</body>
</html>
"""

HOME_PAGE = """
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>The Gluten Free Cyclist - Health Snapshot</title>
  <link rel="icon" type="image/png" href="data:image/png;base64,{{ favicon }}">
  <style>{{ css }}</style>
</head>
<body>
  <div class="wrap">
    <div class="top-bar">
      <span class="eyebrow">The Gluten Free Cyclist</span>
      <a class="logout-link" href="{{ url_for('logout') }}">Log out</a>
    </div>
    <div class="header-center">
      <img class="home-logo" src="data:image/png;base64,{{ logo }}" alt="The Gluten Free Cyclist">
      <h1 class="page-title display">Health Snapshot</h1>
      <p class="subtitle">Recent window: last {{ days }} days &middot; Season window: last {{ season_days }} days &middot; Intervals.icu data analyzed by AI</p>
    </div>

    <div class="performance-kicker">LAB PERFORMANCE UI v2.1</div>

    <div class="control-deck no-print">
      <section class="control-card chat-section">
        <h2 class="section-title display"><span class="control-icon">&#128172;</span>Coach Chat</h2>
        <p class="subtitle">Before generating the snapshot, is there something you wish your coach would know first?</p>
        <form method="post" action="{{ url_for('ask') }}" id="chat-form" class="control-chat-form">
          <input type="text" class="chat-input" name="question" placeholder="e.g. My left knee has been sore since Tuesday" required>
          <button type="submit" class="btn display" id="chat-btn">Send</button>
        </form>
        {% if chat_error %}
        <div class="error-panel" style="margin-top:14px;">{{ chat_error }}</div>
        {% endif %}
        {% if chat_answer %}
        <p class="chat-noted display">{{ chat_answer }}</p>
        {% endif %}
        {% if notes %}
        <div class="notes-list">
          <p class="stat-label" style="margin-bottom:8px;">Remembered so far</p>
          {% for n in notes|reverse %}
          <p class="note-line"><span class="note-date">{{ n.date }}</span> {{ n.text }}</p>
          {% endfor %}
        </div>
        {% endif %}
      </section>

      <section class="control-card checkin-card">
        <h2 class="section-title display"><span class="control-icon">&#128203;</span>Daily Check-In</h2>
        <p class="subtitle">How are you feeling today? This doesn't come from Intervals.icu &mdash; you tell us.</p>
        <div class="checkin-row">
          {% if latest_feeling %}
          <div class="mini-ring zone-ring-{{ latest_feeling.color }}" style="--pct: {{ latest_feeling.value * 10 }};">
            <div class="mini-ring-inner"><div class="mini-ring-value">{{ latest_feeling.value }}</div></div>
          </div>
          {% endif %}
          <form method="post" action="{{ url_for('log_feeling') }}" class="checkin-buttons">
            {% for n in range(1, 11) %}
            <button type="submit" name="feeling" value="{{ n }}" class="checkin-btn display">{{ n }}</button>
            {% endfor %}
          </form>
        </div>
        <div class="checkin-scale"><span>Terrible</span><span>Neutral</span><span>Amazing</span></div>
      </section>

      <section class="control-card snapshot-card" id="snapshot-card">
        <h2 class="section-title display"><span class="control-icon">&#9889;</span>Snapshot Status</h2>
        <div class="snapshot-status-box">
          <div class="status-pulse" aria-hidden="true"></div>
          <div class="snapshot-status-title" id="snapshot-status-title">Ready</div>
          <div class="snapshot-status-copy" id="snapshot-status-copy">Pull fresh Intervals.icu data and generate your current performance snapshot.</div>
          <form method="post" action="{{ url_for('analyze') }}" id="snapshot-form">
            <button type="submit" class="btn display" id="snapshot-btn">Generate Snapshot</button>
            <div class="loading-track" id="loading-track"><div class="loading-fill"></div></div>
            <p class="loading-label" id="loading-label"></p>
          </form>
        </div>
      </section>
    </div>

    {% if error %}
    <div class="error-panel">{{ error }}</div>
    {% endif %}

    {% if data %}
    <div class="section dashboard-section">
      <h2 class="section-title display">Dashboard</h2>
      <div class="energy-bank-card zone-glow-{{ data.energy_zone }}">
      <div class="energy-bank-label display">Energy Bank</div>
      <p class="energy-bank-explainer">A single 0-100 readiness score blending your current Form, Fatigue and recent sleep &mdash; the quickest way to see where you stand right now.</p>
      <div class="gauge-wrap">
        <svg class="gauge-svg" viewBox="0 0 200 112" aria-label="Energy Bank gauge">
          <path class="gauge-segment s1" d="M18 94 A82 82 0 0 1 39 39"/>
          <path class="gauge-segment s2" d="M48 31 A82 82 0 0 1 78 16"/>
          <path class="gauge-segment s3" d="M89 13 A82 82 0 0 1 111 13"/>
          <path class="gauge-segment s4" d="M122 16 A82 82 0 0 1 152 31"/>
          <path class="gauge-segment s5" d="M161 39 A82 82 0 0 1 182 94"/>
          <polygon class="gauge-pointer" points="100,7 92,0 108,0" transform="rotate({{ data.needle_angle }} 100 95)" aria-label="Current Energy Bank position"/>
        </svg>
        <div class="gauge-score-wrap">
          <div class="energy-bank-score display" data-animate="{{ data.energy_score }}">{{ data.energy_score }}</div>
          <div class="energy-ring-sub">/ 100</div>
        </div>
      </div>
      <div class="zone-badge zone-{{ data.energy_zone }} display">{{ data.energy_label }}</div>

      {% if data.latest_readiness is not none or data.latest_spo2 is not none %}
      <div class="wearable-row">
        {% if data.latest_readiness is not none %}
        <span class="wearable-stat">Wearable Readiness: <strong>{{ data.latest_readiness }}</strong></span>
        {% endif %}
        {% if data.latest_spo2 is not none %}
        <span class="wearable-stat">SpO2: <strong>{{ data.latest_spo2 }}%</strong></span>
        {% endif %}
      </div>
      {% endif %}

      {% if data.recent_trend %}
      <div class="trend-row">
        <p class="stat-label" style="margin-bottom:4px;">Last 5 Days &middot; Form vs. Your Norm</p>
        <p class="stat-sub" style="margin-bottom:10px;">Shown relative to your own typical Form &mdash; not a generic scale. Near zero means a completely ordinary day for you.</p>
        <div class="trend-bars">
          {% for d in data.recent_trend %}
          <div class="trend-bar-col">
            <div class="trend-bar-track">
              <div class="trend-bar-fill zone-fill-{{ d.zone }}" data-trend-height="{{ [((d.tsb + 30) / 60 * 100), 6]|max }}" style="height:6%;"></div>
            </div>
            {% if d.delta is not none %}
            <div class="trend-bar-value trend-{{ d.zone }}">{{ "%+d"|format(d.delta) }}</div>
            <div class="trend-bar-raw">TSB {{ d.tsb }}</div>
            {% else %}
            <div class="trend-bar-value trend-{{ d.zone }}">{{ d.tsb }}</div>
            {% endif %}
            <div class="trend-bar-day">{{ d.weekday }}</div>
          </div>
          {% endfor %}
        </div>
      </div>
      {% endif %}
      </div>

      <div class="dashboard-grid">
        <div class="gauge-card">
          <div class="gauge-card-header"><span class="gauge-card-icon">&#10084;&#65039;</span> Resting HR</div>
          {% if data.health_rings.rhr %}
          <div class="mini-ring zone-ring-{{ data.health_rings.rhr.color }}" style="--pct: {{ data.health_rings.rhr.pct }};">
            <div class="mini-ring-inner">
              <div class="mini-ring-value">{{ data.latest_rhr }}</div>
            </div>
          </div>
          <div class="gauge-card-status trend-{{ data.health_rings.rhr.color }}">{{ data.health_rings.rhr.status }}</div>
          {% else %}
          <div class="stat-value">{{ data.latest_rhr }}</div>
          {% endif %}
          {% if data.trend_arrows.rhr %}<span class="trend-arrow trend-{{ data.trend_arrows.rhr.color }}">{{ data.trend_arrows.rhr.arrow }}</span>{% endif %}
        </div>
        <div class="gauge-card">
          <div class="gauge-card-header"><span class="gauge-card-icon">&#128200;</span> HRV</div>
          {% if data.health_rings.hrv %}
          <div class="mini-ring zone-ring-{{ data.health_rings.hrv.color }}" style="--pct: {{ data.health_rings.hrv.pct }};">
            <div class="mini-ring-inner">
              <div class="mini-ring-value">{{ data.latest_hrv }}</div>
            </div>
          </div>
          <div class="gauge-card-status trend-{{ data.health_rings.hrv.color }}">{{ data.health_rings.hrv.status }}</div>
          {% else %}
          <div class="stat-value">{{ data.latest_hrv }}</div>
          {% endif %}
          {% if data.trend_arrows.hrv %}<span class="trend-arrow trend-{{ data.trend_arrows.hrv.color }}">{{ data.trend_arrows.hrv.arrow }}</span>{% endif %}
        </div>
        <div class="gauge-card">
          <div class="gauge-card-header"><span class="gauge-card-icon">&#128564;</span> Sleep</div>
          {% if data.health_rings.sleep %}
          <div class="mini-ring zone-ring-{{ data.health_rings.sleep.color }}" style="--pct: {{ data.health_rings.sleep.pct }};">
            <div class="mini-ring-inner">
              <div class="mini-ring-value">{{ data.avg_sleep }}</div>
            </div>
          </div>
          <div class="gauge-card-status trend-{{ data.health_rings.sleep.color }}">{{ data.health_rings.sleep.status }}</div>
          {% else %}
          <div class="stat-value">{{ data.avg_sleep }}</div>
          {% endif %}
          {% if data.trend_arrows.sleep %}<span class="trend-arrow trend-{{ data.trend_arrows.sleep.color }}">{{ data.trend_arrows.sleep.arrow }}</span>{% endif %}
        </div>
        <div class="gauge-card sleep-quality-card {{ data.sleep_quality_class }}">
          <div class="gauge-card-header"><span class="gauge-card-icon">&#9790;</span> Sleep Quality</div>
          <div class="sleep-q">{{ data.sleep_quality_label }}</div>
          <div class="sleep-q-label">{{ data.sleep_quality_text }}</div>
          {% if data.latest_sleep_score is not none %}
          <div class="sleep-score-line">Sleep Score <strong>{{ data.latest_sleep_score }}</strong></div>
          <div class="sleep-score-track"><div class="sleep-score-fill" style="width:{{ data.latest_sleep_score }}%;"></div></div>
          {% endif %}
        </div>
      </div>
      <div class="readiness-strip">
        <div class="readiness-panel">
          <div class="readiness-title">Race Readiness</div>
          <div class="readiness-value trend-{{ data.race_readiness_zone }}">{{ data.race_readiness_label }}</div>
          <div class="readiness-reason">{{ data.race_readiness_reason }}</div>
        </div>
        <div class="readiness-panel">
          <div class="readiness-title">Last Night</div>
          <div class="readiness-value">{{ data.latest_sleep_duration }}</div>
          <div class="readiness-reason">Sleep {{ data.sleep_quality_label }}{% if data.latest_sleep_score is not none %} · score {{ data.latest_sleep_score }}{% endif %}{% if data.latest_sleeping_hr is not none %} · sleeping HR {{ data.latest_sleeping_hr }} bpm{% endif %}</div>
        </div>
      </div>
    </div>

    <details class="recommendation-box">
      <summary><h3 class="display">Coach's Suggestion</h3></summary>
      <p>{{ data.recommendation }}</p>
    </details>

    <details class="training-tips-box">
      <summary><h3 class="display">Training Tips</h3></summary>
      <p class="stat-sub" style="margin-top:10px;">Suggested 60-minute trainer sessions for your next Monday, Wednesday and Friday, based on where you stand right now.</p>
      <p class="training-tips-text">{{ data.training_tips }}</p>
    </details>

    <div class="section training-section">
      <h2 class="section-title display">Training</h2>
      <p class="subtitle" style="margin-bottom:16px;">Last {{ days }} days</p>
      <div class="stat-row">
        <div class="stat-card">
          <div class="stat-label">Fitness (CTL)</div>
          <div class="stat-value" data-animate="{{ data.ctl }}">{{ data.ctl }}</div>
          <div class="zone-badge zone-{{ data.fitness_zone }} display">{{ data.fitness_zone }}</div>
        </div>
        <div class="stat-card">
          <div class="stat-label">Fatigue (ATL)</div>
          <div class="stat-value" data-animate="{{ data.atl }}">{{ data.atl }}</div>
          <div class="zone-badge zone-{{ data.fatigue_zone }} display">{{ data.fatigue_zone }}</div>
        </div>
        <div class="stat-card">
          <div class="stat-label">Form (TSB)</div>
          <div class="stat-value" data-animate="{{ data.tsb }}">{{ data.tsb }}</div>
          <div class="zone-badge zone-{{ data.form_zone }} display">{{ data.form_zone }}</div>
        </div>
        <div class="stat-card">
          <div class="stat-label">Avg Training Calories</div>
          <div class="stat-value" data-animate="{{ data.avg_daily_calories }}">{{ data.avg_daily_calories }}</div>
          <div class="stat-sub">kcal burned in training/day, last {{ days }} days</div>
        </div>
      </div>
      <details class="prose-card">
        <summary><h3>Training Load</h3></summary>
        <p>{{ data.training_load }}</p>
      </details>
    </div>

    <div class="section health-section">
      <h2 class="section-title display">Health</h2>
      <p class="subtitle" style="margin-bottom:16px;">Most recent readings</p>
      <div class="stat-row">
        <div class="stat-card">
          <div class="stat-label">Resting HR</div>
          <div class="stat-value">
            {{ data.latest_rhr }}{% if data.trend_arrows.rhr %}<span class="trend-arrow trend-{{ data.trend_arrows.rhr.color }}">{{ data.trend_arrows.rhr.arrow }}</span>{% endif %}
          </div>
        </div>
        <div class="stat-card">
          <div class="stat-label">HRV</div>
          <div class="stat-value">
            {{ data.latest_hrv }}{% if data.trend_arrows.hrv %}<span class="trend-arrow trend-{{ data.trend_arrows.hrv.color }}">{{ data.trend_arrows.hrv.arrow }}</span>{% endif %}
          </div>
        </div>
        <div class="stat-card">
          <div class="stat-label">Avg Sleep</div>
          <div class="stat-value">
            {{ data.avg_sleep }}{% if data.trend_arrows.sleep %}<span class="trend-arrow trend-{{ data.trend_arrows.sleep.color }}">{{ data.trend_arrows.sleep.arrow }}</span>{% endif %}
          </div>
        </div>
        <div class="stat-card">
          <div class="stat-label">Weight</div>
          <div class="stat-value">
            {{ data.latest_weight }}{% if data.trend_arrows.weight %}<span class="trend-arrow trend-{{ data.trend_arrows.weight.color }}">{{ data.trend_arrows.weight.arrow }}</span>{% endif %}
          </div>
        </div>
      </div>
      <details class="prose-card">
        <summary><h3>Fatigue Signals</h3></summary>
        <p>{{ data.fatigue_signals }}</p>
      </details>
    </div>

    <div class="section power-section">
      <h2 class="section-title display">Power Curve</h2>
      <p class="subtitle" style="margin-bottom:16px;">Best efforts, last 42 days</p>
      {% if data.best_watts %}
      <div class="power-bars">
        {% for p in data.best_watts %}
        <div class="power-bar-row">
          <div class="power-bar-label">{{ p.label }}</div>
          <div class="power-bar-track">
            <div class="power-bar-fill" data-width="{{ p.pct }}" style="width:0%;"></div>
          </div>
          <div class="power-bar-value">{{ p.watts }}W</div>
        </div>
        {% endfor %}
      </div>
      {% else %}
      <p class="subtitle">Power curve data isn't available right now.</p>
      {% if data.best_watts_debug %}
      <p class="subtitle" style="margin-top:10px; word-break:break-all;">[DEBUG] {{ data.best_watts_debug }}</p>
      {% endif %}
      {% endif %}
    </div>

    <div class="section season-section">
      <h2 class="section-title display">Season</h2>
      <p class="subtitle" style="margin-bottom:16px;">Zooming out &mdash; last {{ season_days }} days</p>
      <div class="stat-row" style="grid-template-columns: 1fr;">
        <div class="stat-card">
          <div class="stat-label">Total Time</div>
          <div class="stat-value" data-animate="{{ data.season_hours }}h">{{ data.season_hours }}h</div>
        </div>
      </div>
      <div class="zone-bar-wrap">
        <div class="zone-bar">
          <div class="zone-seg zone-seg-low" data-width="{{ data.zone_low_pct }}" style="width:0%;"></div>
          <div class="zone-seg zone-seg-mod" data-width="{{ data.zone_mod_pct }}" style="width:0%;"></div>
          <div class="zone-seg zone-seg-high" data-width="{{ data.zone_high_pct }}" style="width:0%;"></div>
        </div>
        <div class="zone-bar-labels">
          <span><i class="zone-dot zone-dot-low"></i>Low {{ data.zone_low_pct }}%</span>
          <span><i class="zone-dot zone-dot-mod"></i>Moderate {{ data.zone_mod_pct }}%</span>
          <span><i class="zone-dot zone-dot-high"></i>High {{ data.zone_high_pct }}%</span>
        </div>
      </div>
      {% if data.zone_low_pct != "n/a" %}
      <div class="polarization-card">
        <div class="polar-donut" style="--low:{{ data.zone_low_pct }}; --mod:{{ data.zone_mod_pct }};">
          <div class="polar-center">{{ data.zone_low_pct }}%<small>LOW INTENSITY</small></div>
        </div>
        <div class="polar-legend">
          <div class="readiness-title">90-Day Intensity Distribution</div>
          <div class="polar-legend-row"><span>Low intensity</span><strong style="color:var(--green)">{{ data.zone_low_pct }}%</strong></div>
          <div class="polar-legend-row"><span>Moderate</span><strong style="color:var(--orange)">{{ data.zone_mod_pct }}%</strong></div>
          <div class="polar-legend-row"><span>High intensity</span><strong style="color:var(--red)">{{ data.zone_high_pct }}%</strong></div>
        </div>
      </div>
      {% endif %}
      <details class="prose-card">
        <summary><h3>Training Distribution</h3></summary>
        <p>{{ data.season_distribution }}</p>
      </details>
      <details class="prose-card">
        <summary><h3>Seasonal Outlook</h3></summary>
        <p>{{ data.season_outlook }}</p>
      </details>
    </div>

    <button type="button" class="btn display pdf-btn no-print" id="pdf-btn">Download PDF</button>
    {% endif %}
  </div>
  <script>
    (function () {
      var els = document.querySelectorAll('.stat-value[data-animate], .energy-bank-score[data-animate]');
      els.forEach(function (el) {
        var raw = el.getAttribute('data-animate');
        var match = raw.match(/^(-?\\d+(\\.\\d+)?)(.*)$/);
        if (!match) return; // non-numeric values (e.g. "n/a") stay as-is
        var target = parseFloat(match[1]);
        var decimals = match[2] ? (match[2].length - 1) : 0;
        var suffix = match[3] || '';
        var duration = 900;
        var start = null;
        el.textContent = (0).toFixed(decimals) + suffix;
        function step(ts) {
          if (start === null) start = ts;
          var p = Math.min((ts - start) / duration, 1);
          var eased = 1 - Math.pow(1 - p, 3); // ease-out cubic
          var val = target * eased;
          el.textContent = val.toFixed(decimals) + suffix;
          if (p < 1) {
            requestAnimationFrame(step);
          } else {
            el.textContent = target.toFixed(decimals) + suffix;
          }
        }
        requestAnimationFrame(step);
      });

      // Grow-in animation for the Season zone bar
      var segs = document.querySelectorAll('.zone-seg[data-width], .power-bar-fill[data-width]');
      if (segs.length) {
        setTimeout(function () {
          segs.forEach(function (seg) {
            seg.style.width = seg.getAttribute('data-width') + '%';
          });
        }, 150);
      }

      // Grow-in animation for the 5-day trend bars
      var trendBars = document.querySelectorAll('.trend-bar-fill[data-trend-height]');
      if (trendBars.length) {
        setTimeout(function () {
          trendBars.forEach(function (bar) {
            bar.style.height = bar.getAttribute('data-trend-height') + '%';
          });
        }, 150);
      }

      // Download PDF button - uses the browser's native print-to-PDF
      var pdfBtn = document.getElementById('pdf-btn');
      if (pdfBtn) {
        pdfBtn.addEventListener('click', function () {
          window.print();
        });
      }

      // Loading feedback on Generate Snapshot submit
      var form = document.getElementById('snapshot-form');
      if (form) {
        form.addEventListener('submit', function () {
          var btn = document.getElementById('snapshot-btn');
          var track = document.getElementById('loading-track');
          var fill = track ? track.querySelector('.loading-fill') : null;
          var label = document.getElementById('loading-label');
          var messages = [
            'Pulling your Intervals.icu data...',
            'Crunching fitness, fatigue and form...',
            'Reviewing the last 90 days...',
            'Consulting your AI coach...',
            'Almost there...'
          ];
          btn.disabled = true;
          btn.textContent = 'Analyzing...';
          var statusCard = document.getElementById('snapshot-card');
          var statusTitle = document.getElementById('snapshot-status-title');
          var statusCopy = document.getElementById('snapshot-status-copy');
          if (statusCard) statusCard.classList.add('is-loading');
          if (statusTitle) statusTitle.textContent = 'Analyzing...';
          if (statusCopy) statusCopy.textContent = 'Building your fresh performance snapshot. Please wait a few moments.';
          track.style.display = 'block';
          label.style.display = 'block';
          var i = 0;
          label.textContent = messages[0];
          setInterval(function () {
            i = (i + 1) % messages.length;
            label.textContent = messages[i];
          }, 3200);

          // Climbs quickly at first, then slows as it approaches 92% - never
          // hits 100%, since we don't actually know when the request will
          // finish; the page navigates away once the real response arrives.
          if (fill) {
            var pct = 5;
            fill.style.width = pct + '%';
            setInterval(function () {
              if (pct < 92) {
                pct += (92 - pct) * 0.08;
                fill.style.width = pct + '%';
              }
            }, 250);
          }
        });
      }

      // Simple loading feedback on the Coach Chat submit
      var chatForm = document.getElementById('chat-form');
      if (chatForm) {
        chatForm.addEventListener('submit', function () {
          var chatBtn = document.getElementById('chat-btn');
          chatBtn.disabled = true;
          chatBtn.textContent = 'Thinking...';
        });
      }
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

    # Gauge needle angle: -90deg (score 0, points left) to +90deg (score 100,
    # points right), rotating around the pivot at SVG coords (100, 95).
    needle_angle = round((score * 1.8) - 90, 1)

    return {
        "energy_score": score, "energy_label": label, "energy_zone": zone,
        "needle_angle": needle_angle,
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
    """Conservative, transparent readiness label; not a medical metric."""
    points = 0
    reasons = []
    points += {"green": 2, "grey": 0, "red": -2}.get(form_zone, 0)
    points += {"green": 2, "grey": 0, "red": -2}.get(fatigue_zone, 0)
    if sleep_quality in (1, 2):
        points += 2; reasons.append("sleep quality is strong")
    elif sleep_quality in (3, 4):
        points -= 2; reasons.append("sleep quality is below ideal")
    hrv_vals = [w.get("hrv") for w in sorted(wellness, key=lambda x: x.get("id", ""))[:-1] if isinstance(w.get("hrv"), (int, float))]
    if isinstance(latest_hrv, (int, float)) and len(hrv_vals) >= 5:
        baseline = statistics.median(hrv_vals[-14:])
        if latest_hrv >= baseline * 1.05:
            points += 1; reasons.append("HRV is above your recent baseline")
        elif latest_hrv <= baseline * 0.90:
            points -= 1; reasons.append("HRV is below your recent baseline")
    if points >= 3:
        return "Race Ready", "green", "; ".join(reasons) or "Form and fatigue are favourable versus your own baseline."
    if points <= -3:
        return "Recovery Bias", "red", "; ".join(reasons) or "Current recovery signals are unusually strained for you."
    return "Train Smart", "grey", "; ".join(reasons) or "Signals are mixed or close to your normal range."


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
    race_label, race_zone, race_reason = compute_race_readiness(
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
        "race_readiness_label": race_label,
        "race_readiness_zone": race_zone,
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
                date=a.get("start_date_local", "")[:10],
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


def next_weekday_date(target_weekday, from_date):
    """Next date matching target_weekday (0=Monday..6=Sunday) that is
    strictly AFTER from_date - if today IS that weekday, jump to next week
    rather than suggesting a session for a day that's already happening/over."""
    days_ahead = target_weekday - from_date.weekday()
    if days_ahead <= 0:
        days_ahead += 7
    return from_date + timedelta(days=days_ahead)


def compute_next_key_days():
    today = date.today()
    mon = next_weekday_date(0, today)
    wed = next_weekday_date(2, today)
    fri = next_weekday_date(4, today)
    return [
        (d.strftime("%A"), d.strftime("%B %-d")) for d in (mon, wed, fri)
    ]


def ask_claude(data_text, metrics):
    today = date.today()
    (mon_weekday, mon_date), (wed_weekday, wed_date), (fri_weekday, fri_date) = compute_next_key_days()
    mon_label = f"{mon_weekday}, {mon_date}"
    wed_label = f"{wed_weekday}, {wed_date}"
    fri_label = f"{fri_weekday}, {fri_date}"
    prompt = (
        "You are an expert cycling coach. Today's real date is {today_date} ({today_weekday}). "
        "Use this to correctly name the actual weekday for any date you reference in your "
        "recommendation (e.g. next Monday, this Friday) — do not infer today's date from the "
        "data below, it may lag behind by a day or more. "
        "{athlete_context} "
        "They currently have Fitness (CTL) = {ctl} [{fitness_zone} zone], "
        "Fatigue (ATL) = {atl} [{fatigue_zone} zone], Form (TSB) = {tsb} [{form_zone} zone]. "
        "These green/grey/red zones are calibrated against THIS athlete's own 90-day baseline, "
        "not a generic cutoff — so 'grey' or even 'red' here does not necessarily mean something "
        "is wrong for an athlete who trains at chronic high load; it means it's unusual *for them*. "
        "Frame it that way rather than implying alarm by default. "
        "Analyze the following data. Some wellness entries may include a free-text note "
        "(e.g. reporting an injury, illness or soreness) — if present, factor it explicitly "
        "into fatigue_signals and into the recommendation. The SEASON SUMMARY gives real "
        "time-in-zone percentages (not average power, which is misleading for interval "
        "sessions) — use those percentages, not the recent activity list, to judge whether "
        "training is polarized (mostly low + high intensity, little moderate), pyramidal "
        "(low > moderate > high, but a meaningful moderate chunk), or threshold/sweetspot-heavy "
        "(a large moderate-intensity share).\n\n"
        "Respond ONLY with valid JSON (no markdown fences, no extra text) with exactly these "
        "keys, each a plain-prose string with no bullet points and no markdown symbols. Every "
        "key except \"training_tips\" must have no line breaks either:\n"
        '- "training_load": 2-3 sentences on how recent training load and volume (last {days} '
        "days) have been trending\n"
        '- "season_distribution": 2-3 sentences classifying the {season_days}-day training '
        "distribution (polarized / pyramidal / threshold-heavy) using the real zone percentages, "
        "with brief reasoning\n"
        '- "season_outlook": 3-4 sentences on whether this {season_days}-day pattern is likely '
        "to keep producing improvements given the athlete's race season, and what to adjust if not\n"
        '- "fatigue_signals": 2-3 sentences on resting HR, HRV, sleep trends and any logged notes\n'
        '- "recommendation": 3-5 sentences of specific, general guidance for the next 3-5 days '
        "referencing the actual numbers above. Do not include a specific workout prescription "
        "here - that goes in training_tips instead\n"
        '- "training_tips": ONE specific indoor trainer workout for EACH of these three exact '
        "upcoming dates - {mon_label}, {wed_label}, {fri_label} (the athlete's designated "
        "key/hard training days) - each capped at exactly 60 minutes total including warm-up "
        "and cooldown, done indoors on rollers/trainer via Zwift. These dates are all strictly "
        "in the future relative to today; never substitute a day that has already happened "
        "this week. Every workout must be consistent with what you wrote in recommendation and "
        "season_outlook above (e.g. if you called for more race-specific or race-pace effort "
        "given the racing season, these workouts should reflect that, not undercut it with "
        "lighter/generic intervals). All power targets must respect the REAL POWER CURVE data "
        "below as a hard ceiling for that duration or shorter, and must be physiologically "
        "realistic for a SEATED trainer effort - if an effort would realistically require "
        "standing/sprinting (very short, near-maximal power), say so explicitly in that line "
        "instead of prescribing an unrealistic seated wattage. Format as three blocks separated "
        "by a blank line (\\n\\n), each block structured as: a first line with the exact date "
        "(as given above) followed by a colon and a short workout title; then the structure "
        "(Warm-up / Main set / Cooldown) with duration and target watts, each part on its own "
        "line, all fitting within 60 minutes; then a final line starting with \"Why: \" "
        "explaining in 1-2 sentences why this workout suits that specific date given their "
        "current numbers\n\n"
        "DATA:\n{data_text}"
    ).format(
        today_date=today.isoformat(), today_weekday=today.strftime("%A"),
        athlete_context=ATHLETE_CONTEXT,
        ctl=metrics["ctl"], fitness_zone=metrics["fitness_zone"],
        atl=metrics["atl"], fatigue_zone=metrics["fatigue_zone"],
        tsb=metrics["tsb"], form_zone=metrics["form_zone"],
        mon_label=mon_label, wed_label=wed_label, fri_label=fri_label,
        days=DAYS_BACK, season_days=SEASON_DAYS_BACK, data_text=data_text,
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
            "max_tokens": 2800,
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
        return json.loads(text)
    except json.JSONDecodeError as e:
        preview = text[:300].replace("\n", " ")
        raise json.JSONDecodeError(
            f"{e.msg} | raw response preview: {preview}", e.doc, e.pos
        )


def ask_claude_chat(question, notes, current_data):
    today = date.today()
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
        "dashboard. Today's real date is {today_date} ({today_weekday}). {athlete_context} "
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
        today_date=today.isoformat(), today_weekday=today.strftime("%A"),
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
        data_text = build_data_text(recent_activities, wellness, season_stats, notes, feelings, best_watts)
        analysis = ask_claude(data_text, metrics)
        data = {
            **metrics, **season_stats, **analysis, **energy_bank,
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
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=True)
