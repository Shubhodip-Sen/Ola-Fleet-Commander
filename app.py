"""
OLA FLEET COMMANDER  -  gamified ride-analytics dashboard (July 2024, 103,024 bookings)
Run:  streamlit run app.py
Data: data/ola.db (SQLite).  Built automatically from data/ola_cleaned.csv if missing.
"""
import random
import re
import sqlite3
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

HERE = Path(__file__).resolve().parent
DB, CSV, SQLF = HERE / "data" / "ola.db", HERE / "data" / "ola_cleaned.csv", HERE / "sql" / "ola_analysis.sql"

LIME, INK, AMBER, RED, CYAN, GREY = "#C6F432", "#0E1117", "#FFB400", "#FF5A5F", "#4DD0E1", "#8A93A3"
DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
SUCCESS = "Success"
TARGET_RATE = 70.0  # boss-battle win condition (% success rate)

LEVELS = [(0, "Rookie Rider", "🛵"), (50, "Route Scout", "🧭"), (150, "Fleet Captain", "🚖"),
          (250, "Dispatch Boss", "📡"), (350, "Ola Legend", "👑")]
BADGES = {
    "pole": ("🏁", "Pole Position", "Predict the top-revenue vehicle in the Arena"),
    "boss": ("🐉", "Boss Slayer", f"Push the simulated success rate to {TARGET_RATE:.0f}%+ in the Boss Battle"),
    "time": ("⏱️", "Time Lord", "Find the hour with the highest failure rate"),
    "zone": ("🧭", "Zone Hunter", "Spot the weakest pickup zone"),
    "sharp": ("🎯", "Sharp Shooter", "Score 3+ in the Quiz Arena"),
    "quiz": ("🧠", "Quiz Master", "Score 5/5 in the Quiz Arena"),
    "sql": ("🧙", "Query Wizard", "Run 3 different queries in the SQL Lab"),
    "legend": ("👑", "Ola Legend", "Reach the top level"),
}

st.set_page_config(page_title="OLA Fleet Commander", page_icon="🚖", layout="wide")
st.markdown(f"""
<style>
.block-container {{padding-top: 1.6rem;}}
.hero {{background: linear-gradient(120deg,#1b1f27 0%,#10131a 60%); border:1px solid #2a2f3a; border-radius:16px; padding:18px 24px; margin-bottom:14px;}}
.hero h1 {{margin:0; font-size:2rem; color:{LIME};}} .hero p {{margin:4px 0 0; color:{GREY};}}
.kpi {{background:#161a22; border:1px solid #2a2f3a; border-radius:14px; padding:14px 16px;}}
.kpi .l {{color:{GREY}; font-size:.78rem; text-transform:uppercase; letter-spacing:.06em;}}
.kpi .v {{color:#fff; font-size:1.7rem; font-weight:700;}}
.player {{background:#161a22; border:1px solid {LIME}55; border-radius:14px; padding:14px; text-align:center;}}
.player .lv {{color:{LIME}; font-size:1.15rem; font-weight:700;}}
.badge {{border-radius:14px; padding:14px; text-align:center; border:1px solid #2a2f3a; height:100%;}}
.badge.on {{background:#1d2a0e; border-color:{LIME};}} .badge.off {{background:#161a22; opacity:.45; filter:grayscale(1);}}
.badge .e {{font-size:2rem;}} .badge .n {{font-weight:700;}} .badge .d {{color:{GREY}; font-size:.78rem;}}
.mission {{background:#1b1f27; border-left:4px solid {AMBER}; border-radius:8px; padding:10px 14px; margin:8px 0 12px;}}
.win {{background:#1d2a0e; border:1px solid {LIME}; border-radius:10px; padding:10px 14px;}}
.lose {{background:#2a1416; border:1px solid {RED}; border-radius:10px; padding:10px 14px;}}
</style>""", unsafe_allow_html=True)


# --------------------------------------------------------------------- data
def ensure_db():
    if DB.exists():
        return
    if not CSV.exists():
        st.error("Missing data/ola.db and data/ola_cleaned.csv. Run `python prep_data.py` first.")
        st.stop()
    raw = pd.read_csv(CSV)
    con = sqlite3.connect(DB)
    raw.to_sql("bookings", con, index=False)
    raw.groupby("Vehicle_Type", as_index=False).Vehicle_Image.first().to_sql("vehicle_images", con, index=False)
    con.close()


