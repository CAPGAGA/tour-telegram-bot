
export function showMessage(text, type) {
    const messageBox = document.createElement("div");
    messageBox.className = `message-box ${type}`;
    messageBox.innerText = text;
    document.body.appendChild(messageBox);

    setTimeout(() => {
        messageBox.remove();
    }, 5000);
}