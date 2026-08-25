import { useEffect, useState } from "react";

export function useInstallPrompt() {
  const [promptEvent, setPromptEvent] = useState(null);
  const [isInstalled, setIsInstalled] = useState(false);

  useEffect(() => {
    const standalone = window.matchMedia("(display-mode: standalone)").matches || window.navigator.standalone;
    setIsInstalled(Boolean(standalone));

    function handleBeforeInstallPrompt(event) {
      event.preventDefault();
      setPromptEvent(event);
    }

    function handleInstalled() {
      setPromptEvent(null);
      setIsInstalled(true);
    }

    window.addEventListener("beforeinstallprompt", handleBeforeInstallPrompt);
    window.addEventListener("appinstalled", handleInstalled);
    return () => {
      window.removeEventListener("beforeinstallprompt", handleBeforeInstallPrompt);
      window.removeEventListener("appinstalled", handleInstalled);
    };
  }, []);

  async function install() {
    if (!promptEvent) return;
    promptEvent.prompt();
    await promptEvent.userChoice;
    setPromptEvent(null);
  }

  return {
    canInstall: Boolean(promptEvent) && !isInstalled,
    isInstalled,
    install,
  };
}
