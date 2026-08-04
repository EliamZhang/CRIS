#!/usr/bin/env python3
"""
Violation Analysis Tool - Analyze differences between Soufflé and pySHACL
"""

import json
import pandas as pd
from pathlib import Path
from typing import Dict, List, Set
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ViolationAnalyzer:
    """Analyze violation differences between systems"""
    
    def __init__(self, violations_dir: str = "results/all_violations"):
        self.violations_dir = Path(violations_dir)
        
    def analyze_all_violations(self):
        """Analyze all violation files and create comparison report"""
        
        # Group files by test case
        souffle_files = {}
        pyshacl_files = {}
        
        for file in self.violations_dir.glob("*.json"):
            if "souffle" in file.name.lower():
                # Extract test case name
                test_case = file.name.replace("souffle_", "").split("_2024")[0]
                souffle_files[test_case] = file
            elif "pyshacl" in file.name.lower():
                test_case = file.name.replace("pyshacl_", "").split("_2024")[0]
                pyshacl_files[test_case] = file
        
        # Compare each test case
        comparisons = []
        for test_case in souffle_files.keys():
            if test_case in pyshacl_files:
                comparison = self.compare_violation_files(
                    souffle_files[test_case],
                    pyshacl_files[test_case],
                    test_case
                )
                comparisons.append(comparison)
        
        # Create summary report
        self.create_summary_report(comparisons)
        
        return comparisons
    
    def compare_violation_files(self, souffle_file: Path, pyshacl_file: Path, test_case: str) -> Dict:
        """Compare violations from two files"""
        
        # Load violations
        with open(souffle_file, 'r') as f:
            souffle_data = json.load(f)
        
        with open(pyshacl_file, 'r') as f:
            pyshacl_data = json.load(f)
        
        souffle_violations = souffle_data.get('violations', [])
        pyshacl_violations = pyshacl_data.get('violations', [])
        
        # Extract violation details
        souffle_entities = set()
        souffle_messages = []
        
        for v in souffle_violations:
            if isinstance(v, dict):
                if 'entity' in v:
                    souffle_entities.add(v['entity'])
                if 'message' in v:
                    souffle_messages.append(v['message'])
        
        pyshacl_entities = set()
        pyshacl_messages = []
        
        for v in pyshacl_violations:
            if isinstance(v, dict):
                if 'subject' in v:
                    # Extract entity ID from subject URI
                    subject = v['subject']
                    if '/' in subject:
                        entity_id = subject.split('/')[-1]
                        pyshacl_entities.add(entity_id)
                if 'message' in v:
                    pyshacl_messages.append(v['message'])
        
        # Compare
        comparison = {
            'test_case': test_case,
            'souffle_count': souffle_data.get('violations_count', 0),
            'pyshacl_count': pyshacl_data.get('violations_count', 0),
            'count_difference': abs(souffle_data.get('violations_count', 0) - 
                                  pyshacl_data.get('violations_count', 0)),
            'souffle_unique_entities': len(souffle_entities),
            'pyshacl_unique_entities': len(pyshacl_entities),
            'common_entities': len(souffle_entities.intersection(pyshacl_entities)),
            'souffle_only_entities': list(souffle_entities - pyshacl_entities)[:10],
            'pyshacl_only_entities': list(pyshacl_entities - souffle_entities)[:10],
            'souffle_sample_messages': souffle_messages[:5],
            'pyshacl_sample_messages': pyshacl_messages[:5]
        }
        
        return comparison
    
    def create_summary_report(self, comparisons: List[Dict]):
        """Create a summary report of all comparisons"""
        
        report_lines = [
            "# Violation Analysis Report",
            "",
            "## Summary",
            ""
        ]
        
        # Overall statistics
        total_comparisons = len(comparisons)
        matching = sum(1 for c in comparisons if c['souffle_count'] == c['pyshacl_count'])
        
        report_lines.extend([
            f"- Total test cases analyzed: {total_comparisons}",
            f"- Cases with matching counts: {matching} ({matching/total_comparisons*100:.1f}%)",
            f"- Cases with differences: {total_comparisons - matching}",
            "",
            "## Detailed Comparison",
            ""
        ])
        
        # Create comparison table
        df_data = []
        for comp in comparisons:
            df_data.append({
                'Test Case': comp['test_case'],
                'Soufflé Count': comp['souffle_count'],
                'pySHACL Count': comp['pyshacl_count'],
                'Difference': comp['count_difference'],
                'Match': '✓' if comp['souffle_count'] == comp['pyshacl_count'] else '✗'
            })
        
        df = pd.DataFrame(df_data)
        report_lines.append(df.to_markdown(index=False))
        report_lines.append("")
        
        # Detailed analysis for mismatches
        report_lines.append("## Mismatch Analysis")
        report_lines.append("")
        
        for comp in comparisons:
            if comp['souffle_count'] != comp['pyshacl_count']:
                report_lines.extend([
                    f"### {comp['test_case']}",
                    f"- Soufflé violations: {comp['souffle_count']}",
                    f"- pySHACL violations: {comp['pyshacl_count']}",
                    f"- Difference: {comp['count_difference']}",
                    ""
                ])
                
                if comp['souffle_sample_messages']:
                    report_lines.append("**Sample Soufflé messages:**")
                    for msg in comp['souffle_sample_messages'][:3]:
                        report_lines.append(f"  - {msg}")
                    report_lines.append("")
                
                if comp['pyshacl_sample_messages']:
                    report_lines.append("**Sample pySHACL messages:**")
                    for msg in comp['pyshacl_sample_messages'][:3]:
                        report_lines.append(f"  - {msg}")
                    report_lines.append("")
        
        # Save report
        report_file = self.violations_dir.parent / f"violation_analysis_report_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.md"
        with open(report_file, 'w') as f:
            f.write('\n'.join(report_lines))
        
        logger.info(f"Report saved to: {report_file}")
        
        # Also save as CSV for easy analysis
        csv_file = self.violations_dir.parent / f"violation_comparison_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.csv"
        df.to_csv(csv_file, index=False)
        logger.info(f"CSV saved to: {csv_file}")
        
        return report_file

def analyze_violations(violations_dir: str = "results/all_violations"):
    """Main function to analyze violations"""
    analyzer = ViolationAnalyzer(violations_dir)
    comparisons = analyzer.analyze_all_violations()
    
    print("\n" + "="*60)
    print("VIOLATION ANALYSIS COMPLETE")
    print("="*60)
    
    for comp in comparisons:
        match_symbol = "✓" if comp['souffle_count'] == comp['pyshacl_count'] else "✗"
        print(f"{match_symbol} {comp['test_case']}: "
              f"Soufflé={comp['souffle_count']}, "
              f"pySHACL={comp['pyshacl_count']}, "
              f"Diff={comp['count_difference']}")
    
    print("\nCheck the generated report for detailed analysis.")

if __name__ == "__main__":
    analyze_violations()