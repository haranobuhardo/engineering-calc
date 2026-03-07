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
    { id: 'psia', text: 'psia' },
    { id: 'psig', text: 'psig' },
    { id: 'bar', text: 'bar' },
    { id: 'atm', text: 'atm' }
];

export const viscosityUnits = [
    { id: 'cps', text: 'cP' },
    { id: 'kg/m-s', text: 'kg/m-s' }
];

export const densityUnits = [
    { id: 'lbs/ft3', text: 'lbs/ft3' },
    { id: 'kg/m3', text: 'kg/m3' }
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
