"""
Document processing module for Resume Customizer application.
Handles Word document manipulation, project detection, and formatting.
"""

import gc
import threading
from typing import List, Tuple, Dict, Any, Optional
from io import BytesIO
from docx import Document

from config import DOC_CONFIG, PARSING_CONFIG
from logger import get_logger

logger = get_logger()


class DocumentFormatter:
    """Handles document formatting operations."""
    
    @staticmethod
    def copy_paragraph_formatting(source_para, target_para) -> None:
        """
        Copy all formatting from source paragraph to target paragraph with error handling.
        
        Args:
            source_para: Source paragraph to copy formatting from
            target_para: Target paragraph to apply formatting to
        """
        try:
            # Copy paragraph style
            if source_para.style:
                target_para.style = source_para.style
            
            # Copy paragraph alignment
            if source_para.paragraph_format.alignment is not None:
                target_para.paragraph_format.alignment = source_para.paragraph_format.alignment
            
            # Copy paragraph spacing
            if source_para.paragraph_format.space_before is not None:
                target_para.paragraph_format.space_before = source_para.paragraph_format.space_before
            if source_para.paragraph_format.space_after is not None:
                target_para.paragraph_format.space_after = source_para.paragraph_format.space_after
            if source_para.paragraph_format.line_spacing is not None:
                target_para.paragraph_format.line_spacing = source_para.paragraph_format.line_spacing
            
            # Copy indentation
            if source_para.paragraph_format.left_indent is not None:
                target_para.paragraph_format.left_indent = source_para.paragraph_format.left_indent
            if source_para.paragraph_format.first_line_indent is not None:
                target_para.paragraph_format.first_line_indent = source_para.paragraph_format.first_line_indent
        except Exception:
            # Continue if formatting fails - don't let it break the entire process
            pass
    
    @staticmethod
    def copy_run_formatting(source_run, target_run) -> None:
        """
        Copy all formatting from source run to target run.
        
        Args:
            source_run: Source run to copy formatting from
            target_run: Target run to apply formatting to
        """
        try:
            # Copy font properties
            target_run.font.name = source_run.font.name
            target_run.font.size = source_run.font.size
            target_run.font.bold = source_run.font.bold
            target_run.font.italic = source_run.font.italic
            target_run.font.underline = source_run.font.underline
            
            # Copy font color
            if source_run.font.color.rgb:
                target_run.font.color.rgb = source_run.font.color.rgb
            
            # Copy highlighting
            if hasattr(source_run.font, 'highlight_color') and source_run.font.highlight_color:
                target_run.font.highlight_color = source_run.font.highlight_color
        except Exception:
            # Continue if formatting fails
            pass


