from __future__ import annotations

from flask import Flask, render_template_string

app = Flask(__name__)


PHYSIOLOGICAL_CARDS = [
    {
        "emoji": "💗",
        "title": "AUTONOMIC",
        "value": "MIXED",
        "value_class": "muted",
        "description": "Autonomic markers are not aligned strongly enough for a single directional call.",
        "meaning": "Signals point in different directions, so the system avoids a forced yes/no verdict.",
    },
    {
        "emoji": "😴",
        "title": "RECOVERY",
        "value": "WATCH",
        "value_class": "warn",
        "description": "At least one sleep/subjective recovery signal is below the athlete's recent norm.",
        "meaning": "A caution flag. Something is a bit below normal and worth monitoring, but it is not an alarm by itself.",
    },
    {
        "emoji": "⚡",
        "title": "TRAINING",
        "value": "CONTROLLED",
        "value_class": "good",
        "description": "Acute and chronic load are in a broadly controlled relationship for this athlete.",
        "meaning": "Load is being managed within a reasonable range for the current context.",
    },
    {
        "emoji": "🫁",
        "title": "AEROBIC",
        "value": "LEARNING",
        "value_class": "cool",
        "description": "Not enough comparable steady Z2 sessions yet for a reliable longitudinal efficiency call.",
        "meaning": "The model does not have enough clean, comparable data yet, so it stays humble instead of pretending certainty.",
    },
    {
        "emoji": "🩸",
        "title": "ENERGY",
        "value": "HIGH DEMAND",
        "value_class": "warn",
        "description": "Recent training creates high glycogen/replenishment pressure; this is a fueling context, not a fatigue diagnosis.",
        "meaning": "Nutrition and replenishment needs are elevated. This is about support demand, not necessarily poor form.",
    },
]

STATUS_GUIDE = [
    ("MIXED", "Signals disagree, so the system avoids a single forced conclusion."),
    ("WATCH", "A mild caution flag: worth monitoring, not an automatic problem."),
    ("CONTROLLED", "In a manageable or expected range for the current context."),
    ("LEARNING", "Not enough clean, comparable data yet for a confident call."),
    ("HIGH DEMAND", "Higher support or replenishment need, not automatically high fatigue."),
]

COACH_CALL = (
    "Six days out, the taper priority is clear: protect the fitness already built, keep legs feeling snappy, "
    "and arrive at Livorno with full glycogen and a calm autonomic system. Today's PM slot is the last realistic "
    "opportunity for any race-specific stimulus before the event; after that, sessions should progressively lighten. "
    "Given the post-heat HRV dip, the GI disruption, and the 6/10 subjective score, keep tonight easy — a short heat "
    "activation ride is appropriate to maintain the heat-adaptation signal without adding meaningful fatigue. Tomorrow "
    "AM can include one brief sweet-spot or race-pace activation block to remind the legs what race effort feels like; "
    "tomorrow PM should be a pure spin. From Wednesday onward, drop to one easy session per day maximum. On nutrition: "
    "glycogen replenishment pressure is HIGH. Prioritise rice, pasta, oats and other dairy-free carbohydrate sources tonight "
    "and tomorrow — avoid all lactose until after the race. No deliberate carb-loading protocol yet (that starts 2–3 days out), "
    "but general high-carbohydrate eating now is exactly right."
)

