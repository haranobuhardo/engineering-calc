from weebz_calc.calc_app import functions as f

from flask import render_template, request, Blueprint
import math
import numpy as np
import unyt as u
import matplotlib.pyplot as plt

import os
import io
import base64

from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from matplotlib.figure import Figure

from thermo import ChemicalConstantsPackage, CEOSGas, CEOSLiquid, PRMIX, FlashVL, viscosity, Mixture, vapor_pressure
from thermo.interaction_parameters import IPDB
from thermo.utils import TDependentProperty

calc = Blueprint('calc', __name__)

class natural_gas():
    def __init__(self, temp, pressure, gas_comp):
        self.temp = temp * u.celcius
        self.pressure = ((1) * u.atm) + (pressure * u.bar)
        self.temperature_value = float(self.temp.in_units('Kelvin').value)
        self.pressure_value = float(self.pressure.in_units('Pa').value)
        self.gas_comp = gas_comp
        self.hc_comp = {k:v for k, v in self.gas_comp.items() if not k in ['Water', 'H2O']}
        self.gas_name = list(self.gas_comp.keys())
        self.hc_name = list(self.hc_comp.keys())

        self.VF = 0
        self.rho_mass = 0
        self.SG_gas = 0
        self.MW = 0
        self.bulk_visc = 0
        self.dew_point = 0
        self.hc_dew_point = 0

        self.critical_pressure = 0
        self.critical_temp = 0
    
    def dew_point_calculate_(self):
        try:
            constants, properties = ChemicalConstantsPackage.from_IDs(self.gas_name)
            kijs = IPDB.get_ip_asymmetric_matrix('ChemSep PR', constants.CASs, 'kij')

            eos_kwargs = {'Pcs': constants.Pcs, 'Tcs': constants.Tcs, 'omegas': constants.omegas, 'kijs': kijs}
            gas = CEOSGas(PRMIX, eos_kwargs=eos_kwargs, HeatCapacityGases=properties.HeatCapacityGases)
            liquid = CEOSLiquid(PRMIX, eos_kwargs=eos_kwargs, HeatCapacityGases=properties.HeatCapacityGases)
            flasher = FlashVL(constants, properties, liquid=liquid, gas=gas)
            zs = list([i[0] for i in self.gas_comp.values()])
            print('zs', zs)
            if (sum(zs) <= 0): return # safety auto exit when zs less or equal to 0
            normalized_zs = list([i[0]/sum(zs) for i in self.gas_comp.values()])
            print('norm zs', normalized_zs)
            PT = flasher.flash(T=self.temperature_value, P=self.pressure_value, zs=normalized_zs)
            self.VF = PT.VF
            self.rho_mass = PT.rho_mass() * u.kg / u.meter**3 #kg/m^3
            self.SG_gas = PT.SG_gas()
            self.MW = PT.MW()
            self.bulk_visc = PT.mu() * u.kg/(u.meter * u.second)  #cP
            self.critical_pressure = PT.Pmc() * u.Pa
            self.critical_temperature = PT.Tmc() * u.kelvin

            dew_point = flasher.flash(P=float(self.pressure.in_units('Pa').value), VF=1, zs=normalized_zs).T *u.kelvin

            self.dew_point = dew_point.to('celcius')
        
        except Exception as e:
            print('Error', e)

        except UnboundLocalError as e:
            print('Error', e)

    def hc_dew_point_calculate_(self):
        try:
            constants, properties = ChemicalConstantsPackage.from_IDs(self.hc_name)
            kijs = IPDB.get_ip_asymmetric_matrix('ChemSep PR', constants.CASs, 'kij')

            eos_kwargs = {'Pcs': constants.Pcs, 'Tcs': constants.Tcs, 'omegas': constants.omegas, 'kijs': kijs}
            gas = CEOSGas(PRMIX, eos_kwargs=eos_kwargs, HeatCapacityGases=properties.HeatCapacityGases)
            liquid = CEOSLiquid(PRMIX, eos_kwargs=eos_kwargs, HeatCapacityGases=properties.HeatCapacityGases)
            flasher = FlashVL(constants, properties, liquid=liquid, gas=gas)
            zs = list([i[0] for i in self.hc_comp.values()])

            if (sum(zs) <= 0): return

            normalized_zs = list([i[0]/sum(zs) for i in self.hc_comp.values()])

            dew_point = flasher.flash(P=float(self.pressure.in_units('Pa').value), VF=1, zs=normalized_zs).T *u.kelvin

            self.hc_dew_point = dew_point.to('celcius')
        
        except Exception as e:
            print('Error', e)

        except UnboundLocalError as e:
            print('Error', e)
    
    def create_chart(self):
        # define flasher 

        constants, properties = ChemicalConstantsPackage.from_IDs(self.hc_name)
        kijs = IPDB.get_ip_asymmetric_matrix('ChemSep PR', constants.CASs, 'kij')

        eos_kwargs = {'Pcs': constants.Pcs, 'Tcs': constants.Tcs, 'omegas': constants.omegas, 'kijs': kijs}
        gas = CEOSGas(PRMIX, eos_kwargs=eos_kwargs, HeatCapacityGases=properties.HeatCapacityGases)
        liquid = CEOSLiquid(PRMIX, eos_kwargs=eos_kwargs, HeatCapacityGases=properties.HeatCapacityGases)
        flasher = FlashVL(constants, properties, liquid=liquid, gas=gas)
        zs = list([i[0] for i in self.gas_comp.values()])

        if (sum(zs) <= 0): return

        normalized_zs = list([i[0]/sum(zs) for i in self.hc_comp.values()])

        # define pressure list for test
        pressure_min = 1  # in psia
        pressure_max = 1000 # in psia
        n_step = 50

        pressure_list = (np.linspace(pressure_min, pressure_max, n_step) * u.psi)

        dew_point_list = []

        # creating list for dew point list
        for x in pressure_list.to('Pa'):
            print(x)
            try:
                dew_point = flasher.flash(P=float(x.in_units('Pa').value), VF=1, zs=normalized_zs).T *u.kelvin
            except:
                dew_point = None
            
            if dew_point == None:
                dew_point_list.append(None)
            else:
                dew_point_list.append(float(dew_point.to('celcius').value))

        # for x in pressure_list.to('Pa'):
        #     dew_point = flasher.flash(P=float(x.in_units('Pa').value), VF=1, zs=normalized_zs).T *u.kelvin
        #     dew_point_list.append(float(dew_point.to('celcius').value))
        

        # creating list for bubble point list
        bubble_point_list = []

        for x in pressure_list.to('Pa'):
            try:
                bubble_point = flasher.flash(P=float(x.in_units('Pa').value), VF=0, zs=normalized_zs).T *u.kelvin
            except:
                bubble_point = None
                
            if bubble_point == None:
                bubble_point_list.append(None)
            else:
                bubble_point_list.append(float(bubble_point.to('celcius').value))

        # print(dew_point_list)
        # print(bubble_point_list)

        fig = Figure(figsize=(10, 6))
        axis = fig.add_subplot(111)
        axis.set_title('Phase Diagram')
        axis.set_xlabel('Temperature (°C)')
        axis.set_ylabel('Pressure (psi)')
        axis.plot(float(self.critical_temperature.in_units('celcius').value), float(self.critical_pressure.in_units('psi').value), '-rx', label='Critical Point')
        axis.plot(dew_point_list, pressure_list.value,'-o', label='Dew Point', ms=3)
        axis.plot(bubble_point_list, pressure_list.value,'-yD', label='Bubble Point', ms=3)
        axis.plot(self.temp.in_units('celcius').value, self.pressure.in_units('psi').value, '-bs', label='Current Condition', ms=3)
        axis.axhline(y=self.pressure.in_units('psi').value, color='blue', linestyle=':', alpha=0.3)
        axis.grid()
        axis.legend()

        # Convert plot to PNG image
        pngImage = io.BytesIO()
        FigureCanvas(fig).print_png(pngImage)
        
        # Encode PNG image to base64 string
        pngImageB64String = "data:image/png;base64,"
        pngImageB64String += base64.b64encode(pngImage.getvalue()).decode('utf8')

        # print(pngImageB64String)
        return pngImageB64String
        # print(os.getcwd() + '/static/images/new_plot.png')
        # return adp_list
        

