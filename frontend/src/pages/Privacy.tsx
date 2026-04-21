import LandingHeader from '@/components/LandingHeader';
import Footer from '@/components/Footer';

export default function PrivacyPage() {
  return (
    <div className="min-h-screen bg-white font-sans transition-colors">
      <LandingHeader />
      <main className="max-w-4xl mx-auto px-4 py-20">
        <h1 className="text-4xl font-extrabold text-gray-900 mb-8">Privacy Policy</h1>
        <div className="prose prose-gray max-w-none space-y-6 text-gray-600">
          <p className="text-lg">
            Last updated: April 21, 2026
          </p>
          <section>
            <h2 className="text-2xl font-bold text-gray-900 mt-12 mb-4">1. Introduction</h2>
            <p>
              Welcome to JustBuildIt. We value your privacy and the security of your data. This Privacy Policy explains how we collect, use, and protect your information when you use our platform.
            </p>
          </section>
          <section>
            <h2 className="text-2xl font-bold text-gray-900 mt-12 mb-4">2. Data We Collect</h2>
            <p>
              We collect information you provide directly, such as your name, email, and project data. We also collect automated technical data regarding your usage of our services to improve performance and security.
            </p>
          </section>
          <section>
            <h2 className="text-2xl font-bold text-gray-900 mt-12 mb-4">3. How We Use Data</h2>
            <p>
              Your data is used to provide AI-powered task recommendations, project insights, and seamless collaboration features. We do not sell your personal data to third parties.
            </p>
          </section>
          <section>
            <h2 className="text-2xl font-bold text-gray-900 mt-12 mb-4">4. AI and Machine Learning</h2>
            <p>
              JustBuildIt uses AI models (like AWS Bedrock) to process your task descriptions. This data is processed according to our security standards and is used solely to enhance your project management experience.
            </p>
          </section>
          <div className="p-8 bg-gray-50 rounded-2xl border border-gray-100 mt-16">
            <h3 className="text-lg font-bold text-gray-900 mb-2">Questions?</h3>
            <p className="text-sm">Reach out to us at privacy@justbuildit.ai for any concerns regarding your data.</p>
          </div>
        </div>
      </main>
      <Footer />
    </div>
  );
}
