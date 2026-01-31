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
	{ href: '/lag-time', label: 'Lag Time', id: 'lag-time' },
	{ href: '/pressure-drop', label: 'Pressure Drop', id: 'pressure-drop' }
];

export const siteConfig: SiteConfig = {
	title: "Hardo's Calculator Collection",
	description: 'Collection of my engineering calculator'
};
