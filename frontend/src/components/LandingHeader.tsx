import { Link } from "react-router-dom";
import { Button } from "@/components/ui/button";

export default function LandingHeader() {
  const isAuthenticated = !!localStorage.getItem('access_token');

  return (
    <header className="px-6 py-4 flex justify-between items-center border-b border-gray-100 backdrop-blur-md bg-white/70 sticky top-0 z-50">
      <div className="flex items-center gap-2">
        <Link to="/" className="flex items-center gap-2 group">
          <div className="w-8 h-8 bg-black rounded-lg flex items-center justify-center transition-transform group-hover:scale-105">
            <span className="text-white font-black text-lg">
              J
            </span>
          </div>
          <span className="font-bold text-xl tracking-tight text-gray-900">
            justbuildit
          </span>
        </Link>
      </div>
      <nav className="hidden md:flex gap-8 text-sm font-medium text-gray-600">
        <Link
          to="/docs"
          className="hover:text-black transition-colors"
        >
          Documentation
        </Link>
        <Link
          to={isAuthenticated ? "/projects" : "/login"}
          className="hover:text-black transition-colors"
        >
          Product
        </Link>
        <a
          href="https://github.com/SurajsinghBayas/justbuildit"
          target="_blank"
          rel="noreferrer"
          className="hover:text-black transition-colors"
        >
          GitHub
        </a>
      </nav>
      <div className="flex gap-3">
        {isAuthenticated ? (
          <Link to="/dashboard">
            <Button className="bg-black text-white hover:bg-gray-800 shadow-xl shadow-black/10">
              Dashboard
            </Button>
          </Link>
        ) : (
          <>
            <Link to="/login">
              <Button variant="ghost">
                Log in
              </Button>
            </Link>
            <Link to="/register">
              <Button className="bg-black text-white hover:bg-gray-800 shadow-xl shadow-black/10">
                Get Started
              </Button>
            </Link>
          </>
        )}
      </div>
    </header>
  );
}
