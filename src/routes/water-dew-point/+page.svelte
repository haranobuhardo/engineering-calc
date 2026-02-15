<script lang="ts">
	import { siteConfig } from '$lib/nav';
	import {
		Grid,
		Row,
		Column,
		NumberInput,
		Button,
		Tile,
		Dropdown
	} from 'carbon-components-svelte';

	import katex from 'katex';
	import 'katex/dist/katex.min.css';

	let pressure = $state(1); // default
	let pressureUnit = $state('bar');
	let waterContent = $state(100);
	let waterContentUnit = $state('ppmv');
	let result = $state<number | null>(null);

	let stepLatex = $state('');

	const pressureUnitsItems = [
		{ id: 'bar', text: 'bar' },
		{ id: 'psi', text: 'psi' },
		{ id: 'atm', text: 'atm' },
		{ id: 'kpa', text: 'kPa' }
	];

	const waterUnitsItems = [
		{ id: 'ppmv', text: 'ppmv' },
		{ id: 'vol_percent', text: '% vol' }
	];

	function calculate() {
		// Convert Pressure to atm
		let p_atm = 1;
		if (pressureUnit === 'bar') p_atm = pressure / 1.01325;
		else if (pressureUnit === 'psi') p_atm = pressure / 14.696;
		else if (pressureUnit === 'atm') p_atm = pressure;
		else if (pressureUnit === 'kpa') p_atm = pressure / 101.325;

		// Convert Water Content to Mole Fraction
		let fraction = 0;
		if (waterContentUnit === 'ppmv') fraction = waterContent * 1e-6;
		else if (waterContentUnit === 'vol_percent') fraction = waterContent * 1e-2;

		// Calculate Partial Pressure in mmHg
		// P_partial_atm = P_total_atm * fraction
		// P_mmhg = P_partial_atm * 760
		const p_h2o_mmhg = p_atm * fraction * 760;

		if (p_h2o_mmhg <= 0) {
			result = null;
			stepLatex = 'Error: Water partial pressure is 0 or negative';
			return;
		}

		// Formula: WDP (K) = 5038.13 / (20.1424 - ln(P_H2O_mmHg))
		const wdp_kelvin = 5038.13 / (20.1424 - Math.log(p_h2o_mmhg));

		// Convert to Celcius
		result = wdp_kelvin - 273.15;

		let latex = `
			P_{H_2O} = P_{sys} \\times y_{H_2O} \\times 760 \\\\
			P_{H_2O} = ${p_atm.toFixed(3)} \\text{ atm} \\times ${fraction.toExponential(2)} \\times 760 = ${p_h2o_mmhg.toFixed(4)} \\text{ mmHg} \\\\
			T_{K} = \\frac{5038.13}{20.1424 - \\ln(P_{H_2O})} = \\frac{5038.13}{20.1424 - \\ln(${p_h2o_mmhg.toFixed(4)})} = ${wdp_kelvin.toFixed(2)} \\text{ K} \\\\
			T_{^{\\circ}C} = ${wdp_kelvin.toFixed(2)} - 273.15 = ${result.toFixed(2)} ^{\\circ}\\text{C}
		`;
		stepLatex = katex.renderToString(latex, { displayMode: true });
	}
</script>

<svelte:head>
	<title>{siteConfig.title} - Water Dew Point</title>
	<meta name={siteConfig.description} content={siteConfig.description} />
</svelte:head>

<Grid>
	<Row>
		<Column>
			<h1 class="landing-page__heading">Water Dew Point Calculator</h1>
		</Column>
	</Row>

	<Row class="mb-4 items-end">
		<Column sm={2} md={5} lg={5}>
			<NumberInput labelText="System Pressure" bind:value={pressure} hideSteppers/>
		</Column>
		<Column sm={2} md={3} lg={3}>
			<Dropdown bind:selectedId={pressureUnit} items={pressureUnitsItems} />
		</Column>
	</Row>

	<Row class="mb-4 items-end">
		<Column sm={2} md={5} lg={5}>
			<NumberInput labelText="Water Content" bind:value={waterContent} hideSteppers/>
		</Column>
		<Column sm={2} md={3} lg={3}>
			<Dropdown bind:selectedId={waterContentUnit} items={waterUnitsItems} />
		</Column>
	</Row>

	<Row class="mt-4">
		<Column>
			<Button on:click={calculate}>Calculate</Button>
		</Column>
	</Row>

	{#if result !== null}
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
					<h4>Result:</h4>
					<p class="result-text">
						Dew Point: {result.toFixed(2)} °C
					</p>
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
	.result-text {
		font-size: 1.5rem;
		font-weight: 600;
	}

	.latex-step{
		overflow-x: auto;
	}
</style>