class acid_gas():
    def __init__(self, pressure, H2O_content, temp=(25*u.celcius), SO2_content=0, O2_content=0, SO3_content=0):
        
        self.temp = temp.to('celcius')
        self.pressure = pressure.to('atm')
        self.H2O_content = H2O_content
        self.SO2_content = SO2_content
        self.O2_content = O2_content
        self.SO3_content = SO3_content
        self.p_H2O = H2O_content * self.pressure
        self.p_SO2 = SO2_content * self.pressure
        self.p_O2 = O2_content * self.pressure
        self.p_SO3 = SO3_content * self.pressure
        print(self.pressure)
    
    def SO3_conversion(self, inplace=False):
        pressure = 1 * u.atm
        temp = (1273 * u.kelvin).to('celcius')

        if (self.p_SO2.value != 0 and self.p_O2.value != 0):
            Kp = 10**((0.4342*(31.752231-0.040591095*temp.value))/(1+0.0037782493*temp.value))
            SO3_content = Kp*(self.SO2_content)*(self.O2_content**0.5)/(1+Kp*(self.O2_content**0.5))
            if inplace == True: self.SO3_content = SO3_content; self.p_SO3 = SO3_content * self.pressure
            return SO3_content
        else:
            print('SO2 or O2 content can\'t be zero! Returning None...')
            return (0 * u.celcius)
    
    def acid_dew_point(self, pressure=None):
        if pressure == None:
            pressure = self.pressure
            self.p_H2O = self.H2O_content * self.pressure
            self.p_SO3 = self.SO3_content * self.pressure
        else:
            pressure = pressure * u.atm
            self.p_H2O = self.H2O_content * pressure
            self.p_SO3 = self.SO3_content * pressure

        # print('partial pressure H2O', self.p_H2O)
        # print('partial pressure SO3', self.p_SO3)

        if (self.p_SO3.value > 0 and self.p_H2O.value > 0):  
            adp_verhoff = (1/(0.002276-0.00002943*math.log(self.p_H2O.value * 760)
                               -0.0000858*math.log(self.p_SO3.value * 760)
                               +0.0000062*math.log(self.p_H2O.value * 760)*math.log(self.p_SO3.value * 760))
                          ) * u.kelvin
            # print('adp_verhoff', adp_verhoff)
            adp_okkes = (205.25+27.06*math.log(self.p_H2O.value, 10)+10.86*math.log(self.p_SO3.value, 10) 
                        +1.06*((math.log(self.p_SO3.value, 10)+8)**2.19)
                        ) * u.celcius
            # print('adp_okkes', adp_okkes)
            adp_zarenezhad = (150+11.664*math.log(self.p_SO3.value * 760)
                              +8.1328*math.log(self.p_H2O.value * 760)
                              -0.383226*math.log(self.p_SO3.value * 760)*math.log(self.p_H2O.value * 760)
                          ) * u.celcius
            # print('adp_zarenezhad', adp_zarenezhad)
            result = {'verhoff': adp_verhoff.to('celcius'),
                     'okkes': adp_okkes.to('celcius'),
                     'zarenezhad': adp_zarenezhad.to('celcius') }
            return result
        else:
            print('H2O or SO3 content can\'t be zero! Returning None...')
            return (
                {'verhoff': 0 * u.celcius,
                'okkes': 0 * u.celcius,
                'zarenezhad': 0 * u.celcius}
            )
    
    def water_dew_point(self, pressure=None):
        if pressure == None:
            pressure = self.pressure
            self.p_H2O = self.H2O_content * self.pressure
        else:
            pressure = pressure * u.atm
            self.p_H2O = self.H2O_content * pressure

        # print(self.p_H2O.value)
        if (self.p_H2O.value != 0):
            wdp = ((5038.13)/(20.1424-math.log(self.p_H2O.value * 760))) * u.kelvin
            return wdp.to('celcius')
        else:
            print('H2O content can\'t be zero! Returning None...')
            return (0 * u.celcius)

    def create_chart(self, constant):
        print('pressure_list entered')
        min_pressure = 0.001 if self.pressure.value - 50 <= 0 else self.pressure.value - 50
        max_pressure = self.pressure.value + 50
        pressure_list = np.linspace(min_pressure, max_pressure, 200)
        # pressure_list = [i for i in range(min_pressure, max_pressure)]
        adp_list = []
        wdp_list = []
        # print(pressure_list)
        print('pressure_list generated')
        for i in pressure_list:
            try:
                # print(i)
                # print(self.acid_dew_point(i).get(constant, 0).to('celcius').value)
                adp_list.append(self.acid_dew_point(i).get(constant, 0).to('celcius').value)
            except:
                adp_list.append(0)
        
        for i in pressure_list:
            try:
                wdp_list.append(self.water_dew_point(i).to('celcius').value)
            except:
                wdp_list.append(0)
        # print(np.array(adp_list))

        fig = Figure(figsize=(10, 6))
        axis = fig.add_subplot(111)
        axis.set_title('Dew Point Curve')
        axis.set_xlabel('Pressure (atm)')
        axis.set_ylabel('Dew Temperature (°C)')
        axis.grid()
        axis.plot(pressure_list, adp_list, 'r', label='Acid Dew Point')
        axis.plot(pressure_list, wdp_list, 'b', label='Water Dew Point')
        axis.legend()

        # Convert plot to PNG image
        pngImage = io.BytesIO()
        FigureCanvas(fig).print_png(pngImage)
        
        # Encode PNG image to base64 string
        pngImageB64String = "data:image/png;base64,"
        pngImageB64String += base64.b64encode(pngImage.getvalue()).decode('utf8')

        # print(pngImageB64String)
        return pngImageB64String
        # print(os.getcwd() + '/static/images/new_plot.png')
        # return adp_list

