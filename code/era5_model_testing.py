import pandas as pd
import os
import re
from graphviz import Source
import matplotlib.pyplot as plt
from sklearn.utils import class_weight
from sklearn.model_selection import cross_val_score
from sklearn.tree import DecisionTreeClassifier
from sklearn.tree import export_graphviz
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import f1_score, classification_report
from sklearn.neural_network import MLPClassifier
from imblearn.under_sampling import RandomUnderSampler
from imblearn.over_sampling import RandomOverSampler


def clean_features(features):
    #we need to remove lapse rates column because we cannot have a list in the column in order to scale all the features
    #therefore we need to add three more columns, (low_level_lr, mid_level_lr, and high_level_lr), so that the most important data from the lapse rate list is still used for the model
    #we need to change sig-tor value from also being a list
    #removed lfc_temp and lfc_press because 71% of the values were NaN and it wasn't a very important value to the model

    features = features.drop('year', axis=1)
    features.insert(12, 'upper_lvl_lr', 0)
    features.insert(12, 'mid_lvl_lr', 0)
    features.insert(12, 'sur_lvl_lr', 0)

    features['sur_lvl_lr'] = features['lapse_rates'].apply(lambda x: x[10])
    features['mid_lvl_lr'] = features['lapse_rates'].apply(lambda x: x[6])
    features['upper_lvl_lr'] = features['lapse_rates'].apply(lambda x: x[2])

    features['showalter_idx'] = features['showalter_idx'].apply(lambda x: x[0])
    features['sig_tor'] = features['sig_tor'].apply(lambda x: x[0])
    features = features.drop('lfc_temp', axis=1)
    features = features.drop('lfc_press', axis=1)
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

def tree_clf_main():

    df_features_month, df_labels_month = combine_monthly_df()
    df_features_year, df_labels_year = concat_df_full(df_features_month, df_labels_month)

    split_idx = int(len(df_features_year) * 0.80)
    
    feature_train_df = df_features_year.iloc[:split_idx]
    feature_test_df = df_features_year.iloc[split_idx:]

    label_train_df = df_labels_year.iloc[:split_idx]
    label_test_df = df_labels_year.iloc[split_idx:]

    counts = label_train_df['storm_event_type'].value_counts()

    strategy = {}
    for label, count in counts.items():
        strategy[label] = int(count)

    strategy['N/A'] = 60000

    print('Attempting to over sample severe rows.')
    #ros = RandomUnderSampler(sampling_strategy=strategy, random_state=42)
    #X_resampled, Y_resampled = ros.fit_resample(feature_train_df, label_train_df['storm_event_type'])
    rus = RandomUnderSampler(sampling_strategy=strategy, random_state=42)
    X_resampled, Y_resampled = rus.fit_resample(feature_train_df, label_train_df['storm_event_type'])

    print('Creating tree_clf.')
    tree_clf = DecisionTreeClassifier(max_depth= 20, class_weight= 'balanced')

    print('Fitting treec_clf to data.')
    tree_clf = tree_clf.fit(X_resampled, Y_resampled)

    y_pred = tree_clf.predict(feature_test_df)
    print(classification_report(label_test_df['storm_event_type'], y_pred))
    print('Tree depth: ', tree_clf.get_depth())
    print('Num leaves: ', tree_clf.get_n_leaves())

    #print(label_train_df['storm_event_type'].value_counts())
    #print(label_train_df['storm_event_type'].value_counts(normalize=True))

    #predict_index = [681972, 912728, 1153804, 1221287, 1221427, 1221637, 1222056, 1222621, 1223603, 1224060]
    #for i in range (0,10):
    #    
    #    predict_row = feature_test_df.iloc[[predict_index[i]]]
    #    actual_predict = label_test_df.iloc[[predict_index[i]]]
#
    #    print(f'Prediction #{i}: {tree_clf.predict(predict_row)}')
    #    print(f'Actual Storm Report #{i}: {actual_predict}')
    #    print('')


    export_graphviz(tree_clf, 
                out_file='C:/Users/lwojd/Downloads/tree1.dot',
                max_depth=5,
                feature_names=feature_train_df.columns.tolist(),
                class_names=tree_clf.classes_.tolist(),
                filled=True)

