import math
from decimal import Decimal


def decimalize(n: float | str) -> Decimal:
    if isinstance(n, float):
        return Decimal(str(n)).normalize()
        # return Decimal("{:f}".format(n)).normalize()
    elif isinstance(n, str):
        return Decimal(n).normalize()


def lcm(x: Decimal, y: Decimal) -> Decimal:
    scale = Decimal("10000000000000000")
    scaled_x_int = int(x * scale)
    scaled_y_int = int(y * scale)
    scaled_lcm_int = math.lcm(scaled_x_int, scaled_y_int)
    lcm = Decimal(scaled_lcm_int) / scale
    return lcm.normalize()
