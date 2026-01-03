"""
Seed Script for Tabular Data - BI Platform Testing.

This script populates the data lake layers (Bronze, Silver, Gold) with
sample tabular data for testing Superset and Dremio integrations.

Tables Generated:
1. sales_transactions - Sales orders with customer and product details
2. customer_analytics - Customer metrics and segmentation
3. product_performance - Product catalog with performance metrics

Data Flow:
- Bronze (MinIO): Raw CSV files
- Silver (MinIO): Cleaned Parquet files
- Gold (MinIO): Enriched/aggregated Parquet files
- Gold (PostgreSQL): Same data for Superset access

Usage:
    python -m cortex.scripts.seed_tabular_data

Or programmatically:
    from cortex.scripts.seed_tabular_data import seed_tabular_data
    await seed_tabular_data()
"""

import io
import logging
import random
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Any

import pandas as pd

logger = logging.getLogger(__name__)

# Sample data generators
REGIONS = ["North America", "Europe", "Asia Pacific", "Latin America", "Middle East"]
COUNTRIES = {
    "North America": ["USA", "Canada", "Mexico"],
    "Europe": ["UK", "Germany", "France", "Spain", "Italy"],
    "Asia Pacific": ["Japan", "China", "Australia", "Singapore", "India"],
    "Latin America": ["Brazil", "Argentina", "Chile", "Colombia"],
    "Middle East": ["UAE", "Saudi Arabia", "Israel", "Qatar"],
}
PRODUCT_CATEGORIES = ["Electronics", "Software", "Services", "Hardware", "Accessories"]
CUSTOMER_SEGMENTS = ["Enterprise", "Mid-Market", "SMB", "Startup", "Government"]
SALES_CHANNELS = ["Direct", "Partner", "Online", "Reseller", "Marketplace"]
PAYMENT_METHODS = ["Credit Card", "Wire Transfer", "Invoice", "PayPal", "Check"]
ORDER_STATUSES = ["Completed", "Shipped", "Processing", "Pending", "Cancelled"]


def generate_sales_transactions(num_records: int = 1000) -> pd.DataFrame:
    """
    Generate sample sales transaction data.

    Args:
        num_records: Number of records to generate.

    Returns:
        DataFrame with sales transaction data.
    """
    random.seed(42)  # Reproducible data

    # Generate date range (last 2 years)
    end_date = datetime.now(timezone.utc)
    start_date = end_date - timedelta(days=730)

    data = []
    for i in range(num_records):
        region = random.choice(REGIONS)
        country = random.choice(COUNTRIES[region])
        category = random.choice(PRODUCT_CATEGORIES)

        # Generate realistic amounts based on category
        base_amounts = {
            "Electronics": (500, 5000),
            "Software": (100, 10000),
            "Services": (1000, 50000),
            "Hardware": (200, 3000),
            "Accessories": (20, 500),
        }
        min_amt, max_amt = base_amounts[category]
        amount = round(random.uniform(min_amt, max_amt), 2)

        # Random date within range
        days_ago = random.randint(0, 730)
        order_date = end_date - timedelta(days=days_ago)

        quantity = random.randint(1, 20)
        discount_pct = random.choice([0, 0, 0, 5, 10, 15, 20])  # Most orders no discount
        discount_amount = round(amount * quantity * discount_pct / 100, 2)
        total_amount = round(amount * quantity - discount_amount, 2)

        data.append({
            "order_id": f"ORD-{2024000000 + i}",
            "order_date": order_date.strftime("%Y-%m-%d"),
            "customer_id": f"CUST-{random.randint(1000, 9999)}",
            "product_id": f"PROD-{random.randint(100, 999)}",
            "product_category": category,
            "quantity": quantity,
            "unit_price": amount,
            "discount_percent": discount_pct,
            "discount_amount": discount_amount,
            "total_amount": total_amount,
            "region": region,
            "country": country,
            "sales_channel": random.choice(SALES_CHANNELS),
            "payment_method": random.choice(PAYMENT_METHODS),
            "order_status": random.choice(ORDER_STATUSES),
            "sales_rep_id": f"REP-{random.randint(100, 150)}",
        })

    return pd.DataFrame(data)


