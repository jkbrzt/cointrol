import json as _json
from decimal import Decimal
from functools import partial

import rest_framework.utils.encoders


class JSONEncoder(rest_framework.utils.encoders.JSONEncoder):

    def default(self, o):
        if isinstance(o, Decimal):
            return float(o)
        return super().default(o)


class json:
    dumps = partial(_json.dumps, cls=JSONEncoder)
    loads = partial(_json.loads)
