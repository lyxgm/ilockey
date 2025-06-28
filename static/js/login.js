document.addEventListener("DOMContentLoaded", () => {
  const loginBtn = document.getElementById("login-btn")
  const usernameInput = document.getElementById("username")
  const passwordInput = document.getElementById("password")
  const loginError = document.getElementById("login-error")
  const fingerprintLoginBtn = document.getElementById("fingerprint-login-btn")

  // Regular login with username and password
  loginBtn.addEventListener("click", () => {
    const username = usernameInput.value.trim()
    const password = passwordInput.value.trim()

    if (!username || !password) {
      loginError.textContent = "Please enter both username and password"
      return
    }

    fetch("/login", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ username, password }),
    })
      .then((response) => response.json())
      .then((data) => {
        if (data.success) {
          window.location.href = "/dashboard"
        } else {
          loginError.textContent = data.message || "Invalid username or password"
        }
      })
      .catch((error) => {
        loginError.textContent = "An error occurred. Please try again."
        console.error("Error:", error)
      })
  })

  // Fingerprint login
  if (fingerprintLoginBtn) {
    fingerprintLoginBtn.addEventListener("click", () => {
      // Show fingerprint authentication modal
      showFingerprintAuthModal()
    })
  }

  // Allow login with Enter key
  passwordInput.addEventListener("keypress", (e) => {
    if (e.key === "Enter") {
      loginBtn.click()
    }
  })
})

// Show fingerprint authentication modal
function showFingerprintAuthModal() {
  // Create modal if it doesn't exist
  let modal = document.getElementById("fingerprint-auth-modal")
  if (!modal) {
    modal = document.createElement("div")
    modal.id = "fingerprint-auth-modal"
    modal.className = "modal"

    const modalContent = document.createElement("div")
    modalContent.className = "modal-content fingerprint-modal-content"

    const closeBtn = document.createElement("span")
    closeBtn.className = "close"
    closeBtn.innerHTML = "&times;"
    closeBtn.addEventListener("click", () => {
      modal.classList.remove("active")
    })

    const modalBody = document.createElement("div")
    modalBody.className = "modal-body"
    modalBody.innerHTML = `
            <div class="fingerprint-auth">
                <h3>Fingerprint Authentication</h3>
                <div class="fingerprint-scanner">
                    <i class="fas fa-fingerprint"></i>
                    <div class="scanner-status" id="auth-scanner-status">Place your finger on the scanner</div>
                </div>
                <div class="auth-status" id="auth-status"></div>
                <div class="username-input" id="username-input-container" style="display: none;">
                    <p>Please enter your username to continue:</p>
                    <input type="text" id="fingerprint-username" placeholder="Username">
                    <button class="btn btn-primary" id="continue-auth-btn">Continue</button>
                </div>
            </div>
        `

    modalContent.appendChild(closeBtn)
    modalContent.appendChild(modalBody)
    modal.appendChild(modalContent)
    document.body.appendChild(modal)

    // Add styles for fingerprint authentication
    const style = document.createElement("style")
    style.textContent = `
            .fingerprint-modal-content {
                max-width: 400px;
            }
            
            .fingerprint-auth {
                text-align: center;
                padding: 20px;
            }
            
            .fingerprint-auth h3 {
                margin-bottom: 20px;
                color: #2c3e50;
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
                color: #3498db;
                animation: pulse 1.5s infinite;
            }
            
            .fingerprint-scanner.success i {
                color: #2ecc71;
            }
            
            .fingerprint-scanner.error i {
                color: #e74c3c;
            }
            
            .scanner-status {
                margin-top: 10px;
                font-size: 14px;
                color: #7f8c8d;
            }
            
            .auth-status {
                margin-top: 20px;
                font-weight: bold;
            }
            
            .username-input {
                margin-top: 20px;
            }
            
            .username-input input {
                width: 100%;
                padding: 10px;
                margin-bottom: 10px;
                border: 1px solid #ddd;
                border-radius: 4px;
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
        `
    document.head.appendChild(style)

    // Add event listener for continue button
    document.getElementById("continue-auth-btn").addEventListener("click", () => {
      const username = document.getElementById("fingerprint-username").value.trim()
      if (!username) {
        document.getElementById("auth-status").textContent = "Please enter your username"
        return
      }

      // Complete fingerprint authentication with username
      completeFingerprintAuth(username)
    })
  }

  // Reset authentication state
  document.getElementById("auth-scanner-status").textContent = "Place your finger on the scanner"
  document.getElementById("auth-status").textContent = ""
  document.getElementById("username-input-container").style.display = "none"

  const fingerprintScanner = document.querySelector(".fingerprint-scanner")
  fingerprintScanner.className = "fingerprint-scanner"

  // Show modal
  modal.classList.add("active")

  // Start authentication process
  startFingerprintAuth()
}

