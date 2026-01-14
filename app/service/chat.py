import json
from typing import List
from firecrawl import Firecrawl
import requests

from app.agent.agent import AirpodAgent
from app.models.chat import ChatRequest, ChatResponse
from app.utils.store import messages_store
from app.core.settings import settings

class ChatService:
    def __init__(self):
        self.agent = AirpodAgent().get_agent()

    def chat(self, request: ChatRequest) -> ChatResponse:
        # Add user message to store
        messages_store.add_message(request.conversation_id, "user", request.message)
        
        # Get full conversation history
        messages = messages_store.get_messages_for_llm(request.conversation_id)
        
        response = self.agent.invoke(messages)
        
        # Extract assistant response and add to store
        assistant_message = response["messages"][-1].content
        messages_store.add_message(request.conversation_id, "assistant", assistant_message)
        
        return ChatResponse(
            message=assistant_message,
            citations=[],
            conversation_id=request.conversation_id
        )

    def stream(self, request: ChatRequest):
        # Add user message to store
        messages_store.add_message(request.conversation_id, "user", request.message)
        
        # Get full conversation history
        messages = messages_store.get_messages_for_llm(request.conversation_id)
        
        full_response = ""
        all_citations = []

        
        
        for token, metadata in self.agent.stream(messages, stream_mode="messages"):
            node = metadata.get('langgraph_node', '')

            # Check if the token has tool calls
            if hasattr(token, 'tool_calls') and token.tool_calls:
                for tool_call in token.tool_calls:
                    event = {
                        "type": "tool_call",
                        "node": node,
                        "data": {
                            "name": tool_call.get("name", ""),
                            "args": tool_call.get("args", {}),
                            "id": tool_call.get("id", "")
                        }
                    }
                    yield f"data: {json.dumps(event)}\n\n"
            
            # Check for content_blocks (Google Gemini structure)
            elif hasattr(token, 'content_blocks') and token.content_blocks:
                for block in token.content_blocks:
                    if not isinstance(block, dict):
                        continue
                    
                    block_type = block.get("type", "")
                    
                    # Handle reasoning/thinking blocks
                    if block_type == "reasoning":
                        reasoning_text = block.get("reasoning", "")
                        if reasoning_text:
                            event = {
                                "type": "reasoning",
                                "node": node,
                                "data": reasoning_text
                            }
                            yield f"data: {json.dumps(event)}\n\n"
                    
                    # Handle text blocks with optional annotations/citations
                    elif block_type == "text":
                        text = block.get("text", "")
                        if text:
                            full_response += text
                        
                        # Extract citations from annotations
                        annotations = block.get("annotations", [])
                        citations = []
                        formatted_text = full_response
                        
                        # Sort by end_index in reverse to avoid position shifts
                        sorted_annotations = sorted(
                            [a for a in annotations if a.get("type") == "citation"],
                            key=lambda x: x.get("end_index", 0),
                            reverse=True
                        )
                        
                        # Track citation number (in reverse since we process from end to start)
                        citation_num = len(sorted_annotations)
                        
                        for ann in sorted_annotations:
                            url = ann.get("url", "")
                            citations.append({
                                "id": ann.get("id", ""),
                                "url": url,
                                "title": ann.get("title", ""),
                                "end_index": ann.get("end_index", 0),
                                "cited_text": ann.get("cited_text", ""),
                                "citation_number": citation_num
                            })
                            all_citations.append(citations[-1])
                            
                            end_idx = ann.get("end_index", 0)
                            if isinstance(end_idx, int) and end_idx > 0:
                                # Insert numbered hyperlink like [1](url)
                                hyperlink = f" [[{citation_num}]]({url})"
                                formatted_text = formatted_text[:end_idx] + hyperlink + formatted_text[end_idx:]
                            
                            citation_num -= 1
                        
                        print("full_response:", full_response)
                        print("formatted_text:", formatted_text)

                        
                        event = {
                            "type": "text",
                            "node": node,
                            "data": text,
                        }
                        if citations:
                            event["citations"] = citations
                        
                        yield f"data: {json.dumps(event)}\n\n"
            
            # Fallback: check for plain content attribute
            elif hasattr(token, 'content') and token.content:
                if isinstance(token.content, str):
                    full_response += token.content
                    event = {
                        "type": "text",
                        "node": node,
                        "data": token.content
                    }
                    yield f"data: {json.dumps(event)}\n\n"
        
        # Store the complete assistant response
        if full_response:
            messages_store.add_message(request.conversation_id, "assistant", full_response)
        
        # Send final event with all citations
        if all_citations:
            event = {
                "type": "citations",
                "data": all_citations
            }
            yield f"data: {json.dumps(event)}\n\n"

            # Scrape images from citations
            image_links = self.scrape_images(all_citations)

            # Send images event
            if image_links:
                event = {
                    "type": "images",
                    "data": image_links
                }
                yield f"data: {json.dumps(event)}\n\n"

        # Send done event
        yield f"data: {json.dumps({'type': 'done'})}\n\n"

    def scrape_images(self, sources) -> List[str]:
        """
        Scrapes images from the given sources using firecrawl

        Returns:
            List[str]: List of image links
        """

        if not sources:
            return []

        url = settings.FIRECRAWL_API_URL
        headers = {
            "Authorization": f"Bearer {settings.FIRECRAWL_API_KEY}",
            "Content-Type": "application/json"
        }

        all_results = []
        image_links = []

        # Scrape images from each source [Can be optimised via batch or async background processing]
        for source in sources:
            source_url = source.get("url")
            if not source_url:
                continue

            payload = {
                "url": source_url,
                "onlyMainContent": False,
                "maxAge": 172800000,
                "parsers": ["pdf"],
                "formats": [
                    {
                        "type": "json",
                        "schema": {
                            "type": "object",
                            "required": [],
                            "properties": {
                                "company_name": {
                                    "type": "string"
                                },
                                "company_description": {
                                    "type": "string"
                                },
                                "imageUrl": {
                                    "type": "array",
                                    "items": {
                                        "type": "object",
                                        "required": [],
                                        "properties": {}
                                    }
                                }
                            }
                        },
                        "prompt": "Extract any images present on the page."
                    }
                ]
            }

            response = requests.post(url, json=payload, headers=headers)
            result = response.json()
            all_results.append(result)

            # Extract ogImage from data -> metadata -> ogImage
            og_image = result.get("data", {}).get("metadata", {}).get("ogImage")
            if og_image:
                image_links.append(og_image)

        return image_links