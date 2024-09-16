import pandas as pd


class DataLoader:
    @staticmethod
    def load_data(filepath: str) -> pd.DataFrame:
        data = pd.read_csv(filepath)
        data["date"] = pd.to_datetime(data["date"], format="%Y-%m-%d")
        data["day_of_month"] = pd.to_datetime(data["date"], errors="coerce").dt.day
        data["day_of_week"] = pd.to_datetime(data["date"], errors="coerce").dt.dayofweek
        data["desc"] = data["desc"].astype(str)
        return data
