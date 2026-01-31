import os
import httpx
import json
import asyncio
from typing import List, Dict
from config import get_config
from security import SecurityValidator
from logger import logger

config = get_config()

class GeminiClient:
    def __init__(self):
        self.api_key = config.gemini_api_key
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY environment variable is required")
        
        self.base_url = "https://generativelanguage.googleapis.com/v1beta"
        self.model = config.gemini_model
    
    async def expand_knowledge(self, raw_text: str, source_tag: str, domain: str = "general") -> List[Dict]:
        """Process raw text into structured knowledge using single prompt strategy"""
        
        # Truncate input if too long
        if len(raw_text) > config.max_context_length:
            raw_text = raw_text[:config.max_context_length]
        
        prompt = f"""
Process the following raw text into structured knowledge entries. Extract multiple knowledge entries if applicable.

Raw Text: {raw_text}
Source: {source_tag}

Requirements:
1. Extract all relevant topics/concepts
2. Remove any hallucinations or unverified claims
3. Add confidence scores (0.0-1.0) based on information quality
4. Add risk levels (low/medium/high) based on potential impact
5. Output valid JSON array only
6. Maximum 10 entries

Output Format (JSON Array):
[
  {{
    "topic": "specific topic name",
    "symptoms_or_keywords": ["keyword1", "keyword2"],
    "response_guidance": "how to respond about this topic",
    "risk_level": "low/medium/high",
    "confidence": "0.0-1.0",
    "source": "{source_tag}"
  }}
]

Return only the JSON array, no other text or formatting.
"""
        
        async with httpx.AsyncClient(timeout=config.api_timeout) as client:
            payload = {
                "contents": [{
                    "parts": [{"text": prompt}]
                }],
                "generationConfig": {
                    "temperature": 0.3,
                    "maxOutputTokens": 2048,
                    "topP": 0.8,
                    "topK": 40
                },
                "safetySettings": [
                    {
                        "category": "HARM_CATEGORY_HARASSMENT",
                        "threshold": "BLOCK_MEDIUM_AND_ABOVE"
                    },
                    {
                        "category": "HARM_CATEGORY_HATE_SPEECH",
                        "threshold": "BLOCK_MEDIUM_AND_ABOVE"
                    },
                    {
                        "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                        "threshold": "BLOCK_MEDIUM_AND_ABOVE"
                    },
                    {
                        "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
                        "threshold": "BLOCK_MEDIUM_AND_ABOVE"
                    }
                ]
            }
            
            try:
                response = await client.post(
                    f"{self.base_url}/models/{self.model}:generateContent?key={self.api_key}",
                    json=payload
                )
                
                if response.status_code == 429:
                    # Rate limit - wait and retry once
                    await asyncio.sleep(5)
                    response = await client.post(
                        f"{self.base_url}/models/{self.model}:generateContent?key={self.api_key}",
                        json=payload
                    )
                
                if response.status_code != 200:
                    error_detail = f"Status: {response.status_code}, Body: {response.text[:200]}"
                    raise Exception(f"Gemini API error: {error_detail}")
                
                result = response.json()
                
                # Handle safety blocks
                if "candidates" not in result or not result["candidates"]:
                    if "promptFeedback" in result and "blockReason" in result["promptFeedback"]:
                        raise Exception(f"Content blocked by Gemini: {result['promptFeedback']['blockReason']}")
                    raise Exception("No candidates in Gemini response")
                
                candidate = result["candidates"][0]
                
                # Check for finish reason
                if candidate.get("finishReason") == "SAFETY":
                    raise Exception("Content blocked by Gemini safety filters")
                
                if "content" not in candidate or "parts" not in candidate["content"]:
                    raise Exception("Invalid response structure from Gemini")
                
                content = candidate["content"]["parts"][0]["text"]
                
                # Parse and validate JSON response
                return self._parse_and_validate_response(content)
                
            except httpx.TimeoutException:
                raise Exception("Gemini API request timed out")
            except httpx.RequestError as e:
                raise Exception(f"Gemini API request failed: {str(e)}")
            except json.JSONDecodeError as e:
                raise Exception(f"Failed to parse Gemini response as JSON: {str(e)}")
            except Exception as e:
                if "Gemini API" in str(e) or "Content blocked" in str(e):
                    raise
                raise Exception(f"Unexpected error calling Gemini API: {str(e)}")
    
    def _parse_and_validate_response(self, content: str) -> List[Dict]:
        """Parse and validate Gemini response"""
        try:
            # Clean up response (remove markdown if present)
            content = content.strip()
            if content.startswith("```json"):
                content = content[7:]
            elif content.startswith("```"):
                content = content[3:]
            if content.endswith("```"):
                content = content[:-3]
            
            # Parse JSON
            parsed_data = json.loads(content)
            
            # Ensure it's a list
            if not isinstance(parsed_data, list):
                parsed_data = [parsed_data] if isinstance(parsed_data, dict) else []
            
            # Limit number of entries
            if len(parsed_data) > 10:
                parsed_data = parsed_data[:10]
            
            # Validate each entry
            validated_entries = SecurityValidator.validate_knowledge_json(parsed_data)
            
            if not validated_entries:
                raise Exception("No valid knowledge entries found in Gemini response")
            
            return validated_entries
            
        except json.JSONDecodeError as e:
            raise Exception(f"Invalid JSON in Gemini response: {str(e)}")
        except Exception as e:
            if "Invalid JSON" in str(e) or "No valid knowledge" in str(e):
                raise
            raise Exception(f"Failed to process Gemini response: {str(e)}")