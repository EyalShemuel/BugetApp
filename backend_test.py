#!/usr/bin/env python3
"""
Backend API Testing Script for Budget Planning App
Tests all major backend endpoints with comprehensive scenarios
"""

import requests
import json
from datetime import datetime, date
import uuid
import sys

# Get backend URL from environment
BACKEND_URL = "https://d67a36d6-3b06-4d2d-87c5-d44e16785611.preview.emergentagent.com/api"

class BudgetAppTester:
    def __init__(self):
        self.base_url = BACKEND_URL
        self.test_results = []
        self.created_transaction_ids = []
        
    def log_test(self, test_name, success, message, details=None):
        """Log test results"""
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}: {message}")
        if details:
            print(f"   Details: {details}")
        
        self.test_results.append({
            "test": test_name,
            "success": success,
            "message": message,
            "details": details
        })
    
    def test_health_check(self):
        """Test health check endpoint"""
        try:
            response = requests.get(f"{self.base_url}/health", timeout=10)
            if response.status_code == 200:
                data = response.json()
                self.log_test("Health Check", True, "API is healthy", data)
                return True
            else:
                self.log_test("Health Check", False, f"Status code: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Health Check", False, f"Connection error: {str(e)}")
            return False
    
    def test_create_transaction(self):
        """Test creating transactions"""
        test_transactions = [
            {
                "amount": 5000.0,
                "type": "income",
                "category": "משכורת",
                "description": "משכורת חודש דצמבר",
                "date": "2024-12-01"
            },
            {
                "amount": 350.0,
                "type": "expense", 
                "category": "מזון",
                "description": "קניות בסופרמרקט",
                "date": "2024-12-02"
            },
            {
                "amount": 120.0,
                "type": "expense",
                "category": "תחבורה", 
                "description": "דלק לרכב",
                "date": "2024-12-03"
            }
        ]
        
        success_count = 0
        for i, transaction in enumerate(test_transactions):
            try:
                response = requests.post(
                    f"{self.base_url}/transactions",
                    json=transaction,
                    timeout=10
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if "id" in data:
                        self.created_transaction_ids.append(data["id"])
                        self.log_test(f"Create Transaction {i+1}", True, 
                                    f"Created {transaction['type']} transaction", 
                                    f"ID: {data['id']}, Amount: {transaction['amount']}")
                        success_count += 1
                    else:
                        self.log_test(f"Create Transaction {i+1}", False, "No ID returned")
                else:
                    self.log_test(f"Create Transaction {i+1}", False, 
                                f"Status code: {response.status_code}", response.text)
            except Exception as e:
                self.log_test(f"Create Transaction {i+1}", False, f"Error: {str(e)}")
        
        return success_count == len(test_transactions)
    
    def test_get_transactions(self):
        """Test retrieving transactions"""
        try:
            response = requests.get(f"{self.base_url}/transactions", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if "transactions" in data and isinstance(data["transactions"], list):
                    count = len(data["transactions"])
                    self.log_test("Get Transactions", True, 
                                f"Retrieved {count} transactions", 
                                f"Response structure valid")
                    return True
                else:
                    self.log_test("Get Transactions", False, "Invalid response structure")
                    return False
            else:
                self.log_test("Get Transactions", False, f"Status code: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Get Transactions", False, f"Error: {str(e)}")
            return False
    
    def test_update_transaction(self):
        """Test updating a transaction"""
        if not self.created_transaction_ids:
            self.log_test("Update Transaction", False, "No transaction IDs available for testing")
            return False
        
        transaction_id = self.created_transaction_ids[0]
        updated_data = {
            "amount": 5500.0,
            "type": "income",
            "category": "משכורת",
            "description": "משכורת מעודכנת חודש דצמבר",
            "date": "2024-12-01"
        }
        
        try:
            response = requests.put(
                f"{self.base_url}/transactions/{transaction_id}",
                json=updated_data,
                timeout=10
            )
            
            if response.status_code == 200:
                self.log_test("Update Transaction", True, 
                            "Transaction updated successfully", 
                            f"ID: {transaction_id}, New amount: {updated_data['amount']}")
                return True
            else:
                self.log_test("Update Transaction", False, 
                            f"Status code: {response.status_code}", response.text)
                return False
        except Exception as e:
            self.log_test("Update Transaction", False, f"Error: {str(e)}")
            return False
    
    def test_delete_transaction(self):
        """Test deleting a transaction"""
        if len(self.created_transaction_ids) < 2:
            self.log_test("Delete Transaction", False, "Not enough transaction IDs for testing")
            return False
        
        transaction_id = self.created_transaction_ids[-1]  # Delete the last one
        
        try:
            response = requests.delete(f"{self.base_url}/transactions/{transaction_id}", timeout=10)
            
            if response.status_code == 200:
                self.log_test("Delete Transaction", True, 
                            "Transaction deleted successfully", 
                            f"ID: {transaction_id}")
                return True
            else:
                self.log_test("Delete Transaction", False, 
                            f"Status code: {response.status_code}", response.text)
                return False
        except Exception as e:
            self.log_test("Delete Transaction", False, f"Error: {str(e)}")
            return False
    
    def test_monthly_stats(self):
        """Test monthly statistics endpoint"""
        try:
            response = requests.get(f"{self.base_url}/stats/monthly", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if "monthly_stats" in data and isinstance(data["monthly_stats"], list):
                    self.log_test("Monthly Stats", True, 
                                f"Retrieved monthly statistics", 
                                f"Found {len(data['monthly_stats'])} months of data")
                    return True
                else:
                    self.log_test("Monthly Stats", False, "Invalid response structure")
                    return False
            else:
                self.log_test("Monthly Stats", False, f"Status code: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Monthly Stats", False, f"Error: {str(e)}")
            return False
    
    def test_category_stats(self):
        """Test category statistics endpoint"""
        try:
            response = requests.get(f"{self.base_url}/stats/categories", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if "category_stats" in data and isinstance(data["category_stats"], list):
                    self.log_test("Category Stats", True, 
                                f"Retrieved category statistics", 
                                f"Found {len(data['category_stats'])} categories")
                    return True
                else:
                    self.log_test("Category Stats", False, "Invalid response structure")
                    return False
            else:
                self.log_test("Category Stats", False, f"Status code: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Category Stats", False, f"Error: {str(e)}")
            return False
    
    def test_summary_stats(self):
        """Test summary statistics endpoint"""
        try:
            response = requests.get(f"{self.base_url}/stats/summary", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                required_fields = ["total_income", "total_expenses", "total_balance", 
                                 "current_month_income", "current_month_expenses", 
                                 "current_month_balance", "total_transactions"]
                
                if all(field in data for field in required_fields):
                    self.log_test("Summary Stats", True, 
                                "Retrieved summary statistics", 
                                f"Balance: {data.get('total_balance', 0)}, Transactions: {data.get('total_transactions', 0)}")
                    return True
                else:
                    missing = [f for f in required_fields if f not in data]
                    self.log_test("Summary Stats", False, f"Missing fields: {missing}")
                    return False
            else:
                self.log_test("Summary Stats", False, f"Status code: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Summary Stats", False, f"Error: {str(e)}")
            return False
    
    def test_ai_chat(self):
        """Test AI chat endpoint (should return message about missing API key)"""
        chat_data = {
            "session_id": str(uuid.uuid4()),
            "message": "איך אני יכול לחסוך יותר כסף החודש?"
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/ai/chat",
                json=chat_data,
                timeout=15
            )
            
            if response.status_code == 200:
                data = response.json()
                if "response" in data:
                    # Check if it's the expected API key missing message
                    if "מפתח API" in data["response"] or "API key" in data.get("error", ""):
                        self.log_test("AI Chat", True, 
                                    "AI endpoint working - API key not configured as expected", 
                                    "Returned appropriate message about missing API key")
                        return True
                    else:
                        self.log_test("AI Chat", True, 
                                    "AI endpoint working - got response", 
                                    f"Response: {data['response'][:100]}...")
                        return True
                else:
                    self.log_test("AI Chat", False, "No response field in data")
                    return False
            else:
                self.log_test("AI Chat", False, f"Status code: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("AI Chat", False, f"Error: {str(e)}")
            return False
    
    def test_household_comparison(self):
        """Test household comparison endpoint"""
        try:
            response = requests.get(f"{self.base_url}/comparison/household", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                required_sections = ["user_data", "average_household", "category_comparison"]
                
                if all(section in data for section in required_sections):
                    user_data = data["user_data"]
                    avg_data = data["average_household"]
                    self.log_test("Household Comparison", True, 
                                "Retrieved household comparison data", 
                                f"User income: {user_data.get('income', 0)}, Avg income: {avg_data.get('income', 0)}")
                    return True
                else:
                    missing = [s for s in required_sections if s not in data]
                    self.log_test("Household Comparison", False, f"Missing sections: {missing}")
                    return False
            else:
                self.log_test("Household Comparison", False, f"Status code: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Household Comparison", False, f"Error: {str(e)}")
            return False
    
    def test_categories_endpoint(self):
        """Test categories endpoint"""
        try:
            response = requests.get(f"{self.base_url}/categories", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if "categories" in data and isinstance(data["categories"], list):
                    categories = data["categories"]
                    self.log_test("Categories API", True, 
                                f"Retrieved {len(categories)} categories", 
                                f"Sample categories: {[c.get('name', 'N/A') for c in categories[:3]]}")
                    return True
                else:
                    self.log_test("Categories API", False, "Invalid response structure")
                    return False
            else:
                self.log_test("Categories API", False, f"Status code: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Categories API", False, f"Error: {str(e)}")
            return False
    
    def run_all_tests(self):
        """Run all backend tests"""
        print("=" * 60)
        print("BUDGET APP BACKEND API TESTING")
        print("=" * 60)
        print(f"Testing backend at: {self.base_url}")
        print()
        
        # Test sequence
        tests = [
            ("Health Check", self.test_health_check),
            ("Categories API", self.test_categories_endpoint),
            ("Create Transactions", self.test_create_transaction),
            ("Get Transactions", self.test_get_transactions),
            ("Update Transaction", self.test_update_transaction),
            ("Delete Transaction", self.test_delete_transaction),
            ("Monthly Statistics", self.test_monthly_stats),
            ("Category Statistics", self.test_category_stats),
            ("Summary Statistics", self.test_summary_stats),
            ("AI Chat Integration", self.test_ai_chat),
            ("Household Comparison", self.test_household_comparison),
        ]
        
        passed = 0
        total = len(tests)
        
        for test_name, test_func in tests:
            print(f"\n--- Testing {test_name} ---")
            if test_func():
                passed += 1
        
        # Summary
        print("\n" + "=" * 60)
        print("TEST SUMMARY")
        print("=" * 60)
        print(f"Total Tests: {total}")
        print(f"Passed: {passed}")
        print(f"Failed: {total - passed}")
        print(f"Success Rate: {(passed/total)*100:.1f}%")
        
        # Detailed results
        print("\nDETAILED RESULTS:")
        for result in self.test_results:
            status = "✅" if result["success"] else "❌"
            print(f"{status} {result['test']}: {result['message']}")
        
        return passed == total

if __name__ == "__main__":
    tester = BudgetAppTester()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)