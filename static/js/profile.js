// Profile management functionality
let currentUserData = null
let originalUsername = null

// Load user profile data
function loadProfile() {
  console.log("Loading profile data...")

  fetch("/api/profile")
    .then((response) => response.json())
    .then((data) => {
      console.log("Profile data received:", data)

      if (data.success && data.profile) {
        currentUserData = data.profile
        // Get username from session
        fetch("/api/user/current")
          .then((response) => response.json())
          .then((userData) => {
            if (userData.success && userData.user) {
              originalUsername = userData.user.username
              currentUserData.username = userData.user.username
              displayProfileData(currentUserData)
              loadFingerprintStatus()
              loadUserActivity()
            }
          })
          .catch(() => {
            // Fallback if current user API fails
            displayProfileData(data.profile)
            loadFingerprintStatus()
            loadUserActivity()
          })
      } else {
        console.error("Failed to load profile:", data.message)
        showNotification("Failed to load profile data", "error")
      }
    })
    .catch((error) => {
      console.error("Error loading profile:", error)
      showNotification("Error loading profile data", "error")
    })
}

// Display profile data in the form and UI
function displayProfileData(profile) {
  console.log("Displaying profile data:", profile)

  const username = profile.username || originalUsername || getCurrentUsername()

  // Update current user display
  const usernameDisplay = document.getElementById("current-username-display")
  const userRole = document.getElementById("current-user-role")
  const userAvatar = document.getElementById("user-avatar")

  if (usernameDisplay) {
    usernameDisplay.textContent = username
  }

  if (userRole) {
    userRole.textContent = `${profile.role || "guest"} • ${profile.access_type || "full"} access`
  }

  if (userAvatar) {
    userAvatar.textContent = username.charAt(0).toUpperCase()
  }

  // Update form fields
  const fields = {
    "profile-username": username,
    "profile-email": profile.email || "",
    "profile-role": profile.role || "guest",
    "profile-access-type": profile.access_type || "full",
  }

  Object.entries(fields).forEach(([fieldId, value]) => {
    const field = document.getElementById(fieldId)
    if (field) {
      field.value = value
      console.log(`Set ${fieldId} to:`, value)
    } else {
      console.warn(`Field ${fieldId} not found`)
    }
  })

  // Handle access until date
  const accessUntilGroup = document.getElementById("profile-access-until-group")
  const accessUntilField = document.getElementById("profile-access-until")

  if (profile.access_type === "limited" && profile.access_until) {
    if (accessUntilGroup) accessUntilGroup.style.display = "block"
    if (accessUntilField) accessUntilField.value = profile.access_until
  } else {
    if (accessUntilGroup) accessUntilGroup.style.display = "none"
  }

  // Display permissions
  displayUserPermissions(profile.permissions || [])

  // Store username globally for fingerprint operations
  window.currentUsername = username
}

// Display user permissions
function displayUserPermissions(permissions) {
  const permissionsContainer = document.getElementById("user-permissions")
  if (!permissionsContainer) return

  const permissionIcons = {
    unlock: "fas fa-unlock",
    view_logs: "fas fa-list",
    manage_users: "fas fa-users",
    change_settings: "fas fa-cog",
  }

  const permissionLabels = {
    unlock: "Door Control",
    view_logs: "View Logs",
    manage_users: "Manage Users",
    change_settings: "Change Settings",
  }

  if (permissions.length === 0) {
    permissionsContainer.innerHTML = '<p class="text-muted">No permissions assigned</p>'
    return
  }

  const permissionsList = permissions
    .map((permission) => {
      const icon = permissionIcons[permission] || "fas fa-check"
      const label = permissionLabels[permission] || permission

      return `
            <div class="permission-item">
                <i class="${icon}"></i>
                <span>${label}</span>
            </div>
        `
    })
    .join("")

  permissionsContainer.innerHTML = permissionsList
}

// Load user activity
function loadUserActivity() {
  const username = getCurrentUsername()
  if (!username) {
    console.log("No username available for loading activity")
    return
  }

  console.log("Loading activity for user:", username)

  fetch("/api/logs")
    .then((response) => response.json())
    .then((data) => {
      if (data.success) {
        console.log("All logs received:", data.logs.length)
        // Filter logs for current user only
        const userLogs = data.logs.filter((log) => {
          return log.user === username || log.user === originalUsername
        })
        console.log("User logs filtered:", userLogs.length, "for user:", username)
        displayUserActivity(userLogs.slice(0, 15)) // Show last 15 activities
      } else {
        console.error("Failed to load logs:", data.message)
        displayUserActivity([])
      }
    })
    .catch((error) => {
      console.error("Error loading user activity:", error)
      displayUserActivity([])
    })
}

