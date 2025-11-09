#!/usr/bin/env python3
"""
Advanced API Testing Script for Bedrock Access Gateway
Usage: python scripts/test_api.py
"""

import asyncio
import aiohttp
import json
import time
import sys
from pathlib import Path
from typing import Dict, List, Any
from dataclasses import dataclass
from datetime import datetime

# Configuration
BASE_URL = "http://localhost:8000"
API_KEY = "bedrock"
TEST_DIR = Path("test")

@dataclass
class TestResult:
    name: str
    status: str  # PASS, FAIL, ERROR
    duration_ms: float
    response_code: int = 0
    error_message: str = ""
    response_data: Dict = None

class APITester:
    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url
        self.api_key = api_key
        self.results: List[TestResult] = []
        
    async def run_test(self, name: str, method: str, endpoint: str, 
                      data: Dict = None, headers: Dict = None) -> TestResult:
        """Run a single API test"""
        print(f"\n📋 Testing: {name}")
        
        # Prepare headers
        test_headers = headers or {}
        
        start_time = time.time()
        
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.base_url}{endpoint}"
                
                if method == "GET":
                    async with session.get(url, headers=test_headers) as response:
                        response_data = await response.json() if response.content_type == 'application/json' else await response.text()
                        duration_ms = (time.time() - start_time) * 1000
                        
                        if response.status == 200:
                            print(f"✅ PASS - {name} ({duration_ms:.0f}ms)")
                            result = TestResult(name, "PASS", duration_ms, response.status, response_data=response_data)
                        else:
                            print(f"❌ FAIL - {name} (HTTP {response.status})")
                            result = TestResult(name, "FAIL", duration_ms, response.status, str(response_data))
                            
                elif method == "POST":
                    async with session.post(url, json=data, headers=test_headers) as response:
                        response_data = await response.json() if response.content_type == 'application/json' else await response.text()
                        duration_ms = (time.time() - start_time) * 1000
                        
                        if response.status == 200:
                            print(f"✅ PASS - {name} ({duration_ms:.0f}ms)")
                            result = TestResult(name, "PASS", duration_ms, response.status, response_data=response_data)
                        else:
                            print(f"❌ FAIL - {name} (HTTP {response.status})")
                            result = TestResult(name, "FAIL", duration_ms, response.status, str(response_data))
                            
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            print(f"❌ ERROR - {name}: {str(e)}")
            result = TestResult(name, "ERROR", duration_ms, error_message=str(e))
            
        self.results.append(result)
        return result
    
    def load_test_data(self, filename: str) -> Dict:
        """Load test data from JSON file"""
        file_path = TEST_DIR / filename
        if not file_path.exists():
            raise FileNotFoundError(f"Test file not found: {file_path}")
        
        with open(file_path, 'r') as f:
            return json.load(f)
    
    async def run_all_tests(self):
        """Run all API tests"""
        print("🚀 Starting Bedrock Access Gateway API Tests...")
        print(f"📂 Using test directory: {TEST_DIR}")
        print(f"🌐 API Base URL: {BASE_URL}")
        
        # Load test data
        try:
            chat_data = self.load_test_data("test_chat.json")
            text_embedding_data = self.load_test_data("test_text_embedding.json")
            image_embedding_data = self.load_test_data("test_image_embedding.json")
        except FileNotFoundError as e:
            print(f"❌ {e}")
            sys.exit(1)
        
        # Test 1: Health Check
        await self.run_test(
            "Health Check",
            "GET",
            "/health"
        )
        
        # Test 2: Chat API (GPT-4)
        await self.run_test(
            "Chat API (GPT-4)",
            "POST",
            "/openai/deployments/gpt-4/chat/completions?api-version=2024-02-15-preview",
            chat_data,
            {
                "Content-Type": "application/json",
                "api-key": self.api_key
            }
        )
        
        # Test 3: Chat API (GPT-3.5)
        await self.run_test(
            "Chat API (GPT-3.5)",
            "POST", 
            "/openai/deployments/gpt-35-turbo/chat/completions?api-version=2024-02-15-preview",
            chat_data,
            {
                "Content-Type": "application/json",
                "api-key": self.api_key
            }
        )
        
        # Test 4: Text Embedding (Azure Style)
        await self.run_test(
            "Text Embedding (Azure)",
            "POST",
            "/openai/deployments/text-embedding-ada-002/embeddings?api-version=2024-02-15-preview",
            text_embedding_data,
            {
                "Content-Type": "application/json",
                "api-key": self.api_key
            }
        )
        
        # Test 5: Image Embedding (Titan)
        await self.run_test(
            "Image Embedding (Titan)",
            "POST",
            "/openai/deployments/vision-embedding/embeddings?api-version=2024-05-01-preview",
            image_embedding_data,
            {
                "Content-Type": "application/json",
                "api-key": self.api_key
            }
        )
        
        # Test 6: Image Embedding (TwelveLabs)
        await self.run_test(
            "Image Embedding (TwelveLabs)",
            "POST",
            "/openai/deployments/vision-embedding/embeddings?api-version=2024-02-15-preview",
            image_embedding_data,
            {
                "Content-Type": "application/json",
                "api-key": self.api_key
            }
        )
        
        # Test 7: Model List
        await self.run_test(
            "Model List",
            "GET",
            "/v1/models",
            headers={"api-key": self.api_key}
        )
        
        # Test 8: Direct Bedrock Chat
        await self.run_test(
            "Direct Bedrock Chat",
            "POST",
            "/api/v1/chat/completions",
            chat_data,
            {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}"
            }
        )
    
    def print_summary(self):
        """Print test results summary"""
        pass_count = len([r for r in self.results if r.status == "PASS"])
        fail_count = len([r for r in self.results if r.status == "FAIL"])
        error_count = len([r for r in self.results if r.status == "ERROR"])
        total_count = len(self.results)
        
        print(f"\n📊 Test Summary:")
        print("================")
        print(f"✅ Passed: {pass_count}")
        print(f"❌ Failed: {fail_count}")
        print(f"⚠️  Errors: {error_count}")
        print(f"📝 Total: {total_count}")
        
        # Show failed/error tests
        failed_tests = [r for r in self.results if r.status != "PASS"]
        if failed_tests:
            print(f"\n❌ Failed/Error Tests:")
            for test in failed_tests:
                print(f"- {test.name}: {test.status}")
                if test.error_message:
                    print(f"  Error: {test.error_message}")
        
        # Performance summary
        passed_tests = [r for r in self.results if r.status == "PASS"]
        if passed_tests:
            avg_duration = sum(t.duration_ms for t in passed_tests) / len(passed_tests)
            print(f"\n⚡ Average Response Time: {avg_duration:.0f}ms")
            
            # Show individual timings
            print(f"\n⏱️  Individual Timings:")
            for test in passed_tests:
                print(f"- {test.name}: {test.duration_ms:.0f}ms")
        
        print(f"\n🎉 Testing completed at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        return fail_count + error_count == 0
    
    def save_results(self, filename: str = "test_results.json"):
        """Save test results to JSON file"""
        results_data = {
            "timestamp": datetime.now().isoformat(),
            "base_url": self.base_url,
            "total_tests": len(self.results),
            "passed": len([r for r in self.results if r.status == "PASS"]),
            "failed": len([r for r in self.results if r.status == "FAIL"]),
            "errors": len([r for r in self.results if r.status == "ERROR"]),
            "tests": [
                {
                    "name": r.name,
                    "status": r.status,
                    "duration_ms": r.duration_ms,
                    "response_code": r.response_code,
                    "error_message": r.error_message
                }
                for r in self.results
            ]
        }
        
        with open(filename, 'w') as f:
            json.dump(results_data, f, indent=2)
        
        print(f"📄 Results saved to {filename}")

async def main():
    """Main function"""
    tester = APITester(BASE_URL, API_KEY)
    
    try:
        await tester.run_all_tests()
        success = tester.print_summary()
        tester.save_results()
        
        sys.exit(0 if success else 1)
        
    except Exception as e:
        print(f"❌ Test execution failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    # Check if required packages are installed
    try:
        import aiohttp
    except ImportError:
        print("❌ aiohttp is required. Install with: pip install aiohttp")
        sys.exit(1)
    
    asyncio.run(main())