"""
Resume Analytics and Insights module for Resume Customizer application.
Provides performance tracking, content analysis, and optimization suggestions.
"""

import re
import statistics
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from collections import Counter, defaultdict
import streamlit as st

from logger import get_logger
from audit_logger import audit_logger

logger = get_logger()


@dataclass
class ResumeMetrics:
    """Comprehensive resume metrics."""
    file_name: str
    word_count: int
    paragraph_count: int
    bullet_points: int
    tech_keywords: int
    action_verbs: int
    experience_sections: int
    readability_score: float
    tech_diversity_score: float
    impact_score: float
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class ProcessingStats:
    """Processing performance statistics."""
    file_name: str
    processing_time: float
    points_added: int
    tech_stacks_used: List[str]
    success: bool
    errors: List[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)


class ContentAnalyzer:
    """Analyze resume content for quality and optimization opportunities."""
    
    # Strong action verbs for resumes
    STRONG_ACTION_VERBS = {
        'achieved', 'analyzed', 'architected', 'automated', 'built', 'created', 
        'delivered', 'deployed', 'designed', 'developed', 'enhanced', 'established',
        'executed', 'implemented', 'improved', 'increased', 'launched', 'led',
        'managed', 'optimized', 'orchestrated', 'reduced', 'solved', 'streamlined'
    }
    
    # Weak words to avoid
    WEAK_WORDS = {
        'responsible for', 'duties included', 'worked on', 'helped with',
        'participated in', 'involved in', 'assisted with', 'contributed to'
    }
    
    # Technology keywords for scoring
    TECH_CATEGORIES = {
        'programming': ['python', 'javascript', 'java', 'c++', 'c#', 'go', 'rust', 'swift'],
        'web': ['html', 'css', 'react', 'angular', 'vue', 'node.js', 'django', 'flask'],
        'databases': ['sql', 'mongodb', 'postgresql', 'mysql', 'redis', 'elasticsearch'],
        'cloud': ['aws', 'azure', 'gcp', 'docker', 'kubernetes', 'terraform'],
        'data': ['pandas', 'numpy', 'tensorflow', 'pytorch', 'spark', 'hadoop'],
        'tools': ['git', 'jenkins', 'jira', 'confluence', 'slack', 'figma']
    }
    
    def analyze_content(self, content: str) -> ResumeMetrics:
        """Analyze resume content comprehensively."""
        words = content.split()
        paragraphs = content.split('\n\n')
        
        # Basic counts
        word_count = len(words)
        paragraph_count = len([p for p in paragraphs if p.strip()])
        bullet_points = len(re.findall(r'[•\-\*]\s+', content))
        
        # Content analysis
        tech_keywords = self._count_tech_keywords(content.lower())
        action_verbs = self._count_action_verbs(content.lower())
        experience_sections = self._count_experience_sections(content)
        
        # Quality scores
        readability_score = self._calculate_readability_score(content)
        tech_diversity_score = self._calculate_tech_diversity_score(content.lower())
        impact_score = self._calculate_impact_score(content.lower())
        
        return ResumeMetrics(
            file_name="",  # Will be set by caller
            word_count=word_count,
            paragraph_count=paragraph_count,
            bullet_points=bullet_points,
            tech_keywords=tech_keywords,
            action_verbs=action_verbs,
            experience_sections=experience_sections,
            readability_score=readability_score,
            tech_diversity_score=tech_diversity_score,
            impact_score=impact_score
        )
    
    def _count_tech_keywords(self, content: str) -> int:
        """Count technology-related keywords."""
        count = 0
        for category, keywords in self.TECH_CATEGORIES.items():
            for keyword in keywords:
                count += len(re.findall(r'\b' + keyword.replace('.', r'\.') + r'\b', content))
        return count
    
    def _count_action_verbs(self, content: str) -> int:
        """Count strong action verbs."""
        count = 0
        for verb in self.STRONG_ACTION_VERBS:
            count += len(re.findall(r'\b' + verb + r'(?:ed|ing|s)?\b', content))
        return count
    
    def _count_experience_sections(self, content: str) -> int:
        """Count professional experience sections."""
        experience_indicators = [
            r'experience', r'employment', r'work history', r'professional',
            r'software engineer', r'developer', r'analyst', r'manager'
        ]
        
        count = 0
        for indicator in experience_indicators:
            count += len(re.findall(indicator, content, re.IGNORECASE))
        
        return min(count, 10)  # Cap at reasonable number
    
    def _calculate_readability_score(self, content: str) -> float:
        """Calculate readability score (0-100, higher is better)."""
        sentences = re.split(r'[.!?]+', content)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        if not sentences:
            return 0.0
        
        words = content.split()
        avg_sentence_length = len(words) / len(sentences) if sentences else 0
        
        # Simple readability metric (inverse of average sentence length)
        # Optimal sentence length for resumes is 15-20 words
        optimal_length = 17
        score = max(0, 100 - abs(avg_sentence_length - optimal_length) * 2)
        
        return min(100, score)
    
    def _calculate_tech_diversity_score(self, content: str) -> float:
        """Calculate technology diversity score (0-100)."""
        categories_found = 0
        total_categories = len(self.TECH_CATEGORIES)
        
        for category, keywords in self.TECH_CATEGORIES.items():
            if any(keyword in content for keyword in keywords):
                categories_found += 1
        
        return (categories_found / total_categories) * 100
    
    def _calculate_impact_score(self, content: str) -> float:
        """Calculate impact score based on quantifiable achievements."""
        # Look for numbers and percentages
        numbers = re.findall(r'\d+(?:\.\d+)?%?', content)
        
        # Look for impact indicators
        impact_words = [
            'increased', 'decreased', 'reduced', 'improved', 'optimized',
            'saved', 'generated', 'achieved', 'exceeded', 'delivered'
        ]
        
        impact_mentions = sum(len(re.findall(r'\b' + word + r'\b', content)) 
                            for word in impact_words)
        
        # Score based on quantifiable achievements
        quantified_achievements = len([n for n in numbers if '%' in n or int(re.findall(r'\d+', n)[0]) > 10])
        
        # Combine metrics
        base_score = min(quantified_achievements * 15, 60)  # Up to 60 points for numbers
        impact_score = min(impact_mentions * 5, 40)  # Up to 40 points for impact words
        
        return min(100, base_score + impact_score)