def generate_customer_analytics(num_records: int = 500) -> pd.DataFrame:
    """
    Generate sample customer analytics data.

    Args:
        num_records: Number of records to generate.

    Returns:
        DataFrame with customer analytics data.
    """
    random.seed(43)

    data = []
    for i in range(num_records):
        region = random.choice(REGIONS)
        segment = random.choice(CUSTOMER_SEGMENTS)

        # Segment-based metrics
        segment_multipliers = {
            "Enterprise": (50000, 500000, 0.85, 0.95),
            "Mid-Market": (10000, 100000, 0.75, 0.90),
            "SMB": (1000, 25000, 0.65, 0.85),
            "Startup": (500, 10000, 0.55, 0.80),
            "Government": (20000, 200000, 0.90, 0.98),
        }
        min_ltv, max_ltv, min_retention, max_retention = segment_multipliers[segment]

        lifetime_value = round(random.uniform(min_ltv, max_ltv), 2)
        retention_rate = round(random.uniform(min_retention, max_retention), 3)
        churn_risk = round(1 - retention_rate + random.uniform(-0.1, 0.1), 3)
        churn_risk = max(0, min(1, churn_risk))  # Clamp to 0-1

        # Account age
        account_age_days = random.randint(30, 2000)
        first_purchase = datetime.now(timezone.utc) - timedelta(days=account_age_days)
        last_purchase = first_purchase + timedelta(days=random.randint(0, account_age_days))

        data.append({
            "customer_id": f"CUST-{1000 + i}",
            "company_name": f"Company {chr(65 + i % 26)}{i // 26 + 1} Inc.",
            "segment": segment,
            "region": region,
            "country": random.choice(COUNTRIES[region]),
            "industry": random.choice([
                "Technology", "Healthcare", "Finance", "Manufacturing",
                "Retail", "Education", "Energy", "Transportation"
            ]),
            "employee_count": random.choice([
                "1-10", "11-50", "51-200", "201-500", "501-1000", "1000+"
            ]),
            "annual_revenue_tier": random.choice([
                "<1M", "1M-10M", "10M-50M", "50M-100M", "100M-500M", "500M+"
            ]),
            "lifetime_value": lifetime_value,
            "total_orders": random.randint(1, 100),
            "avg_order_value": round(lifetime_value / random.randint(5, 50), 2),
            "retention_rate": retention_rate,
            "churn_risk_score": churn_risk,
            "nps_score": random.randint(-100, 100),
            "support_tickets_total": random.randint(0, 50),
            "first_purchase_date": first_purchase.strftime("%Y-%m-%d"),
            "last_purchase_date": last_purchase.strftime("%Y-%m-%d"),
            "account_age_days": account_age_days,
            "preferred_channel": random.choice(SALES_CHANNELS),
            "is_active": random.choice([True, True, True, False]),  # 75% active
        })

    return pd.DataFrame(data)


def generate_product_performance(num_records: int = 200) -> pd.DataFrame:
    """
    Generate sample product performance data.

    Args:
        num_records: Number of records to generate.

    Returns:
        DataFrame with product performance data.
    """
    random.seed(44)

    data = []
    for i in range(num_records):
        category = random.choice(PRODUCT_CATEGORIES)

        # Category-based pricing
        category_prices = {
            "Electronics": (299, 2999),
            "Software": (49, 999),
            "Services": (99, 9999),
            "Hardware": (149, 1999),
            "Accessories": (9, 199),
        }
        min_price, max_price = category_prices[category]
        list_price = round(random.uniform(min_price, max_price), 2)
        cost = round(list_price * random.uniform(0.3, 0.6), 2)
        margin_pct = round((list_price - cost) / list_price * 100, 1)

        # Performance metrics
        units_sold_ytd = random.randint(10, 5000)
        revenue_ytd = round(units_sold_ytd * list_price * random.uniform(0.8, 1.0), 2)

        data.append({
            "product_id": f"PROD-{100 + i}",
            "product_name": f"{category} Product {chr(65 + i % 26)}{i // 26 + 1}",
            "category": category,
            "subcategory": f"{category} Type {random.randint(1, 5)}",
            "brand": random.choice([
                "TechCorp", "InnovateTech", "CoreSystems", "PrimeTech", "NextGen"
            ]),
            "sku": f"SKU-{category[:3].upper()}-{1000 + i}",
            "list_price": list_price,
            "cost": cost,
            "margin_percent": margin_pct,
            "units_sold_ytd": units_sold_ytd,
            "revenue_ytd": revenue_ytd,
            "units_in_stock": random.randint(0, 500),
            "reorder_point": random.randint(10, 100),
            "lead_time_days": random.randint(3, 30),
            "supplier_id": f"SUP-{random.randint(1, 20)}",
            "avg_rating": round(random.uniform(3.0, 5.0), 1),
            "review_count": random.randint(0, 500),
            "return_rate_pct": round(random.uniform(0.5, 8.0), 1),
            "is_active": random.choice([True, True, True, True, False]),  # 80% active
            "launch_date": (
                datetime.now(timezone.utc) - timedelta(days=random.randint(30, 1000))
            ).strftime("%Y-%m-%d"),
        })

    return pd.DataFrame(data)


