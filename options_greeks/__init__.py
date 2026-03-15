"""options_greeks — Black-Scholes Pricing & Realized Volatility Engine (Step 23).

Pure-math options library using only Python stdlib (no scipy).

Modules
-------
black_scholes   BS pricing + all 5 closed-form Greeks
implied_vol     Newton-Raphson IV solver with bisection fallback
binary_greeks   Cash-or-nothing binary option Greeks (for Kalshi)
realized_vol    Close-to-close, Parkinson, EWM vol + regime classifier
vol_monitor     Playbook integration: queries raw_market_ticks, publishes intel:vol_surface

Public API
----------
    from options_greeks.black_scholes import bs_price, greeks
    from options_greeks.implied_vol import implied_volatility
    from options_greeks.binary_greeks import binary_price, binary_greeks
    from options_greeks.realized_vol import realized_vol, parkinson_vol, vol_regime
    from options_greeks.vol_monitor import run_vol_monitor

Relationship to logit_pricing
------------------------------
logit_pricing   → Kalshi fair value via logit jump-diffusion (no standard BS)
options_greeks  → Standard BS Greeks + binary Greeks + realized vol
Together they provide a complete Kalshi contract analysis toolkit:
  - logit_pricing.assess_contract()  → fair value & edge
  - binary_greeks()                  → delta/gamma/theta/vega sensitivity
"""

__version__ = "1.0.0"
