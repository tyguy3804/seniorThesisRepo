from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
import pandas as pd
from io import BytesIO

file_name = "C:/Users/lwojd/Data/metpyCalc/labelData/2007/01/labels01_2007.parquet"
feature_data = pd.read_parquet(file_name, filters= [('storm_lat', '!=', 'N/A')])

print(feature_data)