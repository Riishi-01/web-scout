#!/usr/bin/env python3
"""
TinyLlama Fine-tuning Script for Web Scraping Domain
=====================================================

This script fine-tunes the TinyLlama 1.1B model specifically for web scraping tasks
including CSS selector generation, pagination detection, and extraction strategies.

Author: Claude Code Assistant
Date: December 13, 2024
"""

import os
import json
import logging
import argparse
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field

import torch
import wandb
from datasets import Dataset, load_dataset
from transformers import (
    AutoTokenizer, 
    AutoModelForCausalLM,
    TrainingArguments,
    Trainer,
    DataCollatorForLanguageModeling,
    EarlyStoppingCallback
)
from peft import LoraConfig, get_peft_model, TaskType
from trl import SFTTrainer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class TrainingConfig:
    """Configuration for TinyLlama fine-tuning"""
    # Model configuration
    model_name: str = "TinyLlama/TinyLlama-1.1B-Chat-v1.0"
    model_output_dir: str = "./models/tinyllama-webscraping-finetuned"
    onnx_output_dir: str = "./models/tinyllama-1.1b-onnx"
    
    # Dataset configuration
    dataset_path: str = "./datasets/webscraping_dataset.jsonl"
    train_split: float = 0.8
    validation_split: float = 0.1
    test_split: float = 0.1
    max_seq_length: int = 2048
    
    # LoRA configuration
    lora_rank: int = 16
    lora_alpha: int = 32
    lora_dropout: float = 0.1
    target_modules: List[str] = field(default_factory=lambda: ["q_proj", "v_proj", "k_proj", "o_proj"])
    
    # Training configuration
    num_epochs: int = 3
    batch_size: int = 4
    gradient_accumulation_steps: int = 4
    learning_rate: float = 2e-4
    weight_decay: float = 0.01
    warmup_steps: int = 100
    save_steps: int = 500
    eval_steps: int = 250
    logging_steps: int = 50
    
    # Hardware configuration
    fp16: bool = True
    gradient_checkpointing: bool = True
    dataloader_num_workers: int = 4
    
    # Wandb configuration
    use_wandb: bool = True
    wandb_project: str = "tinyllama-webscraping"
    wandb_run_name: Optional[str] = None


class WebScrapingDatasetProcessor:
    """Processes web scraping training data for TinyLlama fine-tuning"""
    
    def __init__(self, config: TrainingConfig):
        self.config = config
        self.tokenizer = AutoTokenizer.from_pretrained(config.model_name)
        
        # Add special tokens for web scraping
        special_tokens = {
            "additional_special_tokens": [
                "<HTML>", "</HTML>",
                "<CSS>", "</CSS>", 
                "<STRATEGY>", "</STRATEGY>",
                "<SELECTOR>", "</SELECTOR>",
                "<PAGINATION>", "</PAGINATION>",
                "<FILTER>", "</FILTER>"
            ]
        }
        self.tokenizer.add_special_tokens(special_tokens)
        
        if self.tokenizer.pad_token is None:
            self.tokenizer.pad_token = self.tokenizer.eos_token
    
    def format_training_example(self, example: Dict[str, Any]) -> str:
        """
        Formats a training example into the chat template format
        Expected format:
        {
            "instruction": "Generate CSS selectors for product extraction",
            "input": "HTML content...",
            "output": "CSS selectors and strategy..."
        }
        """
        system_prompt = """You are an expert web scraping AI assistant. Your task is to analyze HTML content and generate precise CSS selectors and extraction strategies for web scraping."""
        
        user_message = f"{example['instruction']}\n\nHTML Content:\n<HTML>\n{example['input']}\n</HTML>"
        
        assistant_message = example['output']
        if isinstance(assistant_message, dict):
            assistant_message = json.dumps(assistant_message, indent=2)
        
        # Format as chat conversation
        conversation = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
            {"role": "assistant", "content": assistant_message}
        ]
        
        # Use tokenizer's chat template if available
        if hasattr(self.tokenizer, 'apply_chat_template'):
            return self.tokenizer.apply_chat_template(
                conversation, 
                tokenize=False, 
                add_generation_prompt=False
            )
        else:
            # Fallback format
            return f"<s>[INST] <<SYS>>\n{system_prompt}\n<</SYS>>\n\n{user_message} [/INST] {assistant_message}</s>"
    
    def load_and_process_dataset(self) -> Dataset:
        """Load and process the web scraping dataset"""
        logger.info(f"Loading dataset from {self.config.dataset_path}")
        
        if not os.path.exists(self.config.dataset_path):
            raise FileNotFoundError(f"Dataset not found: {self.config.dataset_path}")
        
        # Load JSONL dataset
        data = []
        with open(self.config.dataset_path, 'r', encoding='utf-8') as f:
            for line in f:
                data.append(json.loads(line.strip()))
        
        logger.info(f"Loaded {len(data)} training examples")
        
        # Format examples
        formatted_texts = []
        for example in data:
            try:
                formatted_text = self.format_training_example(example)
                formatted_texts.append(formatted_text)
            except Exception as e:
                logger.warning(f"Failed to format example: {e}")
                continue
        
        logger.info(f"Successfully formatted {len(formatted_texts)} examples")
        
        # Create dataset
        dataset = Dataset.from_dict({"text": formatted_texts})
        
        # Tokenize dataset
        def tokenize_function(examples):
            return self.tokenizer(
                examples["text"],
                truncation=True,
                padding=False,
                max_length=self.config.max_seq_length,
                return_overflowing_tokens=False,
            )
        
        dataset = dataset.map(
            tokenize_function,
            batched=True,
            remove_columns=dataset.column_names,
            desc="Tokenizing dataset"
        )
        
        return dataset
    
    def split_dataset(self, dataset: Dataset) -> Dict[str, Dataset]:
        """Split dataset into train/validation/test sets"""
        # Calculate split sizes
        total_size = len(dataset)
        train_size = int(total_size * self.config.train_split)
        val_size = int(total_size * self.config.validation_split)
        
        # Create splits
        train_dataset = dataset.select(range(train_size))
        val_dataset = dataset.select(range(train_size, train_size + val_size))
        test_dataset = dataset.select(range(train_size + val_size, total_size))
        
        logger.info(f"Dataset splits - Train: {len(train_dataset)}, Val: {len(val_dataset)}, Test: {len(test_dataset)}")
        
        return {
            "train": train_dataset,
            "validation": val_dataset,
            "test": test_dataset
        }


