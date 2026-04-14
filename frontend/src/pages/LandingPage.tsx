import { Link } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from "@/components/ui/card";
import { ArrowRight, LayoutDashboard, Zap, ShieldCheck, GitBranch, Brain, Users } from 'lucide-react';

export default function LandingPage() {
  return (
    <div className="flex flex-col min-h-screen bg-white overflow-hidden">

      {/* NAVBAR */}
      <header className="px-6 py-4 flex justify-between items-center border-b border-gray-100 backdrop-blur-md bg-white/70 sticky top-0 z-50">
        <div className="font-bold text-xl tracking-tight text-gray-900">
          justbuildit.
        </div>
        <div className="flex gap-4">
          <Link to="/login">
            <Button variant="ghost">Log in</Button>
          </Link>
          <Link to="/register">
            <Button className="bg-black text-white hover:bg-gray-800">
              Get Started
            </Button>
          </Link>
        </div>
      </header>

      {/* HERO */}
      <main className="flex-1 flex flex-col items-center justify-center px-6 py-24 text-center relative">

        {/* Background Glow */}
        <div className="absolute top-[-100px] w-[600px] h-[600px] bg-gray-200 rounded-full blur-3xl opacity-40" />

        <div className="max-w-4xl space-y-8 relative z-10">

          <span className="px-4 py-1 text-xs rounded-full border border-gray-200">
            justbuildit 2.0 🚀
          </span>

          <h1 className="text-5xl md:text-7xl font-extrabold leading-tight">
            Build faster. <br />
            Manage smarter.
          </h1>

          <p className="text-lg text-gray-500 max-w-2xl mx-auto">
            The modern project OS for teams. Tasks, AI insights, GitHub sync — all in one place.
          </p>

          <div className="flex justify-center gap-4 pt-6">
            <Link to="/register">
              <Button size="lg" className="bg-black text-white px-8">
                Start Free
              </Button>
            </Link>
            <Link to="/login">
              <Button size="lg" variant="outline">
                Live Demo <ArrowRight className="ml-2 w-4 h-4" />
              </Button>
            </Link>
          </div>

          {/* STATS */}
          <div className="flex justify-center gap-10 pt-12 text-sm text-gray-600">
            <Stat number="10x" label="Faster Workflow" />
            <Stat number="99%" label="Task Visibility" />
            <Stat number="24/7" label="Team Sync" />
          </div>
        </div>
      </main>

      {/* FEATURES GRID */}
      <section className="px-6 py-20 max-w-6xl mx-auto grid md:grid-cols-3 gap-6">
        <FeatureCard icon={<LayoutDashboard />} title="Smart Workspace" desc="Everything organized across teams and projects." />
        <FeatureCard icon={<Zap />} title="Real-time Sync" desc="Instant updates across all devices." />
        <FeatureCard icon={<ShieldCheck />} title="Secure" desc="Enterprise-level security for your data." />
        <FeatureCard icon={<GitBranch />} title="GitHub Sync" desc="Track commits, PRs, and progress seamlessly." />
        <FeatureCard icon={<Brain />} title="AI Insights" desc="Predict delays and get smart suggestions." />
        <FeatureCard icon={<Users />} title="Team Control" desc="Role-based access for structured workflows." />
      </section>

      {/* INTERACTIVE SECTION */}
      <section className="bg-gray-50 py-20 px-6 text-center">
        <h2 className="text-3xl font-bold mb-6">See how it works</h2>
        <p className="text-gray-500 mb-12">Hover to explore features</p>

        <div className="grid md:grid-cols-3 gap-6 max-w-5xl mx-auto">
          <HoverCard title="Kanban Board" desc="Drag and drop tasks effortlessly." />
          <HoverCard title="AI Predictions" desc="Know delays before they happen." />
          <HoverCard title="Live Collaboration" desc="Work together in real-time." />
        </div>
      </section>

      {/* CTA */}
      <section className="py-24 text-center">
        <h2 className="text-4xl font-bold mb-4">Ready to build better?</h2>
        <p className="text-gray-500 mb-8">Join teams building faster with JustBuildIt.</p>

        <Link to="/register">
          <Button size="lg" className="bg-black text-white px-10">
            Get Started Now
          </Button>
        </Link>
      </section>

      {/* FOOTER */}
      <footer className="border-t py-6 text-center text-gray-500 text-sm">
        © {new Date().getFullYear()} justbuildit.
      </footer>
    </div>
  );
}

/* ---------------- COMPONENTS ---------------- */

function FeatureCard({ icon, title, desc }: any) {
  return (
    <Card className="group hover:shadow-lg transition-all duration-300 hover:-translate-y-1 cursor-pointer">
      <CardContent className="p-6">
        <div className="mb-4 text-gray-700 group-hover:scale-110 transition">
          {icon}
        </div>
        <h3 className="font-semibold text-lg">{title}</h3>
        <p className="text-gray-500 text-sm mt-2">{desc}</p>
      </CardContent>
    </Card>
  );
}

function HoverCard({ title, desc }: any) {
  return (
    <div className="p-8 bg-white border rounded-xl hover:bg-black hover:text-white transition-all duration-300 cursor-pointer">
      <h3 className="text-lg font-semibold mb-2">{title}</h3>
      <p className="text-sm opacity-70">{desc}</p>
    </div>
  );
}

function Stat({ number, label }: any) {
  return (
    <div>
      <div className="text-2xl font-bold text-black">{number}</div>
      <div>{label}</div>
    </div>
  );
}