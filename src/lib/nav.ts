export interface CalcLink {
	href: string;
	label: string;
	id: string;
}

export interface SiteConfig {
	title: string;
	description: string;
}

export const calcLinks: CalcLink[] = [
	{ href: '/reynolds-number', label: 'Reynolds Number', id: 'reynolds-number' },
	{ href: '/lag-time', label: 'Lag Time', id: 'lag-time' },
	{ href: '/analog-signal', label: 'Analog Converter', id: 'analog-signal' },
	{ href: '/span-factor', label: 'Span Factor', id: 'span-factor' },
	{ href: '/water-dew-point', label: 'Water Dew Point', id: 'water-dew-point' },
	{ href: '/tube-heat-loss', label: 'Tube Heat Loss', id: 'tube-heat-loss' },
	{ href: '/friction-pressure-drop', label: 'Friction Pressure Drop', id: 'friction-pressure-drop' },
	{ href: '/acid-gas', label: 'Acid Gas Dew Point', id: 'acid-gas' },
	{ href: '/gas-concentration', label: 'Gas Concentration Conversion', id: 'gas-concentration' },
	{ href: '/flow-induced-bending', label: 'Flow Induced Bending Stress', id: 'flow-induced-bending' },
	{ href: '/wake-frequency', label: 'Wake Frequency Calculation', id: 'wake-frequency' },
	{ href: '/hcdp', label: 'HCDP Calculator', id: 'hcdp' }
];

export const siteConfig: SiteConfig = {
	title: "Hardo's Calculator Collection",
	description: 'Collection of my engineering calculator'
};
