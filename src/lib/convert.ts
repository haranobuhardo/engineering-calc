export function convertLength(length: number, unit: string): number {
    // convert length to base unit, mm
    switch (unit) {
        case "in":
            return length * 25.4;
        case "ft":
            return length * 304.8;
        case "m":
            return length * 1000;
        case "mm":
        default:
            return length * 1;
    }
}

export function convertFlowRate(flowRate: number, unit: string): number {
    // convert flow rate to base unit, lpm
    switch (unit) {
        case "lpm":
            return flowRate * 1;
        case "lph":
            return flowRate / 60;
        case "bpd":
            return flowRate * 0.1104078437;
        default:
            return flowRate;
    }
}

export function convertViscosity(viscosity: number, unit: string): number {
    // convert viscosity to base unit, kg/m-s
    switch (unit) {
        case "cps":
            return viscosity / 1000;
        case "kg/m-s":
        default:
            return viscosity * 1;
    }
}

export function convertDensity(density: number, unit: string): number {
    // convert density to base unit, kg/m3
    switch (unit) {
        case "lbs/ft3":
            return density * 16.018463;
        case "kg/m3":
        default:
            return density * 1;
    }
}

export function convertModulusOfElasticity(modulus: number, unit: string): number {
    // convert modulus of elasticity to base unit, psi
    switch (unit) {
        case "Pa":
            return modulus * 0.000145038;
        case "kPa":
            return modulus * 0.145038;
        case "MPa":
            return modulus * 145.038;
        case "GPa":
            return modulus * 145038;
        case "psi":
        default:
            return modulus * 1;
    }
}

export function convertSpecificWeight(weight: number, unit: string): number {
    // convert specific weight to base unit, lb/in³
    switch (unit) {
        case "N/m3":
            return weight * 0.000003684;
        case "kN/m3":
            return weight * 0.003684;
        case "lb/in3":
        default:
            return weight * 1;
    }
}

export function convertVelocity(velocity: number, unit: string): number {
    // convert velocity to base unit, m/s
    switch (unit) {
        case "ft/s":
            return velocity * 0.3048;
        case "km/h":
            return velocity * 0.277778;
        case "mph":
            return velocity * 0.44704;
        case "m/s":
        default:
            return velocity * 1;
    }
}

export function convertVolume(volume: number, unit: string): number {
    // convert volume to base unit, cc (cm3)
    switch (unit) {
        case "cc":
        case "ml":
        case "cm3":
            return volume * 1;
        case "m3":
            return volume * 1000000;
        case "liter":
        case "L":
            return volume * 1000;
        case "in3":
            return volume * 16.387064;
        case "ft3":
            return volume * 28316.846592;
        default:
            return volume;
    }
}

export function convertPressure(pressure: number, unit: string): number {
    // convert pressure to base unit, psia
    switch (unit) {
        case "psia":
            return pressure * 1;
        case "psig":
            return pressure + 14.7;
        case "bar":
            return pressure * 14.503774;
        case "atm":
            return pressure * 14.695949;
        case "kPa":
            return pressure * 0.145038;
        case "Pa":
            return pressure * 0.000145038;
        default:
            return pressure;
    }
}



export const lengthUnits = [
    { id: 'in', text: 'in' },
    { id: 'ft', text: 'ft' },
    { id: 'mm', text: 'mm' },
    { id: 'm', text: 'm' }
];

export const volumeUnits = [
    { id: 'cc', text: 'cc' },
    { id: 'ml', text: 'ml' },
    { id: 'L', text: 'L' },
    { id: 'm3', text: 'm3' },
    { id: 'in3', text: 'in3' },
    { id: 'ft3', text: 'ft3' },
    { id: 'cm3', text: 'cm3' },
    { id: "liter", text: "liter" }
];

export const flowRateUnits = [
    { id: 'lpm', text: 'NLPM' },
    { id: 'lph', text: 'NLPH' },
    { id: 'bpd', text: 'BPD' }
];

export const pressureUnits = [
    { id: 'kPa', text: 'kPa' },
    { id: 'Pa', text: 'Pa' },
    { id: 'bar', text: 'bar' },
    { id: 'atm', text: 'atm' },
    { id: 'psia', text: 'psia' },
    { id: 'psig', text: 'psig' }
];

export const viscosityUnits = [
    { id: 'cps', text: 'cP' },
    { id: 'kg/m-s', text: 'kg/m-s' }
];

export const densityUnits = [
    { id: 'lbs/ft3', text: 'lbs/ft3' },
    { id: 'kg/m3', text: 'kg/m3' }
];

export const velocityUnits = [
    { id: 'm/s', text: 'm/s' },
    { id: 'ft/s', text: 'ft/s' },
    { id: 'km/h', text: 'km/h' },
    { id: 'mph', text: 'mph' }
];

export const modulusOfElasticityUnits = [
    { id: 'psi', text: 'psi' },
    { id: 'Pa', text: 'Pa' },
    { id: 'kPa', text: 'kPa' },
    { id: 'MPa', text: 'MPa' },
    { id: 'GPa', text: 'GPa' }
];

export const specificWeightUnits = [
    { id: 'lb/in3', text: 'lb/in³' },
    { id: 'N/m3', text: 'N/m³' },
    { id: 'kN/m3', text: 'kN/m³' }
];

export function convertTemperature(temperature: number, unit: string): number {
    // convert temperature to base unit, Kelvin
    switch (unit) {
        case "C":
        case "°C":
            return temperature + 273.15;
        case "F":
        case "°F":
            return (temperature - 32) * 5/9 + 273.15;
        case "K":
        default:
            return temperature * 1;
    }
}

export function convertThermalConductivity(k: number, unit: string): number {
    // convert thermal conductivity to base unit, W/(m·K)
    switch (unit) {
        case "BTU/(hr·ft·°F)":
            return k * 1.730735;
        case "W/(m·K)":
        default:
            return k * 1;
    }
}

export function convertSpecificHeat(c: number, unit: string): number {
    // convert specific heat capacity to base unit, J/(kg·K)
    switch (unit) {
        case "BTU/(lb·°F)":
            return c * 4186.8;
        case "J/(kg·K)":
        default:
            return c * 1;
    }
}

export const temperatureUnits = [
    { id: 'K', text: 'K' },
    { id: 'C', text: '°C' },
    { id: 'F', text: '°F' }
];

export const thermalConductivityUnits = [
    { id: 'W/(m·K)', text: 'W/(m·K)' },
    { id: 'BTU/(hr·ft·°F)', text: 'BTU/(hr·ft·°F)' }
];

export const specificHeatUnits = [
    { id: 'J/(kg·K)', text: 'J/(kg·K)' },
    { id: 'BTU/(lb·°F)', text: 'BTU/(lb·°F)' }
];
