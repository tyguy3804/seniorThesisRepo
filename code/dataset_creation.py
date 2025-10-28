import metpy_calculations
import calendar
import zipfile
from netCDF4 import Dataset
import pandas as pd
from datetime import datetime, timedelta

##** Don't forget to include storm report data as well

def process_year(year):
    data_rows = []

    start_date = datetime(year, 1, 1)
    end_date = datetime(year, 12, 31)
    current_date = start_date

    while current_date <= end_date:
        for time in range(0, 24):
            for lat_idx in range(0, 14):
                for long_idx in range(0, 35):

                    if current_date.year < 2016:
                        #calculate using era5 data
                        press_path = f"C:/Users/lwojd/Data/era5/pressure/{current_date.year}/{current_date.month:02d}/era5_press_{current_date.year}{current_date.month:02d}{current_date.day:02d}.nc"
                        sur_path = f"C:/Users/lwojd/Data/era5/surface/{current_date.year}/{current_date.month:02d}/era5_sur_{current_date.year}{current_date.month:02d}{current_date.day:02d}.nc"

                        ds_press = Dataset(press_path, 'r')

                        with zipfile.ZipFile(sur_path, 'r') as z:
                            nc_file = [f for f in z.namelist() if f.endswith('.nc')][0]
                            with z.open(nc_file) as f:
                                ds_sur = Dataset('dummy', mode='r', memory=f.read())

                        sb_CAPE, sb_CIN = metpy_calculations.era5_calculate_sb_CAPE_CIN(ds_press, ds_sur, time, lat_idx, long_idx)
                        lcl_press, lcl_temp = metpy_calculations.era5_calculate_lcl(ds_press, ds_sur, time, lat_idx, long_idx)
                        total_helicity = metpy_calculations.era5_calculate_srh(ds_press, ds_sur, time, lat_idx, long_idx)
                        bulk_shear_0to6km = metpy_calculations.era5_calculate_bulk_shear(ds_press, ds_sur, time, lat_idx, long_idx, 6000)
                        mu_CAPE, mu_CIN = metpy_calculations.era5_calculate_mu_CAPE_CIN(ds_press, ds_sur, time, lat_idx, long_idx)

                        row = {
                            'date': current_date.strftime('%Y-%m-%d'),
                            'hour': time,
                            'lat_idx': lat_idx,
                            'long_idx': long_idx,
                            'pwat': metpy_calculations.era5_calculate_pwat(ds_press, ds_sur, time, lat_idx, long_idx),
                            'lcl': [lcl_press, lcl_temp],
                            'lfc': metpy_calculations.era5_calculate_lfc(ds_press, ds_sur, time, lat_idx, long_idx),
                            'lapse_rates': metpy_calculations.era5_calculate_lapse_rates(ds_press, ds_sur, time, lat_idx, long_idx),
                            'showalter_idx': metpy_calculations.era5_calculate_showalter_idx(ds_press, ds_sur, time, lat_idx, long_idx),
                            'ml_CAPE_CIN': metpy_calculations.era5_calculate_ml_CAPE_CIN(ds_press, ds_sur, time, lat_idx, long_idx),
                            'sb_CAPE_CIN': [sb_CAPE, sb_CIN],
                            'mu_CAPE_CIN': [mu_CAPE, mu_CIN],
                            'bulk_shear_0to3km': metpy_calculations.era5_calculate_bulk_shear(ds_press, ds_sur, time, lat_idx, long_idx, 3000),
                            'bulk_shear_0to6km': bulk_shear_0to6km,
                            'srh': total_helicity,
                            'sig_tor': metpy_calculations.era5_calculate_sig_tor(ds_press, ds_sur, time, lat_idx, long_idx, sb_CAPE, lcl_press, lcl_temp, total_helicity, bulk_shear_0to6km),
                            'supercell_comp': metpy_calculations.era5_calculate_supercell_comp(ds_press, ds_sur, time, lat_idx, long_idx, mu_CAPE)
                        }

                        data_rows.append(row)
                        current_date += timedelta(days= 1)
                    else:
                        #calculate using hrrr data
                        sb_CAPE, sb_CIN = metpy_calculations.hrrr_calculate_sb_CAPE_CIN(ds_press, ds_sur, time, lat_idx, long_idx)
                        lcl_press, lcl_temp = metpy_calculations.hrrr_calculate_lcl(ds_press, ds_sur, time, lat_idx, long_idx)
                        total_helicity = metpy_calculations.hrrr_calculate_srh(ds_press, ds_sur, time, lat_idx, long_idx)
                        bulk_shear_0to6km = metpy_calculations.hrrr_calculate_bulk_shear(ds_press, ds_sur, time, lat_idx, long_idx, 6000)
                        mu_CAPE, mu_CIN = metpy_calculations.hrrr_calculate_mu_CAPE_CIN(ds_press, ds_sur, time, lat_idx, long_idx)

                        row = {
                            'date': current_date.strftime('%Y-%m-%d'),
                            'hour': time,
                            'lat_idx': lat_idx,
                            'long_idx': long_idx,
                            'pwat': metpy_calculations.hrrr_calculate_pwat(ds_press, ds_sur, time, lat_idx, long_idx),
                            'lcl': [lcl_press, lcl_temp],
                            'lfc': metpy_calculations.hrrr_calculate_lfc(ds_press, ds_sur, time, lat_idx, long_idx),
                            'lapse_rates': metpy_calculations.hrrr_calculate_lapse_rates(ds_press, ds_sur, time, lat_idx, long_idx),
                            'showalter_idx': metpy_calculations.hrrr_calculate_showalter_idx(ds_press, ds_sur, time, lat_idx, long_idx),
                            'ml_CAPE_CIN': metpy_calculations.hrrr_calculate_ml_CAPE_CIN(ds_press, ds_sur, time, lat_idx, long_idx),
                            'sb_CAPE_CIN': [sb_CAPE, sb_CIN],
                            'mu_CAPE_CIN': [mu_CAPE, mu_CIN],
                            'bulk_shear_0to3km': metpy_calculations.hrrr_calculate_bulk_shear(ds_press, ds_sur, time, lat_idx, long_idx, 3000),
                            'bulk_shear_0to6km': bulk_shear_0to6km,
                            'srh': total_helicity,
                            'sig_tor': metpy_calculations.hrrr_calculate_sig_tor(ds_press, ds_sur, time, lat_idx, long_idx, sb_CAPE, lcl_press, lcl_temp, total_helicity, bulk_shear_0to6km),
                            'supercell_comp': metpy_calculations.hrrr_calculate_supercell_comp(ds_press, ds_sur, time, lat_idx, long_idx, mu_CAPE)
                        }

                        data_rows.append(row)
                        current_date += timedelta(days= 1)

    df = pd.DataFrame(data_rows)
    df['year'] = year
    df.to_parquet(f"data/metpy_calc/{year}/data.parquet",
                  compression= 'snappy',
                  index= False)

