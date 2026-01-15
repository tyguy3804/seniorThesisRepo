import metpy_calculations
import calendar
import zipfile
from netCDF4 import Dataset
import csv
import pandas as pd
from datetime import datetime, timedelta
import calendar
import math
from multiprocessing import Pool, current_process
import os
import traceback

##** Don't forget to include storm report data as well

def find_storm_reports(month, storm_reports):
    all_reports = []

    for row in storm_reports.iloc():
        if month == row['BEGIN_MONTH']:
            all_reports.append(row)

    return all_reports

def convert_cyclical_encoded(original_num, num_values, cos_or_sine):
    retVal = original_num / num_values
    retVal = (math.pi * 2) * retVal
    
    if cos_or_sine == "cos":
        retVal = math.cos(retVal)
    else:
        retVal = math.sin(retVal)

    return retVal

def process_month(monthIdx, year, storm_reports_for_month):

    if os.path.exists(f"C:/Users/lwojd/Data/metpyCalc/featureData/{year}/{monthIdx:02d}/features{monthIdx:02d}_{year}.parquet") and os.path.exists(f"C:/Users/lwojd/Data/metpyCalc/labelData/{year}/{monthIdx:02d}/labels{monthIdx:02d}_{year}.parquet"):
            print(f"Month: {monthIdx} Year: {year} already processed, skipping...")
            return year, "skipped"
    else:
        os.makedirs(f"C:/Users/lwojd/Data/metpyCalc/featureData/{year}/{monthIdx:02d}", exist_ok= True)
        os.makedirs(f"C:/Users/lwojd/Data/metpyCalc/labelData/{year}/{monthIdx:02d}", exist_ok= True)

    process_name = current_process().name
    process_id = os.getpid()
    print(f"[PID {process_id}] {process_name} started processing month: {monthIdx:02d} for year: {year}")

    feature_data_rows = []
    label_data_rows = []

    days_in_month = calendar.monthrange(year, monthIdx)[1]
    start_date = datetime(year, monthIdx, 1)
    end_date = datetime(year, monthIdx, days_in_month)
    current_date = start_date

    while current_date <= end_date:
        
        press_path = f"C:/Users/lwojd/Data/era5/pressure/{current_date.year}/{current_date.month:02d}/era5_press_{current_date.year}{current_date.month:02d}{current_date.day:02d}.nc"
        sur_path = f"C:/Users/lwojd/Data/era5/surface/{current_date.year}/{current_date.month:02d}/era5_sur_{current_date.year}{current_date.month:02d}{current_date.day:02d}.nc"

        ds_press = Dataset(press_path, 'r')
        ds_sur = Dataset(sur_path, 'r')

        storm_reports_idx = 0
        found_report = False

        for time in range(0, 24):
            for lat_idx in range(0,14):
                for lon_idx in range(0,35):

                    date = current_date.strftime("%Y-%m-%d")
                    
                    if storm_reports_for_month:   
                        if date == storm_reports_for_month[storm_reports_idx]['DATE']:
                            if time == storm_reports_for_month[storm_reports_idx]['BEGIN_HOUR']:
                                if lat_idx == storm_reports_for_month[storm_reports_idx]['LAT_IDX']:
                                    if lon_idx == storm_reports_for_month[storm_reports_idx]['LON_IDX']:
                                        report_event = storm_reports_for_month[storm_reports_idx]['EVENT_TYPE']

                                        if math.isnan(storm_reports_for_month[storm_reports_idx]['TOR_F_SCALE']):
                                            report_tor_f_scale = "N/A"
                                        else:
                                            report_tor_f_scale = storm_reports_for_month[storm_reports_idx]['TOR_F_SCALE']

                                        lat = lat_idx
                                        lon = lon_idx

                                        found_report = True
                                        storm_reports_idx += 1

                    if found_report == False:
                        report_event = 'N/A'
                        report_tor_f_scale = 'N/A'
                        lat = 'N/A'
                        lon = 'N/A'
                    


                    sb_CAPE, sb_CIN = metpy_calculations.era5_calculate_sb_CAPE_CIN(ds_press, ds_sur, time, lat_idx, lon_idx)
                    lcl_press, lcl_temp = metpy_calculations.era5_calculate_lcl(ds_press, ds_sur, time, lat_idx, lon_idx)
                    total_helicity = metpy_calculations.era5_calculate_srh(ds_press, ds_sur, time, lat_idx, lon_idx)
                    bulk_shear_0to6km = metpy_calculations.era5_calculate_bulk_shear(ds_press, ds_sur, time, lat_idx, lon_idx, 6000)
                    bulk_shear_0to3km = metpy_calculations.era5_calculate_bulk_shear(ds_press, ds_sur, time, lat_idx, lon_idx, 3000)
                    mu_CAPE, mu_CIN = metpy_calculations.era5_calculate_mu_CAPE_CIN(ds_press, ds_sur, time, lat_idx, lon_idx)
                    pwat = metpy_calculations.era5_calculate_pwat(ds_press, ds_sur, time, lat_idx, lon_idx)
                    lfc_press, lfc_temp = metpy_calculations.era5_calculate_lfc(ds_press, ds_sur, time, lat_idx, lon_idx)
                    lapse_rates = metpy_calculations.era5_calculate_lapse_rates(ds_press, ds_sur, time, lat_idx, lon_idx)
                    showalter_idx = metpy_calculations.era5_calculate_showalter_idx(ds_press, ds_sur, time, lat_idx, lon_idx)
                    ml_CAPE, ml_CIN = metpy_calculations.era5_calculate_ml_CAPE_CIN(ds_press, ds_sur, time, lat_idx, lon_idx)
                    sig_tor = metpy_calculations.era5_calculate_sig_tor(ds_press, ds_sur, time, lat_idx, lon_idx, sb_CAPE, lcl_press, lcl_temp, total_helicity, bulk_shear_0to6km)
                    #supercell_comp = metpy_calculations.era5_calculate_supercell_comp(ds_press, ds_sur, time, lat_idx, lon_idx, mu_CAPE)

                
                    feature_row = {
                        'day_sin': convert_cyclical_encoded(current_date.timetuple().tm_yday, 365, "sin"),    
                        'day_cos': convert_cyclical_encoded(current_date.timetuple().tm_yday, 365, "cos"),
                        'month_sin': convert_cyclical_encoded(current_date.month, 12, "sin"),
                        'month_cos': convert_cyclical_encoded(current_date.month, 12, "cos"),
                        'hour_sin': convert_cyclical_encoded(time, 24, "sin"),
                        'hour_cos': convert_cyclical_encoded(time, 24, "cos"),
                        'lat_idx': lat_idx,
                        'long_idx': lon_idx,
                        'pwat': pwat.magnitude,
                        'lcl_press': lcl_press.magnitude,
                        'lcl_temp': lcl_temp.magnitude,
                        'lfc_press': lfc_press.magnitude,
                        'lfc_temp': lfc_temp.magnitude,
                        'lapse_rates': lapse_rates.magnitude,
                        'showalter_idx': showalter_idx.magnitude,
                        'ml_CAPE': ml_CAPE.magnitude,
                        'ml_CIN':  ml_CIN.magnitude,
                        'sb_CAPE': sb_CAPE.magnitude,
                        'sb_CIN': sb_CIN.magnitude,
                        'mu_CAPE': mu_CAPE.magnitude,
                        'mu_CIN': mu_CIN.magnitude,
                        'bulk_shear_0to3km': bulk_shear_0to3km.magnitude,
                        'bulk_shear_0to6km': bulk_shear_0to6km.magnitude,
                        'srh': total_helicity.magnitude,
                        'sig_tor': sig_tor.magnitude,
                        #'supercell_comp': supercell_comp,
                    }

                    label_row = {
                        
                        'storm_event_type': report_event,
                        'tornado_mag': report_tor_f_scale,
                        'storm_lat': lat,
                        'storm_long': lon
                    }
                    
                    feature_data_rows.append(feature_row)
                    label_data_rows.append(label_row)
                    found_report = False
        
        current_date += timedelta(days=1)
    
    print(f"[PID {process_id}] {process_name} finished month: {monthIdx} for year: {year}")
    df_features = pd.DataFrame(feature_data_rows)
    df_labels = pd.DataFrame(label_data_rows)
    df_features['year'] = year
    df_features.to_parquet(f"C:/Users/lwojd/Data/metpyCalc/featureData/{year}/{monthIdx:02d}/features{monthIdx:02d}_{year}.parquet",
                compression='snappy',
                index=False)
    df_labels['year'] = year
    df_labels.to_parquet(f"C:/Users/lwojd/Data/metpyCalc/labelData/{year}/{monthIdx:02d}/labels{monthIdx:02d}_{year}.parquet",
                           compression= 'snappy',
                           index=False)
    