@calc.context_processor
def utility_functions():
    def print_in_console(message):
        print(str(message))

    return dict(mdebug=print_in_console)

@calc.route('/', methods=['GET', 'POST'])
def acid_gas_analysis():
    pressure_units_dict = {'bara':1, 'psia':1/14.504, 'atm':1.01325} # constant to bar
    concentration_units_dict =  {'%vol':1e-2, 'ppmv':1e-6} # constant to fraction

    H2O_content = 0.0
    O2_content = 0.0
    SO2_content = 0.0
    SO3_content = 0.0
    pressure = 0.0

    pressure_unit = 'bara'
    H2O_unit = '%vol'
    SO2_unit = 'ppmv'
    O2_unit = '%vol'
    SO3_unit = 'ppmv'
    
    if request.method == 'POST':
        try:
            SO3_Convert = bool(int(request.form['SO3_convert']))
            if (SO3_Convert):
                pressure_unit = str(request.form['pressure_unit'])
                H2O_unit = str(request.form['H2O_unit'])
                O2_unit = str(request.form['O2_unit'])
                SO2_unit = str(request.form['SO2_unit'])
                SO3_unit = str(request.form['SO3_unit'])
                H2O_content = float(request.form['H2O_content']) * concentration_units_dict.get(H2O_unit, 1)
                O2_content = float(request.form['O2_content']) * concentration_units_dict.get(O2_unit, 1)
                SO2_content = float(request.form['SO2_content']) * concentration_units_dict.get(SO2_unit, 1)
                pressure = float(request.form['pressure']) * pressure_units_dict.get(pressure_unit, 1) * u.bar
                sample1 = acid_gas(pressure, H2O_content = H2O_content, O2_content = O2_content, SO2_content = SO2_content)
                sample1.SO3_conversion(inplace=True)
                SO3_content = sample1.SO3_content
                return render_template('index.html', 
                                        H2O_content = H2O_content / concentration_units_dict.get(H2O_unit, 1), 
                                        O2_content = O2_content / concentration_units_dict.get(O2_unit, 1), 
                                        SO2_content = SO2_content / concentration_units_dict.get(SO2_unit, 1), 
                                        SO3_content = SO3_content / concentration_units_dict.get(SO3_unit, 1), 
                                        pressure = pressure.value / pressure_units_dict.get(pressure_unit, 1), ##########
                                        SO3_convert_status = SO3_Convert,
                                        pressure_units = [x for x in pressure_units_dict.keys()],
                                        concentration_units = [x for x in concentration_units_dict.keys()],
                                        pressure_unit = pressure_unit, H2O_unit = H2O_unit, SO2_unit = SO2_unit, O2_unit = O2_unit, SO3_unit = SO3_unit,
                                        SO3='{:.2f} ppmv'.format(SO3_content*1e6),
                                        wdp='{:.2f}'.format(sample1.water_dew_point().to('celcius').value),
                                        adp='{:.2f}'.format(sample1.acid_dew_point().get('verhoff', 0).to('celcius').value),
                                        chart=sample1.create_chart('verhoff'))
            elif (SO3_Convert == False):
                pressure_unit = str(request.form['pressure_unit'])
                H2O_unit = str(request.form['H2O_unit'])
                O2_unit = str(request.form['O2_unit'])
                SO2_unit = str(request.form['SO2_unit'])
                SO3_unit = str(request.form['SO3_unit'])
                H2O_content = float(request.form['H2O_content']) * concentration_units_dict.get(H2O_unit, 1)
                SO3_content = float(request.form['SO3_content']) * concentration_units_dict.get(SO3_unit, 1)
                pressure = float(request.form['pressure']) * pressure_units_dict.get(pressure_unit, 1) * u.bar
                sample1 = acid_gas(pressure, H2O_content = H2O_content, SO3_content = SO3_content)
                # [print(x) for x in concentration_units_dict.keys() if x == SO3_unit]
                    # print(SO3_unit, concentration_units_dict.get(SO3_unit, 1))
                return render_template('index.html', 
                                        H2O_content = H2O_content / concentration_units_dict.get(H2O_unit, 1), 
                                        O2_content = O2_content / concentration_units_dict.get(O2_unit, 1), 
                                        SO2_content = SO2_content / concentration_units_dict.get(SO2_unit, 1), 
                                        SO3_content = SO3_content / concentration_units_dict.get(SO3_unit, 1), 
                                        pressure = pressure.value / pressure_units_dict.get(pressure_unit, 1), ##########
                                        SO3_convert_status = SO3_Convert,
                                        pressure_units = [x for x in pressure_units_dict.keys()],
                                        concentration_units = [x for x in concentration_units_dict.keys()],
                                        pressure_unit = pressure_unit, H2O_unit = H2O_unit, SO2_unit = SO2_unit, O2_unit = O2_unit, SO3_unit = SO3_unit,
                                        SO3='{:.2f} ppmv'.format(SO3_content*1e6),
                                        wdp='{:.2f}'.format(sample1.water_dew_point().to('celcius').value),
                                        adp='{:.2f}'.format(sample1.acid_dew_point().get('verhoff', 0).to('celcius').value),
                                        chart=sample1.create_chart('verhoff'))
        except Exception as e:
            return '<h1>Bad Request : {}</h1>'.format(e)
    else:
        return render_template('index.html', 
                                H2O_content = H2O_content / concentration_units_dict.get(H2O_unit, 1), ##########
                                O2_content = O2_content / concentration_units_dict.get(O2_unit, 1), 
                                SO2_content = SO2_content / concentration_units_dict.get(SO2_unit, 1), 
                                SO3_content = SO3_content / concentration_units_dict.get(SO3_unit, 1), 
                                pressure = pressure / pressure_units_dict.get(pressure_unit, 1), ##########
                                SO3_convert_status = False,
                                pressure_units = [x for x in pressure_units_dict.keys()],
                                concentration_units = [x for x in concentration_units_dict.keys()],
                                pressure_unit = pressure_unit, H2O_unit = H2O_unit, SO2_unit = SO2_unit, O2_unit = O2_unit, SO3_unit = SO3_unit
                                )


