#!/usr/bin/env python3
"""
Example: Single-Purpose LLM System
HTML Analysis → Scraping Strategy Generation
"""

import asyncio
import time
from iwsa.config import Settings
from iwsa.llm.hub import LLMHub


async def main():
    """Demonstrate the simplified LLM system"""
    
    print("🤖 Single-Purpose LLM System Demo")
    print("=" * 50)
    
    # Initialize settings and LLM hub
    settings = Settings()
    llm_hub = LLMHub(settings)
    
    # Example HTML content (job listing page)
    html_content = """
    <html>
    <body>
        <div class="job-listings">
            <div class="job-card" data-job-id="1">
                <h3 class="job-title">Senior Python Developer</h3>
                <div class="company-name">TechCorp Inc.</div>
                <div class="location">San Francisco, CA</div>
                <div class="salary">$120,000 - $150,000</div>
                <div class="job-type">Full-time</div>
                <p class="description">Looking for an experienced Python developer...</p>
            </div>
            <div class="job-card" data-job-id="2">
                <h3 class="job-title">Data Scientist</h3>
                <div class="company-name">DataFlow Analytics</div>
                <div class="location">Remote</div>
                <div class="salary">$100,000 - $130,000</div>
                <div class="job-type">Full-time</div>
                <p class="description">Join our data science team...</p>
            </div>
        </div>
        
        <div class="pagination">
            <a href="?page=1" class="page-link current">1</a>
            <a href="?page=2" class="page-link">2</a>
            <a href="?page=3" class="page-link">3</a>
            <a href="?page=next" class="next-btn">Next →</a>
        </div>
        
        <div class="filters">
            <select id="location-filter">
                <option value="">All Locations</option>
                <option value="san-francisco">San Francisco</option>
                <option value="remote">Remote</option>
            </select>
            <select id="salary-filter">
                <option value="">All Salaries</option>
                <option value="100k+">$100k+</option>
                <option value="150k+">$150k+</option>
            </select>
        </div>
    </body>
    </html>
    """
    
    # User intent
    user_intent = "Extract job listings with title, company, location, salary, and job type"
    url = "https://example-jobs.com/listings"
    extraction_fields = ["title", "company", "location", "salary", "job_type"]
    
    print(f"📄 Analyzing HTML content ({len(html_content)} chars)")
    print(f"🎯 User Intent: {user_intent}")
    print(f"🔗 URL: {url}")
    print(f"📋 Fields: {', '.join(extraction_fields)}")
    print()
    
    # Check provider status
    print("🔍 Provider Status:")
    provider_status = llm_hub.get_provider_status()
    for provider, status in provider_status.items():
        available = "✅" if status["available"] else "❌"
        priority = status.get("priority", -1)
        print(f"  {available} {provider.upper():<12} (Priority: {priority}, CB: {status['circuit_breaker_state']})")
    print()
    
    # Estimate cost
    estimated_cost = llm_hub.estimate_cost(html_content, user_intent)
    print(f"💰 Estimated Cost: ${estimated_cost:.4f}")
    print()
    
    # Generate scraping strategy
    print("🧠 Generating Scraping Strategy...")
    start_time = time.time()
    
    strategy = await llm_hub.generate_scraping_strategy(
        html_content=html_content,
        url=url,
        user_intent=user_intent,
        extraction_fields=extraction_fields
    )
    
    response_time = time.time() - start_time
    
    # Display results
    print(f"⏱️  Response Time: {response_time:.2f}s")
    print(f"🎯 Success: {strategy.success}")
    print(f"🤖 Provider Used: {strategy.provider_used.upper()}")
    print(f"💰 Actual Cost: ${strategy.cost:.4f}")
    print(f"📊 Confidence: {strategy.confidence_score:.2f}")
    print()
    
    if strategy.success:
        print("📋 SCRAPING STRATEGY:")
        print("-" * 30)
        
        print("🎯 CSS Selectors:")
        for i, selector in enumerate(strategy.selectors, 1):
            print(f"  {i}. {selector}")
        print()
        
        print("🔄 Extraction Logic:")
        print(f"  {strategy.extraction_logic}")
        print()
        
        if strategy.pagination_strategy:
            print("📄 Pagination Strategy:")
            pag = strategy.pagination_strategy
            print(f"  Type: {pag.get('type', 'unknown')}")
            print(f"  Selectors: {pag.get('selectors', [])}")
            print(f"  Logic: {pag.get('logic', 'N/A')}")
            print()
        
        if strategy.filters:
            print("🔧 Detected Filters:")
            for i, filter_item in enumerate(strategy.filters, 1):
                print(f"  {i}. {filter_item.get('name', 'Unknown')} ({filter_item.get('type', 'unknown')})")
                print(f"     Selector: {filter_item.get('selector', 'N/A')}")
            print()
        
        if strategy.error_handling:
            print("⚠️  Error Handling:")
            for i, strategy_item in enumerate(strategy.error_handling, 1):
                print(f"  {i}. {strategy_item}")
            print()
        
        print("💭 AI Reasoning:")
        print(f"  {strategy.reasoning}")
        
    else:
        print("❌ STRATEGY GENERATION FAILED:")
        print(f"   Reason: {strategy.reasoning}")
    
    print()
    print("🔍 Health Check:")
    health = await llm_hub.health_check()
    print(f"  Overall Health: {health['overall_health'].upper()}")
    print(f"  Primary Provider: {health.get('primary_provider', 'None').upper()}")
    
    for provider, status in health["providers"].items():
        health_icon = {"healthy": "✅", "degraded": "⚠️", "unavailable": "❌", "timeout": "⏱️", "error": "💥"}.get(status["status"], "❓")
        print(f"  {health_icon} {provider.upper()}: {status['status']}")
        if "response_time" in status:
            print(f"     Response Time: {status['response_time']:.2f}s")
        if status.get("error"):
            print(f"     Error: {status['error']}")