class PerformanceTracker:
    """Track processing performance and generate insights."""
    
    def __init__(self):
        if 'processing_history' not in st.session_state:
            st.session_state.processing_history = []
    
    def record_processing(self, stats: ProcessingStats):
        """Record processing statistics."""
        st.session_state.processing_history.append(stats)
        
        # Keep only last 100 entries for performance
        if len(st.session_state.processing_history) > 100:
            st.session_state.processing_history = st.session_state.processing_history[-100:]
        
        # Audit log successful processing
        if stats.success:
            audit_logger.log(
                action="resume_processed",
                details={
                    "file_name": stats.file_name,
                    "processing_time": stats.processing_time,
                    "points_added": stats.points_added,
                    "tech_stacks": len(stats.tech_stacks_used)
                },
                status="success"
            )
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get performance summary statistics."""
        if not st.session_state.processing_history:
            return {"message": "No processing history available"}
        
        history = st.session_state.processing_history
        successful_runs = [h for h in history if h.success]
        
        if not successful_runs:
            return {"message": "No successful processing runs found"}
        
        processing_times = [h.processing_time for h in successful_runs]
        points_added = [h.points_added for h in successful_runs]
        
        return {
            "total_resumes_processed": len(successful_runs),
            "success_rate": len(successful_runs) / len(history) * 100,
            "avg_processing_time": statistics.mean(processing_times),
            "median_processing_time": statistics.median(processing_times),
            "avg_points_added": statistics.mean(points_added),
            "total_points_added": sum(points_added),
            "fastest_processing": min(processing_times),
            "slowest_processing": max(processing_times),
            "most_recent": history[-1].timestamp if history else None
        }
    
    def get_tech_stack_insights(self) -> Dict[str, Any]:
        """Get insights about tech stack usage."""
        if not st.session_state.processing_history:
            return {}
        
        all_tech_stacks = []
        for entry in st.session_state.processing_history:
            if entry.success:
                all_tech_stacks.extend(entry.tech_stacks_used)
        
        if not all_tech_stacks:
            return {}
        
        tech_counter = Counter(all_tech_stacks)
        
        return {
            "most_popular_technologies": tech_counter.most_common(10),
            "total_unique_technologies": len(tech_counter),
            "avg_technologies_per_resume": len(all_tech_stacks) / len([h for h in st.session_state.processing_history if h.success])
        }


class OptimizationSuggester:
    """Suggest optimizations based on analytics."""
    
    def __init__(self):
        self.analyzer = ContentAnalyzer()
    
    def analyze_and_suggest(self, content: str, metrics: Optional[ResumeMetrics] = None) -> Dict[str, Any]:
        """Analyze content and provide optimization suggestions."""
        if metrics is None:
            metrics = self.analyzer.analyze_content(content)
        
        suggestions = {
            "critical": [],
            "important": [],
            "minor": [],
            "praise": []
        }
        
        # Content length analysis
        if metrics.word_count < 300:
            suggestions["critical"].append(
                "Resume is too short. Add more details about your experience and achievements."
            )
        elif metrics.word_count > 800:
            suggestions["important"].append(
                "Resume might be too long. Consider condensing to 1-2 pages."
            )
        
        # Bullet points
        if metrics.bullet_points < 5:
            suggestions["important"].append(
                "Add more bullet points to highlight your achievements and responsibilities."
            )
        elif metrics.bullet_points > 20:
            suggestions["minor"].append(
                "Consider condensing bullet points to focus on most impactful achievements."
            )
        
        # Technical keywords
        if metrics.tech_keywords < 5:
            suggestions["important"].append(
                "Include more technical keywords relevant to your target positions."
            )
        elif metrics.tech_keywords > 30:
            suggestions["praise"].append(
                "Great technical keyword coverage! Your resume should be easily found by ATS systems."
            )
        
        # Action verbs
        if metrics.action_verbs < 3:
            suggestions["critical"].append(
                "Use more strong action verbs (achieved, developed, implemented, etc.) to describe your accomplishments."
            )
        elif metrics.action_verbs > 10:
            suggestions["praise"].append(
                "Excellent use of strong action verbs to showcase your contributions!"
            )
        
        # Readability
        if metrics.readability_score < 60:
            suggestions["important"].append(
                "Improve readability by using shorter sentences and clearer language."
            )
        elif metrics.readability_score > 85:
            suggestions["praise"].append(
                "Great readability! Your resume is easy to scan and understand."
            )
        
        # Technology diversity
        if metrics.tech_diversity_score < 30:
            suggestions["minor"].append(
                "Consider mentioning a broader range of technologies if relevant to your experience."
            )
        elif metrics.tech_diversity_score > 70:
            suggestions["praise"].append(
                "Excellent technology diversity! You demonstrate versatility across different tech stacks."
            )
        
        # Impact score
        if metrics.impact_score < 40:
            suggestions["critical"].append(
                "Add more quantifiable achievements with specific numbers and percentages."
            )
        elif metrics.impact_score > 75:
            suggestions["praise"].append(
                "Outstanding impact demonstration! Your quantified achievements stand out."
            )
        
        return {
            "suggestions": suggestions,
            "overall_score": self._calculate_overall_score(metrics),
            "metrics": metrics
        }
    
    def _calculate_overall_score(self, metrics: ResumeMetrics) -> float:
        """Calculate overall resume quality score (0-100)."""
        scores = [
            metrics.readability_score * 0.2,  # 20% weight
            metrics.tech_diversity_score * 0.15,  # 15% weight
            metrics.impact_score * 0.25,  # 25% weight
            min(metrics.action_verbs * 10, 100) * 0.15,  # 15% weight
            min(metrics.bullet_points * 5, 100) * 0.1,  # 10% weight
            min(metrics.tech_keywords * 3, 100) * 0.15  # 15% weight
        ]
        
        return sum(scores)


# Streamlit UI Components for Analytics
def render_analytics_dashboard():
    """Render the analytics dashboard in Streamlit."""
    st.header("📊 Resume Analytics Dashboard")
    
    tracker = PerformanceTracker()
    analyzer = ContentAnalyzer()
    suggester = OptimizationSuggester()
    
    # Performance Summary
    st.subheader("⚡ Performance Summary")
    perf_summary = tracker.get_performance_summary()
    
    if "message" in perf_summary:
        st.info(perf_summary["message"])
    else:
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Processed", perf_summary["total_resumes_processed"])
        with col2:
            st.metric("Success Rate", f"{perf_summary['success_rate']:.1f}%")
        with col3:
            st.metric("Avg Processing Time", f"{perf_summary['avg_processing_time']:.2f}s")
        with col4:
            st.metric("Total Points Added", perf_summary["total_points_added"])
    
    # Tech Stack Insights
    st.subheader("🔧 Technology Insights")
    tech_insights = tracker.get_tech_stack_insights()
    
    if tech_insights:
        st.write("**Most Popular Technologies:**")
        for tech, count in tech_insights["most_popular_technologies"][:5]:
            st.write(f"• {tech}: {count} uses")
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Unique Technologies", tech_insights["total_unique_technologies"])
        with col2:
            st.metric("Avg per Resume", f"{tech_insights['avg_technologies_per_resume']:.1f}")
    
    # Resume Analysis Tool
    st.subheader("🔍 Resume Content Analyzer")
    
    uploaded_file = st.file_uploader("Upload a resume for detailed analysis", type=['txt'])
    if uploaded_file:
        content = uploaded_file.read().decode('utf-8')
        
        with st.spinner("Analyzing resume content..."):
            analysis = suggester.analyze_and_suggest(content)
        
        # Overall Score
        score = analysis["overall_score"]
        st.metric("Overall Quality Score", f"{score:.1f}/100")
        
        # Progress bar for score
        if score >= 80:
            st.success(f"Excellent resume quality! ({score:.1f}/100)")
        elif score >= 60:
            st.warning(f"Good resume, with room for improvement. ({score:.1f}/100)")
        else:
            st.error(f"Resume needs significant improvement. ({score:.1f}/100)")
        
        # Suggestions
        suggestions = analysis["suggestions"]
        
        if suggestions["critical"]:
            st.error("🚨 Critical Issues:")
            for suggestion in suggestions["critical"]:
                st.error(f"• {suggestion}")
        
        if suggestions["important"]:
            st.warning("⚠️ Important Improvements:")
            for suggestion in suggestions["important"]:
                st.warning(f"• {suggestion}")
        
        if suggestions["minor"]:
            st.info("💡 Minor Suggestions:")
            for suggestion in suggestions["minor"]:
                st.info(f"• {suggestion}")
        
        if suggestions["praise"]:
            st.success("🎉 Great Work:")
            for praise in suggestions["praise"]:
                st.success(f"• {praise}")
        
        # Detailed Metrics
        with st.expander("📈 Detailed Metrics"):
            metrics = analysis["metrics"]
            
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Word Count", metrics.word_count)
                st.metric("Bullet Points", metrics.bullet_points)
                st.metric("Tech Keywords", metrics.tech_keywords)
                st.metric("Action Verbs", metrics.action_verbs)
            
            with col2:
                st.metric("Readability Score", f"{metrics.readability_score:.1f}")
                st.metric("Tech Diversity", f"{metrics.tech_diversity_score:.1f}")
                st.metric("Impact Score", f"{metrics.impact_score:.1f}")
                st.metric("Experience Sections", metrics.experience_sections)


# Global instances
_performance_tracker = None
_content_analyzer = None
_optimization_suggester = None

def get_performance_tracker() -> PerformanceTracker:
    """Get singleton performance tracker."""
    global _performance_tracker
    if _performance_tracker is None:
        _performance_tracker = PerformanceTracker()
    return _performance_tracker

def get_content_analyzer() -> ContentAnalyzer:
    """Get singleton content analyzer."""
    global _content_analyzer
    if _content_analyzer is None:
        _content_analyzer = ContentAnalyzer()
    return _content_analyzer

def get_optimization_suggester() -> OptimizationSuggester:
    """Get singleton optimization suggester."""
    global _optimization_suggester
    if _optimization_suggester is None:
        _optimization_suggester = OptimizationSuggester()
    return _optimization_suggester
