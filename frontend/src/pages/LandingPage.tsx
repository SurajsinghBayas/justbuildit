import { Link } from "react-router-dom";
import { Button } from "@/components/ui/button";
import {
  LayoutDashboard,
  Zap,
  ShieldCheck,
  GitBranch,
  Brain,
  Sparkles,
  CheckCircle2,
  ChevronRight,
  PlayCircle,
} from "lucide-react";
import LandingHeader from "@/components/LandingHeader";
import Footer from "@/components/Footer";

export default function LandingPage() {
  const isAuthenticated = !!localStorage.getItem('access_token');

  return (
    <div className="flex flex-col min-h-screen bg-white transition-colors selection:bg-violet-100 selection:text-violet-900">
      <LandingHeader />

      <main className="flex-1">
        {/* HERO SECTION */}
        <section className="relative pt-20 pb-32 overflow-hidden px-6">
          {/* Decorative Gradients */}
          <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[1000px] h-[600px] bg-gradient-to-b from-violet-100/50 to-transparent rounded-full blur-3xl -z-10 pointer-events-none" />

          <div className="max-w-7xl mx-auto flex flex-col items-center text-center">
            <div className="inline-flex items-center gap-2 px-3 py-1 bg-gray-50 border border-gray-100 rounded-full mb-8 animate-fade-in">
              <span className="flex h-2 w-2 rounded-full bg-violet-600 animate-pulse" />
              <span className="text-xs font-bold text-gray-600 uppercase tracking-widest">
                Now with AWS Bedrock Intelligence
              </span>
            </div>

            <h1 className="text-6xl md:text-8xl font-black text-gray-900 leading-[1.1] mb-8 tracking-tighter">
              Ship products <br />
              <span className="text-transparent bg-clip-text bg-gradient-to-r from-violet-600 to-indigo-600">
                not just features.
              </span>
            </h1>

            <p className="text-xl md:text-2xl text-gray-500 max-w-3xl mx-auto mb-12 font-medium leading-relaxed">
              The AI-native project OS for engineering teams. Automatically
              break down roadmaps, sync with GitHub, and predict delivery risks
              before they happen.
            </p>

            <div className="flex flex-col sm:flex-row gap-4 mb-20">
              <Link to={isAuthenticated ? "/dashboard" : "/register"}>
                <Button
                  size="lg"
                  className="h-14 px-10 bg-black text-white text-lg font-bold rounded-2xl shadow-2xl shadow-violet-500/20"
                >
                  {isAuthenticated ? "Go to Dashboard" : "Build Now — Free"}
                </Button>
              </Link>
              <Link to="/login">
                <Button
                  size="lg"
                  variant="outline"
                  className="h-14 px-10 text-lg font-bold rounded-2xl border-2"
                >
                  <PlayCircle className="mr-2 w-5 h-5" /> Watch Demo
                </Button>
              </Link>
            </div>

            {/* Dashboard Preview Mockup */}
            <div className="relative w-full max-w-5xl group">
              <div className="absolute -inset-1 bg-gradient-to-r from-violet-600 to-indigo-600 rounded-[32px] blur opacity-20 group-hover:opacity-40 transition duration-1000 group-hover:duration-200"></div>
              <div className="relative bg-white border border-gray-100 rounded-[30px] shadow-2xl overflow-hidden aspect-[16/10] flex flex-col">
                <div className="h-10 bg-gray-50 border-b flex items-center px-4 gap-1.5">
                  <div className="w-2.5 h-2.5 rounded-full bg-red-400" />
                  <div className="w-2.5 h-2.5 rounded-full bg-amber-400" />
                  <div className="w-2.5 h-2.5 rounded-full bg-green-400" />
                  <div className="ml-4 h-5 w-48 bg-gray-200 rounded flex-1" />
                </div>
                <div className="flex-1 p-8 flex gap-6">
                  <div className="w-1/4 space-y-4">
                    <div className="h-8 bg-gray-100 rounded-lg animate-pulse" />
                    <div className="h-8 bg-gray-50 rounded-lg" />
                    <div className="h-8 bg-gray-50 rounded-lg" />
                  </div>
                  <div className="flex-1 grid grid-cols-2 gap-6">
                    <div className="bg-gray-50 rounded-2xl p-6 space-y-4 border border-gray-100">
                      <div className="h-4 w-24 bg-violet-200 rounded" />
                      <div className="space-y-2">
                        <div className="h-4 w-full bg-gray-200 rounded" />
                        <div className="h-4 w-3/4 bg-gray-200 rounded" />
                      </div>
                    </div>
                    <div className="bg-gray-50 rounded-2xl p-6 space-y-4 border border-gray-100">
                      <div className="h-4 w-24 bg-indigo-200 rounded" />
                      <div className="space-y-2">
                        <div className="h-4 w-full bg-gray-200 rounded" />
                        <div className="h-4 w-1/2 bg-gray-200 rounded" />
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* LOGOS / TRUST */}
        <section className="py-12 border-y border-gray-100 bg-gray-50/50">
          <div className="max-w-7xl mx-auto px-6 flex flex-wrap justify-center items-center gap-12 grayscale opacity-50">
            <span className="font-bold text-2xl tracking-tighter">
              AWS NOVA
            </span>
            <span className="font-bold text-2xl tracking-tighter">GITHUB</span>
            <span className="font-bold text-2xl tracking-tighter">FASTAPI</span>
            <span className="font-bold text-2xl tracking-tighter">
              POSTGRES
            </span>
            <span className="font-bold text-2xl tracking-tighter">REACT</span>
          </div>
        </section>

        {/* FEATURES OVERVIEW */}
        <section className="py-32 px-6">
          <div className="max-w-7xl mx-auto">
            <div className="text-center mb-20">
              <h2 className="text-4xl md:text-5xl font-black text-gray-900 mb-6">
                Built for High-Velocity Teams
              </h2>
              <p className="text-lg text-gray-500 max-w-2xl mx-auto">
                Ditch the manual issue tracking. JustBuildIt uses
                state-of-the-art LLMs and predictive modeling to manage the
                grunt work.
              </p>
            </div>

            <div className="grid md:grid-cols-3 gap-10">
              <FeatureCard
                icon={<Brain className="w-6 h-6" />}
                title="AI Task Breakdown"
                desc="Describe your project in one sentence. We'll generate a full engineering roadmap with subtasks, estimates, and complexity scores."
                color="violet"
              />
              <FeatureCard
                icon={<GitBranch className="w-6 h-6" />}
                title="GitHub Integration"
                desc="Automatic sync between tasks and GitHub Issues. Every commit updates your roadmap. Continuous visibility for stakeholders."
                color="indigo"
              />
              <FeatureCard
                icon={<Zap className="w-6 h-6" />}
                title="Risk Predictions"
                desc="Our ML models analyze your team velocity to flag 'at-risk' milestones before they impact your release cycle."
                color="blue"
              />
              <FeatureCard
                icon={<LayoutDashboard className="w-6 h-6" />}
                title="Organization-First"
                desc="Manage multiple teams, organizations, and private projects. Role-based access control built for security-conscious groups."
                color="emerald"
              />
              <FeatureCard
                icon={<Sparkles className="w-6 h-6" />}
                title="AI Task Chat"
                desc="Ask our built-in assistant for technical help directly in the task view. Get code snippets or architectural advice instantly."
                color="rose"
              />
              <FeatureCard
                icon={<ShieldCheck className="w-6 h-6" />}
                title="Modern Stack"
                desc="Built with performance in mind. Blazing fast UI, robust FastAPI backend, and secure AWS infrastructure."
                color="amber"
              />
            </div>
          </div>
        </section>

        {/* WORKING FEATURES SHOWCASE */}
        <section className="py-32 bg-gray-50 border-y border-gray-100">
          <div className="max-w-7xl mx-auto px-6">
            <div className="grid lg:grid-cols-2 gap-20 items-center">
              <div>
                <h2 className="text-4xl font-black text-gray-900 mb-8 leading-tight">
                  See JustBuildIt <br />
                  in action.
                </h2>
                <div className="space-y-8">
                  <WorkStep
                    number="01"
                    title="AI Project Inception"
                    desc="Enter your goal. Our Bedrock agent analyzes current modules and team skills to draft the perfect sprint plan."
                    active={true}
                  />
                  <WorkStep
                    number="02"
                    title="Editable Task Execution"
                    desc="Refine AI suggestions, assign team members, and track status via our slick Kanban-style board."
                    active={false}
                  />
                  <WorkStep
                    number="03"
                    title="Predictive Optimization"
                    desc="View the AI Insights dashboard to see regression predictions on time-to-completion and delay risks."
                    active={false}
                  />
                </div>
              </div>
              <div className="relative">
                <div className="absolute -inset-10 bg-violet-600/10 rounded-full blur-3xl" />
                <div className="relative rounded-[40px] border border-gray-100 overflow-hidden shadow-2xl bg-white p-2">
                  <div className="bg-gray-900 rounded-[32px] p-8 aspect-[4/3] flex flex-col justify-center items-center text-center">
                    <div className="w-20 h-20 bg-violet-600 rounded-2xl flex items-center justify-center mb-6 shadow-xl shadow-violet-500/40">
                      <Sparkles className="w-10 h-10 text-white" />
                    </div>
                    <h3 className="text-2xl font-bold text-white mb-4">
                      Generating Sprint Plan...
                    </h3>
                    <div className="w-full max-w-xs h-2 bg-gray-800 rounded-full overflow-hidden">
                      <div className="h-full bg-violet-500 w-2/3 animate-[loading_2s_ease-in-out_infinite]" />
                    </div>
                    <p className="mt-6 text-gray-500 text-sm italic">
                      "Analyzing frontend/api and matching with React/FastAPI
                      skills..."
                    </p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* CTA SECTION */}
        <section className="py-40 px-6 relative overflow-hidden">
          <div className="absolute inset-0 bg-violet-600" />
          <div className="absolute top-0 right-0 w-[800px] h-[800px] bg-white opacity-[0.03] rounded-full -translate-y-1/2 translate-x-1/3" />

          <div className="max-w-4xl mx-auto text-center relative z-10">
            <h2 className="text-5xl md:text-6xl font-black text-white mb-8 tracking-tight">
              Ready to automate your engineering?
            </h2>
            <p className="text-2xl text-violet-100 mb-12 font-medium">
              Join teams shipping software 40% faster with JustBuildIt.
            </p>
            <div className="flex flex-col sm:flex-row justify-center gap-4">
              <Link to="/register">
                <Button
                  size="lg"
                  className="h-16 px-12 bg-white text-violet-700 hover:bg-gray-50 text-xl font-black rounded-2xl shadow-2xl transition-transform hover:scale-105 active:scale-95"
                >
                  Get Started for Free
                </Button>
              </Link>
              <a
                href="https://github.com/SurajsinghBayas/justbuildit"
                target="_blank"
                rel="noreferrer"
                className="inline-flex items-center justify-center h-16 px-12 text-white border-2 border-white/30 hover:border-white text-lg font-bold rounded-2xl transition-all"
              >
                <GitBranch className="mr-2 w-5 h-5" /> Star on GitHub
              </a>
            </div>
          </div>
        </section>
      </main>

      <Footer />
    </div>
  );
}

