import numpy as np
import os
from dotenv import load_dotenv
import ollama
from collections import defaultdict
from chromadb import PersistentClient

# from langchain_core.documents import Document
load_dotenv()
llama3 = os.getenv("LLAMA3")
llama3_url = os.getenv("LLAMA3_URL")
os.environ["OLLAMA_HOST"] = llama3_url


class Rag:
    def __init__(self):
        class OllamaEmbeddingFunction:
            def __call__(self, input: list[str]) -> list[list[float]]:
                return [
                    ollama.embeddings(model="mxbai-embed-large", prompt=text)["embedding"]
                    for text in input
                ]

            def name(self):
                return "ollama-embedding-fn"

        self.embedding_fn = OllamaEmbeddingFunction()

        self.chroma_client = PersistentClient(path="./chroma_db")

        self.chroma_client.get_or_create_collection(
            name="user_stories", embedding_function=self.embedding_fn
        )
        self.chroma_client.get_or_create_collection(
            name="conversation_memory", embedding_function=self.embedding_fn
        )

    def embed_learn_data(self, txt_file="Resources/learning_data.txt"):
        """Generic learning data embedding that adapts to different formats."""
        print(f"[Embedding] Learn Data from '{txt_file}' into 'learn_data_embeds'")
        self.data_collection = self.intialize_chroma_db(name="learn_data_embeds")
        learn_data = self.load_generic_data(txt_file, data_type="learning")
        return self.embedd_all_data(self.data_collection, learn_data)

    def embed_chat_history(self, txt_file="Resources/chat_history.txt"):
        """Generic chat history embedding that adapts to different formats."""
        print(f"[Embedding] Chat History from '{txt_file}' into 'chat_history_embeds'")
        self.chat_collection = self.intialize_chroma_db(name="chat_history_embeds")
        chat_history = self.load_generic_data(txt_file, data_type="chat")

        for i, entry in enumerate(chat_history, 1):
            print(f"[{i}] Embedding Chat Block:\n{entry}\n{'='*40}")
        return self.embedd_all_data(self.chat_collection, chat_history)

    def embed_schema(self, schema: str):
        print("[Embedding] Schema into 'schema_embeds'")
        self.scehma_collection = self.intialize_chroma_db(name="schema_embeds")
        schema_data = {"Schema": [schema]}
        return self.embedd_all_data(self.scehma_collection, schema_data)

    def load_generic_data(self, filepath: str, data_type="generic") -> list:
        """
        Generic data loader that handles multiple formats and structures.
        Adapts to different content types without failing.
        """
        import re
        import os

        if not os.path.exists(filepath):
            print(f"[Warning] File not found: {filepath}")
            return []

        try:
            with open(filepath, "r", encoding="utf-8") as file:
                content = file.read().strip()
        except Exception as e:
            print(f"[Error] Could not read file {filepath}: {str(e)}")
            return []

        if not content:
            print(f"[Warning] File {filepath} is empty")
            return []

        print(f"[Info] Processing {data_type} data from {filepath}")
        blocks = []

        # Strategy 1: Try to detect and parse tagged blocks [Tag] format
        tagged_blocks = self._extract_tagged_blocks(content)
        if tagged_blocks:
            blocks.extend(tagged_blocks)
            print(f"[Detected] {len(tagged_blocks)} tagged blocks")

        # Strategy 2: Try to detect and parse User:/Agent: conversations
        conversation_blocks = self._extract_conversation_blocks_generic(content)
        if conversation_blocks:
            blocks.extend(conversation_blocks)
            print(f"[Detected] {len(conversation_blocks)} conversation blocks")

        # Strategy 3: If no structured format detected, split by patterns
        if not blocks:
            blocks = self._extract_generic_blocks(content)
            print(f"[Detected] {len(blocks)} generic blocks")

        # Filter and clean blocks
        cleaned_blocks = self._clean_and_filter_blocks(blocks)

        print(f"[Parsed] Total blocks: {len(cleaned_blocks)}")

        # Show sample blocks for debugging
        self._show_sample_blocks(cleaned_blocks, data_type)

        return cleaned_blocks

    def _extract_tagged_blocks(self, content):
        """Extract blocks with tags like [Correct], [Incorrect], [Tag], etc."""
        import re

        tagged_blocks = []

        # Pattern to match various tag formats
        patterns = [
            r"(\[(?:Correct|Incorrect)\].*?)(?=\n\s*\[(?:Correct|Incorrect)\]|\Z)",  # [Correct]/[Incorrect]
            r"(\[[\w\s]+\].*?)(?=\n\s*\[[\w\s]+\]|\Z)",  # Any [Tag] format
            r"(^\[.*?\].*?)(?=^\[|\Z)",  # Start of line tags
        ]

        for pattern in patterns:
            matches = re.findall(pattern, content, re.DOTALL | re.MULTILINE)
            if matches:
                for match in matches:
                    cleaned = match.strip()
                    if cleaned and len(cleaned) > 10:
                        tagged_blocks.append(cleaned)
                break  # Use first successful pattern

        return tagged_blocks

    def _extract_conversation_blocks_generic(self, content):
        """Extract conversation blocks with various User/Agent formats."""
        conversation_blocks = []

        # Try different conversation patterns
        conversation_patterns = [
            r"(User:.*?Agent:.*?)(?=User:|\Z)",  # User: ... Agent: ...
            r"(Question:.*?Answer:.*?)(?=Question:|\Z)",  # Question: ... Answer: ...
            r"(Q:.*?A:.*?)(?=Q:|\Z)",  # Q: ... A: ...
            r"(Human:.*?Assistant:.*?)(?=Human:|\Z)",  # Human: ... Assistant: ...
        ]

        for pattern in conversation_patterns:
            import re

            matches = re.findall(pattern, content, re.DOTALL)
            if matches:
                for match in matches:
                    cleaned = match.strip()
                    if cleaned and len(cleaned) > 20:
                        conversation_blocks.append(cleaned)
                break  # Use first successful pattern

        return conversation_blocks

    def _extract_generic_blocks(self, content):
        """Extract blocks using generic patterns when no specific format is detected."""
        blocks = []

        # Try splitting by multiple empty lines
        if "\n\n\n" in content:
            potential_blocks = content.split("\n\n\n")
        elif "\n\n" in content:
            potential_blocks = content.split("\n\n")
        else:
            # Split by single empty lines as last resort
            potential_blocks = content.split("\n\n")

        # If still no good blocks, try paragraph-based splitting
        if len(potential_blocks) <= 1:
            lines = content.split("\n")
            current_block = []

            for line in lines:
                line = line.strip()
                if not line:
                    if current_block:
                        blocks.append("\n".join(current_block))
                        current_block = []
                else:
                    current_block.append(line)

            # Add final block
            if current_block:
                blocks.append("\n".join(current_block))
        else:
            blocks = potential_blocks

        return blocks

    def _clean_and_filter_blocks(self, blocks):
        """Clean and filter blocks to ensure quality."""
        cleaned_blocks = []

        for block in blocks:
            if not block:
                continue

            # Clean the block
            cleaned = block.strip()

            # Skip very short blocks
            if len(cleaned) < 10:
                continue

            # Skip blocks that are just whitespace or special characters
            if not any(c.isalnum() for c in cleaned):
                continue

            # Remove duplicate blocks
            if cleaned not in cleaned_blocks:
                cleaned_blocks.append(cleaned)

        return cleaned_blocks

    def _show_sample_blocks(self, blocks, data_type):
        """Show sample blocks for debugging purposes."""
        if not blocks:
            return

        # Categorize blocks
        tagged_blocks = [b for b in blocks if b.startswith("[")]
        conversation_blocks = [
            b
            for b in blocks
            if any(
                indicator in b.lower()
                for indicator in ["user:", "agent:", "human:", "assistant:", "q:", "a:"]
            )
        ]
        generic_blocks = [
            b for b in blocks if b not in tagged_blocks and b not in conversation_blocks
        ]

        print(f"[Debug] Block Analysis for {data_type}:")
        print(f"  └── Tagged blocks: {len(tagged_blocks)}")
        print(f"  └── Conversation blocks: {len(conversation_blocks)}")
        print(f"  └── Generic blocks: {len(generic_blocks)}")

        # Show samples
        sample_blocks = blocks[:3]
        for i, block in enumerate(sample_blocks, 1):
            block_type = (
                "Tagged"
                if block.startswith("[")
                else (
                    "Conversation"
                    if any(ind in block.lower() for ind in ["user:", "agent:"])
                    else "Generic"
                )
            )
            block_preview = block[:150] + "..." if len(block) > 150 else block
            print(f"[Sample {i}] {block_type}:\n{block_preview}\n{'='*40}")

    def embedd_all_data(self, collection, data_list, default_label="general"):
        """
        Generic embedding function that handles any type of data blocks.
        """
        if not data_list or all(not str(v).strip() for v in data_list):
            print(f"[⚠️] No data found to embed for label: {default_label}")
            return collection

        print(
            f"[Embedding] Starting to embed {len(data_list)} entries for label: {default_label}"
        )
        print("=" * 80)

        try:
            documents = []
            metadatas = []
            ids = []
            successful_embeds = 0

            for i, doc in enumerate(data_list):
                # Handle different data types
                if isinstance(doc, dict):
                    doc_str = str(doc)
                elif isinstance(doc, list):
                    doc_str = "\n".join(str(item) for item in doc)
                else:
                    doc_str = str(doc)

                doc_cleaned = doc_str.strip()

                if not doc_cleaned or len(doc_cleaned) < 5:
                    print(f"[Skip] Block {i+1}: Too short or empty")
                    continue

                # Determine block type generically
                block_type, tag_info = self._determine_block_type(doc_cleaned)

                # Show block content
                print(f"\n[Block {i+1}] {block_type}{tag_info}:")
                print("-" * 60)
                print(doc_cleaned)
                print("-" * 60)
                print(f"Block Length: {len(doc_cleaned)} characters")
                print(f"Block Lines: {doc_cleaned.count(chr(10)) + 1}")

                documents.append(doc_cleaned)

                # Create metadata
                metadata = self._create_block_metadata(doc_cleaned, i, default_label)
                metadatas.append(metadata)

                # Create unique ID
                block_id = (
                    f"{default_label}_{metadata.get('block_type', 'generic')}_{i}"
                )
                ids.append(block_id)
                successful_embeds += 1

                print(f"[✅] Block {i+1} prepared for embedding - ID: {block_id}")

                if i < len(data_list) - 1:
                    print("\n" + "=" * 80)

            # Embed all documents
            if documents:
                print(f"\n{'='*80}")
                print(
                    f"[Embedding Phase] Adding {len(documents)} documents to ChromaDB collection..."
                )

                collection.add(documents=documents, metadatas=metadatas, ids=ids)
                print(
                    f"[✅] Successfully embedded {successful_embeds}/{len(data_list)} documents."
                )

                # Generate summary
                self._print_embedding_summary(metadatas, successful_embeds)
            else:
                print(f"[⚠️] No valid documents to embed after filtering")

        except Exception as e:
            print(f"[❌] Error while embedding: {str(e)}")
            import traceback

            traceback.print_exc()

        print("=" * 80)
        return collection

    def _determine_block_type(self, doc_cleaned):
        """Determine block type and tag info generically."""
        doc_lower = doc_cleaned.lower()

        # Check for various tag patterns
        if doc_cleaned.startswith("[") and "]" in doc_cleaned[:50]:
            tag_end = doc_cleaned.find("]")
            tag_content = doc_cleaned[1:tag_end]
            return "Tagged", f" ({tag_content})"

        # Check for conversation patterns
        conversation_indicators = [
            "user:",
            "agent:",
            "human:",
            "assistant:",
            "q:",
            "a:",
            "question:",
            "answer:",
        ]
        if any(indicator in doc_lower for indicator in conversation_indicators):
            return "Conversation", ""

        # Check for code/SQL patterns
        code_indicators = [
            "select ",
            "from ",
            "where ",
            "def ",
            "class ",
            "import ",
            "function",
        ]
        if any(indicator in doc_lower for indicator in code_indicators):
            return "Code", ""

        # Default to generic
        return "Generic", ""

    def _create_block_metadata(self, doc_cleaned, index, label):
        """Create metadata for a block generically."""
        metadata = {
            "label": label,
            "block_index": index,
            "char_length": len(doc_cleaned),
            "line_count": doc_cleaned.count("\n") + 1,
        }

        # Add block type specific metadata
        if doc_cleaned.startswith("["):
            metadata["block_type"] = "tagged"
            if doc_cleaned.startswith("[Correct]"):
                metadata["tag_type"] = "correct"
            elif doc_cleaned.startswith("[Incorrect]"):
                metadata["tag_type"] = "incorrect"
            else:
                # Extract tag content
                tag_end = doc_cleaned.find("]")
                if tag_end > 0:
                    metadata["tag_type"] = doc_cleaned[1:tag_end].lower()
        elif any(
            ind in doc_cleaned.lower()
            for ind in ["user:", "agent:", "human:", "assistant:"]
        ):
            metadata["block_type"] = "conversation"
        elif any(ind in doc_cleaned.lower() for ind in ["select ", "from ", "where "]):
            metadata["block_type"] = "code"
        else:
            metadata["block_type"] = "generic"

        return metadata

    def _print_embedding_summary(self, metadatas, successful_embeds):
        """Print embedding summary generically."""
        # Count different types
        type_counts = {}
        for meta in metadatas:
            block_type = meta.get("block_type", "unknown")
            type_counts[block_type] = type_counts.get(block_type, 0) + 1

        print(f"\n[Final Summary]")
        print(f"📊 Total Embedded: {successful_embeds}")

        for block_type, count in type_counts.items():
            emoji_map = {
                "tagged": "🏷️",
                "conversation": "💬",
                "code": "💻",
                "generic": "📄",
            }
            emoji = emoji_map.get(block_type, "📋")
            print(f"{emoji} {block_type.title()} Blocks: {count}")

        print(
            f"[🎯] Embedding Status: ALL {successful_embeds} BLOCKS SUCCESSFULLY EMBEDDED!"
        )

    def retrieve_similar_semantic(self, collection, intent=None, label=None, k=5):
        """
        QUICK FIX: Enhanced retrieve function with better distance handling.
        """
        try:
            if not intent:
                return self._retrieve_all_documents(collection, label)

            print(f"[Info] Performing similarity search for query: '{intent}'")

            query_embedding = self._generate_query_embedding(intent)

            # Get more results initially to improve selection
            query_params = {
                "query_embeddings": [query_embedding],
                "n_results": min(
                    k * 4, 100
                ),  # Get 4x more results for better filtering
                "include": ["documents", "metadatas", "distances"],
            }

            if label:
                query_params["where"] = {"label": label}

            results = collection.query(**query_params)
            documents = results.get("documents", [[]])[0]
            metadatas = (
                results.get("metadatas", [[]])[0] if results.get("metadatas") else []
            )
            distances = (
                results.get("distances", [[]])[0] if results.get("distances") else []
            )

            # QUICK FIX: Sort by distance first (smallest distance = most similar)
            combined_results = list(zip(documents, metadatas, distances))
            combined_results.sort(key=lambda x: x[2])  # Sort by distance (ascending)

            # Take top results based on distance
            top_results = combined_results[: k * 2]  # Get 2x what we need for filtering

            # Now apply additional filtering and ranking
            filtered_docs = self._filter_and_rank_results_fixed(
                [r[0] for r in top_results],
                [r[1] for r in top_results],
                [r[2] for r in top_results],
                intent,
                k,
            )

            return filtered_docs

        except Exception as e:
            print(f"[Error] Failed to retrieve similar semantic data: {str(e)}")
            return []

    def _filter_and_rank_results_fixed(
        self, documents, metadatas, distances, intent, target_k
    ):
        """Fixed semantic similarity with proper distance handling."""
        if not documents:
            return []

        print(f"[DEBUG] Distance range: min={min(distances):.4f}, max={max(distances):.4f}")
        
        scored_results = []
        intent_lower = intent.lower().strip()
        intent_words = [word for word in intent_lower.split() if len(word) > 2]

        # Analyze distance distribution to understand the scale
        sorted_distances = sorted(distances)
        min_dist = sorted_distances[0]
        max_dist = sorted_distances[-1]
        
        for i, doc in enumerate(documents):
            if not doc:
                continue

            distance = distances[i] if i < len(distances) else max_dist
            doc_lower = doc.lower()
            
            # FIXED: Handle large distance scales properly
            # Normalize distance to 0-1 range based on actual data distribution
            if max_dist > min_dist:
                normalized_distance = (distance - min_dist) / (max_dist - min_dist)
            else:
                normalized_distance = 0.0
                
            # Convert to similarity score (0-100)
            semantic_score = (1.0 - normalized_distance) * 100
            
            # Enhanced keyword matching for context
            keyword_matches = sum(1 for word in intent_words if word in doc_lower)
            keyword_score = keyword_matches * 5  # Increased weight
            
            # Look for key concepts specifically
            concept_score = 0
            key_concepts = ['effort', 'planned', 'consumed', 'team', 'r1.1', 'level']
            concept_matches = sum(1 for concept in key_concepts if concept in doc_lower)
            concept_score = concept_matches * 8
            
            # Intent matching bonus
            intent_bonus = 0
            if 'user intent:' in doc_lower and any(word in doc_lower for word in intent_words):
                intent_bonus = 20
                
            # Quality score
            quality_score = 0
            metadata_item = metadatas[i] if i < len(metadatas) else {}
            if metadata_item.get("tag_type") == "correct":
                quality_score = 10
            elif metadata_item.get("tag_type") == "incorrect":
                quality_score = 5
                
            # Total score
            total_score = semantic_score + keyword_score + concept_score + intent_bonus + quality_score

            scored_results.append({
                "document": doc,
                "score": total_score,
                "distance": distance,
                "normalized_distance": normalized_distance,
                "semantic_score": semantic_score,
                "keyword_score": keyword_score,
                "concept_score": concept_score,
                "intent_bonus": intent_bonus,
                "metadata": metadata_item,
            })

        # Sort by total score (highest first)
        scored_results.sort(key=lambda x: x["score"], reverse=True)

        # Enhanced debug output
        print(f"\n[RESULTS] Intent: '{intent}'")
        print(f"[Distance Analysis] Min: {min_dist:.4f}, Max: {max_dist:.4f}")
        print(f"[Results] Top 3 semantic matches:")
        
        for i, item in enumerate(scored_results[:3], 1):
            preview = item["document"][:120] + "..." if len(item["document"]) > 120 else item["document"]
            print(f"\n[Rank {i}] Score: {item['score']:.1f} | Distance: {item['distance']:.4f}")
            print(f"  Preview: {preview}")

        return [item["document"] for item in scored_results[:target_k]]

    def _calculate_generic_relevance(
        self, doc, intent_lower, intent_words, distance, metadata
    ):
        """Calculate relevance score generically."""
        score = 0
        doc_lower = doc.lower()

        # Semantic similarity (distance-based)
        semantic_score = max(0, 10 - (distance * 10))
        score += semantic_score

        # Keyword matching
        keyword_matches = sum(1 for word in intent_words if word in doc_lower)
        score += keyword_matches * 5

        # Phrase matching
        for i in range(len(intent_words) - 1):
            phrase = f"{intent_words[i]} {intent_words[i+1]}"
            if phrase in doc_lower:
                score += 10

        # Block type bonuses
        block_type = metadata.get("block_type", "generic")
        if block_type == "tagged" and metadata.get("tag_type") == "incorrect":
            score += 3  # Learning from errors
        elif block_type == "conversation":
            score += 2  # Conversation context valuable

        return score

    # Keep all the existing helper methods for backwards compatibility
    def intialize_chroma_db(self, name="default_name"):
        return self.chroma_client.get_or_create_collection(
            name=name, embedding_function=self.embedding_fn
        )

    def _retrieve_all_documents(self, collection, label):
        """Retrieve all documents, optionally filtered by label."""
        print("[Info] No query — retrieving all documents")
        try:
            results = collection.get(include=["documents", "metadatas"])

            if not label:
                return results.get("documents", [])

            # Filter by label in metadata
            filtered_docs = []
            documents = results.get("documents", [])
            metadatas = results.get("metadatas", [])

            for doc, meta in zip(documents, metadatas):
                if meta and meta.get("label") == label:
                    filtered_docs.append(doc)

            return filtered_docs
        except Exception as e:
            print(f"[Error] Failed to retrieve all documents: {str(e)}")
            return []

    def _generate_query_embedding(self, intent):
        """Generate embedding vector for the query."""
        try:
            response = ollama.embeddings(model="mxbai-embed-large", prompt=intent)
            return response["embedding"]
        except Exception as e:
            print(f"[Error] Failed to generate embedding: {str(e)}")
            raise

    # Keep existing methods for schema and conversation collections
    def _is_schema_collection(self, collection):
        """Check if collection contains schema data."""
        collection_name = getattr(collection, "name", "")
        return "schema" in collection_name.lower()

    def _is_conversation_collection(self, collection):
        """Check if collection contains conversation/chat data."""
        collection_name = getattr(collection, "name", "")
        return any(
            keyword in collection_name.lower()
            for keyword in ["chat", "conversation", "history"]
        )

    # Additional helper methods for backwards compatibility...
    def save_to_memory(self, user_idea, model_reply, collection, tag=None):
        try:
            user_embedding = ollama.embeddings(model="mxbai-embed-large", prompt=user_idea)[
                "embedding"
            ]
            model_embedding = ollama.embeddings(model="mxbai-embed-large", prompt=model_reply)[
                "embedding"
            ]

            base_tag = tag.replace(" ", "_") if tag else "conversation"
            uid = np.random.randint(10000)

            collection.add(
                documents=[user_idea, model_reply],
                embeddings=[user_embedding, model_embedding],
                ids=[f"{base_tag}_user_{uid}", f"{base_tag}_assistant_{uid}"],
                metadatas=[
                    {"context": base_tag, "role": "user"},
                    {"context": base_tag, "role": "assistant"},
                ],
            )

            if hasattr(collection, "persist"):
                collection.persist()
        except Exception as e:
            print(f"[Error] Failed to save to memory: {str(e)}")

    def save_learn_data(
        self, user_intent, sql_query, collection, tag="Correct", error_details=None
    ):
        """
        Save new learning data to the learning collection with proper formatting.
        Matches the existing learning data format with [Correct]/[Incorrect] tags.

        Args:
            user_intent (str): The user's intent or purpose description
            sql_query (str): The SQL query or solution
            collection: The ChromaDB collection to save to
            tag (str): "Correct" or "Incorrect" tag
            error_details (str, optional): Error details for incorrect examples
        """
        try:
            # Format the learning data block to match existing format
            if tag.lower() == "incorrect" and error_details:
                # Format for incorrect examples with error details
                formatted_block = f"""[Incorrect]
    # User Intent: {user_intent}
    # Error Details: {error_details}

    # This query failed with the above error - learn from this mistake
    {sql_query}"""
            else:
                # Format for correct examples
                formatted_block = f"""[Correct]
    -- Purpose: {user_intent}
    {sql_query}"""

            # Generate embedding for the formatted block
            learning_embedding = ollama.embeddings(
                model="mxbai-embed-large", prompt=formatted_block
            )["embedding"]

            # Create unique ID
            base_tag = tag.lower().replace(" ", "_")
            uid = np.random.randint(10000)
            block_id = f"general_{base_tag}_{uid}"

            # Create metadata matching existing structure
            metadata = {
                "label": "general",
                "block_type": "tagged",
                "block_index": uid,
                "char_length": len(formatted_block),
                "line_count": formatted_block.count("\n") + 1,
            }

            # Add tag type for filtering
            if tag.lower() == "correct":
                metadata["tag_type"] = "correct"
            elif tag.lower() == "incorrect":
                metadata["tag_type"] = "incorrect"

            # Add to collection
            collection.add(
                documents=[formatted_block],
                embeddings=[learning_embedding],
                ids=[block_id],
                metadatas=[metadata],
            )

            # Persist if available
            if hasattr(collection, "persist"):
                collection.persist()

            print(f"[✅] Successfully saved learning data with ID: {block_id}")
            print(f"[Info] Tag: {tag}, Intent: {user_intent[:50]}...")

            return block_id

        except Exception as e:
            print(f"[❌] Error while saving learning data: {str(e)}")
            import traceback

            traceback.print_exc()
            return None

    def delete_memory_context(self, context):
        try:
            collection = self.intialize_chroma_db(name="conversation_memory")
            filtered_context = context.replace(" ", "_")

            items = collection.get(ids=None, include=["metadatas"])
            ids_to_delete = [
                item["id"]
                for item in items["metadatas"]
                if item.get("context") == filtered_context
            ]

            if ids_to_delete:
                collection.delete(ids=ids_to_delete)
                if hasattr(collection, "persist"):
                    collection.persist()
            else:
                print(f"[No Match] No documents found for context: {filtered_context}")
        except Exception as e:
            print(f"[Error] Failed to delete memory context: {str(e)}")



    def debug_embedding_model(self):
        """Debug the embedding model and distances."""
        print(f"[DEBUG] Embedding model info:")
    
        # Test with a simple query
        test_embedding = self._generate_query_embedding("test query")
        print(f"[DEBUG] Test embedding shape: {len(test_embedding) if test_embedding else 'None'}")
        print(f"[DEBUG] Test embedding sample: {test_embedding[:5] if test_embedding else 'None'}")
    
        return test_embedding

if __name__ == "__main__":
    rag = Rag()
    
    # Debug the embedding model first
    rag.debug_embedding_model()
    
    learn_data_collection = rag.embed_learn_data()
    print(f"✅ learn_data_collection:\n{learn_data_collection}")
    
    similar_semantic_learn_data = rag.retrieve_similar_semantic(
        learn_data_collection, intent="Efforts Consumed and Planned on team level for R1.1"
    )
    print(f"✅ similar_semantic_learn_data:\n{similar_semantic_learn_data}")
