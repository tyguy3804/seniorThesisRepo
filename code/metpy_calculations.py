import metpy.calc as mpcalc
from metpy.units import units
from netCDF4 import Dataset
import xarray as xr
import numpy as np
import calendar
import os
import zipfile
import math

#data[time_index, pressure_level_index, latitude_index, longitude_index]
#time_index = 0-23 for all 24 hours of data
#pressure_level_index = 0-10 for all 11 pressure levels
#latitude_index = north to south (most likely use a : for all levles)
#longitude_index = east to west(use :)
    
#**Taken from this source https://unidata.github.io/MetPy/latest/examples/calculations/Sounding_Calculations.html#sphx-glr-examples-calculations-sounding-calculations-py**
def effective_layer(p, t, td, h, height_layer=False):
    """A function that determines the effective inflow layer for a convective sounding.

    Uses the default values of Thompason et al. (2004) for CAPE (100 J/kg) and CIN (-250 J/kg).

    Input:
      - p: sounding pressure with units
      - T: sounding temperature with units
      - Td: sounding dewpoint temperature with units
      - h: sounding heights with units

    Returns:
      - pbot/hbot, ptop/htop: pressure/height of the bottom level,
                              pressure/height of the top level
    """
    from metpy.calc import cape_cin, parcel_profile
    from metpy.units import units

    pbot = None

    for i in range(p.shape[0]):
        prof = parcel_profile(p[i:], t[i], td[i])
        sbcape, sbcin = cape_cin(p[i:], t[i:], td[i:], prof)
        if sbcape >= 100 * units('J/kg') and sbcin > -250 * units('J/kg'):
            pbot = p[i]
            hbot = h[i]
            bot_idx = i
            break
    if not pbot:
        return None, None

    for i in range(bot_idx + 1, p.shape[0]):
        prof = parcel_profile(p[i:], t[i], td[i])
        sbcape, sbcin = cape_cin(p[i:], t[i:], td[i:], prof)
        if sbcape < 100 * units('J/kg') or sbcin < -250 * units('J/kg'):
            ptop = p[i]
            htop = h[i]
            break

    if height_layer:
        return hbot, htop
    else:
        return pbot, ptop
    

