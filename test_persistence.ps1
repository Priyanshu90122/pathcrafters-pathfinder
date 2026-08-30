# Test script for database persistence
$API = "http://127.0.0.1:8000"
$LEARNER_ID = "test-learner-" + [guid]::NewGuid().ToString().Substring(0, 8)
$checkmark = "[PASS]"
$cross = "[FAIL]"

Write-Host "Testing PathPilot Database Persistence"
Write-Host "========================================"
Write-Host "Learner ID: $LEARNER_ID`n"

# Test 1: Create a profile
Write-Host "TEST 1: Creating initial profile..."
$profile = @{
    name = "Alex Chen"
    goal = "I want to become an AI Engineer, have 6 hours/week, know Python, and I am weak in deep learning"
    experience = "Intermediate"
    interests = @()
    completed_courses = @()
    weekly_hours = 6
    preferences = @()
    skills = @{
        Python = 80
        Statistics = 50
        "Machine Learning" = 40
        "Deep Learning" = 20
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
    $result = Invoke-WebRequest -Uri "$API/api/profile" -Method POST `
        -Headers @{"Content-Type"="application/json"} -Body $profileReq -UseBasicParsing
    $data = $result.Content | ConvertFrom-Json
    Write-Host "✓ Profile created successfully"
    Write-Host "  Role: $($data.role)"
    Write-Host "  Gaps: $($data.gaps.Count) skill gaps found"
    Write-Host "  Roadmap: $($data.roadmap.Count) items in path`n"
} catch {
    Write-Host "✗ Failed to create profile: $_"
    exit 1
}

# Test 2: Retrieve the profile (should be in database now)
Write-Host "TEST 2: Retrieving saved profile from database..."
try {
    $result = Invoke-WebRequest -Uri "$API/api/profile/$LEARNER_ID" -Method GET `
        -Headers @{"Content-Type"="application/json"} -UseBasicParsing
    $data = $result.Content | ConvertFrom-Json
    Write-Host "✓ Profile retrieved successfully from database"
    Write-Host "  Name: $($data.profile.name)"
    Write-Host "  Goal: $($data.profile.goal)"
    Write-Host "  Weekly Hours: $($data.profile.weekly_hours)`n"
} catch {
    Write-Host "✗ Failed to retrieve profile: $_"
    exit 1
}

# Test 3: Chat with AI Coach (if LLM available)
Write-Host "TEST 3: Testing chat endpoint..."
$chatReq = @{
    learner_id = $LEARNER_ID
    message = "I only have 8 weeks. Prioritize deployment and MLOps and deprioritize NLP."
    history = @()
} | ConvertTo-Json

try {
    $result = Invoke-WebRequest -Uri "$API/api/chat" -Method POST `
        -Headers @{"Content-Type"="application/json"} -Body $chatReq -UseBasicParsing
    $data = $result.Content | ConvertFrom-Json
    Write-Host "✓ Chat endpoint responded"
    Write-Host "  Source: $($data.source)"
    Write-Host "  Roadmap items: $($data.roadmap.Count)`n"
} catch {
    Write-Host "✗ Failed chat: $_"
}

# Test 4: Run assessment
Write-Host "TEST 4: Testing assessment endpoint..."
$assessReq = @{
    learner_id = $LEARNER_ID
    results = @{
        Python = 85
        Statistics = 60
        "Machine Learning" = 55
        "Deep Learning" = 35
        NLP = 20
        Deployment = 25
        MLOps = 15
        "SQL" = 50
    }
} | ConvertTo-Json

try {
    $result = Invoke-WebRequest -Uri "$API/api/assess" -Method POST `
        -Headers @{"Content-Type"="application/json"} -Body $assessReq -UseBasicParsing
    $data = $result.Content | ConvertFrom-Json
    Write-Host "✓ Assessment endpoint responded"
    Write-Host "  Updated profile saved to database"
    Write-Host "  New roadmap items: $($data.roadmap.Count)`n"
} catch {
    Write-Host "✗ Failed assessment: $_"
}

# Test 5: Verify profile persisted after assessment
Write-Host "TEST 5: Verifying profile persisted after assessment..."
try {
    $result = Invoke-WebRequest -Uri "$API/api/profile/$LEARNER_ID" -Method GET `
        -Headers @{"Content-Type"="application/json"} -UseBasicParsing
    $data = $result.Content | ConvertFrom-Json
    $pythonScore = $data.profile.skills.Python
    Write-Host "✓ Profile retrieved again from database"
    Write-Host "  Python skill score (should be 85): $pythonScore`n"
    
    if ($pythonScore -eq 85) {
        Write-Host "✓✓ SUCCESS: Assessment changes were persisted to database!`n"
    } else {
        Write-Host "✗ ERROR: Skills not persisted correctly`n"
    }
} catch {
    Write-Host "✗ Failed to verify persistence: $_"
}

Write-Host "========================================"
Write-Host "All database persistence tests completed!"
