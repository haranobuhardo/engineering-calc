<script lang="ts">
	import { siteConfig } from '$lib/nav';
	import {
		convertLength,
		convertModulusOfElasticity,
		convertSpecificWeight,
		lengthUnits,
		modulusOfElasticityUnits,
		specificWeightUnits
	} from '$lib/convert';
	import {
		Grid,
		Row,
		Column,
		NumberInput,
		Dropdown,
		Button,
		Tile
	} from 'carbon-components-svelte';

	import katex from 'katex';
	import 'katex/dist/katex.min.css';

	// Input parameters with default values from example
	let probeDiameter = $state(0.840); // inches
	let probeDiameterUnit = $state('in');
	let probeLength = $state(18.635); // inches
	let probeLengthUnit = $state('in');
	let modulusOfElasticity = $state(28000000); // psi (2.8 × 10^7)
	let modulusOfElasticityUnit = $state('psi');
	let specificWeight = $state(0.29); // lb/in³
	let specificWeightUnit = $state('lb/in3');
	let flowRate = $state(113); // Nm³/hr
	let pipeDiameter = $state(21); // meters
	let pipeDiameterUnit = $state('mm');

	// Results
	let pipeArea = $state<number>(0);
	let velocity = $state<number>(0);
	let naturalFrequency = $state<number>(0);
	let strouhalFrequency = $state<number>(0);
	let magnificationFactor = $state<number | null>(null);
	let status = $state<string | null>(null);
	let stepLatex = $state('');

	function calculate() {
		// Convert all inputs to base units
		const D_probe = convertLength(probeDiameter, probeDiameterUnit); // mm
		const L = convertLength(probeLength, probeLengthUnit); // mm
		const E = convertModulusOfElasticity(modulusOfElasticity, modulusOfElasticityUnit); // psi
		const delta = convertSpecificWeight(specificWeight, specificWeightUnit); // lb/in³
		const D_pipe = convertLength(pipeDiameter, pipeDiameterUnit) / 1000; // Convert mm to m

		// Convert flow rate from Nm³/hr to m³/s
		const Q = flowRate / 3600; // m³/s

		// Step 1: Frequency constant
		const K_f = 2.09;

		// Step 2: Calculate pipe cross-sectional area
		pipeArea = (1/4) * Math.PI * Math.pow(D_pipe, 2); // m²

		// Step 3: Calculate flow velocity
		velocity = Q / pipeArea; // m/s

		// Step 4: Calculate natural frequency
		// Convert L from mm to inches for the formula (since E is in psi and delta is in lb/in³)
		const L_inches = L / 25.4;
		naturalFrequency = (K_f / Math.pow(L_inches, 2)) * Math.sqrt(E / delta); // Hz

		// Step 5: Calculate Strouhal frequency
		// Convert D_probe from mm to inches for the formula
		const D_probe_inches = D_probe / 25.4;
		strouhalFrequency = 2.64 * velocity / D_probe_inches; // Hz

		// Step 6: Calculate magnification factor
		magnificationFactor = strouhalFrequency / naturalFrequency;

		// Determine status
		if (magnificationFactor >= 0.8) {
			status = 'RESONANCE';
		} else {
			status = 'STATIC';
		}

		// Generate LaTeX Steps
		let latex = `
			\\textbf{Step 1: Define Constants} \\\\[5pt]
			K_f = ${K_f} \\text{ (Frequency constant for probe mounting)} \\\\[10pt]

			\\textbf{Step 2: Cross-Sectional Area ($A_{pipe}$)} \\\\[5pt]
			A_{pipe} = \\frac{1}{4} \\times \\pi \\times D_{pipe}^2 \\\\[5pt]
			A_{pipe} = \\frac{1}{4} \\times \\pi \\times (${D_pipe.toFixed(6)})^2 \\\\[5pt]
			A_{pipe} = ${(pipeArea * 1000).toFixed(6)} \\times 10^{-3} \\text{ m}^2 \\\\[10pt]

			\\textbf{Step 3: Flow Velocity ($v$)} \\\\[5pt]
			Q = ${flowRate} \\text{ Nm}^3\\text{/hr} = ${(Q).toFixed(6)} \\text{ m}^3\\text{/s} \\\\[5pt]
			v = \\frac{Q}{A_{pipe}} = \\frac{${(Q).toFixed(6)}}{${(pipeArea).toFixed(6)}} \\\\[5pt]
			v = ${velocity.toFixed(3)} \\text{ m/s} \\approx ${(velocity * 3.28084).toFixed(3)} \\text{ ft/s} \\\\[10pt]

			\\textbf{Step 4: Natural Frequency ($f_n$)} \\\\[5pt]
			L = ${(L_inches).toFixed(3)} \\text{ in} \\quad E = ${(E).toExponential(2)} \\text{ psi} \\quad \\delta = ${delta.toFixed(2)} \\text{ lb/in}^3 \\\\[5pt]
			f_n = \\frac{K_f}{L^2} \\times \\sqrt{\\frac{E}{\\delta}} \\\\[5pt]
			f_n = \\frac{${K_f}}{(${(L_inches).toFixed(3)})^2} \\times \\sqrt{\\frac{${(E).toExponential(2)}}{${delta.toFixed(2)}}} \\\\[5pt]
			f_n = ${naturalFrequency.toFixed(2)} \\text{ Hz} \\\\[10pt]

			\\textbf{Step 5: Strouhal Frequency ($f_w$)} \\\\[5pt]
			D_{probe} = ${(D_probe_inches).toFixed(3)} \\text{ in} \\\\[5pt]
			f_w = 2.64 \\times \\frac{v}{D_{probe}} \\\\[5pt]
			f_w = 2.64 \\times \\frac{${velocity.toFixed(3)}}{${(D_probe_inches).toFixed(3)}} \\\\[5pt]
			f_w = ${strouhalFrequency.toFixed(2)} \\text{ Hz} \\\\[10pt]

			\\textbf{Step 6: Magnification Factor ($r$)} \\\\[5pt]
			r = \\frac{f_w}{f_n} = \\frac{${strouhalFrequency.toFixed(2)}}{${naturalFrequency.toFixed(2)}} \\\\[5pt]
			r = ${magnificationFactor.toFixed(4)}
		`;

		stepLatex = katex.renderToString(latex, { displayMode: true, fleqn: true });
	}
