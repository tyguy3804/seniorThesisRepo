from herbie import Herbie
import xarray as xr
import os, calendar
import warnings

# Configure warnings and xarray at the start
warnings.filterwarnings('ignore', category=FutureWarning)
warnings.filterwarnings('ignore', category=UserWarning, message='.*regular expression.*')
xr.set_options(use_new_combine_kwarg_defaults=True)

##### HRRR EXTRACTION #####

os.makedirs(f"C:/Users/lwojd/Data/hrrr/surface", exist_ok=True)
os.makedirs(f"C:/Users/lwojd/Data/hrrr/pressure", exist_ok=True)

# Oklahoma bounds (converted to 0-360° longitude format)
lat_min, lat_max = 34, 38
lon_min, lon_max = 257, 266  # -103° and -94° converted to 0-360°

TARGET_LAT_POINTS = 14
TARGET_LONG_POINTS = 35

for year in range(2016, 2019):
    for month in range(1, 13):
        daysInMonth = calendar.monthrange(year, month)[1]

        for day in range(1, daysInMonth + 1):

            #create subdirectories for temp, wind, and pressure level data
            temp_sur_directory = f"C:/Users/lwojd/Data/hrrr/surface/{year:04d}/{month:02d}/temp"
            temp_file_name = f"temp_hrrr_sur_{year:04d}{month:02d}{day:02d}.nc"

            file_press_directory = f"C:/Users/lwojd/Data/hrrr/pressure/{year:04d}/{month:02d}"
            press_file_name = f"hrrr_press_{year:04d}{month:02d}{day:02d}.nc"

            os.makedirs(temp_sur_directory, exist_ok=True)
            os.makedirs(file_press_directory, exist_ok=True)

            #create path to be used when converting GRIB2 data into a netcdf(.nc) file
            temp_sur_path = os.path.join(temp_sur_directory, temp_file_name)
            file_press_path = os.path.join(file_press_directory, press_file_name)

            #check if file already exists
            if os.path.exists(temp_sur_path) and os.path.exists(file_press_path):
                print(f"Skipping {year}-{month:02d}-{day:02d}, already downloaded.")
                continue
            
            all_temp_data = []
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

                    # Get surface variables
                    temp_list = surface_request.xarray("(TMP:2 m|PRES:surface)")

                    if isinstance(temp_list, list):
                        temp = xr.merge(temp_list, compat='override')
                    else:
                        temp = temp_list

                    # Get pressure level data
                    levels = "100|150|200|250|300|400|500|700|850|925|1000"
                    pressure = pressure_request.xarray(f":(UGRD|VGRD|HGT|TMP|DPT):({levels}) mb")

                    # Set coords if needed
                    if 'latitude' not in temp.dims:
                        temp = temp.set_coords(['latitude', 'longitude'])
                    if 'latitude' not in pressure.dims:
                        pressure = pressure.set_coords(['latitude', 'longitude'])
                    
                    # Expand dimensions with actual datetime
                    time_coord = f"{year}-{month:02d}-{day:02d}T{time:02d}:00:00"
                    temp = temp.expand_dims(time_val=[time_coord])
                    pressure = pressure.expand_dims(time_val=[time_coord])
                    
                    # Create masks with CORRECT longitude bounds (257-266)
                    temp_mask = (temp['latitude'] >= lat_min) & (temp['latitude'] <= lat_max) & \
                                (temp['longitude'] >= lon_min) & (temp['longitude'] <= lon_max)
                    press_mask = (pressure['latitude'] >= lat_min) & (pressure['latitude'] <= lat_max) & \
                                 (pressure['longitude'] >= lon_min) & (pressure['longitude'] <= lon_max)
                    
                    temp_subset = temp.where(temp_mask, drop=True)
                    pressure_subset = pressure.where(press_mask, drop=True)

                    coarsen_y = temp_subset.sizes['y'] // 14
                    coarsen_x = temp_subset.sizes['x'] // 35

                    temp_coarse = temp_subset.coarsen(x= coarsen_x, y= coarsen_y, boundary= 'trim').mean()
                    pressure_coarse = pressure_subset.coarsen(x= coarsen_x, y= coarsen_y, boundary= 'trim').mean()

                    #print("Original shape:", temp_subset.sizes)
                    #print("Coarsened shape:", temp_coarse.sizes)
                    print("\nLat/lon coordinates are preserved:")
                    print("Lat shape:", temp_coarse['latitude'].shape)
                    print("Lon shape:", temp_coarse['longitude'].shape)

                    # Check if we got data
                    if temp_coarse.sizes.get('y', pressure_coarse.sizes.get('x', 0)) > 0:
                        all_temp_data.append(temp_coarse)
                        all_press_data.append(pressure_coarse)
                        print(f"{year}-{month:02d}-{day:02d} {time:02d}:00 - Success")
                    else:
                        print(f"{year}-{month:02d}-{day:02d} {time:02d}:00 - No data in region")
                        
                except Exception as e:
                    print(f"{year}-{month:02d}-{day:02d} {time:02d}:00 - Error: {e}")
            
            # Concatenate and save
            if all_temp_data and all_press_data:
                print(f"Concatenating {len(all_temp_data)} time steps for {year}-{month:02d}-{day:02d}...")
                temp_dataset = xr.concat(all_temp_data, dim="time_val")
                pressure_dataset = xr.concat(all_press_data, dim="time_val")

                # Clean attributes before saving
                for ds in [temp_dataset, pressure_dataset]:
                    ds.attrs = {}
                    for var in ds.data_vars:
                        ds[var].attrs = {}
                    for coord in ds.coords:
                        ds[coord].attrs = {}

                # Save to NetCDF
                temp_dataset.to_netcdf(temp_sur_path, engine='netcdf4')    
                pressure_dataset.to_netcdf(file_press_path, engine='netcdf4')
                print(f"Saved datasets for {year}-{month:02d}-{day:02d}\n")
            else:
                print(f"No data collected for {year}-{month:02d}-{day:02d}\n")