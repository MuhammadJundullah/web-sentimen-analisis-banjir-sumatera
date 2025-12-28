<script lang="ts">
  export let label: string;
  export let score: number;

  $: badgeClass = {
    'Positif': 'bg-green-100 text-green-800 border-green-300',
    'Negatif': 'bg-red-100 text-red-800 border-red-300',
    'Netral': 'bg-gray-100 text-gray-800 border-gray-300'
  }[label] || 'bg-gray-100 text-gray-800 border-gray-300';
</script>

<div class="inline-flex items-center gap-2 px-4 py-2 rounded-lg border-2 {badgeClass}">
  <span class="font-semibold text-lg">{label}</span>
  <span class="text-sm opacity-75">({(score * 100).toFixed(1)}%)</span>
</div>
