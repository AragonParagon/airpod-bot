import json
from app.agent.agent import AirpodAgent
from app.models.chat import ChatRequest, ChatResponse
from app.utils.store import messages_store


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
                        for ann in annotations:
                            if ann.get("type") == "citation":
                                citations.append({
                                    "id": ann.get("id", ""),
                                    "url": ann.get("url", ""),
                                    "title": ann.get("title", ""),
                                    "cited_text": ann.get("cited_text", "")
                                })
                                all_citations.append(citations[-1])
                        
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
        
        # Send done event
        yield f"data: {json.dumps({'type': 'done'})}\n\n"