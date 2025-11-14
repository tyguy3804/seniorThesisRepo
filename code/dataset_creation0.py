import metpy_calculations
import calendar
import zipfile
from netCDF4 import Dataset
import csv
import pandas as pd
from datetime import datetime, timedelta
import math
from multiprocessing import Pool, current_process
import os

##** Don't forget to include storm report data as well
def find_closest_lat_lon(report_lat, report_lon, ds_lat, ds_lon):
    temp_diff_lat = 0.0
    temp_diff_lon = 0.0
    lat_idx = 0
    lon_idx = 0
    return_lat = 0
    return_lon = 0

    for lat in ds_lat:
        lat_diff = abs(report_lat - lat)

        if lat_idx == 0:
            temp_diff_lat = lat_diff
        else:
            if lat_diff < temp_diff_lat:
                temp_diff_lat = lat_diff
                return_lat = lat_idx 

        lat_idx += 1

    for lon in ds_lon:
        lon_diff = abs(report_lon - lon)

        if lon_idx == 0:
            temp_diff_lon = lon_diff
        else:
            if lon_diff < temp_diff_lon:
                temp_diff_lon = lon_diff
                return_lon = lon_idx

        lon_idx += 1

    return return_lat, return_lon

def find_storm_reports(date, storm_reports):
    all_reports = []

    for row in storm_reports.iloc():
        if date == row['full_date']:
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

