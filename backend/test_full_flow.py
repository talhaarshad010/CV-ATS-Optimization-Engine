import sys
import json
import requests

def run_test(pdf_path: str):
    base_url = "http://localhost:8000/api/v1"

    # Step 1: Upload CV (Phase 1)
    print(f"Step 1: Uploading CV from path: {pdf_path}...")
    try:
        with open(pdf_path, "rb") as f:
            files = {"file": (pdf_path, f, "application/pdf")}
            upload_resp = requests.post(f"{base_url}/upload", files=files)
    except FileNotFoundError:
        print(f"Error: File not found at '{pdf_path}'. Please specify a valid PDF path.")
        sys.exit(1)
    except Exception as e:
        print(f"Connection failed: {e}")
        sys.exit(1)

    if upload_resp.status_code != 200:
        print(f"Upload failed (Status {upload_resp.status_code}): {upload_resp.text}")
        sys.exit(1)

    upload_data = upload_resp.json()
    candidate_id = upload_data.get("candidate_id")
    print(f"✔ Upload Success! Candidate ID: {candidate_id}")

    # Step 2: Parse CV (Phase 2)
    print(f"\nStep 2: Parsing CV with ID: {candidate_id}...")
    parse_resp = requests.post(f"{base_url}/parse/{candidate_id}")

    if parse_resp.status_code != 200:
        print(f"Parsing failed (Status {parse_resp.status_code}): {parse_resp.text}")
        sys.exit(1)

    parse_data = parse_resp.json()
    print("✔ Parsing Success! Structured Result:")
    print(json.dumps(parse_data, indent=2))

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python test_full_flow.py <path_to_cv_pdf>")
        sys.exit(1)
    run_test(sys.argv[1])
