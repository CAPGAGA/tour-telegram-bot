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
        id: null,
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

        const pointCard = createPointCard(point, index);
        list.appendChild(pointCard);
    });
}

// **Creates a point card**
function createPointCard(point, index) {
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

    const imageContainer = createImageContainer(point);
    const audioContainer = createAudioContainer(point);

    pointMedia.appendChild(imageContainer);
    pointMedia.appendChild(audioContainer);

    pointBody.appendChild(pointLabel);
    pointBody.appendChild(pointDescription);
    pointBody.appendChild(pointMedia);

    pointCard.appendChild(pointIndex);
    pointCard.appendChild(pointBody);

    return pointCard;
}

// **Creates the image container**
function createImageContainer(point) {
    const imageContainer = document.createElement("div");
    imageContainer.className = "media-container image-container";

    const imageLabel = document.createElement("label");
    imageLabel.className = "upload-label";
    imageLabel.innerText = "Images (Limit: 5)";
    imageContainer.appendChild(imageLabel);

    const imageGallery = document.createElement("div");
    imageGallery.className = "image-gallery";

    if (point.image && point.image.length > 0) {
        point.image.forEach(imageName => {
            imageGallery.appendChild(createMediaElement(imageName, "image", point));
        });
    }

    const imageInput = document.createElement("input");
    imageInput.className = "point-media-image-input";
    imageInput.type = "file";
    imageInput.accept = "image/*";
    imageInput.multiple = true;
    imageInput.addEventListener("change", function(event) {
        handleMediaUpload(event, point, "image", imageGallery, imageLabel);
    });

    imageContainer.appendChild(imageGallery);
    imageContainer.appendChild(imageInput);
    return imageContainer;
}

// **Creates the audio container**
function createAudioContainer(point) {
    const audioContainer = document.createElement("div");
    audioContainer.className = "media-container audio-container";

    const audioLabel = document.createElement("label");
    audioLabel.className = "upload-label";
    audioLabel.innerText = "Audio";
    audioContainer.appendChild(audioLabel);

    const audioGallery = document.createElement("div");
    audioGallery.className = "audio-gallery";

    if (point.audio && point.audio.length > 0) {
        point.audio.forEach(audioName => {
            audioGallery.appendChild(createMediaElement(audioName, "audio", point));
        });
    }

    const audioInput = document.createElement("input");
    audioInput.className = "point-media-audio-input";
    audioInput.type = "file";
    audioInput.accept = "audio/*";
    audioInput.addEventListener("change", function(event) {
        handleMediaUpload(event, point, "audio", audioGallery);
    });

    audioContainer.appendChild(audioGallery);
    audioContainer.appendChild(audioInput);
    return audioContainer;
}

// **Handles uploading images/audio (DISABLED UPLOAD FOR TESTING)**
function handleMediaUpload(event, point, type, gallery, label = null) {
    if (!point[type]) {
        point[type] = [];
    }

    if (type === "image" && point.image.length >= 5) {
        showMessage("Image limit reached.", "error");
        return;
    }

    Array.from(event.target.files).forEach(file => {
        const reader = new FileReader();
        reader.onload = function(e) {
            point[type].push(e.target.result); // Add to UI immediately

            const mediaElement = createMediaElement(e.target.result, type, point);
            gallery.appendChild(mediaElement);

            if (label) {
                label.innerText = `Images (${point.image.length}/5)`;
            }
        };
        reader.readAsDataURL(file);

        // *** DISABLED UPLOAD TO SERVER FOR UI TESTING ***
        /*
        const formData = new FormData();
        formData.append("rout_point_id", point.id);
        formData.append(type, file);

        fetch(`/point-media/add-${type}`, {
            method: "POST",
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            if (data.file) {
                point[type].push(data.file);
                const mediaElement = createMediaElement(data.file, type, point);
                gallery.appendChild(mediaElement);

                if (label) {
                    label.innerText = `Images (${point.image.length}/5)`;
                }
            }
        })
        .catch(error => showMessage(`Error uploading ${type}: ${error.message}`, "error"));
        */
    });
}

// **Creates image/audio element with delete button**
function createMediaElement(mediaName, type, point) {
    const mediaWrapper = document.createElement("div");
    mediaWrapper.className = `${type}-wrapper`;

    let mediaElement;
    if (type === "image") {
        mediaElement = document.createElement("img");
        mediaElement.className = "point-media-card point-image";
        mediaElement.src = mediaName;
        mediaElement.addEventListener("click", () => openImageModal(mediaElement.src));
    } else {
        mediaElement = document.createElement("audio");
        mediaElement.controls = true;
        mediaElement.innerHTML = `<source src="${mediaName}" type="audio/mpeg">`;
    }

    // **Delete Button**
    const deleteBtn = document.createElement("button");
    deleteBtn.className = "delete-media-btn";
    deleteBtn.innerHTML = "🗑️";
    deleteBtn.addEventListener("click", () => deleteMedia(mediaName, type, mediaWrapper));

    mediaWrapper.appendChild(mediaElement);
    mediaWrapper.appendChild(deleteBtn);

    return mediaWrapper;
}


// **Deletes an image/audio from UI & database**
async function deleteMedia(mediaName, type, mediaElement, point) {
    const endpoint = `/apiV1/point-media/delete-${type}/${mediaName}`;

    try {
          // **Delete from database**
          // *** DISABLED UPLOAD TO SERVER FOR UI TESTING ***
//        const response = await fetch(endpoint, { method: "DELETE" });
//
//        if (!response.ok) {
//            throw new Error(`Failed to delete ${type}`);
//        }

        // **Remove from UI**
        mediaElement.remove();

        // **Remove from the corresponding array (point.image or point.audio)**
        if (type === "image") {
            point.image = point.image.filter(img => img !== mediaName);
        } else {
            point.audio = point.audio.filter(aud => aud !== mediaName);
        }

        showMessage(`${type.charAt(0).toUpperCase() + type.slice(1)} deleted successfully.`, "success");
    } catch (error) {
        showMessage(`Error deleting ${type}: ${error.message}`, "error");
    }
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
                console.log(point)
                if (!routePoints.some(p => p.latitude === point.latitude && p.longitude === point.longitude)) {
                    routePoints.push(point);
                    L.marker([point.latitude, point.longitude]).addTo(map)
                        .bindPopup(`${routePoints.length}: ${point.point_text}`).openPopup();
                }
            });
            updateRouteList();
            console.log(routePoints)
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
    let command = 'create'

    if (point.id) {
        command = 'edit'
    }

    try {
        // Validate the point data
        if (!point.latitude || !point.longitude ) {
            throw new Error("Point must have coordinates");
        }

        // Send the base tour point data
        const pointResponse = fetch("/apiV1/rout-points/create_rout_point", {
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
        const pointData = pointResponse.json();

        // Upload images if available
        if (point.images && point.images.length) {
            for (const image of point.images) {
                const formData = new FormData();
                formData.append("image", image);
                formData.append("point_id", pointData.id);
                fetch("/apiV1/point-media/add-image", {
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
                fetch("/apiV1/point-media/add-audio", {
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

function deleteTourPoint(pointId) {

};