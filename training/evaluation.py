#!/usr/bin/env python3
"""
Model Evaluation Script for TinyLlama Web Scraping Fine-tuning
=============================================================

This script evaluates the fine-tuned TinyLlama model on web scraping tasks,
measuring accuracy, quality, and performance metrics.

Author: Claude Code Assistant
Date: December 13, 2024
"""

import os
import json
import logging
import argparse
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
import re
from collections import defaultdict
import time

import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
import pandas as pd
from bs4 import BeautifulSoup
import numpy as np
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class EvaluationConfig:
    """Configuration for model evaluation"""
    model_path: str = "./models/tinyllama-webscraping-finetuned"
    test_dataset_path: str = "./datasets/webscraping_dataset_validation.jsonl"
    output_dir: str = "./evaluation_results"
    batch_size: int = 1  # Small batch for inference
    max_length: int = 2048
    temperature: float = 0.1
    top_p: float = 0.9
    num_beams: int = 1
    do_sample: bool = False


class SelectorAccuracyEvaluator:
    """Evaluates the accuracy of generated CSS selectors"""
    
    def __init__(self):
        self.metrics = defaultdict(list)
    
    def validate_selector_syntax(self, selector: str) -> bool:
        """Check if CSS selector has valid syntax"""
        try:
            # Basic syntax validation
            if not selector or not selector.strip():
                return False
            
            # Check for common CSS selector patterns
            valid_patterns = [
                r'^[.#]?[\w-]+$',  # Simple class/id/tag
                r'^[.#]?[\w-]+(\s+[.#]?[\w-]+)*$',  # Descendant selectors
                r'^[.#]?[\w-]+(\s*>\s*[.#]?[\w-]+)*$',  # Child selectors
                r'^[.#]?[\w-]+(\[[^\]]+\])?$',  # Attribute selectors
                r'^[.#]?[\w-]+(:[\w-]+)?$',  # Pseudo selectors
            ]
            
            return any(re.match(pattern, selector.strip()) for pattern in valid_patterns)
        except:
            return False
    
    def test_selector_on_html(self, selector: str, html: str, expected_content: str = None) -> Dict[str, Any]:
        """Test if selector works on given HTML"""
        try:
            soup = BeautifulSoup(html, 'html.parser')
            elements = soup.select(selector)
            
            result = {
                "selector_works": len(elements) > 0,
                "element_count": len(elements),
                "found_content": [elem.get_text(strip=True) for elem in elements[:3]],
                "has_expected_content": False
            }
            
            if expected_content and elements:
                found_text = ' '.join([elem.get_text(strip=True) for elem in elements])
                result["has_expected_content"] = expected_content.lower() in found_text.lower()
            
            return result
        except Exception as e:
            return {
                "selector_works": False,
                "element_count": 0,
                "found_content": [],
                "has_expected_content": False,
                "error": str(e)
            }
    
    def evaluate_selector_quality(self, predicted: Dict[str, Any], expected: Dict[str, Any], html: str) -> Dict[str, float]:
        """Evaluate the quality of predicted selectors"""
        metrics = {
            "syntax_accuracy": 0.0,
            "functionality_accuracy": 0.0,
            "content_accuracy": 0.0,
            "selector_count_accuracy": 0.0
        }
        
        if "selectors" not in predicted:
            return metrics
        
        predicted_selectors = predicted.get("selectors", {})
        expected_selectors = expected.get("selectors", {})
        
        syntax_scores = []
        functionality_scores = []
        content_scores = []
        
        for field, expected_selector_list in expected_selectors.items():
            if field in predicted_selectors:
                predicted_selector_list = predicted_selectors[field]
                if not isinstance(predicted_selector_list, list):
                    predicted_selector_list = [predicted_selector_list]
                
                # Test each predicted selector
                field_syntax_scores = []
                field_functionality_scores = []
                field_content_scores = []
                
                for pred_selector in predicted_selector_list:
                    # Syntax validation
                    syntax_valid = self.validate_selector_syntax(pred_selector)
                    field_syntax_scores.append(1.0 if syntax_valid else 0.0)
                    
                    # Functionality test
                    test_result = self.test_selector_on_html(pred_selector, html)
                    field_functionality_scores.append(1.0 if test_result["selector_works"] else 0.0)
                    
                    # Content accuracy (if we can verify)
                    if test_result["found_content"]:
                        # Simple heuristic: check if found content seems relevant
                        content_relevant = len(test_result["found_content"][0]) > 0
                        field_content_scores.append(1.0 if content_relevant else 0.0)
                    else:
                        field_content_scores.append(0.0)
                
                # Average scores for this field
                if field_syntax_scores:
                    syntax_scores.append(np.mean(field_syntax_scores))
                if field_functionality_scores:
                    functionality_scores.append(np.mean(field_functionality_scores))
                if field_content_scores:
                    content_scores.append(np.mean(field_content_scores))
        
        # Calculate overall metrics
        metrics["syntax_accuracy"] = np.mean(syntax_scores) if syntax_scores else 0.0
        metrics["functionality_accuracy"] = np.mean(functionality_scores) if functionality_scores else 0.0
        metrics["content_accuracy"] = np.mean(content_scores) if content_scores else 0.0
        
        # Selector count accuracy
        expected_field_count = len(expected_selectors)
        predicted_field_count = len(predicted_selectors)
        if expected_field_count > 0:
            metrics["selector_count_accuracy"] = min(predicted_field_count / expected_field_count, 1.0)
        
        return metrics


