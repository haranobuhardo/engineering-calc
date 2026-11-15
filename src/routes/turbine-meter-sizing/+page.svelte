<script lang="ts">
	import { onDestroy, tick } from 'svelte';
	import { siteConfig } from '$lib/nav';
	import { convertFlowRateBetween, liquidFlowRateUnits } from '$lib/convert';
	import turbineCatalog from '$lib/data/sensia-nuflo-turbine.json';
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
	import Chart from 'chart.js/auto';
	import katex from 'katex';
	import 'katex/dist/katex.min.css';

	const PSI_TO_KPA = 6.894757;
	const OVERRUN_FACTOR = turbineCatalog.overrunFactor || 1.5;

	type FitStatus = 'LINEAR_FIT' | 'TRANSIENT_SURGE' | 'UNDER_MIN' | 'OVER_MAX' | 'OUT_OF_BOUNDS';

	interface EvaluatedMeter {
		id: string;
		size: string;
		nominalIn: number;
		minFlow: number;
		maxFlow: number;
		overrunFlow: number;
		span: number;
		coversRange: boolean;
		fitStatus: FitStatus;
		minSpareFlow: number;
		maxSpareFlow: number;
		minSparePct: number;
		maxSparePct: number;
		minSpanSharePct: number;
		activeSpanSharePct: number;
		maxSpanSharePct: number;
		minDpPsi: number;
		minDpKpa: number;
		maxDpPsi: number;
		maxDpKpa: number;
		dpExponent: number;
		dpAtReqMinPsi: number;
		dpAtReqMinKpa: number;
		dpAtReqMaxPsi: number;
		dpAtReqMaxKpa: number;
		dpAtOverrunPsi: number;
		dpAtOverrunKpa: number;
	}

	let mode = $state('auto-select');
	let selectedMeterId = $state('3');

	let minFlowInput = $state(120);
	let maxFlowInput = $state(650);
	let flowUnit = $state('gpm');

	let calculated = $state(false);
	let errorMsg = $state<string | null>(null);
	let reqMin = $state(0);
	let reqMax = $state(0);
	let calcUnitLabel = $state('GPM (US)');
	let calcModeUsed = $state('auto-select');
	let displayedMeters = $state<EvaluatedMeter[]>([]);
	let allEvaluatedMeters = $state<EvaluatedMeter[]>([]);
	let stepLatex = $state('');

	let spareCanvas = $state<HTMLCanvasElement | null>(null);
	let dpCanvas = $state<HTMLCanvasElement | null>(null);
	let spareChart: Chart | null = null;
	let dpChart: Chart | null = null;

	const meterSizeItems = turbineCatalog.meters.map((m) => ({
		id: m.id,
		text: `${m.size} (${m.minFlow.toFixed(2)} – ${m.maxFlow.toFixed(2)} ${turbineCatalog.baseUnit.toUpperCase()})`
	}));

	function getUnitLabel(unitId: string): string {
		const found = liquidFlowRateUnits.find((u) => u.id === unitId);
		return found ? found.text : unitId;
	}

	function fmt(val: number): string {
		return val.toFixed(2);
	}

	function getFitStatusLabel(status: FitStatus): string {
		switch (status) {
			case 'LINEAR_FIT':
				return 'WITHIN LINEAR RANGE';
			case 'TRANSIENT_SURGE':
				return 'EXCEEDS MAX (WITHIN 150% TRANSIENT SURGE ZONE)';
			case 'UNDER_MIN':
				return 'BELOW MINIMUM LINEAR FLOW';
			case 'OVER_MAX':
				return 'EXCEEDS 150% OVERRUN LIMIT';
			case 'OUT_OF_BOUNDS':
			default:
				return 'OUTSIDE METER OPERATING LIMITS';
		}
	}

	function destroyCharts() {
		if (spareChart) {
			spareChart.destroy();
			spareChart = null;
		}
		if (dpChart) {
			dpChart.destroy();
			dpChart = null;
		}
	}

	onDestroy(() => {
		destroyCharts();
	});

	function renderCharts() {
		destroyCharts();
		if (displayedMeters.length === 0) return;

		// 1. % Spare & Flow Range Floating Bar Chart
		if (spareCanvas) {
			const labels = displayedMeters.map((m, i) =>
				calcModeUsed === 'auto-select' && displayedMeters.length > 1
					? `Option ${i + 1}: ${m.size}`
					: `NuFlo ${m.size}`
			);

			spareChart = new Chart(spareCanvas, {
				type: 'bar',
				data: {
					labels,
					datasets: [
						{
							label: 'Min Spare Zone (Meter Min → Req Min)',
							data: displayedMeters.map((m) => [
								Number(fmt(m.minFlow)),
								Number(fmt(Math.max(m.minFlow, Math.min(reqMin, m.maxFlow))))
							]),
							backgroundColor: 'rgba(0, 157, 154, 0.35)',
							borderColor: '#009d9a',
							borderWidth: 1.5,
							barPercentage: 0.6
						},
						{
							label: `Requested Flow Range`,
							data: displayedMeters.map(() => [Number(fmt(reqMin)), Number(fmt(reqMax))]),
							backgroundColor: 'rgba(15, 98, 254, 0.85)',
							borderColor: '#0043ce',
							borderWidth: 1.5,
							barPercentage: 0.6
						},
						{
							label: 'Max Spare Zone (Req Max → Meter Max)',
							data: displayedMeters.map((m) => [
								Number(fmt(Math.min(m.maxFlow, Math.max(reqMax, m.minFlow)))),
								Number(fmt(m.maxFlow))
							]),
							backgroundColor: 'rgba(25, 128, 56, 0.35)',
							borderColor: '#198038',
							borderWidth: 1.5,
							barPercentage: 0.6
						},
						{
							label: '150% Brief Transient Surge Zone',
							data: displayedMeters.map((m) => [
								Number(fmt(m.maxFlow)),
								Number(fmt(m.overrunFlow))
							]),
							backgroundColor: 'rgba(218, 30, 40, 0.15)',
							borderColor: '#da1e28',
							borderWidth: 1.5,
							barPercentage: 0.6
						}
					]
				},
				options: {
					indexAxis: 'y',
					responsive: true,
					maintainAspectRatio: false,
					scales: {
						x: {
							title: {
								display: true,
								text: `Flow Rate (${calcUnitLabel})`
							},
							beginAtZero: true
						},
						y: {
							stacked: true
						}
					},
					plugins: {
						tooltip: {
							callbacks: {
								label(ctx) {
									const raw = ctx.raw as [number, number];
									const meter = displayedMeters[ctx.dataIndex];
									if (!raw || raw.length !== 2) return '';
									const span = raw[1] - raw[0];
									if (ctx.datasetIndex === 0) {
										return `Min Spare: ${fmt(raw[0])} – ${fmt(raw[1])} ${calcUnitLabel} (+${fmt(span)} ${calcUnitLabel} / ${fmt(meter.minSparePct)}% spare to min)`;
									}
									if (ctx.datasetIndex === 1) {
										return `Requested: ${fmt(raw[0])} – ${fmt(raw[1])} ${calcUnitLabel} (${fmt(meter.activeSpanSharePct)}% of meter span)`;
									}
									if (ctx.datasetIndex === 2) {
										return `Max Spare: ${fmt(raw[0])} – ${fmt(raw[1])} ${calcUnitLabel} (+${fmt(span)} ${calcUnitLabel} / ${fmt(meter.maxSparePct)}% spare to max)`;
									}
									return `150% Transient Surge: ${fmt(raw[0])} – ${fmt(raw[1])} ${calcUnitLabel}`;
								}
							}
						}
					}
				}
			});
		}

		// 2. Pressure Drop Curve Chart (Chart.js Line / Scatter)
		if (dpCanvas) {
			const palette = ['#0f62fe', '#198038', '#8a3ffc', '#ba4e00'];
			const datasets: any[] = [];

			displayedMeters.forEach((m, idx) => {
				const color = palette[idx % palette.length];
				const linearPoints: { x: number; y: number }[] = [];
				const surgePoints: { x: number; y: number }[] = [];
				const steps = 30;

				for (let i = 0; i <= steps; i++) {
					const q = m.minFlow + ((m.maxFlow - m.minFlow) * i) / steps;
					const dp = m.maxDpPsi * Math.pow(q / m.maxFlow, m.dpExponent);
					linearPoints.push({ x: Number(fmt(q)), y: Number(fmt(dp)) });
				}

				for (let i = 0; i <= 15; i++) {
					const q = m.maxFlow + ((m.overrunFlow - m.maxFlow) * i) / 15;
					const dp = m.maxDpPsi * Math.pow(q / m.maxFlow, m.dpExponent);
					surgePoints.push({ x: Number(fmt(q)), y: Number(fmt(dp)) });
				}

				datasets.push({
					label: `${m.size} Linear Range`,
					data: linearPoints,
					borderColor: color,
					backgroundColor: color,
					borderWidth: 2.5,
					pointRadius: 0,
					pointHoverRadius: 4,
					tension: 0.25,
					showLine: true
				});

				datasets.push({
					label: `${m.size} Overrun Range`,
					data: surgePoints,
					borderColor: '#da1e28',
					backgroundColor: '#da1e28',
					borderDash: [6, 4],
					borderWidth: 1.75,
					pointRadius: 0,
					pointHoverRadius: 4,
					tension: 0.25,
					showLine: true
				});

				datasets.push({
					label: `${m.size} Min & Max Requested Flow`,
					data: [
						{ x: Number(fmt(reqMin)), y: Number(fmt(m.dpAtReqMinPsi)) },
						{ x: Number(fmt(reqMax)), y: Number(fmt(m.dpAtReqMaxPsi)) }
					],
					borderColor: color,
					backgroundColor: '#ffffff',
					pointBorderWidth: 2.5,
					pointRadius: 5.5,
					pointHoverRadius: 7,
					showLine: false
				});
			});

			dpChart = new Chart(dpCanvas, {
				type: 'scatter',
				data: { datasets },
				options: {
					responsive: true,
					maintainAspectRatio: false,
					scales: {
						x: {
							type: 'linear',
							title: {
								display: true,
								text: `Flow Rate (${calcUnitLabel})`
							},
							beginAtZero: true
						},
						y: {
							type: 'linear',
							title: {
								display: true,
								text: 'Estimated Pressure Drop ΔP (psi)'
							},
							beginAtZero: true
						}
					},
					plugins: {
						tooltip: {
							callbacks: {
								label(ctx) {
									const pt = ctx.raw as { x: number; y: number };
									const kpa = pt.y * PSI_TO_KPA;
									return `${ctx.dataset.label}: Q = ${fmt(pt.x)} ${calcUnitLabel}, ΔP = ${fmt(pt.y)} psi (${fmt(kpa)} kPa)`;
								}
							}
						}
					}
				}
			});
		}
	}

	async function calculate() {
		errorMsg = null;
		displayedMeters = [];
		allEvaluatedMeters = [];
		stepLatex = '';
		destroyCharts();

		if (
			minFlowInput === null ||
			maxFlowInput === null ||
			isNaN(minFlowInput) ||
			isNaN(maxFlowInput)
		) {
			errorMsg = 'Please enter valid numeric values for both Minimum and Maximum Flow Rate.';
			calculated = true;
			return;
		}

		if (minFlowInput <= 0 || maxFlowInput <= 0) {
			errorMsg = 'Minimum and Maximum Flow Rates must be greater than zero.';
			calculated = true;
			return;
		}

		if (minFlowInput > maxFlowInput) {
			errorMsg = 'Minimum Flow Rate cannot be greater than Maximum Flow Rate.';
			calculated = true;
			return;
		}

		reqMin = minFlowInput;
		reqMax = maxFlowInput;
		calcUnitLabel = getUnitLabel(flowUnit);
		calcModeUsed = mode;

		const baseUnit = turbineCatalog.baseUnit || 'gpm';
		const eps = 1e-9;

		const evaluated: EvaluatedMeter[] = turbineCatalog.meters
			.map((m) => {
				const minFlow = convertFlowRateBetween(m.minFlow, baseUnit, flowUnit);
				const maxFlow = convertFlowRateBetween(m.maxFlow, baseUnit, flowUnit);
				const overrunFlow = maxFlow * OVERRUN_FACTOR;
				const span = maxFlow - minFlow;
				const coversRange = minFlow <= reqMin + eps && maxFlow + eps >= reqMax;

				let fitStatus: FitStatus = 'LINEAR_FIT';
				if (coversRange) {
					fitStatus = 'LINEAR_FIT';
				} else if (reqMin >= minFlow - eps && reqMax <= overrunFlow + eps) {
					fitStatus = 'TRANSIENT_SURGE';
				} else if (reqMin < minFlow - eps && reqMax <= maxFlow + eps) {
					fitStatus = 'UNDER_MIN';
				} else if (reqMin >= minFlow - eps && reqMax > overrunFlow + eps) {
					fitStatus = 'OVER_MAX';
				} else {
					fitStatus = 'OUT_OF_BOUNDS';
				}

				const minSpareFlow = reqMin - minFlow;
				const maxSpareFlow = maxFlow - reqMax;

				const minSparePct = reqMin > 0 ? (minSpareFlow / reqMin) * 100 : 0;
				const maxSparePct = maxFlow > 0 ? (maxSpareFlow / maxFlow) * 100 : 0;

				const minSpanSharePct = span > 0 ? Math.max(0, (minSpareFlow / span) * 100) : 0;
				const activeSpanSharePct = span > 0 ? Math.max(0, ((reqMax - reqMin) / span) * 100) : 0;
				const maxSpanSharePct = span > 0 ? Math.max(0, (maxSpareFlow / span) * 100) : 0;

				const minDpPsi = m.minDpPsi;
				const minDpKpa = minDpPsi * PSI_TO_KPA;
				const maxDpPsi = m.maxDpPsi;
				const maxDpKpa = maxDpPsi * PSI_TO_KPA;
				const dpExponent =
					minDpPsi > 0 && maxFlow > minFlow
						? Math.log(maxDpPsi / minDpPsi) / Math.log(maxFlow / minFlow)
						: 2.0;

				const dpAtReqMinPsi = maxDpPsi * Math.pow(reqMin / maxFlow, dpExponent);
				const dpAtReqMinKpa = dpAtReqMinPsi * PSI_TO_KPA;

				const dpAtReqMaxPsi = maxDpPsi * Math.pow(reqMax / maxFlow, dpExponent);
				const dpAtReqMaxKpa = dpAtReqMaxPsi * PSI_TO_KPA;

				const dpAtOverrunPsi = maxDpPsi * Math.pow(OVERRUN_FACTOR, dpExponent);
				const dpAtOverrunKpa = dpAtOverrunPsi * PSI_TO_KPA;

				return {
					id: m.id,
					size: m.size,
					nominalIn: m.nominalIn,
					minFlow,
					maxFlow,
					overrunFlow,
					span,
					coversRange,
					fitStatus,
					minSpareFlow,
					maxSpareFlow,
					minSparePct,
					maxSparePct,
					minSpanSharePct,
					activeSpanSharePct,
					maxSpanSharePct,
					minDpPsi,
					minDpKpa,
					maxDpPsi,
					maxDpKpa,
					dpExponent,
					dpAtReqMinPsi,
					dpAtReqMinKpa,
					dpAtReqMaxPsi,
					dpAtReqMaxKpa,
					dpAtOverrunPsi,
					dpAtOverrunKpa
				};
			})
			.sort((a, b) => a.nominalIn - b.nominalIn);

		allEvaluatedMeters = evaluated;

		if (mode === 'auto-select') {
			displayedMeters = evaluated.filter((m) => m.coversRange);
		} else {
			const picked = evaluated.find((m) => m.id === selectedMeterId);
			displayedMeters = picked ? [picked] : [];
		}

		let latex = `
			\\textbf{Step 1: Requested Process Flow Window} \\\\[5pt]
			Q_{\\text{req,min}} = ${fmt(reqMin)} \\text{ ${calcUnitLabel}}, \\quad Q_{\\text{req,max}} = ${fmt(reqMax)} \\text{ ${calcUnitLabel}} \\\\[5pt]
			\\text{Turndown Ratio} = \\frac{Q_{\\text{req,max}}}{Q_{\\text{req,min}}} = \\frac{${fmt(reqMax)}}{${fmt(reqMin)}} = ${fmt(reqMax / reqMin)}:1 \\\\[10pt]

			\\textbf{Step 2: Linear Coverage \\& Transient Surge Limit} \\\\[5pt]
			Q_{\\text{meter,min}} \\le Q_{\\text{req,min}} \\quad \\text{and} \\quad Q_{\\text{meter,max}} \\ge Q_{\\text{req,max}} \\\\[5pt]
			Q_{\\text{overrun}} = 150.00\\% \\times Q_{\\text{meter,max}} = 1.50 \\times Q_{\\text{meter,max}} \\text{ (brief transient surge only)} \\\\[10pt]

			\\textbf{Step 3: Two-Point Log-Log Pressure Drop Formula (Water Baseline, SG = 1.00)} \\\\[5pt]
			n = \\frac{\\ln(\\Delta P_{\\text{max}} / \\Delta P_{\\text{min}})}{\\ln(Q_{\\text{meter,max}} / Q_{\\text{meter,min}})}, \\quad \\Delta P(Q) = \\Delta P_{\\text{max}} \\times \\left(\\frac{Q}{Q_{\\text{meter,max}}}\\right)^n \\\\[10pt]
			\\\\[20pt]
		`;

		if (displayedMeters.length > 0) {
			displayedMeters.forEach((m, idx) => {
				const safeSizeLatex = m.size.replace(/"/g, "''");
				const headingPrefix =
					mode === 'auto-select' ? `Option ${idx + 1}` : 'Selected Meter Analysis';
				latex += `
					\\textbf{${headingPrefix}: Sensia NuFlo ${safeSizeLatex}} \\\\[5pt]
					\\text{Linear Range: } [${fmt(m.minFlow)},\\; ${fmt(m.maxFlow)}] \\text{ ${calcUnitLabel}}, \\quad Q_{\\text{overrun (150\\%)}} = ${fmt(m.overrunFlow)} \\text{ ${calcUnitLabel}} \\\\[5pt]
					\\%\\text{Spare}_{\\text{min}} = \\frac{Q_{\\text{req,min}} - Q_{\\text{meter,min}}}{Q_{\\text{req,min}}} \\times 100\\% = \\frac{${fmt(reqMin)} - ${fmt(m.minFlow)}}{${fmt(reqMin)}} \\times 100\\% = ${fmt(m.minSparePct)}\\% \\\\[5pt]
					\\%\\text{Spare}_{\\text{max}} = \\frac{Q_{\\text{meter,max}} - Q_{\\text{req,max}}}{Q_{\\text{meter,max}}} \\times 100\\% = \\frac{${fmt(m.maxFlow)} - ${fmt(reqMax)}}{${fmt(m.maxFlow)}} \\times 100\\% = ${fmt(m.maxSparePct)}\\% \\\\[5pt]
					n = \\frac{\\ln(${fmt(m.maxDpPsi)} / ${fmt(m.minDpPsi)})}{\\ln(${fmt(m.maxFlow)} / ${fmt(m.minFlow)})} = ${fmt(m.dpExponent)} \\\\[5pt]
					\\Delta P(Q_{\\text{req,min}}) = ${fmt(m.maxDpPsi)} \\times \\left(\\frac{${fmt(reqMin)}}{${fmt(m.maxFlow)}}\\right)^{${fmt(m.dpExponent)}} = ${fmt(m.dpAtReqMinPsi)} \\text{ psi } (${fmt(m.dpAtReqMinKpa)} \\text{ kPa}) \\\\[5pt]
					\\Delta P(Q_{\\text{req,max}}) = ${fmt(m.maxDpPsi)} \\times \\left(\\frac{${fmt(reqMax)}}{${fmt(m.maxFlow)}}\\right)^{${fmt(m.dpExponent)}} = ${fmt(m.dpAtReqMaxPsi)} \\text{ psi } (${fmt(m.dpAtReqMaxKpa)} \\text{ kPa}) \\\\[10pt]
				`;
			});
		} else {
			latex += `
				\\text{No single turbine meter size satisfies } Q_{\\text{meter,min}} \\le ${fmt(reqMin)} \\text{ and } Q_{\\text{meter,max}} \\ge ${fmt(reqMax)} \\text{ simultaneously.}
			`;
		}

		stepLatex = katex.renderToString(latex, { displayMode: true, fleqn: true });
		calculated = true;

		await tick();
		renderCharts();
	}
</script>

<svelte:head>
	<title>{siteConfig.title} - Sensia NuFlo Turbine Sizing</title>
	<meta name={siteConfig.description} content={siteConfig.description} />
</svelte:head>

<Grid>
	<Row>
		<Column>
			<h1 class="landing-page__heading">Sensia NuFlo Turbine Meter Sizing</h1>
			<p class="description">
				Select the optimal Sensia NuFlo liquid turbine flow meter size or evaluate a specific meter
				size against your required flow range, % spare margins, and estimated pressure drop (ΔP).
			</p>
		</Column>
	</Row>

	<!-- Calculation Mode Selection -->
	<Row class="mb-4">
		<Column>
			<RadioButtonGroup bind:selected={mode} legendText="Calculation Mode">
				<RadioButton
					value="auto-select"
					labelText="Smart Meter Size Advisor"
				/>
				<RadioButton
					value="evaluate-size"
					labelText="Single Meter Size Perf. Evaluation"
				/>
			</RadioButtonGroup>
		</Column>
	</Row>

	<!-- Specific Meter Size Dropdown (Only for Mode B) -->
	{#if mode === 'evaluate-size'}
		<Row class="mb-4">
			<Column sm={4} md={4} lg={4}>
				<Dropdown
					bind:selectedId={selectedMeterId}
					items={meterSizeItems}
					labelText="Select Sensia NuFlo Meter Size"
				/>
			</Column>
		</Row>
	{/if}

	<!-- Flow Rate Inputs -->
	<Row class="mb-4 items-end">
		<Column sm={2} md={3} lg={3}>
			<NumberInput
				labelText="Min. Flow Rate (Q_min)"
				bind:value={minFlowInput}
				hideSteppers
				step={0.1}
			/>
		</Column>
		<Column sm={2} md={3} lg={3}>
			<NumberInput
				labelText="Max. Flow Rate (Q_max)"
				bind:value={maxFlowInput}
				hideSteppers
				step={0.1}
			/>
		</Column>
		<Column sm={4} md={2} lg={3}>
			<Dropdown bind:selectedId={flowUnit} items={liquidFlowRateUnits} labelText="Unit" />
		</Column>
	</Row>

	<Row class="mt-4">
		<Column>
			<Button on:click={calculate}>Calculate</Button>
		</Column>
	</Row>

	{#if calculated}
		{#if errorMsg}
			<Row class="mt-4">
				<Column>
					<Tile>
						<p class="error">{errorMsg}</p>
					</Tile>
				</Column>
			</Row>
		{:else if displayedMeters.length === 0}
			<Row class="mt-4">
				<Column>
					<Tile>
						<h4>Results:</h4>
						<p class="error">
							No single Sensia NuFlo turbine meter size covers both {fmt(reqMin)} {calcUnitLabel}
							and {fmt(reqMax)} {calcUnitLabel} within its recommended linear range (requested
							turndown: {fmt(reqMax / reqMin)}:1).
						</p>
						<div class="note-section">
							<h5>Note on Flow Range & Evaluation Mode:</h5>
							<p>
								Standard Sensia NuFlo turbine meters have a 10:1 linear turndown ratio. You
								can switch to <strong>Single Meter Performance Evaluation</strong> above to inspect how
								a specific meter size performs against this flow range.
							</p>
						</div>
					</Tile>
				</Column>
			</Row>
		{:else}
			<!-- Standard Carbon Result Tile(s) -->
			<Row class="mt-4">
				{#each displayedMeters as meter, idx (meter.id)}
					<Column
						sm={4}
						md={displayedMeters.length > 1 ? 4 : 8}
						lg={displayedMeters.length > 1 ? 8 : 16}
						class="mb-4"
					>
						<Tile>
							<h4>
								{#if calcModeUsed === 'evaluate-size'}
									Performance Evaluation: Sensia NuFlo {meter.size}
								{:else if displayedMeters.length === 1}
									Recommended Meter: Sensia NuFlo {meter.size}
								{:else}
									Option {idx + 1}: Sensia NuFlo {meter.size}
								{/if}
							</h4>

							<p class="result-text">{meter.size}</p>
							<p class="result-secondary">
								Flow Range: {fmt(meter.minFlow)} – {fmt(meter.maxFlow)} {calcUnitLabel}
							</p>
							<p class='result-tertiary'>
							(150% Overrun: {fmt(meter.overrunFlow)} {calcUnitLabel})
							</p>

							<div class="result-info">
								{#if calcModeUsed === 'evaluate-size'}
									<p>
										<strong>Status:</strong>
										<span class={meter.coversRange ? 'status-ok' : 'status-warn'}>
											{getFitStatusLabel(meter.fitStatus)}
										</span>
									</p>
								{/if}
								<p>
									<strong>Requested Flow Range:</strong>
									{fmt(reqMin)} – {fmt(reqMax)} {calcUnitLabel}
								</p>
								<p>
									<strong>Spare to Min Flow:</strong>
									{fmt(meter.minSparePct)}% ({meter.minSpareFlow >= 0 ? '+' : ''}{fmt(meter.minSpareFlow)}
									{calcUnitLabel})
								</p>
								<p>
									<strong>Spare to Max Flow:</strong>
									{fmt(meter.maxSparePct)}% ({meter.maxSpareFlow >= 0 ? '+' : ''}{fmt(meter.maxSpareFlow)}
									{calcUnitLabel})
								</p>
								<p>
									<strong>Estimated ΔP (Min – Max Req):</strong>
									{fmt(meter.dpAtReqMinPsi)} – {fmt(meter.dpAtReqMaxPsi)} psi ({fmt(meter.dpAtReqMinKpa)}
									– {fmt(meter.dpAtReqMaxKpa)} kPa)
								</p>
							</div>
						</Tile>
					</Column>
				{/each}
			</Row>

			<!-- Simplified Engineering Notes Tile -->
			<Row class="mt-4">
				<Column>
					<Tile>
						<h4>Notes:</h4>
						<ul>
							{#if calcModeUsed === 'auto-select' && displayedMeters.length >= 2}
								<li>
									<strong>Size Comparison ({displayedMeters[0].size} vs. {displayedMeters[displayedMeters.length - 1].size}):</strong>
									The larger <strong>{displayedMeters[displayedMeters.length - 1].size}</strong> meter
									produces a lower pressure drop ({fmt(displayedMeters[displayedMeters.length - 1].dpAtReqMaxPsi)}
									psi vs. {fmt(displayedMeters[0].dpAtReqMaxPsi)} psi at max requested flow), but has
									a higher cost.
								</li>
							{/if}
							{#if calcModeUsed === 'evaluate-size' && displayedMeters.length === 1 && !displayedMeters[0].coversRange}
								{@const m = displayedMeters[0]}
								{#if reqMin < m.minFlow}
									<li>
										<strong>Below Min Flow:</strong> Requested min flow ({fmt(reqMin)} {calcUnitLabel})
										is below the meter's minimum linear rating ({fmt(m.minFlow)} {calcUnitLabel}), which
										degrades measurement accuracy.
									</li>
								{/if}
								{#if reqMax > m.maxFlow && reqMax <= m.overrunFlow}
									<li>
										<strong>Within 150% Transient Surge Zone:</strong> Requested max flow ({fmt(reqMax)}
										{calcUnitLabel}) exceeds the 100% continuous rating ({fmt(m.maxFlow)} {calcUnitLabel})
										at {fmt((reqMax / m.maxFlow) * 100)}% of max flow.
									</li>
								{:else if reqMax > m.overrunFlow}
									<li>
										<strong>Exceeds 150% Overrun Limit:</strong> Requested max flow ({fmt(reqMax)} {calcUnitLabel})
										exceeds the 150% surge limit ({fmt(m.overrunFlow)} {calcUnitLabel}) and risks mechanical
										damage.
									</li>
								{/if}
							{/if}
							<li>
								<strong>150% Overrun Capacity:</strong> Each meter can overrun up to 150% of its maximum
								flow rate for a brief transient surge only. Operating above the recommended maximum flow
								rate is not recommended and will shorten the turbine lifetime.
							</li>
						</ul>
					</Tile>
				</Column>
			</Row>

			<!-- Chart 1: Chart.js % Spare & Flow Range Floating Bar Chart -->
			<Row class="mt-4">
				<Column>
					<Tile>
						<h4>% Spare Chart (Requested vs Offered Flow Range):</h4>
						<div class="canvas-wrapper spare-canvas-wrapper">
							<canvas bind:this={spareCanvas}></canvas>
						</div>
					</Tile>
				</Column>
			</Row>

			<!-- Chart 2: Chart.js Pressure Drop Curve -->
			<Row class="mt-4">
				<Column>
					<Tile>
						<h4>Estimated Pressure Drop Curve:</h4>
						<div class="canvas-wrapper dp-canvas-wrapper">
							<canvas bind:this={dpCanvas}></canvas>
						</div>
					</Tile>
				</Column>
			</Row>
		{/if}

		<!-- Calculation Steps (KaTeX) -->
		<Row class="mt-4">
			<Column>
				<Tile>
					<h4>Calculation Steps:</h4>
					<div class="latex-step">{@html stepLatex}</div>
				</Tile>
			</Column>
		</Row>

		<!-- Full Catalog Reference Table -->
		<Row class="mt-4">
			<Column>
				<Tile>
					<h4>Sensia NuFlo Catalog Reference Table ({calcUnitLabel}):</h4>
					<div class="table-scroll">
						<table class="comp-table">
							<thead>
								<tr>
									<th>Meter Size</th>
									<th>Min Flow</th>
									<th>Max Flow (100%)</th>
									<th>Overrun Flow (150%)</th>
									<th>ΔP Range (Min – Max)</th>
									<th>Est. ΔP at Req Max</th>
									<th>Status</th>
								</tr>
							</thead>
							<tbody>
								{#each allEvaluatedMeters as m (m.id)}
									{@const isHighlighted =
										calcModeUsed === 'auto-select' ? m.coversRange : m.id === selectedMeterId}
									<tr class={isHighlighted ? 'matched-row' : ''}>
										<td>{m.size}</td>
										<td>{fmt(m.minFlow)}</td>
										<td>{fmt(m.maxFlow)}</td>
										<td>{fmt(m.overrunFlow)}</td>
										<td>{fmt(m.minDpPsi)} – {fmt(m.maxDpPsi)} psi</td>
										<td>{fmt(m.dpAtReqMaxPsi)} psi ({fmt(m.dpAtReqMaxKpa)} kPa)</td>
										<td>
											{#if m.coversRange}
												<strong>Covers Range</strong> (Min Spare: {fmt(m.minSparePct)}%, Max Spare: {fmt(m.maxSparePct)}%)
											{:else if m.fitStatus === 'TRANSIENT_SURGE'}
												Q_max exceeds 100%, but within 150% short overrun (not recommended)
											{:else if reqMin < m.minFlow}
												Q_min below meter min
											{:else}
												Q_max exceeds 150% limit
											{/if}
										</td>
									</tr>
								{/each}
							</tbody>
						</table>
					</div>
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

	h4 {
		margin-bottom: 1rem;
		font-weight: 500;
	}

	h5 {
		margin-bottom: 0.5rem;
		font-weight: 500;
		color: #161616;
	}

	p {
		margin: 0.4rem 0;
	}

	ul {
		margin: 0.5rem 0;
		padding-left: 1.5rem;
	}

	li {
		margin: 0.4rem 0;
		line-height: 1.5;
	}

	.result-text {
		font-size: 1.5rem;
		font-weight: 600;
	}

	.result-secondary {
		font-size: 1.05rem;
		color: #525252;
		margin-top: 0.25rem;
	}

	.result-tertiary {
		font-size: 0.8rem;
		color: #8f8f8f;
		margin-top: 0.25rem;
	}

	.result-info {
		margin-top: 1rem;
		padding-top: 1rem;
		border-top: 1px solid #e0e0e0;
		font-size: 0.9rem;
		color: #161616;
		line-height: 1.6;
	}

	.status-ok {
		color: #198038;
		font-weight: 600;
	}

	.status-warn {
		color: #da1e28;
		font-weight: 600;
	}

	.note-section {
		margin-top: 1rem;
		padding: 1rem;
		background-color: #f4f4f4;
		border-top: 1px solid #e0e0e0;
	}

	.canvas-wrapper {
		position: relative;
		width: 100%;
	}

	.spare-canvas-wrapper {
		height: 220px;
	}

	.dp-canvas-wrapper {
		height: 320px;
	}

	.latex-step {
		overflow-x: auto;
		padding: 1rem 0;
	}

	.table-scroll {
		overflow-x: auto;
	}

	.comp-table {
		width: 100%;
		border-collapse: collapse;
		margin-top: 0.5rem;
	}

	.comp-table th,
	.comp-table td {
		text-align: left;
		padding: 0.45rem 0.75rem;
		border-bottom: 1px solid #e0e0e0;
		font-size: 0.9rem;
	}

	.comp-table th {
		font-weight: 500;
		color: #525252;
	}

	.matched-row {
		background-color: #e0e0e0;
	}

	.error {
		color: #da1e28;
		font-weight: 500;
	}
</style>
