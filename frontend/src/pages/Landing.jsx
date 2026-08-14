import { motion } from "framer-motion";
import {
  Sparkles,
  ScanLine,
  MessageCircleHeart,
  Search,
  UserRoundCheck,
  Camera,
  ListChecks,
  ArrowRight,
} from "lucide-react";
import { Link } from "react-router-dom";
import { useAuth } from "../hooks/useAuth.js";
import GoogleSignInButton from "../components/GoogleSignInButton.jsx";
import HeroShelf from "../components/HeroShelf.jsx";
import FeatureCard from "../components/FeatureCard.jsx";

const steps = [
  {
    number: "01",
    title: "Tell us what you love",
    description:
      "Sign in, pick a few favorite genres and authors, and Lexora starts building a picture of your taste.",
  },
  {
    number: "02",
    title: "We read between the lines",
    description:
      "Every book gets a semantic embedding — Lexora understands what a book is actually about, not just its category tags.",
  },
  {
    number: "03",
    title: "Ask, scan, or browse",
    description:
      "Search in plain language, snap a photo of your shelf, or just tell the assistant what mood you're in.",
  },
  {
    number: "04",
    title: "Get matches, not guesses",
    description:
      "Recommendations combine semantic similarity with your history and preferences — and Lexora tells you why.",
  },
];

const features = [
  {
    icon: Sparkles,
    callNumber: "AI · 001",
    title: "AI recommendations",
    description:
      "Ranked suggestions that weigh semantic similarity, genre and author preference, and your reading history together — not a single popularity score.",
  },
  {
    icon: Search,
    callNumber: "AI · 002",
    title: "Semantic search",
    description:
      "Search \"beginner-friendly machine learning books\" or \"fantasy with strong female leads\" and get results that actually match the meaning.",
  },
  {
    icon: ScanLine,
    callNumber: "OCR · 003",
    title: "Bookshelf scanner",
    description:
      "Photograph your shelf. Lexora reads the spines, matches them against Google Books, and recommends what to read next based on what you already own.",
  },
  {
    icon: MessageCircleHeart,
    callNumber: "AI · 004",
    title: "AI reading assistant",
    description:
      "Chat naturally — \"what should I read after Harry Potter?\" — and get grounded answers with real book cards, not invented titles.",
  },
  {
    icon: UserRoundCheck,
    callNumber: "AI · 005",
    title: "Personalized reading",
    description:
      "Your wishlist, reading history, and completed books all feed back into future recommendations, so the fit improves over time.",
  },
  {
    icon: ListChecks,
    callNumber: "LOG · 006",
    title: "Reading tracker & analytics",
    description:
      "Track want-to-read, reading, and completed books, and see your genres, streaks, and pace laid out on a real dashboard.",
  },
];

const moods = [
  { emoji: "😊", label: "Happy" },
  { emoji: "❤️", label: "Romantic" },
  { emoji: "🔥", label: "Motivational" },
  { emoji: "🧠", label: "Learning" },
  { emoji: "😱", label: "Thrilling" },
  { emoji: "🌙", label: "Emotional" },
  { emoji: "🧙", label: "Fantasy" },
  { emoji: "💼", label: "Professional" },
];

const testimonials = [
  {
    quote:
      "I scanned my actual shelf out of curiosity and it recommended three books I already meant to buy. That's when I trusted the semantic search.",
    name: "Priya N.",
    detail: "Reads ~40 books a year",
  },
  {
    quote:
      "The chat assistant is the first \"AI book bot\" that hasn't recommended something that doesn't exist. Everything links to a real book card.",
    name: "Marcus T.",
    detail: "Nonfiction & business reader",
  },
  {
    quote:
      "Mood-based recommendations sound gimmicky until you're between books and just want something thrilling. It gets that right.",
    name: "Sofia R.",
    detail: "Fantasy & thriller reader",
  },
];

