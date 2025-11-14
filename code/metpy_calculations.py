import metpy.calc as mpcalc
from metpy.units import units
from netCDF4 import Dataset
import xarray as xr
import numpy as np
import calendar
import os
import zipfile
import math
    
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

#---------------------------------------------------------------------------------
# HRRR Calculations
    
def get_hrrr_variables(ds_press, ds_sur, time, lat_idx, long_idx, variables= 'all'):

    if variables == 'all':
        variables = ['pressure', 'dewpt', 'temp','t2m', 'sp', 'u_wind', 'v_wind', 'geopotential_agl']
    
    results = {}
    
    if 'pressure' in variables:
        p = ds_press.variables['isobaricInhPa'][:]
        pressure = p.filled(np.nan) * units.hPa
        results['pressure'] = pressure

    if 'sp' in variables:
        sp = ds_sur.variables['sp'][time, lat_idx, long_idx] * units.hPa
        results['sp'] = sp
    
    if 'dewpt' in variables:
        td = ds_press.variables['dpt'][time, :, lat_idx, long_idx]
        dewpt = td.filled(np.nan) * units.kelvin
        results['dewpt'] = dewpt

    if 'temp' in variables:
        t = ds_press.variables['t'][time, :, lat_idx, long_idx]
        temp = t.filled(np.nan) * units.kelvin
        temp = temp.to('degC')
        results['temp'] = temp

    if 't2m' in variables:
        t2m = ds_sur.variables['t2m'][time, lat_idx, long_idx] * units.kelvin
        results['t2m'] = t2m

    if 'u_wind' in variables and 'v_wind' in variables:
        u = ds_press.variables['u'][time, :, lat_idx, long_idx]
        v = ds_press.variables['v'][time, :, lat_idx, long_idx]
        u_wind = u.filled(np.nan) * units('m/s')
        v_wind = v.filled(np.nan) * units('m/s')
        results['u_wind'] = u_wind
        results['v_wind'] = v_wind
    
    if 'geopotential_agl' in variables:
        z = ds_press.variables['z'][time, :, lat_idx, long_idx]
        geopotential = z.filled(np.nan) / 9.80665
        geopotential_height = geopotential * units('m')
        geopotential_agl = geopotential_height - geopotential_height[0]
        results['geopotential_agl'] = geopotential_agl

    return results

def hrrr_calculate_pwat(ds_press, ds_sur, time, lat_idx, long_idx):
    data = get_era5_variables(ds_press, ds_sur, time, lat_idx, long_idx, variables= ['pressure', 'dewpt'])

    pressure = data['pressure']
    dewpt = data['dewpt']

    if np.isnan(dewpt).any() == False:
        pwat = mpcalc.precipitable_water(pressure, dewpt)
        return pwat
    else:
        return 0.0 * units.dimensionless
    
def hrrr_calculate_lcl(ds_press, ds_sur, time, lat_idx, long_idx):
    data = get_era5_variables(ds_press, ds_sur, time, lat_idx, long_idx, variables= ['pressure', 'dewpt', 'temp'])   

    pressure = data['pressure']
    temp = data['temp']
    dewpt = data['dewpt']

    if np.isnan(temp).any() == False or np.isnan(dewpt).any() == False:

        lcl_press, lcl_temp = mpcalc.lcl(pressure[0], temp[0], dewpt[0])
        return lcl_press, lcl_temp
    else:
        return 0.0, 0.0

def hrrr_calculate_lfc(ds_press, ds_sur, time, lat_idx, long_idx):
    data = get_era5_variables(ds_press, ds_sur, time, lat_idx, long_idx, variables= ['pressure', 'dewpt', 'temp']) 

    pressure = data['pressure']
    temp = data['temp']
    dewpt = data['dewpt']

    if np.isnan(temp).any() == False or np.isnan(dewpt).any() == False:

        lfc_press, lfc_temp = mpcalc.lfc(pressure, temp, dewpt)
        return lfc_press, lfc_temp
    else:
        return 0.0, 0.0

