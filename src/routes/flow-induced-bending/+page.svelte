<script lang="ts">
	import { siteConfig } from '$lib/nav';
	import { convertLength, convertDensity, convertVelocity, lengthUnits, densityUnits, velocityUnits } from '$lib/convert';
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

	let fluidDensity = $state(2.3945); // kg/m³
	let fluidDensityUnit = $state('kg/m3');
	let fluidVelocity = $state(53.5); // m/s
	let fluidVelocityUnit = $state('m/s');
	let insideDiameter = $state(15.8); // mm
	let insideDiameterUnit = $state('mm');
	let outsideDiameter = $state(21.336); // mm
	let outsideDiameterUnit = $state('mm');
	let unsupportedLength = $state(473.329); // mm
	let unsupportedLengthUnit = $state('mm');
	let ratio = $state(0.584); // Fraction of exposed section (L_exp/L)

	let flowStress = $state<number | null>(null);
	let flowStressMPa = $state<number>(0);
	let stepLatex = $state('');

	function calculate() {
		// Convert all lengths to mm (base unit)
		const d_i = convertLength(insideDiameter, insideDiameterUnit);
		const d_o = convertLength(outsideDiameter, outsideDiameterUnit);
		const L = convertLength(unsupportedLength, unsupportedLengthUnit);

		const rho_f = convertDensity(fluidDensity, fluidDensityUnit); // Convert to kg/m³
		const V_f = convertVelocity(fluidVelocity, fluidVelocityUnit); // Convert to m/s
		const g = 981; // cm/s²
		const r = ratio;

		// Flow induced bending stress calculation
		// Formula: (7.5 × (ρ_f × V_f² / g) × r × L × d_o × (L - 0.5 × r × L)) / (0.098 × (d_o⁴ - d_i⁴) / d_o) × 10⁻³
		const numerator = 7.5 * (rho_f * Math.pow(V_f, 2) / g) * r * L * d_o * (L - 0.5 * r * L);
		const denominator = 0.098 * (Math.pow(d_o, 4) - Math.pow(d_i, 4)) / d_o;

		flowStress = (numerator / denominator) * Math.pow(10, -3); // kgf/cm²
		flowStressMPa = flowStress * 0.0980665; // Convert to MPa

		// Calculate intermediate values for better LaTeX display
		const velocitySquared = Math.pow(V_f, 2);
		const rhoVfSquared = rho_f * velocitySquared;
		const LminusHalfRL = L - 0.5 * r * L;
		const d_oPower4 = Math.pow(d_o, 4);
		const d_iPower4 = Math.pow(d_i, 4);

		// Generate LaTeX Steps
		let latex = `
			\\textbf{Known Information:} \\\\[10pt]
			\\begin{aligned}
			\\rho_f &= ${rho_f.toFixed(4)} \\text{ kg/m}^3 \\text{ (Fluid density)} \\\\[3pt]
			V_f &= ${V_f.toFixed(3)} \\text{ m/s} \\text{ (Fluid velocity)} \\\\[3pt]
			d_i &= ${d_i.toFixed(3)} \\text{ mm} \\text{ (Inside diameter)} \\\\[3pt]
			d_o &= ${d_o.toFixed(3)} \\text{ mm} \\text{ (Outside diameter)} \\\\[3pt]
			L &= ${L.toFixed(3)} \\text{ mm} \\text{ (Unsupported length)} \\\\[3pt]
			r &= ${r.toFixed(6)} \\text{ (Fraction of exposed section)} \\\\[3pt]
			g &= 981 \\text{ cm/s}^2 \\text{ (Gravitational constant)}
			\\end{aligned} \\\\[15pt]

			\\textbf{Flow-Induced Bending Stress ($\\sigma_f$):} \\\\[10pt]
			\\sigma_f = \\frac{7.5 \\times (\\rho_f \\times V_f^2 / g) \\times r \\times L \\times d_o \\times (L - 0.5 \\times r \\times L)}{0.098 \\times (d_o^4 - d_i^4) / d_o} \\times 10^{-3} \\\\[15pt]

			= \\frac{7.5 \\times (${rho_f.toFixed(4)} \\text{ kg/m}^3 \\times (${V_f.toFixed(3)} \\text{ m/s})^2 / 981 \\text{ cm/s}^2) \\times ${r.toFixed(6)} \\times ${L.toFixed(3)} \\text{ mm} \\times ${d_o.toFixed(3)} \\text{ mm} \\times (${L.toFixed(3)} \\text{ mm} - 0.5 \\times ${r.toFixed(6)} \\times ${L.toFixed(3)} \\text{ mm})}{0.098 \\times ((${d_o.toFixed(3)} \\text{ mm})^4 - (${d_i.toFixed(3)} \\text{ mm})^4) / ${d_o.toFixed(3)} \\text{ mm}} \\times 10^{-3} \\\\[15pt]

			= \\frac{7.5 \\times (${rhoVfSquared.toFixed(2)} \\text{ kg/m s}^2 / 981 \\text{ cm/s}^2) \\times ${r.toFixed(6)} \\times ${L.toFixed(3)} \\text{ mm} \\times ${d_o.toFixed(3)} \\text{ mm} \\times ${LminusHalfRL.toFixed(3)} \\text{ mm}}{0.098 \\times (${d_oPower4.toFixed(2)} \\text{ mm}^4 - ${d_iPower4.toFixed(2)} \\text{ mm}^4) / ${d_o.toFixed(3)} \\text{ mm}} \\times 10^{-3} \\\\[15pt]

			= \\frac{${numerator.toFixed(2)} \\text{ kg mm}^3 / \\text{m cm s}^2}{${denominator.toFixed(4)} \\text{ mm}^3} \\times 10^{-3} \\\\[15pt]

			= ${(numerator/denominator).toFixed(2)} \\times \\left(\\frac{1 \\text{ m}}{100 \\text{ cm}}\\right) \\times \\left(\\frac{1 \\text{ cm}}{10 \\text{ mm}}\\right)^3 \\times 10^{-3} \\text{ kgf/cm}^2 \\\\[15pt]

			= ${flowStress.toFixed(2)} \\text{ kgf/cm}^2 \\\\[10pt]

			\\approx ${flowStressMPa.toFixed(2)} \\text{ MPa}
		`;

		stepLatex = katex.renderToString(latex, { displayMode: true, fleqn: true });
	}