export default function Landing() {
  const { isAuthenticated } = useAuth();

  return (
    <div>
      {/* Hero */}
      <section className="relative overflow-hidden bg-ink-radial">
        <div className="mx-auto grid max-w-7xl grid-cols-1 items-center gap-12 px-6 py-20 sm:py-28 lg:grid-cols-2 lg:py-32">
          <motion.div
            initial={{ y: 20, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            transition={{ duration: 0.7 }}
          >
            <span className="eyebrow">Your AI-powered literary companion</span>
            <h1 className="mt-4 font-display text-4xl font-medium leading-[1.1] text-parchment sm:text-5xl lg:text-6xl">
              Discover books that actually match you.
            </h1>
            <p className="mt-6 max-w-lg text-lg leading-relaxed text-parchment/70">
              Lexora reads between the lines of what you love — semantic search,
              a bookshelf scanner, and an AI reading assistant that never makes up a title.
            </p>

            <div className="mt-8 flex flex-wrap items-center gap-4">
              {isAuthenticated ? (
                <Link to="/dashboard" className="brass-btn">
                  Go to your dashboard
                  <ArrowRight className="h-4 w-4" />
                </Link>
              ) : (
                <>
                  <a href="#how-it-works" className="ghost-btn">
                    Start Exploring
                  </a>
                  <GoogleSignInButton />
                </>
              )}
            </div>
            <p className="mt-4 font-mono text-xs text-parchment/40">
              No spam. No password to remember — just your Google account.
            </p>
          </motion.div>

          <div className="hidden justify-self-center lg:block">
            <HeroShelf />
          </div>
        </div>
      </section>

      {/* How it works — a real sequence, so numbering is earned here */}
      <section id="how-it-works" className="border-t border-ink-line/60 bg-ink py-24">
        <div className="mx-auto max-w-7xl px-6">
          <span className="eyebrow">How it works</span>
          <h2 className="section-heading mt-3 max-w-xl">
            From "what should I read next" to a shelf that fits.
          </h2>

          <div className="mt-14 grid grid-cols-1 gap-8 sm:grid-cols-2 lg:grid-cols-4">
            {steps.map((step, i) => (
              <motion.div
                key={step.number}
                initial={{ y: 20, opacity: 0 }}
                whileInView={{ y: 0, opacity: 1 }}
                viewport={{ once: true, margin: "-60px" }}
                transition={{ duration: 0.5, delay: i * 0.1 }}
              >
                <span className="font-mono text-3xl font-medium text-brass/50">
                  {step.number}
                </span>
                <h3 className="mt-3 font-display text-lg font-medium text-parchment">
                  {step.title}
                </h3>
                <p className="mt-2 text-sm leading-relaxed text-parchment/60">
                  {step.description}
                </p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* Feature grid */}
      <section id="features" className="border-t border-ink-line/60 bg-ink-panel py-24">
        <div className="mx-auto max-w-7xl px-6">
          <span className="eyebrow">What's in the catalog</span>
          <h2 className="section-heading mt-3 max-w-xl">
            Six ways Lexora gets to know your shelf.
          </h2>

          <div className="mt-14 grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3">
            {features.map((feature, i) => (
              <FeatureCard key={feature.title} index={i} {...feature} />
            ))}
          </div>
        </div>
      </section>

      {/* Bookshelf scanner teaser */}
      <section id="scanner" className="border-t border-ink-line/60 bg-ink py-24">
        <div className="mx-auto grid max-w-7xl grid-cols-1 items-center gap-12 px-6 lg:grid-cols-2">
          <motion.div
            initial={{ x: -20, opacity: 0 }}
            whileInView={{ x: 0, opacity: 1 }}
            viewport={{ once: true }}
            transition={{ duration: 0.6 }}
          >
            <span className="eyebrow">Bookshelf scanner</span>
            <h2 className="section-heading mt-3">Point your camera at your shelf.</h2>
            <p className="mt-4 max-w-md leading-relaxed text-parchment/70">
              Lexora preprocesses the image, reads the spines with OCR, and matches
              whatever it can against Google Books. Anything it isn't confident about,
              you get to correct — Lexora never guesses silently.
            </p>
            <ul className="mt-6 space-y-3 text-sm text-parchment/60">
              {["Upload a photo", "Detect and match titles", "Correct anything unclear", "Get recommendations from what you own"].map(
                (item, i) => (
                  <li key={item} className="flex items-center gap-3">
                    <span className="font-mono text-xs text-brass">{String(i + 1).padStart(2, "0")}</span>
                    {item}
                  </li>
                )
              )}
            </ul>
          </motion.div>

          <motion.div
            initial={{ x: 20, opacity: 0 }}
            whileInView={{ x: 0, opacity: 1 }}
            viewport={{ once: true }}
            transition={{ duration: 0.6 }}
            className="catalog-card flex aspect-[4/3] flex-col items-center justify-center gap-4 p-8 text-center"
          >
            <Camera className="h-10 w-10 text-moss-dark/60" strokeWidth={1.5} />
            <p className="call-number">Ready to try</p>
            <p className="max-w-xs text-sm text-parchment-ink/60">
              Sign in and upload a photo of your own shelf — Lexora will read the spines
              and match them against the catalog in seconds.
            </p>
            {isAuthenticated ? (
              <Link to="/scanner" className="brass-btn">
                Open the scanner
                <ArrowRight className="h-4 w-4" />
              </Link>
            ) : (
              <GoogleSignInButton redirectTo="/scanner" />
            )}
          </motion.div>
        </div>
      </section>

      {/* Mood-based teaser */}
      <section className="border-t border-ink-line/60 bg-ink-panel py-24">
        <div className="mx-auto max-w-7xl px-6 text-center">
          <span className="eyebrow">What are you in the mood for?</span>
          <h2 className="section-heading mx-auto mt-3 max-w-xl">
            Sometimes the right book is about how you feel, not what you like.
          </h2>

          <div className="mt-12 flex flex-wrap justify-center gap-3">
            {moods.map((mood, i) => (
              <motion.span
                key={mood.label}
                initial={{ scale: 0.9, opacity: 0 }}
                whileInView={{ scale: 1, opacity: 1 }}
                viewport={{ once: true }}
                transition={{ duration: 0.3, delay: i * 0.05 }}
                className="flex items-center gap-2 rounded-full border border-parchment/15 bg-ink px-4 py-2 text-sm text-parchment/80"
              >
                <span className="text-base">{mood.emoji}</span>
                {mood.label}
              </motion.span>
            ))}
          </div>
        </div>
      </section>

      {/* Testimonials */}
      <section className="border-t border-ink-line/60 bg-ink py-24">
        <div className="mx-auto max-w-7xl px-6">
          <span className="eyebrow">From the reading log</span>
          <h2 className="section-heading mt-3 max-w-xl">Readers on the shelf already.</h2>

          <div className="mt-14 grid grid-cols-1 gap-6 md:grid-cols-3">
            {testimonials.map((t, i) => (
              <motion.figure
                key={t.name}
                initial={{ y: 20, opacity: 0 }}
                whileInView={{ y: 0, opacity: 1 }}
                viewport={{ once: true, margin: "-60px" }}
                transition={{ duration: 0.5, delay: i * 0.1 }}
                className="catalog-card flex flex-col justify-between p-6"
              >
                <blockquote className="text-sm leading-relaxed text-parchment-ink/80">
                  "{t.quote}"
                </blockquote>
                <div className="catalog-card__rule" />
                <figcaption className="mt-3">
                  <p className="text-sm font-medium text-parchment-ink">{t.name}</p>
                  <p className="call-number mt-0.5">{t.detail}</p>
                </figcaption>
              </motion.figure>
            ))}
          </div>
        </div>
      </section>

      {/* Final CTA */}
      <section className="border-t border-ink-line/60 bg-ink-radial py-24">
        <div className="mx-auto max-w-3xl px-6 text-center">
          <h2 className="section-heading">Your next book is already in the catalog.</h2>
          <p className="mx-auto mt-4 max-w-md text-parchment/70">
            Sign in with Google and Lexora starts building your shelf in under a minute.
          </p>
          <div className="mt-8 flex justify-center">
            {isAuthenticated ? (
              <Link to="/dashboard" className="brass-btn">
                Go to your dashboard
                <ArrowRight className="h-4 w-4" />
              </Link>
            ) : (
              <GoogleSignInButton />
            )}
          </div>
        </div>
      </section>
    </div>
  );
}