def hrrr_calculate_lapse_rates(ds_press, ds_sur, time, lat_idx, long_idx):
    data = get_hrrr_variables(ds_press, ds_sur, time, lat_idx, long_idx, variables= ['pressure', 'dewpt', 'temp']) 

    pressure = data['pressure']
    temp = data['temp']
    dewpt = data['dewpt']

    if np.isnan(temp).any() == False or np.isnan(dewpt).any() == False:

        lapse_rates = mpcalc.dry_lapse(pressure, temp[0]).to('degC')
        return lapse_rates
    else:
        return [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0 ] * units.kelvin     

def hrrr_calculate_showalter_idx(ds_press, ds_sur, time, lat_idx, long_idx):
    data = get_hrrr_variables(ds_press, ds_sur, time, lat_idx, long_idx, variables= ['pressure', 'dewpt', 'temp']) 

    pressure = data['pressure']
    temp = data['temp']
    dewpt = data['dewpt']

    if np.isnan(temp).any() == False or np.isnan(dewpt).any() == False:
        showalter_idx = mpcalc.showalter_index(pressure, temp, dewpt)
        return showalter_idx
    else:
        return 0.0

def hrrr_calculate_ml_CAPE_CIN(ds_press, ds_sur, time, lat_idx, long_idx):
    data = get_hrrr_variables(ds_press, ds_sur, time, lat_idx, long_idx, variables= ['pressure', 'dewpt', 'temp']) 

    pressure = data['pressure']
    temp = data['temp']
    dewpt = data['dewpt']
    
    if np.isnan(temp).any() == False or np.isnan(dewpt).any() == False:
        ml_CAPE, ml_CIN = mpcalc.mixed_layer_cape_cin(pressure, temp, dewpt)
    else:
        return 0.0

def hrrr_calculate_sb_CAPE_CIN(ds_press, ds_sur, time, lat_idx, long_idx):
    data = get_hrrr_variables(ds_press, ds_sur, time, lat_idx, long_idx, variables= ['pressure', 'dewpt', 'temp']) 

    pressure = data['pressure']
    temp = data['temp']
    dewpt = data['dewpt']

    if np.isnan(temp).any() == False or np.isnan(dewpt).any() == False:
    
        sb_CAPE, sb_CIN = mpcalc.surface_based_cape_cin(pressure, temp, dewpt)
        return sb_CAPE, sb_CIN
    else:
        return 0.0, 0.0

def hrrr_calculate_mu_CAPE_CIN(ds_press, ds_sur, time, lat_idx, long_idx):
    data = get_hrrr_variables(ds_press, ds_sur, time, lat_idx, long_idx, variables= ['pressure', 'dewpt', 'temp']) 

    pressure = data['pressure']
    temp = data['temp']
    dewpt = data['dewpt']

    if np.isnan(temp).any() == False or np.isnan(dewpt).any() == False:
        mu_CAPE, mu_CIN = mpcalc.most_unstable_cape_cin(pressure, temp, dewpt)
        return mu_CAPE, mu_CIN
    else:
        return 0.0, 0.0

def hrrr_calculate_bulk_shear(ds_press, ds_sur, time, lat_idx, long_idx, depth_m):
    data = get_hrrr_variables(ds_press, ds_sur, time, lat_idx, long_idx, variables= ['pressure', 'u_wind', 'v_wind', 'geopotential_agl'])

    pressure = data['pressure']
    u_wind = data['u_wind']
    v_wind = data['v_wind']
    geo_agl = data['geopotential_agl']

    u_shear, v_shear = mpcalc.bulk_shear(
        pressure,
        u_wind,
        v_wind,
        height = geo_agl,
        bottom = 0 * units.m,
        depth = depth_m * units.m
    )

    bulk_shear = np.sqrt(u_shear**2 + v_shear**2)
    return bulk_shear

def hrrr_calculate_srh(ds_press, ds_sur, time, lat_idx, long_idx):
    data = get_hrrr_variables(ds_press, ds_sur, time, lat_idx, long_idx, variables= ['pressure', 'u_wind', 'v_wind', 'geopotential_agl'])

    pressure = data['pressure']
    u_wind = data['u_wind']
    v_wind = data['v_wind']
    geo_agl = data['geopotential_agl']

    (u_storm, v_storm), *_ = mpcalc.bunkers_storm_motion(pressure, u_wind, v_wind, geo_agl)
    *_, total_helicity = mpcalc.storm_relative_helicity(
        geo_agl,
        u_wind,
        v_wind,
        depth= 1000 * units.m,
        storm_u= u_storm,
        storm_v= v_storm
    )
    return total_helicity

