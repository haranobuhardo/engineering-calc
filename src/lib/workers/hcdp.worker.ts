import { convertPressureBetween, convertTemperatureBetween } from '$lib/convert';

export interface CompositionEntry {
	id: number;
	fluid: string;
	moleFraction: number;
}

export interface EnvelopeLandmark {
	tC: number;
	tF: number;
	pPa: number;
	pUnit: number;
}

export interface PhasePoint {
	x: number;
	y: number;
	tF: number;
	pPa: number;
}

export interface CalculateRequest {
	type: 'calculate';
	requestId: number;
	dryNorm: CompositionEntry[];
	wetNorm?: CompositionEntry[];
	pressurePa: number;
	pressureUnit: string;
}

export interface InitRequest {
	type: 'init';
}

export type WorkerRequest = InitRequest | CalculateRequest;

let coolprop: any = null;

function buildGasString(norm: CompositionEntry[]): string {
	const parts = norm
		.filter((row) => row.moleFraction > 0)
		.map((row) => `${row.fluid}[${row.moleFraction.toFixed(6)}]`);
	return `PR::${parts.join('&')}`;
}

function computePhaseEnvelope(
	cp: any,
	dryNorm: CompositionEntry[],
	operatingPressurePa: number,
	unit: string
) {
	let dewCurvePoints: PhasePoint[] = [];
	let bubbleCurvePoints: PhasePoint[] = [];
	let cricondentherm: EnvelopeLandmark | null = null;
	let cricondenbar: EnvelopeLandmark | null = null;
	let criticalPoint: EnvelopeLandmark | null = null;
	let envelopeWarning: string | null = null;

	const activeRows = dryNorm.filter((r) => r.fluid && r.moleFraction > 0);
	if (activeRows.length === 0) {
		return {
			dewCurvePoints,
			bubbleCurvePoints,
			cricondentherm,
			cricondenbar,
			criticalPoint,
			envelopeWarning
		};
	}

	const fluidNames = activeRows.map((r) => r.fluid).join('&');
	let state: any = null;
	let z: any = null;
	let data: any = null;

	try {
		state = cp.factory('PR', fluidNames);
		z = new cp.VectorDouble();
		for (const r of activeRows) {
			z.push_back(r.moleFraction);
		}
		state.set_mole_fractions(z);
		state.build_phase_envelope('');
		data = state.get_phase_envelope_data();

		const T: number[] = cp.readVectorDouble(data.T);
		const P: number[] = cp.readVectorDouble(data.p);
		const Q: number[] = cp.readVectorDouble(data.Q);

		const minValidPa = Math.min(50000, Math.max(1000, operatingPressurePa * 0.25));

		let critTransitionIdx = -1;
		for (let i = 1; i < Q.length; i++) {
			if (Q[i - 1] === 1 && Q[i] === 0) {
				critTransitionIdx = i;
				break;
			}
		}

		const dewRaw: PhasePoint[] = [];
		const bubRaw: PhasePoint[] = [];

		let maxT = -Infinity;
		let maxTPoint: PhasePoint | null = null;
		let maxP = -Infinity;
		let maxPPoint: PhasePoint | null = null;

		for (let i = 0; i < T.length; i++) {
			const tk = T[i];
			const pa = P[i];
			const q = Q[i];

			if (!isFinite(tk) || !isFinite(pa) || tk < 90 || pa < minValidPa) continue;

			const tC = convertTemperatureBetween(tk, 'K', 'C');
			const tF = convertTemperatureBetween(tk, 'K', 'F');
			const pUnitVal = convertPressureBetween(pa, 'Pa', unit);
			const pt: PhasePoint = {
				x: Number(tC.toFixed(2)),
				y: Number(pUnitVal.toFixed(3)),
				tF: Number(tF.toFixed(2)),
				pPa: pa
			};

			if (critTransitionIdx !== -1) {
				if (i < critTransitionIdx && q === 1) {
					dewRaw.push(pt);
				} else if (i >= critTransitionIdx && q === 0) {
					bubRaw.push(pt);
				}
			} else if (q === 1) {
				dewRaw.push(pt);
			} else if (q === 0) {
				bubRaw.push(pt);
			}

			if (tC > maxT) {
				maxT = tC;
				maxTPoint = pt;
			}
			if (pa > maxP) {
				maxP = pa;
				maxPPoint = pt;
			}
		}

		if (
			critTransitionIdx > 0 &&
			critTransitionIdx < T.length &&
			isFinite(T[critTransitionIdx - 1]) &&
			isFinite(T[critTransitionIdx])
		) {
			const tcK = (T[critTransitionIdx - 1] + T[critTransitionIdx]) / 2;
			const pcPa = (P[critTransitionIdx - 1] + P[critTransitionIdx]) / 2;
			const tcC = convertTemperatureBetween(tcK, 'K', 'C');
			const tcF = convertTemperatureBetween(tcK, 'K', 'F');
			const pcUnit = convertPressureBetween(pcPa, 'Pa', unit);

			criticalPoint = {
				tC: Number(tcC.toFixed(2)),
				tF: Number(tcF.toFixed(2)),
				pPa: pcPa,
				pUnit: Number(pcUnit.toFixed(3))
			};

			const critPhasePt: PhasePoint = {
				x: criticalPoint.tC,
				y: criticalPoint.pUnit,
				tF: criticalPoint.tF,
				pPa: pcPa
			};

			dewRaw.push(critPhasePt);
			bubRaw.unshift(critPhasePt);
		}

		if (maxTPoint) {
			cricondentherm = {
				tC: maxTPoint.x,
				tF: maxTPoint.tF,
				pPa: maxTPoint.pPa,
				pUnit: maxTPoint.y
			};
		}

		if (maxPPoint) {
			cricondenbar = {
				tC: maxPPoint.x,
				tF: maxPPoint.tF,
				pPa: maxPPoint.pPa,
				pUnit: maxPPoint.y
			};
		}

		dewCurvePoints = dewRaw;
		bubbleCurvePoints = bubRaw;
	} catch (err) {
		console.warn('Phase envelope solver warning:', err);
		envelopeWarning =
			'Could not construct the full continuous phase envelope for this mixture.';
	} finally {
		if (data) {
			for (const k of Object.keys(data)) {
				if (data[k] && typeof data[k].delete === 'function') {
					data[k].delete();
				}
			}
		}
		if (z && typeof z.delete === 'function') z.delete();
		if (state && typeof state.delete === 'function') state.delete();
	}

	return {
		dewCurvePoints,
		bubbleCurvePoints,
		cricondentherm,
		cricondenbar,
		criticalPoint,
		envelopeWarning
	};
}

