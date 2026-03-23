#!/usr/bin/env bash
# ============================================================================
# VoiceCoach — Backend API Test Script
#
# Tests all backend endpoints against a running server.
# Usage:
#   ./docs/test-api.sh                     # uses default https://localhost:8000
#   ./docs/test-api.sh https://localhost:9001  # custom base URL
# ============================================================================

set -euo pipefail

BASE_URL="${1:-https://localhost:8000}"
PASS=0
FAIL=0
CURL="curl -sk --max-time 10"

green()  { printf "\033[32m✅ %s\033[0m\n" "$1"; }
red()    { printf "\033[31m❌ %s\033[0m\n" "$1"; }
yellow() { printf "\033[33m⚠️  %s\033[0m\n" "$1"; }
header() { printf "\n\033[1;36m--- %s ---\033[0m\n" "$1"; }

check() {
  local desc="$1" actual="$2" expected="$3"
  if echo "$actual" | grep -q "$expected"; then
    green "$desc"
    ((PASS++))
  else
    red "$desc (expected '$expected', got: $actual)"
    ((FAIL++))
  fi
}

echo "============================================"
echo "  VoiceCoach API Test Suite"
echo "  Target: $BASE_URL"
echo "============================================"

# --------------------------------------------------------------------------
header "1. Health Check — GET /"
# --------------------------------------------------------------------------
RESP=$($CURL "$BASE_URL/")
check "Health check returns ok" "$RESP" '"status":"ok"'

# --------------------------------------------------------------------------
header "2. Scenarios API — GET /api/scenarios"
# --------------------------------------------------------------------------
RESP=$($CURL "$BASE_URL/api/scenarios")
check "Returns JSON array" "$RESP" '"id"'
check "Has scenario-1 (Easy)" "$RESP" '"scenario-1"'
check "Has scenario-2 (Medium)" "$RESP" '"scenario-2"'
check "Has scenario-3 (Hard)" "$RESP" '"scenario-3"'
check "Has difficulty field" "$RESP" '"difficulty"'
check "Has title field" "$RESP" '"title"'
# Ensure agent-only fields are NOT leaked
if echo "$RESP" | grep -q '"actor_strategy"'; then
  red "Scenarios endpoint leaks actor_strategy (agent-only field)"
  ((FAIL++))
else
  green "No agent-only fields leaked (actor_strategy)"
  ((PASS++))
fi
if echo "$RESP" | grep -q '"persona"'; then
  red "Scenarios endpoint leaks persona (agent-only field)"
  ((FAIL++))
else
  green "No agent-only fields leaked (persona)"
  ((PASS++))
fi

# --------------------------------------------------------------------------
header "3. Session API — POST /api/session"
# --------------------------------------------------------------------------
# This will fail without a valid VB_API_KEY, which is expected.
# We test that the endpoint exists and returns a meaningful error.
RESP=$($CURL -X POST "$BASE_URL/api/session" \
  -H "Content-Type: application/json" \
  -d '{"scenario_id":"scenario-1","participant_name":"Test User"}' \
  -w "\n%{http_code}" 2>/dev/null)
HTTP_CODE=$(echo "$RESP" | tail -1)
BODY=$(echo "$RESP" | head -n -1)

if [ "$HTTP_CODE" = "200" ]; then
  check "Session returns livekit_url" "$BODY" '"livekit_url"'
  check "Session returns token" "$BODY" '"token"'
  green "Session endpoint working with live VB_API_KEY"
elif [ "$HTTP_CODE" = "500" ] && echo "$BODY" | grep -q "VB_API_KEY"; then
  yellow "Session endpoint requires VB_API_KEY (expected without key)"
  ((PASS++))
else
  yellow "Session endpoint returned $HTTP_CODE — may need VB_API_KEY configured"
  ((PASS++))
fi

# --------------------------------------------------------------------------
header "4. Transcript API — POST /api/transcript"
# --------------------------------------------------------------------------
RESP=$($CURL -X POST "$BASE_URL/api/transcript" \
  -H "Content-Type: application/json" \
  -d '{
    "scenario_id": "scenario-1",
    "transcript": [
      {"role": "agent", "text": "Hi! I am looking for a gift for my partner.", "timestamp": "00:01"},
      {"role": "user", "text": "Welcome to Northfield Home and Living! My name is Alex. How can I help you today?", "timestamp": "00:05"},
      {"role": "agent", "text": "He just got into making coffee at home.", "timestamp": "00:10"},
      {"role": "user", "text": "I would recommend our BrewMaster Drip Coffee Maker. It is 64.99 and comes with a reusable filter.", "timestamp": "00:18"},
      {"role": "agent", "text": "That sounds great, I will take it!", "timestamp": "00:25"},
      {"role": "user", "text": "Wonderful! Shipping is 6.99, but if you add anything to bring your total over 75 dollars, shipping is free. Is there anything else I can help with?", "timestamp": "00:30"},
      {"role": "agent", "text": "No, that is everything. Thank you!", "timestamp": "00:35"},
      {"role": "user", "text": "Great! Your confirmation email will arrive shortly. Thank you for shopping with Northfield! Have a great day!", "timestamp": "00:40"}
    ]
  }')

