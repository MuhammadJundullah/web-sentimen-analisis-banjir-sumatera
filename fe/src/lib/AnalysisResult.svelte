<script lang="ts">
  import type { AnalysisHistory } from '../stores/analysisStore';
  import SentimentBadge from './SentimentBadge.svelte';
  import CategoryTag from './CategoryTag.svelte';

  export let analysis: AnalysisHistory;

  const emptySummary: { label: string; value: number }[] = [];

  function formatTime(date: string): string {
    return new Date(date).toLocaleString('id-ID', {
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit'
    });
  }

  function toSummary(data: Record<string, number> | undefined) {
    if (!data) return emptySummary;
    return Object.entries(data)
      .map(([label, value]) => ({ label, value }))
      .sort((a, b) => b.value - a.value);
  }

  $: sentimentSummary = toSummary(analysis.all_predictions?.sentiment_percentages);
  $: categorySummary = toSummary(analysis.all_predictions?.category_percentages);
  $: totalCount = analysis.all_predictions?.total ?? null;
  $: skippedCount = analysis.all_predictions?.skipped ?? null;
</script>

<div class="bg-white rounded-xl shadow-md p-6 hover:shadow-lg transition-shadow border border-gray-100">
  <div class="flex justify-between items-start mb-4">
    <span class="text-xs text-gray-500">{formatTime(analysis.created_at)}</span>
    <span class="text-xs text-gray-400 uppercase tracking-wide">{analysis.source}</span>
  </div>

  <p class="text-gray-700 mb-4 leading-relaxed">"{analysis.text}"</p>

  <div class="space-y-4">
    <div>
      <h4 class="text-sm font-semibold text-gray-600 mb-2">Sentimen:</h4>
      {#if analysis.sentiment}
        <SentimentBadge label={analysis.sentiment.label} score={analysis.sentiment.score} />
      {:else if analysis.source === 'csv'}
        <span class="text-sm text-gray-400">Ringkasan CSV</span>
      {:else}
        <span class="text-sm text-gray-400">Tidak terdeteksi</span>
      {/if}
    </div>

    {#if analysis.source === 'csv' && (sentimentSummary.length > 0 || categorySummary.length > 0)}
      {#if totalCount !== null}
        <div class="text-xs text-gray-500">
          Total baris: {totalCount}{#if skippedCount !== null} · Terlewati: {skippedCount}{/if}
        </div>
      {/if}

      {#if sentimentSummary.length > 0}
        <div>
          <h4 class="text-sm font-semibold text-gray-600 mb-2">Distribusi Sentimen:</h4>
          <div class="space-y-3 text-sm text-gray-600">
            {#each sentimentSummary as item}
              <div>
                <div class="flex justify-between mb-1">
                  <span class="font-medium text-gray-700">{item.label}</span>
                  <span class="font-semibold">{item.value.toFixed(1)}%</span>
                </div>
                <div class="h-2 bg-gray-100 rounded-full overflow-hidden">
                  <div
                    class="h-full bg-blue-500"
                    style={`width: ${Math.min(item.value, 100)}%`}
                  />
                </div>
              </div>
            {/each}
          </div>
        </div>
      {/if}

      {#if categorySummary.length > 0}
        <div>
          <h4 class="text-sm font-semibold text-gray-600 mb-2">Distribusi Kategori:</h4>
          <div class="space-y-3 text-sm text-gray-600 max-h-56 overflow-y-auto pr-2">
            {#each categorySummary as item}
              <div>
                <div class="flex justify-between mb-1">
                  <span class="font-medium text-gray-700">{item.label}</span>
                  <span class="font-semibold">{item.value.toFixed(1)}%</span>
                </div>
                <div class="h-2 bg-gray-100 rounded-full overflow-hidden">
                  <div
                    class="h-full bg-emerald-500"
                    style={`width: ${Math.min(item.value, 100)}%`}
                  />
                </div>
              </div>
            {/each}
          </div>
        </div>
      {/if}
    {:else if analysis.categories && analysis.categories.length > 0}
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