HTML = """
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>The Lab · Snapshot v36 UI refined</title>
  <style>
    :root {
      --bg: #070a11;
      --panel: rgba(16, 24, 40, 0.90);
      --panel-2: rgba(11, 18, 31, 0.94);
      --stroke: rgba(151, 163, 184, 0.18);
      --text: #f6f2ea;
      --muted: #bcc8d9;
      --cyan: #33d8e8;
      --green: #30d582;
      --amber: #ffbf52;
      --softblue: #9bb5df;
      --pink: #ff5a8c;
      --shadow: 0 18px 50px rgba(0, 0, 0, 0.42);
      --radius: 26px;
      --card-radius: 20px;
    }

    * { box-sizing: border-box; }
    html, body { height: 100%; }
    body {
      margin: 0;
      padding: 22px;
      background:
        radial-gradient(circle at 20% 0%, rgba(49, 120, 198, 0.14), transparent 28%),
        radial-gradient(circle at 80% 30%, rgba(22, 169, 186, 0.08), transparent 24%),
        linear-gradient(180deg, #06090f 0%, #04070d 100%);
      color: var(--text);
      font-family: Georgia, "Times New Roman", serif;
    }

    .dashboard {
      width: min(1450px, 100%);
      margin: 0 auto;
      display: grid;
      grid-template-columns: 2.2fr 1fr;
      gap: 14px;
    }

    .panel {
      background: linear-gradient(180deg, rgba(17,23,36,0.97), rgba(8,12,22,0.97));
      border: 1px solid var(--stroke);
      border-radius: var(--radius);
      box-shadow: var(--shadow);
      position: relative;
      overflow: hidden;
    }

    .panel::before {
      content: "";
      position: absolute;
      inset: 0;
      background: radial-gradient(circle at 50% 50%, rgba(26, 86, 142, 0.10), transparent 55%);
      pointer-events: none;
    }

    .panel > * { position: relative; z-index: 1; }

    .section-head {
      display: flex;
      align-items: flex-start;
      justify-content: space-between;
      gap: 16px;
      margin-bottom: 16px;
    }

    .head-left {
      display: flex;
      align-items: flex-start;
      gap: 14px;
    }

    .section-icon {
      width: 42px;
      height: 42px;
      flex: 0 0 42px;
      display: grid;
      place-items: center;
      border-radius: 999px;
      font-size: 22px;
      background: rgba(255, 184, 41, 0.12);
      border: 1px solid rgba(255, 184, 41, 0.42);
      box-shadow: inset 0 0 0 1px rgba(255,255,255,0.04);
    }

    h1, h2, h3, h4, p { margin: 0; }

    .title-xl {
      font-size: 24px;
      line-height: 1.1;
      font-weight: 700;
      letter-spacing: 0.01em;
      text-transform: uppercase;
    }

    .subtitle {
      margin-top: 8px;
      color: var(--muted);
      font-size: 15px;
      line-height: 1.45;
    }

    .phys-panel {
      padding: 22px 22px 18px;
      min-height: 468px;
    }

    .phys-grid {
      display: grid;
      grid-template-columns: repeat(5, minmax(0, 1fr));
      gap: 14px;
      margin-top: 10px;
    }

    .phys-card {
      min-height: 270px;
      padding: 18px 16px;
      border-radius: var(--card-radius);
      border: 1px solid rgba(161, 170, 189, 0.16);
      background: linear-gradient(180deg, rgba(16,24,40,0.72), rgba(9,14,25,0.78));
      display: flex;
      flex-direction: column;
      gap: 18px;
    }

    .phys-card-head {
      display: flex;
      flex-direction: column;
      align-items: flex-start;
      gap: 10px;
    }

    .phys-title-row {
      display: flex;
      align-items: center;
      gap: 10px;
      min-height: 28px;
    }

    .phys-emoji {
      font-size: 22px;
      line-height: 1;
    }

    .phys-title {
      font-size: 18px;
      font-weight: 700;
      text-transform: uppercase;
      line-height: 1.15;
    }

    .phys-value {
      font-size: 17px;
      font-weight: 700;
      letter-spacing: 0.01em;
      text-transform: uppercase;
      padding-left: 32px;
    }

    .phys-value.warn { color: var(--amber); }
    .phys-value.good { color: var(--cyan); }
    .phys-value.cool { color: var(--softblue); }
    .phys-value.muted { color: #bdc8d9; }

    .phys-desc {
      color: #edf2ff;
      font-size: 15px;
      line-height: 1.8;
    }

    .phys-foot {
      display: grid;
      grid-template-columns: 1.45fr 1fr;
      gap: 14px;
      margin-top: 16px;
      align-items: stretch;
    }

    .foot-note,
    .guide-box {
      border: 1px solid rgba(161, 170, 189, 0.16);
      border-radius: 18px;
      background: rgba(9, 14, 25, 0.45);
      padding: 14px 16px;
    }

    .foot-note {
      color: var(--muted);
      font-size: 14px;
      line-height: 1.55;
      display: flex;
      align-items: center;
    }

    .guide-title {
      font-size: 14px;
      text-transform: uppercase;
      letter-spacing: 0.06em;
      color: var(--cyan);
      margin-bottom: 10px;
      font-weight: 700;
    }

    .guide-list {
      display: grid;
      gap: 8px;
    }

    .guide-item {
      font-size: 13.5px;
      line-height: 1.45;
      color: var(--muted);
    }

    .guide-item strong {
      color: var(--text);
      display: inline-block;
      min-width: 100px;
    }

    .sleep-panel {
      padding: 18px 18px 20px;
      min-height: 468px;
    }

    .sleep-pill {
      padding: 10px 16px;
      border-radius: 999px;
      border: 1px solid rgba(255, 191, 82, 0.55);
      color: var(--amber);
      font-weight: 700;
      font-size: 14px;
      white-space: nowrap;
    }

    .sleep-copy {
      color: var(--muted);
      font-size: 15px;
      line-height: 1.55;
      margin: 8px 0 14px;
    }

    .sleep-card,
    .sleep-subcard {
      border-radius: 18px;
      border: 1px solid rgba(69, 205, 227, 0.22);
      background: linear-gradient(180deg, rgba(8, 29, 46, 0.55), rgba(9, 17, 31, 0.55));
      padding: 16px;
    }

    .sleep-card {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 18px;
      margin-bottom: 12px;
    }

    .sleep-label,
    .mini-label {
      font-size: 14px;
      font-weight: 700;
      text-transform: uppercase;
      color: #d9ddf0;
      margin-bottom: 8px;
      line-height: 1.2;
    }

    .sleep-big {
      font-size: 30px;
      font-weight: 700;
    }

    .sleep-delta {
      color: var(--amber);
      font-size: 16px;
      font-weight: 700;
      text-align: right;
    }

    .sleep-subgrid {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 12px;
    }

    .mini-value {
      font-size: 20px;
      font-weight: 700;
      margin-bottom: 6px;
    }

    .mini-copy {
      font-size: 13.8px;
      line-height: 1.6;
      color: var(--muted);
    }

    .sleep-note {
      margin-top: 16px;
      color: #e7ebf7;
      font-size: 14px;
      line-height: 1.8;
    }

    .wide {
      grid-column: 1 / -1;
    }

    .readiness-panel {
      padding: 18px 22px;
      min-height: 150px;
      display: flex;
      align-items: center;
      gap: 28px;
    }

    .gauge {
      width: 100px;
      height: 100px;
      border-radius: 999px;
      background: conic-gradient(var(--green) 0 324deg, rgba(48, 213, 130, 0.20) 324deg 360deg);
      display: grid;
      place-items: center;
      position: relative;
      flex: 0 0 auto;
    }

    .gauge::after {
      content: "";
      position: absolute;
      inset: 10px;
      border-radius: 999px;
      background: #09111d;
      box-shadow: inset 0 0 0 1px rgba(255,255,255,0.04);
    }

    .gauge-inner {
      position: relative;
      z-index: 1;
      text-align: center;
    }

    .gauge-score {
      font-size: 32px;
      font-weight: 700;
      line-height: 1;
    }

    .gauge-den {
      font-size: 16px;
      color: var(--muted);
      margin-top: 4px;
    }

    .readiness-title {
      font-size: 28px;
      font-weight: 700;
      line-height: 1.15;
    }

    .readiness-state {
      margin-top: 8px;
      font-size: 24px;
      font-weight: 700;
    }

    .readiness-note {
      margin-top: 8px;
      font-size: 16px;
      color: var(--muted);
    }

    .coach-panel {
      padding: 18px 22px 22px;
    }

    .coach-kicker {
      color: var(--cyan);
      font-size: 14px;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.07em;
      margin-bottom: 12px;
    }

    .coach-title {
      font-size: 28px;
      line-height: 1.15;
      font-weight: 700;
      margin-bottom: 16px;
    }

    .coach-grid {
      display: grid;
      grid-template-columns: minmax(0, 2.2fr) minmax(280px, 0.95fr);
      gap: 22px;
      align-items: start;
    }

    .coach-body {
      font-size: 16px;
      line-height: 1.62;
      text-align: justify;
      text-justify: inter-word;
      hyphens: auto;
      max-width: none;
    }

    .coach-side {
      border: 1px solid rgba(161, 170, 189, 0.16);
      background: rgba(9, 14, 25, 0.45);
      border-radius: 18px;
      padding: 15px 16px;
    }

    .coach-side-title {
      font-size: 13px;
      color: var(--amber);
      text-transform: uppercase;
      letter-spacing: 0.07em;
      margin-bottom: 10px;
      font-weight: 700;
    }

    .coach-side-copy {
      display: grid;
      gap: 10px;
      font-size: 14px;
      line-height: 1.5;
      color: var(--muted);
    }

    .bottom-panel {
      padding: 18px 18px 18px 22px;
      display: flex;
      justify-content: space-between;
      gap: 24px;
      align-items: center;
      min-height: 170px;
    }

    .bottom-head {
      display: flex;
      gap: 14px;
      align-items: flex-start;
    }

    .small-round {
      width: 44px;
      height: 44px;
      border-radius: 14px;
      background: rgba(255,255,255,0.03);
      border: 1px solid rgba(161, 170, 189, 0.16);
      display: grid;
      place-items: center;
      font-size: 20px;
      color: var(--amber);
      flex: 0 0 44px;
    }

    .bottom-title {
      font-size: 26px;
      line-height: 1.12;
      font-weight: 700;
      margin-bottom: 6px;
    }

    .bottom-copy {
      color: var(--muted);
      font-size: 15px;
      line-height: 1.45;
      max-width: 900px;
    }

    .phase-card {
      flex: 0 0 250px;
      min-height: 116px;
      border-radius: 18px;
      border: 1px solid rgba(111, 87, 255, 0.38);
      background: linear-gradient(180deg, rgba(31, 25, 56, 0.55), rgba(18, 15, 34, 0.74));
      padding: 14px 16px;
      display: flex;
      flex-direction: column;
      justify-content: center;
      gap: 10px;
    }

    .phase-top {
      display: flex;
      align-items: center;
      gap: 10px;
    }

    .phase-icon {
      width: 18px;
      text-align: center;
      color: #c8b7ff;
      font-size: 16px;
    }

    .phase-label {
      font-size: 14px;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.05em;
      color: #ddd9f8;
    }

    .phase-main {
      font-size: 19px;
      font-weight: 700;
      text-transform: uppercase;
      padding-left: 28px;
    }

    .phase-value {
      font-size: 16px;
      font-weight: 700;
      text-transform: uppercase;
      color: #a8ffe8;
      padding-left: 28px;
    }

    @media (max-width: 1180px) {
      .dashboard { grid-template-columns: 1fr; }
      .phys-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
      .phys-foot,
      .coach-grid,
      .sleep-subgrid { grid-template-columns: 1fr; }
      .bottom-panel {
        align-items: flex-start;
        flex-direction: column;
      }
      .phase-card { width: 100%; flex-basis: auto; }
    }

    @media (max-width: 760px) {
      body { padding: 12px; }
      .phys-grid { grid-template-columns: 1fr; }
      .readiness-panel { flex-direction: column; align-items: flex-start; }
      .sleep-card { flex-direction: column; align-items: flex-start; }
      .sleep-delta { text-align: left; }
    }
  </style>
</head>
<body>
  <main class="dashboard">
    <section class="panel phys-panel">
      <div class="section-head">
        <div class="head-left">
          <div class="section-icon">🧭</div>
          <div>
            <h1 class="title-xl">Physiological State</h1>
            <p class="subtitle">Five systems kept separate so one strong metric cannot hide a conflicting signal.</p>
          </div>
        </div>
      </div>

      <div class="phys-grid">
        {% for card in physiological_cards %}
        <article class="phys-card">
          <div class="phys-card-head">
            <div class="phys-title-row">
              <span class="phys-emoji">{{ card.emoji }}</span>
              <h3 class="phys-title">{{ card.title }}</h3>
            </div>
            <div class="phys-value {{ card.value_class }}">{{ card.value }}</div>
          </div>
          <p class="phys-desc">{{ card.description }}</p>
        </article>
        {% endfor %}
      </div>

      <div class="phys-foot">
        <div class="foot-note">
          Training/recovery interpretation only - not a medical diagnosis. THE LAB keeps the systems separate instead of hiding them inside one opaque score.
        </div>
        <aside class="guide-box">
          <div class="guide-title">How to read the labels</div>
          <div class="guide-list">
            {% for label, meaning in status_guide %}
            <div class="guide-item"><strong>{{ label }}</strong> {{ meaning }}</div>
            {% endfor %}
          </div>
        </aside>
      </div>
    </section>

    <aside class="panel sleep-panel">
      <div class="section-head">
        <div class="head-left">
          <div class="section-icon">🌙</div>
          <div>
            <h2 class="title-xl">Adaptive Sleep<br>Baseline</h2>
            <p class="sleep-copy">What you can habitually sleep is separated from a fixed reference target.</p>
          </div>
        </div>
        <div class="sleep-pill">SHORT VS HABITUAL</div>
      </div>

      <div class="sleep-card">
        <div>
          <div class="sleep-label">Weekday Habitual</div>
          <div class="sleep-big">7h 37m</div>
        </div>
        <div class="sleep-delta">-73 min last night</div>
      </div>

      <div class="sleep-subgrid">
        <div class="sleep-subcard">
          <div class="mini-label">Mon–Fri Habitual</div>
          <div class="mini-value">7h 37m</div>
          <div class="mini-copy">Typical middle range 6h 40m–8h 13m · 30 nights</div>
        </div>
        <div class="sleep-subcard">
          <div class="mini-label">Weekend Habitual</div>
          <div class="mini-value">8h 08m</div>
          <div class="mini-copy">Typical middle range 7h 13m–8h 35m · 12 nights</div>
        </div>
      </div>

      <p class="sleep-note"><strong>Reference ≠ daily penalty target.</strong> Garmin 7h38m remains visible as a reference; THE LAB judges today's duration primarily against the matching weekday opportunity; 14d trend: SHORTER (-16 min).</p>
    </aside>

    <section class="panel readiness-panel wide">
      <div class="gauge">
        <div class="gauge-inner">
          <div class="gauge-score">90</div>
          <div class="gauge-den">/100</div>
        </div>
      </div>
      <div>
        <div class="readiness-title">Race Readiness</div>
        <div class="readiness-state">Race Ready</div>
        <div class="readiness-note">HRV below personal range</div>
      </div>
    </section>

    <section class="panel coach-panel wide">
      <div class="coach-kicker">🔔 Coach Call</div>
      <h2 class="coach-title">What I would do from here</h2>
      <div class="coach-grid">
        <p class="coach-body">{{ coach_call }}</p>
        <aside class="coach-side">
          <div class="coach-side-title">Status guide</div>
          <div class="coach-side-copy">
            <div><strong>WATCH</strong> = caution, not alarm.</div>
            <div><strong>CONTROLLED</strong> = currently manageable load relationship.</div>
            <div><strong>LEARNING</strong> = insufficient comparable data.</div>
            <div><strong>HIGH DEMAND</strong> = increased fueling/replenishment need.</div>
            <div><strong>MIXED</strong> = signals are not fully aligned.</div>
          </div>
        </aside>
      </div>
    </section>

    <section class="panel bottom-panel wide">
      <div class="bottom-head">
        <div class="small-round">🏃</div>
        <div>
          <div class="bottom-title">Upcoming Sessions</div>
          <div class="bottom-copy">Built from snapshot time, completed training, health/availability restrictions and upcoming events. Each session is paired with its own intra-workout fueling target directly underneath.</div>
        </div>
      </div>

      <aside class="phase-card">
        <div class="phase-top">
          <div class="phase-icon">↕</div>
          <div class="phase-label">Training Phase</div>
        </div>
        <div class="phase-main">Taper</div>
        <div class="phase-value">High</div>
      </aside>
    </section>
  </main>
</body>
</html>
"""


@app.route("/")
def index() -> str:
    return render_template_string(
        HTML,
        physiological_cards=PHYSIOLOGICAL_CARDS,
        status_guide=STATUS_GUIDE,
        coach_call=COACH_CALL,
    )


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
