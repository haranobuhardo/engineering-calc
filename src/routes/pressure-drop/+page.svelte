<script lang="ts">
	import { siteConfig } from '$lib/nav';
	import { convertLength, convertFlowRate, convertViscosity, convertDensity } from '$lib/convert';
	import katex from 'katex';
	import {
		Grid,
		Row,
		Column,
		NumberInput,
		Select,
		SelectItem,
		Button,
		Tile
	} from 'carbon-components-svelte';

	interface UnitOption {
		value: string;
		text: string;
		scale?: number;
	}

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
	let stepIDHtml = $state('');
	let stepVelocityHtml = $state('');
	let stepReHtml = $state('');

	let lengthUnits: UnitOption[] = [
		{ value: 'in', text: 'in' },
		{ value: 'ft', text: 'ft' },
		{ value: 'mm', text: 'mm' },
		{ value: 'm', text: 'm' }
	];

	let flowRateUnits: UnitOption[] = [
		{ value: 'lpm', text: 'lpm' },
		{ value: 'lph', text: 'lph' },
		{ value: 'bpd', text: 'bpd' }
	];

	let dynamicViscUnits: UnitOption[] = [
		{ value: 'cps', text: 'cP' },
		{ value: 'kg/m-s', text: 'kg/m-s' }
	];

	let densityUnits: UnitOption[] = [
		{ value: 'lbs/ft3', text: 'lbs/ft3' },
		{ value: 'kg/m3', text: 'kg/m3' }
	];

	function calcID(outsideDiameter: number, wallThickness: number): number {
		return outsideDiameter - 2 * wallThickness;
	}

	function calcVelocity(insideDiameter: number, flowRate: number): number {
		// insideDiameter: mm
		// flowRate: LPM (liter per minute)
		let area = (1 / 4) * 3.14 * (insideDiameter / 1000) ** 2; // m**2
		let flowRateConv = flowRate / 1000 / 60; // m**3/second
		return flowRateConv / area; // in m/s
	}

	function calcRelRoughness(absRoughness: number, insideDiameter: number): number {
		// absRoughness: meter (m)
		// insideDiameter: meter (m)
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
		// viscosity: kg/(m.s)
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
		let relativeRoughness: number = calcRelRoughness(convertedAbsRoughness, insideDiameter);

		reynoldsNumber = calcReynoldsNumber(
			insideDiameter / 1000,
			convertedDensity,
			velocity,
			convertedViscosity
		);

		// Generate LaTeX Steps
		// 1. ID Step
		let idLatex = `ID = OD - 2 \\times t = ${convertedOD.toFixed(2)} \\text{ mm} - 2 \\times ${convertedThickness.toFixed(2)} \\text{ mm} = ${insideDiameter.toFixed(2)} \\text{ mm}`;
		stepIDHtml = katex.renderToString(idLatex, { displayMode: true });

		// 2. Velocity Step
		let velLatex = `v = \\frac{Q}{A} = \\frac{${(convertedFlowRate / 1000 / 60).toExponential(2)} \\text{ m}^3/\\text{s}}{\\frac{\\pi(ID)^2}{4}} = ${velocity.toFixed(2)} \\text{ m/s}`;
		stepVelocityHtml = katex.renderToString(velLatex, { displayMode: true });

		// 3. Reynolds Step
		let reLatex = `Re = \\frac{\\rho v D}{\\mu} = \\frac{${convertedDensity.toFixed(2)} \\times ${velocity.toFixed(2)} \\times ${(insideDiameter / 1000).toFixed(4)}}{${convertedViscosity.toFixed(4)}} = ${reynoldsNumber.toFixed(0)}`;
		stepReHtml = katex.renderToString(reLatex, { displayMode: true });
	}
</script>

<svelte:head>
	<title>{siteConfig.title} - Pressure Drop</title>
	<meta name={siteConfig.description} content={siteConfig.description} />
</svelte:head>

