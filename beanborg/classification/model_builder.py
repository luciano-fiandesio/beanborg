from sklearn.compose import ColumnTransformer
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import MinMaxScaler, OneHotEncoder
from imblearn.pipeline import make_pipeline
from imblearn.over_sampling import SMOTE
from sklearn.svm import SVC

class ModelBuilder:
    @staticmethod
    def build_model():
        column_transformer = ColumnTransformer(
            transformers=[
                ("desc_tfidf", TfidfVectorizer(ngram_range=(1, 3)), "desc"),
                ("day_scaler", MinMaxScaler(), ["day_of_month"]),
                ("day_week_onehot", OneHotEncoder(), ["day_of_week"]),
            ],
            remainder="passthrough",
        )

        pipeline = make_pipeline(
            column_transformer,
            SMOTE(random_state=42, k_neighbors=1),
            SVC(probability=True, kernel="linear", C=1.0),
        )

        return pipeline