# Senior Thesis Repo: [Severe Weather Prediction Model]
This repository is provided to help you build your senior thesis project. You will edit it to store your specification documents, code, and weekly checkins.

First, fork this repo (this makes a copy of it associated with your account) and then clone it to your machine (this makes a copy of your fork on your personal machine). You can then use an editor and a GitHub client to manage the repository.

## Software Requirements Specification for the Severe Weather Prediction Model

## Introduction

### Purpose

The purpose of this document is to specify the qualites of my Severe Weather Prediction Model. This model should be able to predict the possibility of severe weather in a specific location.

The key goals of this model are:
- To extract and gather past and current weather data.
- To calculate meteorological variables that impact severe weather.
- To learn how severe weather days occur based on those variables.
- To predict current weather and the possibility of severe weather.

### Scope
The Severe Weather Prediction model will be desinged to identify and forecast atmospheric conditions favorable for severe weather such as hail, high winds, thunderstorms, and tornaodes. The model will extract historical data, current data, and observed sounding data to calculate meteorological variables important for severe weather. This data will then be used to train the model so that predictions can be generated for a specific location.

This model will do the following:
- Collect ERA5, HRRR, and sounding data.
- Calculate meteorological data (CAPE, CIN, LCL, wind shear, etc) that are key predictors for severe weather.
- Use of machine learning to classifiy and predict conditions favorable for severe weather.
- Use actual SPC storm reports to validate the model's predictions.
- Predict within a statewide location, won't cover the entire US.
- Predict within 1-3 hours, no long-term forecasts.

### Definitions, Acronyms, and Abbreviations
- **ERA5**: ERA5 is the fifth generation ECMWF reanalysis for the global climate and weather for the past 8 decades. It combines model data with observations to provide a global an accurate dataset of the Earth's climate.
- **High Resolution Rapid Refresh (HRRR)**: A real-time, hourly-updating, and high-resolution numerical weather prediction model developed by the National Oceanic and Atmospheric Administration (NOAA). 
- **Sounding data**: 
- **Convective Available Potential Energy (CAPE)**: The measurment of energy (J/kg) that storms can feed on.
- **Convective Inhibition (CIN)**: The measument of needed energy to break the "cap", a layer of warm air that stops rising air from climbing into the atmosphere.
- **Lifted Condensation Level (LCL)**: The altitude at which an air parcel cools and fully condenses into a cloud.
- **Wind Shear**: Wind moving in different directions and speeds with height.
- **Storm Relative Helicity (SRH)**: The measurment of "spin" available in the atmosphere. In order for thunderstorms to have the possibilty of creating a tornado, they must begin to spin or rotate. 
- **Mixing Ratio**: The measurment of mositure compared to the measurment of dry air in an air parcel.

## Overview
The Severe Weather Prediction Model is a machine-learning application designed to predict the possibility of severe weather within a certain location.

### System Features:
1. **Data Extraction**: Extracts historical and current climate data.
2. **Meteorological Calculations**: Uses all extracted climate data to perform meterological calculations that relate to severe weather.
3. **Machine Learning**: Uses calculated meteorological data to train a machine learning model about severe weather.
4. **Prediction**: Predicts the possibility of severe weather within a specified location.

To account for hardware limitations, this model is limited to statewide coverage. In this case the state of Okalahoma was chosen because historically and currenlty it experiences majority of the United State's severe weather.

The following sections detail the specific use cases that the model will support, describing how users and the model itself interact with the model.

## Use Cases

### Use Case 1.1: Displays severe weather prediction
- **Actors**: Model and User
- **Overview**: After data processing, the model will predict where severe weather will occur.

**Typical Course of Events**:
1. Model proccesses current data of the specificed location.
2. Model combines it's understanding of how severe weather occurs and current data to make a logical guess.
3. Model displays it's prediction on a map for the user.

**Alternative Courses**:
- **Step 1**: Incomplete or inconsistent data is given.
- 1. Model gives a warning notifying the user that the data may not be sufficient enough.
- 2. Attempts to use the most recent available data or aborts the program.
- **Step 3**: Confidence rating doesn't meet a certain threshold.
- 1. Notifies the user what the rating is and where it should be.

### Use Case 1.2: Displays probability of the incoming storms and delivers a confidence rating.
- **Actors**: Model
- **Overview**: Alongside the prediction, the model will displaty the probablity of storms and give a confidence rating on it's prediction.

**Typical Course of Events**:
1. Model displays it's prediction.
2. Model displays the probability of storms. Includes severity.(ex: 70% chance of rain or 70% chance of strong thunderstorms)
3. Model displays a confidence rating on it's prediction.

**Alterantive Courses**:
- **Step 2**: Impossible probability (ex: 110% chance of rain)
- 1. Model gives an error stating that the prediction is incorrect or skewed
- 2. Model displays it's confidence rating and aborts.

### Use Case 1.3: Update Prediction with new data
- **Actors**: Model
**Typical Course of Events**:
1. Model extracts the most recent, updated data
2. Model makes meteorlogical calculations and updates the dataset.
3. Model makes a new prediction based on new data.

**Alternative Courses**:

### Use Case 1.4: Download Prediction

### Use Case 2.1: Allows user to test model on custom dates and times.
- **Actors**: Model and User
- **Overview**: User can enter in a custom data and time, instead of using current data, to test the model.

**Typical Course of Events**:
1. Prompts user if they would like current predictions or custom predictions.
2. After entering a custom date and time, model will extract that specified data.
3. Make it's prediction and display all intended features.

**Alternative Courses**:
-**Step 1**: Invalid date
- 1. Model gives an error based on where the date or time becomes invalid (ex: "Day in month doesn't exist (31st of September) or "Please enter a year within 1980 and 2025").
- 2. Model repromtps the user.
- **Step 2**: 
