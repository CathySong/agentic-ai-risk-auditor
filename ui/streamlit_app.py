#!/usr/bin/env python3
"""
Streamlit UI for the Agentic AI Risk Auditor.
Provides web interface for risk assessment and analysis.
"""

import streamlit as st
import asyncio
import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

from app.config import settings
from agent.graph import RiskAuditGraph
from agent.planner import AuditPlanner
from agent.executor import AuditExecutor
from tools.web_scraper import WebScraper
from tools.contract_analyzer import ContractAnalyzer
from rag.retriever import RAGRetriever, DocumentType

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class StreamlitApp:
    """Streamlit web application for AI Risk Auditor."""
    
    def __init__(self):
        self.setup_page_config()
        self.initialize_session_state()
        
    def setup_page_config(self):
        """Setup Streamlit page configuration."""
        st.set_page_config(
            page_title="Agentic AI Risk Auditor",
            page_icon="🔍",
            layout="wide",
            initial_sidebar_state="expanded"
        )
    
    def initialize_session_state(self):
        """Initialize Streamlit session state."""
        if 'audit_results' not in st.session_state:
            st.session_state.audit_results = []
        
        if 'knowledge_base_docs' not in st.session_state:
            st.session_state.knowledge_base_docs = []
        
        if 'current_audit' not in st.session_state:
            st.session_state.current_audit = None
        
        if 'rag_retriever' not in st.session_state:
            st.session_state.rag_retriever = None
        
        if 'audit_planner' not in st.session_state:
            st.session_state.audit_planner = None
        
        if 'audit_executor' not in st.session_state:
            st.session_state.audit_executor = None
    
    def run(self):
        """Run the Streamlit application."""
        # Sidebar
        self.render_sidebar()
        
        # Main content
        self.render_header()
        
        # Tab navigation
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "🏠 Dashboard",
            "🔍 Risk Audit",
            "📚 Knowledge Base",
            "📊 Analytics",
            "⚙️ Settings"
        ])
        
        with tab1:
            self.render_dashboard()
        
        with tab2:
            self.render_risk_audit()
        
        with tab3:
            self.render_knowledge_base()
        
        with tab4:
            self.render_analytics()
        
        with tab5:
            self.render_settings()
    
    def render_sidebar(self):
        """Render the sidebar."""
        with st.sidebar:
            st.title("🔍 AI Risk Auditor")
            st.markdown("---")
            
            # Quick actions
            st.subheader("Quick Actions")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("🔄 Refresh", use_container_width=True):
                    st.rerun()
            
            with col2:
                if st.button("📊 New Audit", use_container_width=True):
                    st.session_state.current_audit = None
                    st.rerun()
            
            # System status
            st.markdown("---")
            st.subheader("System Status")
            
            # Initialize components
            if st.session_state.rag_retriever is None:
                try:
                    st.session_state.rag_retriever = RAGRetriever()
                    st.success("✅ RAG Retriever initialized")
                except Exception as e:
                    st.error(f"❌ RAG Retriever failed: {e}")
            
            if st.session_state.audit_planner is None:
                try:
                    st.session_state.audit_planner = AuditPlanner()
                    st.success("✅ Audit Planner initialized")
                except Exception as e:
                    st.error(f"❌ Audit Planner failed: {e}")
            
            if st.session_state.audit_executor is None:
                try:
                    st.session_state.audit_executor = AuditExecutor()
                    st.success("✅ Audit Executor initialized")
                except Exception as e:
                    st.error(f"❌ Audit Executor failed: {e}")
            
            # Stats
            if st.session_state.rag_retriever:
                stats = st.session_state.rag_retriever.get_collection_stats()
                st.metric("📚 Documents", stats.get("total_documents", 0))
                st.metric("📊 Audits", len(st.session_state.audit_results))
            
            # About
            st.markdown("---")
            st.markdown("### About")
            st.markdown("""
            **Agentic AI Risk Auditor**
            
            Multi-agent system for automated AI risk assessment
            and compliance auditing.
            
            Version: 1.0.0
            """)
    
    def render_header(self):
        """Render the main header."""
        st.title("🔍 Agentic AI Risk Auditor")
        st.markdown("""
        **Multi-agent system for automated AI risk assessment and compliance auditing.**
        
        Assess AI systems for privacy, security, ethics, and regulatory compliance.
        """)
        
        # Quick stats row
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Audits", len(st.session_state.audit_results))
        
        with col2:
            if st.session_state.audit_results:
                avg_risk = sum(r.get("overall_risk_score", 0) for r in st.session_state.audit_results) / len(st.session_state.audit_results)
                st.metric("Avg Risk Score", f"{avg_risk:.2f}")
            else:
                st.metric("Avg Risk Score", "0.00")
        
        with col3:
            if st.session_state.rag_retriever:
                stats = st.session_state.rag_retriever.get_collection_stats()
                st.metric("Knowledge Docs", stats.get("total_documents", 0))
            else:
                st.metric("Knowledge Docs", "0")
        
        with col4:
            high_risk = sum(1 for r in st.session_state.audit_results if r.get("overall_risk_score", 0) > 0.7)
            st.metric("High Risk Audits", high_risk)
    
    def render_dashboard(self):
        """Render the dashboard tab."""
        st.header("📊 Dashboard")
        
        if not st.session_state.audit_results:
            st.info("No audit results yet. Start your first audit in the 'Risk Audit' tab.")
            return
        
        # Recent audits
        st.subheader("Recent Audits")
        recent_audits = st.session_state.audit_results[-5:]  # Last 5 audits
        
        for audit in reversed(recent_audits):
            with st.expander(f"🔍 {audit.get('target_name', 'Unknown')} - {audit.get('timestamp', '')}"):
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    risk_score = audit.get("overall_risk_score", 0)
                    risk_level = "🟢 Low" if risk_score < 0.3 else "🟡 Medium" if risk_score < 0.7 else "🔴 High"
                    st.metric("Risk Level", risk_level)
                
                with col2:
                    st.metric("Risk Score", f"{risk_score:.2f}")
                
                with col3:
                    findings = audit.get("findings", [])
                    st.metric("Findings", len(findings))
                
                # Quick summary
                st.markdown("**Summary:**")
                st.markdown(audit.get("summary", "No summary available.")[:200] + "...")
                
                if st.button("View Details", key=f"view_{audit.get('id', '')}"):
                    st.session_state.current_audit = audit
                    st.rerun()
        
        # Risk score distribution
        st.subheader("Risk Score Distribution")
        
        if len(st.session_state.audit_results) > 1:
            risk_scores = [r.get("overall_risk_score", 0) for r in st.session_state.audit_results]
            
            fig = go.Figure(data=[go.Histogram(x=risk_scores, nbinsx=10)])
            fig.update_layout(
                title="Distribution of Risk Scores",
                xaxis_title="Risk Score",
                yaxis_title="Count",
                showlegend=False
            )
            st.plotly_chart(fig, use_container_width=True)
        
        # Risk by category
        st.subheader("Risk by Category")
        
        if st.session_state.audit_results:
            categories = ["privacy", "security", "compliance", "ethics"]
            category_scores = {cat: [] for cat in categories}
            
            for audit in st.session_state.audit_results:
                analysis = audit.get("analysis", {})
                for cat in categories:
                    if cat in analysis:
                        category_scores[cat].append(analysis[cat].get("risk_score", 0))
            
            avg_scores = {cat: sum(scores)/len(scores) if scores else 0 
                         for cat, scores in category_scores.items()}
            
            df = pd.DataFrame({
                "Category": list(avg_scores.keys()),
                "Average Risk Score": list(avg_scores.values())
            })
            
            fig = px.bar(df, x="Category", y="Average Risk Score", 
                        color="Average Risk Score",
                        color_continuous_scale="RdYlGn_r")
            fig.update_layout(showlegend=False)
            st.plotly_chart(fig, use_container_width=True)
    
    def render_risk_audit(self):
        """Render the risk audit tab."""
        st.header("🔍 Risk Audit")
        
        # Audit creation form
        with st.form("audit_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                audit_type = st.selectbox(
                    "Audit Type",
                    ["Website", "API", "Mobile App", "AI Model", "Data Pipeline", "Custom"]
                )
                
                target_name = st.text_input("Target Name", placeholder="e.g., Example AI Service")
                
                target_url = st.text_input("Target URL", placeholder="https://example.com")
            
            with col2:
                audit_scope = st.multiselect(
                    "Audit Scope",
                    ["Privacy", "Security", "Compliance", "Ethics", "Performance", "Transparency"],
                    default=["Privacy", "Security", "Compliance"]
                )
                
                priority = st.select_slider(
                    "Priority",
                    options=["Low", "Medium", "High", "Critical"],
                    value="Medium"
                )
            
            # Advanced options
            with st.expander("Advanced Options"):
                col3, col4 = st.columns(2)
                
                with col3:
                    use_web_scraping = st.checkbox("Enable Web Scraping", value=True)
                    use_contract_analysis = st.checkbox("Enable Contract Analysis", value=True)
                
                with col4:
                    max_depth = st.slider("Max Scraping Depth", 1, 5, 2)
                    timeout = st.slider("Timeout (seconds)", 30, 300, 60)
            
            # Submit button
            submitted = st.form_submit_button("🚀 Start Audit", use_container_width=True)
            
            if submitted:
                if not target_name:
                    st.error("Please provide a target name.")
                else:
                    self.run_audit({
                        "audit_type": audit_type,
                        "target_name": target_name,
                        "target_url": target_url if target_url else None,
                        "audit_scope": audit_scope,
                        "priority": priority,
                        "use_web_scraping": use_web_scraping,
                        "use_contract_analysis": use_contract_analysis,
                        "max_depth": max_depth,
                        "timeout": timeout
                    })
        
        # Display current audit if exists
        if st.session_state.current_audit:
            self.render_audit_details(st.session_state.current_audit)
    
    async def _run_audit_async(self, audit_params: Dict[str, Any]) -> Dict[str, Any]:
        """Run audit asynchronously."""
        try:
            # Create audit plan
            plan = await st.session_state.audit_planner.create_plan(audit_params)
            
            # Execute audit
            results = await st.session_state.audit_executor.execute_plan(plan)
            
            # Process results through graph
            graph = RiskAuditGraph()
            final_results = await graph.process_results(results)
            
            # Add metadata
            final_results.update({
                "id": f"audit_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                "timestamp": datetime.now().isoformat(),
                "params": audit_params
            })
            
            return final_results
            
        except Exception as e:
            logger.error(f"Audit failed: {e}")
            return {
                "error": str(e),
                "id": f"audit_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                "timestamp": datetime.now().isoformat(),
                "params": audit_params
            }
    
    def run_audit(self, audit_params: Dict[str, Any]):
        """Run audit and display results."""
        with st.spinner("🚀 Running audit..."):
            # Run async audit
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                results = loop.run_until_complete(self._run_audit_async(audit_params))
                
                # Store results
                st.session_state.audit_results.append(results)
                st.session_state.current_audit = results
                
                # Display success
                st.success(f"✅ Audit completed: {results.get('target_name', 'Unknown')}")
                
                # Rerun to show results
                st.rerun()
                
            except Exception as e:
                st.error(f"❌ Audit failed: {e}")
            finally:
                loop.close()
    
    def render_audit_details(self, audit: Dict[str, Any]):
        """Render detailed audit results."""
        st.header(f"📋 Audit Results: {audit.get('target_name', 'Unknown')}")
        
        # Summary card
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            risk_score = audit.get("overall_risk_score", 0)
            st.metric("Overall Risk", f"{risk_score:.2f}")
        
        with col2:
            findings = audit.get("findings", [])
            st.metric("Total Findings", len(findings))
        
        with col3:
            high_risk = sum(1 for f in findings if f.get("risk_level") in ["high", "critical"])
            st.metric("High Risk", high_risk)
        
        with col4:
            recommendations = audit.get("recommendations", [])
            st.metric("Recommendations", len(recommendations))
        
        # Risk gauge
        st.subheader("Risk Assessment")
        
        fig = go.Figure(go.Indicator(
            mode="gauge+number",
            value=risk_score * 100,
            domain={'x': [0, 1], 'y': [0, 1]},
            title={'text': "Risk Score"},
            gauge={
                'axis': {'range': [0, 100]},
                'bar': {'color': "darkblue"},
                'steps': [
                    {'range': [0, 30], 'color': "green"},
                    {'range': [30, 70], 'color': "yellow"},
                    {'range': [70, 100], 'color': "red"}
                ],
                'threshold': {
                    'line': {'color': "black", 'width': 4},
                    'thickness': 0.75,
                    'value': risk_score * 100
                }
            }
        ))
        
        fig.update_layout(height=300)
        st.plotly_chart(fig, use_container_width=True)
        
        # Findings by category
        st.subheader("Findings by Category")
        
        if audit.get("analysis"):
            categories = list(audit["analysis"].keys())
            scores = [audit["analysis"][cat].get("risk_score", 0) for cat in categories]
            
            df = pd.DataFrame({
                "Category": categories,
                "Risk Score": scores
            })
            
            fig = px.bar(df, x="Category", y="Risk Score", 
                        color="Risk Score", color_continuous_scale="RdYlGn_r")
            st.plotly_chart(fig, use_container_width=True)
        
        # Detailed findings
        st.subheader("Detailed Findings")
        
        findings = audit.get("findings", [])
        if findings:
            for i, finding in enumerate(findings, 1):
                with st.expander(f"🔍 Finding {i}: {finding.get('title', 'Unknown')}"):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        risk_level = finding.get("risk_level", "unknown")
                        risk_color = {
                            "low": "🟢",
                            "medium": "🟡", 
                            "high": "🟠",
                            "critical": "🔴"
                        }.get(risk_level, "⚪")
                        
                        st.markdown(f"**Risk Level:** {risk_color} {risk_level.upper()}")
                        st.markdown(f"**Category:** {finding.get('category', 'Unknown')}")
                    
                    with col2:
                        st.markdown(f"**Source:** {finding.get('source', 'Unknown')}")
                        if finding.get("evidence"):
                            st.markdown(f"**Evidence:** {finding['evidence'][:100]}...")
                    
                    st.markdown("**Description:**")
                    st.markdown(finding.get("description", "No description available."))
                    
                    if finding.get("recommendations"):
                        st.markdown("**Recommendations:**")
                        for rec in finding["recommendations"]:
                            st.markdown(f"- {rec}")
        
        # Recommendations
        st.subheader("Recommendations")
        
        recommendations = audit.get("recommendations", [])
        if recommendations:
            for i, rec in enumerate(recommendations, 1):
                st.markdown(f"{i}. **{rec.get('title', 'Recommendation')}**")
                st.markdown(f"   Priority: {rec.get('priority', 'Medium')}")
                st.markdown(f"   {rec.get('description', '')}")
                st.markdown("---")
        else:
            st.info("No specific recommendations available.")
        
        # Export options
        st.subheader("Export Results")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("📄 Export as JSON", use_container_width=True):
                json_str = json.dumps(audit, indent=2, default=str)
                st.download_button(
                    label="Download JSON",
                    data=json_str,
                    file_name=f"audit_{audit.get('id', 'results')}.json",
                    mime="application/json"
                )
        
        with col2:
            if st.button("📊 Export as CSV", use_container_width=True):
                # Convert findings to CSV
                findings = audit.get("findings", [])
                if findings:
                    df = pd.DataFrame(findings)
                    csv = df.to_csv(index=False)
                    st.download_button(
                        label="Download CSV",
                        data=csv,
                        file_name=f"audit_findings_{audit.get('id', 'results')}.csv",
                        mime="text/csv"
                    )
        
        with col3:
            if st.button("📋 Copy Summary", use_container_width=True):
                summary = audit.get("summary", "No summary available.")
                st.code(summary, language="text")
    
    def render_knowledge_base(self):
        """Render the knowledge base tab."""
        st.header("📚 Knowledge Base")
        
        # Add documents section
        with st.expander("➕ Add Documents to Knowledge Base"):
            col1, col2 = st.columns([2, 1])
            
            with col1:
                doc_text = st.text_area(
                    "Document Text",
                    height=200,
                    placeholder="Paste document text here..."
                )
            
            with col2:
                doc_type = st.selectbox(
                    "Document Type",
                    [dt.value for dt in DocumentType]
                )
                
                source = st.text_input("Source", placeholder="e.g., GDPR Article 5")
                
                tags = st.text_input("Tags (comma-separated)", placeholder="privacy, compliance, eu")
            
            if st.button("Add Document", use_container_width=True):
                if doc_text and doc_type:
                    document = {
                        "text": doc_text,
                        "metadata": {
                            "document_type": doc_type,
                            "source": source,
                            "tags": [tag.strip() for tag in tags.split(",")] if tags else [],
                            "added_by": "streamlit_ui",
                            "added_at": datetime.now().isoformat()
                        }
                    }
                    
                    if st.session_state.rag_retriever:
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                        
                        try:
                            result = loop.run_until_complete(
                                st.session_state.rag_retriever.add_documents([document])
                            )
                            st.success(f"✅ Added {result['added']} document(s)")
                            st.rerun()
                        except Exception as e:
                            st.error(f"❌ Failed to add document: {e}")
                        finally:
                            loop.close()
                    else:
                        st.error("RAG retriever not initialized")
        
        # Search knowledge base
        st.subheader("🔍 Search Knowledge Base")
        
        search_query = st.text_input("Search query", placeholder="Enter search terms...")
        
        col1, col2 = st.columns(2)
        
        with col1:
            n_results = st.slider("Results limit", 1, 20, 5)
        
        with col2:
            doc_type_filter = st.multiselect(
                "Filter by type",
                [dt.value for dt in DocumentType],
                default=[]
            )
        
        if st.button("Search", use_container_width=True) and search_query:
            if st.session_state.rag_retriever:
                # Prepare search parameters
                params = {"n_results": n_results}
                
                if doc_type_filter:
                    params["where_filter"] = {
                        "document_type": {"$in": doc_type_filter}
                    }
                
                # Run search
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
                try:
                    with st.spinner("Searching..."):
                        result = loop.run_until_complete(
                            st.session_state.rag_retriever.search(search_query, params)
                        )
                    
                    # Display results
                    st.subheader(f"Search Results ({result.total_results})")
                    
                    for i, doc in enumerate(result.documents, 1):
                        with st.expander(f"📄 Result {i}: Score {doc.score:.3f}"):
                            st.markdown(f"**Type:** {doc.metadata.get('document_type', 'Unknown')}")
                            st.markdown(f"**Source:** {doc.metadata.get('source', 'Unknown')}")
                            st.markdown(f"**Added:** {doc.metadata.get('added_at', 'Unknown')}")
                            
                            st.markdown("**Content:**")
                            st.markdown(doc.text)
                            
                            if doc.metadata.get("tags"):
                                st.markdown("**Tags:** " + ", ".join(doc.metadata["tags"]))
                    
                except Exception as e:
                    st.error(f"❌ Search failed: {e}")
                finally:
                    loop.close()
            else:
                st.error("RAG retriever not initialized")
        
        # Knowledge base statistics
        st.subheader("📊 Knowledge Base Statistics")
        
        if st.session_state.rag_retriever:
            stats = st.session_state.rag_retriever.get_collection_stats()
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Total Documents", stats.get("total_documents", 0))
            
            with col2:
                st.metric("Storage Type", stats.get("storage_type", "Unknown"))
            
            with col3:
                st.metric("Embedding Dim", stats.get("embedding_dimension", 0))
            
            # Document type distribution
            doc_types = stats.get("document_types", {})
            if doc_types:
                df = pd.DataFrame({
                    "Document Type": list(doc_types.keys()),
                    "Count": list(doc_types.values())
                })
                
                fig = px.pie(df, values="Count", names="Document Type", 
                            title="Document Type Distribution")
                st.plotly_chart(fig, use_container_width=True)
    
    def render_analytics(self):
        """Render the analytics tab."""
        st.header("📊 Analytics")
        
        if not st.session_state.audit_results:
            st.info("No audit data available for analytics.")
            return
        
        # Convert audit results to DataFrame
        audits_df = pd.DataFrame(st.session_state.audit_results)
        
        # Time series of risk scores
        st.subheader("Risk Score Trends")
        
        if "timestamp" in audits_df.columns:
            audits_df["timestamp"] = pd.to_datetime(audits_df["timestamp"])
            audits_df = audits_df.sort_values("timestamp")
            
            fig = px.line(audits_df, x="timestamp", y="overall_risk_score",
                         title="Risk Score Over Time",
                         markers=True)
            st.plotly_chart(fig, use_container_width=True)
        
        # Risk score distribution
        st.subheader("Risk Score Distribution")
        
        fig = px.histogram(audits_df, x="overall_risk_score", 
                          nbins=10, title="Distribution of Risk Scores")
        st.plotly_chart(fig, use_container_width=True)
        
        # Audit type analysis
        st.subheader("Audit Type Analysis")
        
        if "params" in audits_df.columns:
            # Extract audit types
            audit_types = []
            for params in audits_df["params"]:
                if isinstance(params, dict):
                    audit_types.append(params.get("audit_type", "Unknown"))
                else:
                    audit_types.append("Unknown")
            
            type_counts = pd.Series(audit_types).value_counts()
            
            fig = px.bar(x=type_counts.index, y=type_counts.values,
                        title="Audits by Type",
                        labels={"x": "Audit Type", "y": "Count"})
            st.plotly_chart(fig, use_container_width=True)
        
        # Risk heatmap by category
        st.subheader("Risk Heatmap by Category")
        
        # Extract category scores
        categories = ["privacy", "security", "compliance", "ethics"]
        category_data = []
        
        for audit in st.session_state.audit_results:
            analysis = audit.get("analysis", {})
            for cat in categories:
                if cat in analysis:
                    category_data.append({
                        "audit": audit.get("target_name", "Unknown"),
                        "category": cat,
                        "score": analysis[cat].get("risk_score", 0)
                    })
        
        if category_data:
            heatmap_df = pd.DataFrame(category_data)
            pivot_df = heatmap_df.pivot(index="audit", columns="category", values="score")
            
            fig = px.imshow(pivot_df, color_continuous_scale="RdYlGn_r",
                           title="Risk Scores by Audit and Category")
            st.plotly_chart(fig, use_container_width=True)
    
    def render_settings(self):
        """Render the settings tab."""
        st.header("⚙️ Settings")
        
        # Model settings
        st.subheader("Model Settings")
        
        col1, col2 = st.columns(2)
        
        with col1:
            llm_provider = st.selectbox(
                "LLM Provider",
                ["openai", "anthropic", "google", "cohere"],
                index=0
            )
        
        with col2:
            embedding_model = st.selectbox(
                "Embedding Model",
                ["text-embedding-3-small", "text-embedding-3-large", "all-MiniLM-L6-v2"],
                index=0
            )
        
        # Vector database settings
        st.subheader("Vector Database")
        
        chroma_path = st.text_input(
            "ChromaDB Path",
            value=settings.vectordb.chroma_db_path,
            help="Path to store ChromaDB database"
        )
        
        collection_name = st.text_input(
            "Collection Name",
            value=settings.vectordb.default_collection,
            help="Name of the document collection"
        )
        
        # Search settings
        st.subheader("Search Settings")
        
        col3, col4 = st.columns(2)
        
        with col3:
            search_limit = st.slider(
                "Search Results Limit",
                min_value=1,
                max_value=50,
                value=settings.vectordb.search_results_limit
            )
        
        with col4:
            context_size = st.slider(
                "Context Size Limit (tokens)",
                min_value=100,
                max_value=10000,
                value=settings.vectordb.context_size_limit,
                step=100
            )
        
        # System settings
        st.subheader("System Settings")
        
        debug_mode = st.checkbox("Enable Debug Mode", value=False)
        log_level = st.selectbox(
            "Log Level",
            ["DEBUG", "INFO", "WARNING", "ERROR"],
            index=1
        )
        
        # Save settings
        if st.button("💾 Save Settings", use_container_width=True):
            # Note: In a real app, these would be saved to a config file
            st.success("Settings saved (note: requires app restart to take effect)")
            
            # Display settings summary
            st.info(f"""
            **Settings Summary:**
            - LLM Provider: {llm_provider}
            - Embedding Model: {embedding_model}
            - ChromaDB Path: {chroma_path}
            - Collection: {collection_name}
            - Search Limit: {search_limit}
            - Context Size: {context_size}
            - Debug Mode: {debug_mode}
            - Log Level: {log_level}
            """)
        
        # System actions
        st.subheader("System Actions")
        
        col5, col6 = st.columns(2)
        
        with col5:
            if st.button("🔄 Reset Knowledge Base", use_container_width=True):
                if st.session_state.rag_retriever:
                    result = st.session_state.rag_retriever.reset_collection()
                    if result.get("reset"):
                        st.success("✅ Knowledge base reset")
                        st.rerun()
                    else:
                        st.error(f"❌ Failed to reset: {result.get('error')}")
                else:
                    st.error("RAG retriever not initialized")
        
        with col6:
            if st.button("🗑️ Clear Audit History", use_container_width=True):
                st.session_state.audit_results = []
                st.session_state.current_audit = None
                st.success("✅ Audit history cleared")
                st.rerun()


def main():
    """Main entry point for Streamlit app."""
    app = StreamlitApp()
    app.run()


if __name__ == "__main__":
    main()
