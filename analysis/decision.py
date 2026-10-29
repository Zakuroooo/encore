"""Step 5: decision - which users to try to save, how, and what it could be worth.
Every rate below is read from the pipeline outputs. Every number that is NOT in the data
(price, discount, save rate, months kept) is an ASSUMPTION, listed in one place and labelled.
Writes outputs/decision.json and outputs/decision_scenarios.csv
"""
import json
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from model_utils import sample_size_two_proportions  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs"

# ---------- assumptions (NOT from the data; Sparkify is a made-up app with no prices) ----------
A = {
    "price_per_month": 9.99,         # a typical 2018 US streaming price, used only as a stand-in
    "discount_per_offer": 5.00,      # the offer: 50% off the next month
    "paid_base": 10_000,             # results are shown per 10,000 paid subscribers, to be easy to scale
    "days_per_month": 30,
    "redeem_rate_if_not_leaving": 0.30,  # email offer: share of NON-churners who would also grab the discount
    # save rate = share of would-be cancellers who take the offer and stay. Unknown -> three scenarios.
    "save_rate": {"low": 0.05, "mid": 0.10, "high": 0.20},
    # months a saved user keeps paying after the discounted month. Unknown -> three scenarios.
    "extra_months_kept": {"low": 1, "mid": 2, "high": 3},
    # A/B test settings, fixed BEFORE any result exists
    "ab_alpha": 0.05, "ab_power": 0.80,
    "ab_control_retained_30d": 0.02,     # assumed: with no offer, ~2% of cancellers come back within 30 days
}

# ---------- facts read from the pipeline ----------
flow = pd.read_csv(OUT / "cancel_flow.csv").set_index("plan")
outcomes = pd.read_csv(OUT / "snapshot_outcomes.csv")
bands = pd.read_csv(OUT / "risk_bands.csv")
model = json.loads((OUT / "model_metrics.json").read_text())
horizon = model["horizon_days"]

paid_out = outcomes[outcomes.plan == "paid"].set_index("outcome")["users"]
paid_users_at_snapshot = int(paid_out.sum())
paid_cancel_rate_window = paid_out.get("cancelled", 0) / paid_users_at_snapshot    # in `horizon` days
paid_cancel_rate_month = paid_cancel_rate_window * A["days_per_month"] / horizon   # simple linear scaling

top_paid = bands[(bands.band == "top_20pct") & (bands.plan == "paid")].iloc[0]
rest_paid = bands[(bands.band == "rest") & (bands.plan == "paid")].iloc[0]
paid_top_share = top_paid.users / (top_paid.users + rest_paid.users)  # share of paid users the model flags
paid_top_precision = top_paid.churned_next_21d / top_paid.users

facts = {
    "cancel_page_users": int(flow.loc["all", "opened_cancel_page"]),
    "cancel_page_confirm_rate": float(flow.loc["all", "confirm_rate"]),
    "median_seconds_cancel_to_confirm": float(flow.loc["all", "median_seconds_to_confirm"]),
    "paid_users_at_snapshot": paid_users_at_snapshot,
    "paid_cancel_rate_21d": round(paid_cancel_rate_window, 4),
    "paid_cancel_rate_month_est": round(paid_cancel_rate_month, 4),
    "model_top20_paid_users": int(top_paid.users),
    "model_top20_paid_churn_rate": round(float(paid_top_precision), 4),
    "model_rest_paid_churn_rate": round(float(rest_paid.churned_next_21d / rest_paid.users), 4),
    "model_p_value_vs_random": model["test"][model["chosen_model"]]["p_value_vs_random"],
}

# ---------- option A: a save offer on the Cancel page (shown only to people about to cancel) ----------
# Per month, per 10,000 paid users. Everyone who sees it was about to cancel (confirm rate above).
attempts = A["paid_base"] * paid_cancel_rate_month * facts["cancel_page_confirm_rate"]
# ---------- option B: e-mail the same offer to the model's top 20% of paid users ----------
contacted = A["paid_base"] * paid_top_share * A["days_per_month"] / horizon   # flagged per month
b_churners = contacted * paid_top_precision

# Money, per saved user: they pay the discounted month (price - discount) plus the extra months.
# Without the offer they would have paid nothing, so all of that is kept revenue.
# A wasted discount = a discount given to someone who was NOT leaving (they would have paid full price).
def kept_per_save(months):
    return (A["price_per_month"] - A["discount_per_offer"]) + months * A["price_per_month"]


rows = []
for scen in ("low", "mid", "high"):
    save, months = A["save_rate"][scen], A["extra_months_kept"][scen]
    # A: only people already cancelling see it, so no discount is wasted
    a_saved = attempts * save
    # B: some users who were never leaving also grab the discount -> wasted
    b_saved = b_churners * save
    b_wasted = (contacted - b_churners) * A["redeem_rate_if_not_leaving"] * A["discount_per_offer"]
    for option, shown, saved, wasted in (("A: offer on Cancel page", attempts, a_saved, 0.0),
                                         ("B: e-mail model's top 20%", contacted, b_saved, b_wasted)):
        rows.append({"option": option, "scenario": scen, "save_rate": save, "extra_months_kept": months,
                     "users_shown_offer": round(shown), "users_saved": round(saved, 1),
                     "revenue_kept": round(saved * kept_per_save(months)), "wasted_discounts": round(wasted),
                     "net_per_month": round(saved * kept_per_save(months) - wasted)})
scen_df = pd.DataFrame(rows).sort_values(["option", "save_rate"])
scen_df.to_csv(OUT / "decision_scenarios.csv", index=False)

# Break-even save rate for option B (mid "months kept"): saves must pay for the wasted discounts.
# Option A has no wasted discounts, so any save rate above zero is a gain (before build cost).
b_wasted_mid = (contacted - b_churners) * A["redeem_rate_if_not_leaving"] * A["discount_per_offer"]
b_break_even = b_wasted_mid / (b_churners * kept_per_save(A["extra_months_kept"]["mid"]))

# ---------- A/B test sizing for option A ----------
p_control = A["ab_control_retained_30d"]
mde_points = A["save_rate"]["low"]                   # smallest effect worth detecting: the low scenario
n_per_arm = sample_size_two_proportions(p_control, p_control + mde_points, A["ab_alpha"], A["ab_power"])
weeks_needed = 2 * n_per_arm / (attempts / A["days_per_month"] * 7)

decision = {
    "assumptions": A, "facts_from_data": facts,
    "monthly_per_10k_paid": {"cancel_page_attempts": round(attempts), "model_flagged_contacts": round(contacted),
                             "model_flagged_true_churners": round(b_churners, 1)},
    "option_b_break_even_save_rate": round(b_break_even, 4),
    "option_b_can_break_even": bool(b_break_even <= 1),
    "ab_test": {"control_retained_30d_assumed": p_control, "minimum_effect_points": mde_points,
                "users_per_arm": n_per_arm, "weeks_needed_at_10k_paid": round(weeks_needed, 1)},
}
(OUT / "decision.json").write_text(json.dumps(decision, indent=2) + "\n")
print(scen_df.to_string(index=False))
print(json.dumps({k: decision[k] for k in ("monthly_per_10k_paid", "option_b_break_even_save_rate", "ab_test")},
                 indent=2))
