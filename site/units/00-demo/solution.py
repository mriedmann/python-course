# exercise: net_value
q = quotes[0]
net_value = q["quantity"] * q["unit_price_eur"] * (1 - q["discount_pct"] / 100)
