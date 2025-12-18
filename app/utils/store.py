from typing import Dict, List, Any


class MessagesStore:
    """Simple in-memory store for conversation messages."""
    
    def __init__(self):
        self._conversations: Dict[str, List[Dict[str, Any]]] = {}

    def add_message(self, conversation_id: str, role: str, content: str) -> None:
        """Add a message to a conversation."""
        if conversation_id not in self._conversations:
            self._conversations[conversation_id] = []
        
        self._conversations[conversation_id].append({
            "role": role,
            "content": content
        })

    def get_messages(self, conversation_id: str) -> List[Dict[str, Any]]:
        """Get all messages for a conversation."""
        return self._conversations.get(conversation_id, [])

    def get_messages_for_llm(self, conversation_id: str) -> Dict[str, List[Dict[str, Any]]]:
        """Get messages in LangGraph format."""
        return {"messages": self.get_messages(conversation_id)}

    def clear(self, conversation_id: str) -> None:
        """Clear a conversation."""
        self._conversations.pop(conversation_id, None)


# Global instance
messages_store = MessagesStore()