class ModelInferenceEngine:
    """Handles model inference for evaluation"""
    
    def __init__(self, config: EvaluationConfig):
        self.config = config
        self.model = None
        self.tokenizer = None
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        logger.info(f"Using device: {self.device}")
    
    def load_model(self):
        """Load the fine-tuned model and tokenizer"""
        logger.info(f"Loading model from {self.config.model_path}")
        
        try:
            self.tokenizer = AutoTokenizer.from_pretrained(self.config.model_path)
            self.model = AutoModelForCausalLM.from_pretrained(
                self.config.model_path,
                torch_dtype=torch.float16 if self.device.type == "cuda" else torch.float32,
                device_map="auto" if self.device.type == "cuda" else None,
                trust_remote_code=True
            )
            
            if self.device.type != "cuda":
                self.model = self.model.to(self.device)
            
            self.model.eval()
            logger.info("Model loaded successfully")
            
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            raise
    
    def format_prompt(self, instruction: str, input_text: str) -> str:
        """Format prompt for inference"""
        system_prompt = "You are an expert web scraping AI assistant. Your task is to analyze HTML content and generate precise CSS selectors and extraction strategies for web scraping."
        
        user_message = f"{instruction}\n\nHTML Content:\n<HTML>\n{input_text}\n</HTML>"
        
        # Format as chat conversation
        conversation = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message}
        ]
        
        # Use tokenizer's chat template if available
        if hasattr(self.tokenizer, 'apply_chat_template'):
            return self.tokenizer.apply_chat_template(
                conversation, 
                tokenize=False, 
                add_generation_prompt=True
            )
        else:
            # Fallback format
            return f"<s>[INST] <<SYS>>\n{system_prompt}\n<</SYS>>\n\n{user_message} [/INST] "
    
    def generate_response(self, prompt: str) -> str:
        """Generate model response for given prompt"""
        try:
            inputs = self.tokenizer(
                prompt,
                return_tensors="pt",
                truncation=True,
                max_length=self.config.max_length - 512,  # Leave room for generation
                padding=False
            ).to(self.device)
            
            start_time = time.time()
            
            with torch.no_grad():
                outputs = self.model.generate(
                    **inputs,
                    max_new_tokens=512,
                    temperature=self.config.temperature,
                    top_p=self.config.top_p,
                    num_beams=self.config.num_beams,
                    do_sample=self.config.do_sample,
                    pad_token_id=self.tokenizer.eos_token_id,
                    eos_token_id=self.tokenizer.eos_token_id,
                )
            
            inference_time = time.time() - start_time
            
            # Decode only the new tokens
            input_length = inputs.input_ids.shape[1]
            generated_tokens = outputs[0][input_length:]
            response = self.tokenizer.decode(generated_tokens, skip_special_tokens=True)
            
            logger.debug(f"Inference time: {inference_time:.2f}s")
            return response.strip()
            
        except Exception as e:
            logger.error(f"Generation failed: {e}")
            return ""
    
    def parse_response(self, response: str) -> Dict[str, Any]:
        """Parse model response into structured format"""
        try:
            # Try to parse as JSON first
            if response.strip().startswith('{'):
                return json.loads(response)
            
            # If not JSON, try to extract structured information
            parsed = {}
            
            # Look for selector patterns
            selector_pattern = r'"([^"]+)":\s*\[([^\]]+)\]'
            matches = re.findall(selector_pattern, response)
            
            if matches:
                selectors = {}
                for field, selector_list in matches:
                    # Parse the selector list
                    selectors_raw = re.findall(r'"([^"]+)"', selector_list)
                    selectors[field] = selectors_raw
                parsed["selectors"] = selectors
            
            # Look for strategy information
            if "strategy" in response.lower():
                strategy_match = re.search(r'"extraction_strategy":\s*"([^"]+)"', response)
                if strategy_match:
                    parsed["extraction_strategy"] = strategy_match.group(1)
            
            return parsed if parsed else {"error": "Failed to parse response"}
            
        except json.JSONDecodeError:
            # Try to extract at least some information
            return {"raw_response": response, "parse_error": True}


