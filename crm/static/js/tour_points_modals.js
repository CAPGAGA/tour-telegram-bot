import { showMessage } from "./revolver.js";
import { fetchTour, fetchTourPoints } from "./fetch_tours.js"

let map;
let routePoints = [];

export function initMap() {
    map = L.map('map').setView([44.81569, 20.45174], 13);

    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; OpenStreetMap contributors'
    }).addTo(map);

    map.on('click', function(e) {
        console.log('adding point');
        addRoutePoint(e.latlng);
    });
}

export function addRoutePoint(latlng) {
    routePoints.push(latlng);
    L.marker(latlng).addTo(map);
    updateRouteList();
}

export function updateRouteList() {
    const list = document.getElementById("tour-points-list");
    list.innerHTML = "";
    routePoints.forEach((point, index) => {
        const pointCard = document.createElement("div");
        pointCard.className = "tour-point-card";

        const pointIndex = document.createElement("div");
        pointIndex.className = "point-index";
        pointIndex.innerText = `${index + 1}`;

        const pointBody = document.createElement("div");
        pointBody.className = "point-body";

        const pointLabel = document.createElement("label");
        pointLabel.className = "point-label";
        pointLabel.innerText = "Text for point (optional)";

        const pointDescription = document.createElement("textarea");
        pointDescription.className = "point-description";

        const pointMedia = document.createElement("div");
        pointMedia.className = "point-media";

        const pointImage = document.createElement("div");
        pointImage.className = "point-image";

        const pointAudio = document.createElement("div");
        pointAudio.className = "point-audio";

        pointMedia.appendChild(pointImage);
        pointMedia.appendChild(pointAudio);
        pointBody.appendChild(pointLabel);
        pointBody.appendChild(pointDescription);
        pointBody.appendChild(pointMedia);

        pointCard.appendChild(pointIndex);
        pointCard.appendChild(pointBody);

        list.appendChild(pointCard);
    });
}

export function populateMapAndList(points) {
    routePoints = points;

    const list = document.getElementById("tour-points-list");
    list.innerHTML = "";

    points.forEach((point, index) => {
        // Add marker to map
        L.marker([point.latitude, point.longitude]).addTo(map)
            .bindPopup(`Point ${index + 1}: ${point.point_text}`).openPopup();

        // Create point card
        const pointCard = document.createElement("div");
        pointCard.className = "tour-point-card";

        const pointIndex = document.createElement("div");
        pointIndex.className = "point-index";
        pointIndex.innerText = index + 1;

        const pointBody = document.createElement("div");
        pointBody.className = "point-body";

        const pointLabel = document.createElement("label");
        pointLabel.className = "point-label";
        pointLabel.innerText = "Text for point";

        const pointDescription = document.createElement("textarea");
        pointDescription.className = "point-description";
        pointDescription.value = point.point_text;

        const pointMedia = document.createElement("div");
        pointMedia.className = "point-media";

        const pointImage = document.createElement("div");
        pointImage.className = "point-image";
        if (point.image) {
            pointImage.style.backgroundImage = `url(${point.image})`;
            pointImage.style.backgroundSize = "cover";
        }

        const pointAudio = document.createElement("div");
        pointAudio.className = "point-audio";
        if (point.audio) {
            pointAudio.innerHTML = `<audio controls><source src="${point.audio}" type="audio/mpeg"></audio>`;
        }

        pointMedia.appendChild(pointImage);
        pointMedia.appendChild(pointAudio);
        pointBody.appendChild(pointLabel);
        pointBody.appendChild(pointDescription);
        pointBody.appendChild(pointMedia);

        pointCard.appendChild(pointIndex);
        pointCard.appendChild(pointBody);

        list.appendChild(pointCard);
    });
}



export function openTourPointModal(tourId) {
    const modal = document.getElementById("tour-points-modal");
    fetchTour(tourId);
    let points = fetchTourPoints(tourId);
    if (points) {
        points.forEach(point => routePoints.push({
            latitude: point.latitude,
            longitude: point.longitude,
            point_text: point.point_text,
            image: point.image,
            audio: point.audio
        }))
    }

    modal.style.display = "block";
    modal.style.opacity = 0;
    initMap();
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
    if (map) {
        map.remove()
        map = null;
    }
    document.getElementById("tour-points-list").innerHTML = "";
    routePoints = []
    setTimeout(() => {
        modal.style.display = "none";
    }, 700);
}

document.addEventListener("DOMContentLoaded", function () {
    document.querySelector("#close-tour-points-modal").addEventListener("click", closeTourPointModal);
});