self.onmessage = async (event: MessageEvent<WorkerRequest>) => {
	const msg = event.data;

	if (msg.type === 'init') {
		try {
			if (!coolprop) {
				const coolpropUrl = new URL('/coolprop.js', self.location.origin).href;
				const CoolPropModule = await import(/* @vite-ignore */ coolpropUrl);
				coolprop = await CoolPropModule.default({
					locateFile: (file: string) => new URL(`/${file}`, self.location.origin).href
				});
			}
			self.postMessage({ type: 'ready' });
		} catch (err) {
			console.error('CoolProp WASM worker init failed:', err);
			self.postMessage({
				type: 'init-error',
				message: 'Fatal EoS Error: WASM load failed.'
			});
		}
		return;
	}

	if (msg.type === 'calculate') {
		const { requestId, dryNorm, wetNorm, pressurePa, pressureUnit } = msg;

		if (!coolprop) {
			self.postMessage({
				type: 'calc-error',
				requestId,
				message: 'EoS engine is not loaded yet. Please wait...'
			});
			return;
		}

		try {
			const dryGasString = buildGasString(dryNorm);
			const tKelvinDry = coolprop.PropsSI('T', 'P', pressurePa, 'Q', 1, dryGasString);

			if (tKelvinDry <= 0 || !isFinite(tKelvinDry)) {
				self.postMessage({
					type: 'calc-error',
					requestId,
					message:
						'Operating pressure exceeds the mixture cricondenbar or returned an invalid temperature.'
				});
				return;
			}

			const dewPointC = convertTemperatureBetween(tKelvinDry, 'K', 'C');
			const dewPointF = convertTemperatureBetween(tKelvinDry, 'K', 'F');

			// Option B: Also compute raw Wet EoS Flash if wetNorm was provided
			let wetDewPointC: number | null = null;
			let wetDewPointF: number | null = null;
			if (wetNorm && wetNorm.length > 0) {
				try {
					const wetGasString = buildGasString(wetNorm);
					const tKelvinWet = coolprop.PropsSI('T', 'P', pressurePa, 'Q', 1, wetGasString);
					if (tKelvinWet > 0 && isFinite(tKelvinWet)) {
						wetDewPointC = convertTemperatureBetween(tKelvinWet, 'K', 'C');
						wetDewPointF = convertTemperatureBetween(tKelvinWet, 'K', 'F');
					}
				} catch {
					// Ignore if wet flash fails to converge
				}
			}

			const envelope = computePhaseEnvelope(
				coolprop,
				dryNorm,
				pressurePa,
				pressureUnit
			);

			self.postMessage({
				type: 'result',
				requestId,
				dewPointC,
				dewPointF,
				wetDewPointC,
				wetDewPointF,
				...envelope
			});
		} catch (e: unknown) {
			const errMsg =
				typeof e === 'string' ? e : (e as Error)?.message || 'Unknown error';
			self.postMessage({
				type: 'calc-error',
				requestId,
				message: `Flash calculation failed: ${errMsg}`
			});
		}
	}
};
