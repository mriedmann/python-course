"""Hidden checks for U7 "Functions: a reusable formula". One check_<exercise label>(ns) each."""


def _value(row):
    return row["quantity"] * row["unit_price_eur"]


def _close(a, b):
    return isinstance(a, (int, float)) and abs(a - b) < 0.005


def _function(ns, name):
    assert callable(ns.get(name)), (
        f"Define a function called {name} first: a def line, then the indented body."
    )
    return ns[name]


def check_retype(ns):
    quote_value = _function(ns, "quote_value")
    row = ns["quotes"][3]
    result = quote_value(row)
    assert result is not None, (
        "Your function gives back None. Hand the result back with return, not print."
    )
    assert _close(result, _value(row)), (
        "The formula is not right yet: the value of a quote line is quantity x unit price."
    )
    assert "first_value" in ns, "Now call the function on quotes[0] and store the result in first_value."
    assert _close(ns["first_value"], _value(ns["quotes"][0])), (
        "first_value should be the value of the first quote line, quotes[0]."
    )


def check_fix_order(ns):
    product_name = _function(ns, "product_name")
    quotes, products = ns["quotes"], ns["products"]
    assert product_name(quotes[5]) == products[quotes[5]["product_id"]]["product_name"], (
        "Keep the body of product_name as it was: it looks the product up in products."
    )
    assert ns.get("first_name") == products[quotes[0]["product_id"]]["product_name"], (
        "Call product_name on quotes[0] after the def block and store the result in first_name."
    )


def check_extra_discount(ns):
    quote_value = _function(ns, "quote_value")
    row = ns["quotes"][4]
    try:
        plain = quote_value(row)
    except TypeError:
        raise AssertionError(
            "Calling quote_value with only a row fails. Give the new parameter a default of 0."
        ) from None
    assert plain is not None, "Your function gives back None. Hand the result back with return."
    assert _close(plain, _value(row)), (
        "Without an extra discount the function must still give quantity x unit price."
    )
    try:
        reduced = quote_value(row, extra_discount_pct=10)
    except TypeError:
        raise AssertionError("Name the new parameter exactly extra_discount_pct.") from None
    assert _close(reduced, _value(row) * 0.9), (
        "With extra_discount_pct=10 the value should drop by 10 percent: multiply by (1 - 10 / 100)."
    )
    assert "offer" in ns, "Store the value of quotes[2] with 5 percent extra discount in offer."
    assert _close(ns["offer"], _value(ns["quotes"][2]) * 0.95), (
        "offer should be the value of quotes[2] with extra_discount_pct=5."
    )


def check_discount_classes(ns):
    discount_class = _function(ns, "discount_class")
    for pct, expected in ((0, "none"), (0.5, "standard"), (9.9, "standard"), (10, "high"), (25, "high")):
        got = discount_class(pct)
        assert got is not None, (
            f"discount_class({pct}) gives back None. Every class needs a return line."
        )
        assert got == expected, (
            f'discount_class({pct}) should give "{expected}". Check the class limits: 0, below 10, 10 or more.'
        )
    try:
        discount_class(-2)
    except ValueError:
        pass
    else:
        raise AssertionError("discount_class(-2) should refuse the input: raise a ValueError first.")
    expected = {"none": 0, "standard": 0, "high": 0}
    for row in ns["quotes"]:
        expected[discount_class(row["discount_pct"])] += 1
    assert ns.get("counts") == expected, (
        "The function works. Now loop over quotes and add 1 to the counts entry of each line's class."
    )
