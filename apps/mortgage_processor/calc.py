import math

INTEREST_RATE = 0.0218
DEBT_AMOUNT = 6_000_000
INSTALLMENT_COUNT = 30 * 12


def cumulative_repayment(debt_amount, remaining_month_count, cumulative_month_count):
    monthly_ir = INTEREST_RATE / 12
    monthly_repayment_amount = (
        debt_amount
        * monthly_ir
        * math.pow(1 + monthly_ir, remaining_month_count)
        / (math.pow(1 + monthly_ir, remaining_month_count) - 1)
    )
    return int(monthly_repayment_amount * cumulative_month_count)


"""
360 期 6_000_000
共償還 8_179_607
"""

print(cumulative_repayment(DEBT_AMOUNT, INSTALLMENT_COUNT, INSTALLMENT_COUNT))

"""
360 期 6_000_000
繳7期後提前還本 1,100,000
共償還 159_047 + 6_642_229 + 1_100_000 = 7_901_276
"""

repaid_amount_1 = cumulative_repayment(DEBT_AMOUNT, INSTALLMENT_COUNT, 7)
repaid_amount_2 = cumulative_repayment(
    DEBT_AMOUNT - 1_100_000, INSTALLMENT_COUNT - 7, INSTALLMENT_COUNT - 7
)

print(
    repaid_amount_1,
    repaid_amount_2,
    1_100_000,
    repaid_amount_1 + repaid_amount_2 + 1_100_000,
)

"""
353 期 4_900_000
共償還 6_642_229
"""
print(cumulative_repayment(4_900_000, 353, 353))