def hrrr_calculate_sig_tor(ds_press, ds_sur, time, lat_idx, long_idx, sb_CAPE, lcl_press, lcl_temp, total_helicity, bulk_shear_0to6km):
    data = get_hrrr_variables(ds_press, ds_sur, time, lat_idx, long_idx, variables= ['sp', 't2m'])

    sp = data['sp']
    t2m = data['t2m']
    
    t_avg = (t2m + (lcl_temp.to('kelvin'))) / 2
    lcl_height =  (287 * units('(m**2/s**2) / kelvin')) * t_avg
    lcl_height = lcl_height / (9.81 * units('m/s**2'))
    log_temp = sp / lcl_press
    log_temp = math.log(log_temp)
    lcl_height = lcl_height * log_temp

    sig_tor_parameter = mpcalc.significant_tornado(sb_CAPE, lcl_height, total_helicity, bulk_shear_0to6km)
    return sig_tor_parameter

def hrrr_calculate_supercell_comp(ds_press, ds_sur, time, lat_idx, long_idx, mu_CAPE):
    data = get_hrrr_variables(ds_press, ds_sur, time, lat_idx, long_idx, variables= ['pressure', 'temp', 'dewpt', 'u_wind', 'v_wind', 'geopotential_agl'])

    pressure = data['pressure']
    temp = data['temp']
    dewpt = data['dewpt']
    u_wind = data['u_wind']
    v_wind = data['v_wind']
    geo_agl = data['geopotential_agl']

    eib_pressure, eit_pressure = effective_layer(pressure, temp, dewpt, geo_agl)

    if eib_pressure is None or eit_pressure is None:
        supercell_comp = 0 * units.dimensionless
    else:
        u_eff_shear, v_eff_shear = mpcalc.bulk_shear(
            pressure,
            u_wind,
            v_wind,
            height = geo_agl,
            bottom = eib_pressure,
            depth = eit_pressure - eib_pressure
        )

        effective_bulk_shear = np.sqrt(u_eff_shear**2 + v_eff_shear**2)
        (u_storm, v_storm), *_ = mpcalc.bunkers_storm_motion(pressure, u_wind, v_wind, geo_agl)

        *_, effective_srh = mpcalc.storm_relative_helicity(
            geo_agl, 
            u_wind,
            v_wind,
            depth = eit_pressure - eib_pressure,
            storm_u = u_storm,
            storm_v = v_storm
        )

        supercell_comp = mpcalc.supercell_composite(mu_CAPE, effective_bulk_shear, effective_srh)
        return supercell_comp

#-----------------------------------------------------------------------------------------------
#ERA5 Calculations


def get_era5_variables(ds_press, ds_sur, time, lat_idx, long_idx, variables= 'all'):

    if variables == 'all':
        variables = ['pressure', 'dewpt', 'temp','t2m', 'sp', 'u_wind', 'v_wind', 'geopotential_agl']
    
    results = {}
    
    if 'pressure' in variables:
        p = ds_press.variables['pressure_level'][:]
        pressure = p.filled(np.nan) * units.hPa
        results['pressure'] = pressure

    if 'sp' in variables:
        sp = (ds_sur.variables['sp'][time, lat_idx, long_idx] / 100) * units.hPa
        results['sp'] = sp
    
    if 'dewpt' in variables:
        q = ds_press.variables['q'][time, :, lat_idx, long_idx]
        spec_humidity = q.filled(np.nan) * units('kg/kg')
        spec_humidity = spec_humidity * 1000
        spec_humidity = spec_humidity * units('g/kg')
        dewpt = mpcalc.dewpoint_from_specific_humidity(pressure, spec_humidity)
        results['dewpt'] = dewpt

    if 'temp' in variables:
        t = ds_press.variables['t'][time, :, lat_idx, long_idx]
        temp = t.filled(np.nan) * units.kelvin
        temp = temp.to('degC')
        results['temp'] = temp

    if 't2m' in variables:
        t2m = ds_sur.variables['t2m'][time, lat_idx, long_idx] * units.kelvin
        results['t2m'] = t2m

    if 'u_wind' in variables and 'v_wind' in variables:
        u = ds_press.variables['u'][time, :, lat_idx, long_idx]
        v = ds_press.variables['v'][time, :, lat_idx, long_idx]
        u_wind = u.filled(np.nan) * units('m/s')
        v_wind = v.filled(np.nan) * units('m/s')
        results['u_wind'] = u_wind
        results['v_wind'] = v_wind
    
    if 'geopotential_agl' in variables:
        z = ds_press.variables['z'][time, :, lat_idx, long_idx]
        geopotential = z.filled(np.nan) / 9.80665
        geopotential_height = geopotential * units('m')
        geopotential_agl = geopotential_height - geopotential_height[0]
        results['geopotential_agl'] = geopotential_agl

    return results

