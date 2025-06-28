document.addEventListener("DOMContentLoaded", () => {
  // Load users data
  loadUsersData()

  // Set up event listeners
  setupEventListeners()
})

// Load users data
function loadUsersData() {
  const usersTableBody = document.getElementById("users-table-body")
  const pendingUsersTableBody = document.getElementById("pending-users-table-body")

  if (usersTableBody && pendingUsersTableBody) {
    fetch("/api/users")
      .then((response) => response.json())
      .then((data) => {
        const users = data.users || {}
        usersTableBody.innerHTML = ""
        pendingUsersTableBody.innerHTML = ""

        if (Object.keys(users).length === 0) {
          usersTableBody.innerHTML = '<tr><td colspan="6">No users found</td></tr>'
          pendingUsersTableBody.innerHTML = '<tr><td colspan="4">No pending approvals</td></tr>'
        } else {
          let approvedCount = 0
          let pendingCount = 0

          for (const [username, user] of Object.entries(users)) {
            const isApproved = user.approved !== false
            const accessType = user.access_type || "full"
            const accessUntil = user.access_until ? ` (until ${user.access_until})` : ""
            const hasFingerprint = user.fingerprint_enrolled === true

            if (isApproved) {
              approvedCount++
              const row = document.createElement("tr")
              row.innerHTML = `
                <td>${username}</td>
                <td>${user.email || ""}</td>
                <td>${user.role}</td>
                <td><span class="approval-badge approved">Approved</span></td>
                <td>
                  <span class="access-badge ${accessType}">
                    ${accessType}${accessType === "limited" ? accessUntil : ""}
                  </span>
                </td>
                <td>
                  <button class="btn btn-sm edit-user" data-username="${username}">
                    <i class="fas fa-edit"></i>
                  </button>
                  <button class="btn btn-sm btn-danger delete-user" data-username="${username}">
                    <i class="fas fa-trash"></i>
                  </button>
                  ${
                    hasFingerprint
                      ? '<span class="fingerprint-badge" title="Fingerprint enrolled"><i class="fas fa-fingerprint"></i></span>'
                      : ""
                  }
                </td>
              `
              usersTableBody.appendChild(row)
            } else {
              pendingCount++
              const row = document.createElement("tr")
              row.innerHTML = `
                <td>${username}</td>
                <td>${user.email || ""}</td>
                <td>${user.role}</td>
                <td>
                  <button class="btn btn-sm btn-primary approve-user" data-username="${username}">
                    <i class="fas fa-check"></i> Approve
                  </button>
                  <button class="btn btn-sm btn-danger delete-user" data-username="${username}">
                    <i class="fas fa-trash"></i>
                  </button>
                </td>
              `
              pendingUsersTableBody.appendChild(row)
            }
          }

          if (approvedCount === 0) {
            usersTableBody.innerHTML = '<tr><td colspan="6">No approved users found</td></tr>'
          }

          if (pendingCount === 0) {
            pendingUsersTableBody.innerHTML = '<tr><td colspan="4">No pending approvals</td></tr>'
          }

          // Add event listeners to edit and delete buttons
          document.querySelectorAll(".edit-user").forEach((btn) => {
            btn.addEventListener("click", function () {
              const username = this.getAttribute("data-username")
              editUser(username, users[username])
            })
          })

          document.querySelectorAll(".delete-user").forEach((btn) => {
            btn.addEventListener("click", function () {
              const username = this.getAttribute("data-username")
              if (confirm(`Are you sure you want to delete user ${username}?`)) {
                deleteUser(username)
              }
            })
          })

          // Add event listeners to approve buttons
          document.querySelectorAll(".approve-user").forEach((btn) => {
            btn.addEventListener("click", function () {
              const username = this.getAttribute("data-username")
              approveUser(username)
            })
          })
        }
      })
      .catch((error) => console.error("Error loading users data:", error))
  }
}

