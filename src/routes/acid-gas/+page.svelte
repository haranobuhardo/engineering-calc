<script lang="ts">
	import { siteConfig } from '$lib/nav';
	import { 
		convertTemperature, 
		convertPressure, 
		temperatureUnits, 
		pressureUnits 
	} from '$lib/convert';
	import {
		Grid,
		Row,
		Column,
		NumberInput,
		Dropdown,
		Button,
		Tile,
		RadioButtonGroup,
		RadioButton
	} from 'carbon-components-svelte';

	import katex from 'katex';
	import 'katex/dist/katex.min.css';

	let mode = $state('calculate-so3'); // 'calculate-so3' or 'direct-so3'
	let temperature = $state(1000); // °C (for SO3 conversion)
	let temperatureUnit = $state('C');
	let pressure = $state(1); // atm
	let pressureUnit = $state('atm');
	let h2oContent = $state(0.1); // mole fraction
	let so2Content = $state(0.01); // mole fraction
	let o2Content = $state(0.05); // mole fraction
	let so3Content = $state(0.001); // mole fraction

	let calculatedSO3 = $state<number | null>(null);
	let acidDewPoints = $state<{verhoff: number, okkes: number, zarenezhad: number} | null>(null);
	let stepLatexSO3 = $state('');
	let stepLatexADP = $state('');

	function calculate() {
		let so3Value: number;
		
		// Convert temperature and pressure to base units
		const T_kelvin = convertTemperature(temperature, temperatureUnit);
		const T = T_kelvin - 273.15; // Convert to Celsius for SO3 conversion formula
		const P_atm = convertPressure(pressure, pressureUnit);
		const P_psia = P_atm; // convertPressure returns psia
		const P = P_psia / 14.696; // Convert psia to atm
		
		if (mode === 'calculate-so3') {
			// Calculate SO3 from SO2 and O2
			// Kp formula: 10^((0.4342*(31.752231-0.040591095*T))/(1+0.0037782493*T))
			// where T is in Celsius
			const Kp_numerator = 0.4342 * (31.752231 - 0.040591095 * T);
			const Kp_denominator = 1 + 0.0037782493 * T;
			const Kp = Math.pow(10, Kp_numerator / Kp_denominator);

			// SO3_content = Kp × SO2_content × O2_content^0.5 / (1 + Kp × O2_content^0.5)
			so3Value = (Kp * so2Content * Math.pow(o2Content, 0.5)) / (1 + Kp * Math.pow(o2Content, 0.5));
			calculatedSO3 = so3Value;

			// Generate LaTeX for SO3 calculation
			let latexSO3 = `
				\\textbf{SO}_3 \\textbf{ Conversion:} \\\\[5pt]
				K_p = 10^{\\frac{0.4342 \\times (31.752231 - 0.040591095 \\times ${T.toFixed(1)})}{1 + 0.0037782493 \\times ${T.toFixed(1)}}} = ${Kp.toFixed(6)} \\\\[5pt]
				\\text{SO}_3 = \\frac{K_p \\times \\text{SO}_2 \\times \\text{O}_2^{0.5}}{1 + K_p \\times \\text{O}_2^{0.5}} \\\\[5pt]
				\\text{SO}_3 = \\frac{${Kp.toFixed(6)} \\times ${so2Content.toFixed(4)} \\times ${o2Content.toFixed(4)}^{0.5}}{1 + ${Kp.toFixed(6)} \\times ${o2Content.toFixed(4)}^{0.5}} \\\\[5pt]
				\\text{SO}_3 = ${so3Value.toFixed(6)}
			`;
			stepLatexSO3 = katex.renderToString(latexSO3, { displayMode: true, fleqn: true });
		} else {
			// Direct SO3 input
			so3Value = so3Content;
			calculatedSO3 = null;
			stepLatexSO3 = '';
		}

		// Calculate partial pressures (in atm)
		const p_H2O = h2oContent * P;
		const p_SO3 = so3Value * P;

		// Calculate acid dew points
		acidDewPoints = {
			verhoff: 0,
			okkes: 0,
			zarenezhad: 0
		};

		if (p_SO3 > 0 && p_H2O > 0) {
			// Verhoff correlation (returns Kelvin, then convert to Celsius)
			// ADP = 1/(0.002276 - 0.00002943*ln(p_H2O*760) - 0.0000858*ln(p_SO3*760) + 0.0000062*ln(p_H2O*760)*ln(p_SO3*760))
			const p_H2O_mmHg = p_H2O * 760;
			const p_SO3_mmHg = p_SO3 * 760;
			const verhoffKelvin = 1 / (0.002276
				- 0.00002943 * Math.log(p_H2O_mmHg)
				- 0.0000858 * Math.log(p_SO3_mmHg)
				+ 0.0000062 * Math.log(p_H2O_mmHg) * Math.log(p_SO3_mmHg));
			acidDewPoints.verhoff = verhoffKelvin - 273.15;

			// Okkes correlation (returns Celsius)
			// ADP = 205.25 + 27.06*log10(p_H2O) + 10.86*log10(p_SO3) + 1.06*(log10(p_SO3)+8)^2.19
			acidDewPoints.okkes = 205.25
				+ 27.06 * Math.log10(p_H2O)
				+ 10.86 * Math.log10(p_SO3)
				+ 1.06 * Math.pow((Math.log10(p_SO3) + 8), 2.19);

			// Zarenezhad correlation (returns Celsius)
			// ADP = 150 + 11.664*ln(p_SO3*760) + 8.1328*ln(p_H2O*760) - 0.383226*ln(p_SO3*760)*ln(p_H2O*760)
			acidDewPoints.zarenezhad = 150
				+ 11.664 * Math.log(p_SO3_mmHg)
				+ 8.1328 * Math.log(p_H2O_mmHg)
				- 0.383226 * Math.log(p_SO3_mmHg) * Math.log(p_H2O_mmHg);

			// Generate LaTeX for ADP calculation
			let latexADP = `
				\\textbf{Partial Pressures:} \\\\[5pt]
				p_{H_2O} = \\text{H}_2\\text{O} \\times P = ${h2oContent.toFixed(4)} \\times ${pressure.toFixed(2)} = ${p_H2O.toFixed(6)} \\text{ atm} \\\\[5pt]
				p_{SO_3} = \\text{SO}_3 \\times P = ${so3Value.toFixed(6)} \\times ${pressure.toFixed(2)} = ${p_SO3.toFixed(6)} \\text{ atm} \\\\[10pt]

				\\textbf{Acid Dew Point Correlations:} \\\\[5pt]
				\\underline{\\text{Verhoff:}} \\\\[3pt]
				T_{ADP} = \\frac{1}{0.002276 - 0.00002943 \\ln(${(p_H2O * 760).toFixed(4)}) - 0.0000858 \\ln(${(p_SO3 * 760).toFixed(4)}) + 0.0000062 \\ln(${(p_H2O * 760).toFixed(4)}) \\ln(${(p_SO3 * 760).toFixed(4)})} \\\\[3pt]
				T_{ADP} = ${acidDewPoints.verhoff.toFixed(2)} ^\\circ \\text{C} \\\\[10pt]

				\\underline{\\text{Okkes:}} \\\\[3pt]
				T_{ADP} = 205.25 + 27.06 \\log_{10}(${p_H2O.toFixed(6)}) + 10.86 \\log_{10}(${p_SO3.toFixed(6)}) + 1.06(\\log_{10}(${p_SO3.toFixed(6)}) + 8)^{2.19} \\\\[3pt]
				T_{ADP} = ${acidDewPoints.okkes.toFixed(2)} ^\\circ \\text{C} \\\\[10pt]

				\\underline{\\text{Zarenezhad:}} \\\\[3pt]
				T_{ADP} = 150 + 11.664 \\ln(${(p_SO3 * 760).toFixed(4)}) + 8.1328 \\ln(${(p_H2O * 760).toFixed(4)}) - 0.383226 \\ln(${(p_SO3 * 760).toFixed(4)}) \\ln(${(p_H2O * 760).toFixed(4)}) \\\\[3pt]
				T_{ADP} = ${acidDewPoints.zarenezhad.toFixed(2)} ^\\circ \\text{C}
			`;
			stepLatexADP = katex.renderToString(latexADP, { displayMode: true, fleqn: true });
		}
	}
