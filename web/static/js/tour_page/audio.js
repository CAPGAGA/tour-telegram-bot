// Plays audio on click
document.addEventListener("DOMContentLoaded", function () {
    let currentAudio = null; // Stores currently playing audio
    let currentButton = null; // Stores the button controlling the audio

    document.querySelectorAll(".play-audio").forEach(button => {
        button.addEventListener("click", function () {
            const audioSrc = this.getAttribute("data-audio");

            // If the same button is clicked, stop audio
            if (currentAudio && !currentAudio.paused && currentButton === this) {
                currentAudio.pause();
                currentAudio.currentTime = 0;
                this.textContent = "▶ Play Audio";
                currentAudio = null;
                currentButton = null;
                return;
            }

            // Stop any previously playing audio
            if (currentAudio) {
                currentAudio.pause();
                currentAudio.currentTime = 0;
                if (currentButton) {
                    currentButton.textContent = "▶ Play Audio";
                }
            }

            // Play new audio
            currentAudio = new Audio(audioSrc);
            currentButton = this;
            this.textContent = "⏹ Stop Audio";

            currentAudio.play();

            // Reset button text when audio ends
            currentAudio.addEventListener("ended", () => {
                this.textContent = "▶ Play Audio";
                currentAudio = null;
                currentButton = null;
            });
        });
    });
});