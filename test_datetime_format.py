from datetime import datetime, timezone

# Test old format (what's currently in DB)
old_format = "2025-10-11T22:04:17.402626"
print(f"Old format (6 digits microseconds): {old_format}")

# Test new format (what we want)
new_format = datetime.now(timezone.utc).isoformat(timespec='milliseconds').replace('+00:00', 'Z')
print(f"New format (3 digits milliseconds + Z): {new_format}")

# Test conversion from old to new
try:
    dt = datetime.fromisoformat(old_format.replace('Z', '+00:00'))
    converted = dt.astimezone(timezone.utc).isoformat(timespec='milliseconds').replace('+00:00', 'Z')
    print(f"Converted old → new: {converted}")
except Exception as e:
    print(f"Error converting: {e}")

# Test JavaScript compatibility
print("\n🧪 Testing JavaScript compatibility:")
print(f"Old: new Date('{old_format}')  → Will fail (no Z, 6 digits)")
print(f"New: new Date('{new_format}')  → Will work ✅ (Z, 3 digits)")