def process_year(year):
    
        storm_reports_path = f"C:/Users/lwojd/Data/stormReports/StormEvents_d{year}_oklahoma.csv"
        storm_reports = pd.read_csv(storm_reports_path)

        for month in range(1, 13):
            try:
                storm_reports_for_month = find_storm_reports(month, storm_reports)
                process_month(month, year, storm_reports_for_month)
            except Exception as e:
                print(f"Error occured for month: {month} for year: {year}")
                print("Full traceback:")
                traceback.print_exc()
        


def generateprocesses():
        
    if __name__ == '__main__':
        years = list(range(2007, 2012))
        print(f"Starting processing of {len(years)} years with 5 processes...")
        try:
            with Pool(processes=5) as pool:
                results = pool.map(process_year, years)
            # Summary
            success = sum(1 for _, status in results if status == "success")
            skipped = sum(1 for _, status in results if status == "skipped")
            failed = sum(1 for _, status in results if status == "failed")
            print(f"\n=== SUMMARY ===")
            print(f"Success: {success}")
            print(f"Skipped: {skipped}")
            print(f"Failed: {failed}")
    
        except KeyboardInterrupt:
            print("\nProcess interrupted by user")



generateprocesses()

#storm_reports_path = f"C:/Users/lwojd/Data/stormReports/StormEvents_d2007_oklahoma.csv"
#storm_reports = pd.read_csv(storm_reports_path)
#
#def find_report(storm_reports_for_month, storm_reports_idx, date, time, lat_idx, lon_idx):
#    if date == storm_reports_for_month[storm_reports_idx]['DATE']:
#        if time == storm_reports_for_month[storm_reports_idx]['BEGIN_HOUR']:
#            if lat_idx == storm_reports_for_month[storm_reports_idx]['LAT_IDX']:
#                if lon_idx == storm_reports_for_month[storm_reports_idx]['LON_IDX']:
#                    report_event = storm_reports_for_month[storm_reports_idx]['EVENT_TYPE']
#
#                    if math.isnan(storm_reports_for_month[storm_reports_idx]['TOR_F_SCALE']):
#                        report_tor_f_scale = "N/A"
#                    else:
#                        report_tor_f_scale = storm_reports_for_month[storm_reports_idx]['TOR_F_SCALE']
#                    lat = lat_idx
#                    lon = lon_idx
#
#                    #found_report = True
#                    print(report_tor_f_scale)
#
#list = find_storm_reports(2, storm_reports)
##process_month(2, 2007, list)
#
#find_report(list, 0, "2007-02-23", 19, 13, 11)