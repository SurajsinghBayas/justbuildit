import { useEffect } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { Loader2 } from "lucide-react";

/**
 * Handles the redirect back from Google OAuth.
 * The backend redirects here with ?access_token=...&refresh_token=...
 * We store them and push the user to /dashboard.
 */
export default function AuthCallback() {
  const [params] = useSearchParams();
  const navigate = useNavigate();

  useEffect(() => {
    const accessToken = params.get("access_token");
    const refreshToken = params.get("refresh_token");

    if (accessToken) {
      localStorage.setItem("access_token", accessToken);
      if (refreshToken) localStorage.setItem("refresh_token", refreshToken);
      navigate("/dashboard", { replace: true });
    } else {
      // Something went wrong — send back to login with an error hint
      navigate("/login?error=google_failed", { replace: true });
    }
  }, []);

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col items-center justify-center gap-4">
      <Loader2 className="w-8 h-8 animate-spin text-gray-400" />
      <p className="text-sm font-medium text-gray-500">Signing you in with Google…</p>
    </div>
  );
}