class BulletFormatter:
    """Handles bullet point formatting and style preservation."""
    
    def __init__(self):
        self.bullet_markers = DOC_CONFIG["bullet_markers"]
    
    def get_bullet_formatting(self, doc: Document, paragraph_index: int) -> Optional[Dict[str, Any]]:
        """Extract complete bullet formatting from a paragraph."""
        if paragraph_index >= len(doc.paragraphs):
            return None
            
        para = doc.paragraphs[paragraph_index]
        if not self._is_bullet_point(para.text):
            return None
            
        # Get comprehensive formatting from all runs
        formatting_info = {
            'runs_formatting': [],
            'paragraph_formatting': {},
            'style': para.style,
            'bullet_marker': self._extract_bullet_marker(para.text)
        }
        
        # Extract formatting from each run
        for run in para.runs:
            run_format = {
                'text': run.text,
                'font_name': run.font.name,
                'font_size': run.font.size,
                'bold': run.font.bold,
                'italic': run.font.italic,
                'underline': run.font.underline,
                'color': run.font.color.rgb if run.font.color.rgb else None
            }
            formatting_info['runs_formatting'].append(run_format)
        
        # Extract paragraph-level formatting
        pf = para.paragraph_format
        formatting_info['paragraph_formatting'] = {
            'alignment': pf.alignment,
            'left_indent': pf.left_indent,
            'right_indent': pf.right_indent,
            'first_line_indent': pf.first_line_indent,
            'space_before': pf.space_before,
            'space_after': pf.space_after,
            'line_spacing': pf.line_spacing
        }
        
        return formatting_info
    
    def _is_bullet_point(self, text: str) -> bool:
        """Check if text starts with a bullet point marker."""
        text = text.strip()
        return (
            any(text.startswith(marker) for marker in self.bullet_markers) or
            (text and text[0].isdigit() and '.' in text[:3])
        )
    
    def _extract_bullet_marker(self, text: str) -> str:
        """Extract the bullet marker from text."""
        text = text.strip()
        for marker in self.bullet_markers:
            if text.startswith(marker):
                return marker
        if text and text[0].isdigit():
            for i, char in enumerate(text):
                if char in '.)': 
                    return text[:i+1]
        return '-'
    
    def apply_bullet_formatting(self, paragraph, formatting: Dict[str, Any], text: str, fallback_formatting: Dict[str, Any] = None) -> None:
        """
        Apply extracted formatting to a new bullet point paragraph with exact matching.
        
        Args:
            paragraph: Paragraph to format
            formatting: Formatting dictionary from get_bullet_formatting
            text: Text content to add
        """
        try:
            # Use fallback formatting if main formatting is missing or incomplete
            if not formatting and fallback_formatting:
                formatting = fallback_formatting

            # Apply paragraph style first (this sets base formatting)
            if formatting and formatting.get('style'):
                try:
                    paragraph.style = formatting['style']
                except Exception:
                    pass

            # Apply comprehensive paragraph formatting
            pf_data = formatting.get('paragraph_format', {}) if formatting else {}
            pf = paragraph.paragraph_format
            for attr, value in pf_data.items():
                if value is not None:
                    try:
                        setattr(pf, attr, value)
                    except Exception:
                        continue

            # Clear existing runs and add formatted text
            marker = formatting.get('bullet_marker', '-') if formatting else '-'
            paragraph.clear()
            run = paragraph.add_run(f"{marker} {text}")

            # Apply comprehensive run formatting
            rf_data = formatting.get('run_format', {}) if formatting else {}
            for attr, value in rf_data.items():
                if value is not None:
                    try:
                        if attr == 'color' and value:
                            run.font.color.rgb = value
                        elif attr == 'highlight_color' and value:
                            run.font.highlight_color = value
                        else:
                            setattr(run.font, attr, value)
                    except Exception:
                        continue

        except Exception as e:
            # Fallback: use fallback formatting if available
            paragraph.clear()
            marker = formatting.get('bullet_marker', '-') if formatting else '-'
            paragraph.add_run(f"{marker} {text}")


