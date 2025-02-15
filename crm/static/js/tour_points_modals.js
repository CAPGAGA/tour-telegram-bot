import { showMessage } from "./revolver.js";
import { fetchTour, fetchTourPoints } from "./fetch_tours.js"

let map;
let routePoints = [];

// redner map
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

// add new point to map, points list and point list in modal
export function addRoutePoint(latlng) {
    const newPoint = {
        latitude: latlng.lat,
        longitude: latlng.lng,
        point_text: "",
        image: null,
        audio: null
    };
    routePoints.push(newPoint);
    L.marker([newPoint.latitude, newPoint.longitude]).addTo(map);
    updateRouteList();
}

// adds point to modal list
export function updateRouteList() {
    const list = document.getElementById("tour-points-list");
    list.innerHTML = "";

    routePoints.forEach((point, index) => {
        if (!point.marker) {
            point.marker = L.marker([point.latitude, point.longitude]).addTo(map)
                .bindPopup(`Point ${index + 1}: ${point.point_text}`).openPopup();
        }

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

// renders modal and all info
export function openTourPointModal(tourId) {
    const modal = document.getElementById("tour-points-modal");
    modal.style.display = "block";
    modal.style.opacity = 0;
    initMap();
    fetchTour(tourId);
    fetchTourPoints(tourId).then(points => {
        if (points) {
            points.forEach(point => {
                if (!routePoints.some(p => p.latitude === point.latitude && p.longitude === point.longitude)) {
                    routePoints.push(point);
                    L.marker([point.latitude, point.longitude]).addTo(map)
                        .bindPopup(`Point ${routePoints.length}: ${point.point_text}`).openPopup();
                }
            });
            updateRouteList();
        }
    });
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

