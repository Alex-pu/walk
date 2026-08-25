const DB_NAME = "walkrun_activity_store";
const DB_VERSION = 1;
const ACTIVE_STORE = "active";
const PENDING_STORE = "pending";
const ACTIVE_KEY = "current";
const CONTEXT_KEY = "walkrun_activity_context";
const LEGACY_ACTIVE_KEY = "walkrun_active_activity";
const LEGACY_PENDING_KEY = "walkrun_pending_activities";

function openDatabase() {
  return new Promise((resolve, reject) => {
    if (!window.indexedDB) {
      reject(new Error("IndexedDB is not available"));
      return;
    }

    const request = window.indexedDB.open(DB_NAME, DB_VERSION);
    request.onupgradeneeded = () => {
      const db = request.result;
      if (!db.objectStoreNames.contains(ACTIVE_STORE)) {
        db.createObjectStore(ACTIVE_STORE);
      }
      if (!db.objectStoreNames.contains(PENDING_STORE)) {
        db.createObjectStore(PENDING_STORE, { keyPath: "local_id" });
      }
    };
    request.onsuccess = () => resolve(request.result);
    request.onerror = () => reject(request.error);
  });
}

async function withStore(storeName, mode, callback) {
  const db = await openDatabase();
  return new Promise((resolve, reject) => {
    const transaction = db.transaction(storeName, mode);
    const store = transaction.objectStore(storeName);
    const request = callback(store);

    request.onsuccess = () => resolve(request.result);
    request.onerror = () => reject(request.error);
    transaction.oncomplete = () => db.close();
    transaction.onerror = () => {
      db.close();
      reject(transaction.error);
    };
  });
}

export async function saveActiveActivity(activity) {
  return withStore(ACTIVE_STORE, "readwrite", (store) => store.put(activity, ACTIVE_KEY));
}

export async function loadActiveActivity() {
  const saved = await withStore(ACTIVE_STORE, "readonly", (store) => store.get(ACTIVE_KEY));
  if (saved) return saved;

  const legacy = window.localStorage.getItem(LEGACY_ACTIVE_KEY);
  if (!legacy) return null;
  const activity = JSON.parse(legacy);
  await saveActiveActivity(activity);
  window.localStorage.removeItem(LEGACY_ACTIVE_KEY);
  return activity;
}

export async function clearActiveActivity() {
  return withStore(ACTIVE_STORE, "readwrite", (store) => store.delete(ACTIVE_KEY));
}

export async function savePendingActivity(activity) {
  return withStore(PENDING_STORE, "readwrite", (store) => store.put(activity));
}

export async function loadPendingActivities() {
  const saved = await withStore(PENDING_STORE, "readonly", (store) => store.getAll());
  const legacy = window.localStorage.getItem(LEGACY_PENDING_KEY);
  if (!legacy) return saved;

  const legacyActivities = JSON.parse(legacy);
  for (const activity of legacyActivities) {
    await savePendingActivity(activity);
  }
  window.localStorage.removeItem(LEGACY_PENDING_KEY);
  return [...saved, ...legacyActivities];
}

export async function removePendingActivity(localId) {
  return withStore(PENDING_STORE, "readwrite", (store) => store.delete(localId));
}

export function saveActivityContext(context) {
  window.localStorage.setItem(CONTEXT_KEY, JSON.stringify(context));
}

export function loadActivityContext() {
  const value = window.localStorage.getItem(CONTEXT_KEY);
  return value ? JSON.parse(value) : null;
}

export function clearActivityContext() {
  window.localStorage.removeItem(CONTEXT_KEY);
}
