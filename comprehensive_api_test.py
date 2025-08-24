#!/usr/bin/env python3
"""
Comprehensive API Testing Suite for AMP4EMAIL Leave Approval System
Tests all endpoints, security, and AMP email functionality
"""

import requests
import json
import time
import jwt
from datetime import datetime, timedelta
import sys
import os
from typing import Dict, Any, List

# Configuration
API_BASE_URL = "http://localhost:8000"
API_TIMEOUT = 30
JWT_SECRET = "your-secret-key-change-in-production"  # Should match backend

class Colors:
    """Console colors for output"""
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    PURPLE = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    END = '\033[0m'

class APITester:
    def __init__(self, base_url: str = API_BASE_URL):
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        self.session.timeout = API_TIMEOUT
        self.test_results = {
            'passed': 0,
            'failed': 0,
            'warnings': 0,
            'security_issues': 0
        }
        self.auth_token = None
        self.manager_token = None
        self.test_user_id = None
        self.test_manager_id = None
        self.test_leave_id = None
        
    def print_header(self, title: str):
        """Print formatted test section header"""
        print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.END}")
        print(f"{Colors.BOLD}{Colors.BLUE}{title.center(60)}{Colors.END}")
        print(f"{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.END}")
        
    def print_test(self, test_name: str, status: str, message: str = "", warning: bool = False):
        """Print formatted test result"""
        if status == "PASS":
            color = Colors.GREEN
            self.test_results['passed'] += 1
        elif status == "FAIL":
            color = Colors.RED
            self.test_results['failed'] += 1
        elif status == "WARN":
            color = Colors.YELLOW
            self.test_results['warnings'] += 1
            warning = True
        else:
            color = Colors.WHITE
            
        icon = "✅" if status == "PASS" else "❌" if status == "FAIL" else "⚠️"
        print(f"{icon} {color}{test_name:<50} [{status}]{Colors.END}")
        if message:
            print(f"   {Colors.CYAN}→ {message}{Colors.END}")
            
        if warning:
            self.test_results['warnings'] += 1
            
    def print_security_issue(self, issue: str, severity: str = "HIGH"):
        """Print security issue"""
        color = Colors.RED if severity == "HIGH" else Colors.YELLOW
        print(f"🔒 {color}SECURITY {severity}: {issue}{Colors.END}")
        self.test_results['security_issues'] += 1

    def test_server_connectivity(self):
        """Test basic server connectivity and health"""
        self.print_header("SERVER CONNECTIVITY TESTS")
        
        try:
            # Test root endpoint
            response = self.session.get(f"{self.base_url}/")
            if response.status_code == 200:
                self.print_test("Root endpoint connectivity", "PASS", f"Status: {response.status_code}")
            else:
                self.print_test("Root endpoint connectivity", "FAIL", f"Status: {response.status_code}")
        except Exception as e:
            self.print_test("Root endpoint connectivity", "FAIL", str(e))
            
        try:
            # Test health endpoint
            response = self.session.get(f"{self.base_url}/health")
            if response.status_code == 200:
                data = response.json()
                self.print_test("Health endpoint", "PASS", f"Status: {data.get('status', 'unknown')}")
            else:
                self.print_test("Health endpoint", "FAIL", f"Status: {response.status_code}")
        except Exception as e:
            self.print_test("Health endpoint", "FAIL", str(e))
            
        try:
            # Test API docs
            response = self.session.get(f"{self.base_url}/docs")
            if response.status_code == 200:
                self.print_test("API Documentation", "PASS", "Swagger UI accessible")
            else:
                self.print_test("API Documentation", "WARN", "Docs not accessible")
        except Exception as e:
            self.print_test("API Documentation", "WARN", str(e))

    def test_cors_configuration(self):
        """Test CORS configuration for AMP email compatibility"""
        self.print_header("CORS CONFIGURATION TESTS")
        
        # Test CORS preflight for AMP requests
        test_origins = [
            "https://mail.google.com",
            "https://outlook.live.com", 
            "https://amp.gmail.dev",
            "http://localhost:3000"
        ]
        
        for origin in test_origins:
            try:
                response = self.session.options(
                    f"{self.base_url}/api/leave/submit",
                    headers={
                        "Origin": origin,
                        "Access-Control-Request-Method": "POST",
                        "Access-Control-Request-Headers": "Content-Type"
                    }
                )
                
                if response.status_code in [200, 204]:
                    cors_headers = response.headers.get("Access-Control-Allow-Origin", "")
                    if cors_headers == "*" or origin in cors_headers:
                        self.print_test(f"CORS for {origin}", "PASS", f"Headers: {cors_headers}")
                    else:
                        self.print_test(f"CORS for {origin}", "FAIL", f"Origin not allowed: {cors_headers}")
                        if "mail.google.com" in origin:
                            self.print_security_issue("Gmail AMP emails will be blocked by CORS", "HIGH")
                else:
                    self.print_test(f"CORS for {origin}", "FAIL", f"Status: {response.status_code}")
                    
            except Exception as e:
                self.print_test(f"CORS for {origin}", "FAIL", str(e))

    def test_authentication_endpoints(self):
        """Test authentication endpoints"""
        self.print_header("AUTHENTICATION ENDPOINT TESTS")
        
        # Test user registration
        test_user_data = {
            "username": f"testuser_{int(time.time())}",
            "email": f"test_{int(time.time())}@example.com",
            "password": "TestPass123!",
            "full_name": "Test User",
            "role": "employee",
            "department": "IT"
        }
        
        test_manager_data = {
            "username": f"testmanager_{int(time.time())}",
            "email": f"manager_{int(time.time())}@example.com",
            "password": "TestPass123!",
            "full_name": "Test Manager",
            "role": "manager",
            "department": "IT"
        }
        
        try:
            # Register test user
            response = self.session.post(
                f"{self.base_url}/api/auth/register",
                json=test_user_data
            )
            
            if response.status_code == 200:
                self.print_test("User registration", "PASS", "Employee registered successfully")
                self.test_user_data = test_user_data
            else:
                self.print_test("User registration", "FAIL", f"Status: {response.status_code}, Response: {response.text}")
                
        except Exception as e:
            self.print_test("User registration", "FAIL", str(e))
            
        try:
            # Register test manager
            response = self.session.post(
                f"{self.base_url}/api/auth/register",
                json=test_manager_data
            )
            
            if response.status_code == 200:
                self.print_test("Manager registration", "PASS", "Manager registered successfully")
                self.test_manager_data = test_manager_data
            else:
                self.print_test("Manager registration", "FAIL", f"Status: {response.status_code}")
                
        except Exception as e:
            self.print_test("Manager registration", "FAIL", str(e))
            
        # Test user login
        try:
            login_data = {
                "username": test_user_data["username"],
                "password": test_user_data["password"]
            }
            
            response = self.session.post(
                f"{self.base_url}/api/auth/login",
                data=login_data,  # FastAPI OAuth2 expects form data
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )
            
            if response.status_code == 200:
                token_data = response.json()
                self.auth_token = token_data.get("access_token")
                self.print_test("User login", "PASS", "Token received")
                
                # Test token validation
                if self.auth_token:
                    headers = {"Authorization": f"Bearer {self.auth_token}"}
                    profile_response = self.session.get(f"{self.base_url}/api/auth/profile", headers=headers)
                    if profile_response.status_code == 200:
                        profile = profile_response.json()
                        self.test_user_id = profile.get("user_id")
                        self.print_test("Token validation", "PASS", f"User ID: {self.test_user_id}")
                    else:
                        self.print_test("Token validation", "FAIL", f"Status: {profile_response.status_code}")
            else:
                self.print_test("User login", "FAIL", f"Status: {response.status_code}, Response: {response.text}")
                
        except Exception as e:
            self.print_test("User login", "FAIL", str(e))
            
        # Test manager login
        try:
            login_data = {
                "username": test_manager_data["username"],
                "password": test_manager_data["password"]
            }
            
            response = self.session.post(
                f"{self.base_url}/api/auth/login",
                data=login_data,
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )
            
            if response.status_code == 200:
                token_data = response.json()
                self.manager_token = token_data.get("access_token")
                self.print_test("Manager login", "PASS", "Manager token received")
            else:
                self.print_test("Manager login", "FAIL", f"Status: {response.status_code}")
                
        except Exception as e:
            self.print_test("Manager login", "FAIL", str(e))

    def test_leave_management_endpoints(self):
        """Test leave management endpoints"""
        self.print_header("LEAVE MANAGEMENT ENDPOINT TESTS")
        
        if not self.auth_token:
            self.print_test("Leave endpoints", "FAIL", "No auth token available")
            return
            
        headers = {"Authorization": f"Bearer {self.auth_token}"}
        
        # Test leave submission
        leave_data = {
            "start_date": "2024-12-25",
            "end_date": "2024-12-27", 
            "leave_type": "Annual Leave",
            "reason": "Holiday vacation with family",
            "manager_email": self.test_manager_data.get("email", "manager@example.com")
        }
        
        try:
            response = self.session.post(
                f"{self.base_url}/api/leave/submit",
                json=leave_data,
                headers=headers
            )
            
            if response.status_code == 200:
                result = response.json()
                self.test_leave_id = result.get("leave_request_id")
                self.print_test("Leave submission", "PASS", f"Leave ID: {self.test_leave_id}")
            else:
                self.print_test("Leave submission", "FAIL", f"Status: {response.status_code}, Response: {response.text}")
                
        except Exception as e:
            self.print_test("Leave submission", "FAIL", str(e))
            
        # Test get my requests
        try:
            response = self.session.get(
                f"{self.base_url}/api/leave/my-requests",
                headers=headers
            )
            
            if response.status_code == 200:
                requests_data = response.json()
                self.print_test("Get my requests", "PASS", f"Found {len(requests_data)} requests")
            else:
                self.print_test("Get my requests", "FAIL", f"Status: {response.status_code}")
                
        except Exception as e:
            self.print_test("Get my requests", "FAIL", str(e))
            
        # Test pending approvals (manager only)
        if self.manager_token:
            manager_headers = {"Authorization": f"Bearer {self.manager_token}"}
            try:
                response = self.session.get(
                    f"{self.base_url}/api/leave/pending-approvals",
                    headers=manager_headers
                )
                
                if response.status_code == 200:
                    approvals = response.json()
                    self.print_test("Pending approvals", "PASS", f"Found {len(approvals)} pending approvals")
                elif response.status_code == 403:
                    self.print_test("Pending approvals access control", "PASS", "Non-manager access denied")
                else:
                    self.print_test("Pending approvals", "FAIL", f"Status: {response.status_code}")
                    
            except Exception as e:
                self.print_test("Pending approvals", "FAIL", str(e))

    def test_amp_email_endpoints(self):
        """Test AMP email specific endpoints"""
        self.print_header("AMP EMAIL ENDPOINT TESTS")
        
        if not self.test_leave_id:
            self.print_test("AMP endpoints", "FAIL", "No test leave request available")
            return
            
        # Generate test action token
        try:
            test_token = jwt.encode(
                {
                    'leave_request_id': self.test_leave_id,
                    'manager_id': self.test_manager_id or "test_manager_id",
                    'exp': datetime.utcnow() + timedelta(hours=24),
                    'iat': datetime.utcnow(),
                    'type': 'leave_action'
                },
                JWT_SECRET,
                algorithm='HS256'
            )
            
            # Test AMP approve endpoint
            amp_data = {
                "token": test_token,
                "comments": "Approved via AMP email test"
            }
            
            response = self.session.post(
                f"{self.base_url}/api/leave/amp/approve",
                data=amp_data,
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )
            
            if response.status_code == 200:
                result = response.json()
                self.print_test("AMP approve endpoint", "PASS", f"Action: {result.get('action', 'unknown')}")
            else:
                self.print_test("AMP approve endpoint", "FAIL", f"Status: {response.status_code}, Response: {response.text}")
                
        except Exception as e:
            self.print_test("AMP approve endpoint", "FAIL", str(e))
            
        # Test token status endpoint
        try:
            response = self.session.get(f"{self.base_url}/api/leave/amp/status/{test_token}")
            
            if response.status_code == 200:
                status_data = response.json()
                self.print_test("AMP status endpoint", "PASS", f"Status: {status_data.get('status', 'unknown')}")
            else:
                self.print_test("AMP status endpoint", "FAIL", f"Status: {response.status_code}")
                
        except Exception as e:
            self.print_test("AMP status endpoint", "FAIL", str(e))

    def test_security_vulnerabilities(self):
        """Test for common security vulnerabilities"""
        self.print_header("SECURITY VULNERABILITY TESTS")
        
        # Test SQL injection attempts
        injection_payloads = [
            "'; DROP TABLE users; --",
            "' OR 1=1 --",
            "admin'; --",
            "<script>alert('xss')</script>",
            "{{constructor.constructor('return process')().exit()}}"
        ]
        
        for payload in injection_payloads:
            try:
                malicious_data = {
                    "username": payload,
                    "password": "test123"
                }
                
                response = self.session.post(
                    f"{self.base_url}/api/auth/login",
                    data=malicious_data,
                    headers={"Content-Type": "application/x-www-form-urlencoded"}
                )
                
                # Should not return 500 or crash
                if response.status_code == 500:
                    self.print_security_issue(f"Potential injection vulnerability with payload: {payload[:20]}...", "HIGH")
                elif response.status_code == 200:
                    self.print_security_issue(f"Authentication bypass possible with payload: {payload[:20]}...", "CRITICAL")
                    
            except Exception as e:
                if "500" in str(e):
                    self.print_security_issue(f"Server error on malicious input: {payload[:20]}...", "MEDIUM")
                    
        # Test JWT token manipulation
        if self.auth_token:
            try:
                # Test with tampered token
                tampered_token = self.auth_token[:-10] + "tampered123"
                headers = {"Authorization": f"Bearer {tampered_token}"}
                
                response = self.session.get(f"{self.base_url}/api/leave/my-requests", headers=headers)
                
                if response.status_code == 200:
                    self.print_security_issue("JWT token validation bypass", "CRITICAL")
                elif response.status_code in [401, 403]:
                    self.print_test("JWT token tampering protection", "PASS", "Tampered token rejected")
                    
            except Exception as e:
                self.print_test("JWT token security test", "WARN", str(e))
                
        # Test rate limiting
        self.print_test("Rate limiting", "WARN", "Manual testing required - not implemented in automated tests")
        
        # Test HTTPS redirect
        self.print_test("HTTPS enforcement", "WARN", "Production should enforce HTTPS")

    def test_email_template_validation(self):
        """Validate AMP email template compliance"""
        self.print_header("AMP EMAIL TEMPLATE VALIDATION")
        
        template_path = os.path.join(os.path.dirname(__file__), "backend", "app", "utils", "templates", "leave_action.amp.html")
        
        try:
            with open(template_path, 'r', encoding='utf-8') as f:
                template_content = f.read()
                
            # Check for required AMP4EMAIL elements
            required_elements = [
                'amp4email',
                'amp-form',
                'amp4email-boilerplate',
                'action-xhr',
                'custom-validation-reporting'
            ]
            
            for element in required_elements:
                if element in template_content:
                    self.print_test(f"AMP element: {element}", "PASS", "Found in template")
                else:
                    self.print_test(f"AMP element: {element}", "FAIL", "Missing from template")
                    
            # Check for security issues in template
            security_patterns = [
                'javascript:',
                'on[a-z]+=\"',
                'eval\\(',
                'innerHTML',
                'document\\.'
            ]
            
            import re
            for pattern in security_patterns:
                if re.search(pattern, template_content, re.IGNORECASE):
                    self.print_security_issue(f"Potentially unsafe pattern in template: {pattern}", "MEDIUM")
                    
            # Check template size
            template_size = len(template_content.encode('utf-8'))
            if template_size > 200 * 1024:  # 200KB limit for AMP emails
                self.print_test("Template size", "FAIL", f"Template too large: {template_size} bytes")
            else:
                self.print_test("Template size", "PASS", f"Size: {template_size} bytes")
                
        except FileNotFoundError:
            self.print_test("AMP template file", "FAIL", f"Template not found: {template_path}")
        except Exception as e:
            self.print_test("AMP template validation", "FAIL", str(e))

    def test_performance_and_load(self):
        """Test basic performance and load handling"""
        self.print_header("PERFORMANCE & LOAD TESTS")
        
        # Test response times
        endpoints_to_test = [
            ("/", "GET"),
            ("/health", "GET"),
            ("/api/auth/register", "POST")
        ]
        
        for endpoint, method in endpoints_to_test:
            start_time = time.time()
            try:
                if method == "GET":
                    response = self.session.get(f"{self.base_url}{endpoint}")
                else:
                    response = self.session.post(f"{self.base_url}{endpoint}", json={})
                    
                response_time = (time.time() - start_time) * 1000  # ms
                
                if response_time < 1000:  # Under 1 second
                    self.print_test(f"Response time {endpoint}", "PASS", f"{response_time:.2f}ms")
                elif response_time < 3000:  # Under 3 seconds
                    self.print_test(f"Response time {endpoint}", "WARN", f"{response_time:.2f}ms (slow)")
                else:
                    self.print_test(f"Response time {endpoint}", "FAIL", f"{response_time:.2f}ms (too slow)")
                    
            except Exception as e:
                self.print_test(f"Response time {endpoint}", "FAIL", str(e))
                
        # Simple concurrent request test
        self.print_test("Concurrent requests", "WARN", "Basic load testing - implement stress tests for production")

    def generate_report(self):
        """Generate comprehensive test report"""
        self.print_header("TEST RESULTS SUMMARY")
        
        total_tests = self.test_results['passed'] + self.test_results['failed'] + self.test_results['warnings']
        
        print(f"{Colors.GREEN}✅ PASSED: {self.test_results['passed']}{Colors.END}")
        print(f"{Colors.RED}❌ FAILED: {self.test_results['failed']}{Colors.END}")
        print(f"{Colors.YELLOW}⚠️  WARNINGS: {self.test_results['warnings']}{Colors.END}")
        print(f"{Colors.PURPLE}🔒 SECURITY ISSUES: {self.test_results['security_issues']}{Colors.END}")
        print(f"{Colors.BLUE}📊 TOTAL TESTS: {total_tests}{Colors.END}")
        
        if self.test_results['failed'] > 0:
            print(f"\n{Colors.RED}{Colors.BOLD}❌ CRITICAL ISSUES FOUND - FIX BEFORE PRODUCTION{Colors.END}")
            
        if self.test_results['security_issues'] > 0:
            print(f"\n{Colors.PURPLE}{Colors.BOLD}🔒 SECURITY VULNERABILITIES DETECTED{Colors.END}")
            
        success_rate = (self.test_results['passed'] / total_tests * 100) if total_tests > 0 else 0
        print(f"\n{Colors.BOLD}SUCCESS RATE: {success_rate:.1f}%{Colors.END}")
        
        return self.test_results

    def run_all_tests(self):
        """Run the complete test suite"""
        print(f"{Colors.BOLD}{Colors.BLUE}AMP4EMAIL Leave Approval System - API Test Suite{Colors.END}")
        print(f"{Colors.BLUE}Testing API at: {self.base_url}{Colors.END}")
        print(f"{Colors.BLUE}Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}{Colors.END}")
        
        try:
            self.test_server_connectivity()
            self.test_cors_configuration()
            self.test_authentication_endpoints()
            self.test_leave_management_endpoints()
            self.test_amp_email_endpoints()
            self.test_security_vulnerabilities()
            self.test_email_template_validation()
            self.test_performance_and_load()
            
        except KeyboardInterrupt:
            print(f"\n{Colors.YELLOW}Tests interrupted by user{Colors.END}")
        except Exception as e:
            print(f"\n{Colors.RED}Test suite error: {str(e)}{Colors.END}")
            
        finally:
            results = self.generate_report()
            return results

def main():
    """Main test execution function"""
    if len(sys.argv) > 1:
        api_url = sys.argv[1]
    else:
        api_url = API_BASE_URL
        
    print(f"Starting API tests for: {api_url}")
    
    tester = APITester(api_url)
    results = tester.run_all_tests()
    
    # Exit with appropriate code
    if results['failed'] > 0 or results['security_issues'] > 0:
        sys.exit(1)
    else:
        sys.exit(0)

if __name__ == "__main__":
    main()
