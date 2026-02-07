import numpy as np
import os
from dotenv import load_dotenv
import ollama
from collections import defaultdict
from chromadb import PersistentClient

# Import centralized logger
from Utils.logger import FrameworkLogger as log

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
                    ollama.embeddings(model="mxbai-embed-large", prompt=text)[
                        "embedding"
                    ]
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
        log.info(f"Embedding Learn Data from '{txt_file}' into 'learn_data_embeds'")
        self.data_collection = self.intialize_chroma_db(name="learn_data_embeds")
        learn_data = self.load_generic_data(txt_file, data_type="learning")
        return self.embedd_all_data(self.data_collection, learn_data)

    def embed_chat_history(self, txt_file="Resources/chat_history.txt"):
        """Generic chat history embedding that adapts to different formats."""
        log.info(f"Embedding Chat History from '{txt_file}' into 'chat_history_embeds'")
        self.chat_collection = self.intialize_chroma_db(name="chat_history_embeds")
        chat_history = self.load_generic_data(txt_file, data_type="chat")

        for i, entry in enumerate(chat_history, 1):
            log.safe_print(f"[{i}] Embedding Chat Block:\n{entry}\n{'='*40}")
        return self.embedd_all_data(self.chat_collection, chat_history)

    def embed_schema(self, schema: str):
        log.safe_print("[Embedding] Schema into 'schema_embeds'")
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
            log.safe_print(f"[Warning] File not found: {filepath}")
            return []

        try:
            with open(filepath, "r", encoding="utf-8") as file:
                content = file.read().strip()
        except Exception as e:
            log.safe_print(f"[Error] Could not read file {filepath}: {str(e)}")
            return []

        if not content:
            log.safe_print(f"[Warning] File {filepath} is empty")
            return []

        log.safe_print(f"[Info] Processing {data_type} data from {filepath}")
        blocks = []

        # Strategy 1: Try to detect and parse tagged blocks [Tag] format
        tagged_blocks = self._extract_tagged_blocks(content)
        if tagged_blocks:
            blocks.extend(tagged_blocks)
            log.safe_print(f"[Detected] {len(tagged_blocks)} tagged blocks")

        # Strategy 2: Try to detect and parse User:/Agent: conversations
        conversation_blocks = self._extract_conversation_blocks_generic(content)
        if conversation_blocks:
            blocks.extend(conversation_blocks)
            log.safe_print(f"[Detected] {len(conversation_blocks)} conversation blocks")

        # Strategy 3: If no structured format detected, split by patterns
        if not blocks:
            blocks = self._extract_generic_blocks(content)
            log.safe_print(f"[Detected] {len(blocks)} generic blocks")

        # Filter and clean blocks
        cleaned_blocks = self._clean_and_filter_blocks(blocks)

        log.safe_print(f"[Parsed] Total blocks: {len(cleaned_blocks)}")

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

        log.safe_print(f"[Debug] Block Analysis for {data_type}:")
        log.safe_print(f"  +-- Tagged blocks: {len(tagged_blocks)}")
        log.safe_print(f"  +-- Conversation blocks: {len(conversation_blocks)}")
        log.safe_print(f"  +-- Generic blocks: {len(generic_blocks)}")

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
            log.safe_print(f"[Sample {i}] {block_type}:\n{block_preview}\n{'='*40}")

    def embedd_all_data(self, collection, data_list, default_label="general"):
        """
        Generic embedding function that handles any type of data blocks.
        """
        if not data_list or all(not str(v).strip() for v in data_list):
            log.safe_print(
                f"[[WARNING]] No data found to embed for label: {default_label}"
            )
            return collection

        log.safe_print(
            f"[Embedding] Starting to embed {len(data_list)} entries for label: {default_label}"
        )
        log.safe_print("=" * 80)

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
                    log.safe_print(f"[Skip] Block {i+1}: Too short or empty")
                    continue

                # Determine block type generically
                block_type, tag_info = self._determine_block_type(doc_cleaned)

                # Show block content
                log.safe_print(f"\n[Block {i+1}] {block_type}{tag_info}:")
                log.safe_print("-" * 60)
                log.safe_print(doc_cleaned)
                log.safe_print("-" * 60)
                log.safe_print(f"Block Length: {len(doc_cleaned)} characters")
                log.safe_print(f"Block Lines: {doc_cleaned.count(chr(10)) + 1}")

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

                log.safe_print(
                    f"[[OK]] Block {i+1} prepared for embedding - ID: {block_id}"
                )

                if i < len(data_list) - 1:
                    log.safe_print("\n" + "=" * 80)

            # Embed all documents
            if documents:
                log.safe_print(f"\n{'='*80}")
                log.safe_print(
                    f"[Embedding Phase] Adding {len(documents)} documents to ChromaDB collection..."
                )

                collection.add(documents=documents, metadatas=metadatas, ids=ids)
                log.safe_print(
                    f"[[OK]] Successfully embedded {successful_embeds}/{len(data_list)} documents."
                )

                # Generate summary
                self._print_embedding_summary(metadatas, successful_embeds)
            else:
                log.safe_print(
                    f"[[WARNING]] No valid documents to embed after filtering"
                )

        except Exception as e:
            log.safe_print(f"[[ERROR]] Error while embedding: {str(e)}")
            import traceback

            traceback.print_exc()

        log.safe_print("=" * 80)
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

        log.safe_print(f"\n[Final Summary]")
        log.safe_print(f">> Total Embedded: {successful_embeds}")

        for block_type, count in type_counts.items():
            emoji_map = {
                "tagged": "[TAG]",
                "conversation": "💬",
                "code": "[CODE]",
                "generic": "📄",
            }
            emoji = emoji_map.get(block_type, "[CLIPBOARD]")
            log.safe_print(f"{emoji} {block_type.title()} Blocks: {count}")

        log.safe_print(
            f"[[TARGET]] Embedding Status: ALL {successful_embeds} BLOCKS SUCCESSFULLY EMBEDDED!"
        )

    def retrieve_similar_semantic(self, collection, intent=None, label=None, k=5):
        """
        QUICK FIX: Enhanced retrieve function with better distance handling.
        """
        try:
            if not intent:
                return self._retrieve_all_documents(collection, label)

            log.safe_print(f"[Info] Performing similarity search for query: '{intent}'")

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
            log.safe_print(
                f"[Error] Failed to retrieve similar semantic data: {str(e)}"
            )
            return []

    def _filter_and_rank_results_fixed(
        self, documents, metadatas, distances, intent, target_k
    ):
        """Fixed semantic similarity with proper distance handling."""
        if not documents:
            return []

        log.safe_print(
            f"[DEBUG] Distance range: min={min(distances):.4f}, max={max(distances):.4f}"
        )

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
            key_concepts = ["effort", "planned", "consumed", "team", "r1.1", "level"]
            concept_matches = sum(1 for concept in key_concepts if concept in doc_lower)
            concept_score = concept_matches * 8

            # Intent matching bonus
            intent_bonus = 0
            if "user intent:" in doc_lower and any(
                word in doc_lower for word in intent_words
            ):
                intent_bonus = 20

            # Quality score
            quality_score = 0
            metadata_item = metadatas[i] if i < len(metadatas) else {}
            if metadata_item.get("tag_type") == "correct":
                quality_score = 10
            elif metadata_item.get("tag_type") == "incorrect":
                quality_score = 5

            # Total score
            total_score = (
                semantic_score
                + keyword_score
                + concept_score
                + intent_bonus
                + quality_score
            )

            scored_results.append(
                {
                    "document": doc,
                    "score": total_score,
                    "distance": distance,
                    "normalized_distance": normalized_distance,
                    "semantic_score": semantic_score,
                    "keyword_score": keyword_score,
                    "concept_score": concept_score,
                    "intent_bonus": intent_bonus,
                    "metadata": metadata_item,
                }
            )

        # Sort by total score (highest first)
        scored_results.sort(key=lambda x: x["score"], reverse=True)

        # Enhanced debug output
        log.safe_print(f"\n[RESULTS] Intent: '{intent}'")
        log.safe_print(f"[Distance Analysis] Min: {min_dist:.4f}, Max: {max_dist:.4f}")
        log.safe_print(f"[Results] Top 3 semantic matches:")

        for i, item in enumerate(scored_results[:3], 1):
            preview = (
                item["document"][:120] + "..."
                if len(item["document"]) > 120
                else item["document"]
            )
            log.safe_print(
                f"\n[Rank {i}] Score: {item['score']:.1f} | Distance: {item['distance']:.4f}"
            )
            log.safe_print(f"  Preview: {preview}")

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
        log.safe_print("[Info] No query — retrieving all documents")
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
            log.safe_print(f"[Error] Failed to retrieve all documents: {str(e)}")
            return []

    def _generate_query_embedding(self, intent):
        """Generate embedding vector for the query."""
        try:
            response = ollama.embeddings(model="mxbai-embed-large", prompt=intent)
            return response["embedding"]
        except Exception as e:
            log.safe_print(f"[Error] Failed to generate embedding: {str(e)}")
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
            user_embedding = ollama.embeddings(
                model="mxbai-embed-large", prompt=user_idea
            )["embedding"]
            model_embedding = ollama.embeddings(
                model="mxbai-embed-large", prompt=model_reply
            )["embedding"]

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
            log.safe_print(f"[Error] Failed to save to memory: {str(e)}")

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

            log.safe_print(
                f"[[OK]] Successfully saved learning data with ID: {block_id}"
            )
            log.safe_print(f"[Info] Tag: {tag}, Intent: {user_intent[:50]}...")

            return block_id

        except Exception as e:
            log.safe_print(f"[[ERROR]] Error while saving learning data: {str(e)}")
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
                log.safe_print(
                    f"[No Match] No documents found for context: {filtered_context}"
                )
        except Exception as e:
            log.safe_print(f"[Error] Failed to delete memory context: {str(e)}")

    # ==================== SWAGGER/API INTENT METHODS ====================

    def embed_swagger_by_resource(
        self,
        swagger_path: str,
        collection_name: str = "api_endpoints",
        force_refresh: bool = False,
    ):
        """
        Parse swagger.json, group endpoints by resource (e.g., Books, Users, Activities),
        and embed each group as a document in ChromaDB.

        Args:
            swagger_path (str): Absolute path to the swagger.json file
            collection_name (str): Name of the ChromaDB collection to create/use
            force_refresh (bool): If True, delete existing collection and re-embed

        Returns:
            ChromaDB collection with embedded API endpoints
        """
        import json

        log.safe_print(f"\n{'='*80}")
        log.safe_print(f"[Embedding] Swagger API Endpoints from '{swagger_path}'")
        log.safe_print(f"{'='*80}")

        # Handle force refresh - delete existing collection
        if force_refresh:
            try:
                self.client.delete_collection(collection_name)
                log.safe_print(
                    f"[Refresh] Deleted existing collection: {collection_name}"
                )
            except Exception:
                pass  # Collection doesn't exist, that's fine

        # Load swagger file
        try:
            with open(swagger_path, "r", encoding="utf-8") as f:
                swagger_data = json.load(f)
        except FileNotFoundError:
            log.safe_print(f"[[ERROR]] Swagger file not found: {swagger_path}")
            return None
        except json.JSONDecodeError as e:
            log.safe_print(f"[[ERROR]] Invalid JSON in swagger file: {e}")
            return None

        # Initialize collection
        api_collection = self.intialize_chroma_db(name=collection_name)

        # Extract API info
        api_info = swagger_data.get("info", {})
        base_path = swagger_data.get("servers", [{}])[0].get("url", "")
        paths = swagger_data.get("paths", {})
        schemas = swagger_data.get("components", {}).get("schemas", {})

        log.safe_print(f"[Info] API Title: {api_info.get('title', 'Unknown')}")
        log.safe_print(f"[Info] API Version: {api_info.get('version', 'Unknown')}")
        log.safe_print(f"[Info] Total Paths: {len(paths)}")

        # Group endpoints by resource (first segment after /api/v1/)
        resource_groups = self._group_endpoints_by_resource(paths, schemas)

        log.safe_print(f"[Info] Resources Found: {list(resource_groups.keys())}")

        # Embed each endpoint individually for better semantic matching
        documents = []
        metadatas = []
        ids = []
        endpoint_counter = 0

        for resource_name, resource_data in resource_groups.items():
            log.safe_print(f"\n[Resource] {resource_name}")
            log.safe_print(f"  +-- Endpoints: {len(resource_data['endpoints'])}")
            log.safe_print(f"  +-- Methods: {resource_data['methods']}")

            # Create a document for each endpoint instead of the whole resource
            for endpoint in resource_data["endpoints"]:
                endpoint_counter += 1
                doc_content = self._format_single_endpoint_document(
                    resource_name, endpoint, schemas
                )

                documents.append(doc_content)
                metadatas.append(
                    {
                        "resource": resource_name,
                        "method": endpoint["method"],
                        "path": endpoint["path"],
                        "summary": endpoint.get("summary", ""),
                        "has_path_params": "{" in endpoint["path"],
                        "has_request_body": endpoint.get("request_body") is not None,
                    }
                )
                ids.append(
                    f"api_endpoint_{endpoint_counter}_{resource_name.lower()}_{endpoint['method'].lower()}"
                )

        # Add to collection
        if documents:
            try:
                # Check if documents already exist and delete them first
                existing = api_collection.get(ids=ids)
                if existing and existing.get("ids"):
                    api_collection.delete(ids=existing["ids"])
                    log.safe_print(
                        f"[Info] Removed {len(existing['ids'])} existing documents"
                    )

                api_collection.add(documents=documents, metadatas=metadatas, ids=ids)
                log.safe_print(
                    f"\n[[OK]] Successfully embedded {len(documents)} individual endpoints"
                )
            except Exception as e:
                log.safe_print(f"[[ERROR]] Error embedding documents: {e}")
                import traceback

                traceback.print_exc()

        return api_collection

    def _format_single_endpoint_document(
        self, resource_name: str, endpoint: dict, schemas: dict
    ) -> str:
        """
        Format a single endpoint into a compact document for embedding.
        Keeps documents small enough for the embedding model's context length.
        """
        doc_parts = []

        method = endpoint["method"]
        path = endpoint["path"]

        # Header with searchable keywords
        doc_parts.append(f"Resource: {resource_name}")
        doc_parts.append(f"Endpoint: {method} {path}")

        # Add action keywords for better semantic matching
        action_keywords = self._get_action_keywords(method, path, resource_name)
        doc_parts.append(f"Actions: {action_keywords}")

        if endpoint.get("summary"):
            doc_parts.append(f"Summary: {endpoint['summary']}")
        if endpoint.get("description"):
            # Truncate long descriptions
            desc = endpoint["description"][:200]
            doc_parts.append(f"Description: {desc}")

        # Parameters (concise)
        if endpoint.get("parameters"):
            params = []
            for param in endpoint["parameters"]:
                param_str = f"{param.get('name')}({param.get('in')})"
                if param.get("required"):
                    param_str += "*"
                params.append(param_str)
            doc_parts.append(f"Parameters: {', '.join(params)}")

        # Request Body (concise)
        if endpoint.get("request_body"):
            content = endpoint["request_body"].get("content", {})
            for content_type, content_data in content.items():
                schema_ref = content_data.get("schema", {}).get("$ref", "")
                if schema_ref:
                    schema_name = schema_ref.split("/")[-1]
                    doc_parts.append(f"RequestBody: {schema_name}")

                    # Include key properties only
                    if schema_name in schemas:
                        props = list(schemas[schema_name].get("properties", {}).keys())
                        if props:
                            doc_parts.append(f"Properties: {', '.join(props[:10])}")

        # Response codes only
        if endpoint.get("responses"):
            codes = list(endpoint["responses"].keys())
            doc_parts.append(f"ResponseCodes: {', '.join(codes)}")

        return "\n".join(doc_parts)

    def _get_action_keywords(self, method: str, path: str, resource_name: str) -> str:
        """Generate action keywords for better semantic search matching."""
        keywords = []

        # Singular and plural forms
        singular = (
            resource_name.rstrip("s") if resource_name.endswith("s") else resource_name
        )
        plural = resource_name if resource_name.endswith("s") else resource_name + "s"

        # Method-based keywords
        if method == "GET":
            if "{" in path:
                keywords.extend(
                    [
                        f"get {singular}",
                        f"fetch {singular}",
                        f"retrieve {singular}",
                        f"find {singular}",
                        f"get {singular} by id",
                    ]
                )
            else:
                keywords.extend(
                    [
                        f"get all {plural}",
                        f"list {plural}",
                        f"fetch all {plural}",
                        f"retrieve all {plural}",
                        f"get {plural}",
                    ]
                )
        elif method == "POST":
            keywords.extend(
                [
                    f"create {singular}",
                    f"add {singular}",
                    f"new {singular}",
                    f"insert {singular}",
                    f"post {singular}",
                ]
            )
        elif method == "PUT":
            keywords.extend(
                [
                    f"update {singular}",
                    f"modify {singular}",
                    f"edit {singular}",
                    f"change {singular}",
                    f"put {singular}",
                ]
            )
        elif method == "DELETE":
            keywords.extend(
                [
                    f"delete {singular}",
                    f"remove {singular}",
                    f"destroy {singular}",
                    f"erase {singular}",
                ]
            )
        elif method == "PATCH":
            keywords.extend([f"patch {singular}", f"partial update {singular}"])

        return ", ".join(keywords)

    def _group_endpoints_by_resource(self, paths: dict, schemas: dict) -> dict:
        """
        Group API endpoints by their resource name.

        Example:
            /api/v1/Books -> Books
            /api/v1/Books/{id} -> Books
            /api/v1/Users -> Users
        """
        resource_groups = {}

        for path, methods_data in paths.items():
            # Extract resource name from path
            # Pattern: /api/v1/ResourceName or /api/v1/ResourceName/{id}
            path_parts = path.strip("/").split("/")

            # Find the resource name (usually after 'v1' or 'api')
            resource_name = None
            for i, part in enumerate(path_parts):
                if part.startswith("v") and part[1:].isdigit():
                    # Found version, next part is resource
                    if i + 1 < len(path_parts):
                        resource_name = path_parts[i + 1]
                        break
                elif part == "api" and i + 1 < len(path_parts):
                    # Check if next is version or resource
                    next_part = path_parts[i + 1]
                    if next_part.startswith("v") and len(next_part) > 1:
                        if i + 2 < len(path_parts):
                            resource_name = path_parts[i + 2]
                            break
                    else:
                        resource_name = next_part
                        break

            # Fallback: use first non-api, non-version part
            if not resource_name:
                for part in path_parts:
                    if (
                        part
                        and not part.startswith("{")
                        and part not in ["api", "v1", "v2", "v3"]
                    ):
                        resource_name = part
                        break

            if not resource_name:
                resource_name = "Unknown"

            # Clean up resource name (remove {id} patterns)
            if resource_name.startswith("{"):
                continue  # Skip if the resource itself is a parameter

            # Initialize resource group if needed
            if resource_name not in resource_groups:
                resource_groups[resource_name] = {
                    "endpoints": [],
                    "methods": set(),
                    "has_path_params": False,
                    "has_request_body": False,
                    "schemas": set(),
                }

            # Process each HTTP method for this path
            for method, method_data in methods_data.items():
                if method.upper() not in ["GET", "POST", "PUT", "DELETE", "PATCH"]:
                    continue

                endpoint_info = {
                    "path": path,
                    "method": method.upper(),
                    "tags": method_data.get("tags", []),
                    "parameters": method_data.get("parameters", []),
                    "request_body": method_data.get("requestBody"),
                    "responses": method_data.get("responses", {}),
                    "summary": method_data.get("summary", ""),
                    "description": method_data.get("description", ""),
                }

                resource_groups[resource_name]["endpoints"].append(endpoint_info)
                resource_groups[resource_name]["methods"].add(method.upper())

                # Check for path parameters
                if "{" in path:
                    resource_groups[resource_name]["has_path_params"] = True

                # Check for request body
                if method_data.get("requestBody"):
                    resource_groups[resource_name]["has_request_body"] = True

                    # Extract schema reference
                    content = method_data.get("requestBody", {}).get("content", {})
                    for content_type, content_data in content.items():
                        schema_ref = content_data.get("schema", {}).get("$ref", "")
                        if schema_ref:
                            schema_name = schema_ref.split("/")[-1]
                            resource_groups[resource_name]["schemas"].add(schema_name)

        # Convert sets to lists for JSON serialization
        for resource_name in resource_groups:
            resource_groups[resource_name]["methods"] = list(
                resource_groups[resource_name]["methods"]
            )
            resource_groups[resource_name]["schemas"] = list(
                resource_groups[resource_name]["schemas"]
            )

        return resource_groups

    def _format_resource_document(
        self, resource_name: str, resource_data: dict, schemas: dict
    ) -> str:
        """
        Format a resource group into a comprehensive document for embedding.
        This document will be used by GitLab Duo to understand and generate curl commands.
        """
        doc_parts = []

        # Header
        doc_parts.append(f"# API Resource: {resource_name}")
        doc_parts.append(
            f"Available HTTP Methods: {', '.join(resource_data['methods'])}"
        )
        doc_parts.append("")

        # Endpoints section
        doc_parts.append("## Endpoints")
        for endpoint in resource_data["endpoints"]:
            doc_parts.append(f"\n### {endpoint['method']} {endpoint['path']}")

            if endpoint.get("summary"):
                doc_parts.append(f"Summary: {endpoint['summary']}")
            if endpoint.get("description"):
                doc_parts.append(f"Description: {endpoint['description']}")

            # Parameters
            if endpoint.get("parameters"):
                doc_parts.append("\nParameters:")
                for param in endpoint["parameters"]:
                    param_info = f"  - {param.get('name')} ({param.get('in')})"
                    if param.get("required"):
                        param_info += " [REQUIRED]"
                    param_schema = param.get("schema", {})
                    if param_schema:
                        param_info += f" - type: {param_schema.get('type', 'unknown')}"
                    doc_parts.append(param_info)

            # Request Body
            if endpoint.get("request_body"):
                doc_parts.append("\nRequest Body:")
                content = endpoint["request_body"].get("content", {})
                for content_type, content_data in content.items():
                    schema_ref = content_data.get("schema", {}).get("$ref", "")
                    if schema_ref:
                        schema_name = schema_ref.split("/")[-1]
                        doc_parts.append(f"  Content-Type: {content_type}")
                        doc_parts.append(f"  Schema: {schema_name}")

                        # Include schema details
                        if schema_name in schemas:
                            schema_def = schemas[schema_name]
                            doc_parts.append(f"  Properties:")
                            for prop_name, prop_data in schema_def.get(
                                "properties", {}
                            ).items():
                                prop_type = prop_data.get("type", "unknown")
                                prop_format = prop_data.get("format", "")
                                prop_info = f"    - {prop_name}: {prop_type}"
                                if prop_format:
                                    prop_info += f" (format: {prop_format})"
                                doc_parts.append(prop_info)

            # Responses
            if endpoint.get("responses"):
                doc_parts.append("\nResponses:")
                for status_code, response_data in endpoint["responses"].items():
                    doc_parts.append(
                        f"  - {status_code}: {response_data.get('description', '')}"
                    )

        # Schema section (full definitions for this resource)
        if resource_data.get("schemas"):
            doc_parts.append("\n## Schemas")
            for schema_name in resource_data["schemas"]:
                if schema_name in schemas:
                    schema_def = schemas[schema_name]
                    doc_parts.append(f"\n### {schema_name}")
                    doc_parts.append("Properties:")
                    for prop_name, prop_data in schema_def.get(
                        "properties", {}
                    ).items():
                        prop_type = prop_data.get("type", "unknown")
                        prop_format = prop_data.get("format", "")
                        nullable = prop_data.get("nullable", False)
                        prop_info = f"  - {prop_name}: {prop_type}"
                        if prop_format:
                            prop_info += f" (format: {prop_format})"
                        if nullable:
                            prop_info += " [nullable]"
                        doc_parts.append(prop_info)

        return "\n".join(doc_parts)

    def retrieve_endpoints_by_intent(
        self, intent: str, collection_name: str = "api_endpoints", top_k: int = 1
    ):
        """
        Semantic search to find relevant API endpoints based on user intent.

        Args:
            intent (str): User's intent (e.g., "delete book with id 5", "get all users")
            collection_name (str): Name of the ChromaDB collection to search
            top_k (int): Number of top results to return

        Returns:
            List of matched resource documents with their swagger context
        """
        log.safe_print(f"\n[RAG] Searching for endpoints matching intent: '{intent}'")

        try:
            # Get or create collection
            api_collection = self.chroma_client.get_or_create_collection(
                name=collection_name, embedding_function=self.embedding_fn
            )

            # Check if collection has documents
            collection_count = api_collection.count()
            if collection_count == 0:
                log.safe_print(
                    f"[[WARNING]] Collection '{collection_name}' is empty. Please embed swagger first."
                )
                return []

            log.safe_print(f"[Info] Collection has {collection_count} endpoints")

            # Use existing retrieve method
            results = self.retrieve_similar_semantic(
                collection=api_collection, intent=intent, k=top_k
            )

            if results:
                log.safe_print(f"[[OK]] Found {len(results)} matching endpoint(s)")
                for i, doc in enumerate(results):
                    # Extract resource name and endpoint from document
                    lines = doc.split("\n")[:2] if doc else []
                    for line in lines:
                        log.safe_print(f"  [{i+1}] {line[:80]}")
            else:
                log.safe_print(
                    f"[[WARNING]] No matching endpoints found for intent: '{intent}'"
                )

            return results

        except Exception as e:
            log.safe_print(f"[[ERROR]] Error retrieving endpoints: {e}")
            import traceback

            traceback.print_exc()
            return []

    def debug_embedding_model(self):
        """Debug the embedding model and distances."""
        log.safe_print(f"[DEBUG] Embedding model info:")

        # Test with a simple query
        test_embedding = self._generate_query_embedding("test query")
        log.safe_print(
            f"[DEBUG] Test embedding shape: {len(test_embedding) if test_embedding else 'None'}"
        )
        log.safe_print(
            f"[DEBUG] Test embedding sample: {test_embedding[:5] if test_embedding else 'None'}"
        )

        return test_embedding

    # ==================== DB INTENT-BASED FUNCTIONS ====================

    def embed_db_schema(
        self,
        schema_data: dict,
        collection_name: str = "db_context",
        force_refresh: bool = False,
    ):
        """
        Embed database schema with table relationships into ChromaDB.
        Groups related tables together based on foreign key relationships.

        Args:
            schema_data: Dict of table_name -> {"columns": [...], "foreign_keys": [...]}
                        where columns come from DESCRIBE table query
            collection_name: Name of the ChromaDB collection
            force_refresh: If True, clears existing schema documents before embedding

        Returns:
            ChromaDB collection with embedded schema
        """
        import json
        from collections import defaultdict

        log.safe_print(f"\n{'='*80}")
        log.safe_print(f"[Embedding] Database Schema into '{collection_name}'")
        log.safe_print(f"{'='*80}")

        # Initialize collection
        db_collection = self.intialize_chroma_db(name=collection_name)

        if not schema_data:
            log.safe_print("[[WARNING]] No schema data provided")
            return db_collection

        # If force refresh, remove existing schema documents
        if force_refresh:
            try:
                existing = db_collection.get(where={"type": "schema"})
                if existing and existing.get("ids"):
                    db_collection.delete(ids=existing["ids"])
                    log.safe_print(
                        f"[Info] Removed {len(existing['ids'])} existing schema documents"
                    )
            except Exception as e:
                log.safe_print(f"[Warning] Could not clear existing schema: {e}")

        log.safe_print(f"[Info] Found {len(schema_data)} tables in schema")

        # Build relationships from foreign_keys data
        relationships = []
        for table_name, table_info in schema_data.items():
            fks = table_info.get("foreign_keys", [])
            for fk in fks:
                if fk:
                    relationships.append(
                        {
                            "from_table": table_name,
                            "from_column": fk.get("COLUMN_NAME", ""),
                            "to_table": fk.get("REFERENCED_TABLE_NAME", ""),
                            "to_column": fk.get("REFERENCED_COLUMN_NAME", ""),
                        }
                    )

        log.safe_print(f"[Info] Found {len(relationships)} foreign key relationships")

        # Group related tables based on relationships
        table_groups = self._group_tables_by_fk(schema_data, relationships)
        log.safe_print(f"[Info] Created {len(table_groups)} table groups for embedding")

        # Embed each table group
        documents = []
        metadatas = []
        ids = []

        for group_idx, group_info in enumerate(table_groups):
            doc_content = self._format_table_group_for_embedding(group_info)

            table_names = group_info["tables"]
            doc_id = f"schema_{group_idx}_{('_'.join(table_names[:3]))[:50]}"

            documents.append(doc_content)
            metadatas.append(
                {
                    "type": "schema",
                    "tables": json.dumps(table_names),
                    "has_relationships": len(group_info.get("relationships", [])) > 0,
                    "table_count": len(table_names),
                }
            )
            ids.append(doc_id)

            log.safe_print(f"\n[Group {group_idx + 1}] Tables: {table_names}")

        # Add to collection
        if documents:
            try:
                db_collection.add(documents=documents, metadatas=metadatas, ids=ids)
                log.safe_print(
                    f"\n[[OK]] Successfully embedded {len(documents)} table groups"
                )
            except Exception as e:
                log.safe_print(f"[[ERROR]] Error embedding schema: {e}")

        return db_collection

    def _group_tables_by_fk(self, schema_data: dict, relationships: list) -> list:
        """
        Group tables by foreign key relationships.
        Tables that reference each other are grouped together.
        """
        from collections import defaultdict

        # Build adjacency list
        adjacency = defaultdict(set)
        for rel in relationships:
            from_table = rel["from_table"]
            to_table = rel["to_table"]
            if from_table and to_table:
                adjacency[from_table].add(to_table)
                adjacency[to_table].add(from_table)

        # Find connected components using BFS
        visited = set()
        groups = []

        all_tables = set(schema_data.keys())

        for start_table in all_tables:
            if start_table in visited:
                continue

            # BFS to find all connected tables
            component = set()
            queue = [start_table]

            while queue:
                table = queue.pop(0)
                if table in visited:
                    continue
                visited.add(table)
                component.add(table)

                for neighbor in adjacency.get(table, []):
                    if neighbor not in visited and neighbor in all_tables:
                        queue.append(neighbor)

            # Build group info
            group_tables = list(component)
            group_columns = {t: schema_data[t].get("columns", []) for t in group_tables}
            group_relationships = [
                r
                for r in relationships
                if r["from_table"] in component or r["to_table"] in component
            ]

            groups.append(
                {
                    "tables": group_tables,
                    "columns": group_columns,
                    "relationships": group_relationships,
                }
            )

        return groups

    def _format_table_group_for_embedding(self, group_info: dict) -> str:
        """
        Format a group of related tables into a document for embedding.
        """
        lines = []
        lines.append("=== DATABASE SCHEMA ===\n")

        for table_name in group_info["tables"]:
            columns = group_info["columns"].get(table_name, [])
            lines.append(f"TABLE: {table_name}")
            lines.append("-" * 40)

            for col in columns:
                # Handle DESCRIBE output format
                col_name = col.get("Field", col.get("COLUMN_NAME", "unknown"))
                col_type = col.get("Type", col.get("DATA_TYPE", "unknown"))
                nullable = col.get("Null", col.get("IS_NULLABLE", "YES"))
                key = col.get("Key", "")
                default = col.get("Default", col.get("COLUMN_DEFAULT", ""))

                key_indicator = ""
                if key == "PRI":
                    key_indicator = " [PRIMARY KEY]"
                elif key == "MUL":
                    key_indicator = " [FOREIGN KEY]"
                elif key == "UNI":
                    key_indicator = " [UNIQUE]"

                null_indicator = "NULL" if nullable == "YES" else "NOT NULL"

                lines.append(
                    f"  - {col_name}: {col_type} {null_indicator}{key_indicator}"
                )

            lines.append("")

        # Add relationship info
        if group_info.get("relationships"):
            lines.append("RELATIONSHIPS:")
            for rel in group_info["relationships"]:
                lines.append(
                    f"  - {rel['from_table']}.{rel['from_column']} -> {rel['to_table']}.{rel['to_column']}"
                )
            lines.append("")

        return "\n".join(lines)

    def _detect_table_relationships(self, tables: dict) -> list:
        """
        Detect foreign key relationships based on naming conventions.
        Looks for columns ending in '_id' that match other table names.
        """
        relationships = []

        table_names = set(tables.keys())
        table_names_lower = {t.lower(): t for t in table_names}

        for table_name, columns in tables.items():
            for col in columns:
                col_name = col.get("COLUMN_NAME", "").lower()

                # Check for foreign key patterns: user_id, post_id, etc.
                if col_name.endswith("_id") and col_name != "id":
                    # Extract potential referenced table
                    ref_table_singular = col_name[:-3]  # Remove '_id'
                    ref_table_plural = ref_table_singular + "s"

                    # Check if referenced table exists
                    for potential_ref in [ref_table_singular, ref_table_plural]:
                        if potential_ref in table_names_lower:
                            relationships.append(
                                {
                                    "from_table": table_name,
                                    "from_column": col.get("COLUMN_NAME"),
                                    "to_table": table_names_lower[potential_ref],
                                    "to_column": "id",
                                }
                            )
                            break

        return relationships

    def _group_related_tables(self, tables: dict, relationships: list) -> list:
        """
        Group tables that are related via foreign keys.
        Uses Union-Find algorithm to find connected components.
        """
        from collections import defaultdict

        # Build adjacency list
        adjacency = defaultdict(set)
        for rel in relationships:
            adjacency[rel["from_table"]].add(rel["to_table"])
            adjacency[rel["to_table"]].add(rel["from_table"])

        # Find connected components using BFS
        visited = set()
        groups = []

        for table_name in tables.keys():
            if table_name in visited:
                continue

            # BFS to find all connected tables
            group_tables = set()
            queue = [table_name]

            while queue:
                current = queue.pop(0)
                if current in visited:
                    continue
                visited.add(current)
                group_tables.add(current)

                for neighbor in adjacency[current]:
                    if neighbor not in visited and neighbor in tables:
                        queue.append(neighbor)

            # Build group info
            group_relationships = [
                rel
                for rel in relationships
                if rel["from_table"] in group_tables or rel["to_table"] in group_tables
            ]

            group_columns = {t: tables[t] for t in group_tables}

            groups.append(
                {
                    "tables": group_tables,
                    "columns": group_columns,
                    "relationships": group_relationships,
                }
            )

        return groups

    def _format_db_schema_document(
        self, table_names: set, columns: dict, relationships: list
    ) -> str:
        """
        Format a table group into a document for embedding.
        Includes searchable keywords for better semantic matching.
        """
        doc_parts = []

        # Header with all table names
        doc_parts.append(f"Tables: {', '.join(sorted(table_names))}")

        # Relationships
        if relationships:
            rel_strs = []
            for rel in relationships:
                rel_strs.append(
                    f"{rel['from_table']}.{rel['from_column']} -> {rel['to_table']}.{rel['to_column']}"
                )
            doc_parts.append(f"Relationships: {'; '.join(rel_strs)}")

        # Table details
        for table_name in sorted(table_names):
            doc_parts.append(f"\nTable: {table_name}")

            table_cols = columns.get(table_name, [])
            col_strs = []
            primary_keys = []
            nullable_cols = []

            for col in table_cols:
                col_name = col.get("COLUMN_NAME", "")
                col_type = col.get("COLUMN_TYPE", col.get("DATA_TYPE", ""))
                is_nullable = col.get("IS_NULLABLE", "YES") == "YES"
                is_pk = col.get("COLUMN_KEY", "") == "PRI"

                col_str = f"{col_name}({col_type})"
                if is_pk:
                    col_str += "*"
                    primary_keys.append(col_name)
                if not is_nullable:
                    col_str += "!"

                col_strs.append(col_str)
                if is_nullable:
                    nullable_cols.append(col_name)

            doc_parts.append(f"  Columns: {', '.join(col_strs)}")

            if primary_keys:
                doc_parts.append(f"  PrimaryKey: {', '.join(primary_keys)}")

        # Add searchable action keywords
        keywords = self._get_db_action_keywords(table_names)
        doc_parts.append(f"\nActions: {keywords}")

        return "\n".join(doc_parts)

    def _get_db_action_keywords(self, table_names: set) -> str:
        """Generate action keywords for better semantic search matching."""
        keywords = []

        for table in table_names:
            singular = table.rstrip("s") if table.endswith("s") else table
            plural = table if table.endswith("s") else table + "s"

            keywords.extend(
                [
                    f"get {singular}",
                    f"get all {plural}",
                    f"find {singular}",
                    f"select from {table}",
                    f"query {table}",
                    f"list {plural}",
                    f"fetch {singular}",
                    f"retrieve {plural}",
                    f"count {plural}",
                    f"search {table}",
                ]
            )

        return ", ".join(keywords[:20])  # Limit to avoid too long strings

    def store_query_learning(
        self,
        intent: str,
        query: str,
        tables_used: list,
        is_correct: bool,
        error_message: str = None,
        collection_name: str = "db_context",
    ):
        """
        Store a query execution result in the learning context.

        Args:
            intent: The user's original intent
            query: The generated SQL query
            tables_used: List of table names used in the query
            is_correct: Whether the query executed successfully
            error_message: Error message if query failed
            collection_name: ChromaDB collection name

        Returns:
            The document ID that was stored
        """
        import json
        import hashlib
        from datetime import datetime

        log.safe_print(f"\n[Learning] Storing query result...")
        log.safe_print(f"  Intent: {intent[:50]}...")
        log.safe_print(f"  Status: {'[correct]' if is_correct else '[incorrect]'}")

        # Get or create collection
        db_collection = self.chroma_client.get_or_create_collection(
            name=collection_name, embedding_function=self.embedding_fn
        )

        # Create document content
        status_tag = "[correct]" if is_correct else "[incorrect]"
        doc_content = f"""{status_tag}
Intent: {intent}
Query: {query}
Tables: {', '.join(tables_used)}"""

        if error_message and not is_correct:
            doc_content += f"\nError: {error_message}"

        # Generate unique ID based on intent and query hash
        hash_input = f"{intent}_{query}_{datetime.now().isoformat()}"
        doc_id = f"learning_{hashlib.md5(hash_input.encode()).hexdigest()[:12]}"

        metadata = {
            "type": "learning",
            "status": "correct" if is_correct else "incorrect",
            "intent": intent[:500],  # Truncate for metadata
            "query": query[:1000],  # Truncate for metadata
            "tables_used": json.dumps(tables_used),
            "timestamp": datetime.now().isoformat(),
        }

        if error_message and not is_correct:
            metadata["error"] = error_message[:500]

        try:
            db_collection.add(
                documents=[doc_content], metadatas=[metadata], ids=[doc_id]
            )
            log.safe_print(f"[[OK]] Stored learning document: {doc_id}")
            return doc_id
        except Exception as e:
            log.safe_print(f"[[ERROR]] Failed to store learning: {e}")
            return None

    def retrieve_db_context_by_intent(
        self,
        intent: str,
        collection_name: str = "db_context",
        top_k_schema: int = 2,
        top_k_learning: int = 3,
    ) -> dict:
        """
        Retrieve both schema context and learning examples by intent.

        Args:
            intent: User's natural language intent
            collection_name: ChromaDB collection name
            top_k_schema: Number of schema documents to retrieve
            top_k_learning: Number of learning examples to retrieve

        Returns:
            dict: {
                "schema": [schema documents],
                "correct_examples": [correct query examples],
                "incorrect_examples": [incorrect query examples]
            }
        """
        log.safe_print(f"\n[RAG] Retrieving DB context for intent: '{intent}'")

        result = {"schema": [], "correct_examples": [], "incorrect_examples": []}

        try:
            # Get collection
            db_collection = self.chroma_client.get_or_create_collection(
                name=collection_name, embedding_function=self.embedding_fn
            )

            collection_count = db_collection.count()
            if collection_count == 0:
                log.safe_print(f"[[WARNING]] Collection '{collection_name}' is empty")
                return result

            log.safe_print(f"[Info] Collection has {collection_count} documents")

            # Generate query embedding
            query_embedding = self._generate_query_embedding(intent)

            # Retrieve schema documents
            schema_results = db_collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k_schema,
                where={"type": "schema"},
                include=["documents", "metadatas", "distances"],
            )

            if schema_results and schema_results.get("documents"):
                result["schema"] = schema_results["documents"][0]
                log.safe_print(
                    f"[[OK]] Found {len(result['schema'])} schema document(s)"
                )
                for i, doc in enumerate(result["schema"]):
                    preview = doc[:100].replace("\n", " ")
                    log.safe_print(f"  [{i+1}] {preview}...")

            # Retrieve correct learning examples
            try:
                correct_results = db_collection.query(
                    query_embeddings=[query_embedding],
                    n_results=top_k_learning,
                    where={"$and": [{"type": "learning"}, {"status": "correct"}]},
                    include=["documents", "metadatas", "distances"],
                )

                if correct_results and correct_results.get("documents"):
                    result["correct_examples"] = correct_results["documents"][0]
                    log.safe_print(
                        f"[[OK]] Found {len(result['correct_examples'])} correct example(s)"
                    )
            except Exception as e:
                log.safe_print(f"[Info] No correct examples found: {e}")

            # Retrieve incorrect learning examples (for negative examples)
            try:
                incorrect_results = db_collection.query(
                    query_embeddings=[query_embedding],
                    n_results=2,  # Fewer incorrect examples
                    where={"$and": [{"type": "learning"}, {"status": "incorrect"}]},
                    include=["documents", "metadatas", "distances"],
                )

                if incorrect_results and incorrect_results.get("documents"):
                    result["incorrect_examples"] = incorrect_results["documents"][0]
                    log.safe_print(
                        f"[[OK]] Found {len(result['incorrect_examples'])} incorrect example(s)"
                    )
            except Exception as e:
                log.safe_print(f"[Info] No incorrect examples found: {e}")

            return result

        except Exception as e:
            log.safe_print(f"[[ERROR]] Error retrieving DB context: {e}")
            import traceback

            traceback.print_exc()
            return result


