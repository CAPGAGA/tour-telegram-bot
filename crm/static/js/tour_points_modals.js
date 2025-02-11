import { showMessage } from "./revolver.js";
import { fetchTourPoints } from "./fetch_tours.js"

export function openTourPointModal(tourId) {
    const modal = document.getElementById("tour-points-modal");
    fetchTourPoints(tourId);
    modal.style.display = "block";
    modal.style.opacity = 0;
    setTimeout(() => {
        modal.style.opacity = 1;
        modal.style.transition = "opacity 0.2s ease-in-out";
    }, 50);
}

export function closeTourPointModal() {
    const modal = document.getElementById("tour-points-modal")
    const settingForm = document.querySelector(".tour-settings");
    settingForm.reset();
    modal.style.opacity = 0;
    setTimeout(() => {
        modal.style.display = "none";
    }, 700);
}

document.addEventListener("DOMContentLoaded", function () {
    document.querySelector("#close-tour-points-modal").addEventListener("click", closeTourPointModal);
});