class BulletPointProcessor:
    """Handles bullet point detection and formatting."""
    
    def __init__(self):
        self.bullet_markers = DOC_CONFIG["bullet_markers"]
    
    def is_bullet_point(self, text: str) -> bool:
        """
        Check if text starts with a bullet point marker.
        
        Args:
            text: Text to check
            
        Returns:
            True if text starts with a bullet point marker
        """
        text = text.strip()
        return (
            any(text.startswith(marker) for marker in self.bullet_markers) or
            (text and text[0].isdigit() and '.' in text[:3])
        )
    
    def get_bullet_formatting(self, doc: Document, paragraph_index: int) -> Optional[Dict[str, Any]]:
        """
        Extract complete bullet formatting from a paragraph with enhanced detection.
        
        Args:
            doc: Document containing the paragraph
            paragraph_index: Index of the paragraph
            
        Returns:
            Dictionary containing comprehensive formatting information or None
        """
        if paragraph_index >= len(doc.paragraphs):
            return None
            
        para = doc.paragraphs[paragraph_index]
        if not self.is_bullet_point(para.text):
            return None
            
        # Get comprehensive formatting from all runs to handle mixed formatting
        formatting_info = {
            'runs_formatting': [],
            'paragraph_formatting': {},
            'style': para.style,
            'bullet_marker': self._extract_bullet_marker(para.text)
        }
        
        # Extract formatting from each run
        for run in para.runs:
            run_format = {
                'text': run.text,
                'font_name': run.font.name,
                'font_size': run.font.size,
                'bold': run.font.bold,
                'italic': run.font.italic,
                'underline': run.font.underline,
                'color': run.font.color.rgb if run.font.color.rgb else None,
                'subscript': run.font.subscript,
                'superscript': run.font.superscript,
                'strike': run.font.strike,
                'shadow': run.font.shadow,
                'small_caps': run.font.small_caps,
                'all_caps': run.font.all_caps
            }
            formatting_info['runs_formatting'].append(run_format)
        
        # Extract paragraph-level formatting
        pf = para.paragraph_format
        formatting_info['paragraph_formatting'] = {
            'alignment': pf.alignment,
            'left_indent': pf.left_indent,
            'right_indent': pf.right_indent,
            'first_line_indent': pf.first_line_indent,
            'space_before': pf.space_before,
            'space_after': pf.space_after,
            'line_spacing': pf.line_spacing,
            'line_spacing_rule': pf.line_spacing_rule,
            'widow_control': pf.widow_control,
            'keep_together': pf.keep_together,
            'keep_with_next': pf.keep_with_next,
            'page_break_before': pf.page_break_before
        }
        
        return formatting_info
    
    def _extract_bullet_marker(self, text: str) -> str:
        """
        Extract the bullet marker from text.
        
        Args:
            text: Text to extract bullet marker from
            
        Returns:
            The bullet marker character or pattern
        """
        text = text.strip()
        
        # Check for common bullet markers
        for marker in self.bullet_markers:
            if text.startswith(marker):
                return marker
        
        # Check for numbered bullets (1., 2., etc.)
        if text and text[0].isdigit():
            for i, char in enumerate(text):
                if char in '.)':
                    return text[:i+1]
        
        # Default bullet marker
        return '-'
    
    def apply_bullet_formatting(self, paragraph, formatting: Dict[str, Any], text: str) -> None:
        """
        Apply complete formatting to a new bullet point with perfect style matching.
        
        Args:
            paragraph: Target paragraph
            formatting: Comprehensive formatting dictionary
            text: Text to add
        """
        if not formatting:
            return
            
        # Clear existing content
        paragraph.clear()
        
        # Apply paragraph-level formatting first
        self._apply_paragraph_formatting(paragraph, formatting.get('paragraph_formatting', {}))
        
        # Apply paragraph style
        if formatting.get('style'):
            try:
                paragraph.style = formatting['style']
            except Exception:
                pass
        
        # Create bullet point with proper marker
        bullet_marker = formatting.get('bullet_marker', '-')
        full_text = f"{bullet_marker} {text.lstrip('-•* ')}"
        
        # Apply run-level formatting based on the original formatting
        runs_formatting = formatting.get('runs_formatting', [])
        
        if runs_formatting:
            # Use the formatting from the first meaningful run (usually the bullet content)
            primary_format = runs_formatting[0]
            if len(runs_formatting) > 1:
                # If there are multiple runs, use the one with actual content (not just the bullet)
                for run_format in runs_formatting:
                    if run_format['text'].strip() and not any(marker in run_format['text'] for marker in self.bullet_markers):
                        primary_format = run_format
                        break
            
            # Create run with formatted text
            run = paragraph.add_run(full_text)
            self._apply_run_formatting(run, primary_format)
        else:
            # Fallback: create simple formatted run
            run = paragraph.add_run(full_text)
    
    def _apply_paragraph_formatting(self, paragraph, para_formatting: Dict[str, Any]) -> None:
        """
        Apply paragraph-level formatting.
        
        Args:
            paragraph: Target paragraph
            para_formatting: Paragraph formatting dictionary
        """
        try:
            pf = paragraph.paragraph_format
            
            # Apply all paragraph formatting properties
            if para_formatting.get('alignment') is not None:
                pf.alignment = para_formatting['alignment']
            if para_formatting.get('left_indent') is not None:
                pf.left_indent = para_formatting['left_indent']
            if para_formatting.get('right_indent') is not None:
                pf.right_indent = para_formatting['right_indent']
            if para_formatting.get('first_line_indent') is not None:
                pf.first_line_indent = para_formatting['first_line_indent']
            if para_formatting.get('space_before') is not None:
                pf.space_before = para_formatting['space_before']
            if para_formatting.get('space_after') is not None:
                pf.space_after = para_formatting['space_after']
            if para_formatting.get('line_spacing') is not None:
                pf.line_spacing = para_formatting['line_spacing']
            if para_formatting.get('line_spacing_rule') is not None:
                pf.line_spacing_rule = para_formatting['line_spacing_rule']
            if para_formatting.get('widow_control') is not None:
                pf.widow_control = para_formatting['widow_control']
            if para_formatting.get('keep_together') is not None:
                pf.keep_together = para_formatting['keep_together']
            if para_formatting.get('keep_with_next') is not None:
                pf.keep_with_next = para_formatting['keep_with_next']
            if para_formatting.get('page_break_before') is not None:
                pf.page_break_before = para_formatting['page_break_before']
                
        except Exception:
            # Continue if formatting fails
            pass
    
    def _apply_run_formatting(self, run, run_formatting: Dict[str, Any]) -> None:
        """
        Apply run-level formatting.
        
        Args:
            run: Target run
            run_formatting: Run formatting dictionary
        """
        try:
            font = run.font
            
            # Apply all font properties
            if run_formatting.get('font_name'):
                font.name = run_formatting['font_name']
            if run_formatting.get('font_size'):
                font.size = run_formatting['font_size']
            if run_formatting.get('bold') is not None:
                font.bold = run_formatting['bold']
            if run_formatting.get('italic') is not None:
                font.italic = run_formatting['italic']
            if run_formatting.get('underline') is not None:
                font.underline = run_formatting['underline']
            if run_formatting.get('color'):
                font.color.rgb = run_formatting['color']
            if run_formatting.get('subscript') is not None:
                font.subscript = run_formatting['subscript']
            if run_formatting.get('superscript') is not None:
                font.superscript = run_formatting['superscript']
            if run_formatting.get('strike') is not None:
                font.strike = run_formatting['strike']
            if run_formatting.get('shadow') is not None:
                font.shadow = run_formatting['shadow']
            if run_formatting.get('small_caps') is not None:
                font.small_caps = run_formatting['small_caps']
            if run_formatting.get('all_caps') is not None:
                font.all_caps = run_formatting['all_caps']
                
        except Exception:
            # Continue if formatting fails
            pass


