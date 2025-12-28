<script lang="ts">
  import type { AnalysisHistory } from '../stores/analysisStore';
  import SentimentBadge from './SentimentBadge.svelte';
  import CategoryTag from './CategoryTag.svelte';

  export let analysis: AnalysisHistory;

  function formatTime(date: Date): string {
    return new Date(date).toLocaleString('id-ID', {
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit'
    });
  }
</script>

<div class="bg-white rounded-xl shadow-md p-6 hover:shadow-lg transition-shadow border border-gray-100">
  <div class="flex justify-between items-start mb-4">
    <span class="text-xs text-gray-500">{formatTime(analysis.timestamp)}</span>
  </div>

  <p class="text-gray-700 mb-4 leading-relaxed">"{analysis.text}"</p>

  <div class="space-y-4">
    <div>
      <h4 class="text-sm font-semibold text-gray-600 mb-2">Sentimen:</h4>
      <SentimentBadge label={analysis.sentiment.label} score={analysis.sentiment.score} />
    </div>

    {#if analysis.categories && analysis.categories.length > 0}
      <div>
        <h4 class="text-sm font-semibold text-gray-600 mb-2">Kategori:</h4>
        <div class="flex flex-wrap gap-2">
          {#each analysis.categories as category}
            <CategoryTag label={category.label} score={category.score} />
          {/each}
        </div>
      </div>
    {/if}
  </div>
</div>