def era5_calculate_pwat(ds_press, ds_sur, time, lat_idx, long_idx):
    data = get_era5_variables(ds_press, ds_sur, time, lat_idx, long_idx, variables= ['pressure', 'dewpt'])

    pressure = data['pressure']
    dewpt = data['dewpt']

    pwat = mpcalc.precipitable_water(pressure, dewpt)
    return pwat

def era5_calculate_lcl(ds_press, ds_sur, time, lat_idx, long_idx):
    data = get_era5_variables(ds_press, ds_sur, time, lat_idx, long_idx, variables= ['pressure', 'dewpt', 'temp'])   

    pressure = data['pressure']
    temp = data['temp']
    dewpt = data['dewpt']

    lcl_press, lcl_temp = mpcalc.lcl(pressure[0], temp[0], dewpt[0])
    return lcl_press, lcl_temp

def era5_calculate_lfc(ds_press, ds_sur, time, lat_idx, long_idx):
    data = get_era5_variables(ds_press, ds_sur, time, lat_idx, long_idx, variables= ['pressure', 'dewpt', 'temp']) 

    pressure = data['pressure']
    temp = data['temp']
    dewpt = data['dewpt']

    lfc_press, lfc_temp = mpcalc.lfc(pressure, temp, dewpt)
    return lfc_press, lfc_temp

def era5_calculate_lapse_rates(ds_press, ds_sur, time, lat_idx, long_idx):
    data = get_era5_variables(ds_press, ds_sur, time, lat_idx, long_idx, variables= ['pressure', 'dewpt', 'temp']) 

    pressure = data['pressure']
    temp = data['temp']
    dewpt = data['dewpt']

    lapse_rates = mpcalc.dry_lapse(pressure, temp[0]).to('degC')

    return lapse_rates

def era5_calculate_showalter_idx(ds_press, ds_sur, time, lat_idx, long_idx):
    data = get_era5_variables(ds_press, ds_sur, time, lat_idx, long_idx, variables= ['pressure', 'dewpt', 'temp']) 

    pressure = data['pressure']
    temp = data['temp']
    dewpt = data['dewpt']

    showalter_idx = mpcalc.showalter_index(pressure, temp, dewpt)

    return showalter_idx

def era5_calculate_ml_CAPE_CIN(ds_press, ds_sur, time, lat_idx, long_idx):
    data = get_era5_variables(ds_press, ds_sur, time, lat_idx, long_idx, variables= ['pressure', 'dewpt', 'temp']) 

    pressure = data['pressure']
    temp = data['temp']
    dewpt = data['dewpt']

    ml_CAPE, ml_CIN = mpcalc.mixed_layer_cape_cin(pressure, temp, dewpt)

    return ml_CAPE, ml_CIN

def era5_calculate_sb_CAPE_CIN(ds_press, ds_sur, time, lat_idx, long_idx):
    data = get_era5_variables(ds_press, ds_sur, time, lat_idx, long_idx, variables= ['pressure', 'dewpt', 'temp']) 
    
    pressure = data['pressure']
    temp = data['temp']
    dewpt = data['dewpt']

    sb_CAPE, sb_CIN = mpcalc.surface_based_cape_cin(pressure, temp, dewpt)

    return sb_CAPE, sb_CIN

def era5_calculate_mu_CAPE_CIN(ds_press, ds_sur, time, lat_idx, long_idx):
    data = get_era5_variables(ds_press, ds_sur, time, lat_idx, long_idx, variables= ['pressure', 'dewpt', 'temp']) 

    pressure = data['pressure']
    temp = data['temp']
    dewpt = data['dewpt']

    mu_CAPE, mu_CIN = mpcalc.most_unstable_cape_cin(pressure, temp, dewpt)

    return mu_CAPE, mu_CIN

