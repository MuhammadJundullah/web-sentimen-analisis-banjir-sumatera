<script lang="ts">
  export let label: string;
  export let score: number;
</script>

<div class="inline-flex items-center gap-2 px-3 py-1.5 bg-blue-50 text-blue-700 border border-blue-200 rounded-full text-sm">
  <span class="font-medium">{label}</span>
  <span class="text-xs opacity-75">({(score * 100).toFixed(0)}%)</span>
</div>
