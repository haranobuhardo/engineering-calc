<script lang="ts">
	import { siteConfig } from '$lib/nav';
	import {
		Grid,
		Row,
		Column,
		NumberInput,
		Button,
		Tile
	} from 'carbon-components-svelte';

	import katex from 'katex';
	import 'katex/dist/katex.min.css';

	let measuredValue = $state(100.0);
	let trueValue = $state(100.0);
	let result_error = $state<number | null>(null);
	let result_span = $state<number | null>(null);
	let initialSpanFactor = $state<number | null>(1.00);
	let stepLatex = $state('');

	function calculate() {
		if (trueValue === 0) {
			result_error = 0; // Avoid division by zero
			stepLatex = 'Error: True value cannot be 0';
			return;
		}
		// Formula: abs(measured - true) / true * 100
		result_error = (Math.abs(measuredValue - trueValue) / trueValue) * 100;
		result_span = (trueValue / measuredValue) * initialSpanFactor;

		let latex = `\\text{Error} \\% = \\left| \\frac{\\text{Measured} - \\text{True}}{\\text{True}} \\right| \\times 100 \\\\ = \\left| \\frac{${measuredValue} - ${trueValue}}{${trueValue}} \\right| \\times 100 = ${result_error.toFixed(4)} \\%`;
		stepLatex = katex.renderToString(latex, { displayMode: true });
	}
</script>

<svelte:head>
	<title>{siteConfig.title} - Span Factor (Error %)</title>
	<meta name={siteConfig.description} content={siteConfig.description} />
</svelte:head>

<Grid>
	<Row>
		<Column>
			<h1 class="landing-page__heading">Span Factor / Error Percentage</h1>
		</Column>
	</Row>

	<Row class="mb-4">
		<Column sm={4} md={4} lg={4}>
			<NumberInput labelText="True / Reference Value" bind:value={trueValue} hideSteppers/>
		</Column>
		<Column sm={4} md={4} lg={4}>
			<NumberInput labelText="Current Measured Value" bind:value={measuredValue} hideSteppers/>
		</Column>
		<Column sm={4} md={4} lg={4}>
			<NumberInput labelText="Initial Span Factor" bind:value={initialSpanFactor} hideSteppers/>
		</Column>
	</Row>

	<Row class="mt-4 mb-4">
		<Column>
			<Button on:click={calculate}>Calculate Error %</Button>
		</Column>
	</Row>

	{#if result_error !== null && result_span !== null}
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
						Error: {result_error.toFixed(4)} % <br>
						New Span Factor: {result_span.toFixed(4)}
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
		font-size: 1.2rem;
		font-weight: 600;
	}
</style>
