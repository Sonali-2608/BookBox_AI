import { createContext, useCallback, useEffect, useMemo, useState } from "react";
import { authApi, getStoredToken, setStoredToken } from "../services/api";

export const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);

  // On first load, if we have a stored token, verify it's still valid by
  // fetching the current user rather than trusting it blindly.
  useEffect(() => {
    const token = getStoredToken();
    if (!token) {
      setIsLoading(false);
      return;
    }

    authApi
      .getMe()
      .then((res) => setUser(res.data))
      .catch(() => setStoredToken(null))
      .finally(() => setIsLoading(false));
  }, []);

  const loginWithGoogleCredential = useCallback(async (credential) => {
    setError(null);
    try {
      const res = await authApi.loginWithGoogle(credential);
      setStoredToken(res.data.access_token);
      setUser(res.data.user);
      return res.data.user;
    } catch (err) {
      setError("We couldn't sign you in. Please try again.");
      throw err;
    }
  }, []);

  const logout = useCallback(async () => {
    try {
      await authApi.logout();
    } catch {
      // Even if the network call fails, the token is discarded locally —
      // logout should always succeed from the user's point of view.
    }
    setStoredToken(null);
    setUser(null);
  }, []);

  const value = useMemo(
    () => ({
      user,
      isAuthenticated: Boolean(user),
      isLoading,
      error,
      loginWithGoogleCredential,
      logout,
    }),
    [user, isLoading, error, loginWithGoogleCredential, logout]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}
