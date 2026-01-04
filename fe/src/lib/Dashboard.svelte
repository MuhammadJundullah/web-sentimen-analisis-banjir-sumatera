<script lang="ts">
  import { onMount } from 'svelte';
  import { analysisHistory, type AnalysisHistory } from '../stores/analysisStore';
  import { apiClient, type FetchStatusResponse } from '../services/api';
  import AnalysisResult from './AnalysisResult.svelte';

  let tweetText = '';
  const apiUrl = import.meta.env.VITE_BACKEND_URL ?? '';
  let isLoading = false;
  let error = '';
  let uploadFile: File | null = null;
  let uploadMessage = '';
  let uploadError = '';
  let isUploading = false;
  let uploadSummary: { label: string; value: number }[] = [];
  let categorySummary: { label: string; value: number }[] = [];
  let fetchStatus: FetchStatusResponse | null = null;
  let fetchMessage = '';
  let fetchError = '';
  let isFetching = false;
  let tokenInput = '';
  let tokenMessage = '';
  let tokenError = '';
  let isSettingToken = false;
  let activePage: 'input' | 'upload' | 'fetch' | 'history' = 'input';
  let historyError = '';
  let historyMessage = '';
  let isHistoryLoading = false;
  let isClearingHistory = false;
  let deletingHistoryId: number | null = null;
  let latestAnalysis: AnalysisHistory | null = null;

  function ensureApiUrl(target: 'error' | 'uploadError' | 'fetchError' | 'tokenError' | 'historyError') {
    if (apiUrl.trim()) {
      return true;
    }

    const message = 'URL API Backend belum dikonfigurasi.';
    if (target === 'error') {
      error = message;
    } else if (target === 'uploadError') {
      uploadError = message;
    } else if (target === 'fetchError') {
      fetchError = message;
    } else if (target === 'tokenError') {
      tokenError = message;
    } else if (target === 'historyError') {
      historyError = message;
    }
    return false;
  }

  async function handleAnalysis() {
    if (!tweetText.trim()) {
      error = 'Mohon masukkan teks tweet';
      return;
    }

    if (!ensureApiUrl('error')) return;

    isLoading = true;
    error = '';

    try {
      apiClient.setBaseUrl(apiUrl.trim());
      const result = await apiClient.predict(tweetText);
      const analysisItem = {
        id: result.history_id ?? 0,
        text: result.text,
        sentiment: result.sentiment ?? null,
        categories: result.categories ?? [],
        all_predictions: result.all_predictions,
        source: result.source ?? 'manual',
        created_at: result.created_at ?? new Date().toISOString(),
      };
      latestAnalysis = analysisItem;
      if (result.history_id && result.created_at) {
        analysisHistory.addAnalysis(analysisItem);
      }
      tweetText = '';
    } catch (err) {
      error = err instanceof Error ? err.message : 'Terjadi kesalahan saat analisis';
    } finally {
      isLoading = false;
    }
  }

  async function handleUpload() {
    if (!ensureApiUrl('uploadError')) return;

    if (!uploadFile) {
      uploadError = 'Mohon pilih file CSV';
      return;
    }

    isUploading = true;
    uploadError = '';
    uploadMessage = '';

    try {
      apiClient.setBaseUrl(apiUrl.trim());
      const result = await apiClient.uploadCsv(uploadFile);
      uploadMessage = 'Analisis selesai. Persentase siap ditampilkan.';
      uploadSummary = Object.entries(result.sentiment_percentages)
        .map(([label, value]) => ({ label, value }))
        .sort((a, b) => b.value - a.value);
      categorySummary = Object.entries(result.category_percentages)
        .map(([label, value]) => ({ label, value }))
        .sort((a, b) => b.value - a.value);
      uploadFile = null;
    } catch (err) {
      uploadError = err instanceof Error ? err.message : 'Gagal upload CSV';
    } finally {
      isUploading = false;
    }
  }

  async function handleFetchNow() {
    if (!ensureApiUrl('fetchError')) return;

    isFetching = true;
    fetchError = '';
    fetchMessage = '';

    try {
      apiClient.setBaseUrl(apiUrl.trim());
      const result = await apiClient.fetchTweets();
      fetchMessage = `Fetch selesai: ${result.inserted}/${result.total} data tersimpan.`;
      fetchStatus = await apiClient.fetchStatus();
    } catch (err) {
      fetchError = err instanceof Error ? err.message : 'Gagal fetch tweet';
    } finally {
      isFetching = false;
    }
  }

  async function handleSetToken() {
    if (!ensureApiUrl('tokenError')) return;

    if (!tokenInput.trim()) {
      tokenError = 'Mohon masukkan Bearer Token';
      return;
    }

    isSettingToken = true;
    tokenError = '';
    tokenMessage = '';

    try {
      apiClient.setBaseUrl(apiUrl.trim());
      await apiClient.setToken(tokenInput.trim());
      tokenMessage = 'Token berhasil diperbarui.';
      tokenInput = '';
    } catch (err) {
      tokenError = err instanceof Error ? err.message : 'Gagal memperbarui token';
    } finally {
      isSettingToken = false;
    }
  }

  async function loadFetchStatus() {
    if (!apiUrl.trim()) {
      return;
    }

    try {
      apiClient.setBaseUrl(apiUrl.trim());
      fetchStatus = await apiClient.fetchStatus();
    } catch (err) {
      fetchError = err instanceof Error ? err.message : 'Gagal mengambil status fetch';
    }
  }

  async function loadHistory() {
    if (!ensureApiUrl('historyError')) return;

    isHistoryLoading = true;
    historyError = '';
    historyMessage = '';

    try {
      apiClient.setBaseUrl(apiUrl.trim());
      const result = await apiClient.getHistory(100, 0);
      analysisHistory.setHistory(result);
    } catch (err) {
      historyError = err instanceof Error ? err.message : 'Gagal memuat history';
    } finally {
      isHistoryLoading = false;
    }
  }

  async function handleDeleteHistory(id: number) {
    if (!ensureApiUrl('historyError')) return;
    if (deletingHistoryId) return;

    deletingHistoryId = id;
    historyError = '';

    try {
      apiClient.setBaseUrl(apiUrl.trim());
      await apiClient.deleteHistoryItem(id);
      analysisHistory.removeHistory(id);
    } catch (err) {
      historyError = err instanceof Error ? err.message : 'Gagal menghapus history';
    } finally {
      deletingHistoryId = null;
    }
  }

  async function handleClearHistory() {
    if (!ensureApiUrl('historyError')) return;

    isClearingHistory = true;
    historyError = '';
    historyMessage = '';

    try {
      apiClient.setBaseUrl(apiUrl.trim());
      await apiClient.clearHistory();
      analysisHistory.clearHistory();
      historyMessage = 'Semua history berhasil dihapus.';
    } catch (err) {
      historyError = err instanceof Error ? err.message : 'Gagal menghapus semua history';
    } finally {
      isClearingHistory = false;
    }
  }

  function handleFileChange(event: Event) {
    const target = event.target as HTMLInputElement;
    uploadFile = target.files && target.files.length > 0 ? target.files[0] : null;
  }

  function formatStatusTime(value: string | null): string {
    if (!value) {
      return '-';
    }
    return new Date(value).toLocaleString('id-ID');
  }

  onMount(() => {
    loadFetchStatus();
    loadHistory();
    const interval = setInterval(loadFetchStatus, 30000);
    return () => clearInterval(interval);
  });
