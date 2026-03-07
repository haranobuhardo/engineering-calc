<script lang="ts">
	import { siteConfig } from '$lib/nav';
	import {
		convertLength,
		convertFlowRate,
		convertDensity,
		convertTemperature,
		convertThermalConductivity,
		convertSpecificHeat,
		lengthUnits,
		flowRateUnits,
		densityUnits,
		temperatureUnits,
		thermalConductivityUnits,
		specificHeatUnits
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

	let thermalConductivityValue = $state(0.04);
	let thermalConductivityUnit = $state('W/(m·K)');
	let lengthValue = $state(6);
	let lengthUnit = $state('m');
	let insulationThicknessValue = $state(0.336);
	let insulationThicknessUnit = $state('in');
	let tubeODValue = $state(0.25);
	let tubeODUnit = $state('in');
	let tubeThicknessValue = $state(0.035);
	let tubeThicknessUnit = $state('in');
	let flowRateValue = $state(3);
	let flowRateUnit = $state('lpm');
	let densityValue = $state(1);
	let densityUnit = $state('kg/m3');
	let specificHeatValue = $state(1000);
	let specificHeatUnit = $state('J/(kg·K)');
	let ambientTempValue = $state(35);
	let ambientTempUnit = $state('C');
	let systemTempValue = $state(125);
	let systemTempUnit = $state('C');

	let heatLoss = $state(0);
	let finalTemp = $state(0);
	let maxHeatLoss = $state(0);
	let maxLength = $state(0);
	let reachedAmbient = $state(false);
	let stepLatex = $state('');

	function calculateHeatLoss() {
		// Convert all inputs to SI units
		let k = convertThermalConductivity(thermalConductivityValue, thermalConductivityUnit); // W/(m·K)
		let length = convertLength(lengthValue, lengthUnit) / 1000; // Convert mm to m
		let inslThick = convertLength(insulationThicknessValue, insulationThicknessUnit) / 1000; // Convert mm to m
		let tubeOD = convertLength(tubeODValue, tubeODUnit) / 1000;  // Convert mm to m
		let tubeThickness = convertLength(tubeThicknessValue, tubeThicknessUnit) / 1000;// Convert mm to m
		let tubeDia = tubeOD-2*(tubeThickness)
		let flowRate = convertFlowRate(flowRateValue, flowRateUnit) / 1000 / 60; // Convert lpm to m³/s
		let density = convertDensity(densityValue, densityUnit); // kg/m³
		let c = convertSpecificHeat(specificHeatValue, specificHeatUnit); // J/(kg·K)
		let ambientTemp = convertTemperature(ambientTempValue, ambientTempUnit); // K
		let systemTemp = convertTemperature(systemTempValue, systemTempUnit); // K
		console.log(ambientTemp)
		// Calculate outer and inner diameters
		let OD = tubeDia + 2 * inslThick; // m (outer diameter of insulation)
		let ID = tubeDia; // m (tube outer diameter = insulation inner diameter)

		// Calculate heat loss through cylindrical insulation
		// Q = k * 2 * π * L * (T_ambient - T_system) / ln(OD/ID)
		let tempDiff = ambientTemp - systemTemp;
		heatLoss = k * 2 * Math.PI * length * tempDiff / Math.log(OD / ID); // W

		// Calculate maximum possible heat loss based on fluid energy content
		// Max Q = flow_rate * density * c * (T_ambient - T_system)
		maxHeatLoss = flowRate * density * c * tempDiff; // W

		// Check if heat loss exceeds maximum
		if (Math.abs(heatLoss) > Math.abs(maxHeatLoss)) {
			reachedAmbient = true;
			heatLoss = maxHeatLoss;
			finalTemp = ambientTemp;

			// Calculate length needed to reach ambient temperature
			// L_max = Q_max * ln(OD/ID) / (k * 2 * π * (T_ambient - T_system))
			maxLength = maxHeatLoss * Math.log(OD / ID) / (k * 2 * Math.PI * tempDiff); // m

			// Generate LaTeX Steps
			let latex = `
				\\textbf{Input Parameters:} \\\\[5pt]
				k = ${k.toFixed(4)} \\text{ W/(m} \\cdot \\text{K)}, \\quad L = ${length.toFixed(2)} \\text{ m} \\\\[3pt]
				t_{insulation} = ${(inslThick * 1000).toFixed(2)} \\text{ mm}, \\quad D_{tube} = ${(tubeDia * 1000).toFixed(2)} \\text{ mm} \\\\[3pt]
				Q_{flow} = ${(flowRate * 1000 * 60).toFixed(2)} \\text{ LPM}, \\quad \\rho = ${density.toFixed(1)} \\text{ kg/m}^3 \\\\[3pt]
				c_p = ${c.toFixed(0)} \\text{ J/(kg} \\cdot \\text{K)} \\\\[3pt]
				T_{ambient} = ${(ambientTemp - 273.15).toFixed(1)} ^\\circ \\text{C}, \\quad T_{system} = ${(systemTemp - 273.15).toFixed(1)} ^\\circ \\text{C} \\\\[10pt]

				\\textbf{Geometry:} \\\\[5pt]
				OD = D_{tube} + 2 \\times t_{insulation} = ${(tubeDia * 1000).toFixed(2)} + 2 \\times ${(inslThick * 1000).toFixed(2)} = ${(OD * 1000).toFixed(2)} \\text{ mm} \\\\[5pt]
				ID = D_{tube} = ${(ID * 1000).toFixed(2)} \\text{ mm} \\\\[10pt]

				\\textbf{Heat Loss Calculation:} \\\\[5pt]
				Q = \\frac{k \\cdot 2\\pi \\cdot L \\cdot (T_{ambient} - T_{system})}{\\ln(OD/ID)} \\\\[5pt]
				Q = \\frac{${k.toFixed(4)} \\times 2\\pi \\times ${length.toFixed(2)} \\times (${(ambientTemp - 273.15).toFixed(1)} - ${(systemTemp - 273.15).toFixed(1)})}{\\ln(${(OD * 1000).toFixed(2)}/${(ID * 1000).toFixed(2)})} \\\\[5pt]
				Q = ${heatLoss.toFixed(2)} \\text{ W} \\\\[10pt]

				\\textbf{Maximum Heat Loss:} \\\\[5pt]
				Q_{max} = Q_{flow} \\times \\rho \\times c_p \\times (T_{ambient} - T_{system}) \\\\[5pt]
				Q_{max} = ${(flowRate * 1000 * 60).toFixed(2)} \\times ${density.toFixed(1)} \\times ${c.toFixed(0)} \\times (${(ambientTemp - 273.15).toFixed(1)} - ${(systemTemp - 273.15).toFixed(1)}) \\\\[5pt]
				Q_{max} = ${maxHeatLoss.toFixed(2)} \\text{ W} \\\\[10pt]

				\\textbf{Result:} \\\\[5pt]
				|Q| > |Q_{max}| \\implies \\text{ Fluid reaches ambient temperature} \\\\[5pt]
				L_{max} = \\frac{Q_{max} \\cdot \\ln(OD/ID)}{k \\cdot 2\\pi \\cdot (T_{ambient} - T_{system})} = ${maxLength.toFixed(2)} \\text{ m} \\\\[5pt]
				T_{final} = T_{ambient} = ${(finalTemp - 273.15).toFixed(1)} ^\\circ \\text{C}
			`;

			stepLatex = katex.renderToString(latex, { displayMode: true, fleqn: true });
		} else {
			reachedAmbient = false;

			// Calculate final temperature
			// T_final = T_system + Q / (flow_rate * density * c)
			finalTemp = systemTemp + (heatLoss / (flowRate * density * c)); // K

			// Generate LaTeX Steps
			let latex = `
				\\textbf{Input Parameters:} \\\\[5pt]
				k = ${k.toFixed(4)} \\text{ W/(m} \\cdot \\text{K)}, \\quad L = ${length.toFixed(2)} \\text{ m} \\\\[3pt]
				t_{insulation} = ${(inslThick * 1000).toFixed(2)} \\text{ mm}, \\quad D_{tube} = ${(tubeDia * 1000).toFixed(2)} \\text{ mm} \\\\[3pt]
				Q_{flow} = ${(flowRate * 1000 * 60).toFixed(2)} \\text{ LPM}, \\quad \\rho = ${density.toFixed(1)} \\text{ kg/m}^3 \\\\[3pt]
				c_p = ${c.toFixed(0)} \\text{ J/(kg} \\cdot \\text{K)} \\\\[3pt]
				T_{ambient} = ${(ambientTemp - 273.15).toFixed(1)} ^\\circ \\text{C}, \\quad T_{system} = ${(systemTemp - 273.15).toFixed(1)} ^\\circ \\text{C} \\\\[10pt]

				\\textbf{Geometry:} \\\\[5pt]
				OD = D_{tube} + 2 \\times t_{insulation} = ${(tubeDia * 1000).toFixed(2)} + 2 \\times ${(inslThick * 1000).toFixed(2)} = ${(OD * 1000).toFixed(2)} \\text{ mm} \\\\[5pt]
				ID = D_{tube} = ${(ID * 1000).toFixed(2)} \\text{ mm} \\\\[10pt]

				\\textbf{Heat Loss Calculation:} \\\\[5pt]
				Q = \\frac{k \\cdot 2\\pi \\cdot L \\cdot (T_{ambient} - T_{system})}{\\ln(OD/ID)} \\\\[5pt]
				Q = \\frac{${k.toFixed(4)} \\times 2\\pi \\times ${length.toFixed(2)} \\times (${(ambientTemp - 273.15).toFixed(1)} - ${(systemTemp - 273.15).toFixed(1)})}{\\ln(${(OD * 1000).toFixed(2)}/${(ID * 1000).toFixed(2)})} \\\\[5pt]
				Q = ${heatLoss.toFixed(2)} \\text{ W} \\\\[10pt]

				\\textbf{Maximum Heat Loss:} \\\\[5pt]
				Q_{max} = Q_{flow} \\times \\rho \\times c_p \\times (T_{ambient} - T_{system}) \\\\[5pt]
				Q_{max} = ${(flowRate * 1000 * 60).toFixed(2)} \\times ${density.toFixed(1)} \\times ${c.toFixed(0)} \\times (${(ambientTemp - 273.15).toFixed(1)} - ${(systemTemp - 273.15).toFixed(1)}) \\\\[5pt]
				Q_{max} = ${maxHeatLoss.toFixed(2)} \\text{ W} \\\\[10pt]

				\\textbf{Result:} \\\\[5pt]
				|Q| < |Q_{max}| \\implies \\text{ Fluid remains above ambient} \\\\[5pt]
				T_{final} = T_{system} + \\frac{Q}{Q_{flow} \\times \\rho \\times c_p} \\\\[5pt]
				T_{final} = ${(systemTemp - 273.15).toFixed(1)} + \\frac{${heatLoss.toFixed(2)}}{${(flowRate * 1000 * 60).toFixed(2)} \\times ${density.toFixed(1)} \\times ${c.toFixed(0)}} \\\\[5pt]
				T_{final} = ${(finalTemp - 273.15).toFixed(2)} ^\\circ \\text{C}
			`;

			stepLatex = katex.renderToString(latex, { displayMode: true, fleqn: true });
		}
	}
</script>

<svelte:head>
	<title>{siteConfig.title} - Tube Heat Loss</title>
	<meta name={siteConfig.description} content={siteConfig.description} />
</svelte:head>

<Grid>
	<Row>
		<Column>
			<h1 class="landing-page__heading">Tube Heat Loss Calculator</h1>
			<p class="description">Calculate heat loss through insulated tubing and final fluid temperature</p>
		</Column>
	</Row>

	<!-- Thermal Conductivity (k) -->
	<Row class="mb-4 items-end">
		<Column sm={2} md={5} lg={5}>
			<NumberInput labelText="Thermal Conductivity (k)" bind:value={thermalConductivityValue} hideSteppers />
		</Column>
		<Column sm={2} md={3} lg={3}>
			<Dropdown bind:selectedId={thermalConductivityUnit} items={thermalConductivityUnits} label="Unit" />
		</Column>
	</Row>

	<!-- Tube Length -->
	<Row class="mb-4 items-end">
		<Column sm={2} md={5} lg={5}>
			<NumberInput labelText="Tube Length (L)" bind:value={lengthValue} hideSteppers />
		</Column>
		<Column sm={2} md={3} lg={3}>
			<Dropdown bind:selectedId={lengthUnit} items={lengthUnits} label="Unit" />
		</Column>
	</Row>

	<!-- Insulation Thickness -->
	<Row class="mb-4 items-end">
		<Column sm={2} md={5} lg={5}>
			<NumberInput labelText="Insulation Thickness" bind:value={insulationThicknessValue} hideSteppers />
		</Column>
		<Column sm={2} md={3} lg={3}>
			<Dropdown bind:selectedId={insulationThicknessUnit} items={lengthUnits} label="Unit" />
		</Column>
	</Row>

	<!-- Tube Diameter OD -->
	<Row class="mb-4 items-end">
		<Column sm={2} md={5} lg={5}>
			<NumberInput labelText="Tube Diameter (OD)" bind:value={tubeODValue} hideSteppers />
		</Column>
		<Column sm={2} md={3} lg={3}>
			<Dropdown bind:selectedId={tubeODUnit} items={lengthUnits} label="Unit" />
		</Column>
	</Row>

	<!-- Tube Thickness -->
	<Row class="mb-4 items-end">
		<Column sm={2} md={5} lg={5}>
			<NumberInput labelText="Tube Thickness" bind:value={tubeThicknessValue} hideSteppers />
		</Column>
		<Column sm={2} md={3} lg={3}>
			<Dropdown bind:selectedId={tubeThicknessUnit} items={lengthUnits} label="Unit" />
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

	<!-- Density -->
	<Row class="mb-4 items-end">
		<Column sm={2} md={5} lg={5}>
			<NumberInput labelText="Fluid Density (ρ)" bind:value={densityValue} hideSteppers />
		</Column>
		<Column sm={2} md={3} lg={3}>
			<Dropdown bind:selectedId={densityUnit} items={densityUnits} label="Unit" />
		</Column>
	</Row>

	<!-- Specific Heat Capacity -->
	<Row class="mb-4 items-end">
		<Column sm={2} md={5} lg={5}>
			<NumberInput labelText="Specific Heat Capacity (cp)" bind:value={specificHeatValue} hideSteppers />
		</Column>
		<Column sm={2} md={3} lg={3}>
			<Dropdown bind:selectedId={specificHeatUnit} items={specificHeatUnits} label="Unit" />
		</Column>
	</Row>

	<!-- Ambient Temperature -->
	<Row class="mb-4 items-end">
		<Column sm={2} md={5} lg={5}>
			<NumberInput labelText="Ambient Temperature" bind:value={ambientTempValue} hideSteppers />
		</Column>
		<Column sm={2} md={3} lg={3}>
			<Dropdown bind:selectedId={ambientTempUnit} items={temperatureUnits} label="Unit" />
		</Column>
	</Row>

	<!-- System Temperature -->
	<Row class="mb-4 items-end">
		<Column sm={2} md={5} lg={5}>
			<NumberInput labelText="System Temperature" bind:value={systemTempValue} hideSteppers />
		</Column>
		<Column sm={2} md={3} lg={3}>
			<Dropdown bind:selectedId={systemTempUnit} items={temperatureUnits} label="Unit" />
		</Column>
	</Row>

	<Row class="mt-4">
		<Column>
			<Button on:click={calculateHeatLoss}>Calculate</Button>
		</Column>
	</Row>

	{#if heatLoss !== 0}
		<Row class="mt-4">
			<Column>
				<Tile>
					<h4>Results:</h4>
					{#if reachedAmbient}
						<p><strong>Heat Loss:</strong> {heatLoss.toFixed(2)} W</p>
						<p><strong>Maximum Heat Loss:</strong> {maxHeatLoss.toFixed(2)} W</p>
						<p><strong>Final Temperature:</strong> {(finalTemp - 273.15).toFixed(1)} °C (Ambient)</p>
						<p><strong>Length to Reach Ambient:</strong> {maxLength.toFixed(4)} m</p>
						<p class="warning">⚠️ The fluid reaches ambient temperature before the end of the tube!</p>
					{:else}
						<p><strong>Heat Loss:</strong> {heatLoss.toFixed(2)} W</p>
						<p><strong>Maximum Heat Loss:</strong> {maxHeatLoss.toFixed(2)} W</p>
						<p><strong>Final Temperature:</strong> {(finalTemp - 273.15).toFixed(2)} °C</p>
						<!-- <p><strong>Temperature Drop:</strong> {((systemTempValue - ambientTempValue) - (finalTemp - 273.15 - (ambientTemp - 273.15))).toFixed(2)} {(systemTempUnit === 'C' || systemTempUnit === '°C' ? '°C' : systemTempUnit)}</p> -->
					{/if}
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

	.warning {
		color: #da1e28;
		font-weight: 500;
		margin-top: 1rem;
	}

	h4 {
		margin-bottom: 1rem;
		font-weight: 500;
	}

	p {
		margin: 0.5rem 0;
	}
</style>
