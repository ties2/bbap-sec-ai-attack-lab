import requests
import numpy as np

print("1. Searching for an active sandbox...")
response = requests.get("http://localhost:5000/api/v2/sandbox/list")
sandboxes = response.json().get("sandboxes", [])

active_id = None
for sb in sandboxes:
    if sb.get("status") == "running":
        active_id = sb["id"]
        break

if not active_id:
    print("❌ No running sandboxes found in the database!")
    exit()

print(f"✅ Found active Sandbox! ID is: {active_id}")

print("2. Generating a random 224x224 image...")
dummy_image = np.random.rand(1, 3, 224, 224).tolist()

print(f"3. Sending request to Sandbox {active_id}...")
prediction_response = requests.post(
    f"http://localhost:5000/api/v2/sandbox/{active_id}/predict",
    json={"input": dummy_image}
)

print("\n--- Sandbox Response ---")
print(f"Status Code: {prediction_response.status_code}")
print(prediction_response.json())