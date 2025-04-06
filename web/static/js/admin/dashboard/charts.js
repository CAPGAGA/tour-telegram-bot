import { showMessage } from "../../revolver.js";

let chartInstance = null;

// Function to fetch sales data based on selected timescale
export async function fetchSalesData(timescale) {
    try {
        const response = await fetch(`/apiV1/creator_rout/get-sales-per-month?timescale=${timescale}`);

        if (!response.ok) throw new Error("Failed to fetch sales data");

        const data = await response.json();  // Awaiting the JSON response

        // Call function to create chart with the fetched data
        createSalesChart(data);
    } catch (error) {
        showMessage(error.message, "error");
    }
}

// Function to create the sales chart
function createSalesChart(data) {
    const ctx = document.getElementById('salesPerMonthChart').getContext('2d');

    if (chartInstance) {
        chartInstance.destroy();
    }

    chartInstance = new Chart(ctx, {
        type: 'line', // You can also use 'bar' for a bar chart
        data: {
            labels: data.months, // X-axis labels (months)
            datasets: [{
                label: 'Sales per Month',
                data: data.sales, // Y-axis data (sales values)
                borderColor: '#3498db', // Modern blue color
                backgroundColor: 'rgba(52, 152, 219, 0.3)', // Light blue background
                borderWidth: 2,
                pointBackgroundColor: '#3498db',
                tension: 0.3, // For smooth curve lines
                fill: true, // Fill area under the line
                hoverBackgroundColor: 'rgba(52, 152, 219, 0.5)',
            }]
        },
        options: {
            responsive: true,
            interaction: {
                mode: 'index',
                intersect: false
            },
            plugins: {
                tooltip: {
                    backgroundColor: '#2c3e50', // Dark background for tooltips
                    bodyColor: '#fff', // White text in tooltips
                    borderColor: '#3498db', // Blue border for tooltips
                    borderWidth: 1
                },
                legend: {
                    position: 'top',
                    labels: {
                        font: {
                            size: 14,
                            weight: 'bold'
                        },
                        color: '#34495e'
                    }
                }
            },
            scales: {
                x: {
                    title: {
                        display: true,
                        text: 'Month',
                        font: {
                            size: 16
                        },
                        color: '#34495e'
                    },
                    grid: {
                        color: '#ecf0f1'
                    }
                },
                y: {
                    title: {
                        display: true,
                        text: 'Sales ($)',
                        font: {
                            size: 16
                        },
                        color: '#34495e'
                    },
                    grid: {
                        color: '#ecf0f1'
                    }
                }
            },
            elements: {
                line: {
                    tension: 0.4 // Makes the line curves smoother
                },
                point: {
                    radius: 4,
                    hoverRadius: 6
                }
            }
        }
    });
}

// Function to handle time scale change and update chart
export function onTimescaleChange(event) {
    const timescale = event.target.value; // Get the selected value
    fetchSalesData(timescale);  // Fetch sales data for the selected timescale
}

// Adding event listener for the timescale dropdown menu
document.addEventListener('DOMContentLoaded', function () {
    const timescaleList = document.getElementById('timescale-list'); // ID of the list element

    // Listen for clicks on the timescale list
    timescaleList.addEventListener('click', function (event) {
        if (event.target && event.target.matches("li.timescale-option")) {
            // Get the timescale option clicked
            const timescale = event.target.getAttribute("data-timescale");

            document.querySelectorAll(".timescale-option").forEach(scl => {
                scl.classList.remove("active");
            });

            event.target.classList.add("active");

            // Fetch and display sales data based on selected timescale
            fetchSalesData(timescale);
        }
    });

    // Trigger default fetch for the initial timescale
    fetchSalesData('month');
});
