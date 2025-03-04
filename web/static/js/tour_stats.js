// **Calculates the total distance between points (Haversine Formula)**
function calculateTotalDistance(points) {
    if (points.length < 2) return 0; // Not enough points for distance calculation

    let totalDistance = 0;
    for (let i = 0; i < points.length - 1; i++) {
        const lat1 = points[i].latitude;
        const lon1 = points[i].longitude;
        const lat2 = points[i + 1].latitude;
        const lon2 = points[i + 1].longitude;

        totalDistance += haversineDistance(lat1, lon1, lat2, lon2);
    }
    return totalDistance.toFixed(2); // Round to 2 decimal places
}

// **Haversine Formula for distance calculation (in km)**
function haversineDistance(lat1, lon1, lat2, lon2) {
    const R = 6371; // Radius of the Earth in km
    const dLat = (lat2 - lat1) * Math.PI / 180;
    const dLon = (lon2 - lon1) * Math.PI / 180;

    const a = Math.sin(dLat / 2) * Math.sin(dLat / 2) +
              Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) *
              Math.sin(dLon / 2) * Math.sin(dLon / 2);

    const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
    return R * c;
}

// **Updates the route stats widget**
export function updateRouteStats(points) {
    // Calculate total distance
    const totalDistance = calculateTotalDistance(points);

    // Count the number of points
    const pointCount = points.length;

    // Count total photos
    const totalPhotos = points.reduce((count, point) => count + (point.image ? point.image.length : 0), 0);

    // Calculate total audio duration (assuming audio duration is available)
    // TODO: fix this to display correct number and not NaN
    const totalAudioLength = points.reduce((total, point) => {
        return total + (point.audio ? point.audio.reduce((sum, audio) => sum + audio.duration, 0) : 0);
    }, 0);


    // Update the UI
    document.getElementById("stat-distance").innerText = `${totalDistance} km`;
    document.getElementById("stat-points").innerText = pointCount;
    document.getElementById("stat-photos").innerText = totalPhotos;
    document.getElementById("stat-audio").innerText = `${totalAudioLength} sec`;
}