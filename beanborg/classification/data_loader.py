import os

import pandas as pd


class DataLoader:
    @staticmethod
    def load_data(filepath: str) -> pd.DataFrame:

        expanded_filepath = os.path.expanduser(filepath)
        if not os.path.exists(expanded_filepath):
            os.makedirs(os.path.dirname(expanded_filepath), exist_ok=True)
            with open(expanded_filepath, "w") as f:
                f.write("date,desc,amount,cat\n")

        data = pd.read_csv(filepath)
        data["date"] = pd.to_datetime(data["date"], format="%Y-%m-%d")
        data["day_of_month"] = pd.to_datetime(data["date"], errors="coerce").dt.day
        data["day_of_week"] = pd.to_datetime(data["date"], errors="coerce").dt.dayofweek
        data["desc"] = data["desc"].astype(str)
        return data

    @staticmethod
    def add_training_row(self, filepath: str, row: pd.Series):
        expanded_filepath = os.path.expanduser(filepath)
        if os.path.exists(expanded_filepath):
            data = pd.read_csv(filepath)
            data = pd.concat([data, row], ignore_index=True)
            data.to_csv(filepath, index=False)