class ComprehensiveEvaluator:
    """Main evaluation class that coordinates all evaluation metrics"""
    
    def __init__(self, config: EvaluationConfig):
        self.config = config
        self.inference_engine = ModelInferenceEngine(config)
        self.selector_evaluator = SelectorAccuracyEvaluator()
        self.results = []
        self.metrics_summary = defaultdict(list)
    
    def load_test_dataset(self) -> List[Dict[str, Any]]:
        """Load test dataset"""
        logger.info(f"Loading test dataset from {self.config.test_dataset_path}")
        
        examples = []
        with open(self.config.test_dataset_path, 'r', encoding='utf-8') as f:
            for line in f:
                examples.append(json.loads(line.strip()))
        
        logger.info(f"Loaded {len(examples)} test examples")
        return examples
    
    def evaluate_single_example(self, example: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate model on a single example"""
        instruction = example["instruction"]
        input_html = example["input"]
        expected_output = example["output"]
        
        # Generate model response
        prompt = self.inference_engine.format_prompt(instruction, input_html)
        raw_response = self.inference_engine.generate_response(prompt)
        parsed_response = self.inference_engine.parse_response(raw_response)
        
        # Evaluate based on task type
        task_type = example.get("task_type", "css_selector_generation")
        
        evaluation_result = {
            "example_id": example.get("id", "unknown"),
            "task_type": task_type,
            "domain": example.get("domain", "unknown"),
            "instruction": instruction,
            "raw_response": raw_response,
            "parsed_response": parsed_response,
            "expected_output": expected_output,
            "metrics": {}
        }
        
        if task_type == "css_selector_generation":
            metrics = self.selector_evaluator.evaluate_selector_quality(
                parsed_response, expected_output, input_html
            )
            evaluation_result["metrics"] = metrics
            
            # Add to summary metrics
            for metric_name, value in metrics.items():
                self.metrics_summary[metric_name].append(value)
        
        # Calculate response quality metrics
        response_quality = self.evaluate_response_quality(raw_response, parsed_response)
        evaluation_result["response_quality"] = response_quality
        
        for metric_name, value in response_quality.items():
            self.metrics_summary[f"response_{metric_name}"].append(value)
        
        return evaluation_result
    
    def evaluate_response_quality(self, raw_response: str, parsed_response: Dict[str, Any]) -> Dict[str, float]:
        """Evaluate the quality of the raw response"""
        metrics = {
            "length": len(raw_response),
            "is_valid_json": "parse_error" not in parsed_response,
            "has_selectors": "selectors" in parsed_response,
            "response_completeness": 0.0
        }
        
        # Check completeness
        expected_fields = ["selectors", "extraction_strategy", "confidence"]
        found_fields = sum(1 for field in expected_fields if field in parsed_response)
        metrics["response_completeness"] = found_fields / len(expected_fields)
        
        return metrics
    
    def run_evaluation(self):
        """Run complete evaluation"""
        logger.info("Starting model evaluation...")
        
        # Load model
        self.inference_engine.load_model()
        
        # Load test dataset
        test_examples = self.load_test_dataset()
        
        # Evaluate each example
        for i, example in enumerate(test_examples):
            logger.info(f"Evaluating example {i+1}/{len(test_examples)}")
            
            try:
                result = self.evaluate_single_example(example)
                self.results.append(result)
                
                # Log progress
                if (i + 1) % 10 == 0:
                    self.log_progress_metrics()
                    
            except Exception as e:
                logger.error(f"Failed to evaluate example {i}: {e}")
                continue
        
        logger.info("Evaluation completed!")
    
    def log_progress_metrics(self):
        """Log current progress metrics"""
        if not self.metrics_summary:
            return
        
        logger.info("Current metrics:")
        for metric_name, values in self.metrics_summary.items():
            if values:
                avg_value = np.mean(values)
                logger.info(f"  {metric_name}: {avg_value:.3f}")
    
    def generate_report(self):
        """Generate comprehensive evaluation report"""
        logger.info("Generating evaluation report...")
        
        # Calculate summary statistics
        summary_stats = {}
        for metric_name, values in self.metrics_summary.items():
            if values:
                summary_stats[metric_name] = {
                    "mean": float(np.mean(values)),
                    "std": float(np.std(values)),
                    "min": float(np.min(values)),
                    "max": float(np.max(values)),
                    "count": len(values)
                }
        
        # Create report
        report = {
            "evaluation_config": self.config.__dict__,
            "summary_statistics": summary_stats,
            "total_examples": len(self.results),
            "successful_evaluations": len([r for r in self.results if r["metrics"]]),
            "task_type_breakdown": self.get_task_type_breakdown(),
            "detailed_results": self.results
        }
        
        # Save report
        os.makedirs(self.config.output_dir, exist_ok=True)
        
        report_path = os.path.join(self.config.output_dir, "evaluation_report.json")
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        # Save summary CSV
        self.save_summary_csv()
        
        logger.info(f"Evaluation report saved to {report_path}")
        
        # Print key metrics
        self.print_key_metrics(summary_stats)
    
    def get_task_type_breakdown(self) -> Dict[str, Dict[str, Any]]:
        """Get metrics breakdown by task type"""
        breakdown = defaultdict(lambda: defaultdict(list))
        
        for result in self.results:
            task_type = result["task_type"]
            for metric_name, value in result["metrics"].items():
                breakdown[task_type][metric_name].append(value)
        
        # Calculate averages
        task_type_summary = {}
        for task_type, metrics in breakdown.items():
            task_type_summary[task_type] = {}
            for metric_name, values in metrics.items():
                if values:
                    task_type_summary[task_type][metric_name] = {
                        "mean": float(np.mean(values)),
                        "count": len(values)
                    }
        
        return task_type_summary
    
    def save_summary_csv(self):
        """Save summary metrics to CSV"""
        csv_data = []
        for result in self.results:
            row = {
                "task_type": result["task_type"],
                "domain": result["domain"],
                **result["metrics"],
                **result["response_quality"]
            }
            csv_data.append(row)
        
        if csv_data:
            df = pd.DataFrame(csv_data)
            csv_path = os.path.join(self.config.output_dir, "evaluation_metrics.csv")
            df.to_csv(csv_path, index=False)
            logger.info(f"Summary CSV saved to {csv_path}")
    
    def print_key_metrics(self, summary_stats: Dict[str, Dict[str, float]]):
        """Print key evaluation metrics"""
        print("\n" + "="*60)
        print("EVALUATION RESULTS SUMMARY")
        print("="*60)
        
        key_metrics = [
            "syntax_accuracy",
            "functionality_accuracy", 
            "content_accuracy",
            "response_is_valid_json",
            "response_has_selectors",
            "response_response_completeness"
        ]
        
        for metric in key_metrics:
            if metric in summary_stats:
                stats = summary_stats[metric]
                print(f"{metric:30s}: {stats['mean']:.3f} ± {stats['std']:.3f}")
        
        print("\nOverall Performance:")
        if "syntax_accuracy" in summary_stats and "functionality_accuracy" in summary_stats:
            overall_score = (summary_stats["syntax_accuracy"]["mean"] + 
                           summary_stats["functionality_accuracy"]["mean"]) / 2
            print(f"{'Overall Accuracy':30s}: {overall_score:.3f}")
        
        print("="*60)


def main():
    """Main evaluation function"""
    parser = argparse.ArgumentParser(description="Evaluate TinyLlama web scraping model")
    parser.add_argument("--model-path", type=str, required=True, help="Path to fine-tuned model")
    parser.add_argument("--test-dataset", type=str, required=True, help="Path to test dataset")
    parser.add_argument("--output-dir", type=str, default="./evaluation_results", help="Output directory")
    parser.add_argument("--batch-size", type=int, default=1, help="Batch size for inference")
    parser.add_argument("--temperature", type=float, default=0.1, help="Generation temperature")
    parser.add_argument("--max-examples", type=int, help="Limit number of examples to evaluate")
    
    args = parser.parse_args()
    
    config = EvaluationConfig(
        model_path=args.model_path,
        test_dataset_path=args.test_dataset,
        output_dir=args.output_dir,
        batch_size=args.batch_size,
        temperature=args.temperature
    )
    
    evaluator = ComprehensiveEvaluator(config)
    evaluator.run_evaluation()
    evaluator.generate_report()


if __name__ == "__main__":
    main()