def era5_calculate_bulk_shear(ds_press, ds_sur, time, lat_idx, long_idx, depth_m):
    data = get_era5_variables(ds_press, ds_sur, time, lat_idx, long_idx, variables= ['pressure', 'u_wind', 'v_wind', 'geopotential_agl'])

    pressure = data['pressure']
    u_wind = data['u_wind']
    v_wind = data['v_wind']
    geo_agl = data['geopotential_agl']

    u_shear, v_shear = mpcalc.bulk_shear(
        pressure,
        u_wind,
        v_wind,
        height = geo_agl,
        bottom = 0 * units.m,
        depth = depth_m * units.m
    )

    bulk_shear = np.sqrt(u_shear**2 + v_shear**2)

    return bulk_shear

def era5_calculate_srh(ds_press, ds_sur, time, lat_idx, long_idx):
    data = get_era5_variables(ds_press, ds_sur, time, lat_idx, long_idx, variables= ['pressure', 'u_wind', 'v_wind', 'geopotential_agl'])

    pressure = data['pressure']
    u_wind = data['u_wind']
    v_wind = data['v_wind']
    geo_agl = data['geopotential_agl']

    (u_storm, v_storm), *_ = mpcalc.bunkers_storm_motion(pressure, u_wind, v_wind, geo_agl)
    *_, total_helicity = mpcalc.storm_relative_helicity(
        geo_agl,
        u_wind,
        v_wind,
        depth= 1000 * units.m,
        storm_u= u_storm,
        storm_v= v_storm
    )

    return total_helicity

def era5_calculate_sig_tor(ds_press, ds_sur, time, lat_idx, long_idx, sb_CAPE, lcl_press, lcl_temp, total_helicity, bulk_shear_0to6km):
    data = get_era5_variables(ds_press, ds_sur, time, lat_idx, long_idx, variables= ['sp', 't2m'])

    sp = data['sp']
    t2m = data['t2m']
    
    t_avg = (t2m + (lcl_temp.to('kelvin'))) / 2
    lcl_height =  (287 * units('(m**2/s**2) / kelvin')) * t_avg
    lcl_height = lcl_height / (9.81 * units('m/s**2'))
    log_temp = sp / lcl_press
    log_temp = math.log(log_temp)
    lcl_height = lcl_height * log_temp

    sig_tor_parameter = mpcalc.significant_tornado(sb_CAPE, lcl_height, total_helicity, bulk_shear_0to6km)

    return sig_tor_parameter

def era5_calculate_supercell_comp(ds_press, ds_sur, time, lat_idx, long_idx, mu_CAPE):
    data = get_era5_variables(ds_press, ds_sur, time, lat_idx, long_idx, variables= ['pressure', 'temp', 'dewpt', 'u_wind', 'v_wind', 'geopotential_agl'])

    pressure = data['pressure']
    temp = data['temp']
    dewpt = data['dewpt']
    u_wind = data['u_wind']
    v_wind = data['v_wind']
    geo_agl = data['geopotential_agl']

    eib_pressure, eit_pressure = effective_layer(pressure, temp, dewpt, geo_agl)

    if eib_pressure is None or eit_pressure is None:
        supercell_comp = 0 * units.dimensionless
    else:
        u_eff_shear, v_eff_shear = mpcalc.bulk_shear(
            pressure,
            u_wind,
            v_wind,
            height = geo_agl,
            bottom = eib_pressure,
            depth = eit_pressure - eib_pressure
        )

        effective_bulk_shear = np.sqrt(u_eff_shear**2 + v_eff_shear**2)
        (u_storm, v_storm), *_ = mpcalc.bunkers_storm_motion(pressure, u_wind, v_wind, geo_agl)

        *_, effective_srh = mpcalc.storm_relative_helicity(
            geo_agl, 
            u_wind,
            v_wind,
            depth = eit_pressure - eib_pressure,
            storm_u = u_storm,
            storm_v = v_storm
        )

        supercell_comp = mpcalc.supercell_composite(mu_CAPE, effective_bulk_shear, effective_srh)

        return supercell_comp

