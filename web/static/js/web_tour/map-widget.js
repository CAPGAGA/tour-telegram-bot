
class MapWidget {
    constructor(containerId, options = {}) {
        this.containerId = containerId;
        this.map = null;
        this.userMarker = null;
        this.tourMarker = null;
        this.watchId = null;
        this.accuracyCircle = null;
        this.positionHistory = [];
        this.trackingPath = null;

        // Modal elements
        this.locationModal = document.getElementById('locationModal');
        this.locationError = document.getElementById('locationError');
        this.locationErrorMessage = document.getElementById('locationErrorMessage');

        // Default options
        this.options = {
            defaultLat: 37.7749,
            defaultLng: -122.4194,
            defaultZoom: 15,
            userLocationZoom: 17,
            trackUser: true,
            showAccuracy: true,
            trackPath: true,
            maxPathPoints: 100,
            pathColor: '#4285f4',
            pathWeight: 3,
            ...options
        };

        this.init();
    }

    init() {
        this.createMap();
        this.attachModalEventListeners();
        if (this.options.trackUser) {
            this.requestLocationPermission();
        }
    }

    attachModalEventListeners() {
        // Location modal event listeners
        document.getElementById('allowLocationBtn').addEventListener('click', () => {
            this.closeLocationModal();
            this.startLocationTracking();
        });

        document.getElementById('skipLocationBtn').addEventListener('click', () => {
            this.closeLocationModal();
        });

        document.getElementById('closeLocationModalBtn').addEventListener('click', () => {
            this.closeLocationModal();
        });

        // Error notification close
        document.getElementById('closeErrorBtn').addEventListener('click', () => {
            this.hideLocationError();
        });

        // Close modal on background click
        this.locationModal.querySelector('.modal-background').addEventListener('click', () => {
            this.closeLocationModal();
        });

        // Close modal on Escape key
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && this.isLocationModalOpen()) {
                this.closeLocationModal();
            }
        });
    }

    createMap() {
        const container = document.getElementById(this.containerId);
        if (!container) {
            console.error(`Container with id "${this.containerId}" not found`);
            return;
        }

        // Debug container dimensions
        console.log('Container dimensions:', {
            width: container.offsetWidth,
            height: container.offsetHeight,
            display: window.getComputedStyle(container).display
        });

        // Initialize map
        this.map = L.map(this.containerId, {
            center: [this.options.defaultLat, this.options.defaultLng],
            zoom: this.options.defaultZoom,
            zoomControl: true,
            attributionControl: true
        });

        // Add tile layer
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '© <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
            maxZoom: 19
        }).addTo(this.map);

        // Force map resize after a short delay (fixes common display issues)
        setTimeout(() => {
            if (this.map) {
                this.map.invalidateSize();
            }
        }, 100);

        console.log('Map initialized');
    }

    async requestLocationPermission() {
        if (!navigator.geolocation) {
            console.warn('Geolocation is not supported by this browser');
            this.showLocationError('Geolocation is not supported by your browser');
            return;
        }

        // Try to get permission status first, but don't rely on it entirely
        try {
            if ('permissions' in navigator) {
                const permission = await navigator.permissions.query({ name: 'geolocation' });
                console.log('Permission state:', permission.state);

                if (permission.state === 'granted') {
                    this.startLocationTracking();
                    return;
                } else if (permission.state === 'denied') {
                    this.showLocationError('Location access was previously denied. Please enable it in your browser settings.');
                    return;
                }
                // If state is 'prompt', continue to show modal
            }
        } catch (error) {
            console.log('Permissions API not available, will try direct geolocation');
        }

        // Always try to get location directly first (handles edge cases)
        this.tryDirectLocation();
    }

    tryDirectLocation() {
        const options = {
            enableHighAccuracy: false, // Start with less accuracy for faster response
            timeout: 5000, // Short timeout for quick check
            maximumAge: 60000 // Accept cached location up to 1 minute old
        };

        navigator.geolocation.getCurrentPosition(
            (position) => {
                // Success - user has already granted permission
                console.log('Location already available');
                this.onLocationSuccess(position);
                this.startLocationTracking(); // Start continuous tracking
            },
            (error) => {
                console.log('Direct location failed:', error.message);
                // Only show modal if it's a permission issue or user hasn't decided yet
                if (error.code === error.PERMISSION_DENIED) {
                    this.showLocationError('Location access denied. Please enable it in your browser settings and refresh the page.');
                } else {
                    // Show modal for user to decide
                    this.openLocationModal();
                }
            },
            options
        );
    }

    openLocationModal() {
        this.locationModal.classList.add('is-active');
        // Prevent body scroll when modal is open
        document.body.style.overflow = 'hidden';
    }

    closeLocationModal() {
        this.locationModal.classList.remove('is-active');
        // Restore body scroll
        document.body.style.overflow = '';
    }

    isLocationModalOpen() {
        return this.locationModal.classList.contains('is-active');
    }

    showLocationError(message) {
        this.locationErrorMessage.textContent = message;
        this.locationError.style.display = 'block';

        // Auto-hide after 8 seconds for longer messages
        setTimeout(() => {
            this.hideLocationError();
        }, 8000);
    }

    hideLocationError() {
        this.locationError.style.display = 'none';
    }

    startLocationTracking() {
        console.log('Starting location tracking...');

        // Options for continuous tracking
        const options = {
            enableHighAccuracy: true,
            timeout: 15000, // Longer timeout for high accuracy
            maximumAge: 30000 // 30 seconds
        };

        // Get current position first with better error handling
        navigator.geolocation.getCurrentPosition(
            (position) => {
                console.log('Location tracking started successfully');
                this.onLocationSuccess(position);
            },
            (error) => {
                console.error('Location tracking failed:', error);
                this.handleLocationError(error);
            },
            options
        );

        // Start watching position
        this.watchId = navigator.geolocation.watchPosition(
            (position) => this.onLocationUpdate(position),
            (error) => this.handleLocationError(error),
            options
        );
    }

    handleLocationError(error) {
        let message = 'Unable to get your location';

        switch (error.code) {
            case error.PERMISSION_DENIED:
                message = 'Location access denied. Please check your browser settings and allow location access for this site.';
                break;
            case error.POSITION_UNAVAILABLE:
                message = 'Your location is currently unavailable. Please check your device\'s location settings.';
                break;
            case error.TIMEOUT:
                message = 'Location request timed out. Please try again.';
                break;
            default:
                message = `Location error: ${error.message}`;
        }

        console.error('Location error:', message, error);
        this.showLocationError(message);
    }

    stopLocationTracking() {
        if (this.watchId !== null) {
            navigator.geolocation.clearWatch(this.watchId);
            this.watchId = null;
            console.log('Location tracking stopped');
        }

        if (this.userMarker) {
            this.map.removeLayer(this.userMarker);
            this.userMarker = null;
        }
    }

    onLocationSuccess(position) {
        const { latitude, longitude, accuracy } = position.coords;

        console.log('Location acquired:', { latitude, longitude, accuracy: `${Math.round(accuracy)}m` });

        this.updateUserLocation(latitude, longitude, accuracy);

        // Center map on user location
        this.map.setView([latitude, longitude], this.options.userLocationZoom);

        // Hide any error messages
        this.hideLocationError();
    }

    onLocationUpdate(position) {
        const { latitude, longitude, accuracy } = position.coords;
        console.log('Location updated:', { latitude, longitude, accuracy: `${Math.round(accuracy)}m` });
        this.updateUserLocation(latitude, longitude, accuracy);
    }

    updateUserLocation(lat, lng, accuracy) {
        const newPosition = { lat, lng, accuracy, timestamp: Date.now() };

        // Add to position history
        this.positionHistory.push(newPosition);

        // Limit history size
        if (this.positionHistory.length > this.options.maxPathPoints) {
            this.positionHistory.shift();
        }

        // Remove old user marker and accuracy circle
        if (this.userMarker) {
            this.map.removeLayer(this.userMarker);
        }
        if (this.accuracyCircle) {
            this.map.removeLayer(this.accuracyCircle);
        }

        // Create user location marker with improved styling
        const userIcon = L.divIcon({
            className: 'user-location-marker',
            html: `<div class="user-location-dot" data-accuracy="${Math.round(accuracy)}"></div>`,
            iconSize: [20, 20],
            iconAnchor: [10, 10]
        });

        this.userMarker = L.marker([lat, lng], { icon: userIcon })
            .addTo(this.map)
            .bindPopup(this.getUserLocationPopupContent(lat, lng, accuracy));

        // Add accuracy circle if enabled
        if (this.options.showAccuracy && accuracy < 200) {
            this.accuracyCircle = L.circle([lat, lng], {
                radius: accuracy,
                color: this.options.pathColor,
                fillColor: this.options.pathColor,
                fillOpacity: 0.1,
                weight: 1
            }).addTo(this.map);
        }

        // Update tracking path
        if (this.options.trackPath && this.positionHistory.length > 1) {
            this.updateTrackingPath();
        }

        // Calculate distance to tour point if available
        if (this.tourMarker) {
            const distance = this.calculateDistance(
                lat, lng,
                this.tourMarker.getLatLng().lat,
                this.tourMarker.getLatLng().lng
            );
            console.log(`Distance to tour point: ${distance.toFixed(0)}m`);
        }
    }

    updateTrackingPath() {
        // Remove existing path
        if (this.trackingPath) {
            this.map.removeLayer(this.trackingPath);
        }

        // Create path from position history
        const pathCoords = this.positionHistory.map(pos => [pos.lat, pos.lng]);

        if (pathCoords.length > 1) {
            this.trackingPath = L.polyline(pathCoords, {
                color: this.options.pathColor,
                weight: this.options.pathWeight,
                opacity: 0.7,
                smoothFactor: 1
            }).addTo(this.map);
        }
    }

    getUserLocationPopupContent(lat, lng, accuracy) {
        const speed = this.calculateSpeed();
        const totalDistance = this.calculateTotalDistance();

        let content = `
            <div class="user-location-popup">
                <strong>📍 Your Location</strong><br>
                <small>Accuracy: ${Math.round(accuracy)}m</small>
        `;

        if (speed !== null) {
            content += `<br><small>Speed: ${speed.toFixed(1)} km/h</small>`;
        }

        if (totalDistance > 0) {
            content += `<br><small>Distance traveled: ${totalDistance.toFixed(0)}m</small>`;
        }

        if (this.tourMarker) {
            const distanceToTour = this.calculateDistance(
                lat, lng,
                this.tourMarker.getLatLng().lat,
                this.tourMarker.getLatLng().lng
            );
            content += `<br><small>To tour point: ${distanceToTour.toFixed(0)}m</small>`;
        }

        content += '</div>';
        return content;
    }

    calculateSpeed() {
        if (this.positionHistory.length < 2) return null;

        const recent = this.positionHistory.slice(-2);
        const timeDiff = (recent[1].timestamp - recent[0].timestamp) / 1000; // seconds

        if (timeDiff === 0) return null;

        const distance = this.calculateDistance(
            recent[0].lat, recent[0].lng,
            recent[1].lat, recent[1].lng
        );

        return (distance / timeDiff) * 3.6; // Convert m/s to km/h
    }

    calculateTotalDistance() {
        if (this.positionHistory.length < 2) return 0;

        let totalDistance = 0;
        for (let i = 1; i < this.positionHistory.length; i++) {
            totalDistance += this.calculateDistance(
                this.positionHistory[i-1].lat, this.positionHistory[i-1].lng,
                this.positionHistory[i].lat, this.positionHistory[i].lng
            );
        }

        return totalDistance;
    }

    calculateDistance(lat1, lng1, lat2, lng2) {
        // Haversine formula to calculate distance between two points
        const R = 6371000; // Earth's radius in meters
        const φ1 = lat1 * Math.PI / 180;
        const φ2 = lat2 * Math.PI / 180;
        const Δφ = (lat2 - lat1) * Math.PI / 180;
        const Δλ = (lng2 - lng1) * Math.PI / 180;

        const a = Math.sin(Δφ/2) * Math.sin(Δφ/2) +
                  Math.cos(φ1) * Math.cos(φ2) *
                  Math.sin(Δλ/2) * Math.sin(Δλ/2);
        const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a));

        return R * c; // Distance in meters
    }

    // Public methods for tour functionality
    addTourPoint(lat, lng, title = 'Tour Point', description = '') {
        if (this.tourMarker) {
            this.map.removeLayer(this.tourMarker);
        }

        const tourIcon = L.divIcon({
            className: 'tour-marker',
            html: '<div class="tour-marker-pin">📍</div>',
            iconSize: [30, 30],
            iconAnchor: [15, 30]
        });

        this.tourMarker = L.marker([lat, lng], { icon: tourIcon })
            .addTo(this.map)
            .bindPopup(`<strong>${title}</strong><br>${description}`)
            .openPopup();

        // Update user location popup if available
        if (this.userMarker) {
            const userPos = this.userMarker.getLatLng();
            this.userMarker.setPopupContent(
                this.getUserLocationPopupContent(
                    userPos.lat,
                    userPos.lng,
                    this.positionHistory.length > 0 ? this.positionHistory[this.positionHistory.length - 1].accuracy : 0
                )
            );
        }

        return this.tourMarker;
    }

    centerOnTourPoint() {
        if (this.tourMarker) {
            this.map.setView(this.tourMarker.getLatLng(), this.options.userLocationZoom);
        }
    }

    centerOnUser() {
        if (this.userMarker) {
            this.map.setView(this.userMarker.getLatLng(), this.options.userLocationZoom);
        }
    }

    showBothMarkers() {
        if (this.userMarker && this.tourMarker) {
            const group = L.featureGroup([this.userMarker, this.tourMarker]);
            this.map.fitBounds(group.getBounds(), { padding: [20, 20] });
        }
    }

    // Public method to refresh map display
    refreshMap() {
        if (this.map) {
            this.map.invalidateSize();
            console.log('Map refreshed');
        }
    }

    // New public methods for position tracking
    getPositionHistory() {
        return [...this.positionHistory]; // Return copy
    }

    clearPositionHistory() {
        this.positionHistory = [];
        if (this.trackingPath) {
            this.map.removeLayer(this.trackingPath);
            this.trackingPath = null;
        }
        console.log('Position history cleared');
    }

    exportPositionData() {
        return {
            positions: this.positionHistory,
            totalDistance: this.calculateTotalDistance(),
            startTime: this.positionHistory.length > 0 ? this.positionHistory[0].timestamp : null,
            endTime: this.positionHistory.length > 0 ? this.positionHistory[this.positionHistory.length - 1].timestamp : null
        };
    }

    togglePathVisibility() {
        if (this.trackingPath) {
            if (this.map.hasLayer(this.trackingPath)) {
                this.map.removeLayer(this.trackingPath);
                console.log('Path hidden');
                return false;
            } else {
                this.map.addLayer(this.trackingPath);
                console.log('Path shown');
                return true;
            }
        }
        return null;
    }

    fitToTrackingPath() {
        if (this.trackingPath) {
            this.map.fitBounds(this.trackingPath.getBounds(), { padding: [20, 20] });
        }
    }

    // Public method to manually trigger location modal
    requestLocation() {
        this.requestLocationPermission();
    }

    // Enhanced cleanup method
    destroy() {
        this.stopLocationTracking();
        if (this.trackingPath) {
            this.map.removeLayer(this.trackingPath);
        }
        if (this.accuracyCircle) {
            this.map.removeLayer(this.accuracyCircle);
        }
        if (this.map) {
            this.map.remove();
        }
        this.closeLocationModal();
        this.hideLocationError();
        this.positionHistory = [];
    }
}



document.addEventListener("DOMContentLoaded", function () {

    const mapWidget = new MapWidget('map', {
        defaultLat: 37.7749,
        defaultLng: -122.4194,
        trackUser: true,
        showAccuracy: true
    });

    // Add a tour point (example)
    setTimeout(() => {
        mapWidget.addTourPoint(
            45.152823,
            19.839515,
            'Historic Building',
            'Built in 1906, this building survived the great earthquake.'
        );
    }, 2000);
})