// Start fingerprint authentication process
function startFingerprintAuth() {
  const scannerStatus = document.getElementById("auth-scanner-status")
  const authStatus = document.getElementById("auth-status")
  const fingerprintScanner = document.querySelector(".fingerprint-scanner")

  // Update UI for scanning
  scannerStatus.textContent = "Scanning..."
  fingerprintScanner.className = "fingerprint-scanner scanning"

  // Simulate scanning delay
  setTimeout(() => {
    // Simulate fingerprint match
    fetch("/api/fingerprint/authenticate", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({}),
    })
      .then((response) => response.json())
      .then((data) => {
        if (data.success) {
          if (data.username) {
            // Authentication successful with known username
            authSuccess(data.username)
          } else {
            // Fingerprint recognized but need username
            fingerprintScanner.className = "fingerprint-scanner success"
            scannerStatus.textContent = "Fingerprint recognized"
            authStatus.textContent = "Fingerprint matched"

            // Show username input
            document.getElementById("username-input-container").style.display = "block"
          }
        } else {
          // Authentication failed
          authFailed(data.message || "Authentication failed")
        }
      })
      .catch((error) => {
        console.error("Error:", error)
        authFailed("An error occurred")
      })
  }, 2000)
}

// Complete fingerprint authentication with username
function completeFingerprintAuth(username) {
  const authStatus = document.getElementById("auth-status")

  fetch("/api/fingerprint/verify", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ username }),
  })
    .then((response) => response.json())
    .then((data) => {
      if (data.success) {
        // Authentication successful
        authSuccess(username)
      } else {
        // Authentication failed
        authFailed(data.message || "Authentication failed")
      }
    })
    .catch((error) => {
      console.error("Error:", error)
      authFailed("An error occurred")
    })
}

// Handle successful authentication
function authSuccess(username) {
  const scannerStatus = document.getElementById("auth-scanner-status")
  const authStatus = document.getElementById("auth-status")
  const fingerprintScanner = document.querySelector(".fingerprint-scanner")

  fingerprintScanner.className = "fingerprint-scanner success"
  scannerStatus.textContent = "Authentication successful"
  authStatus.textContent = `Welcome, ${username}! Redirecting...`

  // Redirect to dashboard after successful authentication
  setTimeout(() => {
    window.location.href = "/dashboard"
  }, 1500)
}

// Handle failed authentication
function authFailed(message) {
  const scannerStatus = document.getElementById("auth-scanner-status")
  const authStatus = document.getElementById("auth-status")
  const fingerprintScanner = document.querySelector(".fingerprint-scanner")

  fingerprintScanner.className = "fingerprint-scanner error"
  scannerStatus.textContent = "Authentication failed"
  authStatus.textContent = message

  // Reset after a delay
  setTimeout(() => {
    fingerprintScanner.className = "fingerprint-scanner"
    scannerStatus.textContent = "Place your finger on the scanner"
    // Don't clear the error message
  }, 3000)
}
