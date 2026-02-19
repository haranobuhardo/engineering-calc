<script lang="ts">
	import { siteConfig } from '$lib/nav';
	import { convertLength, convertFlowRate, convertVolume, convertPressure, lengthUnits, volumeUnits, flowRateUnits, pressureUnits } from '$lib/convert';
	import katex from 'katex';
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

	let mode = $state('tube'); // 'tube' or 'chamber'

	// Tube inputs
	let odValue = $state(0.25);
	let odUnit = $state('in');
	let wallValue = $state(0.035);
	let wallUnit = $state('in');
	let lengthValue = $state(6);
	let lengthUnit = $state('m');

	// Chamber inputs
	let volumeValue = $state(100);
	let volumeUnit = $state('cc');

	// Common inputs
	let flowRateValue = $state(1);
	let flowRateUnit = $state('lpm');
	let pressureInValue = $state(29.4);
	let pressureInUnit = $state('psia');
	let pressureOutValue = $state(14.7);
	let pressureOutUnit = $state('psia');
	let lagOrder = $state(1);
	let additionalTime = $state(0);

	// Outputs
	let resultVolume = $state(0);
	let resultTime = $state(0);
	let resultVelocity = $state(0);
	let calculated = $state(false);

	// LaTeX Calculation Steps (HTML strings)
	let stepLatex = $state('');

	function calculateLagTime() {
		// 1. Calculate Volume in cc
		let volCC = 0;
		let lenM = 0;
		let latex = '';

		if (mode === 'tube') {
			let odMM = convertLength(odValue, odUnit);
			let wallMM = convertLength(wallValue, wallUnit);
			let lenMM = convertLength(lengthValue, lengthUnit);
			lenM = lenMM / 1000;

			let idMM = odMM - 2 * wallMM;
			if (idMM < 0) {
				alert('Inside Diameter is negative! Check OD and Wall Thickness.');
				return;
			}
			let idCm = idMM / 10;
			let areaCm2 = (Math.PI * Math.pow(idCm, 2)) / 4;
			let lenCm = lenMM / 10;
			volCC = areaCm2 * lenCm;

			latex += `V = \\frac{\\pi \\times (ID_{cm})^2}{4} \\times L_{cm} = \\frac{\\pi \\times (${idCm.toFixed(3)})^2}{4} \\times ${lenCm.toFixed(1)} = ${volCC.toFixed(2)} \\text{ cc} \\\\[10pt]`;
		} else {
			volCC = convertVolume(volumeValue, volumeUnit);
			latex += `V = ${volumeValue} \\text{ ${volumeUnit}} = ${volCC.toFixed(2)} \\text{ cc} \\\\[10pt]`;
		}

		resultVolume = volCC;

		// 2. Calculate Flow Rate in cc/s
		// convertFlowRate returns LPM (NLPM)
		// 1 LPM = 1000 cc/min = 1000/60 cc/s
		let flowLPM = convertFlowRate(flowRateValue, flowRateUnit);
		let flowCC_S = (flowLPM * 1000) / 60;
		
		latex += `Q = ${flowRateValue} \\text{ ${flowRateUnit}} = ${flowCC_S.toFixed(2)} \\text{ cc/s} \\\\[10pt]`;

		// 3. Compressibility Factor Z (Pressure Ratio)
		// ratio of P_flowing / P_outlet (both absolute)
		let pInAbs = convertPressure(pressureInValue, pressureInUnit);
		let pOutAbs = convertPressure(pressureOutValue, pressureOutUnit);
		let z = pInAbs / pOutAbs;

		latex += `Z = \\frac{P_{in}}{P_{out}} = \\frac{${pInAbs.toFixed(2)}}{${pOutAbs.toFixed(2)}} = ${z.toFixed(3)} \\\\[10pt]`;

		// 4. Lag Time
		// t = V/Q * Z * Lag + Add
		resultTime = (volCC / flowCC_S) * z * lagOrder + additionalTime;

		latex += `t = \\frac{V}{Q} \\times Z \\times \\text{Lag} + t_{add} = \\frac{${volCC.toFixed(2)}}{${flowCC_S.toFixed(2)}} \\times ${z.toFixed(3)} \\times ${lagOrder} + ${additionalTime} = ${resultTime.toFixed(2)} \\text{ s}`;

		stepLatex = katex.renderToString(latex, { displayMode: true, fleqn: true });

		// 5. Velocity (only relevant for tube really, but we cancalc based on length/time?)
		// Requirement says: Output volume, velocity, calculated lag time.
		// If tube, Velocity = Length / Time is effectively transport speed?
		// Or Velocity = Q_actual / Area.
		// User requirement simply says "velocity". I will calc Q_actual / Area for Tube, or N/A for Chamber?
		// Actually, simpler is Length / Time if we have length.
		// For chamber, velocity isn't really standard, but maybe residence time logic?
		// Let's settle on Q_actual / Area for Tube.
		// Q_actual = Q_std * (P_std / P_flowing) ... wait, Z = P_flowing / P_outlet.
		// Let's use the simplest Velocity = Length / LagTime (if Tube).
		if (mode === 'tube' && resultTime > 0) {
			resultVelocity = lenM / resultTime;
		} else {
			resultVelocity = 0;
		}

		calculated = true;
	}
