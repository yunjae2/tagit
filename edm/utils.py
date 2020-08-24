def param_dict(param_str):
    # Convert param_str: str() -> params: {}
    params = dict(item.split("=") for item in param_str.split(","))
    params = {k.strip(): v.strip() for k, v in params.items()}

    return params
