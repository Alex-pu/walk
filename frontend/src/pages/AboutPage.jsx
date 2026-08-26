import { ArrowRight, HeartHandshake, MapPinned, ShieldCheck, UsersRound } from "lucide-react";
import { Link } from "react-router-dom";

import SupportFooter from "../components/SupportFooter.jsx";

const communityGroups = [
  "Morning and evening runners",
  "Recreational walkers",
  "Beginners starting their fitness journey",
  "Regular runners looking for training partners",
  "Estate and neighbourhood running crews",
  "Friends organizing weekly runs",
  "People looking for a more social way to exercise",
];

export default function AboutPage() {
  return (
    <main className="about-page">
      <section className="about-hero">
        <Link className="landing-brand" to="/">
          <span className="brand-mark">RC</span>
          <span>Run Community Kenya</span>
        </Link>
        <div className="about-hero-copy">
          <p className="landing-kicker">About RunCommunity</p>
          <h1>Run together. Feel safer. Build community.</h1>
          <p>
            RunCommunity is a free community running platform built in Kenya to help people find others nearby to walk,
            jog, and run with.
          </p>
          <div className="landing-actions">
            <Link className="landing-primary" to="/register">
              Join the community <ArrowRight size={18} aria-hidden="true" />
            </Link>
            <Link className="landing-secondary" to="/login">Login</Link>
          </div>
        </div>
      </section>

      <article className="about-article">
        <section className="about-intro">
          <p>
            Our idea is simple: exercise is better when you have people around you. For many people, especially those
            who prefer running early in the morning or later in the evening, safety can be a concern. Others simply find
            it difficult to stay motivated when exercising alone.
          </p>
          <p>
            RunCommunity brings these needs together by helping people discover local running communities, join group
            runs, and build consistent exercise habits together. Whether you are an experienced runner, a beginner
            starting your first 3 km, or simply looking for people to walk with around your neighbourhood, you are
            welcome.
          </p>
        </section>

        <section className="about-feature-grid">
          <div>
            <ShieldCheck size={24} aria-hidden="true" />
            <strong>Safety first</strong>
            <span>Group exercise with trusted local crews.</span>
          </div>
          <div>
            <UsersRound size={24} aria-hidden="true" />
            <strong>Community</strong>
            <span>Participation matters more than pace.</span>
          </div>
          <div>
            <MapPinned size={24} aria-hidden="true" />
            <strong>Local crews</strong>
            <span>Find walks and runs near your estate.</span>
          </div>
        </section>

        <section>
          <h2>Community and safety come first</h2>
          <p>
            RunCommunity is not primarily about being the fastest runner. It is about community, consistency, and safer
            group exercise.
          </p>
          <p>
            We want to make it easier for people living in the same neighbourhoods and estates to organize runs and
            walks together. Instead of heading out alone, members can discover nearby crews, see upcoming activities,
            and join other people exercising in their area.
          </p>
          <p>
            Running together does not eliminate every safety risk, but being part of an organized community can provide
            companionship, visibility, and greater confidence compared with exercising alone. Our long-term goal is to
            build trusted local running communities across Kenya.
          </p>
        </section>

        <section>
          <h2>Free and open to everyone</h2>
          <p>
            RunCommunity is a free application. You do not need to be an athlete or belong to a professional running
            club. The platform is intended for ordinary people who want to become more active and connect with others.
          </p>
          <div className="about-list">
            {communityGroups.map((group) => (
              <span key={group}>{group}</span>
            ))}
          </div>
          <p>The focus is participation rather than competition.</p>
        </section>

        <section>
          <h2>Our vision for manned community runs</h2>
          <p>
            As RunCommunity grows, we want to go beyond simply connecting people online. Through future community
            support, donations, partnerships, and sponsorships, our goal is to organize manned community runs in estates
            and neighbourhoods across Kenya.
          </p>
          <p>
            These organized runs would be particularly valuable during hours when people may feel less comfortable
            exercising alone, such as early mornings and evenings.
          </p>
          <blockquote>
            Imagine knowing that every Tuesday and Thursday at 5:30 AM there is an organized RunCommunity crew leaving
            from a known public meeting point in your estate. You show up. Other runners show up. And you run together.
          </blockquote>
          <p>That is the community we want to build.</p>
        </section>

        <section>
          <h2>From local crews to a national running community</h2>
          <p>
            We are starting locally, but our ambition is national. We envision interconnected RunCommunity crews across
            Kenya, with runners and walkers able to find communities wherever they live or travel.
          </p>
          <p>
            A member could belong to their local estate crew while also being part of the wider RunCommunity Kenya
            network. Over time, we hope to support community runs, local challenges, wellness initiatives, charity runs,
            partnerships, and larger events that bring different crews together.
          </p>
          <p>
            Our long-term vision is to create a national community of runners and walkers connected by a shared
            commitment to fitness, community, and looking out for one another.
          </p>
        </section>

        <section>
          <h2>Built in Kenya</h2>
          <p>
            RunCommunity was founded and developed by Alex, a Kenyan software developer and sports enthusiast, from a
            simple observation: there are many people who would like to exercise regularly but do not always have someone
            to walk or run with.
          </p>
          <p>
            Technology can help those people find each other. Instead of building another application focused only on
            statistics, pace, or competition, RunCommunity is being developed around the human side of exercise.
          </p>
          <div className="about-question">
            <HeartHandshake size={28} aria-hidden="true" />
            <strong>Who are you running with?</strong>
          </div>
          <p>That question is at the heart of RunCommunity.</p>
        </section>

        <section className="about-closing">
          <h2>Join the community</h2>
          <p>
            You do not have to be fast. You do not have to run long distances. And you do not have to start alone.
          </p>
          <p>
            Find a crew near you, join an upcoming run or walk, meet people in your community, and start moving
            together.
          </p>
          <strong>Run together. Stay active. Look out for each other.</strong>
          <Link className="landing-primary" to="/register">
            Welcome to RunCommunity Kenya <ArrowRight size={18} aria-hidden="true" />
          </Link>
        </section>
      </article>
      <SupportFooter />
    </main>
  );
}
