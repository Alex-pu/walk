import { ArrowRight, MapPinned, ShieldCheck, UsersRound } from "lucide-react";
import { Link } from "react-router-dom";

import SupportFooter from "../components/SupportFooter.jsx";

export default function LandingPage() {
  return (
    <main className="landing-page">
      <section className="landing-hero">
        <div className="landing-nav">
          <Link className="landing-brand" to="/">
            <span className="brand-mark">RC</span>
            <span>Run Community Kenya</span>
          </Link>
          <div className="landing-nav-actions">
            <Link to="/about">About</Link>
            <Link to="/login">Login</Link>
            <Link className="landing-nav-button" to="/register">Join</Link>
          </div>
        </div>

        <div className="landing-panels" aria-hidden="true">
          <span />
          <span />
          <span />
        </div>

        <div className="landing-copy">
          <p className="landing-kicker">Kenya runs together</p>
          <h1>Find your crew. Show up. Move safely.</h1>
          <p>
            Discover nearby walking and running crews, join organized sessions, and build a trusted local fitness community.
          </p>
          <div className="landing-actions">
            <Link className="landing-primary" to="/login">
              Login <ArrowRight size={18} aria-hidden="true" />
            </Link>
            <Link className="landing-secondary" to="/register">Create account</Link>
            <Link className="landing-secondary" to="/about">Read about us</Link>
          </div>
        </div>

        <div className="landing-stats" aria-label="Run Community Kenya highlights">
          <div>
            <UsersRound size={20} aria-hidden="true" />
            <strong>Crews</strong>
            <span>Local groups</span>
          </div>
          <div>
            <MapPinned size={20} aria-hidden="true" />
            <strong>Routes</strong>
            <span>Nearby sessions</span>
          </div>
          <div>
            <ShieldCheck size={20} aria-hidden="true" />
            <strong>Safety</strong>
            <span>Trusted Organizers </span>
          </div>
        </div>
      </section>
      <SupportFooter />
    </main>
  );
}
