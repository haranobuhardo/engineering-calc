<script lang="ts">
	import { siteConfig } from '$lib/nav';
	import { convertLength, convertFlowRate, convertVolume, convertPressure } from '$lib/convert';
	import {
		Grid,
		Row,
		Column,
		NumberInput,
		Select,
		SelectItem,
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

	let lengthUnits = [
		{ value: 'in', text: 'in' },
		{ value: 'ft', text: 'ft' },
		{ value: 'mm', text: 'mm' },
		{ value: 'm', text: 'm' }
	];

	let volumeUnits = [
		{ value: 'cc', text: 'cc' },
		{ value: 'ml', text: 'ml' },
		{ value: 'L', text: 'L' },
		{ value: 'm3', text: 'm3' },
		{ value: 'in3', text: 'in3' },
		{ value: 'ft3', text: 'ft3' }
	];

	let flowRateUnits = [
		{ value: 'lpm', text: 'NLPM' },
		{ value: 'lph', text: 'NLPH' },
		{ value: 'bpd', text: 'BPD' }
	];

	let pressureUnits = [
		{ value: 'psia', text: 'psia' },
		{ value: 'psig', text: 'psig' },
		{ value: 'bar', text: 'bar' },
		{ value: 'atm', text: 'atm' }
	];

	function calculateLagTime() {
		// 1. Calculate Volume in cc
		let volCC = 0;
		let lenM = 0;

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
		} else {
			volCC = convertVolume(volumeValue, volumeUnit);
		}

		resultVolume = volCC;

		// 2. Calculate Flow Rate in cc/s
		// convertFlowRate returns LPM (NLPM)
		// 1 LPM = 1000 cc/min = 1000/60 cc/s
		let flowLPM = convertFlowRate(flowRateValue, flowRateUnit);
		let flowCC_S = (flowLPM * 1000) / 60;

		// 3. Compressibility Factor Z (Pressure Ratio)
		// ratio of P_flowing / P_outlet (both absolute)
		let pInAbs = convertPressure(pressureInValue, pressureInUnit);
		let pOutAbs = convertPressure(pressureOutValue, pressureOutUnit);
		let z = pInAbs / pOutAbs;

		// 4. Lag Time
		// t = V/Q * Z * Lag + Add
		resultTime = (volCC / flowCC_S) * z * lagOrder + additionalTime;

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
			<Column sm={3} md={5} lg={5}>
				<NumberInput label="Outside Diameter (OD)" bind:value={odValue} />
			</Column>
			<Column sm={1} md={3} lg={3}>
				<Select bind:selected={odUnit} labelText="Unit">
					{#each lengthUnits as unit}
						<SelectItem value={unit.value} text={unit.text} />
					{/each}
				</Select>
			</Column>
		</Row>
		<Row class="mb-4 items-end">
			<Column sm={3} md={5} lg={5}>
				<NumberInput label="Wall Thickness" bind:value={wallValue} />
			</Column>
			<Column sm={1} md={3} lg={3}>
				<Select bind:selected={wallUnit} labelText="Unit">
					{#each lengthUnits as unit}
						<SelectItem value={unit.value} text={unit.text} />
					{/each}
				</Select>
			</Column>
		</Row>
		<Row class="mb-4 items-end">
			<Column sm={3} md={5} lg={5}>
				<NumberInput label="Length" bind:value={lengthValue} />
			</Column>
			<Column sm={1} md={3} lg={3}>
				<Select bind:selected={lengthUnit} labelText="Unit">
					{#each lengthUnits as unit}
						<SelectItem value={unit.value} text={unit.text} />
					{/each}
				</Select>
			</Column>
		</Row>
	{:else}
		<!-- Chamber Inputs -->
		<Row class="mb-4 items-end">
			<Column sm={3} md={5} lg={5}>
				<NumberInput label="Known Volume" bind:value={volumeValue} />
			</Column>
			<Column sm={1} md={3} lg={3}>
				<Select bind:selected={volumeUnit} labelText="Unit">
					{#each volumeUnits as unit}
						<SelectItem value={unit.value} text={unit.text} />
					{/each}
				</Select>
			</Column>
		</Row>
	{/if}

	<!-- Common Inputs -->
	<Row class="mb-4 items-end">
		<Column sm={3} md={5} lg={5}>
			<NumberInput label="Flow Rate" bind:value={flowRateValue} />
		</Column>
		<Column sm={1} md={3} lg={3}>
			<Select bind:selected={flowRateUnit} labelText="Unit">
				{#each flowRateUnits as unit}
					<SelectItem value={unit.value} text={unit.text} />
				{/each}
			</Select>
		</Column>
	</Row>

	<Row class="mb-4 items-end">
		<Column sm={3} md={5} lg={5}>
			<NumberInput label="Pressure (Flowing)" bind:value={pressureInValue} />
		</Column>
		<Column sm={1} md={3} lg={3}>
			<Select bind:selected={pressureInUnit} labelText="Unit">
				{#each pressureUnits as unit}
					<SelectItem value={unit.value} text={unit.text} />
				{/each}
			</Select>
		</Column>
	</Row>

	<Row class="mb-4 items-end">
		<Column sm={3} md={5} lg={5}>
			<NumberInput label="Pressure (Outlet)" bind:value={pressureOutValue} />
		</Column>
		<Column sm={1} md={3} lg={3}>
			<Select bind:selected={pressureOutUnit} labelText="Unit">
				{#each pressureUnits as unit}
					<SelectItem value={unit.value} text={unit.text} />
				{/each}
			</Select>
		</Column>
	</Row>

	<Row class="mb-4 items-end">
		<Column sm={3} md={5} lg={5}>
			<NumberInput label="First Order Lag" bind:value={lagOrder} />
		</Column>
	</Row>

	<Row class="mb-4 items-end">
		<Column sm={3} md={5} lg={5}>
			<NumberInput label="Additional Time (sec)" bind:value={additionalTime} />
		</Column>
	</Row>

	<Row class="mt-4">
		<Column>
			<Button on:click={calculateLagTime}>Calculate</Button>
		</Column>
	</Row>

	{#if calculated}
		<Row class="mt-8">
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
</style>
