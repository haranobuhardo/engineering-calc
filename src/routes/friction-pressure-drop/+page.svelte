<script lang="ts">
	import { siteConfig } from '$lib/nav';
	import {
		convertLength,
		convertFlowRate,
		convertViscosity,
		convertDensity,
		lengthUnits,
		flowRateUnits,
		viscosityUnits,
		densityUnits
	} from '$lib/convert';
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
	let lengthValue = $state(6);
	let lengthUnit = $state('m');
	let wallThicknessValue = $state(0.035);
	let wallThicknessUnit = $state('in');
	let absRoughnessValue = $state(0.015);
	let absRoughnessUnit = $state('mm');
	let flowRateValue = $state(3);
	let flowRateUnit = $state('lpm');
	let dynamicViscValue = $state(0.01);
	let dynamicViscUnit = $state('cps');
	let densityValue = $state(1);
	let densityUnit = $state('kg/m3');

	let reynoldsNumber = $state(0);
	let insideDiameter = $state(0);
	let velocity = $state(0);
	let frictionFactors = $state({ laminar: 0, churchill: 0, chen: 0 });
	let pressureDrops = $state({ laminar: 0, churchill: 0, chen: 0 });
	let flowRegime = $state('');
	let stepLatex = $state('');

	function calculateFrictionFactor(Re: number, roughness: number, ID: number): { laminar: number, churchill: number, chen: number } {
		let factors = { laminar: 0, churchill: 0, chen: 0 };

		// Laminar friction factor
		factors.laminar = 64 / Re;

		// Churchill friction factor
		const term1 = Math.pow((8 / Re), 12);
		const term2_log = Math.log((7 / Re) ** 0.9 + 0.27 * (roughness / ID));
		const term2 = 1 / Math.pow((Math.pow((2.457 * term2_log), 16) + Math.pow((37530 / Re), 16)), (3/2));
		factors.churchill = 8 * Math.pow((term1 + term2), (1/12));

		// Chen friction factor
		const chen_term1 = roughness / ID / 3.7065;
		const chen_term2 = (5.042 / Re) * Math.log10(((roughness / ID) ** 1.1098) / 2.8257 + Math.pow((7.149 / Re), 0.8981));
		factors.chen = Math.pow((1 / (-4 * Math.log10(chen_term1 - chen_term2))), 2) * 4;

		return factors;
	}

	function calculatePressureDrop() {
		// Convert all inputs to SI units
		let convertedOD = convertLength(outsideDiameterValue, outsideDiameterUnit) / 1000; // m
		let convertedLength = convertLength(lengthValue, lengthUnit) / 1000; // m
		let convertedThickness = convertLength(wallThicknessValue, wallThicknessUnit) / 1000; // m
		let convertedAbsRoughness = convertLength(absRoughnessValue, absRoughnessUnit) / 1000; // m
		let convertedFlowRate = convertFlowRate(flowRateValue, flowRateUnit) / 1000 / 60; // m³/s
		let convertedViscosity = convertViscosity(dynamicViscValue, dynamicViscUnit); // kg/(m·s)
		let convertedDensity = convertDensity(densityValue, densityUnit); // kg/m³

		// Calculate inside diameter
		insideDiameter = convertedOD - 2 * convertedThickness; // m

		// Calculate cross-sectional area
		const area = Math.PI * Math.pow(insideDiameter / 2, 2); // m²

		// Calculate velocity
		velocity = convertedFlowRate / area; // m/s

		// Calculate Reynolds number
		reynoldsNumber = (convertedDensity * velocity * insideDiameter) / convertedViscosity;

		// Determine flow regime
		if (reynoldsNumber < 2300) {
			flowRegime = 'Laminar';
		} else if (reynoldsNumber > 4000) {
			flowRegime = 'Turbulent';
		} else {
			flowRegime = 'Transitional';
		}

		// Calculate friction factors
		frictionFactors = calculateFrictionFactor(reynoldsNumber, convertedAbsRoughness, insideDiameter);

		// Calculate pressure drops (in Pascals)
		pressureDrops.laminar = (frictionFactors.laminar * convertedLength * convertedDensity * Math.pow(velocity, 2)) / (insideDiameter * 2);
		pressureDrops.churchill = (frictionFactors.churchill * convertedLength * convertedDensity * Math.pow(velocity, 2)) / (insideDiameter * 2);
		pressureDrops.chen = (frictionFactors.chen * convertedLength * convertedDensity * Math.pow(velocity, 2)) / (insideDiameter * 2);

		// Convert to psi (6895 Pa = 1 psi)
		pressureDrops.laminar /= 6895;
		pressureDrops.churchill /= 6895;
		pressureDrops.chen /= 6895;

		// Generate LaTeX Steps
		let latex = `
			\\textbf{Geometry:} \\\\[5pt]
			ID = OD - 2 \\times t = ${(convertedOD * 1000).toFixed(2)} - 2 \\times ${(convertedThickness * 1000).toFixed(2)} = ${(insideDiameter * 1000).toFixed(2)} \\text{ mm} \\\\[5pt]
			A = \\frac{\\pi \\cdot ID^2}{4} = \\frac{\\pi \\times ${(insideDiameter * 1000).toFixed(2)}^2}{4} = ${(area * 1e6).toFixed(4)} \\text{ mm}^2 \\\\[10pt]

			\\textbf{Flow Properties:} \\\\[5pt]
			v = \\frac{Q}{A} = \\frac{${(convertedFlowRate * 1000 * 60).toFixed(2)} \\text{ LPM}}{(area \\times 10^6 \\text{ mm}^2)} = ${velocity.toFixed(3)} \\text{ m/s} \\\\[5pt]
			Re = \\frac{\\rho \\cdot v \\cdot D}{\\mu} = \\frac{${convertedDensity.toFixed(1)} \\times ${velocity.toFixed(3)} \\times ${(insideDiameter * 1000).toFixed(2)}}{${convertedViscosity.toExponential(3)}} = ${reynoldsNumber.toFixed(0)} \\\\[5pt]
			\\text{Flow Regime: } ${flowRegime} \\\\[10pt]

			\\textbf{Friction Factors:} \\\\[5pt]
			f_{laminar} = \\frac{64}{Re} = \\frac{64}{${reynoldsNumber.toFixed(0)}} = ${frictionFactors.laminar.toFixed(6)} \\\\[5pt]
			f_{churchill} = ${frictionFactors.churchill.toFixed(6)} \\text{ (Churchill correlation)} \\\\[5pt]
			f_{chen} = ${frictionFactors.chen.toFixed(6)} \\text{ (Chen correlation)} \\\\[10pt]

			\\textbf{Pressure Drop:} \\\\[5pt]
			\\Delta P = \\frac{f \\cdot L \\cdot \\rho \\cdot v^2}{2 \\cdot D} \\\\[5pt]
			\\Delta P_{laminar} = ${pressureDrops.laminar.toFixed(4)} \\text{ psi} \\\\[5pt]
			\\Delta P_{churchill} = ${pressureDrops.churchill.toFixed(4)} \\text{ psi} \\\\[5pt]
			\\Delta P_{chen} = ${pressureDrops.chen.toFixed(4)} \\text{ psi}
		`;

		stepLatex = katex.renderToString(latex, { displayMode: true, fleqn: true });
	}
