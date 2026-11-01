import pandas as pd

def clean_financial_transactions(df: pd.DataFrame) -> pd.DataFrame:
    """Cleans raw financial transactions, handles nulls, and computes net revenue."""
    df['transaction_date'] = pd.to_datetime(df['transaction_date'])
    df['quantity'] = df['quantity'].fillna(1)
    df['unit_price'] = df['unit_price'].fillna(0.0)
    df['discount'] = df['discount'].fillna(0.0)

    # Calculate computed revenue
    df['calculated_revenue'] = (df['unit_price'] * df['quantity']) * (1.0 - df['discount'])
    return df

def aggregate_revenue_by_region(df: pd.DataFrame) -> pd.DataFrame:
    """Aggregates revenue projections by region and product category."""
    cleaned = clean_financial_transactions(df)
    agg = cleaned.groupby(['region', 'product_category']).agg(
        total_transactions=('transaction_id', 'count'),
        total_revenue=('calculated_revenue', 'sum')
    ).reset_index()
    return agg
