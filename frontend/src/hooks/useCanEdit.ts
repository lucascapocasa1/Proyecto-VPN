import { useAuth } from "../context/AuthContext";

export function useCanEdit(): boolean {
  const { user } = useAuth();
  return user?.role === "SUPERADMIN" || user?.role === "ADMIN_LIGA";
}