# =========================================================================
# UI MODULE-BASED LEARNING METHODS (Simplified Flow)
# =========================================================================
# Flow:
# 1. Retrieve from ChromaDB by module + intent
# 2. If found [correct] -> return stored metadata for DUO to use
# 3. If not found or [incorrect] -> return None (caller uses live HTML)
# 4. DUO returns full metadata dict, we store it with status
# =========================================================================


def _rag_get_ui_learning_collection(self):
    """Get or create the UI learning collection."""
    try:
        return self.chroma_client.get_or_create_collection(
            name="ui_module_learning", embedding_function=self.embedding_fn
        )
    except Exception as e:
        log.safe_print(f"[ERROR] Failed to get UI learning collection: {e}")
        return None


def _rag_extract_module_from_url(self, url: str) -> str:
    """
    Extract module name from URL path.

    Examples:
        /inventory.html -> "inventory"
        /cart.html -> "cart"
        /checkout-step-one.html -> "checkout-step-one"
        / -> "home"
    """
    from urllib.parse import urlparse

    if not url:
        return "unknown"

    try:
        parsed = urlparse(url)
        path = parsed.path.strip("/")

        if not path:
            return "home"

        # Remove .html extension and get the last segment
        if path.endswith(".html"):
            path = path[:-5]

        # Get last segment if path has slashes
        segments = path.split("/")
        module = segments[-1] if segments else "home"

        return module if module else "home"

    except Exception:
        return "unknown"


