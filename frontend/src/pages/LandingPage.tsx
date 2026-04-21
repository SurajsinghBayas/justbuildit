import { Link } from "react-router-dom";
import { Button } from "@/components/ui/button";
import {
  Zap,
  GitBranch,
  Brain,
  ArrowRight,
  Terminal,
  Activity,
  Code2
} from "lucide-react";
import LandingHeader from "@/components/LandingHeader";
import Footer from "@/components/Footer";

export default function LandingPage() {
  const isAuthenticated = !!localStorage.getItem('access_token');

  return (
    <div className="flex flex-col min-h-screen bg-[#fafafa] selection:bg-black selection:text-white">
      <LandingHeader />

      <main className="flex-1">
        {/* HERO SECTION - CLEAN AND PROACTIVE */}
        <section className="relative pt-24 pb-20 md:pt-32 md:pb-32 overflow-hidden px-6">
          <div className="absolute inset-0 bg-[linear-gradient(to_right,#80808012_1px,transparent_1px),linear-gradient(to_bottom,#80808012_1px,transparent_1px)] bg-[size:24px_24px]"></div>
          
          <div className="max-w-5xl mx-auto flex flex-col items-center text-center relative z-10">
            <div className="inline-flex items-center gap-2 px-3 py-1.5 bg-white border border-gray-200 rounded-full mb-8 shadow-sm">
              <span className="flex h-2 w-2 rounded-full bg-black animate-pulse" />
              <span className="text-xs font-semibold text-gray-800 tracking-wide">
                JustBuildIt v2.0 is live
              </span>
            </div>

            <h1 className="text-5xl md:text-7xl font-bold text-gray-900 leading-[1.1] mb-6 tracking-tight">
              Stop managing tasks. <br />
              <span className="text-gray-400">Start building proactively.</span>
            </h1>

            <p className="text-lg md:text-xl text-gray-500 max-w-2xl mx-auto mb-10 font-medium leading-relaxed">
              The AI-first engineering OS that breaks down projects, syncs seamlessly with your codebase, and predicts bottlenecks before they delay your launch.
            </p>

            <div className="flex flex-col sm:flex-row gap-4 mb-20 w-full justify-center">
              <Link to={isAuthenticated ? "/dashboard" : "/register"}>
                <Button
                  size="lg"
                  className="h-14 px-8 bg-black hover:bg-gray-800 text-white text-base overflow-hidden rounded-xl shadow-lg transition-all group w-full sm:w-auto"
                >
                  <span className="mr-2">{isAuthenticated ? "Go to Dashboard" : "Start Building Free"}</span>
                  <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
                </Button>
              </Link>
              <a
                href="https://github.com/SurajsinghBayas/justbuildit"
                target="_blank"
                rel="noreferrer"
              >
                <Button
                  size="lg"
                  variant="outline"
                  className="h-14 px-8 text-base bg-white border-gray-200 hover:border-gray-300 hover:bg-gray-50 rounded-xl transition-all w-full sm:w-auto text-gray-700"
                >
                  <GitBranch className="mr-2 w-5 h-5 text-gray-500" /> View on GitHub
                </Button>
              </a>
            </div>
            
            {/* Minimal Dashboard/Stats Preview */}
            <div className="w-full max-w-4xl bg-white border border-gray-200 rounded-[24px] shadow-2xl shadow-black/5 overflow-hidden p-2 mx-auto animate-fade-in-up">
               <div className="bg-gray-50/80 rounded-[16px] border border-gray-100 p-8 flex flex-col md:flex-row gap-10 items-center justify-between text-left">
                  <div className="flex-1 w-full space-y-5">
                     <div className="flex items-center gap-3 mb-2">
                        <Terminal className="w-5 h-5 text-gray-400" />
                        <span className="text-sm font-semibold text-gray-600 uppercase tracking-widest">AI Breakdown</span>
                     </div>
                     <div className="space-y-3">
                        <div className="flex items-center gap-3">
                           <div className="w-4 h-4 rounded bg-gray-200 flex-shrink-0"></div>
                           <div className="h-2.5 w-full bg-gray-200 rounded-full"></div>
                        </div>
                        <div className="flex items-center gap-3">
                           <div className="w-4 h-4 rounded bg-black flex-shrink-0"></div>
                           <div className="h-2.5 w-3/4 bg-gray-800 rounded-full"></div>
                        </div>
                        <div className="flex items-center gap-3">
                           <div className="w-4 h-4 rounded bg-gray-200 flex-shrink-0"></div>
                           <div className="h-2.5 w-5/6 bg-gray-200 rounded-full"></div>
                        </div>
                     </div>
                  </div>
                  <div className="hidden md:block w-px h-28 bg-gray-200/60"></div>
                  <div className="flex-1 w-full space-y-5">
                     <div className="flex items-center gap-3 mb-2">
                        <Activity className="w-5 h-5 text-gray-400" />
                        <span className="text-sm font-semibold text-gray-600 uppercase tracking-widest">Velocity</span>
                     </div>
                     <div className="flex items-end justify-between gap-2 h-16 pt-2">
                        <div className="w-full bg-gray-200 rounded-t-sm h-1/3 hover:h-1/2 transition-all"></div>
                        <div className="w-full bg-gray-300 rounded-t-sm h-2/3 hover:h-[75%] transition-all"></div>
                        <div className="w-full bg-black rounded-t-sm h-full shadow-[0_0_15px_rgba(0,0,0,0.2)] relative">
                           <div className="absolute -top-3 left-1/2 -translate-x-1/2 w-1.5 h-1.5 rounded-full bg-green-400"></div>
                        </div>
                        <div className="w-full bg-gray-300 rounded-t-sm h-4/5 hover:h-[90%] transition-all"></div>
                        <div className="w-full bg-gray-200 rounded-t-sm h-1/2 hover:h-[60%] transition-all"></div>
                     </div>
                  </div>
               </div>
            </div>

          </div>
        </section>

        {/* PROACTIVE WORKFLOW SECTION (Bento Box style) */}
        <section className="py-24 bg-white border-t border-gray-100">
           <div className="max-w-6xl mx-auto px-6">
              <div className="mb-16 text-center md:text-left flex flex-col md:flex-row justify-between items-end gap-6">
                 <div>
                    <h2 className="text-3xl md:text-5xl font-bold text-gray-900 mb-5 tracking-tight">Stay in the flow. <br/>We handle the rest.</h2>
                    <p className="text-lg text-gray-500 max-w-md">Our proactive AI agents constantly analyze your project context to unblock developers and maintain alignment.</p>
                 </div>
              </div>

              <div className="grid md:grid-cols-3 gap-6">
                 {/* Large Card */}
                 <div className="md:col-span-2 bg-gray-50 rounded-[32px] p-8 md:p-12 border border-gray-100 hover:border-gray-300 hover:shadow-lg transition-all group overflow-hidden relative">
                    <div className="relative z-10">
                       <div className="w-12 h-12 bg-white rounded-2xl flex items-center justify-center mb-6 shadow-sm">
                          <Brain className="w-6 h-6 text-gray-900" />
                       </div>
                       <h3 className="text-2xl font-bold text-gray-900 mb-4">AI Project Inception</h3>
                       <p className="text-gray-600 mb-8 max-w-md text-lg leading-relaxed">Describe your desired feature in plain English. Our LLMs generate a comprehensive technical roadmap with precise task breakdowns and estimations instantly.</p>
                       <Link to="/register" className="inline-flex items-center text-sm font-bold text-black group-hover:text-gray-600 transition-colors">
                          Experience AI Planning <ArrowRight className="w-4 h-4 ml-2 group-hover:translate-x-1 transition-transform" />
                       </Link>
                    </div>
                 </div>

                 {/* Square Cards */}
                 <div className="bg-gray-50 rounded-[32px] p-8 md:p-10 border border-gray-100 hover:border-gray-300 hover:shadow-lg transition-all flex flex-col justify-between">
                    <div>
                       <div className="w-12 h-12 bg-white rounded-2xl flex items-center justify-center mb-6 shadow-sm">
                          <GitBranch className="w-6 h-6 text-gray-900" />
                       </div>
                       <h3 className="text-xl font-bold text-gray-900 mb-3">GitHub Sync</h3>
                       <p className="text-gray-600 leading-relaxed">Continuous two-way sync with your repositories. Commits push tasks forward autonomously.</p>
                    </div>
                 </div>

                 <div className="bg-gray-50 rounded-[32px] p-8 md:p-10 border border-gray-100 hover:border-gray-300 hover:shadow-lg transition-all flex flex-col justify-between">
                    <div>
                       <div className="w-12 h-12 bg-white rounded-2xl flex items-center justify-center mb-6 shadow-sm">
                          <Activity className="w-6 h-6 text-gray-900" />
                       </div>
                       <h3 className="text-xl font-bold text-gray-900 mb-3">Risk Protection</h3>
                       <p className="text-gray-600 leading-relaxed">Predictive analytics flag stalled tasks and at-risk milestones before they impact the sprint.</p>
                    </div>
                 </div>

                 <div className="md:col-span-2 bg-gray-900 rounded-[32px] p-8 md:p-12 text-white overflow-hidden relative hover:shadow-2xl hover:shadow-black/20 transition-all">
                    <div className="relative z-10">
                       <div className="w-12 h-12 bg-gray-800 rounded-2xl flex items-center justify-center mb-6 border border-gray-700">
                          <Code2 className="w-6 h-6 text-gray-200" />
                       </div>
                       <h3 className="text-2xl font-bold mb-4">Enterprise Architecture</h3>
                       <p className="text-gray-400 mb-0 max-w-md text-lg leading-relaxed">Role-based access controls, robust private workspaces, and a lightning-fast FastAPI backend designed for engineering teams at scale.</p>
                    </div>
                    {/* Abstract background shape for the dark card */}
                    <div className="absolute top-0 right-0 w-[400px] h-[400px] bg-white/[0.03] rounded-full blur-3xl -translate-y-1/2 translate-x-1/3"></div>
                 </div>
              </div>
           </div>
        </section>

        {/* BOTTOM CTA */}
        <section className="py-28 px-6 bg-white">
          <div className="max-w-4xl mx-auto text-center border border-gray-100 bg-[#fafafa] rounded-[40px] p-12 md:p-20 shadow-sm relative overflow-hidden">
             
            <div className="absolute top-0 right-0 p-8 opacity-10 blur-sm pointer-events-none">
               <Zap className="w-32 h-32" />
            </div>

            <div className="relative z-10">
               <h2 className="text-4xl md:text-5xl font-bold text-gray-900 mb-6 tracking-tight">
                 Ready to ship faster?
               </h2>
               <p className="text-lg md:text-xl text-gray-500 mb-10 max-w-xl mx-auto leading-relaxed">
                 Join modern engineering teams who focus on writing code instead of managing ticket boards.
               </p>
               <div className="flex justify-center flex-col sm:flex-row gap-4">
                 <Link to="/register">
                   <Button
                     size="lg"
                     className="h-14 px-10 bg-black hover:bg-gray-800 text-white text-base font-semibold rounded-xl shadow-lg transition-transform hover:scale-[1.02] active:scale-[0.98] w-full sm:w-auto"
                   >
                     Create free account
                   </Button>
                 </Link>
                 <Link to="/login">
                   <Button
                     size="lg"
                     variant="outline"
                     className="h-14 px-10 text-base font-semibold rounded-xl border-gray-200 hover:bg-gray-50 w-full sm:w-auto text-gray-700"
                   >
                     Sign In
                   </Button>
                 </Link>
               </div>
            </div>
          </div>
        </section>
      </main>

      <Footer />
    </div>
  );
}