class ProjectDetector:
    """Handles detection of projects and responsibilities sections."""
    
    def __init__(self):
        self.config = PARSING_CONFIG
        
    def find_projects_and_responsibilities(self, doc: Document) -> List[Tuple[str, int, int]]:
        """
        Find all projects and their Responsibilities sections in the resume.
        Format: Company | Date
                Project title
                Responsibilities:
        
        Args:
            doc: Document to search
            
        Returns:
            List of tuples with (project_name, responsibilities_start_index, responsibilities_end_index)
        """
        projects = []
        current_project = None
        project_title_line = None
        in_responsibilities = False
        responsibilities_start = -1
        

        def is_responsibilities_heading(text):
            # Normalize text: lowercase, remove punctuation, collapse spaces
            import re
            norm = re.sub(r'[^a-z ]', '', text.lower())
            norm = re.sub(r'\s+', ' ', norm).strip()
            keywords = [
                'responsibilities', 'key responsibilities', 'duties', 'tasks'
            ]
            return any(norm.startswith(k) for k in keywords)

        for i, para in enumerate(doc.paragraphs):
            text = para.text.strip()

            # Look for company | date format (first line of project)
            if '|' in text and self._looks_like_company_date(text):
                # Save previous project if exists
                if current_project and responsibilities_start != -1:
                    responsibilities_end = self._find_responsibilities_end(doc, i, responsibilities_start)
                    projects.append((current_project, responsibilities_start, responsibilities_end))
                # Start new project - use company|date as project identifier
                current_project = text
                project_title_line = None
                in_responsibilities = False
                responsibilities_start = -1

            # If we just found a company|date line, next non-empty line should be project title
            elif current_project and project_title_line is None and text and not is_responsibilities_heading(text):
                project_title_line = text
                # Combine company|date with project title for full project name
                current_project = f"{current_project} - {project_title_line}"

            # Look for Responsibilities section (robust match)
            elif text and is_responsibilities_heading(text):
                in_responsibilities = True
                responsibilities_start = i + 1  # Start after the Responsibilities heading

            # If we're in responsibilities and find the end (next section or next project)
            elif in_responsibilities and text and (self._is_section_end(text) or ('|' in text and self._looks_like_company_date(text))):
                if current_project and responsibilities_start != -1:
                    responsibilities_end = i - 1
                    projects.append((current_project, responsibilities_start, responsibilities_end))
                in_responsibilities = False
                responsibilities_start = -1

        # Add the last project if found
        if current_project:
            if responsibilities_start != -1:
                responsibilities_end = len(doc.paragraphs) - 1
                projects.append((current_project, responsibilities_start, responsibilities_end))
            else:
                print(f"⚠️ Warning: No Responsibilities section found for project: {current_project}")

        # Debug print to diagnose project tuples before filtering
        print(f"[DEBUG] Raw projects before filter: {projects}")
        # Defensive filter: remove any projects with responsibilities_start == -1
        projects = [p for p in projects if p[1] != -1]
        print(f"[DEBUG] Filtered projects: {projects}")
        return projects
    def find_projects(self, doc: Document) -> List[Dict[str, Any]]:
        """Find projects in the document and return structured information."""
        projects_data = self.find_projects_and_responsibilities(doc)

        structured_projects = []
        for i, (title, start_idx, end_idx) in enumerate(projects_data):
            structured_projects.append({
                'title': title,
                'index': i,
                'responsibilities_start': start_idx,
                'responsibilities_end': end_idx
            })

        return structured_projects

    
    def _is_potential_project(self, text: str) -> bool:
        """
        Check if text looks like a project/role heading.
        
        Args:
            text: Text to check
            
        Returns:
            True if text looks like a project heading
        """
        if not text or len(text) >= DOC_CONFIG["max_project_title_length"]:
            return False
            
        if any(keyword in text.lower() for keyword in self.config["project_exclude_keywords"]):
            return False
        
        # Check if it contains pipe symbol (common in project titles like "Project Name | Date")
        if '|' in text:
            return True
        
        # Check if it's all caps (common for project/role headings)
        if text.isupper():
            return True
            
        # Check for common job title keywords
        if any(keyword in text.lower() for keyword in self.config["job_title_keywords"]):
            return True
            
        # Check for project-specific patterns
        if any(keyword in text.lower() for keyword in self.config["project_keywords"]):
            return True
            
        # Check if it looks like a company/project format (contains dates)
        import re
        date_pattern = r'\b(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec|\d{4}|\d{1,2}/\d{1,2}/\d{2,4})\b'
        if re.search(date_pattern, text.lower()):
            return True
            
        return False
    
    def _looks_like_company_date(self, text: str) -> bool:
        """
        Check if text looks like "Company | Date" format.
        
        Args:
            text: Text to check
            
        Returns:
            True if text looks like company|date format
        """
        if not text or '|' not in text:
            return False
        
        parts = text.split('|')
        if len(parts) != 2:
            return False
        
        # Check if second part contains date-like patterns
        date_part = parts[1].strip().lower()
        import re
        date_patterns = [
            r'\b(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\b',  # Month names
            r'\b\d{4}\b',  # Years
            r'\b\d{1,2}/\d{1,2}/\d{2,4}\b',  # Date formats
            r'\b(present|current|now)\b'  # Current indicators
        ]
        
        return any(re.search(pattern, date_part) for pattern in date_patterns)
    
    def _is_section_end(self, text: str) -> bool:
        """
        Check if text indicates the end of a section.
        
        Args:
            text: Text to check
            
        Returns:
            True if text indicates section end
        """
        return (
            text.startswith("##") or 
            any(keyword in text.lower() for keyword in self.config["section_end_keywords"])
        )
    
    def _find_responsibilities_end(self, doc: Document, current_index: int, start_index: int) -> int:
        """
        Find the end index of a responsibilities section.
        
        Args:
            doc: Document to search
            current_index: Current paragraph index
            start_index: Start of responsibilities section
            
        Returns:
            End index of responsibilities section
        """
        responsibilities_end = current_index - 1
        for j in range(current_index - 1, start_index - 1, -1):
            if (j < len(doc.paragraphs) and 
                doc.paragraphs[j].text.strip() and 
                not doc.paragraphs[j].text.strip().startswith("-")):
                responsibilities_end = j
                break
        return responsibilities_end