def _rag_retrieve_ui_action_for_intent(self, module: str, intent: str) -> dict:
    """
    Retrieve a matching [correct] action for the intent from ChromaDB.
    Uses TF-IDF similarity to find the best match.

    Args:
        module: The module name (e.g., "inventory", "cart")
        intent: The step intent to match

    Returns:
        dict with:
        {
            "found": True/False,
            "stored_metadata": {...} or None,  # Full metadata if found [correct]
            "status": "[correct]" or "[incorrect]" or None,
            "match_score": 0.0-1.0
        }
    """
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity

    result = {
        "found": False,
        "stored_metadata": None,
        "status": None,
        "match_score": 0.0,
    }

    try:
        collection = self.get_ui_learning_collection()
        if not collection:
            return result

        # Query for documents with this module
        query_results = collection.query(
            query_texts=[f"module:{module} {intent}"],
            n_results=20,
            where={"module": module},
            include=["documents", "metadatas"],
        )

        if not query_results or not query_results.get("metadatas"):
            log.safe_print(f"[RAG] No actions found for module: {module}")
            return result

        metadatas = query_results["metadatas"][0] if query_results["metadatas"] else []

        if not metadatas:
            return result

        # Use TF-IDF to find best matching intent
        stored_intents = []
        stored_data = []

        for metadata in metadatas:
            if metadata.get("type") == "ui_module_action":
                stored_intent = metadata.get("intent", "")
                if stored_intent:
                    stored_intents.append(stored_intent)
                    stored_data.append(metadata)

        if not stored_intents:
            return result

        # Create TF-IDF vectors
        vectorizer = TfidfVectorizer(
            ngram_range=(1, 2), lowercase=True, stop_words="english"
        )

        # Fit on stored intents + query intent
        all_texts = stored_intents + [intent]
        tfidf_matrix = vectorizer.fit_transform(all_texts)

        # Get query vector (last one)
        query_vector = tfidf_matrix[-1]

        # Calculate similarities with stored intents
        stored_vectors = tfidf_matrix[:-1]
        similarities = cosine_similarity(query_vector, stored_vectors)[0]

        # Find best match
        best_idx = similarities.argmax()
        best_score = similarities[best_idx]

        # Require minimum similarity threshold (0.3)
        if best_score < 0.3:
            log.safe_print(
                f"[RAG] Best match score {best_score:.3f} below threshold 0.3"
            )
            return result

        best_metadata = stored_data[best_idx]
        status = best_metadata.get("status", "[incorrect]")

        log.safe_print(f"[RAG] Found match: score={best_score:.3f}, status={status}")

        # Only return as "found" if status is [correct]
        if status == "[correct]":
            result["found"] = True
            result["stored_metadata"] = best_metadata
            result["status"] = status
            result["match_score"] = float(best_score)
        else:
            # Found but [incorrect] - still return metadata for reference
            result["found"] = False
            result["stored_metadata"] = (
                best_metadata  # Caller can see what failed before
            )
            result["status"] = status
            result["match_score"] = float(best_score)

        return result

    except Exception as e:
        log.safe_print(f"[ERROR] Failed to retrieve UI action: {e}")
        import traceback

        traceback.print_exc()
        return result


