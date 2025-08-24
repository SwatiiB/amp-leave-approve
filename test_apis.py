#!/usr/bin/env python3
"""
Comprehensive API Testing Script for Leave Management System
Tests all endpoints with proper authentication flow
"""

import requests
import json
from datetime import datetime, timedelta
import time

# Configuration
BASE_URL = "http://127.0.0.1:8000"
API_BASE_URL = f"{BASE_URL}/api"

# Colors for output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    PURPLE = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    END = '\033[0m'

def print_header(title):
    print(f"\n{Colors.BOLD}{Colors.CYAN}{'='*60}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.CYAN}{title.center(60)}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.CYAN}{'='*60}{Colors.END}\n")

def print_test(test_name, status, details=""):
    status_color = Colors.GREEN if status == "PASS" else Colors.RED
    print(f"{Colors.BOLD}Test: {test_name}{Colors.END}")
    print(f"Status: {status_color}{status}{Colors.END}")
    if details:
        print(f"Details: {details}")
    print("-" * 50)

def print_response(response):
    print(f"{Colors.YELLOW}Status Code: {response.status_code}{Colors.END}")
    try:
        print(f"{Colors.PURPLE}Response: {json.dumps(response.json(), indent=2)}{Colors.END}")
    except:
        print(f"{Colors.PURPLE}Response: {response.text}{Colors.END}")

# Global variables to store tokens and IDs
user_token = None
hr_token = None
manager_token = None
test_user_id = None
test_leave_id = None

def test_health_endpoints():
    """Test basic health and root endpoints"""
    print_header("HEALTH & ROOT ENDPOINTS")
    
    # Test root endpoint
    try:
        response = requests.get(f"{BASE_URL}/")
        print_test("Root Endpoint (/)", 
                  "PASS" if response.status_code == 200 else "FAIL",
                  f"Status: {response.status_code}")
        print_response(response)
    except Exception as e:
        print_test("Root Endpoint (/)", "FAIL", f"Error: {str(e)}")
    
    # Test health endpoint
    try:
        response = requests.get(f"{BASE_URL}/health")
        print_test("Health Check (/health)", 
                  "PASS" if response.status_code == 200 else "FAIL",
                  f"Status: {response.status_code}")
        print_response(response)
    except Exception as e:
        print_test("Health Check (/health)", "FAIL", f"Error: {str(e)}")

def test_user_registration():
    """Test user registration endpoints"""
    print_header("USER REGISTRATION")
    global test_user_id
    
    # Test Employee Registration
    employee_data = {
        "username": f"test_employee_{int(time.time())}",
        "email": f"employee_{int(time.time())}@test.com",
        "password": "testpass123",
        "full_name": "Test Employee",
        "role": "employee",
        "department": "Engineering"
    }
    
    try:
        response = requests.post(f"{API_BASE_URL}/auth/register", json=employee_data)
        print_test("Employee Registration", 
                  "PASS" if response.status_code == 200 else "FAIL",
                  f"Status: {response.status_code}")
        print_response(response)
        
        if response.status_code == 200:
            test_user_id = response.json().get("user_id")
    except Exception as e:
        print_test("Employee Registration", "FAIL", f"Error: {str(e)}")
    
    # Test Manager Registration  
    manager_data = {
        "username": f"test_manager_{int(time.time())}",
        "email": f"manager_{int(time.time())}@test.com",
        "password": "managerpass123",
        "full_name": "Test Manager",
        "role": "manager",
        "department": "Engineering"
    }
    
    try:
        response = requests.post(f"{API_BASE_URL}/auth/register", json=manager_data)
        print_test("Manager Registration", 
                  "PASS" if response.status_code == 200 else "FAIL",
                  f"Status: {response.status_code}")
        print_response(response)
    except Exception as e:
        print_test("Manager Registration", "FAIL", f"Error: {str(e)}")
    
    # Test HR Registration
    hr_data = {
        "username": f"test_hr_{int(time.time())}",
        "email": f"hr_{int(time.time())}@test.com",
        "password": "hrpass123",
        "full_name": "Test HR",
        "role": "hr", 
        "department": "Human Resources"
    }
    
    try:
        response = requests.post(f"{API_BASE_URL}/auth/register", json=hr_data)
        print_test("HR Registration", 
                  "PASS" if response.status_code == 200 else "FAIL",
                  f"Status: {response.status_code}")
        print_response(response)
    except Exception as e:
        print_test("HR Registration", "FAIL", f"Error: {str(e)}")
    
    # Test Duplicate Registration (should fail)
    try:
        response = requests.post(f"{API_BASE_URL}/auth/register", json=employee_data)
        print_test("Duplicate Registration (Expected Fail)", 
                  "PASS" if response.status_code == 400 else "FAIL",
                  f"Status: {response.status_code}")
        print_response(response)
    except Exception as e:
        print_test("Duplicate Registration", "FAIL", f"Error: {str(e)}")