// Display user activity
function displayUserActivity(logs) {
  const activityContainer = document.getElementById("profile-activity")
  if (!activityContainer) return

  if (logs.length === 0) {
    activityContainer.innerHTML = '<p class="text-muted">No recent activity found</p>'
    return
  }

  const activityList = logs
    .map((log) => {
      const statusClass =
        log.status === "success" || log.status === "unlock" ? "success" : log.status === "failed" ? "error" : "info"

      return `
            <div class="activity-item">
                <div class="activity-icon ${statusClass}">
                    <i class="fas fa-${getActivityIcon(log.action)}"></i>
                </div>
                <div class="activity-details">
                    <div class="activity-title">${formatActivityTitle(log)}</div>
                    <div class="activity-time">${formatTimestamp(log.timestamp)}</div>
                    ${log.details ? `<div class="activity-details-text">${log.details}</div>` : ""}
                </div>
            </div>
        `
    })
    .join("")

  activityContainer.innerHTML = activityList
}

// Get activity icon
function getActivityIcon(action) {
  const icons = {
    door: "door-open",
    login: "sign-in-alt",
    logout: "sign-out-alt",
    camera: "camera",
    fingerprint: "fingerprint",
    profile: "user-edit",
    passcode: "key",
    user: "user-cog",
    settings: "cog",
  }
  return icons[action] || "info-circle"
}

// Format activity title
function formatActivityTitle(log) {
  const titles = {
    door: log.status === "unlock" ? "Door Unlocked" : "Door Locked",
    login: log.status === "success" ? "Logged In Successfully" : "Login Failed",
    logout: "Logged Out",
    camera: log.status === "capture" ? "Image Captured" : "Camera " + log.status,
    fingerprint:
      "Fingerprint " +
      (log.status === "enrolled"
        ? "Enrolled"
        : log.status === "success"
          ? "Authentication Success"
          : "Authentication Failed"),
    profile: "Profile Updated",
    passcode: log.status === "success" ? "Passcode Authentication Success" : "Passcode Failed",
    user: "User Account " + log.status,
    settings: "Settings Updated",
  }
  return titles[log.action] || `${log.action.charAt(0).toUpperCase() + log.action.slice(1)} - ${log.status}`
}

// Format timestamp
function formatTimestamp(timestamp) {
  try {
    const date = new Date(timestamp)
    const now = new Date()
    const diffMs = now - date
    const diffMins = Math.floor(diffMs / 60000)
    const diffHours = Math.floor(diffMs / 3600000)
    const diffDays = Math.floor(diffMs / 86400000)

    if (diffMins < 1) return "Just now"
    if (diffMins < 60) return `${diffMins} minutes ago`
    if (diffHours < 24) return `${diffHours} hours ago`
    if (diffDays < 7) return `${diffDays} days ago`

    return date.toLocaleDateString() + " " + date.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })
  } catch (error) {
    return timestamp
  }
}

// Handle profile form submission
function handleProfileSubmit(event) {
  event.preventDefault()

  const formData = new FormData(event.target)
  const profileData = {}

  // Get form values
  const newUsername = formData.get("username").trim()
  profileData.email = formData.get("email")

  // Check if username changed
  if (newUsername !== originalUsername) {
    profileData.username = newUsername
  }

  // Handle password change
  const newPassword = formData.get("password")
  if (newPassword && newPassword.trim()) {
    const currentPassword = prompt("Enter your current password to change it:")
    if (!currentPassword) {
      showNotification("Password change cancelled", "info")
      return
    }
    profileData.current_password = currentPassword
    profileData.new_password = newPassword
  }

  console.log("Submitting profile data:", profileData)

  fetch("/api/profile", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(profileData),
  })
    .then((response) => response.json())
    .then((data) => {
      if (data.success) {
        showNotification("Profile updated successfully!", "success")

        // If username changed, update the original username and reload
        if (profileData.username) {
          originalUsername = profileData.username
          window.currentUsername = profileData.username

          // Update header username if it exists
          const headerUsername = document.querySelector(".user-info span")
          if (headerUsername) {
            headerUsername.textContent = profileData.username
          }
        }

        loadProfile() // Reload profile data

        // Clear password field
        const passwordField = document.getElementById("profile-password")
        if (passwordField) passwordField.value = ""
      } else {
        showNotification(data.message || "Failed to update profile", "error")
      }
    })
    .catch((error) => {
      console.error("Error updating profile:", error)
      showNotification("Error updating profile", "error")
    })
}

