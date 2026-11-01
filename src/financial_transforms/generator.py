"""
Simulated Enterprise Financial Invoices & Revenue Generator
Generates both real-time streaming events (Hot Path) and historical batch exports (Cold Path).
"""

import json
import time
import random
import uuid
import datetime
import argparse
from pathlib import Path

REGIONS = ["North America", "Europe", "Asia Pacific", "Latin America", "Middle East & Africa"]
PRODUCT_CATEGORIES = [
    {"name": "Software License", "unit_price": 1200.00},
    {"name": "Cloud Infrastructure", "unit_price": 450.00},
    {"name": "Professional Services", "unit_price": 2500.00},
    {"name": "Support & Maintenance", "unit_price": 800.00},
    {"name": "SaaS Subscription", "unit_price": 350.00}
]
CUSTOMERS = [f"CUST-{100 + i}" for i in range(1, 21)]

def generate_invoice_event():
    """Generates a single enterprise invoice transaction event."""
    product = random.choice(PRODUCT_CATEGORIES)
    quantity = random.randint(1, 20)
    discount = round(random.choice([0.0, 0.05, 0.10, 0.15, 0.20]), 2)
    gross_amount = round(product["unit_price"] * quantity, 2)
    net_revenue = round(gross_amount * (1.0 - discount), 2)

    now = datetime.datetime.now(datetime.timezone.utc)
    return {
        "invoice_id": f"INV-{uuid.uuid4().hex[:8].upper()}",
        "timestamp": now.isoformat(),
        "date": now.strftime("%Y-%m-%d"),
        "customer_id": random.choice(CUSTOMERS),
        "region": random.choice(REGIONS),
        "product_category": product["name"],
        "unit_price": product["unit_price"],
        "quantity": quantity,
        "discount": discount,
        "gross_amount": gross_amount,
        "net_revenue": net_revenue,
        "currency": "USD",
        "payment_status": random.choice(["PAID", "PENDING", "PROCESSING"])
    }

def run_hot_path_stream(interval_sec: float = 2.0, count: int = 50, output_file: str = None):
    """Simulates streaming Hot Path ingestion events."""
    print(f"🚀 Starting Hot Path Event Stream (Generating {count} events every {interval_sec}s)...")
    events = []
    for i in range(count):
        event = generate_invoice_event()
        events.append(event)
        print(f"[{i+1}/{count}] Streaming Hot Event -> Invoice: {event['invoice_id']} | Region: {event['region']} | Net Rev: ${event['net_revenue']}")
        time.sleep(interval_sec)

    if output_file:
        Path(output_file).parent.mkdir(parents=True, exist_ok=True)
        with open(output_file, 'w') as f:
            json.dump(events, f, indent=2)
        print(f"✅ Hot path streaming batch written to {output_file}")

def run_cold_path_batch(num_records: int = 500, output_file: str = "data/sample/cold_path_invoices.csv"):
    """Generates batch historical invoice data for Cold Path ingestion."""
    print(f"📦 Generating Cold Path Batch Dataset ({num_records} historical records)...")
    import pandas as pd

    records = []
    base_date = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=30)

    for _ in range(num_records):
        event = generate_invoice_event()
        # Randomize historical dates over the last 30 days
        random_days = random.randint(0, 30)
        random_hours = random.randint(0, 23)
        event_date = base_date + datetime.timedelta(days=random_days, hours=random_hours)
        event["timestamp"] = event_date.isoformat()
        event["date"] = event_date.strftime("%Y-%m-%d")
        records.append(event)

    df = pd.DataFrame(records)
    Path(output_file).parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_file, index=False)
    print(f"✅ Cold path batch saved to {output_file} ({len(df)} rows)")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Financial Revenue Generator for Fabric Hot/Cold Paths")
    parser.add_argument("--mode", choices=["hot", "cold", "both"], default="both", help="Generator mode")
    parser.add_argument("--hot-count", type=int, default=10, help="Number of hot stream events")
    parser.add_argument("--cold-count", type=int, default=200, help="Number of cold batch records")
    args = parser.parse_args()

    if args.mode in ["hot", "both"]:
        run_hot_path_stream(interval_sec=0.1, count=args.hot_count, output_file="data/sample/hot_stream_batch.json")
    if args.mode in ["cold", "both"]:
        run_cold_path_batch(num_records=args.cold_count, output_file="data/sample/cold_path_invoices.csv")
