<script lang="ts">
	import { siteConfig } from '$lib/nav';
	import { convertLength, convertFlowRate, convertViscosity, convertDensity, lengthUnits, flowRateUnits, viscosityUnits, densityUnits } from '$lib/convert';
	import katex from 'katex';
	import {
		Grid,
		Row,
		Column,
		NumberInput,
		Dropdown,
		Button,
		Tile
	} from 'carbon-components-svelte';

	let outsideDiameterValue = $state(0.25);
	let outsideDiameterUnit = $state('in');
	let lengthValue = $state(1);
	let lengthUnit = $state('m');
	let wallThicknessValue = $state(0.035);
	let wallThicknessUnit = $state('in');
	let absRoughnessValue = $state(0.0015);
	let absRoughnessUnit = $state('mm');
	let flowRateValue = $state(25);
	let flowRateUnit = $state('lpm');
	let dynamicViscValue = $state(0.03);
	let dynamicViscUnit = $state('cps');
	let densityValue = $state(0.9);
	let densityUnit = $state('kg/m3');

	let reynoldsNumber = $state(0);

	// LaTeX Calculation Steps (HTML strings)
	let stepLatex = $state('');

	function calcID(outsideDiameter: number, wallThickness: number): number {
		return outsideDiameter - 2 * wallThickness;
	}

	function calcVelocity(insideDiameter: number, flowRate: number): number {
		// insideDiameter: mm
		// flowRate: LPM (liter per minute)
		// area uses diameter in meters
		let area = (1 / 4) * 3.14 * (insideDiameter / 1000) ** 2; // m**2
		let flowRateConv = flowRate / 1000 / 60; // m**3/second
		return flowRateConv / area; // in m/s
	}

	function calcRelRoughness(absRoughness: number, insideDiameter: number): number {
		// absRoughness: meter (m)
		// insideDiameter: meter (m)
		// Wait, absRoughnessValue input is unit aware, convertedAbsRoughness depends on unit. 
		// Usually roughness k is in mm or similar small unit.
		return absRoughness / insideDiameter;
	}

	function calcReynoldsNumber(
		insideDiameter: number,
		density: number,
		velocity: number,
		viscosity: number
	): number {
		// insideDiameter: meter (m)
		// density: kg/m3
		// velocity: m/s
		// viscosity: kg/(m.s) = Pa.s = 1000 cP? 1 cP = 0.001 Pa.s
		// Input dynamicViscValue is 'cps' by default. convertViscosity converts to kg/m/s (Pa.s).
		return (insideDiameter * density * velocity) / viscosity;
	}

	function calculatePressureDrop() {
		let convertedOD = convertLength(outsideDiameterValue, outsideDiameterUnit);
		let convertedThickness = convertLength(wallThicknessValue, wallThicknessUnit);
		let convertedFlowRate = convertFlowRate(flowRateValue, flowRateUnit);
		let convertedAbsRoughness = convertLength(absRoughnessValue, absRoughnessUnit);
		let convertedViscosity = convertViscosity(dynamicViscValue, dynamicViscUnit);
		let convertedDensity = convertDensity(densityValue, densityUnit);

		let insideDiameter: number = calcID(convertedOD, convertedThickness); // in mm
		let velocity: number = calcVelocity(insideDiameter, convertedFlowRate); // in m/s
		
		reynoldsNumber = calcReynoldsNumber(
			insideDiameter / 1000,
			convertedDensity,
			velocity,
			convertedViscosity
		);

		// Generate LaTeX Steps
		let latex = `
			ID = OD - 2 \\times t = ${convertedOD.toFixed(2)} \\text{ mm} - 2 \\times ${convertedThickness.toFixed(2)} \\text{ mm} = ${insideDiameter.toFixed(2)} \\text{ mm} \\\\[10pt]
			v = \\frac{Q}{A} = \\frac{${(convertedFlowRate / 1000 / 60).toExponential(2)} \\text{ m}^3/\\text{s}}{\\frac{\\pi(ID/1000)^2}{4}} = ${velocity.toFixed(2)} \\text{ m/s} \\\\[10pt]
			Re = \\frac{\\rho v D}{\\mu} = \\frac{${convertedDensity.toFixed(2)} \\times ${velocity.toFixed(2)} \\times ${(insideDiameter / 1000).toFixed(4)}}{${convertedViscosity.toFixed(4)}} = ${reynoldsNumber.toFixed(0)}
		`;
		
		stepLatex = katex.renderToString(latex, { displayMode: true, fleqn: true });
	}
</script>

<svelte:head>
	<title>{siteConfig.title} - Reynolds Number</title>
	<meta name={siteConfig.description} content={siteConfig.description} />