@st.cache_data(show_spinner="Loading bookings…")
def load():
    ensure_db()
    con = sqlite3.connect(DB)
    cols = ("Booking_ID,Booking_Date,Hour,Day_Of_Week,Day_Num,Booking_Status,Customer_ID,Vehicle_Type,Pickup_Location,"
            "Drop_Location,V_TAT,C_TAT,Canceled_Rides_by_Customer,Canceled_Rides_by_Driver,Incomplete_Rides,"
            "Incomplete_Rides_Reason,Booking_Value,Payment_Method,Ride_Distance,Driver_Ratings,Customer_Rating")
    df = pd.read_sql_query(f"SELECT {cols} FROM bookings", con)
    icons = dict(pd.read_sql_query("SELECT Vehicle_Type, Vehicle_Image FROM vehicle_images", con).values)
    con.close()
    df["Booking_Date"] = pd.to_datetime(df["Booking_Date"])
    df["is_ok"] = df["Booking_Status"] == SUCCESS
    return df, icons


def run_sql(sql: str) -> pd.DataFrame:
    """Read-only SQL for the lab: one SELECT/WITH statement only."""
    s = sql.strip().rstrip(";").strip()
    body = re.sub(r"--.*", "", s).strip().lower()
    if not (body.startswith("select") or body.startswith("with")):
        raise ValueError("Only SELECT / WITH queries are allowed in the Lab.")
    if ";" in body:
        raise ValueError("Run one statement at a time.")
    con = sqlite3.connect(DB.resolve().as_uri() + "?mode=ro", uri=True)
    try:
        return pd.read_sql_query(s, con)
    finally:
        con.close()


@st.cache_data
def preset_queries():
    out = {}
    if SQLF.exists():
        for blk in re.split(r"\n(?=-- Q\d+\.\d+ )", SQLF.read_text(encoding="utf-8"))[1:]:
            title = blk.split("\n")[0].lstrip("- ").strip()
            body = "\n".join(l for l in blk.split("\n")[1:] if not l.strip().startswith("--")).split(";")[0].strip()
            if body:
                out[title] = body
    return out


# ------------------------------------------------------------------- gamification
def init_state():
    ss = st.session_state
    ss.setdefault("xp", 0)
    ss.setdefault("awarded", set())
    ss.setdefault("badges", set())
    ss.setdefault("log", [])
    ss.setdefault("results", {})
    ss.setdefault("sql_runs", set())


def award(key, xp, label):
    ss = st.session_state
    if key in ss.awarded:
        return False
    ss.awarded.add(key)
    ss.xp += xp
    ss.log.append((label, xp))
    st.toast(f"+{xp} XP · {label}", icon="⚡")
    return True


def unlock(badge):
    if badge not in st.session_state.badges:
        st.session_state.badges.add(badge)
        e, n, _ = BADGES[badge]
        st.toast(f"Badge unlocked: {n}", icon=e)
        return True
    return False


def level_info(xp):
    idx = max(i for i, (t, _, _) in enumerate(LEVELS) if xp >= t)
    cur = LEVELS[idx]
    if idx == len(LEVELS) - 1:
        return idx, cur, None, 1.0
    nxt = LEVELS[idx + 1]
    return idx, cur, nxt, (xp - cur[0]) / (nxt[0] - cur[0])


def kpi(col, label, value):
    col.markdown(f'<div class="kpi"><div class="l">{label}</div><div class="v">{value}</div></div>', unsafe_allow_html=True)


def style(fig, h=360):
    fig.update_layout(template="plotly_dark", height=h, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                      margin=dict(l=10, r=10, t=40, b=10), font=dict(size=13))
    return fig


def pct(a, b):
    return 100.0 * a / b if b else 0.0


# ------------------------------------------------------------------------ app
init_state()
full, ICONS = load()
player_slot = st.sidebar.container()

