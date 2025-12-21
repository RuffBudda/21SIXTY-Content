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
        # Default to gpt-4o-mini (more accessible) or gpt-3.5-turbo as fallback
        # Users can override via OPENAI_MODEL environment variable
        configured_model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        # If gpt-4 is configured but not available, fallback to gpt-4o-mini
        if configured_model == "gpt-4":
            logger.warning("gpt-4 model configured but may not be available. Using gpt-4o-mini as fallback.")
            self.model = "gpt-4o-mini"
        else:
            self.model = configured_model
        # List of fallback models to try if primary model fails
        self.fallback_models = ["gpt-4o-mini", "gpt-3.5-turbo", "gpt-4o"]
        
    async def generate_text(self, prompt: str, max_tokens: int = 2000, temperature: float = 0.7) -> str:
        """Generate text using OpenAI API with automatic fallback to alternative models"""
        models_to_try = [self.model] + [m for m in self.fallback_models if m != self.model]
        last_error = None
        
        for model_to_try in models_to_try:
            try:
                response = self.client.chat.completions.create(
                    model=model_to_try,
                    messages=[
                        {"role": "system", "content": "You are a professional content writer specializing in podcast summaries, blog posts, and marketing content."},
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=max_tokens,
                    temperature=temperature
                )
                
                # If we used a fallback model, log it
                if model_to_try != self.model:
                    logger.info(f"Successfully used fallback model '{model_to_try}' instead of '{self.model}'")
                
                return response.choices[0].message.content.strip()
            except Exception as e:
                error_msg = str(e)
                last_error = e
                # If it's a model access error, try next fallback
                if "model_not_found" in error_msg or "does not have access" in error_msg:
                    logger.warning(f"Model '{model_to_try}' not available, trying fallback models...")
                    continue
                # For other errors, break and raise immediately
                break
        
        # If we get here, all models failed
        error_msg = str(last_error) if last_error else "Unknown error"
        logger.error(f"Error generating text with OpenAI: {error_msg}", exc_info=True)
        if "model_not_found" in error_msg or "does not have access" in error_msg:
            raise Exception(f"OpenAI API error: None of the attempted models are available. Tried: {', '.join(models_to_try)}. Please set OPENAI_MODEL environment variable to a model your project has access to. Original error: {error_msg}")
        raise Exception(f"OpenAI API error: {error_msg}")
    
    async def generate_text_with_tokens(self, prompt: str, max_tokens: int = 2000, temperature: float = 0.7) -> Dict:
        """Generate text and return both content and token usage with automatic fallback to alternative models"""
        models_to_try = [self.model] + [m for m in self.fallback_models if m != self.model]
        last_error = None
        
        for model_to_try in models_to_try:
            try:
                response = self.client.chat.completions.create(
                    model=model_to_try,
                    messages=[
                        {"role": "system", "content": "You are a professional content writer specializing in podcast summaries, blog posts, and marketing content."},
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=max_tokens,
                    temperature=temperature
                )
                
                # If we used a fallback model, log it
                if model_to_try != self.model:
                    logger.info(f"Successfully used fallback model '{model_to_try}' instead of '{self.model}'")
                
                return {
                    'content': response.choices[0].message.content.strip(),
                    'tokens_used': response.usage.total_tokens if response.usage else 0,
                    'prompt_tokens': response.usage.prompt_tokens if response.usage else 0,
                    'completion_tokens': response.usage.completion_tokens if response.usage else 0
                }
            except Exception as e:
                error_msg = str(e)
                last_error = e
                # If it's a model access error, try next fallback
                if "model_not_found" in error_msg or "does not have access" in error_msg:
                    logger.warning(f"Model '{model_to_try}' not available, trying fallback models...")
                    continue
                # For other errors, break and raise immediately
                break
        
        # If we get here, all models failed
        error_msg = str(last_error) if last_error else "Unknown error"
        logger.error(f"Error generating text with OpenAI: {error_msg}", exc_info=True)
        if "model_not_found" in error_msg or "does not have access" in error_msg:
            raise Exception(f"OpenAI API error: None of the attempted models are available. Tried: {', '.join(models_to_try)}. Please set OPENAI_MODEL environment variable to a model your project has access to. Original error: {error_msg}")
        raise Exception(f"OpenAI API error: {error_msg}")
    
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
            
            # Check API key validity by attempting a small API call
            # Note: OpenAI doesn't provide a direct "credits" endpoint via API
            # We'll verify the key works and provide dashboard link for actual credits
            try:
                # Make a minimal test call (1 token) to verify API key works
                test_response = self.client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[{"role": "user", "content": "hi"}],
                    max_tokens=1
                )
                
                # Extract usage information
                usage = test_response.usage
                tokens_used = usage.total_tokens if usage else 0
                
                # API key is valid and working
                return {
                    'success': True,
                    'message': 'API Active - Check Dashboard for Credits',
                    'status': 'operational',
                    'model': self.model,
                    'test_tokens_used': tokens_used,
                    'note': 'OpenAI API is active. Check dashboard for remaining credits/balance.',
                    'dashboard_url': 'https://platform.openai.com/usage',
                    'balance_url': 'https://platform.openai.com/account/billing',
                    'credits_note': 'Actual credit balance must be checked in OpenAI dashboard'
                }
            except Exception as api_error:
                # If the API call fails, the key might be invalid or rate limited
                error_msg = str(api_error)
                if "insufficient_quota" in error_msg.lower() or "quota" in error_msg.lower():
                    return {
                        'success': False,
                        'message': 'Insufficient Credits/Quota',
                        'status': 'no_credits',
                        'error': 'quota_exceeded',
                        'dashboard_url': 'https://platform.openai.com/account/billing',
                        'note': 'Please add credits to your OpenAI account.'
                    }
                elif "invalid_api_key" in error_msg.lower() or "authentication" in error_msg.lower():
                    return {
                        'success': False,
                        'message': 'Invalid API Key',
                        'status': 'invalid_key',
                        'error': 'authentication_failed'
                    }
                else:
                    # Other errors - still show as configured but with warning
                    logger.warning(f"OpenAI API test call failed: {error_msg}")
                    return {
                        'success': True,
                        'message': 'API Key Configured (Status Unknown)',
                        'status': 'unknown',
                        'error_detail': error_msg[:100],  # Truncate long errors
                        'dashboard_url': 'https://platform.openai.com/usage',
                        'note': 'Unable to verify API status. Check dashboard for details.'
                    }
                
        except Exception as e:
            logger.error(f"Error fetching credit info: {str(e)}", exc_info=True)
            return {
                'success': False,
                'error': str(e),
                'message': 'Could not retrieve credit information'
            }

