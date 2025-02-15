import { showMessage } from "./revolver.js";
import { openTourModal } from "./tours_modals.js"
import { openTourPointModal } from "./tour_points_modals.js"

export function fetchTours() {
    const adminId = document.getElementById("username").getAttribute("data-admin-id");
    fetch(`/apiV1/admin_rout/get-admin-rout?admin_id=${adminId}`)
        .then(response => response.json())
        .then(data => {
            const toursGrid = document.getElementById("tours-grid");
            toursGrid.innerHTML = "";
            // re-add first button
            const addTourButton = document.createElement("button");
            addTourButton.className = "tour-card add-tour";
            addTourButton.id = "add-tour-button";
            addTourButton.innerHTML = `<span class="plus">+</span><p>Add New Rout</p>`;
            addTourButton.addEventListener("click", openTourModal);
            toursGrid.appendChild(addTourButton);


            data.routs.forEach(tour => {
                const tourCard = document.createElement("div");
                tourCard.className = "tour-card";
                tourCard.onclick = () => openTourPointModal(tour.id);
                tourCard.innerHTML = `
                    <h3 class="tour-card-title">${tour.rout_name}</h3>
                    <p class="tour-card-description">${tour.rout_description.substring(0, 300)}...</p>
                    <p class="tour-card-price">${tour.base_price}$</p>
                    <p class="tour-card-displayed"><img class="tour-card-icon" src="/static/icons/${tour.is_displayed ? 'viz' : 'not-viz'}.png" alt="Visibility"></p>
                `;
                toursGrid.appendChild(tourCard);
            });
        })
        .catch(error => showMessage(error.message, "error"));
}

export function fetchTour(tourId) {
    fetch(`/apiV1/rout/get-rout/${tourId}`)
    .then(response => response.json())
    .then(data => {
        // base rout info
        document.getElementById("tour-point-name").value = data.rout_name;
        document.getElementById("tour-point-description").value = data.rout_description;
        document.getElementById("tour-point-price").value = data.base_price;
        document.getElementById("viz-toggle").checked = data.is_displayed ? true : false;

    })
    .catch(error => showMessage(error.message, "error"));
}

export function fetchTourPoints(tourId) {
    return fetch(`/apiV1/rout-points/get-rout?rout_id=${tourId}`)
        .then(response => {
            if (!response.ok) {
                if (response.status == 404) {
                    showMessage("This rout is empty", "info");
                    return []
                }
                showMessage(response.statusText, "error");
                throw new Error(response.statusText);
            }
            return response.json();
        })
        .catch(error => {
            showMessage(error.message, "error");
            return [];
        });
}
