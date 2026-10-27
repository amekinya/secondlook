from datetime import date

from app.ai.tasks import lookalike_verdict
from app.engine.assess import Item, assess
from app.engine.recalls import cpsc


def _boppy():
    return next(r for r in cpsc() if "boppy" in r["title"].lower())


def test_lookalike_is_caution_not_recalled():
    b = _boppy()
    it = Item(category="lounger", product_name="baby lounger", listing_text="grey newborn lounger, barely used")
    r = assess(it, date(2026, 10, 26), lookalikes=[{"id": b["id"], "score": 0.94}])
    assert any(x["rule_id"] == "R-RCL-LOOK" for x in r["reasons"])
    assert not any(x["rule_id"] in ("R-RCL-01", "R-CS-RCL") for x in r["reasons"])
    assert r["questions"][0].startswith("Who made it?")


def test_lookalike_kept_when_only_brand_differs():
    cand = {"match": "lookalike"}
    j = {"verdict": "does_not_apply", "decided_by": "notice reading", "same_brand": "no", "same_kind_of_product": "yes", "item_detail_vs_limit": "not_shown"}
    assert lookalike_verdict(j, cand)["verdict"] == "lookalike"
    j2 = j | {"same_kind_of_product": "no"}
    assert lookalike_verdict(j2, cand)["verdict"] == "does_not_apply"
    j3 = j | {"verdict": "does_not_apply", "decided_by": "model number"}
    assert lookalike_verdict(j3, cand)["verdict"] == "does_not_apply"


def test_no_endpoint_no_change():
    it = Item(category="lounger", product_name="baby lounger")
    assert not any(x["rule_id"] == "R-RCL-LOOK" for x in assess(it, date(2026, 10, 26))["reasons"])


def test_lookalike_never_recalled_without_model_number():
    cand = {"match": "lookalike"}
    j = {"verdict": "applies", "decided_by": "notice reading", "same_brand": "unclear", "same_kind_of_product": "yes",
         "recall_limited_to": "several", "item_detail_vs_limit": "matches"}
    assert lookalike_verdict(j, cand)["verdict"] == "lookalike"
    assert lookalike_verdict(j | {"decided_by": "model number"}, cand)["verdict"] == "applies"


def test_lookalike_kept_when_product_line_name_differs():
    j = {"verdict": "does_not_apply", "decided_by": "notice reading", "same_brand": "no", "same_kind_of_product": "yes",
         "recall_limited_to": "named_product_line", "item_detail_vs_limit": "differs"}
    assert lookalike_verdict(j, {"match": "lookalike"})["verdict"] == "lookalike"
    assert lookalike_verdict(j, {"match": "possible", "lookalike_score": 0.95})["verdict"] == "lookalike"


def test_prices_are_not_model_numbers():
    from app.engine.recalls import _models
    assert _models("Graco high chair $100 OBO, pickup 800 Main St") == set()
    assert "1234567" in _models("Graco stroller model 1234567")
    assert "BB501" in _models("Bumbo BB501 seat")
