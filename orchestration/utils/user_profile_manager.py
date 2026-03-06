"""
User Profile Manager
Handles persistence of user profile and onboarding status
"""

import json
import os
from typing import Dict, Any, Optional
from pathlib import Path
from utils.logger import get_logger

logger = get_logger()


class UserProfileManager:
    """Manages user profile persistence"""
    
    def __init__(self, user_id: str = "default_user"):
        self.user_id = user_id
        self.profile_dir = Path.home() / ".eva" / "profiles"
        self.profile_file = self.profile_dir / f"{user_id}.json"
        
        # Create directory if it doesn't exist
        self.profile_dir.mkdir(parents=True, exist_ok=True)
    
    def save_profile(self, profile_data: Dict[str, Any]) -> bool:
        """
        Save user profile to disk
        
        Args:
            profile_data: User profile data including onboarding_completed flag
        
        Returns:
            True if successful, False otherwise
        """
        try:
            with open(self.profile_file, 'w') as f:
                json.dump(profile_data, f, indent=2)
            logger.info(f"User profile saved for {self.user_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to save user profile: {str(e)}")
            return False
    
    def load_profile(self) -> Optional[Dict[str, Any]]:
        """
        Load user profile from disk
        
        Returns:
            User profile data if exists, None otherwise
        """
        try:
            if not self.profile_file.exists():
                logger.info(f"No existing profile found for {self.user_id}")
                return None
            
            with open(self.profile_file, 'r') as f:
                profile_data = json.load(f)
            
            logger.info(f"User profile loaded for {self.user_id}")
            return profile_data
        except Exception as e:
            logger.error(f"Failed to load user profile: {str(e)}")
            return None
    
    def profile_exists(self) -> bool:
        """Check if user profile exists"""
        return self.profile_file.exists()
    
    def delete_profile(self) -> bool:
        """
        Delete user profile (for testing or reset)
        
        Returns:
            True if successful, False otherwise
        """
        try:
            if self.profile_file.exists():
                self.profile_file.unlink()
                logger.info(f"User profile deleted for {self.user_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete user profile: {str(e)}")
            return False

# Made with Bob
