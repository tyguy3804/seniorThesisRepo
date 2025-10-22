from herbie import Herbie
import xarray as xr
import os, calendar

##### HRRR EXTRACTION #####

#All of this data extraction will be very similar to everything I will be doing with ERA5 data. There will be less data (2021-2024) but the variables are all the same. 
#The file system will be in the data directory and have a subdirectory named hrrr. Inside that subdirectory will be another two subdirectories, 
# one with surface data and the other with pressure data.

os.makedirs(f"C:/Users/lwojd/Data/hrrr/surface", exist_ok=True)
os.makedirs(f"C:/Users/lwojd/Data/hrrr/pressure", exist_ok=True)

for year in range(2017, 2019):
    for month in range(12, 13):
        daysInMonth = calendar.monthrange(year, month)[1]

        for day in range(1, daysInMonth + 1):

            #create subdirectories for temp, wind, and pressure level data
            #create file for each day within the loop
            temp_sur_directory = f"C:/Users/lwojd/Data/hrrr/surface/{year:02d}/{month:02d}/temp"
            temp_file_name = f"temp_hrrr_sur_{year:02d}{month:02d}{day:02d}.nc"

            wind_sur_directory = f"C:/Users/lwojd/Data/hrrr/surface/{year:02d}/{month:02d}/wind"
            wind_file_name = f"wind_hrrr_sur_{year:02d}{month:02d}{day:02d}.nc"

            file_press_directory = f"C:/Users/lwojd/Data/hrrr/pressure/{year:02d}/{month:02d}"
            press_file_name = f"hrrr_press_{year:02d}{month:02d}{day:02d}.nc"

            os.makedirs(temp_sur_directory, exist_ok=True)
            os.makedirs(wind_sur_directory, exist_ok=True)
            os.makedirs(file_press_directory, exist_ok=True)

            #create path to be used when converting GRIB2 data into a netcdf(.nc) file
            temp_sur_path = os.path.join(temp_sur_directory, temp_file_name)
            wind_sur_path = os.path.join(wind_sur_directory, wind_file_name)
            file_press_path = os.path.join(file_press_directory, press_file_name)

            #check if file already exists so that we don't loop through previously looped over dates
            if os.path.exists(temp_sur_path) and os.path.exists(wind_sur_path) and os.path.exists(file_press_path):
                print (f"Skipping {year}-{month:02d}-{day:02d}, already downloaded.")
                continue
            
            all_temp_data = []
            all_wind_data = []
            all_press_data = []

            for time in range(0, 24):

                try:
                    surface_request = Herbie(
                        f"{year}-{month:02d}-{day:02d} {time:02d}:00",
                        model="hrrr",
                        product="sfc",
                        fxx=0,   
                    )

                    pressure_request = Herbie(
                        f"{year}-{month:02d}-{day:02d} {time:02d}:00",
                        model="hrrr",
                        product="prs",
                        fxx=0,
                    )

                    #seperate datasets into temp and wind because variables don't match so one dataset isn't allowed (EX: 2m and 10m)
                    temp = surface_request.xarray("(TMP:2 m|DPT:2 m|SPFH:2 m|PRES:sfc|APCP:sfc)")
                    wind = surface_request.xarray("(UGRD:10 m|VGRD:10 m)")

                    #create dataset of wind and temp values on all pressure levels
                    pressure = pressure_request.xarray("(:[U\|V]GRD:\d+ mb|HGT:\d+ mb|:(?:TMP\|DPT):)")
                
                    #create a new dimension for all datasets
                    #used later to concatenate datasets
                    temp = temp.expand_dims(time_val = [time])
                    wind = wind.expand_dims(time_val = [time])
                    pressure = pressure.expand_dims(time_val = [time])

                    temp_lat = temp['latitude']
                    temp_lon = temp['longitude']

                    wind_lat = wind['latitude']
                    wind_lon = wind['longitude']

                    press_lat = pressure['latitude']
                    press_lon = pressure['longitude']
            
                    #create box of the oklahoma area
                    temp_mask = (temp_lat >= 34) & (temp_lat <= 38) & (temp_lon >= -103) & (temp_lon <= -94)
                    wind_mask = (wind_lat >= 34) & (wind_lat <= 38) & (wind_lon >= -103) & (wind_lon <= -94)
                    press_mask = (press_lat >= 34) & (press_lat <= 38) & (press_lon >= -103) & (press_lon <= -94)

                    #subset temp, wind, and pressure levels data only for the oklahoma area
                    temp_subset = temp.where(temp_mask, drop=True)
                    wind_subset = wind.where(wind_mask, drop=True)
                    pressure_subset = pressure.where(press_mask, drop=True)

                    all_temp_data.append(temp_subset)
                    all_wind_data.append(wind_subset)
                    all_press_data.append(pressure_subset)
                except Exception as e:
                    print(f"Skipping time={time:02d}:00 (not available): {e}")
            
            #make sure the data list isn't empty
            if all_temp_data and all_wind_data and all_press_data:
                temp_dataset = xr.concat(all_temp_data, dim="time_val")
                wind_dataset = xr.concat(all_wind_data, dim="time_val")
                pressure_dataset = xr.concat(all_press_data, dim="time_val")

                #convert to .nc file (if files don't already exist)
                if not (os.path.exists(temp_sur_path) and os.path.exists(wind_sur_path) and os.path.exists(file_press_path)):
                    temp_dataset.to_netcdf(temp_sur_path)
                    wind_dataset.to_netcdf(wind_sur_path)    
                    pressure_dataset.to_netcdf(file_press_path)
                    print(f"Dataset for {year}/{day}/{month} created.")
            else:
                print("List is empty, could not concatenate OR File already exists")

        