def process_year(year):
    try:
        if os.path.exists(f"C:/Users/lwojd/Data/metpyCalc/{year}/data{year}.parquet"):
            print(f"Year: {year} already processed, skipping...")
            return year, "skipped"
        else:
            os.makedirs(f"C:/Users/lwojd/Data/metpyCalc/{year}", exist_ok= True)

        process_name = current_process().name
        process_id = os.getpid()
        print(f"[PID {process_id}] {process_name} started processing year {year}")
    
        data_rows = []

        storm_reports_path = f"C:/Users/lwojd/Data/stormReports/StormEvents_d{year}_oklahoma.csv"
        storm_reports = pd.read_csv(storm_reports_path)

        start_date = datetime(year, 1, 1)
        end_date = datetime(year, 12, 31)
        current_date = start_date
    
        while current_date <= end_date:
        
            if current_date.year < 2016:
                press_path = f"C:/Users/lwojd/Data/era5/pressure/{current_date.year}/{current_date.month:02d}/era5_press_{current_date.year}{current_date.month:02d}{current_date.day:02d}.nc"
                sur_path = f"C:/Users/lwojd/Data/era5/surface/{current_date.year}/{current_date.month:02d}/era5_sur_{current_date.year}{current_date.month:02d}{current_date.day:02d}.nc"

                ds_press = Dataset(press_path, 'r')

                try:
                    with zipfile.ZipFile(sur_path, 'r') as z:
                        nc_file = [f for f in z.namelist() if f.endswith('.nc')][0]
                        with z.open(nc_file) as f:
                            ds_sur = Dataset('dummy', mode='r', memory=f.read())
                except Exception as e:
                    print(f"An unexpected error occurred: {e}")
            else:
                press_path = f"C:/Users/lwojd/Data/hrrr/{current_date.year}/{current_date.month:02d}/hrrr_press_{current_date.year}{current_date.month:02d}{current_date.day:02d}.nc"
                sur_path = f"C:/Users/lwojd/Data/hrrr/{current_date.year}/{current_date.month:02d}/temp/temp_hrrr_sur_{current_date.year}{current_date.month:02d}{current_date.day:02d}.nc"

                ds_press = Dataset(press_path, 'r')
                ds_sur = Dataset(sur_path, 'r')
    
            all_reports = find_storm_reports(current_date.strftime('%Y-%m-%d'), storm_reports)
            reports_idx = 0

            for time in range(0, 24):  
                for lat_idx in range(0, 14):
                    for long_idx in range(0, 35):
                        if current_date.year < 2016:
                            # Calculate using era5 data
                            if len(all_reports) != 0 and reports_idx < len(all_reports):
                                if time == all_reports[reports_idx]['BEGIN_HOUR']:
                                    report_lat, report_lon = find_closest_lat_lon(
                                        all_reports[reports_idx]['BEGIN_LAT'], 
                                        all_reports[reports_idx]['BEGIN_LON'], 
                                        ds_press.variables['latitude'][:], 
                                        ds_press.variables['longitude'][:]
                                    )

                                if lat_idx == report_lat and long_idx == report_lon:
                                    report_event = all_reports[reports_idx]['EVENT_TYPE']
                                    report_tor_f_scale = all_reports[reports_idx]['TOR_F_SCALE']
                                    lat = all_reports[reports_idx]['BEGIN_LAT']
                                    lon = all_reports[reports_idx]['BEGIN_LON']
                                    reports_idx += 1
                                else:
                                    report_event = "NA"
                                    report_tor_f_scale = "NA"
                                    lat = "NA"
                                    lon = "NA"
                            else:
                                report_event = "N/A"
                                report_tor_f_scale = "N/A"
                                lat = "N/A"
                                lon = "N/A"

                            sb_CAPE, sb_CIN = metpy_calculations.era5_calculate_sb_CAPE_CIN(ds_press, ds_sur, time, lat_idx, long_idx)
                            lcl_press, lcl_temp = metpy_calculations.era5_calculate_lcl(ds_press, ds_sur, time, lat_idx, long_idx)
                            total_helicity = metpy_calculations.era5_calculate_srh(ds_press, ds_sur, time, lat_idx, long_idx)
                            bulk_shear_0to6km = metpy_calculations.era5_calculate_bulk_shear(ds_press, ds_sur, time, lat_idx, long_idx, 6000)
                            bulk_shear_0to3km = metpy_calculations.era5_calculate_bulk_shear(ds_press, ds_sur, time, lat_idx, long_idx, 3000)
                            mu_CAPE, mu_CIN = metpy_calculations.era5_calculate_mu_CAPE_CIN(ds_press, ds_sur, time, lat_idx, long_idx)
                            pwat = metpy_calculations.era5_calculate_pwat(ds_press, ds_sur, time, lat_idx, long_idx)
                            lfc_press, lfc_temp = metpy_calculations.era5_calculate_lfc(ds_press, ds_sur, time, lat_idx, long_idx)
                            lapse_rates = metpy_calculations.era5_calculate_lapse_rates(ds_press, ds_sur, time, lat_idx, long_idx)
                            showalter_idx = metpy_calculations.era5_calculate_showalter_idx(ds_press, ds_sur, time, lat_idx, long_idx)
                            ml_CAPE, ml_CIN = metpy_calculations.era5_calculate_ml_CAPE_CIN(ds_press, ds_sur, time, lat_idx, long_idx)
                            sig_tor = metpy_calculations.era5_calculate_sig_tor(ds_press, ds_sur, time, lat_idx, long_idx, sb_CAPE, lcl_press, lcl_temp, total_helicity, bulk_shear_0to6km)
                            supercell_comp = metpy_calculations.era5_calculate_supercell_comp(ds_press, ds_sur, time, lat_idx, long_idx, mu_CAPE)

                            row = {
                                'day_sin': convert_cyclical_encoded(current_date.timetuple().tm_yday, 365, "sin"),    
                                'day_cos': convert_cyclical_encoded(current_date.timetuple().tm_yday, 365, "cos"),
                                'month_sin': convert_cyclical_encoded(current_date.month, 12, "sin"),
                                'month_cos': convert_cyclical_encoded(current_date.month, 12, "cos"),
                                'hour_sin': convert_cyclical_encoded(time, 24, "sin"),
                                'hour_cos': convert_cyclical_encoded(time, 24, "cos"),
                                'lat_idx': lat_idx,
                                'long_idx': long_idx,
                                'pwat': pwat,
                                'lcl_press': lcl_press,
                                'lcl_temp': lcl_temp,
                                'lfc_press': lfc_press,
                                'lfc_temp': lfc_temp,
                                'lapse_rates': lapse_rates,
                                'showalter_idx': showalter_idx,
                                'ml_CAPE': ml_CAPE,
                                'ml_CIN':  ml_CIN,
                                'sb_CAPE': sb_CAPE,
                                'sb_CIN': sb_CIN,
                                'mu_CAPE': mu_CAPE,
                                'mu_CIN': mu_CIN,
                                'bulk_shear_0to3km': bulk_shear_0to3km,
                                'bulk_shear_0to6km': bulk_shear_0to6km,
                                'srh': total_helicity,
                                'sig_tor': sig_tor,
                                'supercell_comp': supercell_comp,
                                'storm_event_type': report_event,
                                'tornado_mag': report_tor_f_scale,
                                'storm_lat': lat,
                                'storm_long': lon
                            }

                            data_rows.append(row)
                        
                        else:
                            # Calculate using hrrr data
                            if len(all_reports) != 0 and reports_idx < len(all_reports):
                                if time == all_reports[reports_idx]['BEGIN_HOUR']:
                                    report_lat, report_lon = find_closest_lat_lon(
                                        all_reports[reports_idx]['BEGIN_LAT'], 
                                        all_reports[reports_idx]['BEGIN_LON'], 
                                        ds_press.variables['latitude'][:], 
                                        ds_press.variables['longitude'][:]
                                    )

                                if lat_idx == report_lat and long_idx == report_lon:
                                    report_event = all_reports[reports_idx]['EVENT_TYPE']
                                    report_tor_f_scale = all_reports[reports_idx]['TOR_F_SCALE']
                                    lat = all_reports[reports_idx]['BEGIN_LAT']
                                    lon = all_reports[reports_idx]['BEGIN_LON']
                                    reports_idx += 1
                                else:
                                    report_event = "NA"
                                    report_tor_f_scale = "NA"
                                    lat = "NA"
                                    lon = "NA"
                            else:
                                report_event = "N/A"
                                report_tor_f_scale = "N/A"
                                lat = "N/A"
                                lon = "N/A"

                            sb_CAPE, sb_CIN = metpy_calculations.hrrr_calculate_sb_CAPE_CIN(ds_press, ds_sur, time, lat_idx, long_idx)
                            lcl_press, lcl_temp = metpy_calculations.hrrr_calculate_lcl(ds_press, ds_sur, time, lat_idx, long_idx)
                            total_helicity = metpy_calculations.hrrr_calculate_srh(ds_press, ds_sur, time, lat_idx, long_idx)
                            bulk_shear_0to3km = metpy_calculations.hrrr_calculate_bulk_shear(ds_press, ds_sur, time, lat_idx, long_idx, 3000)
                            bulk_shear_0to6km = metpy_calculations.hrrr_calculate_bulk_shear(ds_press, ds_sur, time, lat_idx, long_idx, 6000)
                            mu_CAPE, mu_CIN = metpy_calculations.hrrr_calculate_mu_CAPE_CIN(ds_press, ds_sur, time, lat_idx, long_idx)
                            pwat = metpy_calculations.hrrr_calculate_pwat(ds_press, ds_sur, time, lat_idx, long_idx)
                            lfc_press, lfc_temp = metpy_calculations.hrrr_calculate_lfc(ds_press, ds_sur, time, lat_idx, long_idx)
                            lapse_rates = metpy_calculations.hrrr_calculate_lapse_rates(ds_press, ds_sur, time, lat_idx, long_idx)
                            showalter_idx = metpy_calculations.hrrr_calculate_showalter_idx(ds_press, ds_sur, time, lat_idx, long_idx)
                            ml_CAPE, ml_CIN = metpy_calculations.hrrr_calculate_ml_CAPE_CIN(ds_press, ds_sur, time, lat_idx, long_idx)
                            sig_tor = metpy_calculations.hrrr_calculate_sig_tor(ds_press, ds_sur, time, lat_idx, long_idx, sb_CAPE, lcl_press, lcl_temp, total_helicity, bulk_shear_0to6km)
                            supercell_comp = metpy_calculations.hrrr_calculate_supercell_comp(ds_press, ds_sur, time, lat_idx, long_idx, mu_CAPE)

                            row = {
                                'day_sin': convert_cyclical_encoded(current_date.timetuple().tm_yday, 365, "sin"),    
                                'day_cos': convert_cyclical_encoded(current_date.timetuple().tm_yday, 365, "cos"),
                                'month_sin': convert_cyclical_encoded(current_date.month, 12, "sin"),
                                'month_cos': convert_cyclical_encoded(current_date.month, 12, "cos"),
                                'hour_sin': convert_cyclical_encoded(time, 24, "sin"),
                                'hour_cos': convert_cyclical_encoded(time, 24, "cos"),
                                'lat_idx': lat_idx,
                                'long_idx': long_idx,
                                'pwat': pwat,
                                'lcl_press': lcl_press,
                                'lcl_temp': lcl_temp,
                                'lfc_press': lfc_press,
                                'lfc_temp': lfc_temp,
                                'lapse_rates': lapse_rates,
                                'showalter_idx': showalter_idx,
                                'ml_CAPE': ml_CAPE,
                                'ml_CIN':  ml_CIN,
                                'sb_CAPE': sb_CAPE,
                                'sb_CIN': sb_CIN,
                                'mu_CAPE': mu_CAPE,
                                'mu_CIN': mu_CIN,
                                'bulk_shear_0to3km': bulk_shear_0to3km,
                                'bulk_shear_0to6km': bulk_shear_0to6km,
                                'srh': total_helicity,
                                'sig_tor': sig_tor,
                                'supercell_comp': supercell_comp,
                                'storm_event_type': report_event,
                                'tornado_mag': report_tor_f_scale,
                                'storm_lat': lat,
                                'storm_long': lon
                            }

                            data_rows.append(row)


            current_date += timedelta(days=1)

        print(f"[PID {process_id}] {process_name} finished year {year}")
        df = pd.DataFrame(data_rows)
        df['year'] = year
        df.to_parquet(f"C:/Users/lwojd/Data/metpyCalc/{year}/data{year}.parquet",
                    compression='snappy',
                    index=False)
        
    except Exception as e:
        print(f"[ERROR] Year {year} failed: {e}")
        with open("error_log.txt", "a") as f:
            f.write(f"{year}: {e}\n")
        return year, "failed"


if __name__ == '__main__':
    years = list(range(1980, 2022))
    
    print(f"Starting processing of {len(years)} years with 14 processes...")
    
    try:
        with Pool(processes=14) as pool:
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