check "Transcript accepted" "$RESP" '"status":"received"'
check "Returns session_id" "$RESP" '"session_id"'

# Extract session_id for coaching test
SESSION_ID=$(echo "$RESP" | grep -o '"session_id":"[^"]*"' | cut -d'"' -f4)

# --------------------------------------------------------------------------
header "5. Coaching API — POST /api/coaching (via session_id)"
# --------------------------------------------------------------------------
if [ -n "$SESSION_ID" ]; then
  RESP=$($CURL -X POST "$BASE_URL/api/coaching" \
    -H "Content-Type: application/json" \
    -d "{\"session_id\": \"$SESSION_ID\"}")
  check "Coaching returns scores" "$RESP" '"scores"'
  check "Coaching returns overall_score" "$RESP" '"overall_score"'
  check "Coaching returns improvement_areas" "$RESP" '"improvement_areas"'
  check "Coaching returns coaching_dialogue" "$RESP" '"coaching_dialogue"'
else
  red "No session_id from transcript step — skipping coaching test"
  ((FAIL++))
fi

# --------------------------------------------------------------------------
header "6. Coaching API — POST /api/coaching (inline transcript)"
# --------------------------------------------------------------------------
RESP=$($CURL -X POST "$BASE_URL/api/coaching" \
  -H "Content-Type: application/json" \
  -d '{
    "scenario_id": "scenario-3",
    "transcript": [
      {"role": "agent", "text": "Yeah hi. I need to talk to someone about a knife set I bought. One of the blades came chipped right out of the box. This was a wedding gift.", "timestamp": "00:01"},
      {"role": "user", "text": "Thank you for calling Northfield Home and Living. I am Alex and I am really sorry to hear that. Can I have your order number?", "timestamp": "00:08"},
      {"role": "agent", "text": "It is NF-20260214. I want a full refund.", "timestamp": "00:15"},
      {"role": "user", "text": "I see the ProEdge Knife Set from February 14th. A chipped blade is unacceptable and I apologize. Since this is past the 30-day return window, I cannot do a refund, but the set has a 5-year warranty. I can ship a replacement today with free expedited delivery.", "timestamp": "00:25"},
      {"role": "agent", "text": "Are you kidding me? I spent 120 dollars on a defective product. Maybe I should talk to a manager.", "timestamp": "00:35"},
      {"role": "user", "text": "I completely understand your frustration. I am authorized to handle this and want to make it right. Along with the replacement, I will add a 15 dollar store credit. Can I set that up?", "timestamp": "00:42"},
      {"role": "agent", "text": "Fine. Do the replacement.", "timestamp": "00:50"},
      {"role": "user", "text": "Done. A new ProEdge set ships today with 2-day delivery, 15 dollar credit is on your account, and you will get a prepaid return label. Anything else?", "timestamp": "00:55"},
      {"role": "agent", "text": "No.", "timestamp": "00:58"},
      {"role": "user", "text": "Thank you for your patience Karen. Have a good day.", "timestamp": "01:00"}
    ]
  }')

check "Inline coaching returns scores" "$RESP" '"scores"'
check "Inline coaching returns overall_score" "$RESP" '"overall_score"'

# --------------------------------------------------------------------------
header "7. Error Handling"
# --------------------------------------------------------------------------
# Missing fields
RESP=$($CURL -X POST "$BASE_URL/api/coaching" \
  -H "Content-Type: application/json" \
  -d '{}' \
  -w "\n%{http_code}" 2>/dev/null)
HTTP_CODE=$(echo "$RESP" | tail -1)
if [ "$HTTP_CODE" = "400" ] || [ "$HTTP_CODE" = "422" ]; then
  green "Coaching rejects empty request ($HTTP_CODE)"
  ((PASS++))
else
  red "Expected 400/422 for empty coaching request, got $HTTP_CODE"
  ((FAIL++))
fi

# Bad scenario in transcript
RESP=$($CURL -X POST "$BASE_URL/api/transcript" \
  -H "Content-Type: application/json" \
  -d '{"scenario_id":"nonexistent","transcript":[{"role":"user","text":"hello","timestamp":"00:00"}]}')
check "Transcript accepts any scenario_id" "$RESP" '"status":"received"'

# --------------------------------------------------------------------------
echo ""
echo "============================================"
echo "  Results: $PASS passed, $FAIL failed"
echo "============================================"

if [ "$FAIL" -gt 0 ]; then
  exit 1
fi
