"""Schema contracts for bronze tables (canonical lower-case names and target types)."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Contract:
    name: str
    columns: dict[str, str]
    required: frozenset[str]


TAXI_TRIPS = Contract(
    name="taxi_trips",
    columns={
        "vendorid": "bigint",
        "tpep_pickup_datetime": "timestamp",
        "tpep_dropoff_datetime": "timestamp",
        "passenger_count": "double",
        "trip_distance": "double",
        "ratecodeid": "double",
        "store_and_fwd_flag": "string",
        "pulocationid": "bigint",
        "dolocationid": "bigint",
        "payment_type": "bigint",
        "fare_amount": "double",
        "extra": "double",
        "mta_tax": "double",
        "tip_amount": "double",
        "tolls_amount": "double",
        "improvement_surcharge": "double",
        "total_amount": "double",
        "congestion_surcharge": "double",
        "airport_fee": "double",
    },
    required=frozenset(
        {
            "tpep_pickup_datetime",
            "tpep_dropoff_datetime",
            "pulocationid",
            "dolocationid",
            "fare_amount",
            "total_amount",
        }
    ),
)

WEATHER_DAILY = Contract(
    name="weather_daily",
    columns={
        "date": "string",
        "temperature_2m_max": "double",
        "temperature_2m_min": "double",
        "precipitation_sum": "double",
    },
    required=frozenset({"date"}),
)

ZONES = Contract(
    name="zones",
    columns={
        "location_id": "bigint",
        "borough": "string",
        "zone": "string",
        "service_zone": "string",
        "updated_at": "string",
    },
    required=frozenset({"location_id", "updated_at"}),
)

PAYMENT_TYPES = Contract(
    name="payment_types",
    columns={
        "payment_type_id": "bigint",
        "payment_name": "string",
        "updated_at": "string",
    },
    required=frozenset({"payment_type_id", "updated_at"}),
)