// Load fingerprint status
function loadFingerprintStatus() {
  const username = getCurrentUsername()
  if (!username) return

  console.log("Loading fingerprint status for:", username)

  fetch(`/api/fingerprint/status/${username}`)
    .then((response) => response.json())
    .then((data) => {
      console.log("Fingerprint status:", data)
      updateProfileFingerprintStatus(data)
    })
    .catch((error) => {
      console.error("Error loading fingerprint status:", error)
      updateProfileFingerprintStatus({ success: false, enrolled: false })
    })
}

// Update fingerprint status display
function updateProfileFingerprintStatus(data) {
  const statusElement = document.getElementById("profile-fingerprint-status")
  const enrollBtn = document.getElementById("profile-enroll-fingerprint-btn")
  const deleteBtn = document.getElementById("profile-delete-fingerprint-btn")
  const enrollmentDetails = document.getElementById("enrollment-details")
  const enrollmentDate = document.getElementById("enrollment-date")

  if (data.success && data.enrolled) {
    if (statusElement) {
      statusElement.textContent = "Enrolled"
      statusElement.className = "status-badge enrolled"
    }

    if (enrollBtn) enrollBtn.style.display = "none"
    if (deleteBtn) deleteBtn.style.display = "inline-block"

    if (data.enrolled_date && enrollmentDate) {
      enrollmentDate.textContent = new Date(data.enrolled_date).toLocaleDateString()
      if (enrollmentDetails) enrollmentDetails.style.display = "block"
    }
  } else {
    if (statusElement) {
      statusElement.textContent = "Not Enrolled"
      statusElement.className = "status-badge not-enrolled"
    }

    if (enrollBtn) enrollBtn.style.display = "inline-block"
    if (deleteBtn) deleteBtn.style.display = "none"
    if (enrollmentDetails) enrollmentDetails.style.display = "none"
  }
}

// Get current username from session/profile
function getCurrentUsername() {
  // Try to get from stored data first
  if (originalUsername) {
    return originalUsername
  }

  if (currentUserData && currentUserData.username) {
    return currentUserData.username
  }

  // Try to get from global variable
  if (window.currentUsername) {
    return window.currentUsername
  }

  return "unknown"
}

// Set up fingerprint event listeners
function setupFingerprintEventListeners() {
  const enrollBtn = document.getElementById("profile-enroll-fingerprint-btn")
  const deleteBtn = document.getElementById("profile-delete-fingerprint-btn")

  if (enrollBtn) {
    enrollBtn.addEventListener("click", () => {
      const username = getCurrentUsername()
      showFingerprintEnrollmentModal(username)
    })
  }

  if (deleteBtn) {
    deleteBtn.addEventListener("click", () => {
      if (confirm("Are you sure you want to remove your fingerprint data?")) {
        const username = getCurrentUsername()
        deleteFingerprintData(username)
      }
    })
  }
}

// Delete fingerprint data
function deleteFingerprintData(username) {
  fetch("/api/fingerprint/delete", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ username }),
  })
    .then((response) => response.json())
    .then((data) => {
      if (data.success) {
        showNotification("Fingerprint data removed successfully", "success")
        loadFingerprintStatus() // Reload status
      } else {
        showNotification(data.message || "Failed to remove fingerprint data", "error")
      }
    })
    .catch((error) => {
      console.error("Error:", error)
      showNotification("An error occurred", "error")
    })
}