</script>

<svelte:head>
	<title>{siteConfig.title} - Friction Pressure Drop</title>
	<meta name={siteConfig.description} content={siteConfig.description} />
</svelte:head>

<Grid>
	<Row>
		<Column>
			<h1 class="landing-page__heading">Friction Pressure Drop Calculator</h1>
			<p class="description">Calculate pressure drop due to friction in pipes using multiple correlations</p>
		</Column>
	</Row>

	<!-- Outside Diameter (OD) -->
	<Row class="mb-4 items-end">
		<Column sm={2} md={5} lg={5}>
			<NumberInput labelText="Outside Diameter (OD)" bind:value={outsideDiameterValue} hideSteppers />
		</Column>
		<Column sm={2} md={3} lg={3}>
			<Dropdown bind:selectedId={outsideDiameterUnit} items={lengthUnits} label="Unit" />
		</Column>
	</Row>

	<!-- Length -->
	<Row class="mb-4 items-end">
		<Column sm={2} md={5} lg={5}>
			<NumberInput labelText="Pipe Length (L)" bind:value={lengthValue} hideSteppers />
		</Column>
		<Column sm={2} md={3} lg={3}>
			<Dropdown bind:selectedId={lengthUnit} items={lengthUnits} label="Unit" />
		</Column>
	</Row>

	<!-- Wall Thickness -->
	<Row class="mb-4 items-end">
		<Column sm={2} md={5} lg={5}>
			<NumberInput labelText="Wall Thickness (t)" bind:value={wallThicknessValue} hideSteppers />
		</Column>
		<Column sm={2} md={3} lg={3}>
			<Dropdown bind:selectedId={wallThicknessUnit} items={lengthUnits} label="Unit" />
		</Column>
	</Row>

	<!-- Absolute Roughness -->
	<Row class="mb-4 items-end">
		<Column sm={2} md={5} lg={5}>
			<NumberInput labelText="Absolute Roughness (ε)" bind:value={absRoughnessValue} hideSteppers />
		</Column>
		<Column sm={2} md={3} lg={3}>
			<Dropdown bind:selectedId={absRoughnessUnit} items={lengthUnits} label="Unit" />
		</Column>
	</Row>

	<!-- Flow Rate -->
	<Row class="mb-4 items-end">
		<Column sm={2} md={5} lg={5}>
			<NumberInput labelText="Flow Rate (Q)" bind:value={flowRateValue} hideSteppers />
		</Column>
		<Column sm={2} md={3} lg={3}>
			<Dropdown bind:selectedId={flowRateUnit} items={flowRateUnits} label="Unit" />
		</Column>
	</Row>

	<!-- Viscosity -->
	<Row class="mb-4 items-end">
		<Column sm={2} md={5} lg={5}>
			<NumberInput labelText="Dynamic Viscosity (μ)" bind:value={dynamicViscValue} hideSteppers />
		</Column>
		<Column sm={2} md={3} lg={3}>
			<Dropdown bind:selectedId={dynamicViscUnit} items={viscosityUnits} label="Unit" />
		</Column>
	</Row>

	<!-- Density -->
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
				<Tile>
					<h4>Results:</h4>
					<p><strong>Inside Diameter:</strong> {(insideDiameter * 1000).toFixed(2)} mm</p>
					<p><strong>Velocity:</strong> {velocity.toFixed(3)} m/s</p>
					<p><strong>Reynolds Number:</strong> {reynoldsNumber.toFixed(0)}</p>
					<p><strong>Flow Regime:</strong> {flowRegime}</p>
					<br />
					<h5>Pressure Drops:</h5>
					<p><strong>Laminar:</strong> {pressureDrops.laminar.toFixed(4)} psi</p>
					<p><strong>Churchill:</strong> {pressureDrops.churchill.toFixed(4)} psi</p>
					<p><strong>Chen:</strong> {pressureDrops.chen.toFixed(4)} psi</p>
				</Tile>
			</Column>
		</Row>

		<Row class="mt-4">
			<Column>
				<Tile>
					<h4>Calculation Steps:</h4>
					<div class="latex-step">{@html stepLatex}</div>
				</Tile>
			</Column>
		</Row>
	{/if}
</Grid>

<style>
	:global(.landing-page__heading) {
		font-size: 2rem;
		font-weight: 400;
		margin-bottom: 0.5rem;
	}

	.description {
		font-size: 0.95rem;
		color: #525252;
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

	.latex-step {
		overflow-x: auto;
		padding: 1rem 0;
	}

	h4 {
		margin-bottom: 1rem;
		font-weight: 500;
	}

	h5 {
		margin-top: 1rem;
		margin-bottom: 0.5rem;
		font-weight: 500;
	}

	p {
		margin: 0.5rem 0;
	}
</style>
