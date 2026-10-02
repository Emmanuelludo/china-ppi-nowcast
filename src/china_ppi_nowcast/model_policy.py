"""Active model policy; archived artifacts and forecasts remain reproducible."""
RETIRED_MODELS = frozenset({"category_factor", "category_factor_regression"})

def is_active(name):
    return name not in RETIRED_MODELS
