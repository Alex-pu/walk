import React, { createContext, useContext, useEffect, useMemo, useState } from "react";

import { api } from "../api/client.js";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!window.localStorage.getItem("walkrun_token")) {
      setLoading(false);
      return;
    }

    api
      .me()
      .then((data) => setUser(data.user))
      .catch(() => window.localStorage.removeItem("walkrun_token"))
      .finally(() => setLoading(false));
  }, []);

  async function login(payload) {
    const data = await api.login(payload);
    window.localStorage.setItem("walkrun_token", data.access_token);
    setUser(data.user);
  }

  async function register(payload) {
    const data = await api.register(payload);
    window.localStorage.setItem("walkrun_token", data.access_token);
    setUser(data.user);
  }

  async function updateProfile(payload) {
    const data = await api.updateMe(payload);
    setUser(data.user);
    return data.user;
  }

  function logout() {
    window.localStorage.removeItem("walkrun_token");
    setUser(null);
  }

  const value = useMemo(() => ({ user, loading, login, register, updateProfile, logout }), [user, loading]);
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  return useContext(AuthContext);
}