<Grid>
	<Row>
		<Column>
			<h1 class="landing-page__heading">Pressure Drop Calculator</h1>
		</Column>
	</Row>

	<!-- Input section -->
	<!-- Outside Diameter (OD) -->
	<Row class="mb-4 items-end">
		<Column sm={3} md={5} lg={5}>
			<NumberInput labelText="Outside Diameter (OD)" bind:value={outsideDiameterValue} />
		</Column>
		<Column sm={1} md={3} lg={3}>
			<Select bind:selected={outsideDiameterUnit} labelText="Unit">
				{#each lengthUnits as lengthUnit}
					<SelectItem value={lengthUnit.value} text={lengthUnit.text} />
				{/each}
			</Select>
		</Column>
	</Row>

	<!-- Length (l) -->
	<Row class="mb-4 items-end">
		<Column sm={3} md={5} lg={5}>
			<NumberInput labelText="Length (l)" bind:value={lengthValue} />
		</Column>
		<Column sm={1} md={3} lg={3}>
			<Select bind:selected={lengthUnit} labelText="Unit">
				{#each lengthUnits as lengthUnit}
					<SelectItem value={lengthUnit.value} text={lengthUnit.text} />
				{/each}
			</Select>
		</Column>
	</Row>

	<!-- Wall Thickness (sch) -->
	<Row class="mb-4 items-end">
		<Column sm={3} md={5} lg={5}>
			<NumberInput labelText="Wall Thickness (t)" bind:value={wallThicknessValue} />
		</Column>
		<Column sm={1} md={3} lg={3}>
			<Select bind:selected={wallThicknessUnit} labelText="Unit">
				{#each lengthUnits as lengthUnit}
					<SelectItem value={lengthUnit.value} text={lengthUnit.text} />
				{/each}
			</Select>
		</Column>
	</Row>

	<!-- Absolute Roughness (k) -->
	<Row class="mb-4 items-end">
		<Column sm={3} md={5} lg={5}>
			<NumberInput labelText="Absolute Roughness (k)" bind:value={absRoughnessValue} />
		</Column>
		<Column sm={1} md={3} lg={3}>
			<Select bind:selected={absRoughnessUnit} labelText="Unit">
				{#each lengthUnits as lengthUnit}
					<SelectItem value={lengthUnit.value} text={lengthUnit.text} />
				{/each}
			</Select>
		</Column>
	</Row>

	<!-- Flow Rate (Q) -->
	<Row class="mb-4 items-end">
		<Column sm={3} md={5} lg={5}>
			<NumberInput labelText="Flow Rate (Q)" bind:value={flowRateValue} />
		</Column>
		<Column sm={1} md={3} lg={3}>
			<Select bind:selected={flowRateUnit} labelText="Unit">
				{#each flowRateUnits as flowRateUnit}
					<SelectItem value={flowRateUnit.value} text={flowRateUnit.text} />
				{/each}
			</Select>
		</Column>
	</Row>

	<!-- Viscosity (mu) -->
	<Row class="mb-4 items-end">
		<Column sm={3} md={5} lg={5}>
			<NumberInput labelText="Dynamic Viscosity (μ)" bind:value={dynamicViscValue} />
		</Column>
		<Column sm={1} md={3} lg={3}>
			<Select bind:selected={dynamicViscUnit} labelText="Unit">
				{#each dynamicViscUnits as dynamicViscUnit}
					<SelectItem value={dynamicViscUnit.value} text={dynamicViscUnit.text} />
				{/each}
			</Select>
		</Column>
	</Row>

	<!-- Density (rho) -->
	<Row class="mb-4 items-end">
		<Column sm={3} md={5} lg={5}>
			<NumberInput labelText="Density (ρ)" bind:value={densityValue} />
		</Column>
		<Column sm={1} md={3} lg={3}>
			<Select bind:selected={densityUnit} labelText="Unit">
				{#each densityUnits as densityUnit}
					<SelectItem value={densityUnit.value} text={densityUnit.text} />
				{/each}
			</Select>
		</Column>
	</Row>

	<Row class="mt-4">
		<Column>
			<Button on:click={calculatePressureDrop}>Calculate</Button>
		</Column>
	</Row>

	{#if reynoldsNumber > 0}
		<Row class="mt-8">
			<Column>
				<Tile>
					<h4>Calculation Steps:</h4>
					<div class="latex-step">{@html stepIDHtml}</div>
					<div class="latex-step">{@html stepVelocityHtml}</div>
					<div class="latex-step">{@html stepReHtml}</div>
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
</style>
