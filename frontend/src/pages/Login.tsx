import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  CardDescription,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import apiClient from "@/api/client";
import { Loader2 } from "lucide-react";

export default function Login() {
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError("");

    try {
      const response = await apiClient.post("/auth/login", {
        email,
        password,
      });

      localStorage.setItem("access_token", response.data.access_token);
      if (response.data.refresh_token) {
        localStorage.setItem("refresh_token", response.data.refresh_token);
      }

      // Use internal navigation to maintain state
      navigate("/dashboard");
    } catch (err: any) {
      setError(err.response?.data?.detail || "Invalid email or password.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col justify-center items-center p-4">
      <Link
        to="/"
        className="absolute top-8 left-8 font-bold text-xl tracking-tighter text-gray-900"
      >
        justbuildit.
      </Link>

      <div className="w-full max-w-[400px]">
        <Card className="border border-gray-200 shadow-sm rounded-xl">
          <CardHeader className="space-y-2 text-center pb-6">
            <CardTitle className="text-2xl font-bold tracking-tight text-gray-900">
              Welcome back
            </CardTitle>
            <CardDescription className="text-sm font-medium text-gray-500">
              Enter your credentials to access your account
            </CardDescription>
          </CardHeader>
          <CardContent>
            {error && (
              <div className="mb-4 p-3 rounded-md bg-red-50 text-red-600 border border-red-100 text-sm font-medium text-center">
                {error}
              </div>
            )}
            <form onSubmit={handleLogin} className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="email">Email address</Label>
                <Input
                  id="email"
                  type="email"
                  placeholder="name@example.com"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                  className="border-gray-200"
                  disabled={loading}
                />
              </div>
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <Label htmlFor="password">Password</Label>
                  <Link
                    to="#"
                    className="text-xs font-semibold text-gray-600 hover:text-gray-900"
                  >
                    Forgot password?
                  </Link>
                </div>
                <Input
                  id="password"
                  type="password"
                  placeholder="••••••••"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                  className="border-gray-200"
                  disabled={loading}
                />
              </div>
              <Button
                type="submit"
                className="w-full bg-gray-900 text-white hover:bg-gray-800 shadow-sm transition-all h-10 mt-2"
                disabled={loading}
              >
                {loading ? (
                  <Loader2 className="w-4 h-4 animate-spin mr-2" />
                ) : null}
                {loading ? "Logging in..." : "Log In"}
              </Button>
            </form>

            <p className="mt-6 text-center text-sm text-gray-600 font-medium">
              Don't have an account?{" "}
              <Link
                to="/register"
                className="font-semibold text-gray-900 hover:underline"
              >
                Sign up
              </Link>
            </p>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
