param()
# Test script for database persistence
$API = "http://127.0.0.1:8000"
$LEARNER_ID = "test-learner-" + [guid]::NewGuid().ToString().Substring(0, 8)

Write-Host "Testing PathPilot Database Persistence"
Write-Host "========================================"
Write-Host "Learner ID: $LEARNER_ID`n"

# Test 1: Create a profile
Write-Host "TEST 1: Creating initial profile..."
$profile = @{
    name = "Alex Chen"
    goal = "AI Engineer"
    experience = "Intermediate"
    interests = @()
    completed_courses = @()
    weekly_hours = 6
    preferences = @()
    skills = @{
        Python = 80
        Statistics = 50
        'Machine Learning' = 40
        'Deep Learning' = 20
        NLP = 10
        Deployment = 15
        MLOps = 5
    }
}

$profileReq = @{
    learner_id = $LEARNER_ID
    profile = $profile
} | ConvertTo-Json

try {
    $result = Invoke-WebRequest -Uri "$API/api/profile" -Method POST -Headers @{"Content-Type"="application/json"} -Body $profileReq -UseBasicParsing
    $data = $result.Content | ConvertFrom-Json
    Write-Host "[PASS] Profile created successfully"
    Write-Host "       Role: $($data.role)"
    Write-Host "       Gaps: $($data.gaps.Count) skill gaps"
    Write-Host "       Roadmap: $($data.roadmap.Count) items`n"
} catch {
    Write-Host "[FAIL] Failed to create profile"
    Write-Host $_.Exception.Message
    exit 1
}

# Test 2: Retrieve the profile
Write-Host "TEST 2: Retrieving saved profile from database..."
try {
    $result = Invoke-WebRequest -Uri "$API/api/profile/$LEARNER_ID" -Method GET -Headers @{"Content-Type"="application/json"} -UseBasicParsing
    $data = $result.Content | ConvertFrom-Json
    Write-Host "[PASS] Profile retrieved from database"
    Write-Host "       Name: $($data.profile.name)"
    Write-Host "       Weekly Hours: $($data.profile.weekly_hours)`n"
} catch {
    Write-Host "[FAIL] Failed to retrieve profile"
    Write-Host $_.Exception.Message
    exit 1
}

# Test 3: Chat endpoint
Write-Host "TEST 3: Testing chat endpoint..."
$chatReq = @{
    learner_id = $LEARNER_ID
    message = "I only have 8 weeks. Prioritize deployment."
    history = @()
} | ConvertTo-Json

try {
    $result = Invoke-WebRequest -Uri "$API/api/chat" -Method POST -Headers @{"Content-Type"="application/json"} -Body $chatReq -UseBasicParsing
    $data = $result.Content | ConvertFrom-Json
    Write-Host "[PASS] Chat endpoint responded"
    Write-Host "       Source: $($data.source)`n"
} catch {
    Write-Host "[FAIL] Chat endpoint error"
    Write-Host $_.Exception.Message
}

# Test 4: Assessment
Write-Host "TEST 4: Testing assessment endpoint..."
$assessReq = @{
    learner_id = $LEARNER_ID
    results = @{
        Python = 85
        Statistics = 60
        'Machine Learning' = 55
        'Deep Learning' = 35
        NLP = 20
        Deployment = 25
        MLOps = 15
        SQL = 50
    }
} | ConvertTo-Json

try {
    $result = Invoke-WebRequest -Uri "$API/api/assess" -Method POST -Headers @{"Content-Type"="application/json"} -Body $assessReq -UseBasicParsing
    $data = $result.Content | ConvertFrom-Json
    Write-Host "[PASS] Assessment endpoint responded`n"
} catch {
    Write-Host "[FAIL] Assessment endpoint error"
    Write-Host $_.Exception.Message
}

# Test 5: Verify persistence
Write-Host "TEST 5: Verifying persistence after assessment..."
try {
    $result = Invoke-WebRequest -Uri "$API/api/profile/$LEARNER_ID" -Method GET -Headers @{"Content-Type"="application/json"} -UseBasicParsing
    $data = $result.Content | ConvertFrom-Json
    $pythonScore = $data.profile.skills.Python
    Write-Host "[PASS] Profile retrieved from database"
    Write-Host "       Python score (should be 85): $pythonScore"
    
    if ($pythonScore -eq 85) {
        Write-Host "[PASS] Assessment changes persisted to database!`n"
    } else {
        Write-Host "[FAIL] Skills not persisted correctly`n"
    }
} catch {
    Write-Host "[FAIL] Failed to verify persistence"
    Write-Host $_.Exception.Message
}

Write-Host "========================================"
Write-Host "Database persistence tests completed!"