st.sidebar.markdown("### 🎛️ Filters")
st.sidebar.caption("Filters shape the charts. Challenges and quizzes always use the full month so answers stay fair.")
veh_all = sorted(full.Vehicle_Type.unique())
veh_sel = st.sidebar.multiselect("Vehicle type", veh_all, default=veh_all)
dmin, dmax = full.Booking_Date.min().date(), full.Booking_Date.max().date()
date_sel = st.sidebar.date_input("Date range", (dmin, dmax), min_value=dmin, max_value=dmax)
if isinstance(date_sel, tuple) and len(date_sel) == 2:
    d0, d1 = date_sel
else:
    d0 = d1 = date_sel if not isinstance(date_sel, tuple) else date_sel[0]

df = full[full.Vehicle_Type.isin(veh_sel) & (full.Booking_Date.dt.date >= d0) & (full.Booking_Date.dt.date <= d1)]

st.markdown('<div class="hero"><h1>🚖 OLA Fleet Commander</h1><p>July 2024 · Bengaluru ride bookings · '
            'Explore the data, beat the challenges, earn XP and badges.</p></div>', unsafe_allow_html=True)

if df.empty:
    st.warning("No bookings match the current filters. Widen the vehicle or date selection.")
else:
    ok = df[df.Booking_Status == SUCCESS]
    full_ok = full[full.Booking_Status == SUCCESS]
    tabs = st.tabs(["🎮 Mission Control", "🏁 Vehicle Arena", "🐉 Boss Battle", "⏱️ Time Machine",
                    "🗺️ Zone Hunter", "🧠 Quiz Arena", "🧙 SQL Lab", "🏆 Trophy Room"])

    # ------------------------------------------------ 1. Mission Control
    with tabs[0]:
        total, n_ok = len(df), len(ok)
        rate = pct(n_ok, total)
        rating = ok.Customer_Rating.mean()
        health = 0.7 * rate + 0.3 * (rating / 5 * 100)
        c = st.columns(5)
        kpi(c[0], "Bookings", f"{total:,}")
        kpi(c[1], "Success rate", f"{rate:.1f}%")
        kpi(c[2], "Revenue", f"₹{ok.Booking_Value.sum() / 1e6:.2f}M")
        kpi(c[3], "Avg fare", f"₹{ok.Booking_Value.mean():.0f}")
        kpi(c[4], "Avg rating", f"{rating:.2f} ★")
        st.markdown(f'<div class="mission">🎯 <b>Mission:</b> take the platform success rate from '
                    f'<b>{rate:.1f}%</b> to <b>{TARGET_RATE:.0f}%</b>. Head to the Boss Battle to find out how.</div>',
                    unsafe_allow_html=True)
        g1, g2 = st.columns([1, 2])
        with g1:
            gauge = go.Figure(go.Indicator(mode="gauge+number", value=health, number={"suffix": " / 100"},
                              title={"text": "Fleet Health Score"},
                              gauge={"axis": {"range": [0, 100]}, "bar": {"color": LIME},
                                     "steps": [{"range": [0, 50], "color": "#3a1d20"}, {"range": [50, 75], "color": "#3a3320"},
                                               {"range": [75, 100], "color": "#223315"}]}))
            st.plotly_chart(style(gauge, 300), width="stretch")
            with st.expander("How is this scored?"):
                st.write("Health Score = 70% × success rate + 30% × average customer rating (scaled to 100). "
                         "A simple index to track progress, not an Ola metric.")
        with g2:
            daily = df.groupby("Booking_Date").agg(bookings=("Booking_ID", "count"),
                                                   success=("is_ok", "mean")).reset_index()
            daily["success"] *= 100
            fig = go.Figure()
            fig.add_bar(x=daily.Booking_Date, y=daily.bookings, name="Bookings", marker_color=GREY)
            fig.add_scatter(x=daily.Booking_Date, y=daily.success, name="Success rate %", yaxis="y2", line=dict(color=LIME, width=3))
            fig.update_layout(title="Daily bookings vs success rate", yaxis2=dict(overlaying="y", side="right", range=[0, 100], tickvals=[0, 25, 50, 75, 100], showgrid=False),
                              legend=dict(orientation="h", y=-0.15))
            st.plotly_chart(style(fig, 300), width="stretch")
        s1, s2 = st.columns(2)
        stat = df.Booking_Status.value_counts().reset_index()
        pie = px.pie(stat, names="Booking_Status", values="count", hole=0.55, title="Where do the bookings end up?",
                     color="Booking_Status", color_discrete_map={SUCCESS: LIME, "Canceled by Driver": RED,
                                                                 "Canceled by Customer": AMBER, "Driver Not Found": GREY})
        s1.plotly_chart(style(pie, 330), width="stretch")
        pay = ok.Payment_Method.value_counts().reset_index()
        bar = px.bar(pay, x="Payment_Method", y="count", title="How completed rides are paid", color_discrete_sequence=[CYAN])
        s2.plotly_chart(style(bar, 330), width="stretch")

    # ------------------------------------------------ 2. Vehicle Arena
    with tabs[1]:
        rev_full = full_ok.groupby("Vehicle_Type").Booking_Value.sum().sort_values(ascending=False)
        champ = rev_full.index[0]
        st.markdown('<div class="mission">🎯 <b>Challenge:</b> which vehicle type earned the most revenue in July? '
                    'Lock in your guess to reveal the leaderboard. (+40 XP if right, +10 for trying)</div>', unsafe_allow_html=True)
        res = st.session_state.results.get("arena")
        if res is None:
            guess = st.radio("Your champion", veh_all, horizontal=True, key="arena_guess")
            if st.button("🔒 Lock in", key="arena_lock"):
                st.session_state.results["arena"] = (guess, champ)
                if guess == champ:
                    award("arena", 40, "Arena: called the champion"); unlock("pole")
                else:
                    award("arena", 10, "Arena: good try")
                st.rerun()
        else:
            guess, champ = res
            st.markdown(f'<div class="{"win" if guess == champ else "lose"}">'
                        f'{"✅ Called it!" if guess == champ else f"❌ You picked {guess}."} The revenue champion is <b>{champ}</b> '
                        f'(₹{rev_full.iloc[0] / 1e6:.2f}M), but the gap to last place is only '
                        f'{pct(rev_full.iloc[0] - rev_full.iloc[-1], rev_full.iloc[-1]):.1f}%.</div>', unsafe_allow_html=True)
            metric = st.selectbox("Rank vehicles by", ["Revenue (₹)", "Success rate (%)", "Avg fare (₹)",
                                                       "Avg distance (km)", "Customer rating"])
            g = df.groupby("Vehicle_Type").agg(bookings=("Booking_ID", "count"),
                                              success=("is_ok", "mean")).join(
                ok.groupby("Vehicle_Type").agg(revenue=("Booking_Value", "sum"), fare=("Booking_Value", "mean"),
                                               dist=("Ride_Distance", "mean"), rating=("Customer_Rating", "mean")))
            g["success"] *= 100
            col = {"Revenue (₹)": "revenue", "Success rate (%)": "success", "Avg fare (₹)": "fare",
                   "Avg distance (km)": "dist", "Customer rating": "rating"}[metric]
            g = g.sort_values(col, ascending=False).reset_index()
            g["Rank"] = (["🥇", "🥈", "🥉"] + [f"#{i}" for i in range(4, len(g) + 1)])[: len(g)]
            g["icon"] = g.Vehicle_Type.map(ICONS)
            a, b = st.columns([3, 2])
            fig = px.bar(g, x="Vehicle_Type", y=col, text_auto=".3s" if col == "revenue" else ".2f", title=f"Leaderboard · {metric}",
                         color_discrete_sequence=[LIME])
            fig.update_yaxes(range=[g[col].min() * 0.9, g[col].max() * 1.03] if col != "revenue" else None)
            a.plotly_chart(style(fig, 380), width="stretch")
            b.dataframe(g[["Rank", "icon", "Vehicle_Type", col]].rename(columns={"icon": " ", "Vehicle_Type": "Vehicle"}),
                        hide_index=True, width="stretch",
                        column_config={" ": st.column_config.ImageColumn(" ", width="small")})
            st.info("📌 Reality check: vehicle types are very evenly matched on bookings, success rate and ratings. "
                    "The one real outlier is Auto: its rides are ~10 km vs ~25 km for the rest, so its revenue per km is ~2.5× higher.")

    # ------------------------------------------------ 3. Boss Battle
    with tabs[2]:
        fails = df[df.Booking_Status != SUCCESS].Booking_Status.value_counts()
        n_drv, n_cus, n_nf = (int(fails.get(k, 0)) for k in ["Canceled by Driver", "Canceled by Customer", "Driver Not Found"])
        n_fail = n_drv + n_cus + n_nf
        fare = ok.Booking_Value.mean()
        st.markdown(f'<div class="mission">🐉 <b>The Failure Dragon</b> has <b>{n_fail:,}</b> HP: bookings that never became rides. '
                    f'Each rider you win back is worth about ₹{fare:.0f}. Defeat it by lifting the success rate to '
                    f'<b>{TARGET_RATE:.0f}%</b>. (+60 XP)</div>', unsafe_allow_html=True)
        s = st.columns(3)
        p1 = s[0].slider(f"Cut driver cancellations (now {n_drv:,})", 0, 100, 0, 5, format="%d%%")
        p2 = s[1].slider(f"Cut customer cancellations (now {n_cus:,})", 0, 100, 0, 5, format="%d%%")
        p3 = s[2].slider(f"Cut 'driver not found' (now {n_nf:,})", 0, 100, 0, 5, format="%d%%")
        rec = n_drv * p1 / 100 + n_cus * p2 / 100 + n_nf * p3 / 100
        sim_rate = pct(n_ok + rec, len(df))
        hp_left = pct(n_fail - rec, n_fail)
        st.progress(min(max(hp_left / 100, 0), 1.0), text=f"Dragon HP: {n_fail - rec:,.0f} / {n_fail:,} ({hp_left:.0f}%)")
        m = st.columns(3)
        kpi(m[0], "Simulated success rate", f"{sim_rate:.1f}%")
        kpi(m[1], "Rides won back", f"{rec:,.0f}")
        kpi(m[2], "Extra revenue", f"₹{rec * fare / 1e6:.2f}M")
        if sim_rate >= TARGET_RATE:
            st.markdown('<div class="win">🎉 <b>Boss defeated!</b> That would take the platform past the target.</div>', unsafe_allow_html=True)
            if award("boss", 60, "Boss Battle: Failure Dragon defeated"):
                unlock("boss"); st.balloons()
        else:
            need = (TARGET_RATE - sim_rate) / 100 * len(df)
            st.markdown(f'<div class="lose">Not yet. You still need about <b>{need:,.0f}</b> more completed rides to hit {TARGET_RATE:.0f}%.</div>',
                        unsafe_allow_html=True)
        st.caption("Assumption: every booking you win back completes at the average fare. This is an upper-bound what-if, not a forecast.")
        r1, r2 = st.columns(2)
        cd = df[df.Booking_Status == "Canceled by Driver"].Canceled_Rides_by_Driver.value_counts().reset_index()
        cc = df[df.Booking_Status == "Canceled by Customer"].Canceled_Rides_by_Customer.value_counts().reset_index()
        r1.plotly_chart(style(px.bar(cd, y="Canceled_Rides_by_Driver", x="count", orientation="h", title="Why drivers cancel",
                                     color_discrete_sequence=[RED]).update_yaxes(categoryorder="total ascending", title=""), 320), width="stretch")
        r2.plotly_chart(style(px.bar(cc, y="Canceled_Rides_by_Customer", x="count", orientation="h", title="Why customers cancel",
                                     color_discrete_sequence=[AMBER]).update_yaxes(categoryorder="total ascending", title=""), 320), width="stretch")
        st.info(f"📌 Driver cancellations are {pct(n_drv, n_fail):.0f}% of all failures. Two of the top customer reasons "
                "('driver not moving' and 'driver asked to cancel') are driver behaviour too.")

    # ------------------------------------------------ 4. Time Machine
    with tabs[3]:
        by_hour = (~full.is_ok).groupby(full.Hour).mean() * 100
        worst_h = int(by_hour.idxmax())
        st.markdown('<div class="mission">⏱️ <b>Challenge:</b> at which hour of the day do the most bookings fail? '
                    'Pick an hour to unlock the failure chart. (+40 XP if right)</div>', unsafe_allow_html=True)
        hm = df.groupby(["Day_Num", "Hour"]).size().unstack(fill_value=0)
        ndays = df.groupby("Day_Num").Booking_Date.nunique()
        hm = hm.div(ndays.reindex(hm.index), axis=0)
        fig = px.imshow(hm.values, x=[f"{h:02d}" for h in hm.columns], y=[DAYS[i] for i in hm.index], aspect="auto",
                        color_continuous_scale=["#161a22", "#3b4a12", LIME], labels=dict(color="Avg bookings"),
                        title="Average bookings per hour, by weekday (per-day average, so 5-Monday months are not inflated)")
        st.plotly_chart(style(fig, 330), width="stretch")
        res = st.session_state.results.get("time")
        if res is None:
            hr = st.selectbox("Worst hour for failures", list(range(24)), format_func=lambda h: f"{h:02d}:00", key="time_pick")
            if st.button("🔒 Lock in", key="time_lock"):
                st.session_state.results["time"] = (hr, worst_h)
                if hr == worst_h:
                    award("time", 40, "Time Machine: found the worst hour"); unlock("time")
                else:
                    award("time", 10, "Time Machine: good try")
                st.rerun()
        else:
            hr, worst_h = res
            st.markdown(f'<div class="{"win" if hr == worst_h else "lose"}">'
                        f'{"✅ Nailed it." if hr == worst_h else f"❌ You picked {hr:02d}:00."} The worst hour is '
                        f'<b>{worst_h:02d}:00</b> with a {by_hour.max():.1f}% failure rate, versus {by_hour.min():.1f}% at the best hour.</div>',
                        unsafe_allow_html=True)
            fh = by_hour.reset_index(name="failure")
            f2 = px.line(fh, x="Hour", y="failure", markers=True, title="Failure rate by hour (full month)", color_discrete_sequence=[RED])
            f2.update_yaxes(range=[30, 45], title="% of bookings that failed")
            st.plotly_chart(style(f2, 320), width="stretch")
            st.info("📌 Failure sits in a narrow 36-40% band all day. There is no 'bad hour' to fix: the "
                    "problem is structural (driver supply and behaviour), not a rush-hour spike.")

    # ------------------------------------------------ 5. Zone Hunter
    with tabs[4]:
        zone_full = (full.is_ok.groupby(full.Pickup_Location).mean() * 100).sort_values()
        weakest = zone_full.index[0]
        st.markdown('<div class="mission">🧭 <b>Challenge:</b> which pickup zone completes the fewest of its bookings? '
                    'Choose from four suspects. (+40 XP if right)</div>', unsafe_allow_html=True)
        res = st.session_state.results.get("zone")
        if res is None:
            rng = random.Random(11)
            opts = [weakest] + rng.sample([z for z in zone_full.index if z != weakest], 3)
            rng.shuffle(opts)
            pick = st.radio("Weakest pickup zone", opts, horizontal=True, key="zone_pick")
            if st.button("🔒 Lock in", key="zone_lock"):
                st.session_state.results["zone"] = (pick, weakest)
                if pick == weakest:
                    award("zone", 40, "Zone Hunter: found the weakest zone"); unlock("zone")
                else:
                    award("zone", 10, "Zone Hunter: good try")
                st.rerun()
        else:
            pick, weakest = res
            st.markdown(f'<div class="{"win" if pick == weakest else "lose"}">'
                        f'{"✅ Right on target." if pick == weakest else f"❌ You picked {pick}."} <b>{weakest}</b> completes only '
                        f'{zone_full.iloc[0]:.1f}% of bookings (best zone: {zone_full.index[-1]} at {zone_full.iloc[-1]:.1f}%).</div>',
                        unsafe_allow_html=True)
        z = df.groupby("Pickup_Location").agg(bookings=("Booking_ID", "count"),
                                              success=("is_ok", "mean")).reset_index()
        z["success"] *= 100
        if st.session_state.results.get("zone"):
            a, b = st.columns(2)
            low = z.nsmallest(10, "success").sort_values("success", ascending=False)
            a.plotly_chart(style(px.bar(low, x="success", y="Pickup_Location", orientation="h", title="10 weakest pickup zones (success %)",
                                        color_discrete_sequence=[RED]).update_xaxes(range=[55, 66]), 380), width="stretch")
            top = z.nlargest(10, "bookings").sort_values("bookings")
            b.plotly_chart(style(px.bar(top, x="bookings", y="Pickup_Location", orientation="h", title="10 busiest pickup zones",
                                        color_discrete_sequence=[LIME]), 380), width="stretch")
            routes = ok[ok.Pickup_Location != ok.Drop_Location].assign(
                route=lambda x: x.Pickup_Location + " → " + x.Drop_Location).groupby("route").agg(
                rides=("Booking_ID", "count"), revenue=("Booking_Value", "sum")).nlargest(10, "rides").reset_index()
            st.subheader("Top 10 routes by completed rides")
            st.dataframe(routes, hide_index=True, width="stretch")
            st.info("📌 Demand is spread evenly across all 50 zones (about 2,000 bookings each) and no single route has more than ~50 "
                    "rides, so fleet should be positioned city-wide rather than around a few hotspots.")
        else:
            st.caption("Lock in your guess to open the zone charts.")

    # ------------------------------------------------ 6. Quiz Arena
    with tabs[5]:
        rng = random.Random(7)
        top_veh = full_ok.groupby("Vehicle_Type").Booking_Value.sum().idxmax()
        sr = round(pct(len(full_ok), len(full)))
        drv_r = full[full.Booking_Status == "Canceled by Driver"].Canceled_Rides_by_Driver.value_counts()
        pay = full_ok.Payment_Method.value_counts()
        once = round(pct((full.groupby("Customer_ID").size() == 1).sum(), full.Customer_ID.nunique()))
        Q = [
            ("Which vehicle type earned the most revenue?", sorted(full.Vehicle_Type.unique()), top_veh,
             f"{top_veh} led, but the spread between best and worst was under 10%."),
            ("What share of July bookings ended in a completed ride?", [f"{sr - 20}%", f"{sr - 10}%", f"{sr}%", f"{sr + 10}%"], f"{sr}%",
             f"{sr}% completed, so about {100 - sr}% of demand was lost."),
            ("What is the #1 reason drivers cancel?", list(drv_r.index), drv_r.index[0],
             f"'{drv_r.index[0]}' accounts for {pct(drv_r.iloc[0], drv_r.sum()):.0f}% of driver cancellations."),
            ("Which payment method is used for the most completed rides?", list(pay.index), pay.index[0],
             f"{pay.index[0]} covers {pct(pay.iloc[0], pay.sum()):.0f}% of completed rides."),
            ("What share of customers booked exactly once in the month?", [f"{once - 45}%", f"{once - 30}%", f"{once - 15}%", f"{once}%"], f"{once}%",
             f"{once}% were one-time bookers, so retention is the big open question."),
        ]
        st.markdown('<div class="mission">🧠 <b>Quiz Arena:</b> five questions on the real data. +30 XP per correct answer, '
                    '+5 for each attempt. Score 3+ for Sharp Shooter and 5/5 for Quiz Master.</div>', unsafe_allow_html=True)
        done = st.session_state.results.get("quiz")
        if done is None:
            with st.form("quiz"):
                answers = []
                for i, (q, opts, _, _) in enumerate(Q):
                    o = opts[:]
                    random.Random(100 + i).shuffle(o)
                    answers.append(st.radio(f"{i + 1}. {q}", o, index=None, key=f"q{i}"))
                sent = st.form_submit_button("Submit answers")
            if sent:
                if any(a is None for a in answers):
                    st.warning("Answer all five questions first.")
                else:
                    st.session_state.results["quiz"] = answers
                    st.rerun()
        else:
            score = 0
            for i, ((q, _, correct, why), a) in enumerate(zip(Q, done)):
                ok_ = a == correct
                score += ok_
                award(f"quiz{i}", 30 if ok_ else 5, f"Quiz Q{i + 1}: {'correct' if ok_ else 'attempted'}")
                st.markdown(f'<div class="{"win" if ok_ else "lose"}"><b>{i + 1}. {q}</b><br>Your answer: {a} '
                            f'{"✅" if ok_ else "❌ → " + str(correct)}<br><span style="color:{GREY}">{why}</span></div>',
                            unsafe_allow_html=True)
                st.write("")
            st.subheader(f"Score: {score} / {len(Q)}")
            if score >= 3: unlock("sharp")
            if score == len(Q): unlock("quiz")
            if st.button("🔁 Retake quiz"):
                st.session_state.results.pop("quiz")
                for i in range(len(Q)):
                    st.session_state.pop(f"q{i}", None)
                st.rerun()
            st.caption("Retakes are for practice: XP is only awarded once per question.")

    # ------------------------------------------------ 7. SQL Lab
    with tabs[6]:
        st.markdown('<div class="mission">🧙 <b>SQL Lab:</b> run the project queries (or write your own) against the live database. '
                    'Read-only. +20 XP for your first run, and run 3 different queries for the Query Wizard badge.</div>',
                    unsafe_allow_html=True)
        presets = preset_queries()
        if presets:
            pick = st.selectbox("Pick a project query", list(presets.keys()))
            sql = st.text_area("SQL", value=presets[pick], height=230, key=f"sql_{pick}")
        else:
            sql = st.text_area("SQL", value="SELECT Vehicle_Type, COUNT(*) AS bookings FROM bookings GROUP BY 1", height=150)
        if st.button("▶ Run query"):
            try:
                out = run_sql(sql)
                st.dataframe(out.head(500), hide_index=True, width="stretch")
                st.caption(f"{len(out):,} rows" + (" (showing first 500)" if len(out) > 500 else ""))
                st.session_state.sql_runs.add(sql.strip())
                award("sql_first", 20, "SQL Lab: first query run")
                if len(st.session_state.sql_runs) >= 3:
                    unlock("sql")
            except Exception as e:
                st.error(f"Query error: {e}")
        st.caption("Table: bookings · View: v_vehicle_summary is created by the .sql file when you run it in a SQLite shell.")

    # ------------------------------------------------ 8. Trophy Room
    with tabs[7]:
        if st.session_state.xp >= LEVELS[-1][0]:
            unlock("legend")
        st.subheader("Badges")
        cols = st.columns(4)
        for i, (k, (e, n, d)) in enumerate(BADGES.items()):
            on = k in st.session_state.badges
            cols[i % 4].markdown(f'<div class="badge {"on" if on else "off"}"><div class="e">{e}</div><div class="n">{n}</div>'
                                 f'<div class="d">{d}</div></div>', unsafe_allow_html=True)
            if i % 4 == 3:
                cols = st.columns(4)
        st.subheader("XP log")
        if st.session_state.log:
            st.dataframe(pd.DataFrame(st.session_state.log[::-1], columns=["Event", "XP"]), hide_index=True, width="stretch")
        else:
            st.caption("No XP yet. Take on a challenge.")
        if st.button("♻️ Reset progress"):
            for k in ["xp", "awarded", "badges", "log", "results", "sql_runs"]:
                st.session_state.pop(k, None)
            for k in [k for k in st.session_state.keys() if k.startswith(("q", "arena_", "time_", "zone_", "sql_"))]:
                st.session_state.pop(k, None)
            st.rerun()

# --------------------------------------------------------------- player card
if st.session_state.xp >= LEVELS[-1][0]:
    unlock("legend")
idx, cur, nxt, frac = level_info(st.session_state.xp)
with player_slot:
    st.markdown(f'<div class="player"><div style="font-size:2.2rem">{cur[2]}</div><div class="lv">Lv {idx + 1} · {cur[1]}</div>'
                f'<div style="color:{GREY}">{st.session_state.xp} XP · {len(st.session_state.badges)}/{len(BADGES)} badges</div></div>',
                unsafe_allow_html=True)
    st.progress(frac, text=f"{nxt[0] - st.session_state.xp} XP to {nxt[1]}" if nxt else "Max level reached")
    st.divider()