</script>

<svelte:head>
	<title>{siteConfig.title} - Lag Time</title>
	<meta name={siteConfig.description} content={siteConfig.description} />
</svelte:head>

<Grid>
	<Row>
		<Column>
			<h1 class="landing-page__heading">Lag Time Calculator</h1>
		</Column>
	</Row>

	<!-- Mode Selection -->
	<Row class="mb-4">
		<Column>
			<RadioButtonGroup name="mode-group" bind:selected={mode}>
				<RadioButton value="tube" labelText="Transportation Tube" />
				<RadioButton value="chamber" labelText="Known Volume Chamber" />
			</RadioButtonGroup>
		</Column>
	</Row>

	{#if mode === 'tube'}
		<!-- Tube Inputs -->
		<Row class="mb-4 items-end">
			<Column sm={2} md={5} lg={5}>
				<NumberInput labelText="Outside Diameter (OD)" bind:value={odValue} hideSteppers />
			</Column>
			<Column sm={2} md={3} lg={3}>
<Dropdown bind:selectedId={odUnit} items={lengthUnits} label="Unit" />
			</Column>
		</Row>
		<Row class="mb-4 items-end">
			<Column sm={2} md={5} lg={5}>
				<NumberInput labelText="Wall Thickness (t)" bind:value={wallValue} hideSteppers />
			</Column>
			<Column sm={2} md={3} lg={3}>
<Dropdown bind:selectedId={wallUnit} items={lengthUnits} label="Unit" />
			</Column>
		</Row>
		<Row class="mb-4 items-end">
			<Column sm={2} md={5} lg={5}>
				<NumberInput labelText="Length (L)" bind:value={lengthValue} hideSteppers />
			</Column>
			<Column sm={2} md={3} lg={3}>
<Dropdown bind:selectedId={lengthUnit} items={lengthUnits} label="Unit" />
			</Column>
		</Row>
	{:else}
		<!-- Chamber Inputs -->
		<Row class="mb-4 items-end">
			<Column sm={2} md={5} lg={5}>
				<NumberInput labelText="Known Volume (V)" bind:value={volumeValue} hideSteppers />
			</Column>
			<Column sm={2} md={3} lg={3}>
<Dropdown bind:selectedId={volumeUnit} items={volumeUnits} label="Unit" />
			</Column>
		</Row>
	{/if}

	<!-- Common Inputs -->
	<Row class="mb-4 items-end">
		<Column sm={2} md={5} lg={5}>
			<NumberInput labelText="Flow Rate (Q)" bind:value={flowRateValue} hideSteppers />
		</Column>
		<Column sm={2} md={3} lg={3}>
<Dropdown bind:selectedId={flowRateUnit} items={flowRateUnits} label="Unit" />
		</Column>
	</Row>

	<Row class="mb-4 items-end">
		<Column sm={2} md={5} lg={5}>
			<NumberInput labelText="Pressure (Flowing) (Pin)" bind:value={pressureInValue} hideSteppers />
		</Column>
		<Column sm={2} md={3} lg={3}>
<Dropdown bind:selectedId={pressureInUnit} items={pressureUnits} label="Unit" />
		</Column>
	</Row>

	<Row class="mb-4 items-end">
		<Column sm={2} md={5} lg={5}>
			<NumberInput labelText="Pressure (Outlet) (Pout)" bind:value={pressureOutValue} hideSteppers />
		</Column>
		<Column sm={2} md={3} lg={3}>
<Dropdown bind:selectedId={pressureOutUnit} items={pressureUnits} label="Unit" />
		</Column>
	</Row>

	<Row class="mb-4 items-end">
		<Column sm={4} md={5} lg={5}>
			<NumberInput labelText="First Order Lag (Lag)" bind:value={lagOrder} hideSteppers />
		</Column>
	</Row>

	<Row class="mb-4 items-end">
		<Column sm={4} md={5} lg={5}>
			<NumberInput labelText="Additional Time (t_add) in sec" bind:value={additionalTime} hideSteppers />
		</Column>
	</Row>

	<Row class="mt-4">
		<Column>
			<Button on:click={calculateLagTime}>Calculate</Button>
		</Column>
	</Row>

	{#if calculated}
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
					<p>Volume: <strong>{resultVolume.toFixed(2)} cc</strong></p>
					{#if mode === 'tube'}
						<p>Velocity: <strong>{resultVelocity.toFixed(2)} m/s</strong></p>
					{/if}
					<p>Lag Time: <strong>{resultTime.toFixed(2)} s</strong></p>
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