@calc.route('/hcdp/', methods=['GET', 'POST'])
def hydrocarbon_analysis():
    pressure_units_dict = {'barg':1, 'psig':1/14.504} # constant to bar

    # gas_comp = {
    #     'N2':[0.2769e-2], 
    #     'CO2':[4.3924e-2], 
    #     'Methane':[87.5619e-2],
    #     'Ethane':[4.4493e-2],
    #     'Propane':[2.0557e-2],
    #     'i-Butane':[0.4096e-2],
    #     'n-Butane':[0.4988e-2],
    #     'i-Pentane':[0.1436e-2],
    #     'n-Pentane':[0.0866e-2],
    #     'C6H14':[0.1213e-2],
    #     'C7H16':[0],
    #     'C8H18':[0],
    #     'Water':[0.0061e-2],
    #     'H2S':[0.0004e-2]
    # }

    gas_comp = {
        'N2':[0], 
        'CO2':[0], 
        'Methane':[0],
        'Ethane':[0],
        'Propane':[0],
        'i-Butane':[0],
        'n-Butane':[0],
        'i-Pentane':[0],
        'n-Pentane':[0],
        'C6H14':[0],
        'C7H16':[0],
        'C8H18':[0],
        'Water':[0],
        'H2S':[0]
    }


    pressure_unit = 'bara'
    pressure = 1
    temp = 25

    if request.method == 'POST':
        try:
            pressure_unit = str(request.form['pressure_unit'])
            # temp_unit = str(request.form['temp_unit'])
            for i in gas_comp.keys():
                gas_comp[i][0] = float(request.form[i]) / 100
            
            pressure = (float(request.form['pressure']) * pressure_units_dict.get(pressure_unit, 1) * u.bar).value
            temp = (float(request.form['temperature']) * u.celcius).value
            print(gas_comp)
            print(pressure)
            hcdp_sample = natural_gas(temp=temp, pressure=pressure, gas_comp=gas_comp)
            hcdp_sample.dew_point_calculate_()
            hcdp_sample.hc_dew_point_calculate_()
            results_dict = {'Hydrocarbon Dew Point': hcdp_sample.hc_dew_point,
            'Dew Point': hcdp_sample.dew_point,
            'Vapor Fraction': hcdp_sample.VF,
            'Mass Density': hcdp_sample.rho_mass,
            'Specific Gravity': hcdp_sample.SG_gas,
            'Molecular Weight': hcdp_sample.MW,
            'Bulk Viscosity': hcdp_sample.bulk_visc
                }
            
            return render_template('hcdp.html', 
                                    temperature = temp,
                                    pressure = pressure / pressure_units_dict.get(pressure_unit, 1), ##########
                                    # pressure = pressure,
                                    gas_comp = gas_comp,
                                    pressure_units = [x for x in pressure_units_dict.keys()],
                                    pressure_unit = pressure_unit,
                                    results = results_dict,
                                    chart=hcdp_sample.create_chart())
        except Exception as e:
            return '<h1>Bad Request : {}</h1>'.format(e)
    else:
        hcdp_sample = natural_gas(temp=temp, pressure=pressure, gas_comp=gas_comp)
        hcdp_sample.dew_point_calculate_()
        hcdp_sample.hc_dew_point_calculate_()
        results_dict = {'Hydrocarbon Dew Point': hcdp_sample.hc_dew_point,
        'Dew Point': hcdp_sample.dew_point,
        'Vapor Fraction': hcdp_sample.VF,
        'Mass Density': hcdp_sample.rho_mass,
        'Specific Gravity': hcdp_sample.SG_gas,
        'Molecular Weight': hcdp_sample.MW,
        'Bulk Viscosity': hcdp_sample.bulk_visc
            }
        return render_template('hcdp.html', 
                                temperature = temp,
                                pressure = pressure,
                                gas_comp = gas_comp,
                                pressure_units = [x for x in pressure_units_dict.keys()],
                                pressure_unit = pressure_unit,
                                results = results_dict)

