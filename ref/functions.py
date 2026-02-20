import numpy as np
import unyt as u

import os
import io
import base64

def analog_output_to_reading(min, max, reading):
    gradient = (max-min) / (20 - 4)
    intercept = min
    return(gradient * (reading - 4) + intercept)

def reading_to_analog_output(min, max, reading):
    gradient = (20 - 4) / (max-min)
    intercept = 4
    return(gradient * (reading - min) + intercept)

def percent_error(measured_value, true_value):
    if measured_value == 0 or true_value == 0:
        return 0.0
    return(abs(measured_value - true_value)/true_value) * 100 # in percent 0-100%

def tube_flow_to_velo(flow, OD = 0 * u.meter, thick = 0 * u.meter):
    ID = OD - (2*thick)
    velocity = flow / ((1/4) * np.pi * (ID**2))
    return velocity.to('m/s')

def tube_vol(length, OD = 0 * u.meter, thick = 0 * u.meter, vol_per_length = 0 * u.centimeter**3 / u.foot):
    print(length, OD, thick)
    if vol_per_length > 0:
        vol = (vol_per_length * length).to('cm**3')
    else:
        ID = OD - (2 * thick)
        area = np.pi * (ID / 2)**2
        vol = (area * length).to('cm**3')
    return vol

def calc_lag_time(vol, Q, P, Patm, O = 1):
    time = vol / Q * (P/Patm) * O
    return time.to('second')

def temperature_drop_tube(k, length, insl_thick, tube_dia, flow_rate, density, c, ambient_temp, system_temp):
    OD = (tube_dia + 2 * (insl_thick)).to('meter')
    ID = tube_dia.to('meter')
    k = k.to('J/(K*m*second)')
    length = length.to('meter')
    insl_thick = insl_thick.to('meter')
    flow_rate = flow_rate.to('m**3/second')
    density = density.to('kg/m**3')
    c = c.to('J/(K*kg)')
    ambient_temp = ambient_temp.to('Kelvin')
    system_temp = system_temp.to('Kelvin')
    

    max_heat_loss = flow_rate * density * c * (ambient_temp - system_temp)
    heat_loss = k * 2 * np.pi * length * (ambient_temp - system_temp) / np.log(OD/ID)
    if abs(heat_loss) > abs(max_heat_loss):
        heat_loss = max_heat_loss
        final_temp = ambient_temp
        max_length = heat_loss * np.log(OD/ID) / (k * 2 * np.pi * (ambient_temp - system_temp))
        max_heat_loss = k * 2 * np.pi * max_length * (ambient_temp - system_temp) / np.log(OD/ID)
        print('max heat-loss', max_heat_loss)
        print('length needed to drop to ambient', max_length)
        print('heat-loss', heat_loss)
        return(ambient_temp.to('celcius'), heat_loss)

    final_temp = system_temp + (heat_loss / (flow_rate * density * c))
    print('max heat-loss', max_heat_loss)
    print('heat-loss', heat_loss)
    return(ambient_temp.to('celcius'), heat_loss)

# thermal_conductivity = 0.04 * u.watt / (u.meter * u.kelvin) # for Fiberglass from https://www.engineeringtoolbox.com/thermal-conductivity-d_429.html
# length = 18 * u.meter
# insl = 0.336 * u.inch
# OD = 6 * u.milimeter
# flow_rate = 3 * u.decimeter**3 / u.minute
# density = 1 * u.kg / (u.meter**3) # mean of densities from simulation result at 50degC and 125degC
# heat_capacity = 1040.2917495525905 * u.joule / (u.kilogram * u.kelvin) # from simulation result at 125degC
# ambient_temp = 35 * u.celcius
# system_temp = 125 * u.celcius

# temp_drop, heat_loss = temperature_drop_tube(thermal_conductivity, length, insl, OD, flow_rate, density, heat_capacity, ambient_temp, system_temp)

class dp_friction():
    def __init__(self, OD, length, sch, abs_roughness, flow_rate, visc, rho):
        self.OD = OD.to('meter')
        self.length = length.to('meter')
        self.sch = sch.to('meter')
        self.abs_roughness = abs_roughness.to('meter')
        self.flow_rate = flow_rate.to('m**3/second')
        self.visc = visc.to('kg/(m*second)')
        self.rho = rho.to('kg/m**3')
        self.ID = self.OD - (2*self.sch)
        self.area = 3.14 * (1/2*self.ID)**2
        self.vel = self.flow_rate / self.area
        self.RE = self.rho * self.vel * self.ID / self.visc
    
    def calculate_fric_factor(self):
        self.fric_factor = dict()
        self.fric_factor['laminar'] = 64 / self.RE
        self.fric_factor['churchill'] = 8*((8/self.RE)**12+(1/((2.457*np.log((7/self.RE)**0.9+0.27*(self.abs_roughness/self.ID)))**16+(37530/self.RE)**16)**(3/2)))**(1/12)
        self.fric_factor['chen'] = (1/(-4*np.log10((self.abs_roughness/self.ID/3.7065)-((5.042/self.RE)*np.log10(((self.abs_roughness/self.ID)**1.1098)/2.8257+(7.149/self.RE)**0.8981))))**2)*4 * u.meter / u.meter
        return self.fric_factor
    
    def calculate_pressure_drop(self):
        try:
            self.pressure_drop = dict()
            self.pressure_drop['laminar'] = ((self.fric_factor.get('laminar', 0) * self.length * self.rho * self.vel**2)/(self.ID * 2)).to('bar')
            self.pressure_drop['churchill'] = ((self.fric_factor.get('churchill', 0) * self.length * self.rho * self.vel**2)/(self.ID * 2)).to('bar')
            self.pressure_drop['chen'] = ((self.fric_factor.get('chen', 0) * self.length * self.rho * self.vel**2)/(self.ID * 2)).to('bar')
            return self.pressure_drop
        except AttributeError as e:
            print('Please calculate the fric factor first with calculate_fric_factor() method!')
            print(e)
            return None

# OD = 0.25 * u.inch
# length = 4 * u.meter 
# sch = 0.049 * u.inch
# abs_roughness = 0.0015 * u.milimeter
# flow_rate = (4/1000) * u.meter**3 / u.minute # from LPM to m3/min 
# visc = (0.0128/1000) * u.kg / u.meter / u.second # from cp to kg/(m.s)
# rho = 2.542 * u.kg / u.meter**3

# tube_dp = dp_friction(OD, length, sch, abs_roughness, flow_rate, visc, rho)
# tube_dp.calculate_fric_factor()
# pressure_drop = tube_dp.calculate_pressure_drop()['churchill']