
from app.services.recovery_engine import evaluate

tests = [
    {
        "name": "Working phone",
        "input": {
            "category": "Mobile & Communication",
            "working_status": "working",
            "physical_condition": "good",
            "defects": "",
            "age_years": 2,
        },
        "expected": "reuse_resale",
    },
    {
        "name": "Repairable laptop",
        "input": {
            "category": "Laptop / Computer",
            "working_status": "partially_working",
            "physical_condition": "good",
            "defects": "Keyboard needs repair",
            "estimated_repair_cost": 30,
            "estimated_resale_value": 200,
            "age_years": 3,
        },
        "expected": "repair",
    },
    {
        "name": "Swollen battery",
        "input": {
            "category": "Battery & Power Equipment",
            "working_status": "not_working",
            "physical_condition": "poor",
            "defects": "Battery swollen",
            "safety_flags": ["swollen_battery"],
        },
        "expected": "safety_review",
    },
    {
        "name": "Missing repair cost",
        "input": {
            "category": "Laptop / Computer",
            "working_status": "partially_working",
            "physical_condition": "good",
            "defects": "Keyboard needs repair",
            "estimated_resale_value": 200,
        },
        "expected": "manual_review",
    },
    {
        "name": "Unknown category",
        "input": {
            "category": "Unknown",
            "working_status": "working",
            "physical_condition": "good",
        },
        "expected": "manual_review",
    },
]

for test in tests:
    result = evaluate(**test["input"])
    passed = result.route == test["expected"]

    print(f"\nTest: {test['name']}")
    print(f"Expected: {test['expected']}")
    print(f"Actual:   {result.route}")
    print(f"Score:    {result.suitability_score}")
    print(f"Reasons:  {result.reason_codes}")
    print(f"Safety:   {result.safety_flag}")
    print(f"Result:   {'PASS' if passed else 'FAIL'}")

print("\nAll tests completed.")