class PointDistributor:
    """Handles distribution of points across projects."""
    
    def distribute_points_to_projects(self, projects: List[Dict], tech_stacks_data) -> Dict[str, Any]:
        """
        Distribute tech stack points across the top 3 projects using round-robin distribution.
        Each project gets a mix of all tech stacks with points distributed evenly.
        This method only calculates distribution, it does NOT add points to the document.
        
        Args:
            projects: List of detected projects
            tech_stacks_data: Either a dictionary of tech stacks or tuple of (points, tech_names)
            
        Returns:
            Dictionary containing distribution results (no points are actually added)
        """
        if not projects or not tech_stacks_data:
            return {'success': False, 'error': 'No projects or tech stacks found'}
        
        # Handle different input formats
        if isinstance(tech_stacks_data, dict):
            tech_stacks = tech_stacks_data
        else:
            # Convert from (points, tech_names) tuple format
            selected_points, tech_names = tech_stacks_data
            if not selected_points or not tech_names:
                return {'success': False, 'error': 'No valid tech stacks found'}
            
            # Create a simple distribution - assign points to tech stacks
            tech_stacks = {}
            points_per_tech = len(selected_points) // len(tech_names) if tech_names else 0
            remaining_points = len(selected_points) % len(tech_names) if tech_names else 0
            
            current_index = 0
            for i, tech_name in enumerate(tech_names):
                points_for_tech = points_per_tech
                if i < remaining_points:
                    points_for_tech += 1
                
                if points_for_tech > 0:
                    tech_stacks[tech_name] = selected_points[current_index:current_index + points_for_tech]
                    current_index += points_for_tech
        
        # Use top 3 projects
        top_projects = projects[:3]
        
        # Calculate round-robin distribution
        distributed_points = self._calculate_round_robin_distribution(tech_stacks, len(top_projects))
        
        distribution = {}
        total_points_added = 0
        
        # Assign distributed points to each project
        for i, project in enumerate(top_projects):
            project_points = distributed_points[i]
            
            distribution[project['title']] = {
                'mixed_tech_stacks': project_points,  # Multiple tech stacks per project
                'project_index': project['index'],
                'insertion_point': project['responsibilities_start'],
                'responsibilities_end': project['responsibilities_end'],
                'total_points': sum(len(points) for points in project_points.values())
            }
            total_points_added += distribution[project['title']]['total_points']
        
        return {
            'success': True,
            'distribution': distribution,
            'points_added': total_points_added,
            'projects_used': len(distribution),
            'distribution_method': 'round_robin'
        }
    
    def _calculate_round_robin_distribution(self, tech_stacks: Dict[str, List[str]], num_projects: int) -> List[Dict[str, List[str]]]:
        """
        Calculate round-robin distribution of tech stack points across projects.
        Each project gets points in a true round-robin fashion, no duplicates, and points are split as evenly as possible.
        """
        project_distributions = [{} for _ in range(num_projects)]
        # Track all points assigned to each project to avoid duplicates
        project_points_set = [set() for _ in range(num_projects)]
        
        # Keep track of the next project to assign points to
        next_project_idx = 0
        
        # Process each tech stack
        for tech_name, points in tech_stacks.items():
            # For each point in this tech stack
            for point in points:
                # Try to find a project that doesn't have this point yet
                start_idx = next_project_idx
                assigned = False
                
                # Try each project once
                for _ in range(num_projects):
                    # If this project doesn't have this point yet
                    if point not in project_points_set[next_project_idx]:
                        # Add the tech stack to this project if it doesn't exist yet
                        if tech_name not in project_distributions[next_project_idx]:
                            project_distributions[next_project_idx][tech_name] = []
                        
                        # Add the point to this project
                        project_distributions[next_project_idx][tech_name].append(point)
                        project_points_set[next_project_idx].add(point)
                        assigned = True
                        
                        # Move to the next project for the next point
                        next_project_idx = (next_project_idx + 1) % num_projects
                        break
                    
                    # Try the next project
                    next_project_idx = (next_project_idx + 1) % num_projects
                
                # If we couldn't assign this point to any project (all projects already have it)
                # Just skip it to avoid duplicates
                if not assigned:
                    continue
        
        return project_distributions


