import pandas as pd
from financial_transforms.transforms import clean_financial_transactions, aggregate_revenue_by_region

def test_clean_financial_transactions():
    data = {
        'transaction_id': ['T1', 'T2'],
        'transaction_date': ['2026-10-01', '2026-10-02'],
        'customer_id': ['C1', 'C2'],
        'region': ['NA', 'EU'],
        'product_category': ['Svc', 'Lic'],
        'unit_price': [100.0, 200.0],
        'quantity': [2, 3],
        'discount': [0.1, 0.0],
        'revenue': [180.0, 600.0]
    }
    df = pd.DataFrame(data)
    result = clean_financial_transactions(df)
    assert 'calculated_revenue' in result.columns
    assert result.loc[0, 'calculated_revenue'] == 180.0

def test_aggregate_revenue_by_region():
    data = {
        'transaction_id': ['T1', 'T2'],
        'transaction_date': ['2026-10-01', '2026-10-01'],
        'customer_id': ['C1', 'C2'],
        'region': ['NA', 'NA'],
        'product_category': ['Svc', 'Svc'],
        'unit_price': [100.0, 100.0],
        'quantity': [1, 1],
        'discount': [0.0, 0.0],
        'revenue': [100.0, 100.0]
    }
    df = pd.DataFrame(data)
    agg = aggregate_revenue_by_region(df)
    assert len(agg) == 1
    assert agg.loc[0, 'total_revenue'] == 200.0
