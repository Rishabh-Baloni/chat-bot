import json
import os
import shutil
from typing import List, Dict
from pathlib import Path
from datetime import datetime
from config import get_config
from logger import logger

config = get_config()

class KnowledgeManager:
    def __init__(self):
        self.knowledge_dir = Path(config.knowledge_dir)
        self.core_knowledge_file = self.knowledge_dir / "core_knowledge.json"
        self.expanded_knowledge_file = self.knowledge_dir / "expanded_knowledge.json"
        self.backup_dir = self.knowledge_dir / "backups"
        
        # Ensure directories exist
        self.knowledge_dir.mkdir(exist_ok=True)
        self.backup_dir.mkdir(exist_ok=True)
        
        # Initialize files if they don't exist
        self._init_knowledge_files()
    
    def _init_knowledge_files(self):
        """Initialize knowledge files with empty arrays if they don't exist"""
        if not self.core_knowledge_file.exists():
            self._save_json_atomic(self.core_knowledge_file, [])
        
        if not self.expanded_knowledge_file.exists():
            self._save_json_atomic(self.expanded_knowledge_file, [])
    
    def _load_json(self, file_path: Path) -> List[Dict]:
        """Load JSON file safely with error handling"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data if isinstance(data, list) else []
        except (FileNotFoundError, json.JSONDecodeError, UnicodeDecodeError) as e:
            logger.error_logger.error(f"Failed to load {file_path}: {e}")
            return []
    
    def _save_json_atomic(self, file_path: Path, data: List[Dict]):
        """Save JSON file atomically with backup protection"""
        try:
            # Create backup if file exists
            if file_path.exists():
                backup_name = f"{file_path.stem}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                backup_path = self.backup_dir / backup_name
                shutil.copy2(file_path, backup_path)
                
                # Keep only last 5 backups
                self._cleanup_backups(file_path.stem)
            
            # Write to temporary file first
            temp_path = file_path.with_suffix('.tmp')
            with open(temp_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            # Atomic move
            temp_path.replace(file_path)
            
        except Exception as e:
            logger.error_logger.error(f"Failed to save {file_path}: {e}")
            # Clean up temp file if it exists
            temp_path = file_path.with_suffix('.tmp')
            if temp_path.exists():
                temp_path.unlink()
            raise
    
    def _cleanup_backups(self, file_stem: str, keep_count: int = 5):
        """Keep only the most recent backups"""
        try:
            backups = sorted(
                [f for f in self.backup_dir.glob(f"{file_stem}_*.json")],
                key=lambda x: x.stat().st_mtime,
                reverse=True
            )
            
            for backup in backups[keep_count:]:
                backup.unlink()
                
        except Exception as e:
            logger.error_logger.error(f"Failed to cleanup backups: {e}")
    
    def load_all_knowledge(self) -> List[Dict]:
        """Load both core and expanded knowledge"""
        core = self._load_json(self.core_knowledge_file)
        expanded = self._load_json(self.expanded_knowledge_file)
        return core + expanded
    
    def find_relevant_knowledge(self, user_message: str, max_results: int = 5) -> List[Dict]:
        """Find knowledge entries relevant to user message with improved ranking"""
        all_knowledge = self.load_all_knowledge()
        if not all_knowledge:
            return []
        
        user_message_lower = user_message.lower()
        scored_entries = []
        
        for entry in all_knowledge:
            score = self._calculate_relevance_score(entry, user_message_lower)
            if score > 0:
                entry_with_score = entry.copy()
                entry_with_score['_relevance_score'] = score
                scored_entries.append(entry_with_score)
        
        # Sort by relevance score (descending) and confidence (descending)
        scored_entries.sort(
            key=lambda x: (x['_relevance_score'], float(x.get('confidence', 0.5))),
            reverse=True
        )
        
        # Remove score before returning
        result = []
        for entry in scored_entries[:max_results]:
            clean_entry = entry.copy()
            clean_entry.pop('_relevance_score', None)
            result.append(clean_entry)
        
        return result
    
    def _calculate_relevance_score(self, entry: Dict, user_message_lower: str) -> float:
        """Calculate relevance score for knowledge entry"""
        score = 0.0
        
        # Topic match (highest weight)
        topic = entry.get('topic', '').lower()
        if topic and topic in user_message_lower:
            score += 3.0
        
        # Keyword matches
        keywords = entry.get('symptoms_or_keywords', [])
        for keyword in keywords:
            if keyword.lower() in user_message_lower:
                score += 1.0
        
        # Partial matches (lower weight)
        for keyword in keywords:
            if any(word in user_message_lower for word in keyword.lower().split()):
                score += 0.3
        
        # Confidence boost
        confidence = float(entry.get('confidence', 0.5))
        score *= (0.5 + confidence)
        
        return score
    
    def add_expanded_knowledge(self, new_entries: List[Dict]):
        """Add new entries to expanded knowledge with atomic write"""
        if not new_entries:
            return
        
        current_expanded = self._load_json(self.expanded_knowledge_file)
        current_expanded.extend(new_entries)
        self._save_json_atomic(self.expanded_knowledge_file, current_expanded)
    
    def add_core_knowledge(self, new_entries: List[Dict]):
        """Add new entries to core knowledge with atomic write"""
        if not new_entries:
            return
        
        current_core = self._load_json(self.core_knowledge_file)
        current_core.extend(new_entries)
        self._save_json_atomic(self.core_knowledge_file, current_core)