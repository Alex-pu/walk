export function createActivityTimer() {
  let startedAt = null;
  let pausedAt = null;
  let pausedTotalMs = 0;

  return {
    start(snapshot) {
      startedAt = snapshot?.startedAt || Date.now();
      pausedAt = snapshot?.pausedAt || null;
      pausedTotalMs = snapshot?.pausedTotalMs || 0;
    },
    pause() {
      if (!pausedAt) pausedAt = Date.now();
    },
    resume() {
      if (pausedAt) {
        pausedTotalMs += Date.now() - pausedAt;
        pausedAt = null;
      }
    },
    getDurationSeconds() {
      if (!startedAt) return 0;
      const end = pausedAt || Date.now();
      return Math.floor((end - startedAt - pausedTotalMs) / 1000);
    },
    getSnapshot() {
      return { startedAt, pausedAt, pausedTotalMs };
    },
  };
}
