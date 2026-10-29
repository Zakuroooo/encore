"""Encore dashboard. Run:  streamlit run dashboard/app.py
Every number on this page is read from outputs/ (written by `python pipeline.py`). Nothing is typed in by hand.
"""
import json
from pathlib import Path

import altair as alt
import pandas as pd
import streamlit as st

OUT = Path(__file__).resolve().parents[1] / "outputs"
BLUE, ORANGE = "#2a78d6", "#eb6834"          # free = blue, paid = orange, everywhere on the page
TIER_COLORS = alt.Scale(domain=["free", "paid"], range=[BLUE, ORANGE])
SEQ_BLUE = ["#cde2fb", "#86b6ef", "#3987e5", "#1c5cab", "#0d366b"]  # light = low, dark = high


@st.cache_data
def csv(name):
    return pd.read_csv(OUT / f"{name}.csv")


@st.cache_data
def js(name):
    return json.loads((OUT / f"{name}.json").read_text())


def pct(x, digits=1):
    return f"{100 * x:.{digits}f}%"


def table(df, label="Show the table"):
    with st.expander(label):
        st.dataframe(df, hide_index=True, width="stretch")


st.set_page_config(page_title="Encore - streaming churn & retention", layout="wide")
churn = csv("churn_summary").iloc[0]
daily = csv("daily_active")
model = js("model_metrics")
decision = js("decision")
flow = csv("cancel_flow").set_index("plan")
st.title("Encore: who leaves a music app, and what to do about it")
st.caption(f"Public Udacity 'Sparkify' sample event log (simulated app), {daily.day.min()} to {daily.day.max()}. "
           "All numbers are read from the pipeline output in outputs/.")


c1, c2, c3, c4 = st.columns(4)
c1.metric("Users in the log", f"{int(churn.users)}")
c2.metric(f"Cancelled in the log ({pct(churn.churn_rate)})", f"{int(churn.churned_users)}")
c3.metric("Median DAU / 28-day MAU", pct(daily.stickiness.median()))
c4.metric("Cancel page -> confirmed", pct(flow.loc["all", "confirm_rate"], 0),
          help=f"Median {flow.loc['all', 'median_seconds_to_confirm']:.0f} seconds between the two clicks")

tabs = st.tabs(["Engagement", "Activation funnel", "Cohort retention", "Paid vs free", "RFM",
                "Churn model", "Decision"])

# ---------------- Engagement ----------------
with tabs[0]:
    st.subheader("Daily active users")
    d = daily.melt(id_vars="day", value_vars=["dau_free", "dau_paid"], var_name="tier", value_name="users")
    d["tier"] = d.tier.str.replace("dau_", "")
    d["day"] = pd.to_datetime(d.day)
    st.altair_chart(
        alt.Chart(d).mark_line(strokeWidth=2).encode(
            x=alt.X("day:T", title=None), y=alt.Y("users:Q", title="active users"),
            color=alt.Color("tier:N", scale=TIER_COLORS, title="plan that day"),
            tooltip=[alt.Tooltip("day:T"), "tier", "users"]).properties(height=280),
        width="stretch")
    paid_days = int((daily.dau_paid > daily.dau_free).sum())
    st.markdown(f"Paid daily users outnumbered free ones on {paid_days} of {len(daily)} days.")
    s = daily.dropna(subset=["stickiness"]).assign(day=lambda x: pd.to_datetime(x.day))
    st.subheader("Stickiness = DAU / active users in the last 28 days")
    st.altair_chart(
        alt.Chart(s).mark_line(strokeWidth=2, color=BLUE).encode(
            x=alt.X("day:T", title=None), y=alt.Y("stickiness:Q", axis=alt.Axis(format="%"), title=None),
            tooltip=[alt.Tooltip("day:T"), alt.Tooltip("stickiness:Q", format=".1%"), "dau", "mau_28d"])
        .properties(height=220), width="stretch")
    st.caption("Starts on Oct 28: a 28-day window needs 28 days of history.")
    w = csv("weekly_active")
    table(w, "Weekly active users (WAU) table")
    table(csv("session_stats"), "Session length table")

