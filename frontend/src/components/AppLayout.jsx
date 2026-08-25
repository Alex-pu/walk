import { useEffect, useState } from "react";
import { ClipboardList, Home, Map, MessageSquare, PlayCircle, Shield, Users, UserRound } from "lucide-react";
import { NavLink, Outlet } from "react-router-dom";

import { api } from "../api/client.js";
import { useAuth } from "../context/AuthContext.jsx";

const baseNavItems = [
  { to: "/home", label: "Home", icon: Home },
  { to: "/discover", label: "Discover", icon: Map },
  { to: "/activity", label: "Activity", icon: PlayCircle },
  { to: "/forum", label: "Forum", icon: MessageSquare },
  { to: "/crews", label: "Crews", icon: Users },
  { to: "/profile", label: "Profile", icon: UserRound },
];

export default function AppLayout() {
  const { user } = useAuth();
  const [hasOrganizerCrews, setHasOrganizerCrews] = useState(false);

  useEffect(() => {
    if (!user) {
      setHasOrganizerCrews(false);
      return;
    }

    api
      .crews()
      .then((data) => {
        setHasOrganizerCrews(data.crews.some((crew) => crew.current_user_role === "organizer"));
      })
      .catch(() => setHasOrganizerCrews(false));
  }, [user]);

  const navItems = [...baseNavItems];
  if (hasOrganizerCrews) {
    navItems.push({ to: "/organizer", label: "Organizer", icon: ClipboardList });
  }
  if (user?.platform_role === "admin") {
    navItems.push({ to: "/admin", label: "Manage Users", icon: Shield });
  }

  return (
    <div className="app-shell">
      <main className="app-main">
        <Outlet />
      </main>
      <nav className="bottom-nav">
        {navItems.map((item) => {
          const Icon = item.icon;
          return (
            <NavLink key={item.to} to={item.to} end={item.to === "/home"} className="nav-item">
              <Icon size={20} aria-hidden="true" />
              <span>{item.label}</span>
            </NavLink>
          );
        })}
      </nav>
    </div>
  );
}
