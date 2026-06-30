"""
definitions.py
Dagster Definitions entry point — registers jobs, schedules, and sensors.
"""

from dagster import Definitions

from pipeline import medical_warehouse_pipeline, daily_schedule

defs = Definitions(
    jobs=[medical_warehouse_pipeline],
    schedules=[daily_schedule],
)