</script>

<svelte:head>
	<title>{siteConfig.title} - Wake Frequency Calculation</title>
	<meta name={siteConfig.description} content={siteConfig.description} />
</svelte:head>

<Grid>
	<Row>
		<Column>
			<h1 class="landing-page__heading">Wake Frequency Calculation (WFC)</h1>
			<p class="description">Calculate wake frequency and resonance risk for thermowell/probe installations according to ASME PTC 19.3</p>
		</Column>
	</Row>

	<!-- Probe Diameter -->
	<Row class="mb-4 items-end">
		<Column sm={2} md={5} lg={5}>
			<NumberInput labelText="Probe Diameter (D_probe)" bind:value={probeDiameter} hideSteppers />
		</Column>
		<Column sm={2} md={3} lg={3}>
			<Dropdown bind:selectedId={probeDiameterUnit} items={lengthUnits} label="Unit" />
		</Column>
	</Row>

	<!-- Probe Length -->
	<Row class="mb-4 items-end">
		<Column sm={2} md={5} lg={5}>
			<NumberInput labelText="Probe Length (L)" bind:value={probeLength} hideSteppers />
		</Column>
		<Column sm={2} md={3} lg={3}>
			<Dropdown bind:selectedId={probeLengthUnit} items={lengthUnits} label="Unit" />
		</Column>
	</Row>

	<!-- Modulus of Elasticity -->
	<Row class="mb-4 items-end">
		<Column sm={2} md={5} lg={5}>
			<NumberInput labelText="Modulus of Elasticity (E)" bind:value={modulusOfElasticity} hideSteppers />
		</Column>
		<Column sm={2} md={3} lg={3}>
			<Dropdown bind:selectedId={modulusOfElasticityUnit} items={modulusOfElasticityUnits} label="Unit" />
		</Column>
	</Row>

	<!-- Specific Weight -->
	<Row class="mb-4 items-end">
		<Column sm={2} md={5} lg={5}>
			<NumberInput labelText="Specific Weight (δ)" bind:value={specificWeight} hideSteppers />
		</Column>
		<Column sm={2} md={3} lg={3}>
			<Dropdown bind:selectedId={specificWeightUnit} items={specificWeightUnits} label="Unit" />
		</Column>
	</Row>

	<!-- Flow Rate -->
	<Row class="mb-4">
		<Column sm={2} md={5} lg={5}>
			<NumberInput labelText="Flow Rate (Q)" bind:value={flowRate} hideSteppers />
		</Column>
		<Column sm={2} md={3} lg={3}>
			<p class="unit-label">Nm³/hr</p>
		</Column>
	</Row>

	<!-- Pipe Diameter -->
	<Row class="mb-4 items-end">
		<Column sm={2} md={5} lg={5}>
			<NumberInput labelText="Pipe Diameter (D_pipe)" bind:value={pipeDiameter} hideSteppers />
		</Column>
		<Column sm={2} md={3} lg={3}>
			<Dropdown bind:selectedId={pipeDiameterUnit} items={lengthUnits} label="Unit" />
		</Column>
	</Row>

	<Row class="mt-4">
		<Column>
			<Button on:click={calculate}>Calculate</Button>
		</Column>
	</Row>

	{#if magnificationFactor !== null}
		<Row class="mt-4">
			<Column>
				<Tile>
					<h4>Results:</h4>
					<p><strong>Pipe Cross-Sectional Area:</strong> {(pipeArea * 1000).toFixed(6)} × 10⁻³ m²</p>
					<p><strong>Flow Velocity:</strong> {velocity.toFixed(3)} m/s ({(velocity * 3.28084).toFixed(3)} ft/s)</p>
					<p><strong>Natural Frequency (f_n):</strong> {naturalFrequency.toFixed(2)} Hz</p>
					<p><strong>Strouhal Frequency (f_w):</strong> {strouhalFrequency.toFixed(2)} Hz</p>
					<p><strong>Magnification Factor (r):</strong> {magnificationFactor.toFixed(4)}</p>

					<div class="status-section {status === 'RESONANCE' ? 'danger' : 'safe'}">
						<h5>Status: {status}</h5>
						{#if status === 'RESONANCE'}
							<p class="status-description"><strong>⚠️ DANGER:</strong> The calculated magnification factor ({magnificationFactor.toFixed(2)}) is significantly greater than the safety limit of <strong>0.8</strong>. This indicates that the wake frequency is dangerously close to (or has surpassed) the natural frequency of the probe, posing a significant risk of structural damage or fatigue failure.</p>
						{:else}
							<p class="status-description"><strong>✓ SAFE:</strong> The calculated magnification factor ({magnificationFactor.toFixed(2)}) is below the safety limit of <strong>0.8</strong>. The wake frequency is sufficiently different from the natural frequency, posing minimal risk to structural integrity.</p>
						{/if}
					</div>
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

		<Row class="mt-4">
			<Column>
				<Tile>
					<h4>Reference Information:</h4>
					<ul>
						<li><strong>ASME PTC 19.3 Standard:</strong> This calculation follows the ASME PTC 19.3 standard for thermowell/probe installations.</li>
						<li><strong>Safety Threshold:</strong> A magnification factor (r) ≥ 0.8 indicates resonance risk.</li>
						<li><strong>Frequency Constant (K_f):</strong> 2.09 (standard value for probe mounting)</li>
						<li><strong>Strouhal Number Factor:</strong> 2.64 (conversion factor for English units)</li>
					</ul>
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

	.unit-label {
		font-size: 0.875rem;
		color: #525252;
		padding-top: 1.5rem;
	}

	h4 {
		margin-bottom: 1rem;
		font-weight: 500;
	}

	h5 {
		margin-top: 1.5rem;
		margin-bottom: 0.75rem;
		font-weight: 600;
		font-size: 1.1rem;
	}

	p {
		margin: 0.5rem 0;
	}

	ul {
		margin: 0.5rem 0;
		padding-left: 1.5rem;
	}

	li {
		margin: 0.5rem 0;
		line-height: 1.5;
	}

	.status-section {
		margin-top: 1.5rem;
		padding: 1rem;
		border-radius: 4px;
	}

	.status-section.danger {
		background-color: #fff1f1;
		border-left: 4px solid #da1e28;
	}

	.status-section.safe {
		background-color: #f0fff0;
		border-left: 4px solid #198038;
	}

	.status-section.danger h5 {
		color: #da1e28;
	}

	.status-section.safe h5 {
		color: #198038;
	}

	.status-description {
		margin-top: 0.75rem;
		line-height: 1.6;
	}
</style>
