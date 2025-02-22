import { showMessage } from "./revolver.js";
import {autoResizeTextarea, updateImageCounter } from "./utils.js"
import { fetchTour, fetchTourPoints } from "./fetch_tours.js"

let map;
let routePoints = [];

// redner map
export function initMap(routId) {
    map = L.map('map').setView([44.81569, 20.45174], 13);

    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; OpenStreetMap contributors'
    }).addTo(map);

    map.on('click', function(e) {
        addRoutePoint(e.latlng, routId);
    });
}

export function addDraggableSave(marker, point) {
    marker.on("dragend", function (event) {
        const newLatLng = event.target.getLatLng();
        updatePointLocation(point.id, newLatLng.lat, newLatLng.lng);
    });
}

// add new point to map, points list and point list in modal
function addRoutePoint(latlng, routId) {
    const newPoint = {
        rout_id: routId,
        latitude: latlng.lat,
        longitude: latlng.lng,
        point_text: "" // Empty text by default
    };

    fetch("/apiV1/rout-points/create", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify(newPoint)
    })
    .then(response => {
        if (!response.ok) {
            throw new Error("Failed to save point to the database");
        }
        return response.json();
    })
    .then(savedPoint => {
        // Add the saved point to `routePoints` with its new DB ID
        newPoint.id = savedPoint.id;

        // Update the UI
        const newMarker = L.marker([savedPoint.latitude, savedPoint.longitude],{
            draggable: true,
            autoPan: true
        })
            .addTo(map)
            .bindPopup(`${routePoints.length + 1}: ${savedPoint.point_text}`);

        addDraggableSave(newMarker, newPoint);

        // Add marker to point object
        newPoint.marker = newMarker;

        // Add point to list
        routePoints.push(newPoint);
        // Refresh the list
        updateRouteList();
    })
    .catch(error => {
        showMessage(`Error saving point: ${error.message}`, "error");
    });
}