/* ---------------- COMPONENTS ---------------- */

function FeatureCard({ icon, title, desc, color }: any) {
  const colors: any = {
    violet:
      "bg-violet-50 text-violet-700 border-violet-100",
    indigo:
      "bg-indigo-50 text-indigo-700 border-indigo-100",
    blue: "bg-blue-50 text-blue-700 border-blue-100",
    emerald:
      "bg-emerald-50 text-emerald-700 border-emerald-100",
    rose: "bg-rose-50 text-rose-700 border-rose-100",
    amber:
      "bg-amber-50 text-amber-700 border-amber-100",
  };

  return (
    <div className="p-10 bg-white border border-gray-100 rounded-[32px] hover:shadow-2xl hover:shadow-violet-500/10 transition-all duration-500 hover:-translate-y-2 group cursor-default">
      <div
        className={`w-14 h-14 rounded-2xl flex items-center justify-center mb-8 border transition-transform group-hover:scale-110 group-hover:rotate-3 ${colors[color]}`}
      >
        {icon}
      </div>
      <h3 className="text-xl font-bold text-gray-900 mb-4">
        {title}
      </h3>
      <p className="text-gray-500 leading-relaxed font-medium">
        {desc}
      </p>
      <div className="mt-8 flex items-center gap-1 text-sm font-bold text-gray-900 opacity-0 group-hover:opacity-100 transition-opacity">
        Learn more <ChevronRight className="w-4 h-4" />
      </div>
    </div>
  );
}

function WorkStep({ number, title, desc, active }: any) {
  return (
    <div
      className={`flex gap-6 p-6 rounded-3xl transition-all ${active ? "bg-white shadow-xl shadow-black/5 border border-gray-100" : "opacity-50 hover:opacity-100 cursor-pointer"}`}
    >
      <div
        className={`text-3xl font-black italic tracking-tighter ${active ? "text-violet-600" : "text-gray-300"}`}
      >
        {number}
      </div>
      <div>
        <h3 className="text-xl font-bold text-gray-900 mb-2">
          {title}
        </h3>
        <p className="text-gray-500 text-sm leading-relaxed">
          {desc}
        </p>
        {active && (
          <div className="mt-4 flex items-center gap-2 text-violet-600 text-xs font-bold uppercase tracking-widest">
            <CheckCircle2 className="w-4 h-4" /> Core Feature Operational
          </div>
        )}
      </div>
    </div>
  );
}
