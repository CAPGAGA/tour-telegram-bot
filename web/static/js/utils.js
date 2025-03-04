import { showMessage } from "./revolver.js";

// automatically resize textareas to fill their content
export function autoResizeTextarea(textarea) {
    textarea.style.height = "auto";
    textarea.style.minHeight = "40px"; // Ensures a reasonable starting height
    textarea.style.height = textarea.scrollHeight + "px";
}

// **Updates and rerenders the image counter (x/5)**
export function updateImageCounter(point, label) {
    if (!point || !label) return;

    // Count total images
    const imageCount = point.image ? point.image.length : 0;

    // Update label text
    label.innerText = `Images (${imageCount}/5)`;
}

export function addVizTogglerCheck(toggler, tourId) {
    toggler.addEventListener("change", function () {
        const isDisplayed = toggler.checked;
        const data = {
            is_displayed: isDisplayed
        }

        fetch(`/apiV1/rout/display-rout/${tourId}`, {
            method: "PUT",
            body: JSON.stringify(data),
            headers: {
                "Content-Type": "application/json"
            }
        })
        .then(response => response.json().then(data => ({ status: response.status, body: data }))) // ✅ Extract response body
        .then(({ status, body }) => {
            if (status !== 200) {
                showMessage(`Error updating route: ${body.detail}`, "error");

                // Revert toggle switch on failure
                toggler.checked = !isDisplayed;
                throw new Error(body.detail);
            }

            showMessage(`Route is now ${isDisplayed ? "visible" : "hidden"}!`, "success");
        })
        .catch(error => {
            console.error("Request failed:", error);
            showMessage(`Error updating route: ${error.message}`, "error");

            // Ensure toggle is reverted on error
            toggler.checked = !isDisplayed;
        });
    });
}

export function updateTourImage(imageInput, tourId) {
    imageInput.addEventListener("change", function (event) {
        const file = event.target.files[0]; // Get the selected file
        if (!file) return; // No file selected

        // Select the tour image element
        const tourImage = document.getElementById("tour-point-image");
        if (!tourImage) {
            console.error("Tour image element not found!");
            return;
        }

        // Create form data to send the image
        const formData = new FormData();
        formData.append("image", file);
        formData.append("rout_id", tourId);

        // Upload the image via API
        fetch(`/apiV1/rout/upload-image/${tourId}`, {
            method: "POST",
            body: formData
        })
        .then(response => {
            if (!response.ok) {
                throw new Error("Failed to upload image");
            }
            return response.json();
        })
        .then(data => {
            if (data.image_url) {
                // Update UI with new image
                tourImage.src = data.image_url;
                tourImage.style.display = "block";

                if (typeof showMessage === "function") {
                    showMessage("Image uploaded successfully!", "success");
                }
            }
        })
        .catch(error => {
            console.error("Image upload failed:", error);
            if (typeof showMessage === "function") {
                showMessage("Image upload failed!", "error");
            }
        });
    });
}