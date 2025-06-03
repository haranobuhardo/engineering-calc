<script lang="ts">
  import {siteConfig} from '$lib/nav';
  import {convertLength, convertFlowRate, convertViscosity, convertDensity} from './convert'

  interface UnitOption {
    value: string,
    text: string,
    scale?: number,
  }
  
  let outsideDiameterValue = $state(0.25);
  let outsideDiameterUnit = $state("in");
  let lengthValue = $state(1);
  let lengthUnit = $state("m");
  let wallThicknessValue = $state(0.035);
  let wallThicknessUnit = $state("in");
  let absRoughnessValue = $state(0.0015);
  let absRoughnessUnit = $state("mm");
  let flowRateValue = $state(25);
  let flowRateUnit = $state("lpm");
  let dynamicViscValue = $state(0.03);
  let dynamicViscUnit = $state("cps");
  let densityValue = $state(0.9);
  let densityUnit = $state("kg/m3");

  let reynoldsNumber = $state(0);

  let lengthUnits: UnitOption[] = [
    {value: "in", text: "in"},
    {value: "ft", text: "ft"},
    {value: "mm", text: "mm"},
    {value: "m", text: "m"},
  ]

  let flowRateUnits: UnitOption[] = [
    {value: "lpm", text: "lpm"},
    {value: "lph", text: "lph"},
    {value: "bpd", text: "bpd"},
  ]

  let dynamicViscUnits: UnitOption[] = [
    {value: "cps", text: "cP"},
    {value: "kg/m-s", text: "kg/m-s"},
  ]

  let densityUnits: UnitOption[] = [
    {value: "lbs/ft3", text: "lbs/ft3"},
    {value: "kg/m3", text: "kg/m3"},
  ]

  function calcID(outsideDiameter: number, wallThickness: number): number{
    return outsideDiameter - (2*wallThickness)
  }

  function calcVelocity(insideDiameter: number, flowRate: number): number{
    // insideDiameter: mm
    // flowRate: LPM (liter per minute)
    let area = 1/4 * 3.14 * (insideDiameter/1000)**2 // m**2
    let flowRateConv = flowRate / 1000 / 60 // m**3/second
    return flowRateConv / area // in m/s
  }

  function calcRelRoughness(absRoughness: number, insideDiameter: number): number {
    // absRoughness: meter (m)
    // insideDiameter: meter (m)
    return absRoughness / insideDiameter
  }

  function calcReynoldsNumber(insideDiameter: number, density: number, velocity: number, viscosity: number): number {
    // insideDiameter: meter (m)
    // density: kg/m3
    // velocity: m/s
    // viscosity: kg/(m.s)
    return insideDiameter * density * velocity / viscosity
  }

  function calculatePressureDrop(){
    let convertedOD = convertLength(outsideDiameterValue, outsideDiameterUnit)
    let convertedThickness = convertLength(wallThicknessValue, wallThicknessUnit)
    let convertedFlowRate = convertFlowRate(flowRateValue, flowRateUnit)
    let convertedAbsRoughness = convertLength(absRoughnessValue, absRoughnessUnit)
    let convertedViscosity = convertViscosity(dynamicViscValue, dynamicViscUnit)
    let convertedDensity = convertDensity(densityValue, densityUnit)
    
    let insideDiameter: number = calcID(convertedOD, convertedThickness) // in mm
    let velocity: number = calcVelocity(insideDiameter, convertedFlowRate) // in m/s
    let relativeRoughness: number = calcRelRoughness(convertedAbsRoughness, insideDiameter)

    reynoldsNumber = calcReynoldsNumber(insideDiameter/1000, convertedDensity, velocity, convertedViscosity)

    console.log(insideDiameter)
    console.log(velocity)
    console.log(relativeRoughness)
    console.log(reynoldsNumber)
  }

</script>

<svelte:head>
  <title>{siteConfig.title} - Pressure Drop</title>
  <meta name={siteConfig.description} content={siteConfig.description} />
</svelte:head>