class DocumentProcessor:
    """Main document processor that coordinates all operations."""
    
    def __init__(self):
        self.formatter = BulletFormatter()
        self.project_detector = ProjectDetector()
        self.point_distributor = PointDistributor()
    
    def add_points_to_project(self, doc: Document, project_info: Dict) -> int:
        # Debug print to catch missing insertion_point
        if 'insertion_point' not in project_info:
            print(f"DEBUG ERROR: project_info missing 'insertion_point': {project_info}")
        # Find the first existing bullet point in Responsibilities section
        insertion_point = project_info['insertion_point']
        mixed_tech_stacks = project_info['mixed_tech_stacks']
        # Get formatting from the first existing bullet in Responsibilities section
        formatting = None
        fallback_formatting = None
        first_bullet_index = None
        
        # Search for the first existing bullet point in the responsibilities section
        for i in range(insertion_point, min(len(doc.paragraphs), project_info.get('responsibilities_end', len(doc.paragraphs)) + 1)):
            para_formatting = self.formatter.get_bullet_formatting(doc, i)
            if para_formatting:
                formatting = para_formatting
                first_bullet_index = i
                break
        
        # If no existing bullet point found, use the original insertion point
        if first_bullet_index is None:
            first_bullet_index = insertion_point
        else:
            # Insert after the first existing bullet point
            first_bullet_index += 1
            
        points_added = 0
        current_insertion_point = first_bullet_index
        # Insert new points after the first existing point of the project
        for tech_name, points in mixed_tech_stacks.items():
            for point in points:
                try:
                    if current_insertion_point < len(doc.paragraphs):
                        new_para = doc.paragraphs[current_insertion_point].insert_paragraph_before()
                    else:
                        new_para = doc.add_paragraph()
                    self.formatter.apply_bullet_formatting(new_para, formatting, point, fallback_formatting)
                    points_added += 1
                    current_insertion_point += 1
                except Exception as e:
                    logger.error(f"Failed to add point '{point}' to project", extra={'error': str(e)})
                    continue
        return points_added
    
    def process_document(self, file_data: Dict) -> Dict[str, Any]:
        """
        Process a document by adding tech stack points to projects using round-robin distribution.
        
        Args:
            file_data: Dictionary containing file and processing information
            
        Returns:
            Processing result dictionary
        """
        try:
            # Load document
            doc = Document(BytesIO(file_data['file_content']))
            
            # Detect projects
            projects_data = self.project_detector.find_projects_and_responsibilities(doc)
            if not projects_data:
                return {
                    'success': False,
                    'error': 'No projects found in the document. Please ensure your resume has clear project sections.'
                }
            
            # Convert to structured format
            projects = []
            for i, (title, start_idx, end_idx) in enumerate(projects_data):
                projects.append({
                    'title': title,
                    'index': i,
                    'responsibilities_start': start_idx,
                    'responsibilities_end': end_idx
                })
            
            # Distribute points using round-robin logic
            distribution_result = self.point_distributor.distribute_points_to_projects(projects, file_data['tech_stacks'])
            if not distribution_result['success']:
                return distribution_result
            
            # Add points to each project with mixed tech stacks
            total_added = 0
            # Sort projects by insertion point to process them in order
            sorted_projects = sorted(distribution_result['distribution'].items(),
                                   key=lambda x: x[1]['insertion_point'])
            
            # Keep track of how many paragraphs we've added to adjust insertion points
            paragraph_offset = 0
            
            for project_title, project_info in sorted_projects:
                # Adjust insertion point based on previous additions
                adjusted_project_info = project_info.copy()
                adjusted_project_info['insertion_point'] += paragraph_offset
                if 'responsibilities_end' in adjusted_project_info:
                    adjusted_project_info['responsibilities_end'] += paragraph_offset
                
                added = self.add_points_to_project(doc, adjusted_project_info)
                total_added += added
                
                # Update the offset for subsequent projects
                paragraph_offset += added
            
            # Save modified document
            output_buffer = BytesIO()
            doc.save(output_buffer)
            output_buffer.seek(0)
            
            return {
                'success': True,
                'modified_content': output_buffer.getvalue(),
                'points_added': total_added,
                'projects_modified': distribution_result['projects_used'],
                'distribution_details': distribution_result['distribution'],
                'distribution_method': 'round_robin'
            }
            
        except Exception as e:
            logger.error(f"Document processing failed for {file_data.get('filename', 'unknown')}", exception=e)
            return {
                'success': False,
                'error': f"Failed to process document: {str(e)}"
            }


