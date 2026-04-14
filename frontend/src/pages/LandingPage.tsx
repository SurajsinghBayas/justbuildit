import { Link } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from "@/components/ui/card";

export default function LandingPage() {
  return (
    <div className="flex flex-col min-h-screen">
      {/* Navbar Minimal */}
      <header className="p-6 flex justify-between items-center bg-white border-b border-gray-100">
        <div className="font-bold text-2xl tracking-tighter text-gray-900">justbuildit.</div>
        <div className="flex gap-4">
          <Link to="/login">
            <Button variant="outline" className="rounded-full bg-white text-gray-900 border-gray-200">Log in</Button>
          </Link>
          <Link to="/register">
            <Button className="rounded-full bg-primary text-primary-foreground hover:bg-primary/90">Get Started</Button>
          </Link>
        </div>
      </header>
      
      {/* Hero Section */}
      <main className="flex-1 flex flex-col items-center justify-center p-8 bg-gray-50 text-center">
        <div className="max-w-3xl space-y-6">
          <h1 className="text-6xl md:text-7xl font-extrabold tracking-tight text-gray-900 leading-tight">
            Manage your <span className="text-secondary bg-secondary/20 px-2 rounded-lg">projects</span> brilliantly.
          </h1>
          <p className="text-xl text-gray-600 font-medium">
            AI-powered task management without the clutter. Beautiful, simple, and absolutely no gradients.
          </p>
          <div className="pt-8 flex justify-center gap-4">
            <Link to="/dashboard">
              <Button size="lg" className="rounded-full bg-accent text-accent-foreground hover:bg-accent/90 text-lg px-8 py-6">
                Go to Dashboard
              </Button>
            </Link>
          </div>
        </div>
        
        {/* Features using cards */}
        <div className="grid md:grid-cols-3 gap-8 mt-24 max-w-5xl">
          <Card className="bg-white border border-gray-100 shadow-sm hover:shadow-xl hover:-translate-y-2 transition-all duration-300 pb-0 pt-6">
            <CardContent>
              <div className="h-12 w-12 bg-primary/10 rounded-2xl flex items-center justify-center mb-6">
                <div className="h-6 w-6 rounded-full bg-primary" />
              </div>
              <h3 className="font-bold text-xl mb-2 text-gray-900">Organization</h3>
              <p className="text-gray-500">Keep teams aligned in one place.</p>
            </CardContent>
          </Card>
          <Card className="bg-white border border-gray-100 shadow-sm hover:shadow-xl hover:-translate-y-2 transition-all duration-300 pb-0 pt-6">
            <CardContent>
              <div className="h-12 w-12 bg-secondary rounded-2xl flex items-center justify-center mb-6">
                <div className="h-6 w-6 rounded-full bg-secondary-foreground" />
              </div>
              <h3 className="font-bold text-xl mb-2 text-gray-900">Projects</h3>
              <p className="text-gray-500">Streamline tasks efficiently.</p>
            </CardContent>
          </Card>
          <Card className="bg-white border border-gray-100 shadow-sm hover:shadow-xl hover:-translate-y-2 transition-all duration-300 pb-0 pt-6">
            <CardContent>
              <div className="h-12 w-12 bg-accent rounded-2xl flex items-center justify-center mb-6">
                <div className="h-6 w-6 rounded-full bg-accent-foreground" />
              </div>
              <h3 className="font-bold text-xl mb-2 text-gray-900">Analytics</h3>
              <p className="text-gray-500">Understand your velocity easily.</p>
            </CardContent>
          </Card>
        </div>
      </main>
    </div>
  );
}