def calculate_era5():
    n_times = 306600
    n_lat = 14
    n_long = 35

    lfc_dtype = [('lfc_press', 'f4'), ('lfc_temp', 'f4')]
    lcl_dtype = [('lcl_press', 'f4'), ('lcl_temp', 'f4')]
    ml_dtype = [('ml_CAPE', 'f4'), ('ml_CIN', 'f4')]
    sb_dtype = [('sb_CAPE', 'f4'), ('sb_CIN', 'f4')]
    mu_dtype = [('mu_CAPE', 'f4'), ('mu_CIN', 'f4')]

    #create data arrays for all variables
    pwat_array = np.zeros((n_times, n_lat, n_long))
    dewpt_array = np.zeros((n_times, n_lat, n_long, 11))
    lfc_array = np.zeros((n_times, n_lat, n_long), dtype=lfc_dtype)
    lcl_array = np.zeros((n_times, n_lat, n_long), dtype=lcl_dtype)
    lapse_rates_array = np.zeros((n_times, n_lat, n_long, 11))
    showalter_idx_array = np.zeros((n_times, n_lat, n_long))
    ml_CAPE_CIN_array = np.zeros((n_times, n_lat, n_long), dtype=ml_dtype)
    sb_CAPE_CIN_array = np.zeros((n_times, n_lat, n_long), dtype=sb_dtype)
    mu_CAPE_CIN_array = np.zeros((n_times, n_lat, n_long), dtype=mu_dtype)
    bulk_shear_0to3km_array = np.zeros((n_times, n_lat, n_long))
    bulk_shear_0to6km_array = np.zeros((n_times, n_lat, n_long))
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
                press_path = f"C:/Users/lwojd/Data/era5/pressure/{year}/{month:02d}/era5_press_{year}{month:02d}{day:02d}.nc"
                #press_path = f"C:/Users/lwojd/Data/era5/pressure/1980/05/era5_press_19800521.nc"

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
                    print(f"Time is: {time}")
                    for lat_idx in range(0, 14):
                        for(long_idx) in range(0, 35):
                            
                            p = ds_press.variables['pressure_level'][:]
                            sp = (ds_sur.variables['sp'][time, lat_idx, long_idx] / 100) * units.hPa
                            pressure = p.filled(np.nan) * units.hPa

                            q = ds_press.variables['q'][time, :, lat_idx, long_idx]
                            spec_humidity = q.filled(np.nan) * units('kg/kg')
                            spec_humidity = spec_humidity * 1000
                            spec_humidity = spec_humidity * units('g/kg')

                            t = ds_press.variables['t'][time, :, lat_idx, long_idx]
                            t2m = ds_sur.variables['t2m'][time, lat_idx, long_idx] * units.kelvin
                            temp = t.filled(np.nan) * units.kelvin
                            temp = temp.to('degC')

                            dewpt = mpcalc.dewpoint_from_specific_humidity(pressure, spec_humidity)
                            lcl_press, lcl_temp = mpcalc.lcl(pressure[0], temp[0], dewpt[0])
                            pwat = mpcalc.precipitable_water(pressure, dewpt)
                            lfc_press, lfc_temp = mpcalc.lfc(pressure, temp, dewpt)
                            lapse_rates = mpcalc.dry_lapse(pressure, temp[0]).to('degC')
                            showalter_idx = mpcalc.showalter_index(pressure, temp, dewpt)
                            ml_CAPE, ml_CIN = mpcalc.mixed_layer_cape_cin(pressure, temp, dewpt)
                            sb_CAPE, sb_CIN = mpcalc.surface_based_cape_cin(pressure, temp, dewpt)
                            mu_CAPE, mu_CIN = mpcalc.most_unstable_cape_cin(pressure, temp, dewpt)
                            
                            u = ds_press.variables['u'][time, :, lat_idx, long_idx]
                            v = ds_press.variables['v'][time, :, lat_idx, long_idx]
                            z = ds_press.variables['z'][time, :, lat_idx, long_idx]

                            u_wind = u.filled(np.nan) * units('m/s')
                            v_wind = v.filled(np.nan) * units('m/s')
                            geopotential = z.filled(np.nan) / 9.80665
                            geopotential_height = geopotential * units('m')
                            geopotential_agl = geopotential_height - geopotential_height[0]

                            u_shear_0to3km, v_shear_0to3km = mpcalc.bulk_shear(
                                pressure, 
                                u_wind, 
                                v_wind, 
                                height = geopotential_agl, 
                                bottom = 0 * units.m, 
                                depth = 3000 * units.m
                            )

                            bulk_shear_0to3km = np.sqrt(u_shear_0to3km**2 + v_shear_0to3km**2)
                            
                            u_shear_0to6km, v_shear_0to6km = mpcalc.bulk_shear(
                                pressure,
                                u_wind, 
                                v_wind,
                                height = geopotential_agl,
                                bottom = 0 * units.m,
                                depth = 6000 * units.m
                            )

                            bulk_shear_0to6km = np.sqrt(u_shear_0to6km**2 + v_shear_0to6km**2)

                            (u_storm, v_storm), *_ = mpcalc.bunkers_storm_motion(pressure, u_wind, v_wind, geopotential_agl)
                            *_, total_helicity = mpcalc.storm_relative_helicity(geopotential_agl, u_wind, v_wind, depth=1000 * units('m'), storm_u= u_storm, storm_v= v_storm)
                            
                            t_avg = (t2m + (lcl_temp.to('kelvin'))) / 2
                            lcl_height =  (287 * units('(m**2/s**2) / kelvin')) * t_avg
                            lcl_height = lcl_height / (9.81 * units('m/s**2'))
                            log_temp = sp / lcl_press
                            log_temp = math.log(log_temp)
                            lcl_height = lcl_height * log_temp

                            sig_tor_parameter = mpcalc.significant_tornado(sb_CAPE, lcl_height, total_helicity, bulk_shear_0to6km)

                            #eib_pressure, eit_pressure = effective_layer(pressure, temp, dewpt, geopotential_agl)
                            #
                            #if eib_pressure is None or eit_pressure is None:
                            #    scp = 0
                            #else:
                            #    u_eff_shear, v_eff_shear = mpcalc.bulk_shear(
                            #    pressure,
                            #    u_wind,
                            #    v_wind, 
                            #    height = geopotential_agl,
                            #    bottom = eib_pressure,
                            #    depth = eit_pressure - eib_pressure
                            #    )

                            #    effective_bulk_shear = np.sqrt(u_eff_shear**2 + v_eff_shear**2)

                            #    *_, effective_srh = mpcalc.storm_relative_helicity(geopotential_agl, u_wind, v_wind, depth= eit_pressure - eib_pressure, storm_u = u_storm, storm_v = v_storm)
                            #    supercell_composite = mpcalc.supercell_composite(mu_CAPE, effective_bulk_shear, effective_srh)

                            pwat_array[time, lat_idx, long_idx] = pwat.magnitude
                            dewpt_array[time, lat_idx, long_idx, :] = dewpt.magnitude
                            lfc_array[time, lat_idx, long_idx] = (lfc_press.magnitude, lfc_temp.magnitude)
                            lcl_array[time, lat_idx, long_idx] = (lcl_press.magnitude, lcl_temp.magnitude)
                            lapse_rates_array[time, lat_idx, long_idx, :] = lapse_rates.magnitude
                            showalter_idx_array[time, lat_idx, long_idx] = showalter_idx.magnitude
                            ml_CAPE_CIN_array[time, lat_idx, long_idx] = (ml_CAPE.magnitude, ml_CIN.magnitude)
                            sb_CAPE_CIN_array[time, lat_idx, long_idx] = (sb_CAPE.magnitude, sb_CIN.magnitude)
                            mu_CAPE_CIN_array[time, lat_idx, long_idx] = (mu_CAPE.magnitude, mu_CIN.magnitude)
                            bulk_shear_0to3km_array[time, lat_idx, long_idx] = bulk_shear_0to3km.magnitude
                            bulk_shear_0to6km_array[time, lat_idx, long_idx] = bulk_shear_0to6km.magnitude
                            srh_array[time, lat_idx, long_idx] = total_helicity.magnitude
                            sig_tor_array[time, lat_idx, long_idx] = sig_tor_parameter.magnitude
                            #supercell_array[time, lat_idx, long_idx] = supercell_composite.magnitude



    #code goes here
    print("era5 data yayyyyy")

def calculate_hrrr(data):
    #code goes here
    print("hrrr data lets fucking goooo")


calculate_era5()