def _rag_store_ui_action_from_duo(
    self, module: str, duo_response: dict, status: str, url: str = ""
) -> bool:
    """
    Store DUO's response as a UI action in ChromaDB.

    DUO response format (same as our metadata):
    {
        "action_key": "click_login",
        "intent": "click login button",
        "action_type": "click",
        "locator": "#login-btn",
        "action_json": {...},
        "playwright_code": "page.click('#login-btn')"
    }

    We add:
    - type: "ui_module_action"
    - module: from parameter
    - status: "[correct]" or "[incorrect]"
    - url: current URL
    - timestamp: now

    Status update logic:
    - [incorrect] -> [correct] = UPDATE
    - [correct] -> [incorrect] = DON'T UPDATE (keep working version)

    Returns:
        True if stored/updated, False otherwise
    """
    import json
    from datetime import datetime

    try:
        collection = self.get_ui_learning_collection()
        if not collection:
            return False

        # Extract fields from DUO response
        action_key = duo_response.get("action_key", "")
        intent = duo_response.get("intent", "")
        action_type = duo_response.get("action_type", "")
        locator = duo_response.get("locator", "")
        action_json = duo_response.get("action_json", {})
        playwright_code = duo_response.get("playwright_code", "")

        if not action_key:
            # Generate action_key from action_type and intent if not provided
            import re

            intent_lower = intent.lower()
            stop_words = {
                "with",
                "the",
                "a",
                "an",
                "on",
                "in",
                "to",
                "for",
                "and",
                "or",
                "i",
                "should",
                "see",
                "be",
            }
            words = [
                w
                for w in re.findall(r"\w+", intent_lower)
                if w not in stop_words and len(w) > 1
            ]

            if len(words) >= 2:
                target_words = [w for w in words if w != action_type.lower()][:2]
                action_key = f"{action_type}_{'_'.join(target_words)}"
            elif words:
                action_key = f"{action_type}_{words[0]}"
            else:
                action_key = f"{action_type}_action"

        doc_id = f"ui_{module}_{action_key}"

        # Check if document already exists
        try:
            existing = collection.get(ids=[doc_id], include=["metadatas"])

            if (
                existing
                and existing.get("metadatas")
                and len(existing["metadatas"]) > 0
            ):
                existing_metadata = existing["metadatas"][0]
                existing_status = existing_metadata.get("status", "[incorrect]")

                # Status update logic:
                # - [incorrect] -> [correct] = UPDATE
                # - [correct] -> [incorrect] = DON'T UPDATE
                if existing_status == "[correct]" and status == "[incorrect]":
                    log.safe_print(
                        f"[RAG] Keeping existing [correct] action: {action_key}"
                    )
                    return False

                # Delete existing to update
                collection.delete(ids=[doc_id])
                log.safe_print(
                    f"[RAG] Updating action: {action_key} ({existing_status} -> {status})"
                )

        except Exception:
            pass  # Document doesn't exist, proceed with add

        # Prepare document content for embedding
        document_text = (
            f"module:{module} intent:{intent} action:{action_type} locator:{locator}"
        )

        # Prepare metadata (full DUO response + our additions)
        metadata = {
            "type": "ui_module_action",
            "module": module,
            "action_key": action_key,
            "intent": intent,
            "action_type": action_type,
            "locator": locator,
            "action_json": (
                json.dumps(action_json)
                if isinstance(action_json, dict)
                else str(action_json)
            ),
            "playwright_code": playwright_code,
            "status": status,
            "url": url,
            "timestamp": datetime.now().isoformat(),
        }

        # Add to collection
        collection.add(documents=[document_text], metadatas=[metadata], ids=[doc_id])

        log.safe_print(f"[RAG] Stored action: {module}.{action_key} = {status}")
        return True

    except Exception as e:
        log.safe_print(f"[ERROR] Failed to store UI action: {e}")
        import traceback

        traceback.print_exc()
        return False