def test_authentication():
    """Test login endpoints"""
    print_header("AUTHENTICATION")
    global user_token, hr_token, manager_token
    
    # Test Employee Login
    login_data = {
        "username": f"test_employee_{int(time.time() - 10)}",  # Use recent username
        "password": "testpass123"
    }
    
    try:
        response = requests.post(f"{API_BASE_URL}/auth/login", data=login_data)
        print_test("Employee Login", 
                  "PASS" if response.status_code == 200 else "FAIL",
                  f"Status: {response.status_code}")
        print_response(response)
        
        if response.status_code == 200:
            user_token = response.json().get("access_token")
    except Exception as e:
        print_test("Employee Login", "FAIL", f"Error: {str(e)}")
    
    # Test Invalid Login
    invalid_login = {
        "username": "invalid_user",
        "password": "wrong_password"
    }
    
    try:
        response = requests.post(f"{API_BASE_URL}/auth/login", data=invalid_login)
        print_test("Invalid Login (Expected Fail)", 
                  "PASS" if response.status_code == 401 else "FAIL",
                  f"Status: {response.status_code}")
        print_response(response)
    except Exception as e:
        print_test("Invalid Login", "FAIL", f"Error: {str(e)}")

def test_leave_submission():
    """Test leave request submission"""
    print_header("LEAVE REQUEST SUBMISSION")
    global test_leave_id
    
    if not user_token:
        print_test("Leave Submission", "SKIP", "No user token available")
        return
    
    headers = {"Authorization": f"Bearer {user_token}"}
    
    # Test Leave Submission
    leave_data = {
        "start_date": (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d"),
        "end_date": (datetime.now() + timedelta(days=9)).strftime("%Y-%m-%d"),
        "leave_type": "Vacation",
        "reason": "Family vacation",
        "manager_email": "manager@test.com"
    }
    
    try:
        response = requests.post(f"{API_BASE_URL}/leave/submit", json=leave_data, headers=headers)
        print_test("Leave Request Submission", 
                  "PASS" if response.status_code == 200 else "FAIL",
                  f"Status: {response.status_code}")
        print_response(response)
        
        if response.status_code == 200:
            test_leave_id = response.json().get("leave_request_id")
    except Exception as e:
        print_test("Leave Request Submission", "FAIL", f"Error: {str(e)}")
    
    # Test Unauthorized Leave Submission
    try:
        response = requests.post(f"{API_BASE_URL}/leave/submit", json=leave_data)
        print_test("Unauthorized Leave Submission (Expected Fail)", 
                  "PASS" if response.status_code == 401 else "FAIL",
                  f"Status: {response.status_code}")
        print_response(response)
    except Exception as e:
        print_test("Unauthorized Leave Submission", "FAIL", f"Error: {str(e)}")

def test_leave_retrieval():
    """Test leave request retrieval endpoints"""
    print_header("LEAVE REQUEST RETRIEVAL")
    
    if not user_token:
        print_test("Leave Retrieval", "SKIP", "No user token available")
        return
    
    headers = {"Authorization": f"Bearer {user_token}"}
    
    # Test My Requests
    try:
        response = requests.get(f"{API_BASE_URL}/leave/my-requests", headers=headers)
        print_test("Get My Requests", 
                  "PASS" if response.status_code == 200 else "FAIL",
                  f"Status: {response.status_code}")
        print_response(response)
    except Exception as e:
        print_test("Get My Requests", "FAIL", f"Error: {str(e)}")
    
    # Test Pending Approvals (should fail for employee)
    try:
        response = requests.get(f"{API_BASE_URL}/leave/pending-approvals", headers=headers)
        print_test("Get Pending Approvals (Employee - Expected Fail)", 
                  "PASS" if response.status_code == 403 else "FAIL",
                  f"Status: {response.status_code}")
        print_response(response)
    except Exception as e:
        print_test("Get Pending Approvals (Employee)", "FAIL", f"Error: {str(e)}")

def test_leave_actions():
    """Test leave approval/rejection"""
    print_header("LEAVE ACTIONS")
    
    if not test_leave_id:
        print_test("Leave Actions", "SKIP", "No leave request ID available")
        return
    
    if not user_token:
        print_test("Leave Actions", "SKIP", "No user token available")
        return
    
    headers = {"Authorization": f"Bearer {user_token}"}
    
    # Test Leave Approval (should fail - wrong password)
    action_data = {
        "manager_password": "wrong_password",
        "comments": "Test approval"
    }
    
    try:
        response = requests.post(f"{API_BASE_URL}/leave/{test_leave_id}/approve", 
                               json=action_data, headers=headers)
        print_test("Leave Approval (Wrong Password - Expected Fail)", 
                  "PASS" if response.status_code == 401 else "FAIL",
                  f"Status: {response.status_code}")
        print_response(response)
    except Exception as e:
        print_test("Leave Approval (Wrong Password)", "FAIL", f"Error: {str(e)}")

def test_amp_email_endpoints():
    """Test AMP email specific endpoints"""
    print_header("AMP EMAIL ENDPOINTS")
    
    # Test AMP endpoints without proper token (should fail)
    form_data = {
        "token": "invalid_token",
        "comments": "Test comment"
    }
    
    try:
        response = requests.post(f"{API_BASE_URL}/leave/amp/approve", data=form_data)
        print_test("AMP Approve (Invalid Token - Expected Fail)", 
                  "PASS" if response.status_code == 400 else "FAIL",
                  f"Status: {response.status_code}")
        print_response(response)
    except Exception as e:
        print_test("AMP Approve (Invalid Token)", "FAIL", f"Error: {str(e)}")
    
    try:
        response = requests.post(f"{API_BASE_URL}/leave/amp/reject", data=form_data)
        print_test("AMP Reject (Invalid Token - Expected Fail)", 
                  "PASS" if response.status_code == 400 else "FAIL",
                  f"Status: {response.status_code}")
        print_response(response)
    except Exception as e:
        print_test("AMP Reject (Invalid Token)", "FAIL", f"Error: {str(e)}")
    
    # Test AMP Status Check
    try:
        response = requests.get(f"{API_BASE_URL}/leave/amp/status/invalid_token")
        print_test("AMP Status Check (Invalid Token - Expected Fail)", 
                  "PASS" if response.status_code == 400 else "FAIL",
                  f"Status: {response.status_code}")
        print_response(response)
    except Exception as e:
        print_test("AMP Status Check (Invalid Token)", "FAIL", f"Error: {str(e)}")

def test_edge_cases():
    """Test edge cases and error handling"""
    print_header("EDGE CASES & ERROR HANDLING")
    
    # Test non-existent endpoints
    try:
        response = requests.get(f"{API_BASE_URL}/nonexistent")
        print_test("Non-existent Endpoint (Expected Fail)", 
                  "PASS" if response.status_code == 404 else "FAIL",
                  f"Status: {response.status_code}")
        print_response(response)
    except Exception as e:
        print_test("Non-existent Endpoint", "FAIL", f"Error: {str(e)}")
    
    # Test malformed JSON
    try:
        response = requests.post(f"{API_BASE_URL}/auth/register", 
                               data="invalid json", 
                               headers={"Content-Type": "application/json"})
        print_test("Malformed JSON (Expected Fail)", 
                  "PASS" if response.status_code in [400, 422] else "FAIL",
                  f"Status: {response.status_code}")
        print_response(response)
    except Exception as e:
        print_test("Malformed JSON", "FAIL", f"Error: {str(e)}")

def run_all_tests():
    """Run all API tests"""
    print(f"{Colors.BOLD}{Colors.GREEN}")
    print("+" * 80)
    print("  LEAVE MANAGEMENT SYSTEM - COMPREHENSIVE API TESTING")
    print("+" * 80)
    print(f"{Colors.END}")
    
    start_time = time.time()
    
    # Run all test suites
    test_health_endpoints()
    test_user_registration()
    test_authentication()
    test_leave_submission()
    test_leave_retrieval()
    test_leave_actions()
    test_amp_email_endpoints()
    test_edge_cases()
    
    end_time = time.time()
    
    print_header("TESTING COMPLETE")
    print(f"{Colors.BOLD}{Colors.GREEN}Total Test Time: {end_time - start_time:.2f} seconds{Colors.END}")
    print(f"{Colors.BOLD}{Colors.CYAN}All API endpoints have been tested!{Colors.END}")
    print(f"{Colors.YELLOW}Note: Some tests expected to fail for security/validation purposes.{Colors.END}")

if __name__ == "__main__":
    run_all_tests()
