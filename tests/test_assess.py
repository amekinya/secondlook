from datetime import date

from app.engine.assess import Item, assess

TODAY = date(2026, 10, 25)


def v(**kw):
    return assess(Item(**kw), TODAY)


def test_inclined_sleeper_is_illegal_and_matches_rock_n_play_recall():
    r = v(category="inclined_sleeper", brand="Fisher-Price", product_name="Rock 'n Play Sleeper", features={"incline_raised": True})
    assert r["level"] == "ILLEGAL_TO_SELL"
    ids = [x["id"] for x in r["recalls"]]
    assert {"19105", "23088"} & set(ids)
    assert any(x["rule_id"] == "R-RCL-01" for x in r["reasons"])


def test_padded_bumper_banned_but_mesh_liner_ok():
    assert v(category="crib_bumper", features={"padded_bumper": True})["level"] == "ILLEGAL_TO_SELL"
    assert v(category="crib_bumper", features={"mesh_liner": True})["level"] == "OK_SO_FAR"


def test_cribs():
    assert v(category="crib", features={"drop_side": True})["level"] == "ILLEGAL_TO_SELL"
    assert v(category="crib", dom=date(2009, 5, 1))["level"] == "ILLEGAL_TO_SELL"
    assert v(category="crib")["level"] == "CHECK"
    r = v(category="crib", dom=date(2019, 3, 1), features={"padded_bumper": True})
    assert r["level"] == "ILLEGAL_TO_SELL" and "bumper" in r["reasons"][0]["title"].lower()


def test_boppy_lounger_recalled_all_models():
    r = v(category="lounger", brand="Boppy", product_name="Boppy Newborn Lounger")
    assert r["level"] == "RECALLED"
    assert r["recalls"][0]["id"] == "21198" and r["recalls"][0]["match"] == "definite"


def test_snuga_swing_remedy_visible():
    unfixed = v(category="swing", brand="Fisher-Price", product_name="Snuga swing", model_text="GVF83", features={"snuga_headrest_present": True})
    assert unfixed["level"] == "RECALLED"
    fixed = v(category="swing", brand="Fisher-Price", product_name="Snuga swing", model_text="GVF83", features={"snuga_headrest_present": False})
    assert fixed["level"] != "RECALLED" and any(x["rule_id"] == "R-RCL-03" for x in fixed["reasons"])


def test_car_seat_expiry_and_recall():
    r = v(category="car_seat", brand="Evenflo", product_name="Tribute", dom=date(2015, 4, 1))
    assert r["level"] == "UNSAFE_ADVISORY" and r["car_seat"]["expires"] == "2025-04-01"
    r = v(category="car_seat", brand="Graco", product_name="4Ever", dom=date(2018, 1, 1))
    assert any("may already be expired" in x["title"] for x in r["reasons"])
    r = v(category="car_seat", brand="Britax", model_text="B-Safe Gen 2", dom=date(2022, 6, 1))
    assert r["level"] == "RECALLED" and r["recalls"][0]["source"] == "NHTSA"
    r = v(category="car_seat", brand="Chicco", product_name="KeyFit 30")
    assert r["level"] == "CHECK"


def test_unknown_brand_no_problems():
    r = v(category="high_chair", brand="Zzyzx", product_name="wooden high chair")
    assert r["level"] == "OK_SO_FAR" and r["checklist"]
