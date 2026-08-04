# SHACL to Datalog Converter - Experimental Results (FIXED)
Generated: 2025-08-17 22:48:57

## Executive Summary

This report presents comprehensive experimental evaluation of the SHACL to Datalog converter
with FIXED memory calculation and constraint validation.

## 1. Correctness Validation

### SHACL Constraint Coverage
| shacl_file              |   shapes_count |   properties_count |   rules_count |   declarations_count | conversion_success   |
|:------------------------|---------------:|-------------------:|--------------:|---------------------:|:---------------------|
| simple_constraints.ttl  |              1 |                  2 |             7 |                   10 | True                 |
| medium_constraints.ttl  |              1 |                  5 |            20 |                   16 | True                 |
| complex_constraints.ttl |              2 |                  7 |            24 |                   16 | True                 |

**Key Findings:**
- Conversion Success Rate: **100.0%**
- Total SHACL Shapes Processed: **4**
- Total Datalog Rules Generated: **51**
- Average Rules per Shape: **12.8**

## 2. Performance Evaluation (FIXED)

**Memory Calculation Fix Verification:**
- Soufflé Average Memory Usage: **6.02 MB**
- Minimum Memory Value: **5.47 MB**

**Performance Highlights:**
- Average Speedup: **81.26x** (Soufflé vs pySHACL)
- Soufflé Success Rate: **100.0%**
- Memory Efficiency: Significant improvement with reliable measurement

## 3. Wikidata Quality Assessment

|   sample_size |   execution_time |   violations_found |   memory_used | success   |   violation_rate | error                  |
|--------------:|-----------------:|-------------------:|--------------:|:----------|-----------------:|:-----------------------|
|          1000 |                0 |                  0 |             0 | False     |                0 | float division by zero |
|          1500 |                0 |                  0 |             0 | False     |                0 | float division by zero |
|          3000 |                0 |                  0 |             0 | False     |                0 | float division by zero |
|          5000 |                0 |                  0 |             0 | False     |                0 | float division by zero |