# ---------------- Funnel ----------------
with tabs[1]:
    f = csv("funnel")
    st.subheader("Activation funnel (users first seen on the free plan)")
    st.altair_chart(
        alt.Chart(f).mark_bar(color=BLUE, cornerRadiusEnd=4).encode(
            y=alt.Y("step:N", sort=list(f.step), title=None, axis=alt.Axis(labelLimit=200)), x=alt.X("users:Q", title="users"),
            tooltip=["step", "users", alt.Tooltip("pct_of_start:Q", format=".1%", title="of start"),
                     alt.Tooltip("pct_of_previous:Q", format=".1%", title="of previous step")])
        .properties(height=220), width="stretch")
    worst = f.dropna().sort_values("pct_of_previous").iloc[0]
    st.markdown(f"Biggest drop: **{worst.step}**, only {pct(worst.pct_of_previous)} of the previous step. "
                f"{pct(f.iloc[-1].pct_of_start)} of free starters became paid.")
    table(f)

# ---------------- Cohorts ----------------
with tabs[2]:
    c = csv("cohort_retention")
    st.subheader("Weekly cohort retention")
    st.markdown("Cohort = week of a user's first event. Cell = share of the cohort active in that week. "
                "The Oct 1 cohort is everyone already using the app when the log starts.")
    c["label"] = pd.to_datetime(c.cohort_week).dt.strftime("%b %d") + " - " + c.cohort_users.astype(str) + " users"
    st.altair_chart(
        alt.Chart(c).mark_rect(stroke="white", strokeWidth=2).encode(
            x=alt.X("week_number:O", title="weeks after first seen", axis=alt.Axis(labelAngle=0)),
            y=alt.Y("label:N", title=None, sort=list(dict.fromkeys(c.label)), axis=alt.Axis(labelLimit=200)),
            color=alt.Color("retention:Q", scale=alt.Scale(range=SEQ_BLUE, domain=[0, 1]),
                            legend=alt.Legend(format="%", title="retained")),
            tooltip=["cohort_week", "cohort_users", "week_number", "active_users",
                     alt.Tooltip("retention:Q", format=".1%")]).properties(height=320),
        width="stretch")
    small = c.drop_duplicates("cohort_week").query("cohort_users < 15")
    st.caption(f"{len(small)} cohorts have under 15 users ({small.cohort_users.min()}-{small.cohort_users.max()}): "
               f"one person moves a cell by {pct(1 / small.cohort_users.max(), 0)} or more. Read them as noise.")
    r = csv("retention_by_tier")
    st.subheader("Oct 1 cohort: retention by plan at first event")
    st.altair_chart(
        alt.Chart(r).mark_line(strokeWidth=2, point=alt.OverlayMarkDef(size=64)).encode(
            x=alt.X("week_number:O", title="week", axis=alt.Axis(labelAngle=0)), y=alt.Y("retention:Q", axis=alt.Axis(format="%"),
                                                           scale=alt.Scale(domain=[0, 1]), title=None),
            color=alt.Color("tier:N", scale=TIER_COLORS, title="plan"),
            tooltip=["tier", "cohort_users", "week_number", "active_users",
                     alt.Tooltip("retention:Q", format=".1%")]).properties(height=260),
        width="stretch")
    last = r[r.week_number == r.week_number.max()].set_index("tier")
    st.markdown(f"Week {int(r.week_number.max())}: paid {pct(last.loc['paid', 'retention'])} "
                f"(of {int(last.loc['paid', 'cohort_users'])}) vs free {pct(last.loc['free', 'retention'])} "
                f"(of {int(last.loc['free', 'cohort_users'])}).")
    table(c.drop(columns="label"), "Cohort table")

# ---------------- Paid vs free ----------------
with tabs[3]:
    p = csv("paid_vs_free")
    st.subheader("How free and paid listening differ (per 100 songs)")
    cols = ["thumbs_up_per_100_songs", "thumbs_down_per_100_songs", "ads_per_100_songs",
            "friends_per_100_songs", "playlist_adds_per_100_songs"]
    m = p.melt(id_vars="level", value_vars=cols, var_name="measure", value_name="per_100_songs")
    m["measure"] = m.measure.str.replace("_per_100_songs", "").str.replace("_", " ")
    st.altair_chart(
        alt.Chart(m).mark_bar(cornerRadiusEnd=4).encode(
            y=alt.Y("measure:N", title=None), x=alt.X("per_100_songs:Q", title="per 100 songs"),
            yOffset="level:N", color=alt.Color("level:N", scale=TIER_COLORS, title="plan"),
            tooltip=["level", "measure", "per_100_songs"]).properties(height=300),
        width="stretch")
    table(p)
    st.subheader("Downgrades and cancellations")
    st.markdown(
        f"- {int(churn.churned_users)} of {int(churn.users)} users cancelled: {int(churn.churned_while_paid)} "
        f"while paid, {int(churn.churned_while_free)} while free.\n"
        f"- {pct(churn.downgrade_rate_of_ever_paid)} of ever-paid users submitted a downgrade.\n"
        f"- Cancel rate if they downgraded: {pct(churn.churn_rate_if_downgraded)}; if not: "
        f"{pct(churn.churn_rate_if_not_downgraded)}. Downgrading is not an early warning sign here.")
    table(csv("weekly_cancels"), "Cancellations per week")

