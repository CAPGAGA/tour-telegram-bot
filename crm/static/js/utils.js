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