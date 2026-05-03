export interface CalcLink {
	href: string;
	label: string;
	id: string;
}

export interface CalcGroup {
	label: string;
	id: string;
	items: CalcLink[];
}

export interface SiteConfig {
	title: string;
	description: string;
}

export const calcGroups: CalcGroup[] = [
	{
		label: "Analyzer Calibration",
		id: "analyzer-calibration",
		items: [
			{
				href: "/analog-signal",
				label: "Analog Converter",
				id: "analog-signal",
			},
			{ href: "/span-factor", label: "Span Factor", id: "span-factor" },
		],
	},
	{
		label: "Dew Point",
		id: "dew-point",
		items: [
			{
				href: "/water-dew-point",
				label: "Water Dew Point",
				id: "water-dew-point",
			},
			{ href: "/acid-gas", label: "Acid Gas Dew Point", id: "acid-gas" },
			{ href: "/hcdp", label: "HCDP Calculator", id: "hcdp" },
		],
	},
	{
		label: "Flow & Hydraulics",
		id: "flow-hydraulics",
		items: [
			{
				href: "/reynolds-number",
				label: "Reynolds Number",
				id: "reynolds-number",
			},
			{
				href: "/friction-pressure-drop",
				label: "Friction Pressure Drop",
				id: "friction-pressure-drop",
			},
			{
				href: "/flow-induced-bending",
				label: "Flow Induced Bending Stress",
				id: "flow-induced-bending",
			},
		],
	},
	{
		label: "Sampling System",
		id: "sampling-system",
		items: [
			{ href: "/lag-time", label: "Lag Time", id: "lag-time" },
			{
				href: "/tube-heat-loss",
				label: "Tube Heat Loss",
				id: "tube-heat-loss",
			},
			{
				href: "/wake-frequency",
				label: "Wake Frequency Calculation",
				id: "wake-frequency",
			},
		],
	},
	{
		label: "Unit Converter",
		id: "unit-converter",
		items: [
			{
				href: "/gas-concentration",
				label: "Gas Concentration Conversion",
				id: "gas-concentration",
			},
		],
	},
];

// Flat list derived from groups for backward compat (search, isSelected checks)
export const calcLinks: CalcLink[] = calcGroups.flatMap((group) => group.items);

export const siteConfig: SiteConfig = {
	title: "Hardo's Calculator Collection",
	description: "Collection of my engineering calculator",
};
