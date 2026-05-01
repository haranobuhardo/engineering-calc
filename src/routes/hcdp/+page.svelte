<script lang="ts">
	import { siteConfig } from '$lib/nav';
	import { pressureUnits } from '$lib/convert';
	import {
		Grid,
		Row,
		Column,
		NumberInput,
		Dropdown,
		Button,
		Tile,
		Loading
	} from 'carbon-components-svelte';
	import { AddFilled, SubtractFilled } from 'carbon-icons-svelte';

	interface CompositionEntry {
		id: number;
		fluid: string;
		moleFraction: number;
	}

	const supportedFluids = [
		'Methane',
		'Ethane',
		'Propane',
		'IsoButane',
		'n-Butane',
		'Isopentane',
		'n-Pentane',
		'Hexane',
		'Heptane',
		'Octane',
		'Nonane',
		'Decane',
		'CarbonDioxide',
		'Nitrogen',
		'Water',
		'HydrogenSulfide',
		'Oxygen',
		'Hydrogen'
	];

	const fluidItems = supportedFluids.map((f) => ({ id: f, text: f }));

	// Engine state
	let engineReady = $state(false);
	let engineError: string | null = $state(null);

	// Calculator inputs
	let pressure = $state(50);
	let pressureUnit = $state('bar');
	let nextId = $state(4);

	let composition = $state<CompositionEntry[]>([
		{ id: 1, fluid: 'Methane', moleFraction: 0.9 },
		{ id: 2, fluid: 'Ethane', moleFraction: 0.07 },
		{ id: 3, fluid: 'Propane', moleFraction: 0.03 }
	]);

	// Results
	let dewPointC: number | null = $state(null);
	let dewPointF: number | null = $state(null);
	let errorMsg: string | null = $state(null);
	let normalizedComposition: CompositionEntry[] = $state([]);

	// Derived
	let totalFraction = $derived(composition.reduce((s, r) => s + r.moleFraction, 0));

	// Load CoolProp WASM lazily on mount
	import { onMount } from 'svelte';

	onMount(async () => {
		try {
			const coolpropUrl = '/coolprop.js';
			const CoolPropModule = await import(
				/* @vite-ignore */ coolpropUrl
			);
			const coolprop = await CoolPropModule.default();
			(window as any).CoolProp = coolprop;
			engineReady = true;
		} catch (err) {
			console.error('CoolProp WASM load failed:', err);
			engineError = 'Fatal EoS Error: WASM load failed.';
		}
	});

	// Composition helpers
	function addRow() {
		composition = [
			...composition,
			{ id: nextId++, fluid: 'Methane', moleFraction: 0 }
		];
	}

	function removeRow(id: number) {
		if (composition.length <= 1) return;
		composition = composition.filter((row) => row.id !== id);
	}

	function updateFluid(id: number, fluid: string) {
		composition = composition.map((row) => (row.id === id ? { ...row, fluid } : row));
	}

	function updateFraction(id: number, moleFraction: number) {
		composition = composition.map((row) =>
			row.id === id ? { ...row, moleFraction } : row
		);
	}

	function getNormalized(): CompositionEntry[] {
		const total = composition.reduce((sum, row) => sum + row.moleFraction, 0);
		if (total === 0) return composition;
		return composition.map((row) => ({
			...row,
			moleFraction: row.moleFraction / total
		}));
	}

	function buildGasString(norm: CompositionEntry[]): string {
		const parts = norm
			.filter((row) => row.moleFraction > 0)
			.map((row) => `${row.fluid}[${row.moleFraction.toFixed(6)}]`);
		return `PR::${parts.join('&')}`;
	}

	function convertToPa(value: number, unit: string): number {
		switch (unit) {
			case 'Pa':
				return value;
			case 'kPa':
				return value * 1000;
			case 'bar':
				return value * 100000;
			case 'atm':
				return value * 101325;
			case 'psia':
				return value * 6894.757;
			case 'psig':
				return (value + 14.7) * 6894.757;
			default:
				return value;
		}
	}

	function calculate() {
		dewPointC = null;
		dewPointF = null;
		errorMsg = null;
		normalizedComposition = [];

		if (!engineReady) {
			errorMsg = 'EoS engine is not loaded yet. Please wait...';
			return;
		}

		if (totalFraction <= 0) {
			errorMsg = 'Total mole fraction is zero. Enter at least one component.';
			return;
		}

		const norm = getNormalized();
		normalizedComposition = norm;
		const gasString = buildGasString(norm);
		const pressurePa = convertToPa(pressure, pressureUnit);

		try {
			const coolprop = (window as any).CoolProp;
			const tKelvin = coolprop.PropsSI('T', 'P', pressurePa, 'Q', 1, gasString);

			if (tKelvin <= 0 || !isFinite(tKelvin)) {
				errorMsg = 'CoolProp returned an invalid temperature. Check your inputs.';
				return;
			}

			dewPointC = tKelvin - 273.15;
			dewPointF = dewPointC * 1.8 + 32;
		} catch (e: unknown) {
			const msg = typeof e === 'string' ? e : (e as Error)?.message || 'Unknown error';
			errorMsg = `Flash calculation failed: ${msg}`;
		}
	}
