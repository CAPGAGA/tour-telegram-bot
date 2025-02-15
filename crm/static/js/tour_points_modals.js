import { showMessage } from "./revolver.js";
import {autoResizeTextarea } from "./utils.js"
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
    L.marker([newPoint.latitude, newPoint.longitude]).addTo(map)
        .bindPopup(`${routePoints.length}: ${newPoint.point_text}`).openPopup();
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

        pointDescription.addEventListener("input", function () {
            autoResizeTextarea(this);
        });
        autoResizeTextarea(pointDescription);

        const pointMedia = document.createElement("div");
        pointMedia.className = "point-media";

        const pointImageContainer = document.createElement("div");
        pointImageContainer.className = "point-image-container";

        const pointImage = document.createElement("div");
        // image gallery for point
        pointImage.className = "point-media-card point-image";
        if (point.image) {
            pointImage.style.backgroundImage = `url(${point.image})`;
            pointImage.style.backgroundSize = "cover";
        }
        // add image button
        const imageInput = document.createElement("input");
        imageInput.className = "point-media-image-input";
        imageInput.type = "file";
        imageInput.accept = "image/*";
        imageInput.multiple = true;
        imageInput.addEventListener("change", function(event) {
            Array.from(event.target.files).forEach(file => {
                const reader = new FileReader();
                reader.onload = function(e) {
                    point.images = point.images || [];
                    point.images.push(e.target.result);
                    const img = document.createElement("img");
                    img.src = e.target.result;
                    img.className = "point-media-card point-image";
                    pointImageContainer.appendChild(img);
                };
                reader.readAsDataURL(file);
            });
        });
        // audio gallery for point
        const pointAudio = document.createElement("div");
        pointAudio.className = "point-media-card point-audio";
        if (point.audio) {
            pointAudio.innerHTML = `<audio controls><source src="${point.audio}" type="audio/mpeg"></audio>`;
        }
        // add audio button
        const audioInput = document.createElement("input");
        audioInput.className = "point-media-audio-input";
        audioInput.type = "file";
        audioInput.accept = "audio/*";
        audioInput.addEventListener("change", function(event) {
            const file = event.target.files[0];
            if (file) {
                const reader = new FileReader();
                reader.onload = function(e) {
                    point.audio = e.target.result;
                    pointAudio.innerHTML = `<audio controls><source src="${e.target.result}" type="audio/mpeg"></audio>`;
                };
                reader.readAsDataURL(file);
            }
        });
        // media
        pointMedia.appendChild(pointImageContainer);
        pointMedia.appendChild(imageInput);
        pointMedia.appendChild(pointAudio);
        pointMedia.appendChild(audioInput);

        // body of card
        pointBody.appendChild(pointLabel);
        pointBody.appendChild(pointDescription);
        pointBody.appendChild(pointMedia);

        // card constructor
        pointCard.appendChild(pointIndex);
        pointCard.appendChild(pointBody);

        // add card to list
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
                        .bindPopup(`${routePoints.length}: ${point.point_text}`).openPopup();
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

// main function to work with points
function saveTourPoint(point) {
    try {
        // Validate the point data
        if (!point.latitude || !point.longitude ) {
            throw new Error("Point must have coordinates");
        }

        // Send the base tour point data
        const pointResponse = await fetch("/rout-points/create_rout_point", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                latitude: point.latitude,
                longitude: point.longitude,
                point_text: point.point_text
            })
        });

        if (!pointResponse.ok) {
            throw new Error("Failed to create route point");
        }
        const pointData = await pointResponse.json();

        // Upload images if available
        if (point.images && point.images.length) {
            for (const image of point.images) {
                const formData = new FormData();
                formData.append("image", image);
                formData.append("point_id", pointData.id);
                await fetch("/point-media/add-image", {
                    method: "POST",
                    body: formData
                });
            }
        }

        // Upload audios if available
        if (point.audios && point.audios.length) {
            for (const audio of point.audios) {
                const formData = new FormData();
                formData.append("audio", audio);
                formData.append("point_id", pointData.id);
                await fetch("/point-media/add-audio", {
                    method: "POST",
                    body: formData
                });
            }
        }

        console.log("Tour point saved successfully");
    } catch (error) {
        console.error("Error saving tour point:", error.message);
    }
}

