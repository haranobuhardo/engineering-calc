export function convertLength(length: number, unit: string): number {
  // convert length to base unit, mm
  switch (unit) {
    case "in":
      length = length * 25.4
      break
    case "ft":
      length = length / 12
      break
    case "mm":
      length = length * 1
      break
    case "m":
      length = length / 1000
  }
    return length
}

export function convertFlowRate(flowRate: number, unit: string): number {
  // convert flow rate to base unit, lpm
  switch (unit) {
    case "lpm":
      flowRate = flowRate * 1
      break
    case "lph":
      flowRate = flowRate * 60
      break
    case "bpd":
      flowRate = flowRate * 0.1104078437
  }
    return flowRate
}

export function convertViscosity(viscosity: number, unit: string): number {
  // convert viscosity to base unit, kg/m-s
  switch (unit) {
    case "cps":
      viscosity = viscosity / 1000
      break
    case "kg/m-s":
      viscosity = viscosity * 1
  }
    return viscosity
}

export function convertDensity(density: number, unit: string): number {
  // convert viscosity to base unit, kg/m3
  switch (unit) {
    case "lbs/ft3":
      density = density / 16.0185
      break
    case "kg/m3":
      density = density * 1
  }
    return density
}