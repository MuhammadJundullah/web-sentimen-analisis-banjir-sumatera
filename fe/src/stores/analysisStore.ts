import { writable } from 'svelte/store';
import type { AnalysisHistoryItem } from '../services/api';

export type AnalysisHistory = AnalysisHistoryItem;

function createAnalysisStore() {
  const { subscribe, update, set } = writable<AnalysisHistory[]>([]);

  return {
    subscribe,
    setHistory: (items: AnalysisHistory[]) => set(items),
    addAnalysis: (analysis: AnalysisHistory) => {
      update(history => [analysis, ...history]);
    },
    removeHistory: (id: number) => {
      update(history => history.filter(item => item.id !== id));
    },
    clearHistory: () => set([]),
  };
}

export const analysisHistory = createAnalysisStore();
