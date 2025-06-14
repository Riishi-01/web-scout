#!/usr/bin/env python3
"""
Web Scraping Dataset Preparation for TinyLlama Training
======================================================

This script creates training datasets for fine-tuning TinyLlama on web scraping tasks.
It generates synthetic and real-world examples for:
- CSS selector generation
- Pagination detection
- Filter strategies
- Data extraction patterns

Author: Claude Code Assistant
Date: December 13, 2024
"""

import os
import json
import random
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from urllib.parse import urljoin
import re

import requests
from bs4 import BeautifulSoup, Comment
import pandas as pd
from faker import Faker

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class DatasetConfig:
    """Configuration for dataset generation"""
    output_path: str = "./datasets/webscraping_dataset.jsonl"
    num_synthetic_examples: int = 2000
    num_real_examples: int = 500
    include_edge_cases: bool = True
    include_error_cases: bool = True
    max_html_length: int = 8192
    seed: int = 42


class HTMLTemplateGenerator:
    """Generates HTML templates for different website types"""
    
    def __init__(self, seed: int = 42):
        self.fake = Faker()
        Faker.seed(seed)
        random.seed(seed)
    
    def generate_ecommerce_product(self) -> Tuple[str, Dict[str, Any]]:
        """Generate e-commerce product page HTML and expected extraction"""
        product_name = self.fake.catch_phrase()
        price = f"${random.randint(10, 999)}.{random.randint(10, 99)}"
        description = self.fake.text(max_nb_chars=200)
        rating = round(random.uniform(1, 5), 1)
        reviews_count = random.randint(0, 1000)
        
        # Vary the HTML structure
        structures = [
            # Structure 1: Standard e-commerce
            f"""
            <div class="product-container">
                <div class="product-header">
                    <h1 class="product-title">{product_name}</h1>
                    <div class="price-section">
                        <span class="current-price">{price}</span>
                    </div>
                </div>
                <div class="product-details">
                    <p class="description">{description}</p>
                    <div class="rating">
                        <span class="stars">{rating}</span>
                        <span class="review-count">({reviews_count} reviews)</span>
                    </div>
                </div>
            </div>
            """,
            # Structure 2: Card-based layout
            f"""
            <article class="product-card" data-product-id="{random.randint(1000, 9999)}">
                <header>
                    <h2 class="title">{product_name}</h2>
                </header>
                <div class="content">
                    <div class="pricing">
                        <span class="price">{price}</span>
                    </div>
                    <div class="meta">
                        <p class="desc">{description}</p>
                        <div class="reviews">
                            <span class="rating-value">{rating}</span>
                            <span class="total-reviews">{reviews_count}</span>
                        </div>
                    </div>
                </div>
            </article>
            """,
            # Structure 3: Table-based (legacy)
            f"""
            <table class="product-info">
                <tr>
                    <td class="label">Product:</td>
                    <td class="product-name">{product_name}</td>
                </tr>
                <tr>
                    <td class="label">Price:</td>
                    <td class="product-price">{price}</td>
                </tr>
                <tr>
                    <td class="label">Description:</td>
                    <td class="product-desc">{description}</td>
                </tr>
                <tr>
                    <td class="label">Rating:</td>
                    <td class="product-rating">{rating} ({reviews_count} reviews)</td>
                </tr>
            </table>
            """
        ]
        
        html = random.choice(structures)
        
        expected = {
            "selectors": {
                "title": [".product-title", ".title", ".product-name"],
                "price": [".current-price", ".price", ".product-price"],
                "description": [".description", ".desc", ".product-desc"],
                "rating": [".stars", ".rating-value", ".product-rating"],
                "reviews": [".review-count", ".total-reviews", ".product-rating"]
            },
            "extraction_strategy": "Extract product information from e-commerce page",
            "data_fields": ["title", "price", "description", "rating", "reviews"],
            "confidence": 0.95
        }
        
        return html.strip(), expected
    
    def generate_job_listing(self) -> Tuple[str, Dict[str, Any]]:
        """Generate job listing HTML and expected extraction"""
        job_title = self.fake.job()
        company = self.fake.company()
        location = f"{self.fake.city()}, {self.fake.state()}"
        salary = f"${random.randint(40, 150)}k - ${random.randint(60, 200)}k"
        description = self.fake.text(max_nb_chars=300)
        
        structures = [
            f"""
            <div class="job-posting">
                <div class="job-header">
                    <h1 class="job-title">{job_title}</h1>
                    <h2 class="company-name">{company}</h2>
                    <div class="job-meta">
                        <span class="location">{location}</span>
                        <span class="salary">{salary}</span>
                    </div>
                </div>
                <div class="job-description">
                    <p>{description}</p>
                </div>
            </div>
            """,
            f"""
            <article class="listing" data-job-id="{random.randint(1000, 9999)}">
                <header class="listing-header">
                    <h3 class="position">{job_title}</h3>
                    <div class="employer">{company}</div>
                </header>
                <div class="details">
                    <div class="location-info">{location}</div>
                    <div class="compensation">{salary}</div>
                    <div class="summary">{description}</div>
                </div>
            </article>
            """
        ]
        
        html = random.choice(structures)
        
        expected = {
            "selectors": {
                "title": [".job-title", ".position"],
                "company": [".company-name", ".employer"],
                "location": [".location", ".location-info"],
                "salary": [".salary", ".compensation"],
                "description": [".job-description p", ".summary"]
            },
            "extraction_strategy": "Extract job posting details from listing page",
            "data_fields": ["title", "company", "location", "salary", "description"],
            "confidence": 0.92
        }
        
        return html.strip(), expected
    
    def generate_pagination_examples(self) -> List[Tuple[str, Dict[str, Any]]]:
        """Generate pagination HTML examples"""
        examples = []
        
        # Numbered pagination
        pagination_html = """
        <div class="pagination">
            <a href="?page=1" class="page-link">1</a>
            <a href="?page=2" class="page-link current">2</a>
            <a href="?page=3" class="page-link">3</a>
            <a href="?page=4" class="page-link">Next</a>
        </div>
        """
        
        expected = {
            "pagination_type": "numbered",
            "selectors": {
                "next_button": [".page-link:contains('Next')", "a[href*='page=']:last"],
                "page_links": [".page-link", ".pagination a"],
                "current_page": [".current", ".active"]
            },
            "strategy": "Click numbered pagination links to navigate",
            "confidence": 0.98
        }
        examples.append((pagination_html.strip(), expected))
        
        # Load more button
        load_more_html = """
        <div class="load-more-container">
            <button class="load-more-btn" data-next-page="3">Load More Results</button>
        </div>
        """
        
        expected = {
            "pagination_type": "load_more",
            "selectors": {
                "load_button": [".load-more-btn", "button:contains('Load More')"],
                "trigger_element": ["[data-next-page]"]
            },
            "strategy": "Click load more button to fetch additional content",
            "confidence": 0.95
        }
        examples.append((load_more_html.strip(), expected))
        
        # Infinite scroll
        infinite_scroll_html = """
        <div class="content-container" data-infinite-scroll="true">
            <div class="results-list">
                <!-- Results here -->
            </div>
            <div class="loading-indicator" style="display: none;">Loading...</div>
        </div>
        """
        
        expected = {
            "pagination_type": "infinite_scroll",
            "selectors": {
                "container": ["[data-infinite-scroll]", ".content-container"],
                "loading_indicator": [".loading-indicator", ".spinner"],
                "results_container": [".results-list", ".items"]
            },
            "strategy": "Scroll to bottom to trigger infinite loading",
            "confidence": 0.88
        }
        examples.append((infinite_scroll_html.strip(), expected))
        
        return examples
    
    def generate_filter_examples(self) -> List[Tuple[str, Dict[str, Any]]]:
        """Generate filter/search HTML examples"""
        examples = []
        
        # Price range filter
        price_filter_html = """
        <div class="filters">
            <div class="price-filter">
                <label>Price Range</label>
                <input type="range" class="price-min" name="min_price" min="0" max="1000" value="100">
                <input type="range" class="price-max" name="max_price" min="0" max="1000" value="500">
            </div>
            <button class="apply-filters">Apply Filters</button>
        </div>
        """
        
        expected = {
            "filter_type": "price_range",
            "selectors": {
                "min_price": [".price-min", "input[name='min_price']"],
                "max_price": [".price-max", "input[name='max_price']"],
                "apply_button": [".apply-filters", "button:contains('Apply')"]
            },
            "strategy": "Set price range values and click apply",
            "interaction_steps": [
                "Set minimum price slider",
                "Set maximum price slider", 
                "Click apply filters button"
            ],
            "confidence": 0.93
        }
        examples.append((price_filter_html.strip(), expected))
        
        # Category dropdown
        category_filter_html = """
        <div class="filter-section">
            <select class="category-filter" name="category">
                <option value="">All Categories</option>
                <option value="electronics">Electronics</option>
                <option value="clothing">Clothing</option>
                <option value="books">Books</option>
            </select>
            <input type="text" class="search-input" placeholder="Search products...">
            <button class="search-btn">Search</button>
        </div>
        """
        
        expected = {
            "filter_type": "category_search",
            "selectors": {
                "category_dropdown": [".category-filter", "select[name='category']"],
                "search_input": [".search-input", "input[type='text']"],
                "search_button": [".search-btn", "button:contains('Search')"]
            },
            "strategy": "Select category and enter search term",
            "interaction_steps": [
                "Select category from dropdown",
                "Enter search term in input field",
                "Click search button"
            ],
            "confidence": 0.96
        }
        examples.append((category_filter_html.strip(), expected))
        
        return examples