<div id="calc" class='flex flex-col justify-center items-center space-y-4 my-4 w-full'>
  <div class='flex flex-col justify-center items-center space-y-2 w-3/4 sm:w-1/2'>
    <article class='prose text-center mb-4'><h1>Pressure Drop Calculator</h1></article>
    <!-- Input section -->
    <!-- Outside Diameter (OD) -->
    <fieldset class="fieldset w-full">
      <legend class="fieldset-legend">Outside Diameter (OD)</legend>
      <div class="flex w-full space-x-1">
        <input type="number" class="w-64 flex-auto input w-full" placeholder="Tube or pipe outside diameter" bind:value={outsideDiameterValue}/>
        <select class="w-16 px-2 sm:w-32 flex-auto select" bind:value={outsideDiameterUnit}>
          {#each lengthUnits as lengthUnit}
            <option value={lengthUnit.value}>{lengthUnit.text}</option>
          {/each}
        </select>
      </div>
    </fieldset>
    <!-- Length (l) -->
    <fieldset class="fieldset w-full">
      <legend class="fieldset-legend">Length (l)</legend>
      <div class="flex w-full space-x-1">
        <input type="number" class="w-64 flex-auto input w-full" placeholder="Tube or pipe length" bind:value={lengthValue}/>
        <select class="w-16 px-2 sm:w-32 flex-auto select" bind:value={lengthUnit}>
          {#each lengthUnits as lengthUnit}
            <option value={lengthUnit.value}>{lengthUnit.text}</option>
          {/each}
        </select>
      </div>
    </fieldset>
    <!-- Wall Thickness (sch) -->
    <fieldset class="fieldset w-full">
      <legend class="fieldset-legend">Wall Thickness</legend>
      <div class="flex w-full space-x-1">
        <input type="number" class="w-64 flex-auto input w-full" placeholder="Tube or pipe wall thickness" bind:value={wallThicknessValue}/>
        <select class="w-16 px-2 sm:w-32 flex-auto select" bind:value={wallThicknessUnit}>
          {#each lengthUnits as lengthUnit}
            <option value={lengthUnit.value}>{lengthUnit.text}</option>
          {/each}
        </select>
      </div>
    </fieldset>
    <!-- Absolute Roughness (k) -->
    <fieldset class="fieldset w-full">
      <legend class="fieldset-legend">Absolute Roughness (k)</legend>
      <div class="flex w-full space-x-1">
        <input type="number" class="w-64 flex-auto input w-full" placeholder="Tube or pipe abs roughness" bind:value={absRoughnessValue}/>
        <select class="w-16 px-2 sm:w-32 flex-auto select" bind:value={absRoughnessUnit}>
          {#each lengthUnits as lengthUnit}
            <option value={lengthUnit.value}>{lengthUnit.text}</option>
          {/each}
        </select>
      </div>
    </fieldset>
    <!-- Flow Rate (Q) -->
    <fieldset class="fieldset w-full">
      <legend class="fieldset-legend">Flow Rate (Q)</legend>
      <div class="flex w-full space-x-1">
        <input type="number" class="w-64 flex-auto input w-full" placeholder="Fluid's flow rate" bind:value={flowRateValue}/>
        <select class="w-16 px-2 sm:w-32 flex-auto select" bind:value={flowRateUnit}>
          {#each flowRateUnits as flowRateUnit}
            <option value={flowRateUnit.value}>{flowRateUnit.text}</option>
          {/each}
        </select>
      </div>
    </fieldset>
    <!-- Viscosity (mu) -->
    <fieldset class="fieldset w-full">
      <legend class="fieldset-legend">Dynamic Viscosity (μ)</legend>
      <div class="flex w-full space-x-1">
        <input type="number" class="w-64 flex-auto input w-full" placeholder="Fluid's viscosity" bind:value={dynamicViscValue}/>
        <select class="w-16 px-2 sm:w-32 flex-auto select" bind:value={dynamicViscUnit}>
          {#each dynamicViscUnits as dynamicViscUnit}
            <option value={dynamicViscUnit.value}>{dynamicViscUnit.text}</option>
          {/each}
        </select>
      </div>
    </fieldset>
    <!-- Density (rho) -->
    <fieldset class="fieldset w-full">
      <legend class="fieldset-legend">Density (ρ)</legend>
      <div class="flex w-full space-x-1">
        <input type="number" class="w-64 flex-auto input w-full" placeholder="Fluid's density" bind:value={densityValue}/>
        <select class="w-16 px-2 sm:w-32 flex-auto select" bind:value={densityUnit}>
          {#each densityUnits as densityUnit}
            <option value={densityUnit.value}>{densityUnit.text}</option>
          {/each}
        </select>
      </div>
    </fieldset>
    <button class="btn w-full mt-2" onclick={calculatePressureDrop}>
      Calculate
    </button>
    {#if reynoldsNumber > 0}
    <div class='flex flex-col justify-center items-center space-y-1 mt-4 w-full'>
      <article class='prose text-center mb-2'><h2>Result:</h2></article>
      <div>Reynold number: {reynoldsNumber.toFixed(3)}</div>
      <div>Flow type: <b>{reynoldsNumber > 4000 ? "Turbulent" : "Laminar"}</b></div>
    </div>
    {/if}
  </div>
</div>