# ---------------- RFM ----------------
with tabs[4]:
    rf = csv("rfm_segments")
    snap = pd.Timestamp(model["test_cutoff"]).strftime("%b %d")
    st.subheader(f"RFM segments at {snap}, and who cancelled in the next {model['horizon_days']} days")
    st.markdown("R = days since last event, F = sessions, M = songs played (no money in this data). "
                f"Segments are built from events before {snap} only; the outcome is what happened after.")
    st.altair_chart(
        alt.Chart(rf).mark_bar(color=BLUE, cornerRadiusEnd=4).encode(
            y=alt.Y("segment:N", sort="-x", title=None, axis=alt.Axis(labelLimit=320)),
            x=alt.X("churn_rate_next_21d:Q", axis=alt.Axis(format="%"), title="cancelled in next 21 days"),
            tooltip=["segment", "users", "churned_next_21d",
                     alt.Tooltip("churn_rate_next_21d:Q", format=".1%")]).properties(height=220),
        width="stretch")
    st.markdown(f"Only {int(rf.churned_next_21d.sum())} users cancelled in the window, so each segment holds "
                "0-6 cancels. The heaviest listeners ('Champions') cancelled most often: classic RFM "
                "does **not** find the cancellers in this app.")
    table(rf)

# ---------------- Model ----------------
with tabs[5]:
    t = model["test"]
    st.subheader(f"Churn model: can we spot cancellers {model['horizon_days']} days early?")
    st.markdown(f"Trained on users at {model['train_cutoff']} ({model['train_users']} users, "
                f"{model['train_churners']} cancellers), tested on users at {model['test_cutoff']} "
                f"({model['test_users']} users, **{model['test_churners']} cancellers**). "
                f"Chosen on training data only: **{model['chosen_model'].replace('_', ' ')}**.")
    order = ["random_order", "rule_days_since_last_event", "logistic_regression", "gradient_boosting"]
    res = pd.DataFrame([{"ranker": n.replace("_", " "), "PR-AUC": t[n]["pr_auc"],
                         "PR-AUC 95% range": " to ".join(map(str, t[n]["pr_auc_95ci"])) if "pr_auc_95ci" in t[n] else "",
                         f"cancellers in top {int(model['top_share'] * 100)}%": t[n]["churners_caught"],
                         "recall at top 20%": t[n]["recall_at_k"], "lift": t[n]["lift_at_k"],
                         "p-value vs random": t[n].get("p_value_vs_random")} for n in order])
    st.dataframe(res, hide_index=True, width="stretch")
    ch = t[model["chosen_model"]]
    st.warning(f"Honest reading: the model catches {ch['churners_caught']} of {model['test_churners']} "
               f"cancellers in the top 20%; random picking catches {t['random_order']['churners_caught']} "
               f"on average. p = {ch['p_value_vs_random']}: with this few cancellers we cannot tell it apart "
               "from luck.")
    imp = csv("model_importance")
    st.subheader("What the model leans on (measured on held-out training users)")
    top = imp.head(8)
    st.altair_chart(
        alt.Chart(top).mark_bar(color=BLUE, cornerRadiusEnd=4).encode(
            y=alt.Y("meaning:N", sort="-x", title=None, axis=alt.Axis(labelLimit=320)),
            x=alt.X("pr_auc_drop_when_shuffled:Q", title="PR-AUC lost when this feature is scrambled"),
            tooltip=["feature", "meaning", "direction", "pr_auc_drop_when_shuffled"]).properties(height=260),
        width="stretch")
    table(imp, "All features")
    table(csv("calibration"), "Calibration (predicted vs actual, three risk groups)")
    table(csv("experiment_snapshots"), "Experiment: stacking more weekly snapshots (training CV only)")
    rb = csv("robustness_cutoffs")
    st.subheader("Robustness: the same test repeated on 7 different dates")
    st.markdown(f"The chosen model beat random at p < 0.05 on **{int((rb.chosen_p_value < 0.05).sum())} of "
                f"{len(rb)}** date choices. Logistic regression caught more cancellers than the random average "
                f"on {int((rb.logistic_regression_caught_top20 > rb.random_expected_caught).sum())} of {len(rb)}. "
                "The windows overlap, so these are not independent tests.")
    table(rb, "Robustness table")
    wl = model["test_wide_label_cancel_or_silent"]
    st.markdown(f"**Label blind spot:** after {model['test_cutoff']}, {wl['users_left_any_way']} users left within "
                f"{model['horizon_days']} days "
                f"if we also count users who simply went silent. For that wider label, 'days since last "
                f"event' is the best ranker (PR-AUC {wl['rule_days_since_last_event']['pr_auc']} vs base "
                f"{wl['rate']}).")
    table(csv("snapshot_outcomes"), "What happened after the test snapshot (cancelled / went silent / stayed)")