class WebScrapingDatasetGenerator:
    """Main dataset generator for web scraping training data"""
    
    def __init__(self, config: DatasetConfig):
        self.config = config
        self.html_generator = HTMLTemplateGenerator(config.seed)
        self.examples = []
    
    def generate_css_selector_examples(self, num_examples: int) -> List[Dict[str, Any]]:
        """Generate CSS selector training examples"""
        examples = []
        
        for i in range(num_examples // 3):
            # Product examples
            html, expected = self.html_generator.generate_ecommerce_product()
            example = {
                "instruction": "Generate CSS selectors to extract product information from the following HTML",
                "input": html,
                "output": expected,
                "task_type": "css_selector_generation",
                "domain": "ecommerce"
            }
            examples.append(example)
            
            # Job listing examples
            html, expected = self.html_generator.generate_job_listing()
            example = {
                "instruction": "Generate CSS selectors to extract job posting details from the following HTML",
                "input": html,
                "output": expected,
                "task_type": "css_selector_generation",
                "domain": "jobs"
            }
            examples.append(example)
            
            # Create variation with different instruction
            example_variant = {
                "instruction": "Analyze this HTML structure and provide CSS selectors for data extraction",
                "input": html,
                "output": expected,
                "task_type": "css_selector_generation",
                "domain": "jobs"
            }
            examples.append(example_variant)
        
        return examples
    
    def generate_pagination_examples(self) -> List[Dict[str, Any]]:
        """Generate pagination detection examples"""
        examples = []
        
        pagination_cases = self.html_generator.generate_pagination_examples()
        
        for html, expected in pagination_cases:
            example = {
                "instruction": "Analyze this HTML and determine the pagination strategy",
                "input": html,
                "output": expected,
                "task_type": "pagination_detection",
                "domain": "general"
            }
            examples.append(example)
            
            # Create variant with different instruction
            variant = {
                "instruction": "Identify pagination elements and suggest navigation strategy",
                "input": html,
                "output": expected,
                "task_type": "pagination_detection", 
                "domain": "general"
            }
            examples.append(variant)
        
        return examples
    
    def generate_filter_examples(self) -> List[Dict[str, Any]]:
        """Generate filter interaction examples"""
        examples = []
        
        filter_cases = self.html_generator.generate_filter_examples()
        
        for html, expected in filter_cases:
            example = {
                "instruction": "Analyze this filter interface and provide interaction strategy",
                "input": html,
                "output": expected,
                "task_type": "filter_interaction",
                "domain": "general"
            }
            examples.append(example)
            
            # Create variant focusing on selectors
            variant = {
                "instruction": "Extract CSS selectors for filter elements and describe interaction steps",
                "input": html,
                "output": expected,
                "task_type": "filter_interaction",
                "domain": "general"
            }
            examples.append(variant)
        
        return examples
    
    def generate_error_cases(self) -> List[Dict[str, Any]]:
        """Generate examples for error handling scenarios"""
        examples = []
        
        # Missing elements
        broken_html = """
        <div class="product-container">
            <h1 class="title">Product Name</h1>
            <!-- Price element missing -->
            <p class="description">Product description here</p>
        </div>
        """
        
        expected = {
            "error_type": "missing_element",
            "selectors": {
                "title": [".title"],
                "price": [],  # Empty - element not found
                "description": [".description"]
            },
            "extraction_strategy": "Extract available fields, handle missing price gracefully",
            "fallback_strategy": "Look for alternative price selectors or mark as unavailable",
            "confidence": 0.70
        }
        
        example = {
            "instruction": "Generate selectors for this HTML that has missing price information",
            "input": broken_html.strip(),
            "output": expected,
            "task_type": "error_handling",
            "domain": "ecommerce"
        }
        examples.append(example)
        
        # Malformed HTML
        malformed_html = """
        <div class="item">
            <h2>Item Title
            <span class="price">$99.99</span>
            <p>Description without closing tag
        </div>
        """
        
        expected = {
            "error_type": "malformed_html",
            "selectors": {
                "title": ["h2", ".item h2"],
                "price": [".price"],
                "description": ["p", ".item p"]
            },
            "extraction_strategy": "Use robust selectors that work with malformed HTML",
            "fallback_strategy": "Use parent containers and text extraction methods",
            "confidence": 0.75
        }
        
        example = {
            "instruction": "Handle this malformed HTML and extract data safely",
            "input": malformed_html.strip(),
            "output": expected,
            "task_type": "error_handling",
            "domain": "general"
        }
        examples.append(example)
        
        return examples
    
    def generate_edge_cases(self) -> List[Dict[str, Any]]:
        """Generate edge case examples"""
        examples = []
        
        # Very nested structure
        nested_html = """
        <div class="container">
            <div class="wrapper">
                <div class="content">
                    <div class="item-container">
                        <div class="item-wrapper">
                            <div class="item">
                                <div class="title-section">
                                    <h1 class="main-title">Deeply Nested Product</h1>
                                </div>
                                <div class="price-section">
                                    <div class="price-wrapper">
                                        <span class="currency">$</span>
                                        <span class="amount">299</span>
                                        <span class="cents">.99</span>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        """
        
        expected = {
            "selectors": {
                "title": [".main-title", ".title-section h1"],
                "price": [".price-wrapper", ".price-section"],
                "price_parts": {
                    "currency": [".currency"],
                    "amount": [".amount"],
                    "cents": [".cents"]
                }
            },
            "extraction_strategy": "Navigate deep nesting, combine price parts",
            "complexity": "high",
            "confidence": 0.85
        }
        
        example = {
            "instruction": "Extract data from this deeply nested HTML structure",
            "input": nested_html.strip(),
            "output": expected,
            "task_type": "complex_structure",
            "domain": "ecommerce"
        }
        examples.append(example)
        
        return examples
    
    def generate_dataset(self):
        """Generate the complete training dataset"""
        logger.info("Starting dataset generation...")
        
        # Generate different types of examples
        css_examples = self.generate_css_selector_examples(
            int(self.config.num_synthetic_examples * 0.6)
        )
        self.examples.extend(css_examples)
        logger.info(f"Generated {len(css_examples)} CSS selector examples")
        
        pagination_examples = self.generate_pagination_examples()
        self.examples.extend(pagination_examples)
        logger.info(f"Generated {len(pagination_examples)} pagination examples")
        
        filter_examples = self.generate_filter_examples()
        self.examples.extend(filter_examples)
        logger.info(f"Generated {len(filter_examples)} filter examples")
        
        if self.config.include_error_cases:
            error_examples = self.generate_error_cases()
            self.examples.extend(error_examples)
            logger.info(f"Generated {len(error_examples)} error handling examples")
        
        if self.config.include_edge_cases:
            edge_examples = self.generate_edge_cases()
            self.examples.extend(edge_examples)
            logger.info(f"Generated {len(edge_examples)} edge case examples")
        
        # Shuffle examples
        random.shuffle(self.examples)
        
        logger.info(f"Total generated examples: {len(self.examples)}")
    
    def save_dataset(self):
        """Save the generated dataset to JSONL format"""
        os.makedirs(os.path.dirname(self.config.output_path), exist_ok=True)
        
        with open(self.config.output_path, 'w', encoding='utf-8') as f:
            for example in self.examples:
                json.dump(example, f, ensure_ascii=False)
                f.write('\n')
        
        logger.info(f"Dataset saved to {self.config.output_path}")
        
        # Save sample for inspection
        sample_path = self.config.output_path.replace('.jsonl', '_sample.json')
        with open(sample_path, 'w', encoding='utf-8') as f:
            json.dump(self.examples[:10], f, indent=2, ensure_ascii=False)
        
        logger.info(f"Sample saved to {sample_path}")
    
    def create_validation_dataset(self):
        """Create a small validation dataset with known good examples"""
        validation_examples = [
            {
                "instruction": "Generate CSS selectors for extracting product information",
                "input": """
                <div class="product">
                    <h1 class="product-title">Test Product</h1>
                    <span class="price">$29.99</span>
                    <p class="description">A great test product</p>
                </div>
                """,
                "output": {
                    "selectors": {
                        "title": [".product-title"],
                        "price": [".price"],
                        "description": [".description"]
                    },
                    "confidence": 0.98
                },
                "task_type": "css_selector_generation",
                "domain": "ecommerce"
            }
        ]
        
        validation_path = self.config.output_path.replace('.jsonl', '_validation.jsonl')
        with open(validation_path, 'w', encoding='utf-8') as f:
            for example in validation_examples:
                json.dump(example, f, ensure_ascii=False)
                f.write('\n')
        
        logger.info(f"Validation dataset saved to {validation_path}")


def main():
    """Main function to generate the web scraping training dataset"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate web scraping training dataset")
    parser.add_argument("--output", type=str, default="./datasets/webscraping_dataset.jsonl")
    parser.add_argument("--num-examples", type=int, default=2000)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--no-edge-cases", action="store_true")
    parser.add_argument("--no-error-cases", action="store_true")
    
    args = parser.parse_args()
    
    config = DatasetConfig(
        output_path=args.output,
        num_synthetic_examples=args.num_examples,
        include_edge_cases=not args.no_edge_cases,
        include_error_cases=not args.no_error_cases,
        seed=args.seed
    )
    
    generator = WebScrapingDatasetGenerator(config)
    generator.generate_dataset()
    generator.save_dataset()
    generator.create_validation_dataset()
    
    logger.info("Dataset generation completed!")


if __name__ == "__main__":
    main()