def save_to_minio(
    df: pd.DataFrame,
    table_name: str,
    layer: str,
    file_format: str = "parquet"
) -> str:
    """
    Save DataFrame to MinIO bucket.

    Args:
        df: DataFrame to save.
        table_name: Name of the table.
        layer: Data lake layer (bronze, silver, gold).
        file_format: File format (csv, parquet).

    Returns:
        Object key in MinIO.
    """
    from cortex.services.minio.service import get_minio_service

    minio_service = get_minio_service()

    # Prepare file content
    buffer = io.BytesIO()
    if file_format == "csv":
        df.to_csv(buffer, index=False)
        content_type = "text/csv"
        extension = "csv"
    else:
        df.to_parquet(buffer, index=False, engine="pyarrow")
        content_type = "application/octet-stream"
        extension = "parquet"

    buffer.seek(0)
    file_content = buffer.read()

    # Determine bucket
    bucket_map = {
        "bronze": minio_service.bronze_bucket,
        "silver": minio_service.silver_bucket,
        "gold": minio_service.gold_bucket,
    }
    bucket = bucket_map[layer]

    # Object key with timestamp
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d")
    object_key = f"tabular/{table_name}/{table_name}_{timestamp}.{extension}"

    # Upload to MinIO using client directly
    data_stream = io.BytesIO(file_content)
    minio_service.client.put_object(
        bucket,
        object_key,
        data_stream,
        length=len(file_content),
        content_type=content_type,
    )

    logger.info(f"Saved {table_name} to MinIO {layer}/{object_key}")
    return object_key


def save_to_postgres(df: pd.DataFrame, table_name: str) -> None:
    """
    Save DataFrame to PostgreSQL Gold layer.

    Args:
        df: DataFrame to save.
        table_name: Name of the table.
    """
    from cortex.database.connection import get_database_service

    db_service = get_database_service()

    # Use pandas to_sql for automatic schema creation
    table_full_name = f"gold_{table_name}"
    df.to_sql(
        table_full_name,
        db_service.engine,
        if_exists="replace",
        index=False,
    )

    logger.info(f"Saved {len(df)} records to PostgreSQL {table_full_name}")


def check_tabular_data_exists() -> bool:
    """
    Check if tabular data already exists in PostgreSQL Gold layer.

    Returns:
        True if data exists, False otherwise.
    """
    try:
        from sqlalchemy import text

        from cortex.database.connection import get_database_service

        db_service = get_database_service()

        with db_service.engine.connect() as conn:
            result = conn.execute(text(
                "SELECT EXISTS (SELECT 1 FROM information_schema.tables "
                "WHERE table_name = 'gold_sales_transactions')"
            ))
            return result.scalar()
    except Exception as e:
        logger.warning(f"Error checking tabular data existence: {e}")
        return False


async def seed_tabular_data() -> tuple[int, int]:
    """
    Seed all tabular data to MinIO and PostgreSQL.

    Returns:
        Tuple of (success_count, error_count).
    """
    print("=" * 60)
    print("SEEDING TABULAR DATA FOR BI PLATFORM")
    print("=" * 60)

    success_count = 0
    error_count = 0

    tables = [
        ("sales_transactions", generate_sales_transactions, 1000),
        ("customer_analytics", generate_customer_analytics, 500),
        ("product_performance", generate_product_performance, 200),
    ]

    for table_name, generator_func, num_records in tables:
        try:
            print(f"\nGenerating {table_name} ({num_records} records)...")
            df = generator_func(num_records)

            # Save to MinIO layers
            print(f"  Saving to MinIO Bronze (CSV)...")
            save_to_minio(df, table_name, "bronze", "csv")

            print(f"  Saving to MinIO Silver (Parquet)...")
            save_to_minio(df, table_name, "silver", "parquet")

            print(f"  Saving to MinIO Gold (Parquet)...")
            save_to_minio(df, table_name, "gold", "parquet")

            # Save to PostgreSQL Gold
            print(f"  Saving to PostgreSQL Gold...")
            save_to_postgres(df, table_name)

            print(f"  ✓ {table_name} complete!")
            success_count += 1

        except Exception as e:
            print(f"  ✗ Error with {table_name}: {e}")
            logger.error(f"Error seeding {table_name}: {e}")
            error_count += 1

    print("\n" + "=" * 60)
    print(f"COMPLETE: {success_count} tables seeded, {error_count} errors")
    print("=" * 60)
    print("\nData available at:")
    print("  - Superset: Connect to PostgreSQL tables (gold_*)")
    print("  - Dremio: Connect to MinIO gold bucket (/tabular/*)")
    print("=" * 60)

    return success_count, error_count


def seed_tabular_data_sync() -> tuple[int, int]:
    """Synchronous wrapper for seed_tabular_data."""
    import asyncio
    return asyncio.run(seed_tabular_data())


if __name__ == "__main__":
    seed_tabular_data_sync()
