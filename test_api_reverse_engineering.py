#!/usr/bin/env python3
"""
Test script for API reverse engineering endpoint
"""

import requests
import json

def test_api_reverse_engineering():
    """Test the API reverse engineering endpoint."""
    
    print("=== TESTING API REVERSE ENGINEERING ENDPOINT ===")
    
    # API endpoint
    base_url = "http://localhost:5001"
    endpoint = "/api/configurations/g_visaev_v251/reverse-engineer"
    url = base_url + endpoint
    
    # Auth token
    token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoxLCJ1c2VybmFtZSI6ImFkbWluIiwicm9sZSI6ImFkbWluIiwiaXNfYWRtaW4iOnRydWUsImV4cCI6MTc1NDY2MDkyMX0.FI7B4gz0kNgEBbYZd9DS6-e7GRv6f_NlnM-2RkalWfQ"
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    print(f"URL: {url}")
    print(f"Headers: {headers}")
    
    try:
        # Make the request
        response = requests.post(url, headers=headers)
        
        print(f"Status Code: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            try:
                data = response.json()
                print(f"Response Data: {json.dumps(data, indent=2)}")
            except json.JSONDecodeError:
                print(f"Raw Response: {response.text}")
        else:
            print(f"Error Response: {response.text}")
            
    except Exception as e:
        print(f"Request failed: {e}")

if __name__ == "__main__":
    test_api_reverse_engineering() 