class TinyLlamaTrainer:
    """TinyLlama fine-tuning trainer for web scraping"""
    
    def __init__(self, config: TrainingConfig):
        self.config = config
        self.model = None
        self.tokenizer = None
        self.processor = WebScrapingDatasetProcessor(config)
        
    def setup_model_and_tokenizer(self):
        """Setup the model and tokenizer for training"""
        logger.info(f"Loading model: {self.config.model_name}")
        
        # Load tokenizer
        self.tokenizer = self.processor.tokenizer
        
        # Load model with appropriate configuration
        model = AutoModelForCausalLM.from_pretrained(
            self.config.model_name,
            torch_dtype=torch.float16 if self.config.fp16 else torch.float32,
            device_map="auto",
            trust_remote_code=True,
        )
        
        # Resize token embeddings for new special tokens
        model.resize_token_embeddings(len(self.tokenizer))
        
        # Setup LoRA configuration
        lora_config = LoraConfig(
            task_type=TaskType.CAUSAL_LM,
            r=self.config.lora_rank,
            lora_alpha=self.config.lora_alpha,
            lora_dropout=self.config.lora_dropout,
            target_modules=self.config.target_modules,
            bias="none",
        )
        
        # Apply LoRA to model
        self.model = get_peft_model(model, lora_config)
        self.model.print_trainable_parameters()
        
        logger.info("Model and tokenizer setup complete")
    
    def setup_training_arguments(self) -> TrainingArguments:
        """Setup training arguments"""
        return TrainingArguments(
            output_dir=self.config.model_output_dir,
            num_train_epochs=self.config.num_epochs,
            per_device_train_batch_size=self.config.batch_size,
            per_device_eval_batch_size=self.config.batch_size,
            gradient_accumulation_steps=self.config.gradient_accumulation_steps,
            learning_rate=self.config.learning_rate,
            weight_decay=self.config.weight_decay,
            warmup_steps=self.config.warmup_steps,
            logging_steps=self.config.logging_steps,
            save_steps=self.config.save_steps,
            eval_steps=self.config.eval_steps,
            evaluation_strategy="steps",
            save_strategy="steps",
            load_best_model_at_end=True,
            metric_for_best_model="eval_loss",
            greater_is_better=False,
            fp16=self.config.fp16,
            gradient_checkpointing=self.config.gradient_checkpointing,
            dataloader_num_workers=self.config.dataloader_num_workers,
            remove_unused_columns=False,
            report_to="wandb" if self.config.use_wandb else None,
            run_name=self.config.wandb_run_name,
        )
    
    def train(self):
        """Main training function"""
        logger.info("Starting TinyLlama fine-tuning for web scraping")
        
        # Initialize Wandb if enabled
        if self.config.use_wandb:
            wandb.init(
                project=self.config.wandb_project,
                name=self.config.wandb_run_name,
                config=self.config.__dict__
            )
        
        # Setup model and tokenizer
        self.setup_model_and_tokenizer()
        
        # Load and process dataset
        dataset = self.processor.load_and_process_dataset()
        dataset_splits = self.processor.split_dataset(dataset)
        
        # Setup training arguments
        training_args = self.setup_training_arguments()
        
        # Create data collator
        data_collator = DataCollatorForLanguageModeling(
            tokenizer=self.tokenizer,
            mlm=False,
        )
        
        # Create trainer
        trainer = SFTTrainer(
            model=self.model,
            args=training_args,
            train_dataset=dataset_splits["train"],
            eval_dataset=dataset_splits["validation"],
            tokenizer=self.tokenizer,
            data_collator=data_collator,
            callbacks=[EarlyStoppingCallback(early_stopping_patience=3)],
            max_seq_length=self.config.max_seq_length,
        )
        
        # Start training
        logger.info("Beginning training...")
        trainer.train()
        
        # Save the final model
        logger.info("Saving final model...")
        trainer.save_model()
        self.tokenizer.save_pretrained(self.config.model_output_dir)
        
        # Evaluate on test set
        if len(dataset_splits["test"]) > 0:
            logger.info("Evaluating on test set...")
            test_results = trainer.evaluate(dataset_splits["test"])
            logger.info(f"Test results: {test_results}")
        
        logger.info("Training completed!")
    
    def convert_to_onnx(self):
        """Convert the fine-tuned model to ONNX format"""
        try:
            from optimum.onnxruntime import ORTModelForCausalLM
            
            logger.info("Converting model to ONNX format...")
            
            # Load the fine-tuned model
            model = AutoModelForCausalLM.from_pretrained(self.config.model_output_dir)
            tokenizer = AutoTokenizer.from_pretrained(self.config.model_output_dir)
            
            # Convert to ONNX
            ort_model = ORTModelForCausalLM.from_pretrained(
                self.config.model_output_dir,
                from_transformers=True
            )
            
            # Save ONNX model
            os.makedirs(self.config.onnx_output_dir, exist_ok=True)
            ort_model.save_pretrained(self.config.onnx_output_dir)
            tokenizer.save_pretrained(self.config.onnx_output_dir)
            
            logger.info(f"ONNX model saved to {self.config.onnx_output_dir}")
            
        except ImportError:
            logger.warning("optimum[onnxruntime] not installed. Skipping ONNX conversion.")
        except Exception as e:
            logger.error(f"ONNX conversion failed: {e}")


