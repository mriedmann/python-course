"""Small helpers for Fluvia quote lines: the functions you wrote in U7, kept in one module.

Use them from a notebook next to this file:

    import quote_tools
    quote_tools.discount_class(12.5)   # "high"

A quote line is a dict with at least the keys "quantity" and "unit_price_eur" (numbers).
"""


def quote_value(row, extra_discount_pct=0):
    """Return the value in EUR of one quote line after an optional extra discount in percent."""
    return row["quantity"] * row["unit_price_eur"] * (1 - extra_discount_pct / 100)


def discount_class(pct):
    """Return the discount class "none", "standard" or "high" of a discount in percent.

    Raises ValueError for a negative discount, which is a data error.
    """
    if pct < 0:
        raise ValueError("A discount cannot be negative.")
    if pct == 0:
        return "none"
    if pct < 10:
        return "standard"
    return "high"
