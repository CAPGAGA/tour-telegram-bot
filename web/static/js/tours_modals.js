import { fetchTours } from "./fetch_tours.js";
import { showMessage } from "./revolver.js";

export function openTourModal() {
    const modal = document.getElementById("tour-modal")
    modal.style.display = "block";
    modal.style.opacity = 0;
    setTimeout(() => {
        modal.style.opacity = 1;
        modal.style.transition = "opacity 0.2s ease-in-out";
    }, 50);
}

document.getElementById("add-tour-button").addEventListener("click", openTourModal);

export function closeTourModal() {
    const modal =document.getElementById("tour-modal")
    modal.style.opacity = 0;
    setTimeout(() => {
        modal.style.display = "none";
    }, 700);

    document.getElementById("new-tour-form").reset();
}

document.getElementById("close-add-tour-modal").addEventListener("click", closeTourModal);

export function openTourDetailModal(tourId) {
    alert("Opening tour details for ID: " + tourId);
}

export function closeTourDetailModal() {
    alert("Closing tour details");
}

document.getElementById("new-tour-form").addEventListener("submit", function(event) {
    event.preventDefault();
    const creatorId = document.getElementById("username").getAttribute("data-creator-id"); // Replace with dynamic admin ID if needed
    const requestData = {
        rout_name: document.getElementById("tour-name").value,
        rout_description: document.getElementById("tour-description").value,
        base_price: parseFloat(document.getElementById("tour-price").value),
    };

    fetch("/apiV1/rout/create", {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
        },
        body: JSON.stringify(requestData),
    })
    .then(response => response.json())
    .then(data => {
        const routId = data.id;
        return fetch("/apiV1/creator_rout/link-rout", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify({ creator_id: creatorId, rout_id: routId }),
        });
    })
    .then(response => response.json())
    .then(() => {
        showMessage("Rout added successfully", "success")
        closeTourModal();
        fetchTours();
    })
    .catch(error => console.error("Error adding and linking tour:", error));
});