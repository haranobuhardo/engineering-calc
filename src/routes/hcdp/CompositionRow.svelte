<script lang="ts">
	import { Dropdown, NumberInput } from 'carbon-components-svelte';
	import { SubtractFilled } from 'carbon-icons-svelte';

	interface Props {
		fluidItems: { id: string; text: string }[];
		selectedFluid: string;
		moleFraction: number;
		canRemove: boolean;
		onremove: () => void;
		onfluidchange: (fluid: string) => void;
		onfractionchange: (value: number) => void;
		showLabels?: boolean;
	}

	let {
		fluidItems,
		selectedFluid,
		moleFraction,
		canRemove,
		onremove,
		onfluidchange,
		onfractionchange,
		showLabels = false
	}: Props = $props();
</script>

<div class="comp-row">
	<Dropdown
        labelText={showLabels ? 'Component Name' : ''}
		selectedId={selectedFluid}
		items={fluidItems}
		label={showLabels ? 'Component' : ''}
		on:select={(e) => onfluidchange(e.detail.selectedId)}
	/>
	<NumberInput
		labelText={showLabels ? 'Mole Fraction' : ''}
		value={moleFraction}
		hideSteppers
		step={0.01}
		on:change={(e) => onfractionchange(Number(e.detail))}
	/>
	<button
		class="remove-btn"
		onclick={onremove}
		disabled={!canRemove}
		title="Remove"
	>
		<SubtractFilled size={16} />
	</button>
</div>

<style>
	.comp-row {
		display: flex;
		align-items: flex-end;
		gap: 0.5rem;
		margin-bottom: 0.5rem;
	}

	.comp-row > :global(*:first-child) {
		flex: 2;
	}

	.comp-row > :global(*:nth-child(2)) {
		flex: 1;
	}

	.remove-btn {
		background: none;
		border: none;
		cursor: pointer;
		padding: 0.5rem;
		color: #525252;
		margin-bottom: 0.15rem;
	}

	.remove-btn:hover:not(:disabled) {
		background: #e0e0e0;
	}

	.remove-btn:disabled {
		opacity: 0.3;
		cursor: not-allowed;
	}
</style>
