document.addEventListener("DOMContentLoaded", () => {
  console.log("Notifications script loaded")

  // Get notifications elements
  const notificationsToggle = document.getElementById("notifications-toggle")
  const notificationsPanel = document.getElementById("notifications-panel")
  const notificationsList = document.getElementById("notifications-list")
  const notificationsBadge = document.getElementById("notifications-badge")
  const clearNotificationsBtn = document.getElementById("clear-notifications")

  // Toggle notifications panel
  if (notificationsToggle) {
    notificationsToggle.addEventListener("click", (e) => {
      e.stopPropagation()
      notificationsPanel.classList.toggle("active")
    })
  }

  // Close notifications panel when clicking outside
  document.addEventListener("click", (e) => {
    if (
      notificationsPanel &&
      notificationsPanel.classList.contains("active") &&
      !notificationsPanel.contains(e.target)
    ) {
      notificationsPanel.classList.remove("active")
    }
  })

  // Clear notifications
  if (clearNotificationsBtn) {
    clearNotificationsBtn.addEventListener("click", () => {
      if (notificationsList) {
        notificationsList.innerHTML = '<div class="notification-item">No notifications</div>'
      }
      if (notificationsBadge) {
        notificationsBadge.textContent = "0"
      }
    })
  }

  // Load notifications
  loadNotifications()
})

// Load notifications
function loadNotifications() {
  const notificationsList = document.getElementById("notifications-list")
  const notificationsBadge = document.getElementById("notifications-badge")

  if (notificationsList) {
    fetch("/api/notifications")
      .then((response) => response.json())
      .then((data) => {
        const notifications = data.notifications || []
        notificationsList.innerHTML = ""

        if (notifications.length === 0) {
          notificationsList.innerHTML = '<div class="notification-item">No notifications</div>'
          if (notificationsBadge) {
            notificationsBadge.textContent = "0"
          }
        } else {
          notifications.forEach((notification) => {
            const notificationItem = document.createElement("div")
            notificationItem.className = `notification-item ${notification.type}`
            notificationItem.innerHTML = `
                            <div>${notification.message}</div>
                            <div class="time">${notification.timestamp}</div>
                        `
            notificationsList.appendChild(notificationItem)
          })

          if (notificationsBadge) {
            notificationsBadge.textContent = notifications.length
          }
        }
      })
      .catch((error) => {
        console.error("Error loading notifications:", error)
        notificationsList.innerHTML = '<div class="notification-item">Error loading notifications</div>'
      })
  }
}
