const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:5000";

function withQuery(path, params = {}) {
  const query = new URLSearchParams(
    Object.entries(params).filter(([, value]) => value !== undefined && value !== null && value !== "")
  ).toString();
  return query ? `${path}?${query}` : path;
}

export async function apiRequest(path, options = {}) {
  const token = window.localStorage.getItem("walkrun_token");
  const controller = new AbortController();
  const timeoutId = window.setTimeout(() => controller.abort(), 30000);
  const isFormData = options.body instanceof FormData;
  let response;

  try {
    response = await fetch(`${API_BASE_URL}${path}`, {
      ...options,
      signal: controller.signal,
      headers: {
        ...(isFormData ? {} : { "Content-Type": "application/json" }),
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
        ...options.headers,
      },
    });
  } catch (error) {
    if (error.name === "AbortError") {
      throw new Error("API request timed out. Check that the backend is running and the database is reachable.");
    }
    throw error;
  } finally {
    window.clearTimeout(timeoutId);
  }

  const body = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(body.error || "Something went wrong");
  }
  return body;
}

export const api = {
  register: (payload) => apiRequest("/api/auth/register", { method: "POST", body: JSON.stringify(payload) }),
  login: (payload) => apiRequest("/api/auth/login", { method: "POST", body: JSON.stringify(payload) }),
  forgotPassword: (payload) => apiRequest("/api/auth/forgot-password", { method: "POST", body: JSON.stringify(payload) }),
  resetPassword: (payload) => apiRequest("/api/auth/reset-password", { method: "POST", body: JSON.stringify(payload) }),
  me: () => apiRequest("/api/auth/me"),
  updateMe: (payload) => apiRequest("/api/auth/me", { method: "PATCH", body: JSON.stringify(payload) }),
  crews: () => apiRequest("/api/crews"),
  nearbyCrews: (params) => apiRequest(withQuery("/api/crews/nearby", params)),
  createCrew: (payload) => apiRequest("/api/crews", { method: "POST", body: JSON.stringify(payload) }),
  myCrewApplications: () => apiRequest("/api/crews/applications/me"),
  submitCrewApplication: (payload) => apiRequest("/api/crews/applications", { method: "POST", body: payload }),
  crew: (id) => apiRequest(`/api/crews/${id}`),
  crewStats: (id) => apiRequest(`/api/crews/${id}/stats`),
  crewReports: (id) => apiRequest(`/api/crews/${id}/reports`),
  updateCrewMemberRole: (crewId, userId, role) =>
    apiRequest(`/api/crews/${crewId}/members/${userId}/role`, { method: "PATCH", body: JSON.stringify({ role }) }),
  joinCrew: (id) => apiRequest(`/api/crews/${id}/join`, { method: "POST" }),
  nearbySessions: (params) => apiRequest(withQuery("/api/sessions/nearby", params)),
  session: (id) => apiRequest(`/api/sessions/${id}`),
  joinSession: (id) => apiRequest(`/api/sessions/${id}/join`, { method: "POST" }),
  checkIn: (id) => apiRequest(`/api/sessions/${id}/check-in`, { method: "POST" }),
  checkOut: (id) => apiRequest(`/api/sessions/${id}/check-out`, { method: "POST" }),
  cancelSession: (id) => apiRequest(`/api/sessions/${id}/cancel`, { method: "POST" }),
  completeSession: (id) => apiRequest(`/api/sessions/${id}/complete`, { method: "POST" }),
  markNoShow: (sessionId, userId) =>
    apiRequest(`/api/sessions/${sessionId}/attendees/${userId}/no-show`, { method: "POST" }),
  createSession: (crewId, payload) =>
    apiRequest(`/api/crews/${crewId}/sessions`, { method: "POST", body: JSON.stringify(payload) }),
  createActivity: (payload) => apiRequest("/api/activities", { method: "POST", body: JSON.stringify(payload) }),
  activities: () => apiRequest("/api/activities/me"),
  activity: (id) => apiRequest(`/api/activities/${id}`),
  activityStats: () => apiRequest("/api/activities/me/stats"),
  deleteActivity: (id) => apiRequest(`/api/activities/${id}`, { method: "DELETE" }),
  reportUser: (payload) => apiRequest("/api/safety/reports", { method: "POST", body: JSON.stringify(payload) }),
  blockUser: (payload) => apiRequest("/api/safety/blocks", { method: "POST", body: JSON.stringify(payload) }),
  blocks: () => apiRequest("/api/safety/blocks"),
  reports: () => apiRequest("/api/safety/reports"),
  adminOverview: () => apiRequest("/api/admin/overview"),
  sendBroadcast: (payload) => apiRequest("/api/admin/broadcasts", { method: "POST", body: JSON.stringify(payload) }),
  reviewCrewApplication: (applicationId, payload) =>
    apiRequest(`/api/admin/crew-applications/${applicationId}`, { method: "PATCH", body: JSON.stringify(payload) }),
  crewApplicationSelfie: (applicationId) =>
    fetch(`${API_BASE_URL}/api/admin/crew-applications/${applicationId}/selfie`, {
      headers: { Authorization: `Bearer ${window.localStorage.getItem("walkrun_token")}` },
    }).then((response) => {
      if (!response.ok) {
        throw new Error("Could not load selfie");
      }
      return response.blob();
    }),
  updatePlatformRole: (userId, platform_role) =>
    apiRequest(`/api/admin/users/${userId}/role`, { method: "PATCH", body: JSON.stringify({ platform_role }) }),
  forumThreads: () => apiRequest("/api/forum/threads"),
  createForumThread: (payload) => apiRequest("/api/forum/threads", { method: "POST", body: JSON.stringify(payload) }),
  crewForumThreads: (crewId) => apiRequest(`/api/forum/crews/${crewId}/threads`),
  createCrewForumThread: (crewId, payload) =>
    apiRequest(`/api/forum/crews/${crewId}/threads`, { method: "POST", body: JSON.stringify(payload) }),
  forumThread: (threadId) => apiRequest(`/api/forum/threads/${threadId}`),
  createForumReply: (threadId, payload) =>
    apiRequest(`/api/forum/threads/${threadId}/replies`, { method: "POST", body: JSON.stringify(payload) }),
  updateForumThread: (threadId, payload) =>
    apiRequest(`/api/forum/threads/${threadId}`, { method: "PATCH", body: JSON.stringify(payload) }),
};
