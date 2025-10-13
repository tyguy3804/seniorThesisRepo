from metpy.calc import cape_cin, dewpoint_from_specific_humidity, parcel_profile, mixing_ratio, moist_lapse, lcl, storm_relative_helicity, wind_components, dewpoint_from_relative_humidity
from metpy.units import units
from netCDF4 import Dataset
import xarray as xr
import numpy as np
import calendar

#*****ERA5 Calculations*****
#* U-component references East/West direction*
#* V-component references North/South direction*

#Moisture values derived from ERA5- Specific Humidity (Pressure levels), 2m dewpoint temperature (Surface), Total precipitation (Surface)   
#Instability values derived from ERA5- None
#Wind/Shear values derived from ERA5- U-component of wind (Pressure levels), V-component of wind (Pressure levels), 10m U-component of wind (Surface), 10m V-component of wind (Surface

#*****HRRR Calculations*****

#Moisture values derived from HRRR- 2m dewpoint temperature (Surface), 2m temperature (Surface), Specific Humidity (Surface), Temperature and Dewpoint (Pressure)
#Instability and Wind/Shear are the same as above

#data[time_index, pressure_level_index, latitude_index, longitude_index]
#time_index = 0-23 for all 24 hours of data
#pressure_level_index = 0-10 for all 11 pressure levels
#latitude_index = north to south (most likely use a : for all levles)
#longitude_index = east to west(use :)

#calculation functions
def calc_total_precip(data):
    
    print("Calculating Total Precipitation")


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

        dewpoint_data = dewpoint_from_specific_humidity(pressure_levels_dewpoint, specific_humidity)

        prof = parcel_profile(pressure_levels, temp[0][0][0], dewpoint_data[0][0][0]).to('degC')
        prof_extra = prof[:, np.newaxis, np.newaxis]

        cape_grid = np.zeros((14, 35))
        cin_grid = np.zeros((14, 35))
        pressure_levels_3d = np.broadcast_to(pressure_levels_dewpoint, (11, 14, 35))

        for i in range(0, 14):
            for j in range(0, 35):

                prof = parcel_profile(pressure_levels_3d[:, i, j], temp[0, i, j], dewpoint_data[0, i, j]).to('degC')

                cape_val, cin_val = cape_cin(pressure_levels_3d[:, i, j], temp[:, i, j], dewpoint_data[:, i, j], prof)

                cape_grid[i, j] = cape_val.magnitude
                cin_grid[i, j] = cin_val.magnitude
    

    print("Calculating CAPE and CIN")


def calc_LCL(data):
    #**LCL**
    #Parameter 1- Pressure (First piece of level data)
    #Parameter 2- Starting temperature (0Z)
    #Parameter 3- Starting dewpoint (0Z)

    print("Calculating LCL")

def calc_lapse_rates(data):
    #**Lapse Rates** 
    #Parameter 1- Pressure profile
    #Parameter 2- Starting Temperature

    print("Calculating lapse rates")

def calc_0to6km_shear(data):
    #**0-6km bulk shear**
    #Parameter 1- Pressure profile
    #Parameter 2- U-component of wind
    #Parameter 3- V-component of wind
    #Parameter 4- Depth in meters (6000 meters)
    #Parameter 5- Bottom of layer (default to surface)

    print("Calculating 0-6km bulk shear")   


def calc_srh(data):
    #**0-1km bulk shear / Storm Relative Helicity**
    #Parameter 1- Atmospheric heights (AGL) (Need to interpolate using geopotential height for more accuarate calculations)
    #Parameter 2- U-component of wind (corresponding to height)
    #Parameter 3- V-component of wind
    #Parameter 4- Depth of layer (Either 1km or 3km)
    #Parameter 5- Bottom of layer (default to surface)
    #Parameter 6- Storm motion (U-component)
    #Parameter 7- Storm motion (V-component)

    print("Calculating Storm Relative Helicity")


def calc_vertical_wind_shear(data):
    #**Vertical Wind Shear** 
    #Parameter 1- Geopotential Height
    #Parameter 2- U-component of wind
    #Parameter 3- V-component of wind
    #Compute rate of change with height with both u and v component of wind
    #Then find the magnitude by squaring both rate's of change, adding them together and finding the square root of that sum

    print("Calculating Vertical wind shear")


def calculate_era5():
    for year in range(1980, 2016):
        for month in range(1, 13):
            days_in_month = calendar.monthrange(year, month)

            for day in range(1, days_in_month + 1):

                #pull pressure and surface files for year/month/day
                press_path = f"C:/Users/lwojd/Data/era5/pressure/{year}/{month:02d}/era5_press_{year}{month:02d}{day:02d}.nc"
                sur_path = f"C:/Users/lwojd/Data/era5/surface/{year}/{month:02d}/era5_sur_{year}{month:02d}{day:02d}.nc"

                #open dataset
                ds_press = Dataset(press_path, 'r')
                ds_sur = Dataset(sur_path, 'r')





    #code goes here
    print("era5 data yayyyyy")

def calculate_hrrr(data):
    #code goes here
    print("hrrr data lets fucking goooo")