</script>

<svelte:head>
	<title>{siteConfig.title} - Flow Induced Bending Stress</title>
	<meta name={siteConfig.description} content={siteConfig.description} />
</svelte:head>

<Grid>
	<Row>
		<Column>
			<h1 class="landing-page__heading">Flow Induced Bending Stress Calculator</h1>
			<p class="description">Calculate flow-induced bending stress at probe support according to IEC 61831</p>
		</Column>
	</Row>

	<!-- Fluid Density -->
	<Row class="mb-4 items-end">
		<Column sm={2} md={5} lg={5}>
			<NumberInput labelText="Fluid Density (ρf)" bind:value={fluidDensity} hideSteppers />
		</Column>
		<Column sm={2} md={3} lg={3}>
			<Dropdown bind:selectedId={fluidDensityUnit} items={densityUnits} label="Unit" />
		</Column>
	</Row>

	<!-- Fluid Velocity -->
	<Row class="mb-4 items-end">
		<Column sm={2} md={5} lg={5}>
			<NumberInput labelText="Fluid Velocity (Vf)" bind:value={fluidVelocity} hideSteppers />
		</Column>
		<Column sm={2} md={3} lg={3}>
			<Dropdown bind:selectedId={fluidVelocityUnit} items={velocityUnits} label="Unit" />
		</Column>
	</Row>

	<!-- Inside Diameter -->
	<Row class="mb-4 items-end">
		<Column sm={2} md={5} lg={5}>
			<NumberInput labelText="Inside Diameter (di)" bind:value={insideDiameter} hideSteppers />
		</Column>
		<Column sm={2} md={3} lg={3}>
			<Dropdown bind:selectedId={insideDiameterUnit} items={lengthUnits} label="Unit" />
		</Column>
	</Row>

	<!-- Outside Diameter -->
	<Row class="mb-4 items-end">
		<Column sm={2} md={5} lg={5}>
			<NumberInput labelText="Outside Diameter (do)" bind:value={outsideDiameter} hideSteppers />
		</Column>
		<Column sm={2} md={3} lg={3}>
			<Dropdown bind:selectedId={outsideDiameterUnit} items={lengthUnits} label="Unit" />
		</Column>
	</Row>

	<!-- Unsupported Length -->
	<Row class="mb-4 items-end">
		<Column sm={2} md={5} lg={5}>
			<NumberInput labelText="Unsupported Length (L)" bind:value={unsupportedLength} hideSteppers />
		</Column>
		<Column sm={2} md={3} lg={3}>
			<Dropdown bind:selectedId={unsupportedLengthUnit} items={lengthUnits} label="Unit" />
		</Column>
	</Row>

	<!-- Ratio (r) -->
	<Row class="mb-4">
		<Column sm={4} md={4} lg={4}>
			<NumberInput labelText="Ratio (r = Lexp/L)" bind:value={ratio} hideSteppers step={0.001} />
		</Column>
	</Row>

	<Row class="mt-4">
		<Column>
			<Button on:click={calculate}>Calculate</Button>
		</Column>
	</Row>

	{#if flowStress !== null}
		<Row class="mt-4">
			<Column>
				<Tile>
					<h4>Results:</h4>
					<p><strong>Flow-Induced Bending Stress (σf):</strong> {flowStress.toFixed(2)} kgf/cm²</p>
					<p><strong>Flow-Induced Bending Stress (σf):</strong> {flowStressMPa.toFixed(2)} MPa</p>

					<div class="note-section">
						<h5>Note on Probe Orientation:</h5>
						<ul>
							<li><strong>Vertical Probe:</strong> The calculated flow-induced stress (σf) is the total stress at the probe support.</li>
							<li><strong>Horizontal Probe:</strong> Additional weight-induced stress (σw) must be considered. The total stress is: <strong>σtotal = σf + σw</strong></li>
						</ul>
						<p class="note-text"><em>This calculator only computes flow-induced bending stress. For horizontal installations, weight-induced stress should be calculated separately and added to the result.</em></p>
					</div>
					
					<div class="note-section">
						<h5>Note on Material Elastic Limit:</h5>
						<p>The calculated stress should be compared with the <strong>elastic limit</strong> of the probe material for safe operation.</p>
						<ul>
							<li><strong>Example - SS316 Material:</strong> Elastic limit ≈ 20,000 psi (≈ 137.9 MPa or ≈ 1406 kgf/cm²)</li>
							<li>The calculated stress must be <strong>below</strong> the elastic limit of the material to avoid permanent deformation.</li>
						</ul>
						<p class="note-text"><em>Always verify the elastic limit specification from the probe manufacturer's material data sheet.</em></p>
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
		margin-top: 1.5rem;
		margin-bottom: 0.75rem;
		font-weight: 500;
		color: #161616;
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

	.note-section {
		margin-top: 1.5rem;
		padding-top: 1rem;
		border-top: 1px solid #e0e0e0;
		background-color: #f4f4f4;
		padding: 1rem;
		border-radius: 4px;
	}

	.note-text {
		margin-top: 0.75rem;
		font-size: 0.9rem;
		color: #525252;
	}
</style>
