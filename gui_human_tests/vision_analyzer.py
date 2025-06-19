#!/usr/bin/env python3
"""
OpenAI Vision Analyzer for FoS_DeckPro GUI Testing
Analyzes screenshots to ensure the app looks, feels, and works as intended
"""

import os
import base64
import json
import time
from datetime import datetime
from typing import List, Dict, Any
import openai
from pathlib import Path

class VisionAnalyzer:
    """OpenAI Vision-based screenshot analyzer for UI/UX validation"""
    
    def __init__(self, api_key: str = None):
        """Initialize the vision analyzer with OpenAI API key"""
        self.api_key = api_key or os.getenv('OPENAI_API_KEY')
        if not self.api_key:
            raise ValueError("OpenAI API key required. Set OPENAI_API_KEY environment variable or pass api_key parameter.")
        
        self.client = openai.OpenAI(api_key=self.api_key)
        self.analysis_results = []
        
    def encode_image(self, image_path: str) -> str:
        """Encode image to base64 for OpenAI Vision API"""
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')
    
    def analyze_screenshot(self, image_path: str, context: str = "") -> Dict[str, Any]:
        """Analyze a single screenshot using OpenAI Vision"""
        try:
            # Encode the image
            base64_image = self.encode_image(image_path)
            
            # Create the analysis prompt
            prompt = f"""
            Analyze this screenshot of a Magic: The Gathering card inventory management application called FoS_DeckPro.
            
            Context: {context}
            
            Please provide a detailed analysis covering:
            
            1. **Visual Design & Layout:**
               - Is the interface clean, modern, and professional?
               - Are elements properly aligned and spaced?
               - Is the color scheme appropriate and accessible?
               - Are fonts readable and consistent?
            
            2. **User Experience:**
               - Is the interface intuitive and easy to navigate?
               - Are buttons, menus, and controls clearly visible and accessible?
               - Is the information hierarchy clear and logical?
               - Would a human user understand what to do next?
            
            3. **Functionality Assessment:**
               - What appears to be happening in this screenshot?
               - Are there any visible errors, warnings, or issues?
               - Is the current state of the application clear to the user?
               - Are there any missing elements or broken functionality?
            
            4. **Human-Centered Design:**
               - Does this interface feel welcoming and user-friendly?
               - Would different types of users (beginner, power user, etc.) find this usable?
               - Are there any accessibility concerns?
               - Does the interface follow modern UI/UX best practices?
            
            5. **Specific Issues:**
               - List any errors, warnings, or problematic elements
               - Identify any confusing or unclear interface elements
               - Note any missing functionality or broken features
            
            6. **Overall Assessment:**
               - Rate the overall quality (1-10)
               - Provide specific recommendations for improvement
               - Would you recommend this interface to users?
            
            Provide your analysis in a structured, detailed format with specific observations and actionable feedback.
            """
            
            # Call OpenAI Vision API
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/png;base64,{base64_image}"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=2000,
                temperature=0.3
            )
            
            # Extract and structure the analysis
            analysis = response.choices[0].message.content
            
            result = {
                'image_path': image_path,
                'context': context,
                'analysis': analysis,
                'timestamp': datetime.now().isoformat(),
                'model': 'gpt-4o',
                'success': True
            }
            
            self.analysis_results.append(result)
            return result
            
        except Exception as e:
            error_result = {
                'image_path': image_path,
                'context': context,
                'error': str(e),
                'timestamp': datetime.now().isoformat(),
                'success': False
            }
            self.analysis_results.append(error_result)
            return error_result
    
    def analyze_screenshot_batch(self, image_paths: List[str], contexts: List[str] = None) -> List[Dict[str, Any]]:
        """Analyze multiple screenshots in batch"""
        if contexts is None:
            contexts = [""] * len(image_paths)
        
        results = []
        for i, (image_path, context) in enumerate(zip(image_paths, contexts)):
            print(f"Analyzing screenshot {i+1}/{len(image_paths)}: {os.path.basename(image_path)}")
            result = self.analyze_screenshot(image_path, context)
            results.append(result)
            
            # Rate limiting - be nice to the API
            if i < len(image_paths) - 1:
                time.sleep(1)
        
        return results
    
    def analyze_persona_screenshots(self, persona_name: str, screenshots_dir: str) -> List[Dict[str, Any]]:
        """Analyze all screenshots for a specific persona"""
        persona_dir = os.path.join(screenshots_dir, f"screenshots_{persona_name}")
        if not os.path.exists(persona_dir):
            print(f"Warning: No screenshots found for persona {persona_name}")
            return []
        
        # Get all PNG files in the persona directory
        image_paths = []
        contexts = []
        
        for image_file in sorted(os.listdir(persona_dir)):
            if image_file.endswith('.png'):
                image_path = os.path.join(persona_dir, image_file)
                image_paths.append(image_path)
                
                # Create context based on filename
                context = f"Persona: {persona_name.replace('_', ' ').title()}, Action: {image_file.replace('.png', '').replace('_', ' ')}"
                contexts.append(context)
        
        return self.analyze_screenshot_batch(image_paths, contexts)
    
    def generate_summary_report(self) -> str:
        """Generate a comprehensive summary report of all analyses"""
        if not self.analysis_results:
            return "No analyses performed yet."
        
        successful_analyses = [r for r in self.analysis_results if r.get('success', False)]
        failed_analyses = [r for r in self.analysis_results if not r.get('success', False)]
        
        report = f"""
# FoS_DeckPro GUI Analysis Report
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Summary
- Total screenshots analyzed: {len(self.analysis_results)}
- Successful analyses: {len(successful_analyses)}
- Failed analyses: {len(failed_analyses)}

## Failed Analyses
"""
        
        for failed in failed_analyses:
            report += f"- {failed['image_path']}: {failed.get('error', 'Unknown error')}\n"
        
        report += "\n## Detailed Analyses\n"
        
        for i, analysis in enumerate(successful_analyses, 1):
            report += f"""
### Analysis {i}: {os.path.basename(analysis['image_path'])}
**Context:** {analysis['context']}
**Timestamp:** {analysis['timestamp']}

{analysis['analysis']}

---
"""
        
        return report
    
    def save_report(self, filename: str = None):
        """Save the analysis report to a file"""
        if filename is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"vision_analysis_report_{timestamp}.md"
        
        report = self.generate_summary_report()
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(report)
        
        print(f"Analysis report saved to: {filename}")
        return filename
    
    def save_raw_results(self, filename: str = None):
        """Save raw analysis results as JSON"""
        if filename is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"vision_analysis_results_{timestamp}.json"
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.analysis_results, f, indent=2, ensure_ascii=False)
        
        print(f"Raw results saved to: {filename}")
        return filename

def main():
    """Example usage of the VisionAnalyzer"""
    # Check for API key
    if not os.getenv('OPENAI_API_KEY'):
        print("Error: OPENAI_API_KEY environment variable not set")
        print("Please set your OpenAI API key:")
        print("export OPENAI_API_KEY='your-api-key-here'")
        return
    
    # Initialize analyzer
    analyzer = VisionAnalyzer()
    
    # Example: Analyze screenshots from a specific persona
    persona_name = "normal_user"
    screenshots_dir = "."
    
    print(f"Analyzing screenshots for persona: {persona_name}")
    results = analyzer.analyze_persona_screenshots(persona_name, screenshots_dir)
    
    # Save reports
    analyzer.save_report()
    analyzer.save_raw_results()
    
    print("Analysis complete!")

if __name__ == "__main__":
    main() 