// adds point to modal list
export function updateRouteList() {
    const list = document.getElementById("tour-points-list");
    list.innerHTML = "";

    routePoints.forEach((point, index) => {
        if (!point.marker) {
            const point = L.marker([point.latitude, point.longitude],{
            draggable: true,
            autoPan: true
            })
                .addTo(map)
                .bindPopup(`Point ${index + 1}: ${point.point_text}`).openPopup();
            addDraggableSave(marker, point);
            point.marker = marker;
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

    let typingTimer;

    pointDescription.addEventListener("input", function () {
        // autoresize to fit whole text
        autoResizeTextarea(this);

        // Clear the existing timer
        clearTimeout(typingTimer);

        // Set a new timer to save after 5 seconds
        typingTimer = setTimeout(() => savePointText(point.id, pointDescription.value), 5000);
    });
    // first autoresize to fit whole text
    autoResizeTextarea(pointDescription);

    // media containers
    const pointMedia = document.createElement("div");
    pointMedia.className = "point-media";

    const imageContainer = createImageContainer(point);
    const audioContainer = createAudioContainer(point);

    // deletion button
    const deleteButton = document.createElement("button");
    deleteButton.className = "delete-point-btn";
    deleteButton.innerHTML = "<img class='delete-icon' src='/static/icons/delete.png' alt='delete-icon'></img>";
    deleteButton.addEventListener("click", () => deleteRoutePoint(point));

    pointMedia.appendChild(imageContainer);
    pointMedia.appendChild(audioContainer);

    pointBody.appendChild(pointLabel);
    pointBody.appendChild(pointDescription);
    pointBody.appendChild(pointMedia);

    pointCard.appendChild(pointIndex);
    pointCard.appendChild(pointBody);
    pointCard.appendChild(deleteButton);

    return pointCard;
}

// **Creates the image container**
function createImageContainer(point) {
    const imageContainer = document.createElement("div");
    imageContainer.className = "media-container image-container";

    // ensure that point.image is not empty
    point.image = Array.isArray(point.image) ? point.image : [];

    const imageLabel = document.createElement("label");
    imageLabel.className = "upload-label";
    imageLabel.innerText = `Images (${point.image.length}/5)`;
    imageContainer.appendChild(imageLabel);

    const imageGallery = document.createElement("div");
    imageGallery.className = "image-gallery";

    if (point.image && point.image.length > 0) {
        point.image.forEach(imageData => {
            imageGallery.appendChild(createMediaElement(imageData, "image", point, imageLabel));
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

    // Count preloaded images/audio
    let currentMediaCount = point[type].length;


    // Prevent uploading if already at limit
    if (type === "image" && currentMediaCount >= 5) {
        showMessage("Image limit reached.", "error");
        return;
    }

    Array.from(event.target.files).forEach(file => {
        if (currentMediaCount >= 5) {
            showMessage("You can only upload up to 5 images.", "error");
            return;
        }

        const formData = new FormData();
        formData.append("rout_point_id", point.id);
        formData.append(type, file);
        // DISABLE THIS FOR UI TEST
        fetch(`/apiV1/point-media/add-${type}?rout_point_id=${point.id}`, {
            method: "POST",
            body: formData,
        })
        .then(response => {
            if (!response.ok) {
                throw new Error(`Upload failed: ${response.statusText}`);
            }

            return response.json();
        })
        .then(data => {
            if (data.id && data.file) {
                const mediaData = data.file;
                point[type].push(mediaData);
                currentMediaCount++; // Update count

                const mediaElement = createMediaElement(mediaData, type, point);
                gallery.appendChild(mediaElement);

                // Update the counter after adding an image
                updateImageCounter(point, label);
            }
        })
        .catch(error => showMessage(`Error uploading ${type}: ${error.message}`, "error"));
    });
}



// **Creates image/audio element with delete button**
function createMediaElement(mediaName, type, point, label) {
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
    deleteBtn.addEventListener("click", () => deleteMedia(mediaName, type, mediaWrapper, point, label));

    mediaWrapper.appendChild(mediaElement);
    mediaWrapper.appendChild(deleteBtn);

    return mediaWrapper;
}


// **Deletes an image/audio from UI & database**
function deleteMedia(mediaName, type, mediaElement, point, label) {
    const fileName = mediaName.split("/").pop();
    const endpoint = `/apiV1/point-media/delete-${type}/${fileName}`;

    fetch(endpoint, { method: "DELETE" })
        .then(response => {
            if (!response.ok) {
                throw new Error(`Failed to delete ${type}`);
            }
            return response.json();
        })
        .then(() => {
            // **Remove from UI**
            mediaElement.remove();

            // **Find the correct point and remove media from its array**
            if (type === "image" && point.image) {
                point.image = point.image.filter(img => img !== mediaName);
            } else if (type === "audio" && point.audio) {
                point.audio = point.audio.filter(aud => aud !== mediaName);
            }

            if (type === "image") {
                updateImageCounter(point, label)
            };

            showMessage(`${type.charAt(0).toUpperCase() + type.slice(1)} deleted successfully.`, "success");
        })
        .catch(error => {
            showMessage(`Error deleting ${type}: ${error.message}`, "error");
        });
}

// renders modal and all info
export function openTourPointModal(tourId) {
    const modal = document.getElementById("tour-points-modal");
    modal.style.display = "block";
    modal.style.opacity = 0;
    initMap(tourId);
    fetchTour(tourId);
    fetchTourPoints(tourId).then(points => {
        if (points) {
            points.forEach(point => {
                if (!routePoints.some(p => p.latitude === point.latitude && p.longitude === point.longitude)) {
                    routePoints.push(point);
                    const marker = L.marker([point.latitude, point.longitude],{
                            draggable: true,
                            autoPan: true
                        })
                        .addTo(map)
                        .bindPopup(`${routePoints.length}: ${point.point_text}`)
                        .openPopup();
                    addDraggableSave(marker, point);
                    point.marker = marker;
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



function deleteRoutePoint(point) {
    const endpoint = `/apiV1/rout-points/delete-rout-point?rout_point_id=${point.id}`;

    fetch(endpoint, { method: "DELETE" })
        .then(response => {
            if (!response.ok) {
                throw new Error("Failed to delete route point");
            }
            return response.json();
        })
        .then(() => {
            // Remove the point from `routePoints` array
            routePoints = routePoints.filter(p => p.id !== point.id);

            // Remove marker from map
            if (point.marker) {
                map.removeLayer(point.marker);
            }

            // Refresh the list
            updateRouteList();

            showMessage("Route point deleted successfully!", "success");
        })
        .catch(error => {
            showMessage(`Error deleting route point: ${error.message}`, "error");
        });
};

function savePointText(pointId, text) {
    fetch(`/apiV1/rout-points/edit-rout-point?rout_point_id=${pointId}`, {
        method: "PUT",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({
            id: pointId,
            point_text: text
        })
    })
    .then(response => {
        if (!response.ok) {
            throw new Error("Failed to save point text");
        }
        return response.json();
    })
    .then(() => {
        showMessage("Point text saved successfully!", "success");
    })
    .catch(error => {
        showMessage(`Error saving point text: ${error.message}`, "error");
    });
}

function updatePointLocation(pointId, newLat, newLng) {
    fetch(`/apiV1/rout-points/edit-rout-point?rout_point_id=${pointId}`, {
        method: "PUT",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({
            latitude: newLat,
            longitude: newLng
        })
    })
    .then(response => {
        if (!response.ok) {
            throw new Error("Failed to update location");
        }
        return response.json();
    })
    .then(() => {
        showMessage("Location updated successfully!", "success");
    })
    .catch(error => {
        showMessage(`Error updating location: ${error.message}`, "error");
    });
}