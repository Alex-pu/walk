import { Mail, Phone, UserRound, MessageCircle } from "lucide-react";

export default function SupportFooter() {
  return (
    <footer className="support-footer">
      <div>
        <strong>Support or reach the admin</strong>
        <span>Questions, partnerships, sponsorships, or community support.</span>
      </div>
      <nav aria-label="Admin contact links">
        <a href="mailto:kamaua175@gmail.com">
          <Mail size={18} aria-hidden="true" />
          Email
        </a>
        <a href="https://wa.me/254704813341" target="_blank" rel="noreferrer">
          <MessageCircle size={18} aria-hidden="true" />
          WhatsApp
        </a>
        <a href="tel:+254704813341">
          <Phone size={18} aria-hidden="true" />
          Call
        </a>
        <a href="https://kamaualex.netlify.app/" target="_blank" rel="noreferrer">
          <UserRound size={18} aria-hidden="true" />
          Profile
        </a>
      </nav>
    </footer>
  );
}