@calc.route('/lag-time/', methods=['GET', 'POST'])
def lag_time():
    pressure_units_dict = {'bar':1, 'psi':1/14.504, 'atm':1.01325}

    # use tube_vol and tube_flow_to_velo
    flow = 0 * u.centimeter**3 / u.minute
    OD = 0 * u.inch
    thick = 0 * u.inch
    length = 0 * u.meter
    tube_sys_p = 1 * u.atm
    tube_atm_p = 1 * u.atm
    pressure_sys_unit = 'bar'
    pressure_atm_unit = 'atm'
    order_lag = 1

    tube_vol = 0 * u.centimeter**3
    lag_time = 0 * u.second
    tube_vel = 0 * u.meter / u.second

    if request.method == 'POST':
        try:
            pressure_sys_unit = str(request.form['pressure_sys_unit'])
            pressure_atm_unit = str(request.form['pressure_atm_unit'])
            tube_sys_p = (float(request.form['pressure_sys']) * pressure_units_dict.get(pressure_sys_unit, 1) * u.bar)
            tube_atm_p = (float(request.form['pressure_atm']) * pressure_units_dict.get(pressure_atm_unit, 1) * u.bar)
            OD = (float(request.form['tube_OD']) * u.inch)
            thick = (float(request.form['tube_thick']) * u.inch)
            length = (float(request.form['tube_len']) * u.meter)
            flow = (float(request.form['flow_rate']) * u.centimeter**3 / u.minute)
            order_lag = (float(request.form['order_lag']))

            tube_vol = f.tube_vol(length, OD, thick)
            lag_time = f.calc_lag_time(tube_vol, flow, tube_sys_p, tube_atm_p, order_lag)
            tube_vel = f.tube_flow_to_velo(flow, OD, thick)
            
            return render_template('lag-time.html', 
                                    pressure_sys = (tube_sys_p / pressure_units_dict.get(pressure_sys_unit, 1)).value, 
                                    pressure_atm = (tube_atm_p / pressure_units_dict.get(pressure_atm_unit, 1)).value, 
                                    pressure_units = [x for x in pressure_units_dict.keys()],
                                    pressure_sys_unit = pressure_sys_unit,
                                    pressure_atm_unit = pressure_atm_unit,
                                    tube_OD = OD.value,
                                    tube_thick = thick.value,
                                    tube_len = length.value,
                                    flow_rate = flow.value,
                                    order_lag = order_lag,
                                    tube_vol = tube_vol.to('cm**3').value,
                                    lag_time = lag_time.to('second').value,
                                    tube_vel = tube_vel.to('m/s').value
                                    )
        except Exception as e:
            return '<h1>Bad Request : {}</h1>'.format(e)
    else:
        return render_template('lag-time.html', 
                                pressure_sys = (tube_sys_p / pressure_units_dict.get(pressure_sys_unit, 1)).value, 
                                pressure_atm = (tube_atm_p / pressure_units_dict.get(pressure_atm_unit, 1)).value, 
                                pressure_units = [x for x in pressure_units_dict.keys()],
                                pressure_sys_unit = pressure_sys_unit,
                                pressure_atm_unit = pressure_atm_unit,
                                tube_OD = OD.value,
                                tube_thick = thick.value,
                                tube_len = length.value,
                                flow_rate = flow.value,
                                order_lag = order_lag,
                                tube_vol = tube_vol.to('cm**3').value,
                                lag_time = lag_time.to('second').value,
                                tube_vel = tube_vel.to('m/s').value
                                )


