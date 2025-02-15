// automatically resize textareas to fill their content

export function autoResizeTextarea(textarea) {
    textarea.style.height = "auto";
    textarea.style.minHeight = "40px"; // Ensures a reasonable starting height
    textarea.style.height = textarea.scrollHeight + "px";
}