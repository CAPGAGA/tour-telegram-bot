import { showMessage } from "../revolver.js";

document.addEventListener("DOMContentLoaded", function () {
    const miniShopGrid = document.getElementById("mini-shop-grid");

    fetch("/apiV1/rout/get-routs/")
    .then(response => {
        if (!response.ok) {
            throw new Error("Failed to fetch tours");
        }
        return response.json();
    })
    .then(data => {
        miniShopGrid.innerHTML = ""; // Clear existing content

        data.slice(0, 3).forEach(tour => {
            const tourCard = document.createElement("div");
            tourCard.className = "column is-one-third";
            tourCard.innerHTML = `
                <div class="card">
                    <div class="card-image">
                        <figure class="image is-4by3">
                            <img src="${tour.image ? `media/images/${tour.image}` : '/static/images/placeholder-image.jpg'}" alt="Tour Image">
                        </figure>
                    </div>
                    <div class="card-content">
                        <h5 class="title is-5">${tour.rout_name}</h5>
                        <p class="subtitle is-6">${tour.rout_description.substring(0, 100)}...</p>
                        <h6 class="has-text-primary">$${tour.base_price}</h6>
                        <a href="/tour/${tour.id}" class="button is-link">View Details</a>
                    </div>
                </div>
            `;

            miniShopGrid.appendChild(tourCard);
        });
    })
    .catch(error => {
        console.error("Error loading mini shop:", error);
        miniShopGrid.innerHTML = "<p class='has-text-danger'>Failed to load tours. Try again later.</p>";
    });
});