param()
# Verify the database has the test data from previous run
$API = "http://127.0.0.1:8000"
$LEARNER_ID = "test-learner-1038ba95"  # ID from previous test

Write-Host "Verifying data in database before restart..."
Write-Host ""

try {
    $result = Invoke-WebRequest -Uri "$API/api/profile/$LEARNER_ID" -Method GET -Headers @{"Content-Type"="application/json"} -UseBasicParsing
    $data = $result.Content | ConvertFrom-Json
    
    Write-Host "Profile found in database:"
    Write-Host "  Name: $($data.profile.name)"
    Write-Host "  Goal: $($data.profile.goal)"
    Write-Host "  Python score: $($data.profile.skills.Python)"
    Write-Host ""
    Write-Host "Ready for backend restart test..."
} catch {
    Write-Host "Failed to retrieve profile: $_"
    exit 1
}
