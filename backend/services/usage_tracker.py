import os
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional
from pathlib import Path

logger = logging.getLogger(__name__)

class UsageTracker:
    """Track API usage for OpenAI and AssemblyAI"""
    
    # OpenAI pricing per 1M tokens (input/output)
    # gpt-4o-mini: $0.15/$0.60 per 1M tokens
    OPENAI_PRICING = {
        "gpt-4o-mini": {"input": 0.15, "output": 0.60},
        "gpt-4o": {"input": 2.50, "output": 10.00},
        "gpt-3.5-turbo": {"input": 0.50, "output": 1.50},
        "gpt-4": {"input": 30.00, "output": 60.00},
        "default": {"input": 0.15, "output": 0.60}  # Default to gpt-4o-mini pricing
    }
    
    # AssemblyAI pricing: $0.00025 per second = $0.015 per minute
    ASSEMBLYAI_PRICE_PER_SECOND = 0.00025
    ASSEMBLYAI_PRICE_PER_MINUTE = 0.015
    
    def __init__(self, data_dir: Optional[str] = None):
        """Initialize usage tracker with data directory"""
        if data_dir is None:
            # Default to backend/data directory
            base_dir = Path(__file__).parent.parent
            data_dir = base_dir / "data"
        else:
            data_dir = Path(data_dir)
        
        self.data_dir = data_dir
        self.data_dir.mkdir(exist_ok=True)
        self.usage_file = self.data_dir / "usage.json"
        
        # Initialize usage file if it doesn't exist
        if not self.usage_file.exists():
            self._initialize_usage_file()
    
    def _initialize_usage_file(self):
        """Initialize empty usage file"""
        initial_data = {
            "openai": [],
            "assemblyai": []
        }
        with open(self.usage_file, 'w') as f:
            json.dump(initial_data, f, indent=2)
        logger.info(f"Initialized usage file at {self.usage_file}")
    
    def _load_usage_data(self) -> Dict:
        """Load usage data from JSON file"""
        try:
            if not self.usage_file.exists():
                self._initialize_usage_file()
            
            with open(self.usage_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading usage data: {e}", exc_info=True)
            return {"openai": [], "assemblyai": []}
    
    def _save_usage_data(self, data: Dict):
        """Save usage data to JSON file"""
        try:
            with open(self.usage_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving usage data: {e}", exc_info=True)
    
    def _calculate_openai_cost(self, prompt_tokens: int, completion_tokens: int, model: str) -> float:
        """Calculate OpenAI cost based on token usage and model"""
        pricing = self.OPENAI_PRICING.get(model, self.OPENAI_PRICING["default"])
        
        # Convert to cost per 1M tokens
        input_cost = (prompt_tokens / 1_000_000) * pricing["input"]
        output_cost = (completion_tokens / 1_000_000) * pricing["output"]
        
        return input_cost + output_cost
    
    def track_openai_usage(self, prompt_tokens: int, completion_tokens: int, 
                          total_tokens: int, model: str = "gpt-4o-mini"):
        """Track OpenAI API usage"""
        try:
            cost = self._calculate_openai_cost(prompt_tokens, completion_tokens, model)
            date = datetime.now().strftime("%Y-%m-%d")
            
            usage_entry = {
                "date": date,
                "tokens": total_tokens,
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "cost": round(cost, 6),
                "model": model
            }
            
            data = self._load_usage_data()
            data["openai"].append(usage_entry)
            self._save_usage_data(data)
            
            logger.info(f"Tracked OpenAI usage: {total_tokens} tokens, ${cost:.6f}, model: {model}")
        except Exception as e:
            logger.error(f"Error tracking OpenAI usage: {e}", exc_info=True)
    
    def track_assemblyai_usage(self, duration_seconds: float):
        """Track AssemblyAI transcription usage"""
        try:
            duration_minutes = duration_seconds / 60.0
            cost = duration_seconds * self.ASSEMBLYAI_PRICE_PER_SECOND
            date = datetime.now().strftime("%Y-%m-%d")
            
            usage_entry = {
                "date": date,
                "seconds": round(duration_seconds, 2),
                "minutes": round(duration_minutes, 2),
                "cost": round(cost, 6)
            }
            
            data = self._load_usage_data()
            data["assemblyai"].append(usage_entry)
            self._save_usage_data(data)
            
            logger.info(f"Tracked AssemblyAI usage: {duration_seconds:.2f}s ({duration_minutes:.2f}min), ${cost:.6f}")
        except Exception as e:
            logger.error(f"Error tracking AssemblyAI usage: {e}", exc_info=True)
    
    def get_usage_stats(self) -> Dict:
        """Get usage statistics grouped by month"""
        try:
            data = self._load_usage_data()
            
            # Group OpenAI usage by month
            openai_by_month = {}
            for entry in data.get("openai", []):
                date_str = entry.get("date", "")
                if date_str:
                    try:
                        date_obj = datetime.strptime(date_str, "%Y-%m-%d")
                        month_key = date_obj.strftime("%Y-%m")
                        if month_key not in openai_by_month:
                            openai_by_month[month_key] = {"cost": 0.0, "tokens": 0}
                        openai_by_month[month_key]["cost"] += entry.get("cost", 0.0)
                        openai_by_month[month_key]["tokens"] += entry.get("tokens", 0)
                    except ValueError:
                        continue
            
            # Group AssemblyAI usage by month
            assemblyai_by_month = {}
            for entry in data.get("assemblyai", []):
                date_str = entry.get("date", "")
                if date_str:
                    try:
                        date_obj = datetime.strptime(date_str, "%Y-%m-%d")
                        month_key = date_obj.strftime("%Y-%m")
                        if month_key not in assemblyai_by_month:
                            assemblyai_by_month[month_key] = {"cost": 0.0, "minutes": 0.0}
                        assemblyai_by_month[month_key]["cost"] += entry.get("cost", 0.0)
                        assemblyai_by_month[month_key]["minutes"] += entry.get("minutes", 0.0)
                    except ValueError:
                        continue
            
            # Calculate totals
            total_openai_cost = sum(entry.get("cost", 0.0) for entry in data.get("openai", []))
            total_assemblyai_cost = sum(entry.get("cost", 0.0) for entry in data.get("assemblyai", []))
            
            return {
                "openai_by_month": openai_by_month,
                "assemblyai_by_month": assemblyai_by_month,
                "total_openai_cost": round(total_openai_cost, 2),
                "total_assemblyai_cost": round(total_assemblyai_cost, 2),
                "total_cost": round(total_openai_cost + total_assemblyai_cost, 2)
            }
        except Exception as e:
            logger.error(f"Error getting usage stats: {e}", exc_info=True)
            return {
                "openai_by_month": {},
                "assemblyai_by_month": {},
                "total_openai_cost": 0.0,
                "total_assemblyai_cost": 0.0,
                "total_cost": 0.0
            }