async def demonstrate_provider_fallback():
    """Demonstrate provider fallback mechanism"""
    print("\n🔄 PROVIDER FALLBACK DEMONSTRATION")
    print("=" * 50)
    
    settings = Settings()
    llm_hub = LLMHub(settings)
    
    # Simple HTML for quick testing
    simple_html = "<div class='product'><h1>Product Title</h1><span class='price'>$99</span></div>"
    
    print("Testing provider fallback with simple HTML...")
    
    # First request (should use primary provider)
    strategy1 = await llm_hub.generate_scraping_strategy(
        html_content=simple_html,
        url="https://example.com/product",
        user_intent="Extract product title and price"
    )
    
    print(f"Request 1: {strategy1.provider_used.upper()} - {strategy1.response_time:.2f}s")
    
    # Second request (may use different provider based on availability)
    strategy2 = await llm_hub.generate_scraping_strategy(
        html_content=simple_html,
        url="https://example.com/product2", 
        user_intent="Extract product information"
    )
    
    print(f"Request 2: {strategy2.provider_used.upper()} - {strategy2.response_time:.2f}s")
    
    # Show final provider status
    status = llm_hub.get_provider_status()
    print("\nFinal Provider Status:")
    for provider, info in status.items():
        print(f"  {provider.upper()}: {info['circuit_breaker_state']} (failures: {info['failure_count']})")


async def benchmark_performance():
    """Benchmark LLM system performance"""
    print("\n⚡ PERFORMANCE BENCHMARK")
    print("=" * 50)
    
    settings = Settings()
    llm_hub = LLMHub(settings)
    
    # Test different HTML sizes
    test_cases = [
        ("Small", "<div class='item'><h1>Title</h1></div>"),
        ("Medium", "<div class='items'>" + "<div class='item'><h1>Title</h1><p>Description</p></div>" * 10 + "</div>"),
        ("Large", "<div class='items'>" + "<div class='item'><h1>Title</h1><p>Long description with more content</p></div>" * 50 + "</div>")
    ]
    
    results = []
    
    for size_name, html in test_cases:
        print(f"Testing {size_name} HTML ({len(html)} chars)...")
        
        start_time = time.time()
        strategy = await llm_hub.generate_scraping_strategy(
            html_content=html,
            url="https://example.com",
            user_intent="Extract items"
        )
        response_time = time.time() - start_time
        
        results.append({
            "size": size_name,
            "chars": len(html),
            "time": response_time,
            "provider": strategy.provider_used,
            "success": strategy.success,
            "cost": strategy.cost
        })
        
        print(f"  ✅ {response_time:.2f}s - {strategy.provider_used.upper()}")
    
    print("\nBenchmark Results:")
    print("Size    | Chars  | Time    | Provider   | Cost")
    print("-" * 45)
    for result in results:
        print(f"{result['size']:<7} | {result['chars']:<6} | {result['time']:.2f}s   | {result['provider']:<10} | ${result['cost']:.4f}")


if __name__ == "__main__":
    asyncio.run(main())
    asyncio.run(demonstrate_provider_fallback())
    asyncio.run(benchmark_performance())