def _rag_get_ui_module_summary(self, module: str = None) -> dict:
    """
    Get a summary of stored UI learning data.

    Args:
        module: Optional module filter

    Returns:
        Summary dict with module counts and action details
    """
    try:
        collection = self.get_ui_learning_collection()
        if not collection:
            return {"error": "Collection not found"}

        # Get all documents
        all_docs = collection.get(include=["metadatas"])

        if not all_docs or not all_docs.get("metadatas"):
            return {"total": 0, "modules": {}}

        # Build summary
        summary = {
            "total": len(all_docs["metadatas"]),
            "modules": {},
            "correct_count": 0,
            "incorrect_count": 0,
        }

        for metadata in all_docs["metadatas"]:
            mod = metadata.get("module", "unknown")
            status = metadata.get("status", "[incorrect]")

            if mod not in summary["modules"]:
                summary["modules"][mod] = {"actions": [], "correct": 0, "incorrect": 0}

            summary["modules"][mod]["actions"].append(
                metadata.get("action_key", "unknown")
            )

            if status == "[correct]":
                summary["modules"][mod]["correct"] += 1
                summary["correct_count"] += 1
            else:
                summary["modules"][mod]["incorrect"] += 1
                summary["incorrect_count"] += 1

        return summary

    except Exception as e:
        log.safe_print(f"[ERROR] Failed to get UI module summary: {e}")
        return {"error": str(e)}


