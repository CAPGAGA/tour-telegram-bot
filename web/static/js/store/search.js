import { showMessage } from "../revolver.js";

document.addEventListener("DOMContentLoaded", function () {
    const searchInput = document.getElementById("search-input");
//    const cityInput = document.getElementById("city-input");
//    const countryInput = document.getElementById("country-input");
//    const maxPriceInput = document.getElementById("max-price");
//    const minRatingInput = document.getElementById("min-rating");
    const searchBtn = document.getElementById("search-btn");
    const tourList = document.getElementById("tour-list");
    const prevPageBtn = document.getElementById("prev-page");
    const nextPageBtn = document.getElementById("next-page");

    let currentPage = 1;

    function fetchTours() {
        let queryParams = new URLSearchParams({
            search: searchInput.value || "",
//            Not implemented yet
//            city: cityInput.value || "",
//            country: countryInput.value || "",
//            max_price: maxPriceInput.value || "",
//            min_rating: minRatingInput.value || "",
            page: currentPage,
            limit: 9
        });

        fetch(`/apiV1/search/get-routs?${queryParams}`)
            .then(response => response.json())
            .then(data => {
                renderTours(data);
            })
            .catch(error => console.error("Error fetching tours:", error));
    }

    function renderTours(tours) {
        tourList.innerHTML = "";

        if (tours.length === 0) {
            tourList.innerHTML = `<p class="has-text-danger">No tours found.</p>`;
            return;
        }

        tours.forEach(tour => {
            const tourCard = document.createElement("div");
            tourCard.className = "column is-one-third";

            tourCard.innerHTML = `
                <div class="card">
                    <div class="card-image">
                        <figure class="image is-4by3">
                            <img src="${'media/images/' + tour.image || '/static/images/placeholder.jpg'}" alt="${tour.rout_name}">
                        </figure>
                    </div>
                    <div class="card-content">
                        <p class="title">${tour.rout_name}</p>
                        <p class="subtitle">$${tour.base_price.toFixed(2)}</p>
                        <p>${tour.rout_description.substring(0, 100)}...</p>
                    </div>
                    <footer class="card-footer">
                        <a href="tour/${tour.id}" class="card-footer-item" data-tour-id="${tour.id}">Learn More</a>
                    </footer>
                </div>
            `;

            tourList.appendChild(tourCard);
        });

        attachBuyListeners();
    }

    function attachBuyListeners() {
        document.querySelectorAll(".buy-btn").forEach(button => {
            button.addEventListener("click", function () {
                const tourId = this.getAttribute("data-tour-id");
                window.location.href = `/tour/${tourId}`;
            });
        });
    }

    searchBtn.addEventListener("click", () => {
        currentPage = 1;
        fetchTours();
    });

    prevPageBtn.addEventListener("click", () => {
        if (currentPage > 1) {
            currentPage--;
            fetchTours();
        }
    });

    nextPageBtn.addEventListener("click", () => {
        currentPage++;
        fetchTours();
    });

    fetchTours();
});