</script>

<svelte:head>
	<title>{siteConfig.title} - HCDP Calculator</title>
	<meta name={siteConfig.description} content={siteConfig.description} />
</svelte:head>

{#if !engineReady && !engineError}
	<Loading description="Loading EoS engine..." withOverlay={false} />
{:else if engineError}
	<Tile>
		<h4 class="error">System Failure</h4>
		<p class="error">{engineError}</p>
	</Tile>
{:else}
	<Grid>
		<Row>
			<Column>
				<h1 class="landing-page__heading">Hydrocarbon Dew Point Calculator</h1>
				<p class="description">
					Calculate hydrocarbon dew point using Peng-Robinson EOS via CoolProp
				</p>
			</Column>
		</Row>

		<!-- Pressure Input -->
		<Row class="mb-4 items-end">
			<Column sm={2} md={5} lg={5}>
				<NumberInput labelText="Pressure" bind:value={pressure} hideSteppers />
			</Column>
			<Column sm={2} md={3} lg={3}>
				<Dropdown bind:selectedId={pressureUnit} items={pressureUnits} label="Unit" />
			</Column>
		</Row>

		<!-- Gas Composition -->
		<Row class="mb-2">
			<Column>
				<h4 class="section-heading">Gas Composition</h4>
			</Column>
		</Row>

		{#each composition as row, i (row.id)}
			<Row class="mb-4 items-end">
				<Column sm={2} md={5} lg={5}>
					<Dropdown
						selectedId={row.fluid}
						items={fluidItems}
						label={i === 0 ? 'Component Name' : ''}
						on:select={(e) => updateFluid(row.id, e.detail.selectedId)}
					/>
				</Column>
				<Column sm={2} md={3} lg={3}>
					<NumberInput
						labelText={i === 0 ? 'Mole Fraction' : ''}
						value={row.moleFraction}
						hideSteppers
						step={0.01}
						on:change={(e) => updateFraction(row.id, Number(e.detail))}
					/>
				</Column>
				<Column sm={1} md={1} lg={1} class="remove-col">
					<button
						class="remove-btn"
						onclick={() => removeRow(row.id)}
						disabled={composition.length <= 1}
						title="Remove"
					>
						<SubtractFilled size={16} />
					</button>
				</Column>
			</Row>
		{/each}

		<!-- Add & Total -->
		<Row class="mb-2">
			<Column sm={4} md={4} lg={4}>
				<Button kind="ghost" on:click={addRow}>
					<AddFilled size={16} />
					Add Component
				</Button>
			</Column>
		</Row>

		<Row class="mb-4">
			<Column>
				<p class="total-info">
					Total mole fraction: {totalFraction.toFixed(4)}
					{#if totalFraction != 1.0}
						<span class="normalize-note">(will be auto-normalized to 1.0)</span>
					{/if}
				</p>
			</Column>
		</Row>

		<!-- Calculate -->
		<Row class="mt-4">
			<Column>
				<Button on:click={calculate}>Calculate HCDP</Button>
			</Column>
		</Row>

		<!-- Error -->
		{#if errorMsg}
			<Row class="mt-4">
				<Column>
					<Tile>
						<p class="error">{errorMsg}</p>
					</Tile>
				</Column>
			</Row>
		{/if}

		<!-- Results -->
		{#if dewPointC !== null}
			<Row class="mt-4">
				<Column>
					<Tile>
						<h4>Hydrocarbon Dew Point:</h4>
						<p class="result-text">{dewPointC.toFixed(2)} °C</p>
						<p class="result-secondary">{dewPointF!.toFixed(2)} °F</p>
					</Tile>
				</Column>
			</Row>

			<Row class="mt-4">
				<Column>
					<Tile>
						<h4>Gas Composition:</h4>
						<table class="comp-table">
							<thead>
								<tr>
									<th>Fluid</th>
									<th>Mole Fraction</th>
								</tr>
							</thead>
							<tbody>
								{#each normalizedComposition as row (row.id)}
									{#if row.moleFraction > 0}
										<tr>
											<td>{row.fluid}</td>
											<td>{row.moleFraction.toFixed(6)}</td>
										</tr>
									{/if}
								{/each}
							</tbody>
						</table>
						<p class="result-info">
							<strong>EOS:</strong> Peng-Robinson<br />
							<strong>Flash:</strong> P-Q (Dew Point at Q=1)<br />
							<strong>Pressure:</strong>
							{pressure} {pressureUnit} ({convertToPa(pressure, pressureUnit).toFixed(0)} Pa)
						</p>
					</Tile>
				</Column>
			</Row>
		{/if}
	</Grid>
{/if}

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

	:global(.mb-2) {
		margin-bottom: 0.5rem;
	}

	:global(.mt-4) {
		margin-top: 1rem;
	}

	:global(.items-end) {
		align-items: flex-end;
	}

	.section-heading {
		font-weight: 500;
		margin-bottom: 0.5rem;
	}

	.total-info {
		font-size: 0.9rem;
		color: #525252;
	}

	.normalize-note {
		color: #0f62fe;
		font-style: italic;
	}

	h4 {
		margin-bottom: 1rem;
		font-weight: 500;
	}

	.result-text {
		font-size: 1.5rem;
		font-weight: 600;
	}

	.result-secondary {
		font-size: 1.1rem;
		color: #525252;
		margin-top: 0.25rem;
	}

	.result-info {
		margin-top: 1rem;
		padding-top: 1rem;
		border-top: 1px solid #e0e0e0;
		font-size: 0.9rem;
		color: #525252;
		line-height: 1.6;
	}

	.comp-table {
		width: 100%;
		border-collapse: collapse;
		margin-bottom: 1rem;

		th,
		td {
			text-align: left;
			padding: 0.35rem 0.75rem;
			border-bottom: 1px solid #e0e0e0;
			font-size: 0.9rem;
		}

		th {
			font-weight: 500;
			color: #525252;
		}
	}

	.error {
		color: #da1e28;
		font-weight: 500;
	}

	:global(.remove-col) {
		display: flex;
		align-items: flex-end;
		padding-bottom: 0.15rem;
	}

	.remove-btn {
		background: none;
		border: none;
		cursor: pointer;
		padding: 0.5rem;
		color: #525252;
	}

	.remove-btn:hover:not(:disabled) {
		background: #e0e0e0;
	}

	.remove-btn:disabled {
		opacity: 0.3;
		cursor: not-allowed;
	}
</style>