// Set up event listeners
function setupEventListeners() {
  // User management
  const addUserBtn = document.getElementById("add-user-btn")
  const closeUserModal = document.getElementById("close-user-modal")
  const userForm = document.getElementById("user-form")
  const userModal = document.getElementById("user-modal")

  if (addUserBtn) {
    addUserBtn.addEventListener("click", () => {
      document.getElementById("user-form-mode").value = "add"
      document.getElementById("user-modal-title").textContent = "Add User"
      document.getElementById("user-username").disabled = false
      document.getElementById("user-username").value = ""
      document.getElementById("user-email").value = ""
      document.getElementById("user-role").value = "guest"

      // Reset checkboxes
      document.getElementById("perm-unlock").checked = true
      document.getElementById("perm-view-logs").checked = false
      document.getElementById("perm-manage-users").checked = false
      document.getElementById("perm-change-settings").checked = false

      // Hide fingerprint section for new users
      const fingerprintSection = document.getElementById("fingerprint-section")
      if (fingerprintSection) {
        fingerprintSection.style.display = "none"
      }

      userModal.classList.add("active")
    })
  }

  if (closeUserModal) {
    closeUserModal.addEventListener("click", () => {
      userModal.classList.remove("active")
    })
  }

  const userAccessType = document.getElementById("user-access-type")
  if (userAccessType) {
    userAccessType.addEventListener("change", function () {
      const accessUntilGroup = document.getElementById("access-until-group")
      if (this.value === "limited") {
        accessUntilGroup.style.display = "block"
      } else {
        accessUntilGroup.style.display = "none"
      }
    })
  }

  // Update the userForm event listener to include the new fields
  if (userForm) {
    userForm.addEventListener("submit", (e) => {
      e.preventDefault()

      const mode = document.getElementById("user-form-mode").value
      const username = document.getElementById("user-username").value
      const email = document.getElementById("user-email").value
      const role = document.getElementById("user-role").value
      const accessType = document.getElementById("user-access-type").value
      const accessUntil = accessType === "limited" ? document.getElementById("user-access-until").value : null

      // Get permissions
      const permissions = []
      if (document.getElementById("perm-unlock").checked) permissions.push("unlock")
      if (document.getElementById("perm-view-logs").checked) permissions.push("view_logs")
      if (document.getElementById("perm-manage-users").checked) permissions.push("manage_users")
      if (document.getElementById("perm-change-settings").checked) permissions.push("change_settings")

      const userData = {
        username,
        email,
        role,
        permissions,
        access_type: accessType,
        access_until: accessUntil,
        approved: false, // Pre-registered users are not approved until they sign up
        pre_approved: true, // Mark as pre-approved for automatic approval after signup
      }

      const endpoint = mode === "add" ? "/api/users/add" : "/api/users/edit"

      fetch(endpoint, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(userData),
      })
        .then((response) => response.json())
        .then((data) => {
          if (data.success) {
            if (mode === "add") {
              showPopupNotification(
                `User ${username} pre-registered successfully. They can now sign up with this username and email.`,
                "success",
              )
            } else {
              showPopupNotification(`User ${username} updated successfully`, "success")
            }
            userModal.classList.remove("active")
            loadUsersData()
          } else {
            showPopupNotification(data.message || "Operation failed", "error")
          }
        })
        .catch((error) => {
          console.error("Error:", error)
          showPopupNotification("An error occurred", "error")
        })
    })
  }

  // Fingerprint enrollment
  const enrollFingerprintBtn = document.getElementById("enroll-fingerprint-btn")
  if (enrollFingerprintBtn) {
    enrollFingerprintBtn.addEventListener("click", () => {
      const username = document.getElementById("user-username").value

      // Show fingerprint enrollment modal
      showFingerprintEnrollmentModal(username)
    })
  }

  // Delete fingerprint
  const deleteFingerprintBtn = document.getElementById("delete-fingerprint-btn")
  if (deleteFingerprintBtn) {
    deleteFingerprintBtn.addEventListener("click", () => {
      const username = document.getElementById("user-username").value

      if (confirm("Are you sure you want to delete this user's fingerprint data?")) {
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
              showPopupNotification("Fingerprint data deleted successfully", "success")

              // Update UI to show fingerprint is not enrolled
              document.getElementById("fingerprint-status").textContent = "Not enrolled"
              document.getElementById("fingerprint-status").className = "status-text not-enrolled"

              // Hide delete button, show enroll button
              document.getElementById("delete-fingerprint-btn").style.display = "none"
              document.getElementById("enroll-fingerprint-btn").style.display = "inline-block"
            } else {
              showPopupNotification(data.message || "Failed to delete fingerprint data", "error")
            }
          })
          .catch((error) => {
            console.error("Error:", error)
            showPopupNotification("An error occurred", "error")
          })
      }
    })
  }
}