// Show fingerprint enrollment modal (reuse from people.js)
function showFingerprintEnrollmentModal(username) {
  // Create modal if it doesn't exist
  let modal = document.getElementById("fingerprint-modal")
  if (!modal) {
    modal = document.createElement("div")
    modal.id = "fingerprint-modal"
    modal.className = "modal"

    const modalContent = document.createElement("div")
    modalContent.className = "modal-content"

    const modalHeader = document.createElement("div")
    modalHeader.className = "modal-header"

    const modalTitle = document.createElement("h3")
    modalTitle.id = "fingerprint-modal-title"
    modalTitle.textContent = "Fingerprint Enrollment"

    const closeBtn = document.createElement("span")
    closeBtn.className = "close"
    closeBtn.innerHTML = "&times;"
    closeBtn.addEventListener("click", () => {
      modal.classList.remove("active")
    })

    modalHeader.appendChild(modalTitle)
    modalHeader.appendChild(closeBtn)

    const modalBody = document.createElement("div")
    modalBody.className = "modal-body"
    modalBody.innerHTML = `
            <div class="fingerprint-enrollment">
                <div class="fingerprint-scanner">
                    <i class="fas fa-fingerprint"></i>
                    <div class="scanner-status" id="scanner-status">Ready</div>
                </div>
                <div class="enrollment-instructions">
                    <p>Please place your finger on the scanner.</p>
                    <p>You will need to scan your finger 3 times to complete enrollment.</p>
                    <div class="enrollment-progress">
                        <div class="progress-step" id="step-1">1</div>
                        <div class="progress-step" id="step-2">2</div>
                        <div class="progress-step" id="step-3">3</div>
                    </div>
                </div>
                <div class="enrollment-status" id="enrollment-status"></div>
            </div>
        `

    modalContent.appendChild(modalHeader)
    modalContent.appendChild(modalBody)
    modal.appendChild(modalContent)
    document.body.appendChild(modal)
  }

  // Reset enrollment state
  document.getElementById("scanner-status").textContent = "Ready"
  document.getElementById("enrollment-status").textContent = ""
  document.getElementById("step-1").className = "progress-step"
  document.getElementById("step-2").className = "progress-step"
  document.getElementById("step-3").className = "progress-step"

  const fingerprintScanner = document.querySelector(".fingerprint-scanner")
  fingerprintScanner.className = "fingerprint-scanner"

  // Show modal
  modal.classList.add("active")

  // Start enrollment process
  startProfileFingerprintEnrollment(username)
}

// Start fingerprint enrollment for profile
function startProfileFingerprintEnrollment(username) {
  const scannerStatus = document.getElementById("scanner-status")
  const enrollmentStatus = document.getElementById("enrollment-status")
  const fingerprintScanner = document.querySelector(".fingerprint-scanner")

  let currentStep = 1

  simulateEnrollmentStep()

  function simulateEnrollmentStep() {
    document.getElementById(`step-${currentStep}`).className = "progress-step active"
    scannerStatus.textContent = "Scanning..."
    fingerprintScanner.className = "fingerprint-scanner scanning"

    setTimeout(() => {
      document.getElementById(`step-${currentStep}`).className = "progress-step completed"

      if (currentStep < 3) {
        currentStep++
        enrollmentStatus.textContent = `Scan ${currentStep} of 3`
        scannerStatus.textContent = "Place finger again"
        fingerprintScanner.className = "fingerprint-scanner"
        setTimeout(simulateEnrollmentStep, 1500)
      } else {
        completeProfileEnrollment(username)
      }
    }, 2000)
  }

  function completeProfileEnrollment(username) {
    scannerStatus.textContent = "Processing..."

    fetch("/api/fingerprint/enroll", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ username }),
    })
      .then((response) => response.json())
      .then((data) => {
        if (data.success) {
          enrollmentStatus.textContent = "Enrollment successful!"
          scannerStatus.textContent = "Complete"
          fingerprintScanner.className = "fingerprint-scanner"

          showNotification("Fingerprint enrolled successfully!", "success")

          setTimeout(() => {
            document.getElementById("fingerprint-modal").classList.remove("active")
            loadFingerprintStatus() // Reload status
          }, 2000)
        } else {
          enrollmentStatus.textContent = data.message || "Enrollment failed"
          scannerStatus.textContent = "Error"
          fingerprintScanner.className = "fingerprint-scanner error"
          showNotification(data.message || "Fingerprint enrollment failed", "error")
        }
      })
      .catch((error) => {
        console.error("Error:", error)
        enrollmentStatus.textContent = "An error occurred"
        scannerStatus.textContent = "Error"
        fingerprintScanner.className = "fingerprint-scanner error"
        showNotification("An error occurred during enrollment", "error")
      })
  }
}

// Show notification
function showNotification(message, type = "info") {
  const notification = document.getElementById("notification")
  if (!notification) return

  notification.textContent = message
  notification.className = `notification ${type}`
  notification.style.display = "block"

  setTimeout(() => {
    notification.style.display = "none"
  }, 5000)
}

// Initialize profile functionality when page loads
document.addEventListener("DOMContentLoaded", () => {
  console.log("Profile page loaded, initializing...")

  // Load profile data
  loadProfile()

  // Set up form submission
  const profileForm = document.getElementById("profile-form")
  if (profileForm) {
    profileForm.addEventListener("submit", handleProfileSubmit)
  }

  // Set up fingerprint event listeners
  setupFingerprintEventListeners()

  console.log("Profile initialization complete")
})