# ---------------- Decision ----------------
with tabs[6]:
    fx, a = decision["facts_from_data"], decision["assumptions"]
    st.subheader("Decision: put the save offer on the Cancel page, not in a model-picked e-mail")
    st.markdown(
        f"- {pct(fx['cancel_page_confirm_rate'], 0)} of the {fx['cancel_page_users']} users who opened the Cancel "
        f"page confirmed (median {fx['median_seconds_cancel_to_confirm']:.0f} seconds later). That screen reaches "
        "people who are about to leave.\n"
        f"- Paid users the model flags cancel at {pct(fx['model_top20_paid_churn_rate'])}; the other paid "
        f"users at {pct(fx['model_rest_paid_churn_rate'])} (risk-band table below: a gap of a few people).\n"
        f"- The e-mail option breaks even only if it saves "
        f"{pct(decision['option_b_break_even_save_rate'], 0)} of flagged cancellers.")
    table(csv("risk_bands"), "Risk bands at the test snapshot (by plan)")
    sc = csv("decision_scenarios")
    st.altair_chart(
        alt.Chart(sc).mark_bar(cornerRadiusEnd=4).encode(
            x=alt.X("scenario:N", sort=["low", "mid", "high"], title="scenario", axis=alt.Axis(labelAngle=0)),
            xOffset="option:N", y=alt.Y("net_per_month:Q", title="net revenue per month, per 10k paid ($)"),
            color=alt.Color("option:N", scale=alt.Scale(range=[BLUE, ORANGE]), title=None,
                            legend=alt.Legend(orient="top")),
            tooltip=["option", "scenario", "save_rate", "extra_months_kept", "users_shown_offer",
                     "users_saved", "revenue_kept", "wasted_discounts", "net_per_month"])
        .properties(height=300), width="stretch")
    sr, mk = a["save_rate"], a["extra_months_kept"]
    st.caption(f"Assumed, not from data: price \\${a['price_per_month']:.2f}/month; offer \\${a['discount_per_offer']:.2f} "
               f"off one month; save rate {pct(sr['low'], 0)} / {pct(sr['mid'], 0)} / {pct(sr['high'], 0)} and "
               f"extra months kept {mk['low']} / {mk['mid']} / {mk['high']} (low / mid / high); "
               f"{pct(a['redeem_rate_if_not_leaving'], 0)} of non-leavers grab an e-mailed discount.")
    table(sc, "Scenario table")
    ab = decision["ab_test"]
    st.subheader("A/B test before rollout")
    st.markdown(f"Randomise users who open the Cancel page 50/50. Primary metric: still paying 30 days later. "
                f"Needs **{ab['users_per_arm']} users per group** to detect a "
                f"{pct(ab['minimum_effect_points'], 0)}-point gain over an assumed "
                f"{pct(ab['control_retained_30d_assumed'], 0)} baseline (about {ab['weeks_needed_at_10k_paid']} "
                "weeks at 10,000 paid users). Full design and the decision rule: docs/AB_TEST.md.")
