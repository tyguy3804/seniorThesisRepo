import metpy.calc as mpcalc
from metpy.units import units
from netCDF4 import Dataset
import xarray as xr
import numpy as np
import calendar
import os
import zipfile

#data[time_index, pressure_level_index, latitude_index, longitude_index]
#time_index = 0-23 for all 24 hours of data
#pressure_level_index = 0-10 for all 11 pressure levels
#latitude_index = north to south (most likely use a : for all levles)
#longitude_index = east to west(use :)
    
def calc_cape_cin(data):
    #**CAPE/CIN**
    #Parameter 1- Total pressure
    #Parameter 2- Temperature corresponding to each pressure level 
    #Parameter 3- Dewpoint corresponding to each pressure level (Need to be calculated using specific humidity)
    #Parameter 4- Parcel Profile
        #Parameter 1- Total pressure
        #Parameter 2- Starting temperature (0Z)
        #Parameter 3- Starting dewpoint (0Z) (*Not sure if the 2m_dewpoint_temperature can work for this or it haas to be calculated like above)

    for time in range(0, 23):
        p = data.variables['pressure_level'][:] 
        pressure_levels = p.filled(np.nan) * units.hPa  
        pressure_levels_dewpoint = pressure_levels[:, np.newaxis, np.newaxis]

        q = data.variables['q'][time]
        specific_humidity = q.filled(np.nan) * units('kg/kg')
        specific_humidity = specific_humidity * 1000
        specific_humidity = specific_humidity * units('g/kg')

        t = data.variables['t'][time]
        temp = t.filled(np.nan) * units.kelvin    

        dewpoint_data = mpcalc.dewpoint_from_specific_humidity(pressure_levels_dewpoint, specific_humidity)

        prof = mpcalc.parcel_profile(pressure_levels, temp[0][0][0], dewpoint_data[0][0][0]).to('degC')
        prof_extra = prof[:, np.newaxis, np.newaxis]

        cape_grid = np.zeros((14, 35))
        cin_grid = np.zeros((14, 35))
        pressure_levels_3d = np.broadcast_to(pressure_levels_dewpoint, (11, 14, 35))

        for i in range(0, 14):
            for j in range(0, 35):

                prof = mpcalc.parcel_profile(pressure_levels_3d[:, i, j], temp[0, i, j], dewpoint_data[0, i, j]).to('degC')

                cape_val, cin_val = mpcalc.cape_cin(pressure_levels_3d[:, i, j], temp[:, i, j], dewpoint_data[:, i, j], prof)

                cape_grid[i, j] = cape_val.magnitude
                cin_grid[i, j] = cin_val.magnitude
    

    print("Calculating CAPE and CIN")


def calculate_era5():
    n_times = 306600
    n_lat = 14
    n_long = 35

    #create data arrays for all variables
    pwat_array = np.zeros((n_times, n_lat, n_long))
    dewpt_array = np.zeros((n_times, n_lat, n_long))
    lfc_array = np.zeros((n_times, n_lat, n_long))
    lcl_array = np.zeros((n_times, n_lat, n_long))
    lapse_rates_array = np.zeros((n_times, n_lat, n_long))
    showalter_idx_array = np.zeros((n_times, n_lat, n_long))
    ml_CAPE_CIN_array = np.zeros((n_times, n_lat, n_long))
    sb_CAPE_CIN_array = np.zeros((n_times, n_lat, n_long))
    mu_CPAE_CIN_array = np.zeros((n_times, n_lat, n_long))
    blk_shear_0to6km_array = np.zeros((n_times, n_lat, n_long))
    blk_shear_0to3km_array = np.zeros((n_times, n_lat, n_long))
    srh_array = np.zeros((n_times, n_lat, n_long))
    sig_tor_array = np.zeros((n_times, n_lat, n_long))
    supercell_array = np.zeros((n_times, n_lat, n_long))

    for year in range(1980, 1981):
        for month in range(1, 2):
            days_in_month = calendar.monthrange(year, month)[1]
            print(f"Month is: {month}")
            for day in range(1, days_in_month + 1):
                print(f"Day is: {day}")

                #pull pressure and surface files for year/month/day
                #press_path = f"C:/Users/lwojd/Data/era5/pressure/{year}/{month:02d}/era5_press_{year}{month:02d}{day:02d}.nc"
                press_path = f"C:/Users/lwojd/Data/era5/pressure/1980/05/era5_press_19800521.nc"

                sur_path = f"C:/Users/lwojd/Data/era5/surface/{year}/{month:02d}/era5_sur_{year}{month:02d}{day:02d}.nc"
                
                #open dataset
                #pressure = pressure levels, geopotential, spec_humidity, temp, u/v wind
                #surface = 10m u/v wind, 2m temp/dewpt, surface_pressure, total_precip
                ds_press = Dataset(press_path, 'r')

                with zipfile.ZipFile(sur_path, 'r') as z:
                    nc_file = [f for f in z.namelist() if f.endswith('.nc')][0]
                    with z.open(nc_file) as f:
                        ds_sur = Dataset('dummy', mode='r', memory=f.read())
                
                for time in range(0, 24):
                    for lat_idx in range(0, 14):
                        for(long_idx) in range(0, 35):
                            
                            p = ds_press.variables['pressure_level'][:]
                            pressure = p.filled(np.nan) * units.hPa

                            q = ds_press.variables['q'][time, :, lat_idx, long_idx]
                            spec_humidity = q.filled(np.nan) * units('kg/kg')
                            spec_humidity = spec_humidity * 1000
                            spec_humidity = spec_humidity * units('g/kg')

                            t = ds_press.variables['t'][time, :, lat_idx, long_idx]
                            temp = t.filled(np.nan) * units.kelvin
                            temp = temp.to('degC')

                            dewpt = mpcalc.dewpoint_from_specific_humidity(pressure, spec_humidity)
                            lcl_press, lcl_temp = mpcalc.lcl(pressure[0], temp[0], dewpt[0])
                            pwat = mpcalc.precipitable_water(pressure, dewpt)
                            lfc_press, lfc_temp = mpcalc.lfc(pressure, temp, dewpt)
                            lapse_rates = mpcalc.dry_lapse(pressure, temp[0]).to('degC')
                            showalter_idx = mpcalc.showalter_index(pressure, temp, dewpt)
                            ml_CAPE, ml_CIN = mpcalc.mixed_layer_cape_cin(pressure, temp, dewpt)
                            #look into using surface based data for this value
                            sb_CAPE, sb_CIN = mpcalc.surface_based_cape_cin(pressure, temp, dewpt)
                            mu_CAPE, mu_CIN = mpcalc.most_unstable_cape_cin(pressure, temp, dewpt)

                            #geopotential height depth = 3000 * meters
                            #height_agl = geopotential_height - geopotential_height[0] //surface value
                            #blk_shear_0to3km = mpcalc.bulk_shear()




    #code goes here
    print("era5 data yayyyyy")

def calculate_hrrr(data):
    #code goes here
    print("hrrr data lets fucking goooo")


calculate_era5()