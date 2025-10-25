import os, calendar
import xarray as xr
import cdsapi
from metpy.calc import mixing_ratio, dewpoint_from_specific_humidity, lcl, cape_cin, parcel_profile, storm_relative_helicity, wind_components


#####ERA5 Data Extraction#####

#start looping through each year 1980-2015
#inside the year loop, start looping through each month
#inside the month loop, start looping through each day in the month

#in the file system there should be two folders (pressure and surface)
#then there should be subdirectories for each year and all twelve months within that year
#inside the month subdirectory will be all .nc files for each day in that month

#***IMPORTANT HOLES IN DATA EXTRACTION***
#Surface Level data: No data for 1980, 1981, 1982
#Pressure Level data: Data up until 12/08/1982
#Unfinished Data extraction for 1983

#last file extracted: 10/18/1982
for year in range(1980, 2016):
    for month in range(1, 13):
        daysInMonth = calendar.monthrange(year, month)[1]

        for day in range(1, daysInMonth + 1): 

            press_dir = f"C:/Users/lwojd/Data/era5/pressure/{year}/{month:02d}"
            sur_dir = f"C:/Users/lwojd/Data/era5/surface/{year}/{month:02d}"

            os.makedirs(press_dir, exist_ok=True)
            os.makedirs(sur_dir, exist_ok=True)


            press_file = f"{press_dir}/era5_press_{year}{month:02d}{day:02d}.nc"
            sur_file = f"{sur_dir}/era5_sur_{year}{month:02d}{day:02d}.nc"

            if os.path.exists(press_file) and os.path.exists(sur_file):
                print (f"Skipping {year}-{month:02d}-{day:02d}, already downloaded.")
                continue
            
            pressure_dataset = "reanalysis-era5-pressure-levels"
            pressure_request = {
                "product_type": "reanalysis",
                "variable": [
                    "geopotential",
                    "specific_humidity",
                    "temperature",
                    "u_component_of_wind",
                    "v_component_of_wind"
                ],
                "year": f"{year}",
                "month": f"{month}",
                "day": f"{day}",
                "time": [
                    "00:00","01:00","02:00","03:00",
                    "04:00","05:00","06:00","07:00",
                    "08:00","09:00","10:00","11:00",
                    "12:00","13:00","14:00","15:00",
                    "16:00","17:00","18:00","19:00",
                    "20:00","21:00","22:00","23:00"
                ],
                "pressure_level": [
                    "100", "150", "200",
                    "250", "300", "400",
                    "500", "700", "850",
                    "925", "1000"
                ],
                "area": [37, -103, 33.6, -94.4],  
                "format": "netcdf"
            }

            surface_dataset = "reanalysis-era5-single-levels"
            surface_request = {
                "product_type": "reanalysis",
                "variable": [
                    "2m_temperature",
                    "surface_pressure",
                ],
                "year": f"{year}",
                "month": f"{month}",
                "day": f"{day}",
                "time": [
                        "00:00","01:00","02:00","03:00",
                        "04:00","05:00","06:00","07:00",
                        "08:00","09:00","10:00","11:00",
                        "12:00","13:00","14:00","15:00",
                        "16:00","17:00","18:00","19:00",
                        "20:00","21:00","22:00","23:00"
                    ],
                "area": [37, -103, 33.6, -94.4], 
                "format": "netcdf"
            }
            
            client = cdsapi.Client()
            if not os.path.exists(press_file):
                client.retrieve(pressure_dataset, pressure_request, press_file)

            if not os.path.exists(sur_file):
                client.retrieve(surface_dataset, surface_request, sur_file)
