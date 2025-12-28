import { writable } from 'svelte/store';
import type { PredictionResponse } from '../services/api';

export interface AnalysisHistory extends PredictionResponse {
  id: string;
  timestamp: Date;
}

function createAnalysisStore() {
  const { subscribe, update } = writable<AnalysisHistory[]>([]);

  return {
    subscribe,
    addAnalysis: (analysis: PredictionResponse) => {
      const historyItem: AnalysisHistory = {
        ...analysis,
        id: crypto.randomUUID(),
        timestamp: new Date(),
      };
      update(history => [historyItem, ...history]);
    },
    clearHistory: () => {
      update(() => []);
    },
  };
}

export const analysisHistory = createAnalysisStore();