// Edit user - improved version with fingerprint status
function editUser(username, userData) {
  if (!userData) {
    showPopupNotification("User data not found", "error")
    return
  }

  const modal = document.getElementById("user-modal")
  if (!modal) {
    showPopupNotification("User modal not found", "error")
    return
  }

  // Set form mode and title
  const formMode = document.getElementById("user-form-mode")
  const modalTitle = document.getElementById("user-modal-title")
  const usernameField = document.getElementById("user-username")

  if (formMode) formMode.value = "edit"
  if (modalTitle) modalTitle.textContent = "Edit User"
  if (usernameField) {
    usernameField.value = username
    usernameField.disabled = true
  }

  // Populate form fields safely
  const fields = {
    "user-email": userData.email || "",
    "user-role": userData.role || "guest",
    "user-access-type": userData.access_type || "full",
    "user-access-until": userData.access_until || "",
  }

  Object.entries(fields).forEach(([id, value]) => {
    const element = document.getElementById(id)
    if (element) element.value = value
  })

  // Handle access until date visibility
  const accessUntilGroup = document.getElementById("access-until-group")
  if (accessUntilGroup) {
    accessUntilGroup.style.display = userData.access_type === "limited" ? "block" : "none"
  }

  // Set permissions checkboxes
  const permissions = userData.permissions || []
  const permissionCheckboxes = {
    "perm-unlock": permissions.includes("unlock"),
    "perm-view-logs": permissions.includes("view_logs"),
    "perm-manage-users": permissions.includes("manage_users"),
    "perm-change-settings": permissions.includes("change_settings"),
  }

  Object.entries(permissionCheckboxes).forEach(([id, checked]) => {
    const checkbox = document.getElementById(id)
    if (checkbox) checkbox.checked = checked
  })

  // Handle fingerprint section
  const fingerprintSection = document.getElementById("fingerprint-section")
  if (fingerprintSection) {
    fingerprintSection.style.display = "block"

    // Check current fingerprint status from server
    checkFingerprintStatus(username).then((enrolled) => {
      updateFingerprintStatus(enrolled)
    })
  }

  // Show modal
  modal.classList.add("active")
}

// Update fingerprint status display
function updateFingerprintStatus(isEnrolled) {
  const fingerprintStatus = document.getElementById("fingerprint-status")
  const enrollBtn = document.getElementById("enroll-fingerprint-btn")
  const deleteBtn = document.getElementById("delete-fingerprint-btn")

  if (fingerprintStatus) {
    fingerprintStatus.textContent = isEnrolled ? "Enrolled" : "Not enrolled"
    fingerprintStatus.className = `status-text ${isEnrolled ? "enrolled" : "not-enrolled"}`
  }

  if (enrollBtn) {
    enrollBtn.style.display = isEnrolled ? "none" : "inline-block"
  }

  if (deleteBtn) {
    deleteBtn.style.display = isEnrolled ? "inline-block" : "none"
  }
}

// Delete user
function deleteUser(username) {
  fetch("/api/users/delete", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ username }),
  })
    .then((response) => response.json())
    .then((data) => {
      if (data.success) {
        showPopupNotification("User deleted successfully", "success")
        loadUsersData()
      } else {
        showPopupNotification(data.message || "Failed to delete user", "error")
      }
    })
    .catch((error) => {
      console.error("Error deleting user:", error)
      showPopupNotification("An error occurred", "error")
    })
}

// Approve user
function approveUser(username) {
  fetch("/api/users/approve", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ username }),
  })
    .then((response) => response.json())
    .then((data) => {
      if (data.success) {
        showPopupNotification("User approved successfully", "success")
        loadUsersData()
      } else {
        showPopupNotification(data.message || "Failed to approve user", "error")
      }
    })
    .catch((error) => {
      console.error("Error approving user:", error)
      showPopupNotification("An error occurred", "error")
    })
}

// Start fingerprint enrollment process
function startFingerprintEnrollment(username) {
  const scannerStatus = document.getElementById("scanner-status")
  const enrollmentStatus = document.getElementById("enrollment-status")
  const fingerprintScanner = document.querySelector(".fingerprint-scanner")

  let currentStep = 1

  // Simulate enrollment process
  simulateEnrollmentStep()

  function simulateEnrollmentStep() {
    // Update UI for current step
    document.getElementById(`step-${currentStep}`).className = "progress-step active"
    scannerStatus.textContent = "Scanning..."
    fingerprintScanner.className = "fingerprint-scanner scanning"

    // Simulate scanning delay
    setTimeout(() => {
      // Mark step as completed
      document.getElementById(`step-${currentStep}`).className = "progress-step completed"

      if (currentStep < 3) {
        // Move to next step
        currentStep++
        enrollmentStatus.textContent = `Scan ${currentStep} of 3`
        scannerStatus.textContent = "Place finger again"
        fingerprintScanner.className = "fingerprint-scanner"

        // Wait before starting next scan
        setTimeout(simulateEnrollmentStep, 1500)
      } else {
        // Enrollment complete
        completeEnrollment(username)
      }
    }, 2000)
  }

  function completeEnrollment(username) {
    scannerStatus.textContent = "Processing..."

    // Send enrollment data to server
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

          // Update UI to show fingerprint is enrolled
          updateFingerprintStatus(true)

          // Show success notification
          showPopupNotification(`Fingerprint enrolled successfully for ${username}`, "success")

          // Close modal after a delay
          setTimeout(() => {
            document.getElementById("fingerprint-modal").classList.remove("active")
          }, 2000)

          // Refresh user list to show fingerprint badge
          loadUsersData()
        } else {
          enrollmentStatus.textContent = data.message || "Enrollment failed"
          scannerStatus.textContent = "Error"
          fingerprintScanner.className = "fingerprint-scanner error"

          // Show error notification
          showPopupNotification(data.message || "Fingerprint enrollment failed", "error")
        }
      })
      .catch((error) => {
        console.error("Error:", error)
        enrollmentStatus.textContent = "An error occurred"
        scannerStatus.textContent = "Error"
        fingerprintScanner.className = "fingerprint-scanner error"

        showPopupNotification("An error occurred during enrollment", "error")
      })
  }
}

