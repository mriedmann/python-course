# exercise: retype
def quote_value(row):
    """Return the value in EUR of one quote line."""
    value = row["quantity"] * row["unit_price_eur"]
    return value


first_value = quote_value(quotes[0])
print(f"{first_value:.2f}")

# exercise: fix_order
def product_name(row):
    """Return the product name of one quote line."""
    return products[row["product_id"]]["product_name"]


first_name = product_name(quotes[0])
print(first_name)

# exercise: extra_discount
def quote_value(row, extra_discount_pct=0):
    """Return the value in EUR of one quote line after an optional extra discount."""
    value = row["quantity"] * row["unit_price_eur"] * (1 - extra_discount_pct / 100)
    return value


offer = quote_value(quotes[2], extra_discount_pct=5)
print(f"{offer:.2f}")

# exercise: discount_classes
def discount_class(pct):
    """Return the discount class "none", "standard" or "high" of a discount in percent."""
    if pct < 0:
        raise ValueError("A discount cannot be negative.")
    if pct == 0:
        return "none"
    elif pct < 10:
        return "standard"
    else:
        return "high"


counts = {"none": 0, "standard": 0, "high": 0}
for row in quotes:
    counts[discount_class(row["discount_pct"])] += 1
print(counts)