</script>

<div class="min-h-screen bg-gradient-to-br from-blue-50 via-white to-blue-50 py-8 px-4">
  <div class="max-w-6xl mx-auto">
    <header class="text-center mb-8">
      <h1 class="text-4xl md:text-5xl font-bold text-gray-800 mb-3">
        Dashboard Monitoring Sentimen Terkait Banjir & Longsor Sumatera di Platform X
      </h1>
      <p class="text-gray-600 text-lg">
        Analisis sentimen dan kategori dari tweet terkait bencana
      </p>
    </header>

    <nav class="flex flex-wrap justify-center gap-3 mb-8">
      <button
        on:click={() => (activePage = 'input')}
        class={`px-5 py-2.5 rounded-full text-sm font-semibold transition-all ${
          activePage === 'input'
            ? 'bg-blue-600 text-white shadow-md'
            : 'bg-white text-gray-600 border border-gray-200 hover:bg-blue-50'
        }`}
      >
        Input Tweet
      </button>
      <button
        on:click={() => (activePage = 'upload')}
        class={`px-5 py-2.5 rounded-full text-sm font-semibold transition-all ${
          activePage === 'upload'
            ? 'bg-blue-600 text-white shadow-md'
            : 'bg-white text-gray-600 border border-gray-200 hover:bg-blue-50'
        }`}
      >
        Upload CSV
      </button>
      <button
        on:click={() => (activePage = 'fetch')}
        class={`px-5 py-2.5 rounded-full text-sm font-semibold transition-all ${
          activePage === 'fetch'
            ? 'bg-blue-600 text-white shadow-md'
            : 'bg-white text-gray-600 border border-gray-200 hover:bg-blue-50'
        }`}
      >
        Fetch Periodik
      </button>
      <button
        on:click={() => (activePage = 'history')}
        class={`px-5 py-2.5 rounded-full text-sm font-semibold transition-all ${
          activePage === 'history'
            ? 'bg-blue-600 text-white shadow-md'
            : 'bg-white text-gray-600 border border-gray-200 hover:bg-blue-50'
        }`}
      >
        Riwayat
      </button>
    </nav>

    {#if activePage === 'input'}
      <div class="bg-white rounded-2xl shadow-xl p-6 md:p-8 mb-8 border border-gray-100">
        <div class="mb-6">
          <label for="tweetInput" class="block text-sm font-semibold text-gray-700 mb-2">
            Masukkan Teks Tweet
          </label>
          <textarea
            id="tweetInput"
            bind:value={tweetText}
            placeholder="Contoh: Bantuan makanan belum sampai di posko pengungsian desa A."
            rows="5"
            class="w-full px-4 py-3 border-2 border-gray-200 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none transition-all resize-none"
          />
        </div>

        {#if error}
          <div class="mb-6 p-4 bg-red-50 border-l-4 border-red-500 text-red-700 rounded">
            <p class="font-medium">{error}</p>
          </div>
        {/if}

        <button
          on:click={handleAnalysis}
          disabled={isLoading}
          class="w-full bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white font-semibold py-4 px-6 rounded-lg transition-all duration-200 transform hover:scale-[1.02] active:scale-[0.98] disabled:transform-none disabled:cursor-not-allowed shadow-lg"
        >
          {#if isLoading}
            <span class="inline-flex items-center gap-2">
              <svg class="animate-spin h-5 w-5" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
              Menganalisis...
            </span>
          {:else}
            Analisis Tweet
          {/if}
        </button>
      </div>

      {#if latestAnalysis}
        <div class="bg-white rounded-2xl shadow-md p-6 md:p-8 mb-8 border border-gray-100">
          <h3 class="text-xl font-bold text-gray-800 mb-4">Hasil Terbaru</h3>
          <AnalysisResult analysis={latestAnalysis} />
        </div>
      {/if}
    {/if}

    {#if activePage === 'upload'}
      <div class="bg-white rounded-2xl shadow-md p-6 md:p-8 mb-8 border border-gray-100">
        <h3 class="text-xl font-bold text-gray-800 mb-4">Upload Data CSV</h3>
        <input
          type="file"
          accept=".csv"
          on:change={handleFileChange}
          class="w-full text-sm text-gray-600 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100"
        />

        {#if uploadError}
          <div class="mt-4 p-3 bg-red-50 border-l-4 border-red-500 text-red-700 rounded">
            <p class="font-medium">{uploadError}</p>
          </div>
        {/if}

        {#if uploadMessage}
          <div class="mt-4 p-3 bg-green-50 border-l-4 border-green-500 text-green-700 rounded">
            <p class="font-medium">{uploadMessage}</p>
          </div>
        {/if}

        {#if uploadSummary.length > 0}
          <div class="mt-4">
            <h4 class="text-sm font-semibold text-gray-700 mb-2">Distribusi Sentimen</h4>
            <div class="space-y-3 text-sm text-gray-600">
              {#each uploadSummary as item}
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
          <div class="mt-4">
            <h4 class="text-sm font-semibold text-gray-700 mb-2">Distribusi Kategori</h4>
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

        <button
          on:click={handleUpload}
          disabled={isUploading}
          class="mt-4 w-full bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white font-semibold py-3 px-4 rounded-lg transition-all duration-200 disabled:cursor-not-allowed"
        >
          {#if isUploading}
            Mengunggah...
          {:else}
            Upload CSV
          {/if}
        </button>
      </div>
    {/if}

    {#if activePage === 'fetch'}
      <div class="bg-white rounded-2xl shadow-md p-6 md:p-8 mb-8 border border-gray-100">
        <h3 class="text-xl font-bold text-gray-800 mb-2">Fetch Tweet Periodik</h3>
        <p class="text-sm text-gray-600 mb-4">
          Sistem mengambil data setiap 2 jam (atau sesuai konfigurasi backend).
        </p>

        <div class="space-y-2 text-sm text-gray-700">
          <div class="flex justify-between">
            <span>Terakhir Fetch</span>
            <span class="font-semibold">{formatStatusTime(fetchStatus?.last_run ?? null)}</span>
          </div>
          <div class="flex justify-between">
            <span>Jumlah Data</span>
            <span class="font-semibold">{fetchStatus?.last_count ?? 0}</span>
          </div>
          <div class="flex justify-between">
            <span>Tersimpan</span>
            <span class="font-semibold">{fetchStatus?.last_inserted ?? 0}</span>
          </div>
        </div>

        {#if fetchStatus?.last_error}
          <div class="mt-4 p-3 bg-amber-50 border-l-4 border-amber-500 text-amber-700 rounded">
            <p class="font-medium">{fetchStatus.last_error}</p>
          </div>
        {/if}

        {#if fetchError}
          <div class="mt-4 p-3 bg-red-50 border-l-4 border-red-500 text-red-700 rounded">
            <p class="font-medium">{fetchError}</p>
          </div>
        {/if}

        {#if fetchMessage}
          <div class="mt-4 p-3 bg-green-50 border-l-4 border-green-500 text-green-700 rounded">
            <p class="font-medium">{fetchMessage}</p>
          </div>
        {/if}

        <button
          on:click={handleFetchNow}
          disabled={isFetching}
          class="mt-4 w-full bg-emerald-600 hover:bg-emerald-700 disabled:bg-gray-400 text-white font-semibold py-3 px-4 rounded-lg transition-all duration-200 disabled:cursor-not-allowed"
        >
          {#if isFetching}
            Mengambil...
          {:else}
            Fetch Sekarang
          {/if}
        </button>

        <div class="mt-6 border-t border-gray-200 pt-4">
          <h4 class="text-sm font-semibold text-gray-700 mb-2">Update Bearer Token</h4>
          <input
            type="password"
            bind:value={tokenInput}
            placeholder="Masukkan Twitter Bearer Token"
            class="w-full px-3 py-2 border-2 border-gray-200 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none transition-all text-sm"
          />

          {#if tokenError}
            <div class="mt-3 p-2 bg-red-50 border-l-4 border-red-500 text-red-700 rounded">
              <p class="font-medium text-sm">{tokenError}</p>
            </div>
          {/if}

          {#if tokenMessage}
            <div class="mt-3 p-2 bg-green-50 border-l-4 border-green-500 text-green-700 rounded">
              <p class="font-medium text-sm">{tokenMessage}</p>
            </div>
          {/if}

          <button
            on:click={handleSetToken}
            disabled={isSettingToken}
            class="mt-3 w-full bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white font-semibold py-2.5 px-4 rounded-lg transition-all duration-200 disabled:cursor-not-allowed text-sm"
          >
            {#if isSettingToken}
              Menyimpan...
            {:else}
              Simpan Token
            {/if}
          </button>
        </div>
      </div>
    {/if}

    {#if activePage === 'history'}
      <div class="bg-white rounded-2xl shadow-md p-6 md:p-8 mb-8 border border-gray-100">
        <div class="flex flex-col md:flex-row md:items-center md:justify-between gap-4 mb-4">
          <div>
            <h2 class="text-2xl font-bold text-gray-800">
              Riwayat Analisis ({$analysisHistory.length})
            </h2>
            <p class="text-sm text-gray-500">
              Data diambil dari hasil analisis manual di dashboard ini.
            </p>
          </div>
          <div class="flex flex-wrap gap-2">
            <button
              on:click={loadHistory}
              class="px-4 py-2 text-sm text-blue-600 hover:text-blue-700 hover:bg-blue-50 rounded-lg transition-colors font-medium"
            >
              Refresh
            </button>
            <button
              on:click={handleClearHistory}
              disabled={isClearingHistory}
              class="px-4 py-2 text-sm text-red-600 hover:text-red-700 hover:bg-red-50 rounded-lg transition-colors font-medium disabled:cursor-not-allowed disabled:text-gray-400"
            >
              {#if isClearingHistory}
                Menghapus...
              {:else}
                Hapus Semua
              {/if}
            </button>
          </div>
        </div>

        {#if historyError}
          <div class="mb-4 p-3 bg-red-50 border-l-4 border-red-500 text-red-700 rounded">
            <p class="font-medium">{historyError}</p>
          </div>
        {/if}

        {#if historyMessage}
          <div class="mb-4 p-3 bg-green-50 border-l-4 border-green-500 text-green-700 rounded">
            <p class="font-medium">{historyMessage}</p>
          </div>
        {/if}

        {#if isHistoryLoading}
          <div class="py-10 text-center text-gray-500">Memuat history...</div>
        {:else if $analysisHistory.length === 0}
          <div class="text-center py-12 bg-gray-50 rounded-2xl border border-dashed border-gray-200">
            <p class="text-gray-500 text-lg">Belum ada history yang tersimpan.</p>
          </div>
        {:else}
          <div class="grid gap-6 md:grid-cols-2">
            {#each $analysisHistory as analysis (analysis.id)}
              <div class="relative">
                <button
                  on:click={() => handleDeleteHistory(analysis.id)}
                  disabled={deletingHistoryId === analysis.id}
                  class="absolute top-4 right-4 text-xs text-red-600 hover:text-red-700 bg-white/90 px-3 py-1 rounded-full shadow border border-gray-100 disabled:cursor-not-allowed disabled:text-gray-400"
                >
                  {#if deletingHistoryId === analysis.id}
                    Menghapus...
                  {:else}
                    Hapus
                  {/if}
                </button>
                <AnalysisResult {analysis} />
              </div>
            {/each}
          </div>
        {/if}
      </div>
    {/if}
  </div>
</div>