// Check fingerprint status for a user
function checkFingerprintStatus(username) {
  return fetch(`/api/fingerprint/status/${username}`)
    .then((response) => response.json())
    .then((data) => {
      if (data.success) {
        return data.enrolled
      }
      return false
    })
    .catch((error) => {
      console.error("Error checking fingerprint status:", error)
      return false
    })
}

// Show fingerprint enrollment modal
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

    // Add styles for fingerprint enrollment
    const style = document.createElement("style")
    style.textContent = `
      .fingerprint-enrollment {
        text-align: center;
        padding: 20px;
      }
      
      .fingerprint-scanner {
        margin: 20px auto;
        width: 120px;
        height: 120px;
        border-radius: 50%;
        background-color: #f5f5f5;
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        position: relative;
      }
      
      .fingerprint-scanner i {
        font-size: 60px;
        color: #3498db;
      }
      
      .fingerprint-scanner.scanning i {
        color: #2ecc71;
        animation: pulse 1.5s infinite;
      }
      
      .fingerprint-scanner.error i {
        color: #e74c3c;
      }
      
      .scanner-status {
        margin-top: 10px;
        font-size: 14px;
        color: #7f8c8d;
      }
      
      .enrollment-instructions {
        margin: 20px 0;
      }
      
      .enrollment-progress {
        display: flex;
        justify-content: center;
        margin-top: 20px;
      }
      
      .progress-step {
        width: 30px;
        height: 30px;
        border-radius: 50%;
        background-color: #ecf0f1;
        color: #7f8c8d;
        display: flex;
        justify-content: center;
        align-items: center;
        margin: 0 10px;
        font-weight: bold;
      }
      
      .progress-step.active {
        background-color: #3498db;
        color: white;
      }
      
      .progress-step.completed {
        background-color: #2ecc71;
        color: white;
      }
      
      .enrollment-status {
        margin-top: 20px;
        font-weight: bold;
      }
      
      @keyframes pulse {
        0% {
          transform: scale(1);
        }
        50% {
          transform: scale(1.1);
        }
        100% {
          transform: scale(1);
        }
      }
      
      .status-text.enrolled {
        color: #2ecc71;
        font-weight: bold;
      }
      
      .status-text.not-enrolled {
        color: #e74c3c;
      }
      
      .fingerprint-badge {
        margin-left: 10px;
        color: #3498db;
      }
    `
    document.head.appendChild(style)
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
  startFingerprintEnrollment(username)
}

// Show popup notification
function showPopupNotification(message, type = "info") {
  const notification = document.createElement("div")
  notification.className = `popup-notification ${type}`
  notification.innerHTML = `
    <div class="notification-content">
      <i class="fas ${getNotificationIcon(type)}"></i>
      <span>${message}</span>
    </div>
  `

  document.body.appendChild(notification)

  // Show notification
  setTimeout(() => {
    notification.classList.add("show")
  }, 10)

  // Hide and remove notification after 3 seconds
  setTimeout(() => {
    notification.classList.remove("show")
    setTimeout(() => {
      document.body.removeChild(notification)
    }, 300)
  }, 3000)
}

// Get notification icon based on type
function getNotificationIcon(type) {
  switch (type) {
    case "success":
      return "fa-check-circle"
    case "error":
      return "fa-exclamation-circle"
    case "warning":
      return "fa-exclamation-triangle"
    case "info":
    default:
      return "fa-info-circle"
  }
}