class FileProcessor:
    """Handles file operations and memory management."""
    
    @staticmethod
    def ensure_file_has_name(file_obj, default_name: str = None) -> Any:
        """
        Ensures file objects have a name attribute for DOCX processing.
        
        Args:
            file_obj: File object to process
            default_name: Default name if none exists
            
        Returns:
            File object with name attribute
        """
        if hasattr(file_obj, 'name'):
            return file_obj
        else:
            # Create wrapper for BytesIO objects
            if default_name is None:
                default_name = DOC_CONFIG["default_filename"]
            file_obj.name = default_name
            return file_obj
    
    @staticmethod
    def cleanup_memory() -> None:
        """Memory optimization - clean up temporary variables."""
        try:
            # Force garbage collection
            gc.collect()
            
            # Clear thread-local storage if any
            current_thread = threading.current_thread()
            if hasattr(current_thread, '__dict__'):
                # Clear non-essential thread data
                thread_dict = current_thread.__dict__.copy()
                for key in thread_dict:
                    if key.startswith('_temp_') or key.startswith('_cache_'):
                        delattr(current_thread, key)
        except Exception:
            # Don't let cleanup errors affect the main application
            pass


def get_document_processor() -> DocumentProcessor:
    """
    Get a new instance of the document processor.
    
    Returns:
        DocumentProcessor instance
    """
    return DocumentProcessor()