# Add methods to Rag class
Rag.get_ui_learning_collection = _rag_get_ui_learning_collection
Rag._extract_module_from_url = _rag_extract_module_from_url
Rag.retrieve_ui_action_for_intent = _rag_retrieve_ui_action_for_intent
Rag.store_ui_action_from_duo = _rag_store_ui_action_from_duo
Rag.get_ui_module_summary = _rag_get_ui_module_summary


# =============================================================================
# API ENDPOINT LEARNING METHODS (Two-Document Approach)
# =============================================================================
# Collection 1: "api_swagger" - Parsed swagger spec (grouped by resource)
# Collection 2: "api_endpoint_learning" - Learned API actions with metadata
# =============================================================================


def _rag_get_api_learning_collection(self):
    """Get or create the API endpoint learning collection."""
    return self.chroma_client.get_or_create_collection(
        name="api_endpoint_learning", embedding_function=self.embedding_fn
    )


def _rag_get_api_swagger_collection(self):
    """Get or create the API swagger collection."""
    return self.chroma_client.get_or_create_collection(
        name="api_swagger", embedding_function=self.embedding_fn
    )


def _rag_retrieve_api_action_for_intent(self, resource: str, intent: str) -> dict:
    """
    Retrieve a stored API action from ChromaDB by resource and intent.

    Algorithm:
    1. Query "api_endpoint_learning" collection for this resource
    2. Use TF-IDF similarity to find best matching intent
    3. Return stored metadata if status is [correct]

    Args:
        resource: API resource name (e.g., "Books", "Users")
        intent: Natural language intent (e.g., "get all books")

    Returns:
        dict with:
            - found: bool
            - status: "[correct]" or "[incorrect]"
            - stored_metadata: Full action metadata if found
            - match_score: Similarity score
    """
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity

    result = {
        "found": False,
        "status": None,
        "stored_metadata": None,
        "match_score": 0.0,
    }

    try:
        collection = self.get_api_learning_collection()

        # Query all actions for this resource
        all_docs = collection.get(
            where={"resource": resource}, include=["documents", "metadatas"]
        )

        if not all_docs or not all_docs.get("documents"):
            return result

        documents = all_docs["documents"]
        metadatas = all_docs["metadatas"]
        ids = all_docs["ids"]

        if not documents:
            return result

        # Use TF-IDF to find best matching intent
        all_texts = documents + [intent]

        vectorizer = TfidfVectorizer(ngram_range=(1, 2), stop_words="english")
        tfidf_matrix = vectorizer.fit_transform(all_texts)

        # Compare intent (last) against all stored documents
        intent_vector = tfidf_matrix[-1]
        doc_vectors = tfidf_matrix[:-1]

        similarities = cosine_similarity(intent_vector, doc_vectors).flatten()

        # Find best match above threshold
        best_idx = similarities.argmax()
        best_score = similarities[best_idx]

        # Threshold for matching
        MATCH_THRESHOLD = 0.3

        if best_score >= MATCH_THRESHOLD:
            result["found"] = True
            result["match_score"] = float(best_score)
            result["status"] = metadatas[best_idx].get("status", "[incorrect]")

            # Reconstruct full metadata
            result["stored_metadata"] = {
                "action_key": metadatas[best_idx].get("action_key"),
                "intent": metadatas[best_idx].get("intent"),
                "resource": metadatas[best_idx].get("resource"),
                "method": metadatas[best_idx].get("method"),
                "endpoint": metadatas[best_idx].get("endpoint"),
                "curl": metadatas[best_idx].get("curl"),
                "expected_status": metadatas[best_idx].get("expected_status"),
                "actual_status": metadatas[best_idx].get("actual_status"),
                "request_body": metadatas[best_idx].get("request_body"),
                "response_body": metadatas[best_idx].get("response_body"),
                "status": metadatas[best_idx].get("status"),
            }

        return result

    except Exception as e:
        log.safe_print(f"[ERROR] Failed to retrieve API action: {e}")
        return result


