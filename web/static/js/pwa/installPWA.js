let deferredPrompt;

document.addEventListener("DOMContentLoaded", function () {
    const installButton = document.getElementById("install-pwa");

    // Listen for the PWA install prompt event
    window.addEventListener("beforeinstallprompt", (event) => {
        event.preventDefault();
        deferredPrompt = event;

        // Show install button
        installButton.classList.remove("is-hidden");

        installButton.addEventListener("click", () => {
            if (deferredPrompt) {
                deferredPrompt.prompt(); // Show install prompt

                deferredPrompt.userChoice.then((choiceResult) => {
                    if (choiceResult.outcome === "accepted") {
                        console.log("User accepted the install prompt");
                    } else {
                        console.log("User dismissed the install prompt");
                    }
                    deferredPrompt = null; // Reset prompt
                    installButton.classList.add("is-hidden"); // Hide button
                });
            }
        });
    });

    // Hide button if app is already installed
    window.addEventListener("appinstalled", () => {
        console.log("PWA installed");
        installButton.classList.add("is-hidden");
    });
});