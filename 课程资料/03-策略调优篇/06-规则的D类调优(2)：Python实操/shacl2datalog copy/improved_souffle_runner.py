#!/usr/bin/env python3
"""
Improved Soufflé Runner with better memory monitoring and violation tracking
Place this file in the root directory of your project
"""

import sys
import logging
from pathlib import Path
import pandas as pd
import numpy as np
from typing import List, Dict, Any
import json
import time
import subprocess
import psutil
import os
import shutil
from datetime import datetime

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ImprovedSouffleRunner:
    """Improved Soufflé runner with better memory monitoring and violation tracking"""
    
    def __init__(self, souffle_path: str = "souffle"):
        self.souffle_path = souffle_path
        self.execution_stats = {}
        self.run_id = None
    
    def run_souffle_program(self, program_file: str, facts_dir: str = None, 
                          output_dir: str = "output", run_id: str = None) -> Dict[str, Any]:
        """Run Soufflé with improved monitoring and unique output preservation"""
        try:
            # Generate unique run ID if not provided
            if run_id is None:
                run_id = f"{Path(program_file).stem}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            self.run_id = run_id
            
            # Create unique output directory for this run
            unique_output_dir = Path(output_dir) / f"run_{run_id}"
            unique_output_dir.mkdir(parents=True, exist_ok=True)
            
            # Build command
            cmd = [self.souffle_path, str(program_file)]
            
            if facts_dir:
                cmd.extend(["-F", str(facts_dir)])
            
            cmd.extend(["-D", str(unique_output_dir)])
            
            logger.info(f"Running Soufflé command: {' '.join(cmd)}")
            logger.info(f"Output will be saved to: {unique_output_dir}")
            
            # Start performance monitoring
            start_time = time.time()
            
            # Launch Soufflé subprocess
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, 
                                     stderr=subprocess.PIPE, text=True)
            
            # IMPROVED MEMORY MONITORING
            max_memory_mb = 0
            memory_samples = []
            sample_count = 0
            
            try:
                ps_process = psutil.Process(process.pid)
                
                # More aggressive sampling for short-running processes
                while process.poll() is None:
                    try:
                        # Get all memory metrics
                        memory_info = ps_process.memory_info()
                        
                        # Calculate different memory metrics
                        rss_mb = memory_info.rss / 1024 / 1024
                        vms_mb = memory_info.vms / 1024 / 1024 if hasattr(memory_info, 'vms') else rss_mb
                        
                        # Track all metrics
                        current_memory = {
                            'rss': rss_mb,
                            'vms': vms_mb,
                            'time': time.time() - start_time
                        }
                        
                        memory_samples.append(current_memory)
                        max_memory_mb = max(max_memory_mb, rss_mb)
                        sample_count += 1
                        
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        break
                    
                    # Very short sleep for better sampling
                    time.sleep(0.001)  # 1ms sampling
                    
            except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
                logger.warning(f"Process monitoring issue: {e}")
            
            # Wait for process to complete
            stdout, stderr = process.communicate()
            end_time = time.time()
            execution_time = end_time - start_time
            
            # Check execution result
            if process.returncode != 0:
                logger.error(f"Soufflé execution failed with return code {process.returncode}")
                logger.error(f"stderr: {stderr}")
                return {
                    "success": False,
                    "error": f"Soufflé execution failed: {stderr}",
                    "stdout": stdout,
                    "stderr": stderr
                }
            
            # IMPROVED MEMORY CALCULATION
            # If we didn't get good samples, try to estimate from output size
            if max_memory_mb <= 0 or sample_count < 5:
                # Estimate based on data size and output
                output_size_mb = self._get_directory_size_mb(unique_output_dir)
                facts_size_mb = self._get_directory_size_mb(facts_dir) if facts_dir else 0
                
                # Soufflé typically uses 2-3x the data size in memory
                estimated_memory = max(
                    (facts_size_mb + output_size_mb) * 2.5,
                    10.0  # Minimum 10MB for Soufflé
                )
                
                logger.warning(f"Limited memory samples ({sample_count}), estimating: {estimated_memory:.2f}MB")
                max_memory_mb = estimated_memory
            else:
                # Calculate more robust memory metric from samples
                if memory_samples:
                    # Use 95th percentile to avoid outliers
                    rss_values = [s['rss'] for s in memory_samples]
                    percentile_95 = np.percentile(rss_values, 95) if len(rss_values) > 10 else max(rss_values)
                    max_memory_mb = max(max_memory_mb, percentile_95)
            
            # Count violations and save detailed results
            violations_count, violation_details = self._analyze_violations(unique_output_dir)
            
            # Save violation details to a separate file
            violation_analysis_file = unique_output_dir / "violation_analysis.json"
            with open(violation_analysis_file, 'w') as f:
                json.dump({
                    'run_id': run_id,
                    'count': violations_count,
                    'details': violation_details,
                    'timestamp': datetime.now().isoformat()
                }, f, indent=2)
            
            self.execution_stats = {
                "execution_time": execution_time,
                "memory_used_mb": max_memory_mb,
                "memory_samples": len(memory_samples),
                "violations_count": violations_count,
                "output_directory": str(unique_output_dir),
                "violation_analysis_file": str(violation_analysis_file)
            }
            
            logger.info(f"Soufflé completed: {execution_time:.3f}s, "
                       f"{max_memory_mb:.2f}MB (from {len(memory_samples)} samples), "
                       f"{violations_count} violations")
            
            return {
                "success": True,
                "stdout": stdout,
                "stderr": stderr,
                "output_dir": str(unique_output_dir),
                "performance": self.execution_stats,
                "violations_count": violations_count,
                "violation_details": violation_details[:10]  # First 10 for preview
            }
            
        except FileNotFoundError:
            logger.error("Soufflé executable not found in PATH")
            return {
                "success": False,
                "error": "Soufflé not found in PATH. Please install Soufflé first."
            }
        except Exception as e:
            logger.error(f"Unexpected error in Soufflé execution: {e}")
            return {
                "success": False,
                "error": f"Unexpected error: {str(e)}"
            }
    
    def _get_directory_size_mb(self, directory: str) -> float:
        """Calculate directory size in MB"""
        if not directory or not Path(directory).exists():
            return 0.0
        
        total_size = 0
        for dirpath, dirnames, filenames in os.walk(directory):
            for filename in filenames:
                filepath = os.path.join(dirpath, filename)
                try:
                    total_size += os.path.getsize(filepath)
                except:
                    pass
        
        return total_size / 1024 / 1024
    
    def _analyze_violations(self, output_dir: str) -> tuple:
        """Analyze violations and return count and details"""
        violation_file = Path(output_dir) / "violation.csv"
        
        if not violation_file.exists():
            logger.info(f"No violation file found at {violation_file}")
            return 0, []
        
        try:
            violations = []
            with open(violation_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            # Parse violations
            has_header = False
            for i, line in enumerate(lines):
                line = line.strip()
                if not line:
                    continue
                
                # Check if first line is header
                if i == 0 and any(keyword in line.lower() for keyword in ['entity', 'constraint', 'message']):
                    has_header = True
                    continue
                
                # Parse violation line
                parts = line.split('\t')
                if len(parts) >= 3:
                    violations.append({
                        'entity': parts[0],
                        'constraint': parts[1],
                        'message': parts[2] if len(parts) > 2 else ''
                    })
                else:
                    violations.append({'raw': line})
            
            logger.info(f"Found {len(violations)} violations in {violation_file}")
            return len(violations), violations
            
        except Exception as e:
            logger.error(f"Error analyzing violation file {violation_file}: {e}")
            return 0, []