@calc.route('/error-percentage/', methods=['GET', 'POST'])
def error_percentage():
    measured_value = 0
    true_value = 0

    value_percent_error = 0.0

    if request.method == 'POST':
        try:
            measured_value = float(request.form['measured_value'])
            true_value = float(request.form['true_value'])

            value_percent_error = f.percent_error(measured_value, true_value)
            return render_template('error-percentage.html', 
                                    measured_value = measured_value,
                                    true_value = true_value,
                                    value_percent_error = value_percent_error
                                    )
        except Exception as e:
            return '<h1>Bad Request : {}</h1>'.format(e)
    else:
        return render_template('error-percentage.html', 
                                    measured_value = measured_value,
                                    true_value = true_value,
                                    value_percent_error = value_percent_error
                                    )
@calc.route('/analog-output-converter/', methods=['GET', 'POST'])
def analog_output_converter():
    min_read = 0
    max_read = 0
    cur_read = 0
    cur_AO = 4

    result = 0

    conv_type = 1

    if request.method == 'POST':
        conv_type = bool(int(request.form['conv_type']))
        
        try:
            if (conv_type):
                min_read = float(request.form['min_range'])
                max_read = float(request.form['max_range'])
                cur_read = float(request.form['cur_read'])
                cur_AO = float(request.form['cur_AO'])

                result = f.reading_to_analog_output(min_read, max_read, cur_read)

                return render_template('analog-output-converter.html', 
                                        conv_type_status = conv_type,
                                        min_range = min_read,
                                        max_range = max_read,
                                        cur_read = cur_read,
                                        cur_AO = cur_AO,
                                        result=result,
                                        unit='mA'
                                        )
            else:
                min_read = float(request.form['min_range'])
                max_read = float(request.form['max_range'])
                cur_AO = float(request.form['cur_AO'])

                result = f.analog_output_to_reading(min_read, max_read, cur_AO)

                return render_template('analog-output-converter.html', 
                                        conv_type_status = conv_type,
                                        min_range = min_read,
                                        max_range = max_read,
                                        cur_read = cur_read,
                                        cur_AO = cur_AO,
                                        result=result,
                                        unit='% or ppm'
                                        )
        except Exception as e:
            return '<h1>Bad Request : {}</h1>'.format(e)
    else:
        return render_template('analog-output-converter.html', 
                                conv_type_status = conv_type,
                                min_range = min_read,
                                max_range = max_read,
                                cur_read = cur_read,
                                cur_AO = cur_AO,
                                result=result,
                                unit='% or ppm'
                                )