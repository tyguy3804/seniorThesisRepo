import pandas as pd
import os
import re
import matplotlib.pyplot as plt
from sklearn.model_selection import cross_val_score
from sklearn.tree import DecisionTreeClassifier
from sklearn.tree import export_graphviz
from graphviz import Source
from sklearn.preprocessing import StandardScaler

def clean_features(features):
    #we need to remove lapse rates column because we cannot have a list in the column in order to scale all the features
    #therefore we need to add three more columns, (low_level_lr, mid_level_lr, and high_level_lr), so that the most important data from the lapse rate list is still used for the model
    #we need to change sig-tor value from also being a list

    features = features.drop('year', axis=1)
    features.insert(12, 'upper_lvl_lr', 0)
    features.insert(12, 'mid_lvl_lr', 0)
    features.insert(12, 'sur_lvl_lr', 0)

    features['sur_lvl_lr'] = features['lapse_rates'].apply(lambda x: x[10])
    features['mid_lvl_lr'] = features['lapse_rates'].apply(lambda x: x[6])
    features['upper_lvl_lr'] = features['lapse_rates'].apply(lambda x: x[2])

    features['showalter_idx'] = features['showalter_idx'].apply(lambda x: x[0])
    features['sig_tor'] = features['sig_tor'].apply(lambda x: x[0])
    features = features.drop('lapse_rates', axis=1)


    return features

def clean_labels(labels):

    #We currently have some rows in the label dataframe with mutiple storm event types that the model treats as unique classifications.
    #So set a hierarchy with Tornado, Funnel Cloud, Hail, and Thunderstorm Wind being the only unique classifications
    #Also make sure that tornado_mag, lat_idx, lon_idx are also only 

    priority = ['Tornado', 'Funnel Cloud', 'Hail', 'Thunderstorm Wind']

    def get_primary_event(event_str):
        for p in priority:
            if p.lower() in event_str.lower():
                return p
        return 'N/A'
    
    def get_primary_mag(mag_str):
        if pd.isna(mag_str):
            return None
        
        match = re.search(r'EF?\d', mag_str, re.IGNORECASE)
        return match.group(0) if match else None
    
    labels['storm_event_type'] = labels['storm_event_type'].apply(get_primary_event)
    labels['storm_lat'] = labels['storm_lat'].str.split(',').str[0].str.strip() 
    labels['storm_lon'] = labels['storm_lon'].str.split(',').str[0].str.strip() 
    labels['tornado_mag'] = labels['tornado_mag'].apply(get_primary_mag)

    return labels

def combine_monthly_df():

    print('Combining data from 2007-2011 into feature and label lists.')
    df_features = []
    df_labels = []

    for year in range(2007, 2012):
        for month in range(1, 13):

            feature_path = f"C:/Users/lwojd/Data/metpyCalc/featureData/{year}/{month:02d}/features{month:02d}_{year}.parquet"
            label_path = f"C:/Users/lwojd/Data/metpyCalc/labelData/{year}/{month:02d}/labels{month:02d}_{year}.parquet"

            if os.path.exists(feature_path) and os.path.exists(label_path):
                feature_file = pd.read_parquet(feature_path)
                label_file = pd.read_parquet(label_path)

                feature_new = clean_features(feature_file)
                label_new = clean_labels(label_file)

                df_features.append(feature_new)
                df_labels.append(label_new)

    return df_features, df_labels



def concat_df_full(df_features, df_labels):

    print('Turning feature and label data lists into Dataframes.')
    df_features_combined = pd.concat(df_features, ignore_index=True)
    df_labels_combined = pd.concat(df_labels, ignore_index=True)

    return df_features_combined, df_labels_combined

def feature_scaling(train_df, test_df):
    #scale the features by using standardization
    print("Feature Scaling in progress.")
    print(train_df)

    scaler = StandardScaler().fit(train_df)
    scaled_feature_train = scaler.transform(train_df)

    return scaled_feature_train

def main():

    df_features_month, df_labels_month = combine_monthly_df()
    df_features_year, df_labels_year = concat_df_full(df_features_month, df_labels_month)

    split_idx = int(len(df_features_year) * 0.80)
    
    feature_train_df = df_features_year.iloc[:split_idx]
    feature_test_df = df_features_year.iloc[split_idx:]

    label_train_df = df_labels_year.iloc[:split_idx]
    label_test_df = df_labels_year.iloc[split_idx:]

    

    #tree_clf = DecisionTreeClassifier()
    print('Creating tree_clf.')
    tree_clf = DecisionTreeClassifier(max_depth= 10)
    #tree_clf = DecisionTreeClassifier(max_depth= 15)
    #tree_clf = DecisionTreeClassifier(max_depth= 20)
    print('Fitting treec_clf to data.')
    tree_clf = tree_clf.fit(feature_train_df, label_train_df['storm_event_type'])

    predict_row = feature_test_df.iloc[[100]]
    predict_row_label = label_test_df.iloc[[100]]

    print('Prediction: ', tree_clf.predict(predict_row))
    print('Actual Storm Report: ', predict_row_label)
    print('Training Score: ',tree_clf.score(feature_train_df, label_train_df['storm_event_type']))
    print('Test Score: ',tree_clf.score(feature_test_df, label_test_df['storm_event_type']))
    print('Tree depth: ', tree_clf.get_depth())
    print('Num leaves: ', tree_clf.get_n_leaves())


    export_graphviz(tree_clf, 
                out_file='C:/Users/lwojd/Downloads/tree1.dot',
                max_depth=12,
                feature_names=feature_train_df.columns.tolist(),
                class_names=tree_clf.classes_.tolist(),
                filled=True)
    
main()
