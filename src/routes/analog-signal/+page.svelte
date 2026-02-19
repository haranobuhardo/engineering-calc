<script lang="ts">
	import { siteConfig } from '$lib/nav';
	import {
		Grid,
		Row,
		Column,
		NumberInput,
		Button,
		Tile,
		RadioButtonGroup,
		RadioButton
	} from 'carbon-components-svelte';

	import katex from 'katex';
	import 'katex/dist/katex.min.css';

	let mode = $state('ma-to-pv'); // 'ma-to-pv' or 'pv-to-ma'
	let minRange = $state(0);
	let maxRange = $state(100);
	let inputValue = $state(12); // Default to mid-range mA
	let result = $state<number | null>(null);

	let stepLatex = $state('');

	function calculate() {
		if (mode === 'ma-to-pv') {
			// mA to Process Value
			// Input is mA (4-20)
			// Formula: (max-min)/(20-4) * (reading - 4) + min
			let gradient = (maxRange - minRange) / 16;
			result = gradient * (inputValue - 4) + minRange;

			let latex = `PV = \\left( \\frac{${maxRange} - ${minRange}}{20 - 4} \\right) \\times (${inputValue} - 4) + ${minRange} = ${result.toFixed(2)}`;
			stepLatex = katex.renderToString(latex, { displayMode: true, fleqn: true });

		} else {
			// Process Value to mA
			// Input is PV
			// Formula: (20-4)/(max-min) * (reading - min) + 4
			let gradient = 16 / (maxRange - minRange);
			result = gradient * (inputValue - minRange) + 4;

			let latex = `mA = \\left( \\frac{20 - 4}{${maxRange} - ${minRange}} \\right) \\times (${inputValue} - ${minRange}) + 4 = ${result.toFixed(2)}`;
			stepLatex = katex.renderToString(latex, { displayMode: true, fleqn: true });
		}
	}
</script>

<svelte:head>
	<title>{siteConfig.title} - Analog Converter</title>
	<meta name={siteConfig.description} content={siteConfig.description} />
</svelte:head>

<Grid>
	<Row>
		<Column>
			<h1 class="landing-page__heading">Analog Signal Converter</h1>
		</Column>
	</Row>

	<Row class="mb-4">
		<Column>
			<RadioButtonGroup bind:selected={mode} legendText="Conversion Mode">
				<RadioButton value="ma-to-pv" labelText="4-20 mA to Process Value" />
				<RadioButton value="pv-to-ma" labelText="Process Value to 4-20 mA" />
			</RadioButtonGroup>
		</Column>
	</Row>

	<Row class="mb-4">
		<Column sm={4} md={4} lg={4}>
			<NumberInput labelText="Min Range" bind:value={minRange} hideSteppers/>
		</Column>
		<Column sm={4} md={4} lg={4}>
			<NumberInput labelText="Max Range" bind:value={maxRange} hideSteppers/>
		</Column>
	</Row>

	<Row class="mb-4">
		<Column sm={4} md={4} lg={4}>
			<NumberInput
				labelText={mode === 'ma-to-pv' ? "Input Signal (mA)" : "Input Process Value"}
				bind:value={inputValue}
				hideSteppers
			/>
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
					<h4>Calculation Step:</h4>
					<div class="latex-step">{@html stepLatex}</div>
				</Tile>
			</Column>
		</Row>
		<Row class="mt-4">
			<Column>
				<Tile>
					<h4>Result:</h4>
					<p class="result-text">
						{result.toFixed(3)}
						{mode === 'ma-to-pv' ? '(Process Value)' : 'mA'}
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
