"""
Session management for maintaining state across scraping operations
"""

import asyncio
import json
import time
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from playwright.async_api import Page, BrowserContext

from ..config import Settings
from ..utils.logger import ComponentLogger
from ..utils.helpers import generate_id


@dataclass
class SessionState:
    """Represents the state of a scraping session"""
    session_id: str
    url: str
    cookies: List[Dict[str, Any]] = field(default_factory=list)
    local_storage: Dict[str, str] = field(default_factory=dict)
    session_storage: Dict[str, str] = field(default_factory=dict)
    request_headers: Dict[str, str] = field(default_factory=dict)
    
    # Navigation state
    current_page: str = ""
    visited_pages: List[str] = field(default_factory=list)
    
    # Form state
    form_data: Dict[str, Any] = field(default_factory=dict)
    
    # Session metadata
    created_at: float = field(default_factory=time.time)
    last_activity: float = field(default_factory=time.time)
    request_count: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert session state to dictionary"""
        return {
            "session_id": self.session_id,
            "url": self.url,
            "cookies": self.cookies,
            "local_storage": self.local_storage,
            "session_storage": self.session_storage,
            "request_headers": self.request_headers,
            "current_page": self.current_page,
            "visited_pages": self.visited_pages,
            "form_data": self.form_data,
            "created_at": self.created_at,
            "last_activity": self.last_activity,
            "request_count": self.request_count
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SessionState':
        """Create session state from dictionary"""
        return cls(**data)


class SessionManager:
    """
    Manages scraping sessions with state persistence and restoration
    """
    
    def __init__(self, settings: Settings):
        self.settings = settings
        self.logger = ComponentLogger("session_manager")
        
        # Active sessions
        self.sessions: Dict[str, SessionState] = {}
        
        # Session configuration
        self.max_session_age = 3600  # 1 hour
        self.max_sessions = 10
        self.session_rotation_enabled = True
        
        self.logger.info("Session manager initialized")
    
    async def create_session(self, url: str, session_id: Optional[str] = None) -> SessionState:
        """
        Create a new scraping session
        
        Args:
            url: Base URL for the session
            session_id: Optional session ID, generated if not provided
            
        Returns:
            SessionState object
        """
        if session_id is None:
            session_id = generate_id("session")
        
        # Clean up old sessions if needed
        await self._cleanup_old_sessions()
        
        session = SessionState(
            session_id=session_id,
            url=url
        )
        
        self.sessions[session_id] = session
        
        self.logger.info("Session created", 
                        session_id=session_id,
                        url=url,
                        total_sessions=len(self.sessions))
        
        return session
    
    async def save_session_state(self, session_id: str, page: Page, context: BrowserContext):
        """
        Save current browser state to session
        
        Args:
            session_id: Session identifier
            page: Playwright page object
            context: Browser context
        """
        if session_id not in self.sessions:
            self.logger.warning("Session not found for state save", session_id=session_id)
            return
        
        session = self.sessions[session_id]
        
        try:
            # Save cookies
            session.cookies = await context.cookies()
            
            # Save storage
            session.local_storage = await page.evaluate("""
                () => {
                    const storage = {};
                    for (let i = 0; i < localStorage.length; i++) {
                        const key = localStorage.key(i);
                        storage[key] = localStorage.getItem(key);
                    }
                    return storage;
                }
            """)
            
            session.session_storage = await page.evaluate("""
                () => {
                    const storage = {};
                    for (let i = 0; i < sessionStorage.length; i++) {
                        const key = sessionStorage.key(i);
                        storage[key] = sessionStorage.getItem(key);
                    }
                    return storage;
                }
            """)
            
            # Save current page URL
            session.current_page = page.url
            
            # Update activity
            session.last_activity = time.time()
            session.request_count += 1
            
            # Add to visited pages if not already there
            if session.current_page not in session.visited_pages:
                session.visited_pages.append(session.current_page)
            
            self.logger.debug("Session state saved", 
                            session_id=session_id,
                            cookies_count=len(session.cookies),
                            local_storage_keys=len(session.local_storage),
                            visited_pages=len(session.visited_pages))
            
        except Exception as e:
            self.logger.error("Failed to save session state", 
                            session_id=session_id,
                            error=str(e))
    
    async def restore_session_state(self, session_id: str, page: Page, context: BrowserContext):
        """
        Restore browser state from session
        
        Args:
            session_id: Session identifier
            page: Playwright page object
            context: Browser context
        """
        if session_id not in self.sessions:
            self.logger.warning("Session not found for state restore", session_id=session_id)
            return
        
        session = self.sessions[session_id]
        
        try:
            # Restore cookies
            if session.cookies:
                await context.add_cookies(session.cookies)
                self.logger.debug("Cookies restored", 
                                session_id=session_id,
                                cookies_count=len(session.cookies))
            
            # Navigate to base URL first
            await page.goto(session.url, wait_until="domcontentloaded")
            
            # Restore local storage
            if session.local_storage:
                for key, value in session.local_storage.items():
                    await page.evaluate(f"localStorage.setItem('{key}', '{value}')")
                
                self.logger.debug("Local storage restored", 
                                session_id=session_id,
                                keys_count=len(session.local_storage))
            
            # Restore session storage
            if session.session_storage:
                for key, value in session.session_storage.items():
                    await page.evaluate(f"sessionStorage.setItem('{key}', '{value}')")
                
                self.logger.debug("Session storage restored", 
                                session_id=session_id,
                                keys_count=len(session.session_storage))
            
            # Navigate to last page if different from base URL
            if session.current_page and session.current_page != session.url:
                await page.goto(session.current_page, wait_until="domcontentloaded")
            
            # Update activity
            session.last_activity = time.time()
            
            self.logger.info("Session state restored", 
                           session_id=session_id,
                           current_page=session.current_page)
            
        except Exception as e:
            self.logger.error("Failed to restore session state", 
                            session_id=session_id,
                            error=str(e))
    
    async def handle_form_interaction(self, 
                                     session_id: str,
                                     form_selector: str,
                                     form_data: Dict[str, str],
                                     page: Page):
        """
        Handle form interactions with state tracking
        
        Args:
            session_id: Session identifier
            form_selector: CSS selector for the form
            form_data: Form field data
            page: Playwright page object
        """
        if session_id not in self.sessions:
            self.logger.warning("Session not found for form interaction", session_id=session_id)
            return
        
        session = self.sessions[session_id]
        
        try:
            # Fill form fields
            for field_selector, value in form_data.items():
                try:
                    await page.fill(field_selector, value)
                    self.logger.debug("Form field filled", 
                                    session_id=session_id,
                                    field=field_selector)
                except Exception as e:
                    self.logger.warning("Failed to fill form field", 
                                      session_id=session_id,
                                      field=field_selector,
                                      error=str(e))
            
            # Save form data to session
            form_key = f"form_{form_selector}"
            session.form_data[form_key] = form_data
            
            # Update activity
            session.last_activity = time.time()
            
            self.logger.info("Form interaction completed", 
                           session_id=session_id,
                           form=form_selector,
                           fields=len(form_data))
            
        except Exception as e:
            self.logger.error("Form interaction failed", 
                            session_id=session_id,
                            error=str(e))
    
    async def handle_navigation(self, 
                               session_id: str,
                               url: str,
                               page: Page,
                               context: BrowserContext):
        """
        Handle navigation with session state management
        
        Args:
            session_id: Session identifier
            url: URL to navigate to
            page: Playwright page object
            context: Browser context
        """
        if session_id not in self.sessions:
            self.logger.warning("Session not found for navigation", session_id=session_id)
            return
        
        session = self.sessions[session_id]
        
        try:
            # Save current state before navigation
            await self.save_session_state(session_id, page, context)
            
            # Navigate to new URL
            await page.goto(url, wait_until="networkidle")
            
            # Update session with new page
            session.current_page = url
            if url not in session.visited_pages:
                session.visited_pages.append(url)
            
            session.last_activity = time.time()
            session.request_count += 1
            
            self.logger.info("Navigation completed", 
                           session_id=session_id,
                           url=url,
                           total_visited=len(session.visited_pages))
            
        except Exception as e:
            self.logger.error("Navigation failed", 
                            session_id=session_id,
                            url=url,
                            error=str(e))
    
    def get_session(self, session_id: str) -> Optional[SessionState]:
        """Get session by ID"""
        return self.sessions.get(session_id)
    
    def get_session_history(self, session_id: str) -> List[str]:
        """Get navigation history for session"""
        session = self.sessions.get(session_id)
        return session.visited_pages if session else []
    
    def should_rotate_session(self, session_id: str) -> bool:
        """Check if session should be rotated"""
        if not self.session_rotation_enabled:
            return False
        
        session = self.sessions.get(session_id)
        if not session:
            return True
        
        # Check age
        age = time.time() - session.created_at
        if age > self.max_session_age:
            return True
        
        # Check request count (rotate after many requests)
        if session.request_count > 100:
            return True
        
        return False
    
    async def rotate_session(self, old_session_id: str, url: str) -> SessionState:
        """
        Create new session and transfer relevant state from old session
        
        Args:
            old_session_id: ID of session to rotate
            url: URL for new session
            
        Returns:
            New SessionState object
        """
        # Create new session
        new_session = await self.create_session(url)
        
        # Transfer relevant state from old session
        old_session = self.sessions.get(old_session_id)
        if old_session:
            # Keep some cookies that might be useful
            domain_cookies = [
                cookie for cookie in old_session.cookies
                if not cookie.get('httpOnly', False)  # Only non-httpOnly cookies
            ]
            new_session.cookies = domain_cookies
            
            self.logger.info("Session rotated", 
                           old_session=old_session_id,
                           new_session=new_session.session_id,
                           transferred_cookies=len(domain_cookies))
        
        # Clean up old session
        await self._cleanup_session(old_session_id)
        
        return new_session
    
    async def cleanup_session(self, session_id: str):
        """Clean up a specific session"""
        await self._cleanup_session(session_id)
    
    async def _cleanup_session(self, session_id: str):
        """Internal method to clean up session"""
        if session_id in self.sessions:
            session = self.sessions[session_id]
            
            self.logger.info("Cleaning up session", 
                           session_id=session_id,
                           age=time.time() - session.created_at,
                           requests=session.request_count)
            
            del self.sessions[session_id]
    
    async def _cleanup_old_sessions(self):
        """Clean up old/expired sessions"""
        current_time = time.time()
        to_cleanup = []
        
        for session_id, session in self.sessions.items():
            # Check age
            if current_time - session.created_at > self.max_session_age:
                to_cleanup.append(session_id)
            # Check inactivity
            elif current_time - session.last_activity > 1800:  # 30 minutes inactive
                to_cleanup.append(session_id)
        
        # Clean up old sessions
        for session_id in to_cleanup:
            await self._cleanup_session(session_id)
        
        # If still too many sessions, clean up least recently used
        while len(self.sessions) > self.max_sessions:
            lru_session_id = min(self.sessions.keys(), 
                               key=lambda sid: self.sessions[sid].last_activity)
            await self._cleanup_session(lru_session_id)
    
    def get_session_stats(self) -> Dict[str, Any]:
        """Get session management statistics"""
        current_time = time.time()
        
        stats = {
            "total_sessions": len(self.sessions),
            "max_sessions": self.max_sessions,
            "sessions": []
        }
        
        for session_id, session in self.sessions.items():
            session_stats = {
                "session_id": session_id,
                "url": session.url,
                "age_seconds": current_time - session.created_at,
                "last_activity_seconds_ago": current_time - session.last_activity,
                "request_count": session.request_count,
                "visited_pages": len(session.visited_pages),
                "cookies_count": len(session.cookies),
                "should_rotate": self.should_rotate_session(session_id)
            }
            stats["sessions"].append(session_stats)
        
        return stats
    
    async def export_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Export session state for persistence"""
        session = self.sessions.get(session_id)
        if not session:
            return None
        
        return session.to_dict()
    
    async def import_session(self, session_data: Dict[str, Any]) -> SessionState:
        """Import session state from persistence"""
        session = SessionState.from_dict(session_data)
        self.sessions[session.session_id] = session
        
        self.logger.info("Session imported", 
                        session_id=session.session_id,
                        url=session.url)
        
        return session