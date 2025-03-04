import { fetchTours } from "./fetch_tours.js";

document.addEventListener("DOMContentLoaded", function () {
    document.querySelectorAll(".nav-button").forEach(button => {
        button.addEventListener("click", function () {
            let windowId = this.id + "-window";
            document.querySelectorAll(".working-window").forEach(window => {
                window.classList.remove("active");
            });
            document.getElementById(windowId).classList.add("active");
            document.querySelectorAll(".nav-button").forEach(btn => {
                btn.classList.remove("active");
            });
            this.classList.add("active");
        });
    });
    if (document.getElementById("tours-window")) {
        fetchTours();
    }
});

