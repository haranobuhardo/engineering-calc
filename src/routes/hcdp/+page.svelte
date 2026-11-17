<script lang="ts">
	import { onMount, onDestroy, tick } from 'svelte';
	import { siteConfig } from '$lib/nav';
	import {
		pressureUnits,
		convertPressureBetween,
		convertTemperatureBetween
	} from '$lib/convert';
	import type {
		CompositionEntry,
		EnvelopeLandmark,
		PhasePoint
	} from '$lib/workers/hcdp.worker';
	import {
		Grid,
		Row,
		Column,
		NumberInput,
		ComboBox,
		Button,
		Tile,
		Loading,
		SkeletonPlaceholder,
		InlineNotification,
		Link
	} from 'carbon-components-svelte';
	import { AddFilled, SubtractFilled } from 'carbon-icons-svelte';
	import Chart from 'chart.js/auto';

	interface TableCompositionRow {
		id: number;
		fluid: string;
		wetFraction: number;
		dryFraction: number;
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

	function getAvailableItems(currentRowId: number) {
		const usedFluids = new Set(
			composition.filter((r) => r.id !== currentRowId && r.fluid).map((r) => r.fluid)
		);
		return fluidItems.filter((item) => !usedFluids.has(item.id));
	}

	// Engine & Worker state
	let engineReady = $state(false);
	let engineError: string | null = $state(null);
	let calculating = $state(false);
	let worker: Worker | null = null;
	let activeRequestId = 0;

	// Calculator inputs
	let pressure = $state(50);
	let pressureUnit = $state('bar');
	let nextId = $state(10);

	// Default composition: C1–C6 + H2O (typical natural gas)
	let composition = $state<CompositionEntry[]>([
		{ id: 1, fluid: 'Methane', moleFraction: 0.872 },
		{ id: 2, fluid: 'Ethane', moleFraction: 0.06 },
		{ id: 3, fluid: 'Propane', moleFraction: 0.03 },
		{ id: 4, fluid: 'IsoButane', moleFraction: 0.008 },
		{ id: 5, fluid: 'n-Butane', moleFraction: 0.012 },
		{ id: 6, fluid: 'Isopentane', moleFraction: 0.004 },
		{ id: 7, fluid: 'n-Pentane', moleFraction: 0.006 },
		{ id: 8, fluid: 'Hexane', moleFraction: 0.003 },
		{ id: 9, fluid: 'Water', moleFraction: 0.005 }
	]);

	// Results (Option B: primary Dry-Basis HCDP + secondary Raw Wet EoS Flash)
	let dewPointC: number | null = $state(null);
	let dewPointF: number | null = $state(null);
	let wetDewPointC: number | null = $state(null);
	let wetDewPointF: number | null = $state(null);
	let errorMsg: string | null = $state(null);
	let tableComposition: TableCompositionRow[] = $state([]);
	let calcPressure = $state(50);
	let calcPressureUnit = $state('bar');
	let calcPressurePa = $state(5000000);

	// Water exclusion warning state
	let waterExcluded = $state(false);
	let waterFractionRemoved = $state(0);

	// Phase envelope landmarks (UI display) & plain non-$state arrays for Chart.js
	let cricondentherm = $state<EnvelopeLandmark | null>(null);
	let cricondenbar = $state<EnvelopeLandmark | null>(null);
	let criticalPoint = $state<EnvelopeLandmark | null>(null);
	let envelopeWarning: string | null = $state(null);

	// Plain arrays (NOT $state proxies) so Chart.js can attach _chartjs metadata without throwing state_descriptors_fixed
	let dewCurvePoints: PhasePoint[] = [];
	let bubbleCurvePoints: PhasePoint[] = [];

	// Chart.js state
	let phaseCanvas = $state<HTMLCanvasElement | null>(null);
	let phaseChart: Chart | null = null;

	// Derived
	let totalFraction = $derived(composition.reduce((s, r) => s + r.moleFraction, 0));

	function destroyChart() {
		if (phaseChart) {
			phaseChart.destroy();
			phaseChart = null;
		}
	}

	onDestroy(() => {
		destroyChart();
		if (worker) {
			worker.terminate();
			worker = null;
		}
	});

	// Spawn CoolProp Web Worker lazily on mount
	onMount(() => {
		try {
			worker = new Worker(
				new URL('$lib/workers/hcdp.worker.ts', import.meta.url),
				{ type: 'module' }
			);

			worker.onmessage = async (event: MessageEvent) => {
				const data = event.data;

				if (data.type === 'ready') {
					engineReady = true;
					return;
				}

				if (data.type === 'init-error') {
					engineError = data.message;
					return;
				}

				if (data.requestId !== activeRequestId) return;

				if (data.type === 'calc-error') {
					calculating = false;
					errorMsg = data.message;
					return;
				}

				if (data.type === 'result') {
					calculating = false;
					dewPointC = data.dewPointC;
					dewPointF = data.dewPointF;
					wetDewPointC = data.wetDewPointC ?? null;
					wetDewPointF = data.wetDewPointF ?? null;
					cricondentherm = data.cricondentherm;
					cricondenbar = data.cricondenbar;
					criticalPoint = data.criticalPoint;
					envelopeWarning = data.envelopeWarning;

					// Store plain arrays from worker structured clone directly
					dewCurvePoints = data.dewCurvePoints || [];
					bubbleCurvePoints = data.bubbleCurvePoints || [];

					await tick();
					renderPhaseChart();
				}
			};

			worker.onerror = (err) => {
				console.error('HCDP Worker error:', err);
				calculating = false;
				if (!engineReady) {
					engineError = 'Fatal EoS Error: Worker failed to initialize.';
				} else {
					errorMsg = 'Background calculation worker encountered an error.';
				}
			};

			worker.postMessage({ type: 'init' });
		} catch (err) {
			console.error('CoolProp Worker creation failed:', err);
			engineError = 'Fatal EoS Error: WASM worker initialization failed.';
		}
	});

	// Composition helpers
	function addRow() {
		composition = [
			...composition,
			{ id: nextId++, fluid: '', moleFraction: 0 }
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

	function drawRegionBadge(
		ctx: CanvasRenderingContext2D,
		text: string,
		cx: number,
		cy: number,
		borderColor: string,
		textColor: string,
		bgColor: string
	) {
		ctx.save();
		ctx.font = '600 11px "IBM Plex Sans", -apple-system, BlinkMacSystemFont, sans-serif';
		const metrics = ctx.measureText(text);
		const padX = 8;
		const padY = 5;
		const w = metrics.width + padX * 2;
		const h = 14 + padY * 2;
		const rx = cx - w / 2;
		const ry = cy - h / 2;

		ctx.fillStyle = bgColor;
		ctx.strokeStyle = borderColor;
		ctx.lineWidth = 1;
		ctx.beginPath();
		ctx.roundRect(rx, ry, w, h, 4);
		ctx.fill();
		ctx.stroke();

		ctx.fillStyle = textColor;
		ctx.textAlign = 'center';
		ctx.textBaseline = 'middle';
		ctx.fillText(text, cx, cy);
		ctx.restore();
	}

	function renderPhaseChart() {
		destroyChart();
		if (!phaseCanvas || dewPointC === null || dewPointF === null) return;
		if (dewCurvePoints.length === 0 && bubbleCurvePoints.length === 0) return;

		const opPUnit = Number(convertPressureBetween(calcPressurePa, 'Pa', calcPressureUnit).toFixed(3));
		const opTC = Number(dewPointC.toFixed(2));
		const opTF = Number(dewPointF.toFixed(2));
		const unitLabel = calcPressureUnit;

		const allX = [
			...dewCurvePoints.map((p) => p.x),
			...bubbleCurvePoints.map((p) => p.x),
			opTC
		];
		const allY = [
			...dewCurvePoints.map((p) => p.y),
			...bubbleCurvePoints.map((p) => p.y),
			opPUnit
		];
		const minEnvTemp = Math.min(...allX);
		const maxEnvTemp = Math.max(...allX);
		const maxEnvP = Math.max(...allY);

		// Generous axis bounds so Liquid, Vapor, and Critical Phase regions are all clearly visible
		const xMin = Math.floor((minEnvTemp - 30) / 10) * 10;
		const xMax = Math.ceil((maxEnvTemp + 45) / 10) * 10;
		const yMax = Number((maxEnvP * 1.25).toPrecision(3));

		// Snapshot plain objects for the custom region plugin closure
		const dewPts = dewCurvePoints.map((p) => ({ x: p.x, y: p.y, tF: p.tF }));
		const bubPts = bubbleCurvePoints.map((p) => ({ x: p.x, y: p.y, tF: p.tF }));
		const critPt = criticalPoint
			? { tC: criticalPoint.tC, pUnit: criticalPoint.pUnit }
			: null;
		const cricT = cricondentherm
			? { tC: cricondentherm.tC, pUnit: cricondentherm.pUnit }
			: null;
		const cricP = cricondenbar
			? { tC: cricondenbar.tC, pUnit: cricondenbar.pUnit }
			: null;

		const phaseRegionsPlugin = {
			id: 'phaseRegions',
			beforeDatasetsDraw(chart: Chart) {
				const { ctx, chartArea, scales } = chart;
				const xScale = scales.x;
				const yScale = scales.y;
				if (!chartArea || !xScale || !yScale) return;

				ctx.save();
				ctx.beginPath();
				ctx.rect(
					chartArea.left,
					chartArea.top,
					chartArea.right - chartArea.left,
					chartArea.bottom - chartArea.top
				);
				ctx.clip();

				const tcPx = critPt
					? xScale.getPixelForValue(critPt.tC)
					: (chartArea.left + chartArea.right) * 0.45;
				const pcPx = critPt
					? yScale.getPixelForValue(critPt.pUnit)
					: chartArea.top + (chartArea.bottom - chartArea.top) * 0.35;

				// 1. Liquid Phase Background (Left of Bubble Point Curve & T < Tc)
				if (bubPts.length > 1) {
					ctx.fillStyle = 'rgba(0, 157, 154, 0.07)';
					ctx.beginPath();
					ctx.moveTo(chartArea.left, chartArea.top);
					ctx.lineTo(tcPx, chartArea.top);
					for (const p of bubPts) {
						ctx.lineTo(xScale.getPixelForValue(p.x), yScale.getPixelForValue(p.y));
					}
					ctx.lineTo(chartArea.left, chartArea.bottom);
					ctx.closePath();
					ctx.fill();
				}

				// 2. Critical / Dense Phase Background (Top-Right quadrant: T > Tc & P > Pc outside envelope)
				if (critPt) {
					ctx.fillStyle = 'rgba(25, 128, 56, 0.075)';
					ctx.beginPath();
					ctx.moveTo(tcPx, chartArea.top);
					ctx.lineTo(chartArea.right, chartArea.top);
					ctx.lineTo(chartArea.right, pcPx);
					const upperDew = dewPts.filter((p) => p.y >= critPt.pUnit);
					for (let i = 0; i < upperDew.length; i++) {
						ctx.lineTo(
							xScale.getPixelForValue(upperDew[i].x),
							yScale.getPixelForValue(upperDew[i].y)
						);
					}
					ctx.lineTo(tcPx, pcPx);
					ctx.closePath();
					ctx.fill();

					// Dashed boundary lines for Critical Phase (T = Tc upward, P = Pc rightward)
					ctx.save();
					ctx.strokeStyle = 'rgba(25, 128, 56, 0.45)';
					ctx.lineWidth = 1.25;
					ctx.setLineDash([5, 5]);

					ctx.beginPath();
					ctx.moveTo(tcPx, pcPx);
					ctx.lineTo(tcPx, chartArea.top);
					ctx.stroke();

					const dewAtPc = dewPts.reduce(
						(best, p) =>
							Math.abs(p.y - critPt.pUnit) < Math.abs(best.y - critPt.pUnit)
								? p
								: best,
						dewPts[0]
					);
					const startXForPc = dewAtPc
						? Math.max(tcPx, xScale.getPixelForValue(dewAtPc.x))
						: tcPx;
					ctx.beginPath();
					ctx.moveTo(startXForPc, pcPx);
					ctx.lineTo(chartArea.right, pcPx);
					ctx.stroke();
					ctx.restore();
				}

				// 3. Vapor Phase Background (Right of Dew Point Curve, below Pc)
				if (dewPts.length > 1) {
					ctx.fillStyle = 'rgba(255, 131, 43, 0.06)';
					ctx.beginPath();
					const lowerDew = critPt
						? dewPts.filter((p) => p.y <= critPt.pUnit)
						: dewPts;
					if (lowerDew.length > 0) {
						ctx.moveTo(
							xScale.getPixelForValue(lowerDew[0].x),
							chartArea.bottom
						);
						for (const p of lowerDew) {
							ctx.lineTo(
								xScale.getPixelForValue(p.x),
								yScale.getPixelForValue(p.y)
							);
						}
						ctx.lineTo(chartArea.right, pcPx);
						ctx.lineTo(chartArea.right, chartArea.bottom);
						ctx.closePath();
						ctx.fill();
					}
				}

				// 4. Two-Phase (Vapor + Liquid) Closed Envelope Polygon Fill
				if (dewPts.length > 1 && bubPts.length > 1) {
					ctx.fillStyle = 'rgba(15, 98, 254, 0.14)';
					ctx.beginPath();
					ctx.moveTo(
						xScale.getPixelForValue(dewPts[0].x),
						yScale.getPixelForValue(dewPts[0].y)
					);
					for (let i = 1; i < dewPts.length; i++) {
						ctx.lineTo(
							xScale.getPixelForValue(dewPts[i].x),
							yScale.getPixelForValue(dewPts[i].y)
						);
					}
					for (let i = 0; i < bubPts.length; i++) {
						ctx.lineTo(
							xScale.getPixelForValue(bubPts[i].x),
							yScale.getPixelForValue(bubPts[i].y)
						);
					}
					ctx.closePath();
					ctx.fill();
				}

				ctx.restore();
			},
			afterDatasetsDraw(chart: Chart) {
				const { ctx, chartArea, scales } = chart;
				const xScale = scales.x;
				const yScale = scales.y;
				if (!chartArea || !xScale || !yScale) return;

				ctx.save();
				ctx.beginPath();
				ctx.rect(
					chartArea.left,
					chartArea.top,
					chartArea.right - chartArea.left,
					chartArea.bottom - chartArea.top
				);
				ctx.clip();

				// A. 2-Phase (Vapor + Liquid) label at centroid of envelope
				if (dewPts.length > 2 && bubPts.length > 2) {
					const midPressure = (cricP ? cricP.pUnit : maxEnvP) * 0.42;
					const closestBub = bubPts.reduce((a, b) =>
						Math.abs(b.y - midPressure) < Math.abs(a.y - midPressure) ? b : a
					);
					const closestDew = dewPts.reduce((a, b) =>
						Math.abs(b.y - midPressure) < Math.abs(a.y - midPressure) ? b : a
					);
					const twoPhaseX = xScale.getPixelForValue(
						(closestBub.x + closestDew.x) / 2
					);
					const twoPhaseY = yScale.getPixelForValue(midPressure);

					drawRegionBadge(
						ctx,
						'2-PHASE (VAPOR + LIQUID)',
						twoPhaseX,
						twoPhaseY,
						'rgba(15, 98, 254, 0.45)',
						'#0043ce',
						'rgba(255, 255, 255, 0.88)'
					);
				}

				// B. Liquid Phase label (left of Bubble Curve)
				const liqX =
					chartArea.left +
					Math.max(
						65,
						(xScale.getPixelForValue(critPt ? critPt.tC : minEnvTemp) -
							chartArea.left) *
							0.45
					);
				const liqY =
					chartArea.top + (chartArea.bottom - chartArea.top) * 0.35;
				drawRegionBadge(
					ctx,
					'LIQUID PHASE',
					liqX,
					liqY,
					'rgba(0, 157, 154, 0.5)',
					'#005d5d',
					'rgba(255, 255, 255, 0.88)'
				);

				// C. Vapor Phase label (right of Dew Curve)
				const cricTxPx = xScale.getPixelForValue(cricT ? cricT.tC : maxEnvTemp);
				const vapX = Math.min(
					chartArea.right - 65,
					cricTxPx + (chartArea.right - cricTxPx) * 0.52
				);
				const vapY =
					chartArea.top + (chartArea.bottom - chartArea.top) * 0.65;
				drawRegionBadge(
					ctx,
					'VAPOR PHASE',
					vapX,
					vapY,
					'rgba(255, 131, 43, 0.55)',
					'#8a3800',
					'rgba(255, 255, 255, 0.88)'
				);

				// D. Critical Phase label (top-right above Pc and right of Tc)
				if (critPt) {
					const tcPx = xScale.getPixelForValue(critPt.tC);
					const pcPx = yScale.getPixelForValue(critPt.pUnit);
					const critLabelX = Math.min(
						chartArea.right - 75,
						tcPx + (chartArea.right - tcPx) * 0.62
					);
					const critLabelY = Math.max(
						chartArea.top + 22,
						chartArea.top + (pcPx - chartArea.top) * 0.45
					);
					drawRegionBadge(
						ctx,
						'CRITICAL PHASE',
						critLabelX,
						critLabelY,
						'rgba(25, 128, 56, 0.5)',
						'#0e6027',
						'rgba(255, 255, 255, 0.88)'
					);
				}

				ctx.restore();
			}
		};

		const datasets: any[] = [];

		// 1. Dew Point Curve (Q = 1)
		if (dewPts.length > 0) {
			datasets.push({
				label: 'Dew Point Curve (Q = 1)',
				data: dewPts,
				borderColor: '#0f62fe',
				backgroundColor: '#0f62fe',
				borderWidth: 2.5,
				pointRadius: 0,
				pointHoverRadius: 4,
				tension: 0.25,
				showLine: true
			});
		}

		// 2. Bubble Point Curve (Q = 0)
		if (bubPts.length > 0) {
			datasets.push({
				label: 'Bubble Point Curve (Q = 0)',
				data: bubPts,
				borderColor: '#009d9a',
				backgroundColor: '#009d9a',
				borderWidth: 2.5,
				borderDash: [6, 4],
				pointRadius: 0,
				pointHoverRadius: 4,
				tension: 0.25,
				showLine: true
			});
		}

		// 3. Operating Isobar Reference Line (P = P_op)
		datasets.push({
			label: `Operating Isobar (${calcPressure} ${unitLabel})`,
			data: [
				{
					x: Number(xMin.toFixed(2)),
					y: opPUnit,
					tF: Number(convertTemperatureBetween(xMin, 'C', 'F').toFixed(2))
				},
				{ x: opTC, y: opPUnit, tF: opTF }
			],
			borderColor: '#8d8d8d',
			backgroundColor: '#8d8d8d',
			borderWidth: 1.5,
			borderDash: [4, 4],
			pointRadius: 0,
			pointHoverRadius: 0,
			showLine: true
		});

		// 4. Operating HCDP Point
		datasets.push({
			label: `Operating HCDP (${opTC.toFixed(2)} °C @ ${calcPressure} ${unitLabel})`,
			data: [{ x: opTC, y: opPUnit, tF: opTF }],
			borderColor: '#da1e28',
			backgroundColor: '#da1e28',
			pointRadius: 7,
			pointHoverRadius: 9,
			pointStyle: 'circle',
			showLine: false
		});

		// 5. Cricondentherm (Max T)
		if (cricondentherm) {
			const ctTC = cricondentherm.tC;
			const ctY = cricondentherm.pUnit;
			const ctTF = cricondentherm.tF;
			datasets.push({
				label: `Cricondentherm (${ctTC.toFixed(2)} °C, ${ctY.toFixed(2)} ${unitLabel})`,
				data: [{ x: ctTC, y: ctY, tF: ctTF }],
				borderColor: '#ff832b',
				backgroundColor: '#ff832b',
				pointRadius: 7,
				pointHoverRadius: 9,
				pointStyle: 'triangle',
				showLine: false
			});
		}

		// 6. Cricondenbar (Max P)
		if (cricondenbar) {
			const cbTC = cricondenbar.tC;
			const cbY = cricondenbar.pUnit;
			const cbTF = cricondenbar.tF;
			datasets.push({
				label: `Cricondenbar (${cbY.toFixed(2)} ${unitLabel} @ ${cbTC.toFixed(2)} °C)`,
				data: [{ x: cbTC, y: cbY, tF: cbTF }],
				borderColor: '#8a3ffc',
				backgroundColor: '#8a3ffc',
				pointRadius: 7,
				pointHoverRadius: 9,
				pointStyle: 'rectRot',
				showLine: false
			});
		}

		// 7. Critical Point (Tc, Pc)
		if (criticalPoint) {
			const cpTC = criticalPoint.tC;
			const cpY = criticalPoint.pUnit;
			const cpTF = criticalPoint.tF;
			datasets.push({
				label: `Critical Point (${cpTC.toFixed(2)} °C, ${cpY.toFixed(2)} ${unitLabel})`,
				data: [{ x: cpTC, y: cpY, tF: cpTF }],
				borderColor: '#198038',
				backgroundColor: '#198038',
				pointRadius: 6.5,
				pointHoverRadius: 8.5,
				pointStyle: 'rect',
				showLine: false
			});
		}

		phaseChart = new Chart(phaseCanvas, {
			type: 'scatter',
			data: { datasets },
			plugins: [phaseRegionsPlugin],
			options: {
				responsive: true,
				maintainAspectRatio: false,
				scales: {
					x: {
						type: 'linear',
						min: xMin,
						max: xMax,
						title: {
							display: true,
							text: 'Temperature (°C)'
						}
					},
					y: {
						type: 'linear',
						min: 0,
						max: yMax,
						title: {
							display: true,
							text: `Pressure (${unitLabel})`
						},
						beginAtZero: true
					}
				},
				plugins: {
					legend: {
						position: 'top'
					},
					tooltip: {
						callbacks: {
							label(ctx) {
								const raw = ctx.raw as { x: number; y: number; tF?: number };
								const tC = raw.x;
								const tF = raw.tF ?? convertTemperatureBetween(tC, 'C', 'F');
								const pVal = raw.y;
								return `${ctx.dataset.label?.split(' (')[0]}: ${tC.toFixed(2)} °C (${tF.toFixed(2)} °F), ${pVal.toFixed(2)} ${unitLabel}`;
							}
						}
					}
				}
			}
		});
	}

	function calculate() {
		dewPointC = null;
		dewPointF = null;
		wetDewPointC = null;
		wetDewPointF = null;
		errorMsg = null;
		tableComposition = [];
		waterExcluded = false;
		waterFractionRemoved = 0;
		cricondentherm = null;
		cricondenbar = null;
		criticalPoint = null;
		envelopeWarning = null;
		dewCurvePoints = [];
		bubbleCurvePoints = [];
		destroyChart();

		if (!engineReady || !worker) {
			errorMsg = 'EoS engine is not loaded yet. Please wait...';
			return;
		}

		if (totalFraction <= 0) {
			errorMsg = 'Total mole fraction is zero. Enter at least one component.';
			return;
		}

		const activeInputRows = composition.filter((r) => r.fluid && r.moleFraction > 0);
		const waterRows = activeInputRows.filter((r) => r.fluid === 'Water');
		const rawWaterSum = waterRows.reduce((s, r) => s + r.moleFraction, 0);

		const dryRows = activeInputRows.filter((r) => r.fluid !== 'Water');
		const drySum = dryRows.reduce((s, r) => s + r.moleFraction, 0);

		if (drySum <= 0) {
			errorMsg =
				'No non-water hydrocarbon/gas components entered. Use the Water Dew Point calculator for pure H₂O condensation.';
			return;
		}

		if (rawWaterSum > 0) {
			waterExcluded = true;
			waterFractionRemoved = rawWaterSum / totalFraction;
		}

		const dryNorm: CompositionEntry[] = dryRows.map((row) => ({
			id: row.id,
			fluid: row.fluid,
			moleFraction: row.moleFraction / drySum
		}));

		const wetNorm: CompositionEntry[] = activeInputRows.map((row) => ({
			id: row.id,
			fluid: row.fluid,
			moleFraction: row.moleFraction / totalFraction
		}));

		tableComposition = activeInputRows.map((row) => ({
			id: row.id,
			fluid: row.fluid,
			wetFraction: row.moleFraction / totalFraction,
			dryFraction: row.fluid === 'Water' ? 0 : row.moleFraction / drySum
		}));

		calcPressure = pressure;
		calcPressureUnit = pressureUnit;
		const pressurePa = convertPressureBetween(pressure, pressureUnit, 'Pa');
		calcPressurePa = pressurePa;

		calculating = true;
		const requestId = ++activeRequestId;

		worker.postMessage({
			type: 'calculate',
			requestId,
			dryNorm,
			wetNorm: waterExcluded ? wetNorm : undefined,
			pressurePa,
			pressureUnit
		});
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
					Calculate hydrocarbon dew point and P–T phase envelope using Peng-Robinson EOS via CoolProp
				</p>
			</Column>
		</Row>

		<!-- Pressure Input -->
		<Row class="mb-4 items-end">
			<Column sm={2} md={5} lg={5}>
				<NumberInput labelText="Pressure" bind:value={pressure} hideSteppers />
			</Column>
			<Column sm={2} md={3} lg={3}>
				<ComboBox
					items={pressureUnits}
					selectedId={pressureUnit}
					itemToString={(item) => item?.text ?? ''}
					labelText="Unit"
					shouldFilterItem={() => true}
					on:select={(e) => (pressureUnit = e.detail.selectedId)}
				/>
			</Column>
		</Row>

		<!-- Gas Composition -->
		<Row class="mb-2">
			<Column>
				<h4 class="section-heading">Gas Composition</h4>
			</Column>
		</Row>

		{#each composition as row, i (row.id)}
			{@const items = getAvailableItems(row.id)}
			<Row class="mb-4 items-end">
				<Column sm={2} md={5} lg={5}>
					<ComboBox
						{items}
						itemToString={(item) => item?.text ?? ''}
						selectedId={row.fluid || undefined}
						labelText={i === 0 ? 'Component Name' : ''}
						placeholder="Search component..."
						shouldFilterItem={(item, value) =>
							item.text.toLowerCase().includes(value.toLowerCase())}
						on:select={(e) => updateFluid(row.id, e.detail.selectedId)}
						on:clear={() => updateFluid(row.id, '')}
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
		<Row class="mt-4 items-center">
			<Column sm={4} md={4} lg={3}>
				<Button on:click={calculate} disabled={calculating}>
					{calculating ? 'Calculating...' : 'Calculate HCDP'}
				</Button>
			</Column>
			{#if calculating}
				<Column sm={4} md={4} lg={5}>
					<div class="skeleton-loading-row" role="status" aria-live="polite">
						<SkeletonPlaceholder style="width: 24px; height: 24px;" />
						<span class="skeleton-loading-text">Solving and generating chart...</span>
					</div>
				</Column>
			{/if}
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

		<!-- Results: Carbon Tiles in Grid Rows/Columns -->
		{#if dewPointC !== null}
			<Row class="mt-4">
				<Column
					sm={4}
					md={waterExcluded && wetDewPointC !== null ? 4 : 8}
					lg={waterExcluded && wetDewPointC !== null ? 8 : 16}
					class="mb-4"
				>
					<Tile class="tile-full-height">
						<h4>Hydrocarbon Dew Point:</h4>
						<p class="result-text">{dewPointC.toFixed(2)} °C</p>
						<p class="result-secondary">{dewPointF!.toFixed(2)} °F</p>
						<p class="result-tertiary">
							{waterExcluded ? 'Dry Hydrocarbon Basis' : 'Peng-Robinson EoS'} at {calcPressure}
							{calcPressureUnit}
						</p>
					</Tile>
				</Column>

				{#if waterExcluded && wetDewPointC !== null && wetDewPointF !== null}
					<Column sm={4} md={4} lg={8} class="mb-4">
						<Tile class="tile-full-height">
							<h4>Unstripped Wet PR Flash (Reference):</h4>
							<p class="result-text">{wetDewPointC.toFixed(2)} °C</p>
							<p class="result-secondary">{wetDewPointF.toFixed(2)} °F</p>
							<p class="result-tertiary">
								Raw 2-phase PR flash with {(waterFractionRemoved * 100).toFixed(2)}% H₂O included
							</p>
						</Tile>
					</Column>
				{/if}
			</Row>

			{#if cricondentherm || cricondenbar || criticalPoint}
				<Row>
					{#if cricondentherm}
						<Column sm={4} md={4} lg={5} class="mb-4">
							<Tile class="tile-full-height">
								<h4>Cricondentherm (Max T):</h4>
								<p class="result-text">{cricondentherm.tC.toFixed(2)} °C</p>
								<p class="result-secondary">{cricondentherm.tF.toFixed(2)} °F</p>
								<p class="result-tertiary">
									at {cricondentherm.pUnit.toFixed(2)} {calcPressureUnit}
								</p>
							</Tile>
						</Column>
					{/if}

					{#if cricondenbar}
						<Column sm={4} md={4} lg={5} class="mb-4">
							<Tile class="tile-full-height">
								<h4>Cricondenbar (Max P):</h4>
								<p class="result-text">
									{cricondenbar.pUnit.toFixed(2)} {calcPressureUnit}
								</p>
								<p class="result-secondary">{cricondenbar.tC.toFixed(2)} °C</p>
								<p class="result-tertiary">{cricondenbar.tF.toFixed(2)} °F</p>
							</Tile>
						</Column>
					{/if}

					{#if criticalPoint}
						<Column sm={4} md={8} lg={6} class="mb-4">
							<Tile class="tile-full-height">
								<h4>Critical Point (Tc, Pc):</h4>
								<p class="result-text">{criticalPoint.tC.toFixed(2)} °C</p>
								<p class="result-secondary">{criticalPoint.tF.toFixed(2)} °F</p>
								<p class="result-tertiary">
									at {criticalPoint.pUnit.toFixed(2)} {calcPressureUnit}
								</p>
							</Tile>
						</Column>
					{/if}
				</Row>
			{/if}

			<!-- Carbon Callout / Static InlineNotification for Dry-Basis Notes -->
			{#if waterExcluded}
				<Row class="mt-4">
					<Column>
						<InlineNotification
							kind="warning"
							lowContrast
							hideCloseButton
							title="Dry-Basis Hydrocarbon Calculation:"
						>
							<svelte:fragment slot="subtitleChildren">
								Water ({(waterFractionRemoved * 100).toFixed(2)}% mol) was automatically excluded
								and the remaining gas components were re-normalized to 1.000000 for the Hydrocarbon
								Dew Point and Phase Envelope because 2-phase Peng-Robinson EoS does not model
								3-phase water–hydrocarbon liquid immiscibility (VLLE). To evaluate aqueous
								condensation, use the
								<Link inline href="/water-dew-point">Water Dew Point Calculator</Link>.
							</svelte:fragment>
						</InlineNotification>
					</Column>
				</Row>
			{/if}

			<!-- Phase Envelope Chart Tile -->
			<Row class="mt-4">
				<Column>
					<Tile>
						<h4>Hydrocarbon Phase Diagram (P–T Envelope):</h4>
						{#if envelopeWarning}
							<p class="error">{envelopeWarning}</p>
						{:else}
							<div class="canvas-wrapper phase-canvas-wrapper">
								<canvas bind:this={phaseCanvas}></canvas>
							</div>
						{/if}
					</Tile>
				</Column>
			</Row>

			<!-- Gas Composition Table Tile -->
			<Row class="mt-4">
				<Column>
					<Tile>
						<h4>Gas Composition:</h4>
						<div class="table-scroll">
							<table class="comp-table">
								<thead>
									<tr>
										<th>Fluid</th>
										{#if waterExcluded}
											<th>Wet Mole Fraction</th>
											<th>Dry Mole Fraction</th>
										{:else}
											<th>Mole Fraction</th>
										{/if}
									</tr>
								</thead>
								<tbody>
									{#each tableComposition as row (row.id)}
										<tr>
											<td>{row.fluid}</td>
											{#if waterExcluded}
												<td>{row.wetFraction.toFixed(6)}</td>
												<td>{row.dryFraction.toFixed(6)}</td>
											{:else}
												<td>{row.dryFraction.toFixed(6)}</td>
											{/if}
										</tr>
									{/each}
								</tbody>
							</table>
						</div>
						<p class="result-info">
							<strong>EOS:</strong> Peng-Robinson<br />
							<strong>Flash:</strong> P-Q (Dew Point at Q=1)<br />
							<strong>Pressure:</strong>
							{calcPressure} {calcPressureUnit} ({calcPressurePa.toFixed(0)} Pa)
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

	:global(.items-center) {
		align-items: center;
	}

	:global(.tile-full-height) {
		height: 100%;
	}

	:global(.bx--inline-notification) {
		max-width: 100%;
	}

	.skeleton-loading-row {
		display: flex;
		align-items: center;
		gap: 0.75rem;
	}

	.skeleton-loading-text {
		font-size: 0.875rem;
		color: #525252;
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

	p {
		margin: 0.4rem 0;
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

	.canvas-wrapper {
		position: relative;
		width: 100%;
	}

	.phase-canvas-wrapper {
		height: 420px;
	}

	.table-scroll {
		overflow-x: auto;
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
