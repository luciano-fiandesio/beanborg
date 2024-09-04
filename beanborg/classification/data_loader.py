import pandas as pd
from typing import Dict, Any

class DataLoader:
    @staticmethod
    def load_data(filepath: str) -> pd.DataFrame:
        data = pd.read_csv(filepath)
        data["day_of_month"] = pd.to_datetime(data["date"], errors="coerce").dt.day
        data["day_of_week"] = pd.to_datetime(data["date"], errors="coerce").dt.dayofweek
        return data