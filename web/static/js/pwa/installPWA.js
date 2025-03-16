let deferredPrompt; // Store the event

document.addEventListener("DOMContentLoaded", () => {
    const installButton = document.getElementById("install-pwa");

    window.addEventListener("beforeinstallprompt", (event) => {
        event.preventDefault();
        deferredPrompt = event;
        installButton.classList.remove("is-hidden"); // Show button
    });

    installButton.addEventListener("click", async () => {
        if (deferredPrompt) {
            deferredPrompt.prompt(); // Show prompt

            const { outcome } = await deferredPrompt.userChoice;
            if (outcome === "accepted") {
                console.log("User accepted the PWA installation");
            } else {
                console.log("User dismissed the PWA installation");
            }
            deferredPrompt = null; // Reset
            installButton.classList.add("is-hidden");
        }
    });

    // Hide button if app is already installed
    window.addEventListener("appinstalled", () => {
        console.log("PWA installed");
        installButton.classList.add("is-hidden");
    });

    // Force show install button on desktop Chrome
    if (window.matchMedia("(display-mode: browser)").matches) {
        console.log("Running in a browser, showing install button");
        installButton.classList.remove("is-hidden");
    }
});