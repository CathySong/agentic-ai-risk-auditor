#!/usr/bin/env python3
"""
Web scraper tool for the Agentic AI Risk Auditor.
Extracts and analyzes website content for risk assessment.
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional
from urllib.parse import urlparse
import re

import aiohttp
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright

from app.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class WebScraper:
    """Web scraper for extracting and analyzing website content."""
    
    def __init__(self):
        self.timeout = settings.tool.web_scraper_timeout
        self.max_pages = settings.tool.web_scraper_max_pages
        self.user_agent = settings.tool.web_scraper_user_agent
        
        # Initialize session
        self.session = None
        self.playwright = None
        self.browser = None
        
        logger.info("Web scraper initialized")
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self._initialize()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self._cleanup()
    
    async def _initialize(self):
        """Initialize resources."""
        # Create aiohttp session
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=self.timeout),
            headers={"User-Agent": self.user_agent}
        )
        
        # Initialize Playwright for JavaScript-heavy sites
        try:
            self.playwright = await async_playwright().start()
            self.browser = await self.playwright.chromium.launch(headless=True)
            logger.info("Playwright browser initialized")
        except Exception as e:
            logger.warning(f"Failed to initialize Playwright: {e}")
            self.playwright = None
            self.browser = None
    
    async def _cleanup(self):
        """Clean up resources."""
        if self.session:
            await self.session.close()
        
        if self.browser:
            await self.browser.close()
        
        if self.playwright:
            await self.playwright.stop()
    
    async def scrape(
        self,
        url: str,
        parameters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Scrape and analyze a website.
        
        Args:
            url: URL to scrape
            parameters: Additional scraping parameters
            
        Returns:
            Dictionary with scraped content and analysis
        """
        logger.info(f"Scraping URL: {url}")
        
        if parameters is None:
            parameters = {}
        
        try:
            # Validate URL
            parsed_url = urlparse(url)
            if not parsed_url.scheme or not parsed_url.netloc:
                raise ValueError(f"Invalid URL: {url}")
            
            # Determine scraping method
            use_playwright = parameters.get("use_playwright", False)
            
            # Scrape content
            if use_playwright and self.browser:
                content = await self._scrape_with_playwright(url, parameters)
            else:
                content = await self._scrape_with_requests(url, parameters)
            
            # Analyze content
            analysis = await self._analyze_content(content, url, parameters)
            
            # Extract links for potential further scraping
            links = self._extract_links(content.get("html", ""), url)
            
            # Limit links to max_pages
            if links and parameters.get("follow_links", False):
                links = links[:self.max_pages - 1]
            
            result = {
                "url": url,
                "scraped_at": asyncio.get_event_loop().time(),
                "content": content,
                "analysis": analysis,
                "links_found": len(links),
                "links_sample": links[:10] if links else [],
                "metadata": {
                    "scraping_method": "playwright" if use_playwright else "requests",
                    "content_length": len(content.get("text", "")),
                    "success": True
                }
            }
            
            logger.info(f"Successfully scraped {url}")
            return result
            
        except Exception as e:
            logger.error(f"Failed to scrape {url}: {e}")
            
            return {
                "url": url,
                "scraped_at": asyncio.get_event_loop().time(),
                "error": str(e),
                "content": {},
                "analysis": {},
                "metadata": {
                    "success": False,
                    "error_type": type(e).__name__
                }
            }
    
    async def _scrape_with_requests(
        self,
        url: str,
        parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Scrape using aiohttp requests."""
        try:
            async with self.session.get(url) as response:
                # Check status
                if response.status != 200:
                    raise ValueError(f"HTTP {response.status}: {response.reason}")
                
                # Get content
                html = await response.text()
                
                # Parse with BeautifulSoup
                soup = BeautifulSoup(html, 'html.parser')
                
                # Extract text
                text = soup.get_text(separator=' ', strip=True)
                
                # Extract metadata
                title = soup.title.string if soup.title else ""
                meta_description = ""
                meta_keywords = ""
                
                for meta in soup.find_all('meta'):
                    if meta.get('name') == 'description':
                        meta_description = meta.get('content', '')
                    elif meta.get('name') == 'keywords':
                        meta_keywords = meta.get('content', '')
                
                # Extract forms (for privacy/security analysis)
                forms = []
                for form in soup.find_all('form'):
                    form_data = {
                        "action": form.get('action', ''),
                        "method": form.get('method', 'get').upper(),
                        "inputs": []
                    }
                    
                    for input_elem in form.find_all(['input', 'textarea', 'select']):
                        input_data = {
                            "type": input_elem.name,
                            "name": input_elem.get('name', ''),
                            "id": input_elem.get('id', ''),
                            "required": input_elem.get('required') is not None
                        }
                        form_data["inputs"].append(input_data)
                    
                    forms.append(form_data)
                
                # Extract scripts (for security analysis)
                scripts = []
                for script in soup.find_all('script'):
                    if script.get('src'):
                        scripts.append({
                            "src": script.get('src'),
                            "type": script.get('type', ''),
                            "async": script.get('async') is not None,
                            "defer": script.get('defer') is not None
                        })
                
                return {
                    "html": html,
                    "text": text,
                    "title": title,
                    "meta_description": meta_description,
                    "meta_keywords": meta_keywords,
                    "forms": forms,
                    "scripts": scripts,
                    "response_status": response.status,
                    "content_type": response.headers.get('Content-Type', ''),
                    "headers": dict(response.headers)
                }
                
        except Exception as e:
            logger.error(f"Request scraping failed for {url}: {e}")
            raise
    
    async def _scrape_with_playwright(
        self,
        url: str,
        parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Scrape using Playwright for JavaScript-heavy sites."""
        if not self.browser:
            raise ValueError("Playwright browser not initialized")
        
        try:
            # Create page
            context = await self.browser.new_context(
                user_agent=self.user_agent
            )
            page = await context.new_page()
            
            # Navigate to URL
            await page.goto(url, wait_until="networkidle")
            
            # Wait for additional time if specified
            wait_time = parameters.get("wait_time", 0)
            if wait_time > 0:
                await asyncio.sleep(wait_time)
            
            # Get page content
            html = await page.content()
            
            # Take screenshot if requested
            screenshot = None
            if parameters.get("take_screenshot", False):
                screenshot = await page.screenshot(full_page=True)
            
            # Evaluate JavaScript for additional data
            page_data = await page.evaluate("""
                () => {
                    return {
                        title: document.title,
                        url: window.location.href,
                        cookies: document.cookie,
                        localStorage: Object.keys(localStorage).length,
                        sessionStorage: Object.keys(sessionStorage).length,
                        forms: Array.from(document.forms).map(form => ({
                            action: form.action,
                            method: form.method,
                            inputs: Array.from(form.elements).map(el => ({
                                type: el.type,
                                name: el.name,
                                required: el.required
                            }))
                        })),
                        scripts: Array.from(document.scripts).map(script => ({
                            src: script.src,
                            type: script.type
                        }))
                    };
                }
            """)
            
            # Parse HTML with BeautifulSoup
            soup = BeautifulSoup(html, 'html.parser')
            text = soup.get_text(separator=' ', strip=True)
            
            # Close page
            await page.close()
            await context.close()
            
            return {
                "html": html,
                "text": text,
                "title": page_data.get("title", ""),
                "url": page_data.get("url", url),
                "cookies": page_data.get("cookies", ""),
                "local_storage_items": page_data.get("localStorage", 0),
                "session_storage_items": page_data.get("sessionStorage", 0),
                "forms": page_data.get("forms", []),
                "scripts": page_data.get("scripts", []),
                "screenshot": screenshot,
                "scraping_method": "playwright"
            }
            
        except Exception as e:
            logger.error(f"Playwright scraping failed for {url}: {e}")
            raise
    
    async def _analyze_content(
        self,
        content: Dict[str, Any],
        url: str,
        parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Analyze scraped content for risk assessment."""
        text = content.get("text", "")
        html = content.get("html", "")
        forms = content.get("forms", [])
        scripts = content.get("scripts", [])
        
        analysis = {
            "privacy_indicators": self._analyze_privacy_indicators(text, forms),
            "security_indicators": self._analyze_security_indicators(html, scripts),
            "compliance_indicators": self._analyze_compliance_indicators(text),
            "content_analysis": self._analyze_content_structure(text),
            "risk_score": 0.0
        }
        
        # Calculate overall risk score
        risk_factors = []
        
        # Privacy risk factors
        privacy_risk = analysis["privacy_indicators"].get("risk_level", 0)
        risk_factors.append(privacy_risk)
        
        # Security risk factors
        security_risk = analysis["security_indicators"].get("risk_level", 0)
        risk_factors.append(security_risk)
        
        # Compliance risk factors
        compliance_issues = len(analysis["compliance_indicators"].get("missing_terms", []))
        compliance_risk = min(compliance_issues * 0.2, 1.0)  # Scale to 0-1
        risk_factors.append(compliance_risk)
        
        # Calculate average risk
        if risk_factors:
            analysis["risk_score"] = sum(risk_factors) / len(risk_factors)
        
        return analysis
    
    def _analyze_privacy_indicators(
        self,
        text: str,
        forms: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Analyze privacy indicators in content."""
        text_lower = text.lower()
        
        # Check for privacy-related terms
        privacy_terms = [
            "privacy policy", "terms of service", "terms and conditions",
            "cookie policy", "data protection", "gdpr", "ccpa",
            "personal data", "user data", "data collection",
            "consent", "opt-out", "opt-in", "unsubscribe"
        ]
        
        found_terms = []
        for term in privacy_terms:
            if term in text_lower:
                found_terms.append(term)
        
        # Analyze forms for data collection
        form_analysis = []
        sensitive_fields = ["password", "credit", "card", "ssn", "social security"]
        
        for form in forms:
            form_sensitive = False
            for input_field in form.get("inputs", []):
                field_name = input_field.get("name", "").lower()
                if any(sensitive in field_name for sensitive in sensitive_fields):
                    form_sensitive = True
                    break
            
            form_analysis.append({
                "action": form.get("action", ""),
                "method": form.get("method", ""),
                "has_sensitive_fields": form_sensitive,
                "input_count": len(form.get("inputs", []))
            })
        
        # Calculate privacy risk level (0-1)
        risk_level = 0.0
        
        # Higher risk if missing privacy terms
        missing_critical = not any(term in found_terms for term in ["privacy policy", "terms of service"])
        if missing_critical:
            risk_level += 0.3
        
        # Higher risk if forms collect sensitive data
        sensitive_forms = sum(1 for f in form_analysis if f["has_sensitive_fields"])
        if sensitive_forms > 0:
            risk_level += min(sensitive_forms * 0.2, 0.4)
        
        return {
            "found_privacy_terms": found_terms,
            "missing_terms": [t for t in ["privacy policy", "terms of service"] if t not in found_terms],
            "form_analysis": form_analysis,
            "sensitive_forms_count": sensitive_forms,
            "risk_level": min(risk_level, 1.0)
        }
    
    def _analyze_security_indicators(
        self,
        html: str,
        scripts: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Analyze security indicators in content."""
        html_lower = html.lower()
        
        # Check for security headers mentions
        security_headers = [
            "content-security-policy", "x-frame-options",
            "x-content-type-options", "strict-transport-security",
            "referrer-policy"
        ]
        
        found_headers = []
        for header in security_headers:
            if header in html_lower:
                found_headers.append(header)
        
        # Analyze scripts
        script_analysis = []
        external_scripts = 0
        insecure_scripts = 0
        
        for script in scripts:
            src = script.get("src", "")
            is_external = bool(src and not src.startswith(('data:', 'blob:')))
            is_insecure = src.startswith('http://') if src else False
            
            script_analysis.append({
                "src": src,
                "is_external": is_external,
                "is_insecure": is_insecure,
                "type": script.get("type", "")
            })
            
            if is_external:
                external_scripts += 1
            if is_insecure:
                insecure_scripts += 1
        
        # Check for common vulnerabilities indicators
        vulnerability_indicators = {
            "sql_injection": bool(re.search(r"select.*from|insert.*into|update.*set|delete.*from", html_lower, re.IGNORECASE)),
            "xss_possible": bool(re.search(r"<script>|javascript:|onclick=|onload=", html_lower, re.IGNORECASE)),
            "mixed_content": bool(re.search(r"http://.*https://", html_lower)),
            "iframe_usage": bool(re.search(r"<iframe", html_lower, re.IGNORECASE))
        }
        
        # Calculate security risk level (0-1)
        risk_level = 0.0
        
        # Higher risk for missing security headers
        if not found_headers:
            risk_level += 0.2
        
        # Higher risk for external scripts
        if external_scripts > 5:
            risk_level += min(external_scripts * 0.05, 0.3)
        
        # Higher risk for insecure scripts
        if insecure_scripts > 0:
            risk_level += min(insecure_scripts * 0.1, 0.3)
        
        # Higher risk for vulnerability indicators
        vulnerability_count = sum(1 for v in vulnerability_indicators.values() if v)
        risk_level += min(vulnerability_count * 0.1, 0.2)
        
        return {
            "found_security_headers": found_headers,
            "script_analysis": script_analysis,
            "external_scripts_count": external_scripts,
            "insecure_scripts_count": insecure_scripts,
            "vulnerability_indicators": vulnerability_indicators,
            "risk_level": min(risk_level, 1.0)
        }
    
    def _analyze_compliance_indicators(self, text: str) -> Dict[str, Any]:
        """Analyze compliance indicators in content."""
        text_lower = text.lower()
        
        # GDPR compliance indicators
        gdpr_terms = [
            "right to access", "right to erasure", "right to rectification",
            "data protection officer", "data processing agreement",
            "lawful basis", "consent", "data subject rights"
        ]
        
        gdpr_found = [term for term in gdpr_terms if term in text_lower]
        
        # CCPA compliance indicators
        ccpa_terms = [
            "do not sell my personal information", "right to know",
            "right to delete", "right to opt-out", "verifiable consumer request"
        ]
        
        ccpa_found = [term for term in ccpa_terms if term in text_lower]
        
        # Accessibility indicators (WCAG)
        accessibility_terms = [
            "accessibility", "wcag", "screen reader", "alt text",
            "keyboard navigation", "aria", "contrast ratio"
        ]
        
        accessibility_found = [term for term in accessibility_terms if term in text_lower]
        
        return {
            "gdpr_indicators": {
                "found_terms": gdpr_found,
                "missing_terms": [t for t in gdpr_terms if t not in gdpr_found],
                "coverage": len(gdpr_found) / len(gdpr_terms) if gdpr_terms else 0
            },
            "ccpa_indicators": {
                "found_terms": ccpa_found,
                "missing_terms": [t for t in ccpa_terms if t not in ccpa_found],
                "coverage": len(ccpa_found) / len(ccpa_terms) if ccpa_terms else 0
            },
            "accessibility_indicators": {
                "found_terms": accessibility_found,
                "missing_terms": [t for t in accessibility_terms if t not in accessibility_found],
                "coverage": len(accessibility_found) / len(accessibility_terms) if accessibility_terms else 0
            },
            "missing_terms": [
                term for term in gdpr_terms + ccpa_terms + accessibility_terms
                if term not in gdpr_found + ccpa_found + accessibility_found
            ]
        }
    
    def _analyze_content_structure(self, text: str) -> Dict[str, Any]:
        """Analyze content structure and quality."""
        # Basic text analysis
        words = text.split()
        sentences = re.split(r'[.!?]+', text)
        
        # Calculate readability metrics (simplified)
        avg_word_length = sum(len(word) for word in words) / len(words) if words else 0
        avg_sentence_length = len(words) / len(sentences) if sentences else 0
        
        # Check for structured content
        has_headings = bool(re.search(r'# |<h[1-6]', text))
        has_lists = bool(re.search(r'[*\-] |<li>', text))
        has_links = bool(re.search(r'https?://', text))
        
        # Content quality indicators
        quality_indicators = {
            "word_count": len(words),
            "sentence_count": len(sentences),
            "avg_word_length": round(avg_word_length, 2),
            "avg_sentence_length": round(avg_sentence_length, 2),
            "has_headings": has_headings,
            "has_lists": has_lists,
            "has_links": has_links,
            "readability_level": "technical" if avg_word_length > 6 else "standard" if avg_word_length > 4 else "simple"
        }
        
        return quality_indicators
    
    def _extract_links(self, html: str, base_url: str) -> List[str]:
        """Extract links from HTML."""
        try:
            soup = BeautifulSoup(html, 'html.parser')
            links = []
            
            for a in soup.find_all('a', href=True):
                href = a['href']
                
                # Convert relative URLs to absolute
                if href.startswith('/'):
                    parsed_base = urlparse(base_url)
                    href = f"{parsed_base.scheme}://{parsed_base.netloc}{href}"
                elif href.startswith('#'):
                    continue  # Skip anchor links
                elif not href.startswith(('http://', 'https://')):
                    continue  # Skip other non-http links
                
                # Validate URL
                parsed = urlparse(href)
                if parsed.scheme and parsed.netloc:
                    links.append(href)
            
            # Remove duplicates
            links = list(set(links))
            
            return links
            
        except Exception as e:
            logger.error(f"Failed to extract links: {e}")
            return []
    
    async def scrape_multiple(
        self,
        urls: List[str],
        parameters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Scrape multiple URLs concurrently.
        
        Args:
            urls: List of URLs to scrape
            parameters: Additional scraping parameters
            
        Returns:
            List of scraping results
        """
        if parameters is None:
            parameters = {}
        
        # Limit concurrent requests
        max_concurrent = parameters.get("max_concurrent", 5)
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def scrape_with_semaphore(url):
            async with semaphore:
                return await self.scrape(url, parameters)
        
        # Scrape all URLs concurrently
        tasks = [scrape_with_semaphore(url) for url in urls]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Failed to scrape {urls[i]}: {result}")
                processed_results.append({
                    "url": urls[i],
                    "error": str(result),
                    "success": False
                })
            else:
                processed_results.append(result)
        
        return processed_results
    
    async def analyze_site_structure(
        self,
        base_url: str,
        max_depth: int = 2,
        parameters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Analyze site structure by crawling multiple pages.
        
        Args:
            base_url: Base URL to start crawling
            max_depth: Maximum crawl depth
            parameters: Additional parameters
            
        Returns:
            Site structure analysis
        """
        if parameters is None:
            parameters = {}
        
        visited = set()
        to_visit = [(base_url, 0)]
        all_results = []
        
        while to_visit and len(visited) < self.max_pages:
            url, depth = to_visit.pop(0)
            
            if url in visited or depth > max_depth:
                continue
            
            visited.add(url)
            
            try:
                # Scrape page
                result = await self.scrape(url, parameters)
                all_results.append(result)
                
                # Add new links to visit
                if depth < max_depth:
                    new_links = result.get("links_sample", [])
                    for link in new_links:
                        if link not in visited:
                            to_visit.append((link, depth + 1))
                
            except Exception as e:
                logger.error(f"Failed to crawl {url}: {e}")
        
        # Analyze site structure
        site_analysis = {
            "base_url": base_url,
            "pages_crawled": len(all_results),
            "unique_domains": len(set(urlparse(r["url"]).netloc for r in all_results if "url" in r)),
            "average_risk_score": sum(r.get("analysis", {}).get("risk_score", 0) for r in all_results) / len(all_results) if all_results else 0,
            "page_results": all_results,
            "crawl_summary": {
                "visited_count": len(visited),
                "max_depth_reached": max_depth,
                "crawl_complete": len(visited) < self.max_pages
            }
        }
        
        return site_analysis


# Example usage
if __name__ == "__main__":
    async def test_web_scraper():
        # Initialize scraper
        async with WebScraper() as scraper:
            # Test single page scraping
            test_url = "https://example.com"
            
            try:
                result = await scraper.scrape(test_url)
                
                print(f"Scraped URL: {result['url']}")
                print(f"Success: {result['metadata']['success']}")
                print(f"Content length: {result['metadata']['content_length']}")
                print(f"Risk score: {result['analysis']['risk_score']:.2f}")
                
                # Test multiple pages
                urls = [
                    "https://httpbin.org/html",
                    "https://httpbin.org/headers"
                ]
                
                results = await scraper.scrape_multiple(urls, {"max_concurrent": 2})
                print(f"\nScraped {len(results)} pages")
                
                # Test site structure analysis
                site_analysis = await scraper.analyze_site_structure(
                    "https://httpbin.org",
                    max_depth=1
                )
                print(f"\nSite analysis: {site_analysis['pages_crawled']} pages crawled")
                
            except Exception as e:
                print(f"Error: {e}")
    
    asyncio.run(test_web_scraper())