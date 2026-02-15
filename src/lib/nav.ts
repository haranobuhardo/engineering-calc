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
	{ href: '/water-dew-point', label: 'Water Dew Point', id: 'water-dew-point' }
];

export const siteConfig: SiteConfig = {
	title: "Hardo's Calculator Collection",
	description: 'Collection of my engineering calculator'
};
