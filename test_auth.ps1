param()
# Test authentication and profile persistence with new account system
$API = "http://127.0.0.1:8000"
$TEST_EMAIL = "test-" + [guid]::NewGuid().ToString().Substring(0, 8) + "@example.com"
$TEST_PASSWORD = "TestPassword123"
$token = $null

Write-Host "Testing PathPilot Authentication System"
Write-Host "========================================"
Write-Host "Test Email: $TEST_EMAIL`n"

# Test 1: Sign up
Write-Host "TEST 1: Signing up new user..."
try {
    $result = Invoke-WebRequest -Uri "$API/api/signup" -Method POST -Headers @{"Content-Type"="application/json"} `
        -Body (@{email=$TEST_EMAIL; password=$TEST_PASSWORD} | ConvertTo-Json) -UseBasicParsing
    $data = $result.Content | ConvertFrom-Json
    $token = $data.token
    Write-Host "[PASS] User signed up successfully"
    Write-Host "       Token: $($token.Substring(0, 20))..."
} catch {
    Write-Host "[FAIL] Signup failed: $_"
    exit 1
}

# Test 2: Create profile with token
Write-Host "`nTEST 2: Creating profile with auth token..."
$profile = @{
    name = "Alice Johnson"
    goal = "Data Scientist"
    experience = "Intermediate"
    weekly_hours = 8
    interests = @()
    completed_courses = @()
    preferences = @()
    skills = @{Python = 75; Statistics = 65}
}
$profileReq = @{profile = $profile} | ConvertTo-Json

try {
    $result = Invoke-WebRequest -Uri "$API/api/profile" -Method POST `
        -Headers @{"Authorization"="Bearer $token"; "Content-Type"="application/json"} `
        -Body $profileReq -UseBasicParsing
    $data = $result.Content | ConvertFrom-Json
    Write-Host "[PASS] Profile created with token auth"
    Write-Host "       Role: $($data.role)"
    Write-Host "       Roadmap items: $($data.roadmap.Count)"
} catch {
    Write-Host "[FAIL] Profile creation failed: $_"
    exit 1
}

# Test 3: Logout
Write-Host "`nTEST 3: Logging out..."
try {
    $result = Invoke-WebRequest -Uri "$API/api/logout" -Method POST `
        -Headers @{"Content-Type"="application/json"} `
        -Body (@{token=$token} | ConvertTo-Json) -UseBasicParsing
    Write-Host "[PASS] Logout successful"
} catch {
    Write-Host "[FAIL] Logout failed: $_"
}

# Test 4: Login again
Write-Host "`nTEST 4: Logging back in with same credentials..."
try {
    $result = Invoke-WebRequest -Uri "$API/api/login" -Method POST -Headers @{"Content-Type"="application/json"} `
        -Body (@{email=$TEST_EMAIL; password=$TEST_PASSWORD} | ConvertTo-Json) -UseBasicParsing
    $data = $result.Content | ConvertFrom-Json
    $newToken = $data.token
    Write-Host "[PASS] Login successful"
    Write-Host "       New token: $($newToken.Substring(0, 20))..."
} catch {
    Write-Host "[FAIL] Login failed: $_"
    exit 1
}

# Test 5: Verify profile persisted
Write-Host "`nTEST 5: Verifying profile persisted after logout/login..."
try {
    $result = Invoke-WebRequest -Uri "$API/api/profile" -Method GET `
        -Headers @{"Authorization"="Bearer $newToken"; "Content-Type"="application/json"} `
        -UseBasicParsing
    $data = $result.Content | ConvertFrom-Json
    $name = $data.profile.name
    $pythonScore = $data.profile.skills.Python
    Write-Host "[PASS] Profile retrieved after login"
    Write-Host "       Name: $name"
    Write-Host "       Python score: $pythonScore"
    
    if ($name -eq "Alice Johnson" -and $pythonScore -eq 75) {
        Write-Host "[PASS] Profile data matches! Persistence confirmed!`n"
    } else {
        Write-Host "[FAIL] Profile data doesn't match`n"
    }
} catch {
    Write-Host "[FAIL] Profile retrieval failed: $_"
}

# Test 6: Logout with invalid token should fail gracefully
Write-Host "TEST 6: Testing profile access with wrong token..."
try {
    $result = Invoke-WebRequest -Uri "$API/api/profile" -Method GET `
        -Headers @{"Authorization"="Bearer invalid-token"; "Content-Type"="application/json"} `
        -UseBasicParsing -ErrorAction Stop
    Write-Host "[FAIL] Should have rejected invalid token"
} catch {
    if ($_.Exception.Response.StatusCode.Value__ -eq 401) {
        Write-Host "[PASS] Invalid token correctly rejected with 401"
    } else {
        Write-Host "[FAIL] Wrong error code: $($_.Exception.Response.StatusCode.Value__)"
    }
}

# Test 7: Duplicate email should fail
Write-Host "`nTEST 7: Testing duplicate signup..."
try {
    $result = Invoke-WebRequest -Uri "$API/api/signup" -Method POST -Headers @{"Content-Type"="application/json"} `
        -Body (@{email=$TEST_EMAIL; password=$TEST_PASSWORD} | ConvertTo-Json) -UseBasicParsing -ErrorAction Stop
    Write-Host "[FAIL] Should have rejected duplicate email"
} catch {
    if ($_.Exception.Response.StatusCode.Value__ -eq 400) {
        $errorData = $_.Exception.Response.Content | ConvertFrom-Json
        Write-Host "[PASS] Duplicate email correctly rejected"
        Write-Host "       Error: $($errorData.detail)"
    }
}

Write-Host "`n========================================"
Write-Host "Authentication tests completed!"