</svelte:head>

<Grid>
	<Row>
		<Column>
			<h1 class="landing-page__heading">Reynolds Number Calculator</h1>
		</Column>
	</Row>

	<!-- Input section -->
	<!-- Outside Diameter (OD) -->
	<Row class="mb-4 items-end">
		<Column sm={2} md={5} lg={5}>
			<NumberInput labelText="Outside Diameter (OD)" bind:value={outsideDiameterValue} hideSteppers />
		</Column>
		<Column sm={2} md={3} lg={3}>
			<Dropdown bind:selectedId={outsideDiameterUnit} items={lengthUnits} label="Unit" />
		</Column>
	</Row>

	<!-- Length (l) -->
	<Row class="mb-4 items-end">
		<Column sm={2} md={5} lg={5}>
			<NumberInput labelText="Length (l)" bind:value={lengthValue} hideSteppers />
		</Column>
		<Column sm={2} md={3} lg={3}>
			<Dropdown bind:selectedId={lengthUnit} items={lengthUnits} label="Unit" />
		</Column>
	</Row>

	<!-- Wall Thickness (sch) -->
	<Row class="mb-4 items-end">
		<Column sm={2} md={5} lg={5}>
			<NumberInput labelText="Wall Thickness (t)" bind:value={wallThicknessValue} hideSteppers />
		</Column>
		<Column sm={2} md={3} lg={3}>
			<Dropdown bind:selectedId={wallThicknessUnit} items={lengthUnits} label="Unit" />
		</Column>
	</Row>

	<!-- Absolute Roughness (k) -->
	<Row class="mb-4 items-end">
		<Column sm={2} md={5} lg={5}>
			<NumberInput labelText="Absolute Roughness (k)" bind:value={absRoughnessValue} hideSteppers />
		</Column>
		<Column sm={2} md={3} lg={3}>
			<Dropdown bind:selectedId={absRoughnessUnit} items={lengthUnits} label="Unit" />
		</Column>
	</Row>

	<!-- Flow Rate (Q) -->
	<Row class="mb-4 items-end">
		<Column sm={2} md={5} lg={5}>
			<NumberInput labelText="Flow Rate (Q)" bind:value={flowRateValue} hideSteppers />
		</Column>
		<Column sm={2} md={3} lg={3}>
			<Dropdown bind:selectedId={flowRateUnit} items={flowRateUnits} label="Unit" />
		</Column>
	</Row>

	<!-- Viscosity (mu) -->
	<Row class="mb-4 items-end">
		<Column sm={2} md={5} lg={5}>
			<NumberInput labelText="Dynamic Viscosity (μ)" bind:value={dynamicViscValue} hideSteppers />
		</Column>
		<Column sm={2} md={3} lg={3}>
			<Dropdown bind:selectedId={dynamicViscUnit} items={viscosityUnits} label="Unit" />
		</Column>
	</Row>

	<!-- Density (rho) -->
	<Row class="mb-4 items-end">
		<Column sm={2} md={5} lg={5}>
			<NumberInput labelText="Density (ρ)" bind:value={densityValue} hideSteppers />
		</Column>
		<Column sm={2} md={3} lg={3}>
			<Dropdown bind:selectedId={densityUnit} items={densityUnits} label="Unit" />
		</Column>
	</Row>

	<Row class="mt-4">
		<Column>
			<Button on:click={calculatePressureDrop}>Calculate</Button>
		</Column>
	</Row>

	{#if reynoldsNumber > 0}
		<Row class="mt-4">
			<Column>
				<Tile class=''>
					<h4>Calculation Steps:</h4>
					<div class="latex-step">{@html stepLatex}</div>
				</Tile>
			</Column>
		</Row>
		<Row class="mt-4">
			<Column>
				<Tile>
					<h4>Result:</h4>
					<p>Reynold number: {reynoldsNumber.toFixed(3)}</p>
					<p>Flow type: <strong>{reynoldsNumber > 4000 ? 'Turbulent' : 'Laminar'}</strong></p>
				</Tile>
			</Column>
		</Row>
	{/if}
</Grid>

<style>
	:global(.landing-page__heading) {
		font-size: 2rem;
		font-weight: 400;
		margin-bottom: 2rem;
	}
	:global(.items-end) {
		align-items: flex-end;
	}
	:global(.mb-4) {
		margin-bottom: 1rem;
	}
	:global(.mt-4) {
		margin-top: 1rem;
	}
	:global(.mt-8) {
		margin-top: 2rem;
	}

	.latex-step{
		overflow-x: auto;
	}
</style>
