from collections import OrderedDict


def param_dict(param_str: str) -> OrderedDict():
    # Convert param_str: str() -> params: OrderedDict()
    param_list = param_str.split(",")
    params = OrderedDict()

    if not param_str.strip():
        return params

    for param in param_list:
        if '=' in param:
            key, value = tuple(x.strip() for x in param.split('='))
            params[key] = value
        else:
            key = param.strip()
            params[key] = '*'

    return params