def _rag_retrieve_swagger_for_intent(self, intent: str, top_k: int = 3) -> list:
    """
    Retrieve swagger context for an intent from the api_swagger collection.

    Args:
        intent: Natural language intent
        top_k: Number of results to return

    Returns:
        List of swagger context strings (endpoint info)
    """
    try:
        collection = self.get_api_swagger_collection()

        # Check if collection has documents
        count = collection.count()
        if count == 0:
            log.safe_print(
                "[WARNING] api_swagger collection is empty. Embed swagger first."
            )
            return []

        # Query by intent
        results = collection.query(
            query_texts=[intent],
            n_results=min(top_k, count),
            include=["documents", "metadatas", "distances"],
        )

        if results and results.get("documents") and results["documents"][0]:
            return results["documents"][0]

        return []

    except Exception as e:
        log.safe_print(f"[ERROR] Failed to retrieve swagger context: {e}")
        return []


def _rag_store_api_action_from_duo(
    self,
    resource: str,
    duo_response: dict,
    execution_result: dict,
    status: str,
    base_url: str = None,
) -> bool:
    """
    Store API action metadata from DUO response in ChromaDB.

    Args:
        resource: API resource name (e.g., "Books", "Users")
        duo_response: Full response from GitLab Duo with action metadata
        execution_result: Result from curl execution (status_code, response_body)
        status: "[correct]" or "[incorrect]"
        base_url: Base URL used for the API call

    Returns:
        bool: True if stored successfully
    """
    import json

    try:
        collection = self.get_api_learning_collection()

        action_key = duo_response.get("action_key", "unknown_action")
        intent = duo_response.get("intent", "")

        # Create unique document ID
        doc_id = f"api_{resource.lower()}_{action_key}"

        # Create searchable document text
        document = f"""
Resource: {resource}
Intent: {intent}
Action: {action_key}
Method: {duo_response.get('method', '')}
Endpoint: {duo_response.get('endpoint', '')}
Status: {status}
"""

        # Prepare metadata (must be string, int, float, or bool)
        request_body = duo_response.get("request_body", {})
        response_body = execution_result.get("response_body", "")

        # Serialize complex objects to JSON strings
        if isinstance(request_body, dict):
            request_body_str = json.dumps(request_body)[:1000]  # Limit size
        else:
            request_body_str = str(request_body)[:1000]

        if isinstance(response_body, dict):
            response_body_str = json.dumps(response_body)[:1000]
        else:
            response_body_str = str(response_body)[:1000]

        metadata = {
            "action_key": action_key,
            "intent": intent[:500],  # Limit size
            "resource": resource,
            "method": duo_response.get("method", "GET"),
            "endpoint": duo_response.get("endpoint", ""),
            "curl": duo_response.get("curl", "")[:2000],  # Limit curl size
            "expected_status": int(duo_response.get("expected_status", 200)),
            "actual_status": int(execution_result.get("status_code", -1)),
            "request_body": request_body_str,
            "response_body": response_body_str,
            "base_url": base_url or "",
            "status": status,
        }

        # Check if document exists
        try:
            existing = collection.get(ids=[doc_id])
            if existing and existing.get("ids"):
                # Update existing - only update if current status is [incorrect]
                # or if we're marking as [incorrect]
                existing_status = existing["metadatas"][0].get("status", "[incorrect]")

                if existing_status == "[correct]" and status == "[correct]":
                    # Already correct, no need to update
                    return True

                # Delete and re-add
                collection.delete(ids=[doc_id])
        except Exception:
            pass  # Document doesn't exist

        # Add new document
        collection.add(documents=[document], metadatas=[metadata], ids=[doc_id])

        return True

    except Exception as e:
        log.safe_print(f"[ERROR] Failed to store API action: {e}")
        import traceback

        traceback.print_exc()
        return False