def random_forest_main():

    df_features_month, df_labels_month = combine_monthly_df()
    df_features_year, df_labels_year = concat_df_full(df_features_month, df_labels_month)

    split_idx = int(len(df_features_year) * 0.80)
    
    feature_train_df = df_features_year.iloc[:split_idx]
    feature_test_df = df_features_year.iloc[split_idx:]

    label_train_df = df_labels_year.iloc[:split_idx]
    label_test_df = df_labels_year.iloc[split_idx:]

    #if it's still a problem consider under sample the non-severe class
    print("Generating Random Forest Classifier.")
    counts = label_train_df['storm_event_type'].value_counts()

    strategy = {}
    for label, count in counts.items():
        strategy[label] = int(count)

    strategy['N/A'] = 5000

    rus = RandomUnderSampler(sampling_strategy=strategy,random_state=42)
    X_resampled, Y_resampled = rus.fit_resample(feature_train_df, label_train_df['storm_event_type'])
    random_forest_clf = RandomForestClassifier(class_weight='balanced_subsample', n_estimators=100, max_leaf_nodes=16, n_jobs=-1, random_state=42)
    print("Fitting data to the Random Forest")
    random_forest_clf.fit(X_resampled, Y_resampled)

    y_pred = random_forest_clf.predict(feature_test_df)
    print(classification_report(label_test_df['storm_event_type'], y_pred))


    #predict_index = [671972, 681972, 700000, 912728, 1153804, 1221287, 1221427, 1221637, 1222056, 1222621, 1223603, 1224060]
    #print("Prediciting...")
    #for i in range (0,12):
    #    
    #    predict_row = feature_test_df.iloc[[predict_index[i]]]
    #    actual_predict = label_test_df.iloc[[predict_index[i]]]
#
    #    print(f'Prediction #{i}: {random_forest_clf.predict(predict_row)}')
    #    print(f'Actual Storm Report #{i}: {actual_predict['storm_event_type']}')
    #    print('')


def random_forest_two_stage_main():
    df_features_month, df_labels_month = combine_monthly_df()
    df_features_year, df_labels_year = concat_df_full(df_features_month, df_labels_month)

    split_idx = int(len(df_features_year) * 0.80)
    
    feature_train_df = df_features_year.iloc[:split_idx]
    feature_test_df = df_features_year.iloc[split_idx:]

    label_train_df = df_labels_year.iloc[:split_idx]
    label_test_df = df_labels_year.iloc[split_idx:]

    print('Generating and Fitting the Stage 1 Model.')
    label_binary_train = label_train_df['storm_event_type'].apply(lambda x: 'severe' if x != 'N/A' else 'N/A')
    
    stage_1_rf = RandomForestClassifier(class_weight='balanced_subsample', n_estimators=100, n_jobs= -1, random_state=42)
    stage_1_rf.fit(feature_train_df, label_binary_train)

    print('Generating and Fitting the Stage 2 Model.')
    severe_mask = label_train_df != 'N/A'
    feature_severe_train = feature_train_df[severe_mask]
    label_severe_train = label_train_df[severe_mask]

    stage_2_rf = RandomForestClassifier(class_weight='balanced_subsample', n_estimators=100, n_jobs= -1, random_state=42)
    stage_2_rf.fit(feature_severe_train, label_severe_train)

    def predict_weather(X):

        proba = stage_1_rf.predict_proba(X)
        severe_threshold = 0.3
        stage_1_pred = ['severe' if p[1] >= severe_threshold else 'N/A' for p in proba]

        final_predictions = stage_1_pred.copy()

        severe_mask = stage_1_pred == 'severe'
        if severe_mask == any(): 
            stage_2_pred = stage_2_rf.predict(X[severe_mask])
            final_predictions[severe_mask] = stage_2_pred
        
        return final_predictions
    
    print('Running Predictions.')
    prediction = predict_weather(feature_test_df)
    print(classification_report(label_test_df, prediction))

def neural_network_main():

    df_features_month, df_labels_month = combine_monthly_df()
    df_features_year, df_labels_year = concat_df_full(df_features_month, df_labels_month)

    split_idx = int(len(df_features_year) * 0.80)
    
    feature_train_df = df_features_year.iloc[:split_idx]
    feature_test_df = df_features_year.iloc[split_idx:]

    label_train_df = df_labels_year.iloc[:split_idx]
    label_test_df = df_labels_year.iloc[split_idx:]

    scaler = StandardScaler()
    feature_train_scaled = scaler.fit_transform(feature_train_df)

    rus = RandomUnderSampler(random_state=42)
    feature_train_resampled, label_train_resampled = rus.fit_resample(feature_train_scaled, label_train_df['storm_event_type'])

    print(label_train_resampled)

    weights = class_weight.compute_sample_weight('balanced', label_train_resampled)

    neural_network_clf = MLPClassifier(solver='lbfgs', hidden_layer_sizes= (75, 50))
    neural_network_clf.fit(feature_train_resampled, label_train_resampled, sample_weight = weights)
    
    feature_test_scaled = scaler.transform(feature_test_df)
    y_pred = neural_network_clf.predict(feature_test_scaled)
    print(classification_report(label_test_df['storm_event_type'], y_pred))

tree_clf_main()
#random_forest_main()
#random_forest_two_stage_main()
#neural_network_main()
