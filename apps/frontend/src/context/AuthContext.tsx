import {
  createContext,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";
import { getMe, registerUser } from "../api";
import { apiRequest, clearToken, getToken, setToken } from "../api/client";
import type { User } from "../api/types";

type AuthContextValue = {
  user: User | null;
  ready: boolean;
  isAuthenticated: boolean;
  login: (email: string, password: string) => Promise<User>;
  register: (input: {
    email: string;
    password: string;
    name?: string;
    phone?: string;
  }) => Promise<User>;
  logout: () => void;
};

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [ready, setReady] = useState(false);

  useEffect(() => {
    if (!getToken()) {
      setReady(true);
      return;
    }
    getMe()
      .then(setUser)
      .catch(() => {
        clearToken();
        setUser(null);
      })
      .finally(() => setReady(true));
  }, []);

  const value = useMemo<AuthContextValue>(
    () => ({
      user,
      ready,
      isAuthenticated: Boolean(user),
      async login(email, password) {
        const body = new URLSearchParams();
        body.set("username", email);
        body.set("password", password);
        const token = await apiRequest<{ access_token: string }>("/api/users/login", {
          method: "POST",
          body,
        });
        setToken(token.access_token);
        const me = await getMe();
        setUser(me);
        return me;
      },
      async register(input) {
        await registerUser(input);
        const body = new URLSearchParams();
        body.set("username", input.email);
        body.set("password", input.password);
        const token = await apiRequest<{ access_token: string }>("/api/users/login", {
          method: "POST",
          body,
        });
        setToken(token.access_token);
        const me = await getMe();
        setUser(me);
        return me;
      },
      logout() {
        clearToken();
        setUser(null);
      },
    }),
    [user, ready],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