def _rag_embed_swagger_to_api_swagger_collection(
    self, swagger_path: str, force_refresh: bool = False
):
    """
    Parse swagger.json and embed into api_swagger collection.
    This is the "Swagger Doc" that contains parsed API specification.

    Args:
        swagger_path: Path to swagger.json file
        force_refresh: If True, delete existing and re-embed

    Returns:
        Collection reference
    """
    import json

    log.safe_print(f"\n{'='*80}")
    log.safe_print(f"[EMBED] Embedding Swagger to api_swagger collection")
    log.safe_print(f"{'='*80}")

    collection = self.get_api_swagger_collection()

    # Handle force refresh
    if force_refresh:
        try:
            self.chroma_client.delete_collection("api_swagger")
            collection = self.get_api_swagger_collection()
            log.safe_print(f"[REFRESH] Deleted and recreated api_swagger collection")
        except Exception:
            pass

    # Load swagger file
    try:
        with open(swagger_path, "r", encoding="utf-8") as f:
            swagger_data = json.load(f)
    except FileNotFoundError:
        log.safe_print(f"[ERROR] Swagger file not found: {swagger_path}")
        return None
    except json.JSONDecodeError as e:
        log.safe_print(f"[ERROR] Invalid JSON in swagger file: {e}")
        return None

    # Extract API info
    api_info = swagger_data.get("info", {})
    base_path = swagger_data.get("servers", [{}])[0].get("url", "")
    paths = swagger_data.get("paths", {})
    schemas = swagger_data.get("components", {}).get("schemas", {})

    log.safe_print(f"[INFO] API Title: {api_info.get('title', 'Unknown')}")
    log.safe_print(f"[INFO] Total Paths: {len(paths)}")

    # Group endpoints by resource
    resource_groups = self._group_endpoints_by_resource(paths, schemas)

    documents = []
    metadatas = []
    ids = []

    for resource_name, resource_data in resource_groups.items():
        # Create a comprehensive document for each endpoint
        for endpoint in resource_data.get("endpoints", []):
            method = endpoint.get("method", "GET")
            path = endpoint.get("path", "")

            # Create searchable document with action keywords
            action_keywords = self._get_action_keywords(method, path, resource_name)

            doc_content = f"""
Resource: {resource_name}
Method: {method}
Endpoint: {path}
Actions: {action_keywords}
Summary: {endpoint.get('summary', '')}
Description: {endpoint.get('description', '')[:500]}
Parameters: {', '.join([p.get('name', '') for p in endpoint.get('parameters', [])])}
"""

            # Add request body schema if present
            if endpoint.get("request_body"):
                content = endpoint["request_body"].get("content", {})
                for content_type, content_data in content.items():
                    schema_ref = content_data.get("schema", {}).get("$ref", "")
                    if schema_ref:
                        schema_name = schema_ref.split("/")[-1]
                        if schema_name in schemas:
                            props = list(
                                schemas[schema_name].get("properties", {}).keys()
                            )
                            doc_content += f"\nRequest Schema: {schema_name}"
                            doc_content += f"\nRequest Properties: {', '.join(props)}"

            documents.append(doc_content)
            metadatas.append(
                {
                    "resource": resource_name,
                    "method": method,
                    "path": path,
                    "summary": endpoint.get("summary", "")[:200],
                    "has_path_params": "{" in path,
                    "has_request_body": endpoint.get("request_body") is not None,
                }
            )
            ids.append(f"swagger_{resource_name.lower()}_{method.lower()}_{len(ids)}")

    # Add to collection
    if documents:
        try:
            # Remove existing documents first
            existing = collection.get(ids=ids)
            if existing and existing.get("ids"):
                collection.delete(ids=existing["ids"])

            collection.add(documents=documents, metadatas=metadatas, ids=ids)
            log.safe_print(
                f"[OK] Embedded {len(documents)} endpoints to api_swagger collection"
            )
        except Exception as e:
            log.safe_print(f"[ERROR] Failed to embed swagger: {e}")

    return collection


def _rag_get_api_learning_summary(self) -> dict:
    """Get summary of stored API actions by resource."""
    try:
        collection = self.get_api_learning_collection()

        all_docs = collection.get(include=["metadatas"])

        summary = {
            "total": len(all_docs.get("ids", [])),
            "correct_count": 0,
            "incorrect_count": 0,
            "resources": {},
        }

        for metadata in all_docs.get("metadatas", []):
            resource = metadata.get("resource", "unknown")
            status = metadata.get("status", "[incorrect]")

            if resource not in summary["resources"]:
                summary["resources"][resource] = {
                    "actions": [],
                    "correct": 0,
                    "incorrect": 0,
                }

            summary["resources"][resource]["actions"].append(
                metadata.get("action_key", "unknown")
            )

            if status == "[correct]":
                summary["resources"][resource]["correct"] += 1
                summary["correct_count"] += 1
            else:
                summary["resources"][resource]["incorrect"] += 1
                summary["incorrect_count"] += 1

        return summary

    except Exception as e:
        log.safe_print(f"[ERROR] Failed to get API learning summary: {e}")
        return {"error": str(e)}


# Add API methods to Rag class
Rag.get_api_learning_collection = _rag_get_api_learning_collection
Rag.get_api_swagger_collection = _rag_get_api_swagger_collection
Rag.retrieve_api_action_for_intent = _rag_retrieve_api_action_for_intent
Rag.retrieve_swagger_for_intent = _rag_retrieve_swagger_for_intent
Rag.store_api_action_from_duo = _rag_store_api_action_from_duo
Rag.embed_swagger_to_api_swagger_collection = (
    _rag_embed_swagger_to_api_swagger_collection
)
Rag.get_api_learning_summary = _rag_get_api_learning_summary


if __name__ == "__main__":
    rag = Rag()

    # Debug the embedding model first
    rag.debug_embedding_model()

    learn_data_collection = rag.embed_learn_data()
    log.safe_print(f"[OK] learn_data_collection:\n{learn_data_collection}")

    similar_semantic_learn_data = rag.retrieve_similar_semantic(
        learn_data_collection,
        intent="Efforts Consumed and Planned on team level for R1.1",
    )
    log.safe_print(f"[OK] similar_semantic_learn_data:\n{similar_semantic_learn_data}")