def main():
    parser = argparse.ArgumentParser(description="Fine-tune TinyLlama for web scraping")
    parser.add_argument("--config", type=str, help="Path to training config JSON file")
    parser.add_argument("--dataset", type=str, help="Path to training dataset")
    parser.add_argument("--output-dir", type=str, help="Output directory for model")
    parser.add_argument("--wandb-run-name", type=str, help="Wandb run name")
    parser.add_argument("--no-wandb", action="store_true", help="Disable Wandb logging")
    parser.add_argument("--convert-onnx", action="store_true", help="Convert to ONNX after training")
    
    args = parser.parse_args()
    
    # Load configuration
    config = TrainingConfig()
    
    if args.config:
        with open(args.config, 'r') as f:
            config_dict = json.load(f)
            for key, value in config_dict.items():
                if hasattr(config, key):
                    setattr(config, key, value)
    
    # Override with command line arguments
    if args.dataset:
        config.dataset_path = args.dataset
    if args.output_dir:
        config.model_output_dir = args.output_dir
    if args.wandb_run_name:
        config.wandb_run_name = args.wandb_run_name
    if args.no_wandb:
        config.use_wandb = False
    
    # Create output directories
    os.makedirs(config.model_output_dir, exist_ok=True)
    os.makedirs(os.path.dirname(config.dataset_path), exist_ok=True)
    
    # Initialize trainer and start training
    trainer = TinyLlamaTrainer(config)
    trainer.train()
    
    # Convert to ONNX if requested
    if args.convert_onnx:
        trainer.convert_to_onnx()


if __name__ == "__main__":
    main()