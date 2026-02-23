import os
import logging
from typing import Dict, Optional
from openai import OpenAI
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class OpenAIService:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY environment variable is required")
        
        self.client = OpenAI(api_key=self.api_key)
        self.model = os.getenv("OPENAI_MODEL", "gpt-4")  # Default to GPT-4 for better quality
        
    async def generate_text(self, prompt: str, max_tokens: int = 2000, temperature: float = 0.7) -> str:
        """Generate text using OpenAI API"""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a professional content writer specializing in podcast summaries, blog posts, and marketing content."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=max_tokens,
                temperature=temperature
            )
            
            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f"Error generating text with OpenAI: {str(e)}", exc_info=True)
            raise Exception(f"OpenAI API error: {str(e)}")
    
    async def generate_text_with_tokens(self, prompt: str, max_tokens: int = 2000, temperature: float = 0.7) -> Dict:
        """Generate text and return both content and token usage"""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a professional content writer specializing in podcast summaries, blog posts, and marketing content."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=max_tokens,
                temperature=temperature
            )
            
            return {
                'content': response.choices[0].message.content.strip(),
                'tokens_used': response.usage.total_tokens if response.usage else 0,
                'prompt_tokens': response.usage.prompt_tokens if response.usage else 0,
                'completion_tokens': response.usage.completion_tokens if response.usage else 0
            }
        except Exception as e:
            logger.error(f"Error generating text with OpenAI: {str(e)}", exc_info=True)
            raise Exception(f"OpenAI API error: {str(e)}")
    
    async def get_credit_info(self) -> Dict:
        """Get OpenAI API credit/usage information"""
        try:
            # Check if API key is configured
            if not self.api_key or self.api_key == "your_api_key_here":
                return {
                    'success': False,
                    'message': 'OpenAI API key not configured',
                    'error': 'missing_api_key'
                }
            
            # Note: OpenAI doesn't provide a direct "credits" endpoint via API
            # Users should check their dashboard for billing information
            # We'll indicate that the API key is configured
            return {
                'success': True,
                'message': 'API key configured',
                'note': 'Check your OpenAI dashboard (https://platform.openai.com/usage) for detailed usage and billing information.',
                'dashboard_url': 'https://platform.openai.com/usage',
                'model': self.model
            }
                
        except Exception as e:
            logger.error(f"Error fetching credit info: {str(e)}", exc_info=True)
            return {
                'success': False,
                'error': str(e),
                'message': 'Could not retrieve credit information'
            }

