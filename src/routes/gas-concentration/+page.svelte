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
		Button,
		Tile,
		RadioButtonGroup,
		RadioButton,
		Dropdown
	} from 'carbon-components-svelte';

	import katex from 'katex';
	import 'katex/dist/katex.min.css';

	// Conversion mode
	let mode = $state('ppmv-to-mgm3'); // 'ppmv-to-mgm3' or 'mgm3-to-ppmv'

	// Condition presets
	let condition = $state('SATP'); // 'SATP', 'NTP', 'STP', 'Other'
	
	// Temperature and pressure (will be set based on condition)
	let temperature = $state(25); // °C
	let temperatureUnit = $state('C');
	let pressure = $state(100); // kPa
	let pressureUnit = $state('kPa');

	// Molecule selection
	let selectedMolecule = $state('SO2');
	let customMolWeight = $state(64.066);

	// Input value
	let inputValue = $state(100);

	// Results
	let result = $state<number | null>(null);
	let percentVol = $state<number | null>(null);
	let molarVolume = $state<number | null>(null);
	let stepLatex = $state('');

	// Predefined conditions
	const conditions = {
		'SATP': { temp: 25, tempUnit: 'C', pressure: 100, pressureUnit: 'kPa', label: 'SATP (25°C, 100 kPa)' },
		'NTP': { temp: 20, tempUnit: 'C', pressure: 101.325, pressureUnit: 'kPa', label: 'NTP (20°C, 101.325 kPa)' },
		'STP': { temp: 0, tempUnit: 'C', pressure: 101.325, pressureUnit: 'kPa', label: 'STP (0°C, 101.325 kPa)' },
		'Other': { temp: 25, tempUnit: 'C', pressure: 100, pressureUnit: 'kPa', label: 'Other' }
	};

	// Common molecules with molecular weights (g/mol)
	const molecules = [
		{ id: 'SO2', text: 'SO₂ (64.066 g/mol)', molWeight: 64.066 },
		{ id: 'SO3', text: 'SO₃ (80.066 g/mol)', molWeight: 80.066 },
		{ id: 'NO2', text: 'NO₂ (46.006 g/mol)', molWeight: 46.006 },
		{ id: 'CO2', text: 'CO₂ (44.01 g/mol)', molWeight: 44.01 },
		{ id: 'CO', text: 'CO (28.011 g/mol)', molWeight: 28.011 },
		{ id: 'HCl', text: 'HCl (36.461 g/mol)', molWeight: 36.461 },
		{ id: 'H2S', text: 'H₂S (34.082 g/mol)', molWeight: 34.082 },
		{ id: 'H2O', text: 'H₂O (18.015 g/mol)', molWeight: 18.015 },
		{ id: 'CS2', text: 'CS₂ (76.131 g/mol)', molWeight: 76.131 },
		{ id: 'Cl2', text: 'Cl₂ (70.906 g/mol)', molWeight: 70.906 },
		{ id: 'ClO2', text: 'ClO₂ (67.452 g/mol)', molWeight: 67.452 },
		{ id: 'Other', text: 'Other (custom)', molWeight: 0 }
	];

	const conditionItems = Object.entries(conditions).map(([key, value]) => ({
		id: key,
		text: value.label
	}));

	// Update temperature and pressure when condition changes
	$effect(() => {
		if (condition !== 'Other') {
			temperature = conditions[condition].temp;
			temperatureUnit = conditions[condition].tempUnit;
			pressure = conditions[condition].pressure;
			pressureUnit = conditions[condition].pressureUnit;
		}
	});

	// Get molecular weight
	function getMolecularWeight(): number {
		if (selectedMolecule === 'Other') {
			return customMolWeight;
		}
		const molecule = molecules.find(m => m.id === selectedMolecule);
		return molecule ? molecule.molWeight : 64.066;
	}

	function calculate() {
		const R = 8.314; // L·kPa/(mol·K)
		const T = convertTemperature(temperature, temperatureUnit); // Convert to Kelvin
		const P_psia = convertPressure(pressure, pressureUnit); // Convert to psia first
		const P = P_psia * 6.894757; // Convert psia to kPa

		// Calculate molar volume
		molarVolume = (R * T) / P; // L/mol

		const molWeight = getMolecularWeight(); // g/mol

		if (mode === 'ppmv-to-mgm3') {
			// Convert ppmv to mg/m³
			// mg/m³ = ppmv × mol wt / molar volume
			result = (inputValue * molWeight) / molarVolume;
			percentVol = null;

			let latex = `
				\\textbf{Molar Volume:} \\\\[5pt]
				V_m = \\frac{R \\times T}{P} = \\frac{8.314 \\times ${T.toFixed(2)}}{${P.toFixed(3)}} = ${molarVolume.toFixed(4)} \\text{ L/mol} \\\\[10pt]

				\\textbf{Conversion:} \\\\[5pt]
				\\text{mg/m}^3 = \\frac{\\text{ppmv} \\times M_w}{V_m} \\\\[5pt]
				\\text{mg/m}^3 = \\frac{${inputValue.toFixed(2)} \\times ${molWeight.toFixed(3)}}{${molarVolume.toFixed(4)}} = ${result.toFixed(4)} \\text{ mg/m}^3
			`;
			stepLatex = katex.renderToString(latex, { displayMode: true, fleqn: true });
		} else {
			// Convert mg/m³ to ppmv
			// ppmv = mg/m³ × molar volume / mol wt
			result = (inputValue * molarVolume) / molWeight;
			percentVol = result / 10000; // ppmv / 10^4

			let latex = `
				\\textbf{Molar Volume:} \\\\[5pt]
				V_m = \\frac{R \\times T}{P} = \\frac{8.314 \\times ${T.toFixed(2)}}{${P.toFixed(3)}} = ${molarVolume.toFixed(4)} \\text{ L/mol} \\\\[10pt]

				\\textbf{Conversion:} \\\\[5pt]
				\\text{ppmv} = \\frac{\\text{mg/m}^3 \\times V_m}{M_w} \\\\[5pt]
				\\text{ppmv} = \\frac{${inputValue.toFixed(2)} \\times ${molarVolume.toFixed(4)}}{${molWeight.toFixed(3)}} = ${result.toFixed(4)} \\text{ ppmv} \\\\[10pt]

				\\textbf{Volume Percent:} \\\\[5pt]
				\\%\\text{vol} = \\frac{\\text{ppmv}}{10^4} = \\frac{${result.toFixed(4)}}{10000} = ${percentVol.toFixed(6)} \\%\\text{vol}
			`;
			stepLatex = katex.renderToString(latex, { displayMode: true, fleqn: true });
		}
	}
