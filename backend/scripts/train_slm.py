#!/usr/bin/env python3
"""
Fine-tuning script for the self-contained local Small Language Model (SLM).
Loads Qwen2.5-0.5B-Instruct and fine-tunes it on the train_dataset.json dataset.

Usage:
    python scripts/train_slm.py
"""

import os
import json
import torch
from loguru import logger
from torch.utils.data import Dataset, DataLoader
from torch.optim import AdamW
from transformers import AutoTokenizer, AutoModelForCausalLM

class QADataset(Dataset):
    def __init__(self, data_path, tokenizer, max_length=512):
        self.examples = []
        
        if not os.path.exists(data_path):
            raise FileNotFoundError(f"Dataset file not found at: {data_path}")

        with open(data_path, 'r') as f:
            data = json.load(f)

        logger.info(f"Loaded {len(data)} examples from {data_path}")
        
        for item in data:
            messages = item.get("messages", [])
            # Format using Hugging Face's apply_chat_template
            text = tokenizer.apply_chat_template(
                messages, 
                tokenize=False, 
                add_generation_prompt=False
            )
            
            encodings = tokenizer(
                text,
                truncation=True,
                max_length=max_length,
                padding="max_length",
                return_tensors="pt"
            )
            
            input_ids = encodings["input_ids"].squeeze(0)
            attention_mask = encodings["attention_mask"].squeeze(0)
            
            # For CausalLM, labels are shifted version of input_ids.
            # PyTorch's CrossEntropyLoss will ignore target indices set to -100 (padding)
            labels = input_ids.clone()
            labels[labels == tokenizer.pad_token_id] = -100
            
            self.examples.append({
                "input_ids": input_ids,
                "attention_mask": attention_mask,
                "labels": labels
            })

    def __len__(self):
        return len(self.examples)

    def __getitem__(self, idx):
        return self.examples[idx]

def train():
    dataset_path = "data/train_dataset.json"
    model_id = "Qwen/Qwen2.5-0.5B-Instruct"
    output_dir = "./models/fine-tuned-slm"
    
    # 1. Initialize tokenizer and model
    logger.info(f"Loading base model and tokenizer: {model_id}...")
    tokenizer = AutoTokenizer.from_pretrained(model_id)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
        
    model = AutoModelForCausalLM.from_pretrained(model_id)
    
    # Auto-detect device
    device = "cpu"
    if torch.cuda.is_available():
        device = "cuda"
    elif torch.backends.mps.is_available():
        device = "mps"
        
    logger.info(f"Training will run on device: {device}")
    model.to(device)
    
    # 2. Load dataset
    logger.info("Preparing dataset...")
    dataset = QADataset(dataset_path, tokenizer)
    dataloader = DataLoader(dataset, batch_size=2, shuffle=True)
    
    # 3. Optimizer and Hyperparameters
    optimizer = AdamW(model.parameters(), lr=5e-5)
    epochs = 3
    
    # 4. Training Loop
    logger.info("Starting training loop...")
    model.train()
    for epoch in range(epochs):
        epoch_loss = 0
        for batch in dataloader:
            optimizer.zero_grad()
            
            input_ids = batch["input_ids"].to(device)
            attention_mask = batch["attention_mask"].to(device)
            labels = batch["labels"].to(device)
            
            outputs = model(
                input_ids=input_ids,
                attention_mask=attention_mask,
                labels=labels
            )
            
            loss = outputs.loss
            loss.backward()
            optimizer.step()
            
            epoch_loss += loss.item()
            
        avg_loss = epoch_loss / len(dataloader)
        logger.info(f"Epoch {epoch+1}/{epochs} Completed | Average Loss: {avg_loss:.4f}")
        
    # 5. Save model and tokenizer
    logger.info(f"Saving fine-tuned model checkpoint to: {output_dir}...")
    os.makedirs(output_dir, exist_ok=True)
    model.save_pretrained(output_dir)
    tokenizer.save_pretrained(output_dir)
    logger.success("Training complete! Fine-tuned model saved successfully.")

if __name__ == "__main__":
    train()