</script>

<svelte:head>
	<title>{siteConfig.title} - Acid Gas Calculator</title>
	<meta name={siteConfig.description} content={siteConfig.description} />
</svelte:head>

<Grid>
	<Row>
		<Column>
			<h1 class="landing-page__heading">Acid Gas Dew Point Calculator</h1>
			<p class="description">Calculate H₂SO₄ acid dew point from gas composition</p>
		</Column>
	</Row>

	<!-- Mode Selection -->
	<Row class="mb-4">
		<Column>
			<RadioButtonGroup bind:selected={mode} legendText="Input Mode">
				<RadioButton value="calculate-so3" labelText="Calculate SO₃ from SO₂ and O₂" />
				<RadioButton value="direct-so3" labelText="Direct SO₃ Input" />
			</RadioButtonGroup>
		</Column>
	</Row>

	<!-- Temperature (for SO3 conversion) -->
	{#if mode === 'calculate-so3'}
		<Row class="mb-4 items-end">
			<Column sm={2} md={5} lg={5}>
				<NumberInput labelText="Temperature" bind:value={temperature} hideSteppers />
			</Column>
			<Column sm={2} md={3} lg={3}>
				<Dropdown bind:selectedId={temperatureUnit} items={temperatureUnits} label="Unit" />
			</Column>
		</Row>
	{/if}

	<!-- Pressure -->
	<Row class="mb-4 items-end">
		<Column sm={2} md={5} lg={5}>
			<NumberInput labelText="Pressure" bind:value={pressure} hideSteppers />
		</Column>
		<Column sm={2} md={3} lg={3}>
			<Dropdown bind:selectedId={pressureUnit} items={pressureUnits} label="Unit" />
		</Column>
	</Row>

	<!-- H2O Content -->
	<Row class="mb-4">
		<Column sm={4} md={4} lg={4}>
			<NumberInput labelText="H₂O Content (mole fraction)" bind:value={h2oContent} hideSteppers />
		</Column>
	</Row>

	<!-- SO2 and O2 (for calculate-so3 mode) -->
	{#if mode === 'calculate-so3'}
		<Row class="mb-4">
			<Column sm={4} md={4} lg={4}>
				<NumberInput labelText="SO₂ Content (mole fraction)" bind:value={so2Content} hideSteppers />
			</Column>
			<Column sm={4} md={4} lg={4}>
				<NumberInput labelText="O₂ Content (mole fraction)" bind:value={o2Content} hideSteppers />
			</Column>
		</Row>
	{/if}

	<!-- SO3 Content (for direct-so3 mode) -->
	{#if mode === 'direct-so3'}
		<Row class="mb-4">
			<Column sm={4} md={4} lg={4}>
				<NumberInput labelText="SO₃ Content (mole fraction)" bind:value={so3Content} hideSteppers />
			</Column>
		</Row>
	{/if}

	<Row class="mt-4">
		<Column>
			<Button on:click={calculate}>Calculate</Button>
		</Column>
	</Row>

	{#if acidDewPoints}
		<!-- SO3 Conversion Result (only for calculate-so3 mode) -->
		{#if mode === 'calculate-so3' && calculatedSO3 !== null}
			<Row class="mt-4">
				<Column>
					<Tile>
						<h4>SO₃ Conversion:</h4>
						<div class="latex-step">{@html stepLatexSO3}</div>
					</Tile>
				</Column>
			</Row>
		{/if}

		<!-- Acid Dew Point Results -->
		<Row class="mt-4">
			<Column>
				<Tile>
					<h4>Acid Dew Point Results:</h4>
					{#if acidDewPoints.verhoff > 0}
						<p><strong>Verhoff:</strong> {acidDewPoints.verhoff.toFixed(2)} °C</p>
						<p><strong>Okkes:</strong> {acidDewPoints.okkes.toFixed(2)} °C</p>
						<p><strong>Zarenezhad:</strong> {acidDewPoints.zarenezhad.toFixed(2)} °C</p>
						<p class="note"><em>Note: All three correlations provide estimates. Average: {((acidDewPoints.verhoff + acidDewPoints.okkes + acidDewPoints.zarenezhad) / 3).toFixed(2)} °C</em></p>
					{:else}
						<p class="error">Error: H₂O and SO₃ content must be greater than zero!</p>
					{/if}
				</Tile>
			</Column>
		</Row>

		<!-- Calculation Steps -->
		{#if acidDewPoints.verhoff > 0}
			<Row class="mt-4">
				<Column>
					<Tile>
						<h4>Calculation Steps:</h4>
						<div class="latex-step">{@html stepLatexADP}</div>
					</Tile>
				</Column>
			</Row>
		{/if}
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

	p {
		margin: 0.5rem 0;
	}

	.note {
		margin-top: 1rem;
		color: #525252;
		font-size: 0.9rem;
	}

	.error {
		color: #da1e28;
		font-weight: 500;
	}
</style>
