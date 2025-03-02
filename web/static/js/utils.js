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