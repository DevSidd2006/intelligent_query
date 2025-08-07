#!/usr/bin/env python3
"""
Performance Testing Script for Intelligent Query API
Tests the complete pipeline and measures timing for each component
"""

import time
import requests
import json
import statistics
from typing import List, Dict, Any
import argparse
from datetime import datetime
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class PerformanceTester:
    def __init__(self, base_url: str = "http://localhost:3000", bearer_token: str = None):
        self.base_url = base_url.rstrip('/')
        self.bearer_token = bearer_token or os.getenv('HACKRX_BEARER_TOKEN')
        self.results = []
        
        # Test document and questions
        self.test_document = "https://hackrx.blob.core.windows.net/assets/policy.pdf?sv=2023-01-03&st=2025-07-04T09%3A11%3A24Z&se=2027-07-05T09%3A11%3A00Z&sr=b&sp=r&sig=N4a9OU0w0QXO6AOIBiu4bpl7AXvEZogeT%2FjUHNO7HzQ%3D"
        
        # Test questions of varying complexity
        self.test_questions = [
            "What is the grace period for premium payment?",
            "What is the waiting period for pre-existing diseases?", 
            "Does this policy cover maternity expenses?",
            "What is the No Claim Discount offered?",
            "Are there any sub-limits on room rent for Plan A?",
            "What is the extent of coverage for AYUSH treatments?",
            "How does the policy define a Hospital?",
            "What is the waiting period for cataract surgery?",
            "Are medical expenses for organ donors covered?",
            "Is there a benefit for preventive health check-ups?"
        ]

    def test_health_endpoint(self) -> Dict[str, Any]:
        """Test the health endpoint"""
        print("🔍 Testing health endpoint...")
        start_time = time.time()
        
        try:
            response = requests.get(f"{self.base_url}/health", timeout=30)
            elapsed_time = time.time() - start_time
            
            result = {
                "endpoint": "health",
                "status_code": response.status_code,
                "response_time": elapsed_time,
                "success": response.status_code == 200,
                "response_data": response.json() if response.status_code == 200 else None,
                "error": None
            }
            
            if result["success"]:
                print(f"✅ Health check passed in {elapsed_time:.2f}s")
            else:
                print(f"❌ Health check failed: {response.status_code}")
                
        except Exception as e:
            elapsed_time = time.time() - start_time
            result = {
                "endpoint": "health",
                "status_code": None,
                "response_time": elapsed_time,
                "success": False,
                "response_data": None,
                "error": str(e)
            }
            print(f"❌ Health check error: {e}")
        
        return result

    def test_single_question(self, question: str) -> Dict[str, Any]:
        """Test API with a single question"""
        print(f"📝 Testing question: {question[:50]}...")
        start_time = time.time()
        
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'Authorization': f'Bearer {self.bearer_token}'
        }
        
        payload = {
            "documents": self.test_document,
            "questions": [question]
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/hackrx/run",
                headers=headers,
                json=payload,
                timeout=120  # 2 minute timeout
            )
            
            elapsed_time = time.time() - start_time
            
            result = {
                "question": question,
                "status_code": response.status_code,
                "response_time": elapsed_time,
                "success": response.status_code == 200,
                "response_data": response.json() if response.status_code == 200 else None,
                "error": None,
                "answer_length": 0
            }
            
            if result["success"] and result["response_data"]:
                answers = result["response_data"].get("answers", [])
                if answers:
                    result["answer_length"] = len(answers[0])
                    print(f"✅ Question answered in {elapsed_time:.2f}s")
                    print(f"   Answer: {answers[0][:100]}...")
                else:
                    print(f"⚠️  No answers in response")
            else:
                print(f"❌ Question failed: {response.status_code}")
                if response.status_code != 200:
                    print(f"   Error: {response.text}")
                    
        except Exception as e:
            elapsed_time = time.time() - start_time
            result = {
                "question": question,
                "status_code": None,
                "response_time": elapsed_time,
                "success": False,
                "response_data": None,
                "error": str(e),
                "answer_length": 0
            }
            print(f"❌ Question error: {e}")
        
        return result

    def test_multiple_questions(self, questions: List[str]) -> Dict[str, Any]:
        """Test API with multiple questions at once"""
        print(f"📚 Testing {len(questions)} questions simultaneously...")
        start_time = time.time()
        
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'Authorization': f'Bearer {self.bearer_token}'
        }
        
        payload = {
            "documents": self.test_document,
            "questions": questions
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/hackrx/run",
                headers=headers,
                json=payload,
                timeout=300  # 5 minute timeout for multiple questions
            )
            
            elapsed_time = time.time() - start_time
            
            result = {
                "test_type": "multiple_questions",
                "question_count": len(questions),
                "status_code": response.status_code,
                "response_time": elapsed_time,
                "success": response.status_code == 200,
                "response_data": response.json() if response.status_code == 200 else None,
                "error": None,
                "avg_time_per_question": elapsed_time / len(questions),
                "total_answer_length": 0
            }
            
            if result["success"] and result["response_data"]:
                answers = result["response_data"].get("answers", [])
                result["total_answer_length"] = sum(len(answer) for answer in answers)
                print(f"✅ {len(answers)} questions answered in {elapsed_time:.2f}s")
                print(f"   Average time per question: {result['avg_time_per_question']:.2f}s")
            else:
                print(f"❌ Multiple questions failed: {response.status_code}")
                if response.status_code != 200:
                    print(f"   Error: {response.text}")
                    
        except Exception as e:
            elapsed_time = time.time() - start_time
            result = {
                "test_type": "multiple_questions",
                "question_count": len(questions),
                "status_code": None,
                "response_time": elapsed_time,
                "success": False,
                "response_data": None,
                "error": str(e),
                "avg_time_per_question": elapsed_time / len(questions),
                "total_answer_length": 0
            }
            print(f"❌ Multiple questions error: {e}")
        
        return result

    def run_comprehensive_test(self, iterations: int = 1) -> Dict[str, Any]:
        """Run comprehensive performance testing"""
        print(f"\n🚀 Starting Comprehensive Performance Test")
        print(f"📊 Iterations: {iterations}")
        print(f"🌐 API URL: {self.base_url}")
        print(f"📅 Test Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)
        
        all_results = {
            "test_info": {
                "start_time": datetime.now().isoformat(),
                "api_url": self.base_url,
                "iterations": iterations,
                "total_questions": len(self.test_questions)
            },
            "health_tests": [],
            "single_question_tests": [],
            "multiple_question_tests": [],
            "summary": {}
        }
        
        # Test health endpoint
        health_result = self.test_health_endpoint()
        all_results["health_tests"].append(health_result)
        
        if not health_result["success"]:
            print("❌ Health check failed. Stopping tests.")
            return all_results
        
        print("\n" + "=" * 60)
        
        for iteration in range(iterations):
            if iterations > 1:
                print(f"\n🔄 Iteration {iteration + 1}/{iterations}")
            
            # Test individual questions
            print(f"\n📝 Testing Individual Questions...")
            for i, question in enumerate(self.test_questions):
                print(f"\n  Question {i+1}/{len(self.test_questions)}")
                result = self.test_single_question(question)
                result["iteration"] = iteration
                all_results["single_question_tests"].append(result)
                
                # Small delay between questions
                time.sleep(1)
            
            # Test multiple questions
            print(f"\n📚 Testing All Questions Together...")
            multi_result = self.test_multiple_questions(self.test_questions)
            multi_result["iteration"] = iteration
            all_results["multiple_question_tests"].append(multi_result)
        
        # Calculate summary statistics
        all_results["summary"] = self.calculate_summary(all_results)
        
        print("\n" + "=" * 60)
        print("📊 PERFORMANCE SUMMARY")
        print("=" * 60)
        self.print_summary(all_results["summary"])
        
        return all_results

    def calculate_summary(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate summary statistics"""
        single_tests = [t for t in results["single_question_tests"] if t["success"]]
        multi_tests = [t for t in results["multiple_question_tests"] if t["success"]]
        
        summary = {
            "health_check": {
                "success_rate": len([t for t in results["health_tests"] if t["success"]]) / len(results["health_tests"]) * 100,
                "avg_response_time": statistics.mean([t["response_time"] for t in results["health_tests"]])
            },
            "single_questions": {
                "total_tests": len(results["single_question_tests"]),
                "successful_tests": len(single_tests),
                "success_rate": len(single_tests) / len(results["single_question_tests"]) * 100 if results["single_question_tests"] else 0,
                "avg_response_time": statistics.mean([t["response_time"] for t in single_tests]) if single_tests else 0,
                "min_response_time": min([t["response_time"] for t in single_tests]) if single_tests else 0,
                "max_response_time": max([t["response_time"] for t in single_tests]) if single_tests else 0,
                "avg_answer_length": statistics.mean([t["answer_length"] for t in single_tests]) if single_tests else 0
            },
            "multiple_questions": {
                "total_tests": len(results["multiple_question_tests"]),
                "successful_tests": len(multi_tests),
                "success_rate": len(multi_tests) / len(results["multiple_question_tests"]) * 100 if results["multiple_question_tests"] else 0,
                "avg_response_time": statistics.mean([t["response_time"] for t in multi_tests]) if multi_tests else 0,
                "avg_time_per_question": statistics.mean([t["avg_time_per_question"] for t in multi_tests]) if multi_tests else 0,
                "avg_total_answer_length": statistics.mean([t["total_answer_length"] for t in multi_tests]) if multi_tests else 0
            }
        }
        
        return summary

    def print_summary(self, summary: Dict[str, Any]):
        """Print formatted summary"""
        print(f"🏥 Health Check:")
        print(f"   Success Rate: {summary['health_check']['success_rate']:.1f}%")
        print(f"   Avg Response Time: {summary['health_check']['avg_response_time']:.2f}s")
        
        print(f"\n📝 Single Questions:")
        print(f"   Total Tests: {summary['single_questions']['total_tests']}")
        print(f"   Success Rate: {summary['single_questions']['success_rate']:.1f}%")
        print(f"   Avg Response Time: {summary['single_questions']['avg_response_time']:.2f}s")
        print(f"   Min Response Time: {summary['single_questions']['min_response_time']:.2f}s")
        print(f"   Max Response Time: {summary['single_questions']['max_response_time']:.2f}s")
        print(f"   Avg Answer Length: {summary['single_questions']['avg_answer_length']:.0f} chars")
        
        print(f"\n📚 Multiple Questions:")
        print(f"   Total Tests: {summary['multiple_questions']['total_tests']}")
        print(f"   Success Rate: {summary['multiple_questions']['success_rate']:.1f}%")
        print(f"   Avg Total Time: {summary['multiple_questions']['avg_response_time']:.2f}s")
        print(f"   Avg Time Per Question: {summary['multiple_questions']['avg_time_per_question']:.2f}s")
        print(f"   Avg Total Answer Length: {summary['multiple_questions']['avg_total_answer_length']:.0f} chars")

    def save_results(self, results: Dict[str, Any], filename: str = None):
        """Save results to JSON file"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"performance_test_results_{timestamp}.json"
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, default=str)
        
        print(f"\n💾 Results saved to: {filename}")

def main():
    parser = argparse.ArgumentParser(description="Performance test for Intelligent Query API")
    parser.add_argument("--url", default="http://localhost:3000", help="API base URL")
    parser.add_argument("--token", help="Bearer token (or set HACKRX_BEARER_TOKEN env var)")
    parser.add_argument("--iterations", type=int, default=1, help="Number of test iterations")
    parser.add_argument("--save", action="store_true", help="Save results to JSON file")
    parser.add_argument("--quick", action="store_true", help="Run quick test (fewer questions)")
    
    args = parser.parse_args()
    
    # Initialize tester
    tester = PerformanceTester(base_url=args.url, bearer_token=args.token)
    
    if args.quick:
        # Use only first 3 questions for quick test
        tester.test_questions = tester.test_questions[:3]
        print("🏃 Running quick test mode (3 questions)")
    
    # Check if bearer token is available
    if not tester.bearer_token:
        print("❌ No bearer token provided. Set HACKRX_BEARER_TOKEN env var or use --token")
        return
    
    # Run tests
    results = tester.run_comprehensive_test(iterations=args.iterations)
    
    # Save results if requested
    if args.save:
        tester.save_results(results)
    
    print(f"\n✅ Performance testing completed!")

if __name__ == "__main__":
    main()
