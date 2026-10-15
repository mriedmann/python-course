"""Hidden checks for unit 00-demo. One check_<exercise label>(ns) per exercise."""


def check_net_value(ns: dict) -> None:
    assert "net_value" in ns, "Store your result in a variable called net_value."
    q = ns["quotes"][0]
    expected = q["quantity"] * q["unit_price_eur"] * (1 - q["discount_pct"] / 100)
    assert isinstance(ns["net_value"], (int, float)), "net_value should be a number, not text."
    gross = q["quantity"] * q["unit_price_eur"]
    assert q["discount_pct"] == 0 or abs(ns["net_value"] - gross) > 0.005, (
        "That is the gross value. Subtract the discount, which is given in percent."
    )
    assert abs(ns["net_value"] - expected) < 0.005, (
        "Not yet: net value = quantity x unit price x (1 - discount_pct / 100)."
    )
