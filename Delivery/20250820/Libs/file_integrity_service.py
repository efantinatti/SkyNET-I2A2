"""
File Integrity Management Service for SkyNET I2A2 HR Automation System

Manages MD5 checksums for input files to detect changes and avoid unnecessary processing.
Follows Single Responsibility Principle for file integrity monitoring.
"""

import hashlib
import os
from pathlib import Path
from typing import Dict, List, Set, Optional
import logging

logger = logging.getLogger(__name__)


class FileIntegrityService:
    """
    Service for managing file integrity using MD5 checksums.
    
    Monitors changes in import files and tracks them using MD5 hashes
    stored in dedicated .md5 files within the md5/ subdirectory.
    """
    
    def __init__(self, import_dir: str = 'Import', md5_dir: str = 'md5'):
        """
        Initialize the file integrity service.
        
        Args:
            import_dir: Directory containing import files
            md5_dir: Directory to store MD5 checksum files (at same level as import_dir)
        """
        self.import_dir = Path(import_dir)
        self.md5_dir = Path(md5_dir)
        self.md5_dir.mkdir(parents=True, exist_ok=True)
        
        # Expected import files
        self.monitored_files = [
            'ATIVOS.xlsx',
            'Base dias uteis.xlsx',
            'Base sindicato x valor.xlsx',
            'DESLIGADOS.xlsx',
            'ESTÁGIO.xlsx',
            'EXTERIOR.xlsx',
            'FÉRIAS.xlsx',
            'ADMISSÃO ABRIL.xlsx',
            'AFASTAMENTOS.xlsx',
            'APRENDIZ.xlsx',
            'VR MENSAL 05.2025.xlsx'
        ]
    
    def calculate_file_md5(self, file_path: Path) -> str:
        """
        Calculate MD5 checksum for a file.
        
        Args:
            file_path: Path to the file
            
        Returns:
            MD5 checksum as hexadecimal string
            
        Raises:
            FileNotFoundError: If file doesn't exist
            IOError: If file cannot be read
        """
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        md5_hash = hashlib.md5()
        
        try:
            with open(file_path, 'rb') as f:
                # Read file in chunks to handle large files efficiently
                for chunk in iter(lambda: f.read(4096), b""):
                    md5_hash.update(chunk)
            
            return md5_hash.hexdigest()
            
        except IOError as e:
            raise IOError(f"Error reading file {file_path}: {e}")
    
    def get_stored_md5(self, filename: str) -> Optional[str]:
        """
        Get stored MD5 checksum for a file.
        
        Args:
            filename: Name of the file (without path)
            
        Returns:
            Stored MD5 checksum or None if not found
        """
        md5_file_path = self.md5_dir / f"{filename}.md5"
        
        if not md5_file_path.exists():
            return None
        
        try:
            with open(md5_file_path, 'r', encoding='utf-8') as f:
                stored_md5 = f.read().strip()
                return stored_md5 if stored_md5 else None
                
        except IOError as e:
            logger.warning(f"Error reading MD5 file {md5_file_path}: {e}")
            return None
    
    def store_md5(self, filename: str, md5_checksum: str) -> bool:
        """
        Store MD5 checksum for a file.
        
        Args:
            filename: Name of the file (without path)
            md5_checksum: MD5 checksum to store
            
        Returns:
            True if successfully stored, False otherwise
        """
        md5_file_path = self.md5_dir / f"{filename}.md5"
        
        try:
            with open(md5_file_path, 'w', encoding='utf-8') as f:
                f.write(md5_checksum)
            
            logger.info(f"Stored MD5 checksum for {filename}: {md5_checksum}")
            return True
            
        except IOError as e:
            logger.error(f"Error storing MD5 file {md5_file_path}: {e}")
            return False
    
    def check_file_changes(self) -> Dict[str, Dict[str, str]]:
        """
        Check all monitored files for changes.
        
        Returns:
            Dictionary with file change information:
            {
                'changed': {'filename': 'new_md5', ...},
                'new': {'filename': 'new_md5', ...},
                'missing': ['filename', ...],
                'unchanged': ['filename', ...]
            }
        """
        result = {
            'changed': {},
            'new': {},
            'missing': [],
            'unchanged': []
        }
        
        for filename in self.monitored_files:
            file_path = self.import_dir / filename
            
            # Check if file exists
            if not file_path.exists():
                result['missing'].append(filename)
                logger.warning(f"Monitored file not found: {filename}")
                continue
            
            try:
                # Calculate current MD5
                current_md5 = self.calculate_file_md5(file_path)
                
                # Get stored MD5
                stored_md5 = self.get_stored_md5(filename)
                
                if stored_md5 is None:
                    # New file (no previous MD5)
                    result['new'][filename] = current_md5
                    logger.info(f"New file detected: {filename}")
                    
                elif stored_md5 != current_md5:
                    # File changed
                    result['changed'][filename] = current_md5
                    logger.info(f"File changed: {filename} (old: {stored_md5[:8]}..., new: {current_md5[:8]}...)")
                    
                else:
                    # File unchanged
                    result['unchanged'].append(filename)
                    logger.debug(f"File unchanged: {filename}")
                    
            except Exception as e:
                logger.error(f"Error checking file {filename}: {e}")
                result['missing'].append(filename)
        
        return result
    
    def update_checksums(self, file_changes: Dict[str, Dict[str, str]]) -> bool:
        """
        Update stored checksums for changed and new files.
        
        Args:
            file_changes: Result from check_file_changes()
            
        Returns:
            True if all updates successful, False otherwise
        """
        success = True
        
        # Update checksums for changed files
        for filename, md5_checksum in file_changes['changed'].items():
            if not self.store_md5(filename, md5_checksum):
                success = False
        
        # Store checksums for new files
        for filename, md5_checksum in file_changes['new'].items():
            if not self.store_md5(filename, md5_checksum):
                success = False
        
        return success
    
    def has_changes(self) -> bool:
        """
        Check if any monitored files have changed.
        
        Returns:
            True if any files have changed or are new, False otherwise
        """
        changes = self.check_file_changes()
        return bool(changes['changed'] or changes['new'])
    
    def get_change_summary(self) -> str:
        """
        Get a human-readable summary of file changes.
        
        Returns:
            Summary string describing the changes
        """
        changes = self.check_file_changes()
        
        summary_parts = []
        
        if changes['new']:
            summary_parts.append(f"New files: {len(changes['new'])}")
        
        if changes['changed']:
            summary_parts.append(f"Changed files: {len(changes['changed'])}")
        
        if changes['unchanged']:
            summary_parts.append(f"Unchanged files: {len(changes['unchanged'])}")
        
        if changes['missing']:
            summary_parts.append(f"Missing files: {len(changes['missing'])}")
        
        return ", ".join(summary_parts) if summary_parts else "No files monitored"
    
    def initialize_monitoring(self) -> bool:
        """
        Initialize monitoring for all existing files.
        
        Creates initial MD5 checksums for all found files.
        
        Returns:
            True if initialization successful, False otherwise
        """
        logger.info("Initializing file monitoring...")
        
        success = True
        initialized_count = 0
        
        for filename in self.monitored_files:
            file_path = self.import_dir / filename
            
            if file_path.exists():
                try:
                    md5_checksum = self.calculate_file_md5(file_path)
                    if self.store_md5(filename, md5_checksum):
                        initialized_count += 1
                    else:
                        success = False
                        
                except Exception as e:
                    logger.error(f"Error initializing monitoring for {filename}: {e}")
                    success = False
            else:
                logger.warning(f"File not found during initialization: {filename}")
        
        logger.info(f"Initialized monitoring for {initialized_count} files")
        return success
    
    def clean_orphaned_md5_files(self) -> int:
        """
        Remove MD5 files for which the corresponding data file doesn't exist.
        
        Returns:
            Number of orphaned MD5 files removed
        """
        removed_count = 0
        
        if not self.md5_dir.exists():
            return removed_count
        
        for md5_file in self.md5_dir.glob("*.md5"):
            # Extract original filename
            original_filename = md5_file.stem
            original_file_path = self.import_dir / original_filename
            
            if not original_file_path.exists():
                try:
                    md5_file.unlink()
                    removed_count += 1
                    logger.info(f"Removed orphaned MD5 file: {md5_file.name}")
                    
                except Exception as e:
                    logger.error(f"Error removing orphaned MD5 file {md5_file}: {e}")
        
        return removed_count