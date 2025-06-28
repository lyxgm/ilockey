import { Chart } from "@/components/ui/chart"
document.addEventListener("DOMContentLoaded", () => {
  // Load metrics data
  loadMetricsData()

  // Refresh data periodically
  setInterval(() => {
    loadMetricsData()
  }, 30000) // Every 30 seconds
})

// Global variables
let authChart = null
let doorChart = null

// Load metrics data
function loadMetricsData() {
  fetch("/api/metrics")
    .then((response) => response.json())
    .then((data) => {
      const metrics = data.metrics || {}

      // Update authentication metrics
      document.getElementById("auth-success").textContent = metrics.authentication?.success || 0
      document.getElementById("auth-failed").textContent = metrics.authentication?.failed || 0

      // Update door unlock metrics
      document.getElementById("door-success").textContent = metrics.door_unlock?.success || 0
      document.getElementById("door-failed").textContent = metrics.door_unlock?.failed || 0

      // Update system metrics
      const cpuUsage = metrics.system?.cpu_usage || 0
      const ramUsage = metrics.system?.ram_usage || 0
      const temperature = metrics.system?.temperature || 0
      const uptime = metrics.system?.uptime || 0

      document.getElementById("cpu-usage").textContent = `${cpuUsage}%`
      document.getElementById("cpu-progress").style.width = `${cpuUsage}%`
      document.getElementById("ram-usage").textContent = `${ramUsage}%`
      document.getElementById("ram-progress").style.width = `${ramUsage}%`
      document.getElementById("temperature").textContent = `${temperature}°C`

      // Format uptime
      const days = Math.floor(uptime / 86400)
      const hours = Math.floor((uptime % 86400) / 3600)
      const minutes = Math.floor((uptime % 3600) / 60)
      document.getElementById("uptime").textContent = `${days}d ${hours}h ${minutes}m`

      // Update camera metrics
      document.getElementById("camera-latency").textContent = `${metrics.camera?.latency || 0}ms`

      // Update charts
      updateAuthChart(metrics.authentication)
      updateDoorChart(metrics.door_unlock)
    })
    .catch((error) => console.error("Error loading metrics data:", error))
}

// Update authentication chart
function updateAuthChart(authData) {
  const ctx = document.getElementById("auth-chart")

  if (ctx) {
    if (authChart) {
      authChart.destroy()
    }

    authChart = new Chart(ctx, {
      type: "pie",
      data: {
        labels: ["Successful", "Failed"],
        datasets: [
          {
            data: [authData?.success || 0, authData?.failed || 0],
            backgroundColor: ["#2ecc71", "#e74c3c"],
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
      },
    })
  }
}

// Update door chart
function updateDoorChart(doorData) {
  const ctx = document.getElementById("door-chart")

  if (ctx) {
    if (doorChart) {
      doorChart.destroy()
    }

    doorChart = new Chart(ctx, {
      type: "pie",
      data: {
        labels: ["Successful", "Failed"],
        datasets: [
          {
            data: [doorData?.success || 0, doorData?.failed || 0],
            backgroundColor: ["#2ecc71", "#e74c3c"],
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
      },
    })
  }
}