</script>

<svelte:head>
	<title>{siteConfig.title} - Gas Concentration Conversion</title>
	<meta name={siteConfig.description} content={siteConfig.description} />
</svelte:head>

<Grid>
	<Row>
		<Column>
			<h1 class="landing-page__heading">Gas Concentration Conversion</h1>
			<p class="description">Convert between ppmv and mg/m³ for gas concentrations</p>
		</Column>
	</Row>

	<!-- Conversion Mode Selection -->
	<Row class="mb-4">
		<Column>
			<RadioButtonGroup bind:selected={mode} legendText="Conversion Mode">
				<RadioButton value="ppmv-to-mgm3" labelText="ppmv to mg/m³" />
				<RadioButton value="mgm3-to-ppmv" labelText="mg/m³ to ppmv" />
			</RadioButtonGroup>
		</Column>
	</Row>

	<!-- Condition Selection -->
	<Row class="mb-4">
		<Column sm={4} md={4} lg={4}>
			<Dropdown bind:selectedId={condition} items={conditionItems} label="Condition" />
		</Column>
	</Row>

	<!-- Temperature and Pressure -->
	<Row class="mb-4 items-end">
		<Column sm={2} md={2} lg={2}>
			<NumberInput 
				labelText="Temperature" 
				bind:value={temperature} 
				hideSteppers 
				disabled={condition !== 'Other'}
			/>
		</Column>
		<Column sm={2} md={2} lg={2}>
			<Dropdown 
				bind:selectedId={temperatureUnit} 
				items={temperatureUnits} 
				label="Unit"
				disabled={condition !== 'Other'}
			/>
		</Column>
		<Column sm={2} md={2} lg={2}>
			<NumberInput 
				labelText="Pressure" 
				bind:value={pressure} 
				hideSteppers 
				disabled={condition !== 'Other'}
			/>
		</Column>
		<Column sm={2} md={2} lg={2}>
			<Dropdown 
				bind:selectedId={pressureUnit} 
				items={pressureUnits} 
				label="Unit"
				disabled={condition !== 'Other'}
			/>
		</Column>
	</Row>

	<!-- Molecule Selection -->
	<Row class="mb-4">
		<Column sm={4} md={4} lg={4}>
			<Dropdown bind:selectedId={selectedMolecule} items={molecules} label="Gas Molecule" />
		</Column>
	</Row>

	<!-- Molecular Weight -->
	{#if selectedMolecule === 'Other'}
	<Row class="mb-4">
    	<Column sm={4} md={4} lg={4}>
    		<NumberInput
    			labelText="Molecular Weight (g/mol)"
    			bind:value={customMolWeight}
    			hideSteppers
    		/>
    	</Column>
	</Row>
	{/if}

	<!-- Input Concentration -->
	<Row class="mb-4">
		<Column sm={4} md={4} lg={4}>
			<NumberInput
				labelText={mode === 'ppmv-to-mgm3' ? "Concentration (ppmv)" : "Concentration (mg/m³)"}
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
					<h4>Result:</h4>
					<p class="result-text">
						{result.toFixed(4)} {mode === 'ppmv-to-mgm3' ? 'mg/m³' : 'ppmv'}
					</p>
					{#if percentVol !== null}
						<p class="result-secondary">
							<strong>Volume Percent:</strong> {percentVol.toFixed(6)} %vol
						</p>
					{/if}
					<p class="result-info">
						<strong>Molar Volume:</strong> {molarVolume.toFixed(4)} L/mol<br>
						<strong>Molecular Weight:</strong> {getMolecularWeight().toFixed(3)} g/mol
					</p>
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

	.result-text {
		font-size: 1.5rem;
		font-weight: 600;
		margin-bottom: 0.5rem;
	}

	.result-secondary {
		font-size: 1.1rem;
		margin: 0.5rem 0;
	}

	.result-info {
		margin-top: 1rem;
		padding-top: 1rem;
		border-top: 1px solid #e0e0e0;
		font-size: 0.95rem;
		color: #525252;
	}
</style>
