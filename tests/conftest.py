import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd
import pytest


@pytest.fixture
def normal_finance_df():
    return pd.DataFrame(
        {
            "year": [2023, 2024, 2025],
            "revenue_m": [100.0, 115.0, 130.0],
            "cogs_m": [55.0, 67.0, 82.0],
            "operating_expenses_m": [25.0, 30.0, 34.0],
            "reported_operating_profit_m": [20.0, 18.0, 14.0],
        }
    )


@pytest.fixture
def normal_operations_df():
    return pd.DataFrame(
        {
            "year": [2023, 2024, 2025],
            "patient_visits": [100000, 110000, 120000],
            "staff_hours": [200000, 242000, 288000],
            "labor_cost_m": [14.0, 17.0, 21.0],
            "average_wait_minutes": [22.0, 25.0, 31.0],
        }
    )
