#!/usr/bin/env python3
"""
主转换器模块 - 协调所有组件（修复版）
项目：Validation of Large Knowledge Graphs  
文件：src/converter.py
"""

import subprocess
import time
from typing import Dict, List, Any, Optional
from pathlib import Path
import logging
from datetime import datetime
import psutil
import os
import json

# 导入项目模块
from .shacl_parser import SHACLParser, NodeShape
from .souffle_generator import SouffleGenerator
from .wikidata_client import WikidataClient
from .pyshacl_validator import PySHACLValidator
from .performance_evaluator import PerformanceEvaluator

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class SouffleRunner:
    """Soufflé程序运行器 - 增强版"""
    
    def __init__(self, souffle_path: str = "souffle"):
        self.souffle_path = souffle_path
        self.execution_stats = {}
    
    def run_souffle_program(self, program_file: str, facts_dir: str = None, 
                          output_dir: str = "output", 
                          profile: bool = False,
                          compile_only: bool = False) -> Dict[str, Any]:
        """运行Soufflé程序并收集性能数据"""
        try:
            # 确保输出目录存在
            Path(output_dir).mkdir(parents=True, exist_ok=True)
            
            # 构建命令
            cmd = [self.souffle_path]
            
            # 添加性能分析选项
            if profile:
                cmd.append("--profile")
                cmd.append(f"{output_dir}/profile.json")
            
            # 编译优化选项
            cmd.extend(["-c", "-j", "4"])  # 使用4个线程编译
            
            cmd.append(str(program_file))
            
            if facts_dir:
                cmd.extend(["-F", str(facts_dir)])
            
            cmd.extend(["-D", str(output_dir)])
            
            # 只编译不运行
            if compile_only:
                cmd.append("--compile")
            
            logger.info(f"运行Soufflé命令: {' '.join(cmd)}")
            
            # 性能测量
            process = psutil.Process(os.getpid())
            mem_before = process.memory_info().rss / 1024 / 1024  # MB
            
            start_time = time.time()
            
            # 运行程序
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            
            end_time = time.time()
            mem_after = process.memory_info().rss / 1024 / 1024  # MB
            
            # 统计违规数量
            violations_count = self._count_violations(output_dir)
            
            # 读取性能分析数据
            profile_data = None
            if profile:
                profile_file = Path(output_dir) / "profile.json"
                if profile_file.exists():
                    with open(profile_file, 'r') as f:
                        profile_data = json.load(f)
            
            self.execution_stats = {
                "execution_time": end_time - start_time,
                "memory_before_mb": mem_before,
                "memory_after_mb": mem_after,
                "memory_used_mb": mem_after - mem_before,
                "violations_count": violations_count,
                "profile": profile_data
            }
            
            logger.info(f"Soufflé程序运行成功，执行时间: {self.execution_stats['execution_time']:.3f}秒")
            logger.info(f"发现违规: {violations_count}")
            
            return {
                "success": True,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "output_dir": output_dir,
                "performance": self.execution_stats,
                "violations_count": violations_count
            }
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Soufflé运行失败: {e}")
            logger.error(f"标准输出: {e.stdout}")
            logger.error(f"标准错误: {e.stderr}")
            return {
                "success": False,
                "error": str(e),
                "stdout": e.stdout if e.stdout else "",
                "stderr": e.stderr if e.stderr else ""
            }
        except FileNotFoundError:
            logger.error("找不到Soufflé可执行文件")
            return {
                "success": False,
                "error": "Soufflé not found in PATH. Please install Soufflé first."
            }
    
    def _count_violations(self, output_dir: str) -> int:
        """统计违规数量"""
        violation_file = Path(output_dir) / "violation.csv"
        if violation_file.exists():
            with open(violation_file, 'r') as f:
                # 计算行数（不包括可能的标题行）
                lines = f.readlines()
                # 检查是否有标题行
                if lines and lines[0].startswith("entity"):
                    return len(lines) - 1
                return len(lines)
        return 0
    
    def analyze_violations(self, output_dir: str) -> Dict[str, Any]:
        """分析违规详情"""
        violation_file = Path(output_dir) / "violation.csv"
        if not violation_file.exists():
            return {"total": 0, "by_constraint": {}, "by_entity": {}}
        
        violations_by_constraint = {}
        violations_by_entity = {}
        
        with open(violation_file, 'r') as f:
            for line in f:
                parts = line.strip().split('\t')
                if len(parts) >= 3:
                    entity, constraint, message = parts[0], parts[1], parts[2]
                    
                    # 按约束类型统计
                    if constraint not in violations_by_constraint:
                        violations_by_constraint[constraint] = []
                    violations_by_constraint[constraint].append({
                        "entity": entity,
                        "message": message
                    })
                    
                    # 按实体统计
                    if entity not in violations_by_entity:
                        violations_by_entity[entity] = []
                    violations_by_entity[entity].append({
                        "constraint": constraint,
                        "message": message
                    })
        
        return {
            "total": sum(len(v) for v in violations_by_constraint.values()),
            "by_constraint": {k: len(v) for k, v in violations_by_constraint.items()},
            "by_entity": {k: len(v) for k, v in violations_by_entity.items()},
            "details": {
                "constraints": violations_by_constraint,
                "entities": violations_by_entity
            }
        }


class SHACLToSouffleConverter:
    """主转换器类 - 增强版"""
    
    def __init__(self):
        self.parser = SHACLParser()
        self.generator = SouffleGenerator()
        self.runner = SouffleRunner()
        self.wikidata_client = WikidataClient()
        self.pyshacl_validator = PySHACLValidator()
        self.evaluator = PerformanceEvaluator()
        self.conversion_stats = {}
    
    def convert_file(self, shacl_file: str, output_dir: str = "output",
                    optimize: bool = True) -> Dict[str, Any]:
        """转换SHACL文件为Soufflé程序"""
        logger.info(f"开始转换SHACL文件: {shacl_file}")
        
        try:
            # 1. 解析SHACL
            shapes = self.parser.parse_shacl_file(shacl_file)
            if not shapes:
                raise ValueError("没有找到有效的SHACL Shape")
            
            logger.info(f"解析到 {len(shapes)} 个形状")
            
            # 2. 生成Soufflé程序
            souffle_program = self.generator.convert_shapes_to_souffle(shapes)
            
            # 3. 优化程序（可选）
            if optimize:
                souffle_program = self._optimize_souffle_program(souffle_program)
            
            # 4. 保存程序文件
            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)
            
            program_file = output_path / "validation.dl"
            with open(program_file, 'w', encoding='utf-8') as f:
                f.write(souffle_program)
            
            logger.info(f"Soufflé程序已保存到: {program_file}")
            
            # 5. 保存中间文件（用于调试）
            self._save_debug_files(output_path, shapes, souffle_program)
            
            # 6. 收集统计信息
            parser_stats = self.parser.get_statistics()
            generator_stats = self.generator.get_statistics()
            
            self.conversion_stats = {
                **parser_stats,
                **generator_stats,
                'conversion_time': datetime.now().isoformat(),
                'input_file': shacl_file,
                'output_file': str(program_file),
                'optimized': optimize
            }
            
            return {
                'success': True,
                'shapes': shapes,
                'program': souffle_program,
                'program_file': str(program_file),
                'parser_stats': parser_stats,
                'generator_stats': generator_stats,
                'stats': self.conversion_stats
            }
            
        except Exception as e:
            logger.error(f"转换失败: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }
    
    def _optimize_souffle_program(self, program: str) -> str:
        """优化Soufflé程序"""
        lines = program.split('\n')
        optimized_lines = []
        
        # 添加优化指令
        optimized_lines.append("// ===== OPTIMIZATION DIRECTIVES =====")
        optimized_lines.append(".pragma \"inline\"")  # 内联小规则
        optimized_lines.append(".pragma \"magic-transform\" \"*\"")  # Magic sets转换
        optimized_lines.append("")
        
        # 添加原始程序
        optimized_lines.extend(lines)
        
        return '\n'.join(optimized_lines)
    
    def _save_debug_files(self, output_path: Path, shapes: List[NodeShape], 
                         program: str):
        """保存调试文件"""
        debug_dir = output_path / "debug"
        debug_dir.mkdir(exist_ok=True)
        
        # 保存解析的形状信息
        shapes_info = []
        for shape in shapes:
            shape_dict = {
                "uri": shape.uri,
                "target_class": shape.target_class,
                "properties": len(shape.properties),
                "closed": shape.closed,
                "constraints": []
            }
            for prop in shape.properties:
                constraint_info = {
                    "path": prop.path,
                    "constraints": []
                }
                if prop.min_count is not None:
                    constraint_info["constraints"].append(f"minCount: {prop.min_count}")
                if prop.max_count is not None:
                    constraint_info["constraints"].append(f"maxCount: {prop.max_count}")
                if prop.datatype:
                    constraint_info["constraints"].append(f"datatype: {prop.datatype}")
                if prop.pattern:
                    constraint_info["constraints"].append(f"pattern: {prop.pattern}")
                if prop.has_value:
                    constraint_info["constraints"].append(f"hasValue: {prop.has_value}")
                if prop.node_kind:
                    constraint_info["constraints"].append(f"nodeKind: {prop.node_kind}")
                if prop.in_values:
                    constraint_info["constraints"].append(f"in: {prop.in_values}")
                shape_dict["constraints"].append(constraint_info)
            shapes_info.append(shape_dict)
        
        with open(debug_dir / "shapes.json", 'w', encoding='utf-8') as f:
            json.dump(shapes_info, f, indent=2, ensure_ascii=False)
        
        # 保存统计信息
        with open(debug_dir / "statistics.json", 'w', encoding='utf-8') as f:
            json.dump(self.conversion_stats, f, indent=2, ensure_ascii=False)
    
    def validate_with_wikidata(self, shacl_file: str, entity_type: str = "person",
                              sample_size: int = 1000, output_dir: str = "output",
                              profile: bool = False) -> Dict[str, Any]:
        """使用Wikidata数据进行验证"""
        logger.info(f"开始Wikidata验证，实体类型: {entity_type}, 样本大小: {sample_size}")
        
        # 1. 转换SHACL
        conversion_result = self.convert_file(shacl_file, output_dir, optimize=True)
        if not conversion_result['success']:
            return conversion_result
        
        # 2. 从Wikidata获取数据
        logger.info("正在从Wikidata获取数据...")
        wikidata_data = self.wikidata_client.fetch_sample_data(entity_type, sample_size)
        if not wikidata_data or wikidata_data.get('count', 0) == 0:
            return {
                'success': False,
                'error': 'Failed to fetch Wikidata sample'
            }
        
        logger.info(f"获取到 {wikidata_data.get('count', 0)} 个实体")
        
        # 3. 转换为RDF和Datalog facts
        data_dir = Path(output_dir) / "facts"
        data_dir.mkdir(parents=True, exist_ok=True)
        
        # 保存为RDF Turtle格式
        rdf_file = Path(output_dir) / f"wikidata_{entity_type}.ttl"
        self.wikidata_client.convert_to_rdf_turtle(wikidata_data, str(rdf_file))
        
        # 转换为Datalog facts
        self.wikidata_client.convert_to_datalog_facts(wikidata_data, str(data_dir))
        
        # 4. 运行Soufflé验证
        logger.info("运行Soufflé验证...")
        program_file = conversion_result['program_file']
        run_result = self.runner.run_souffle_program(
            program_file, str(data_dir), output_dir, profile=profile
        )
        
        # 5. 分析违规
        violation_analysis = self.runner.analyze_violations(output_dir)
        
        # 6. 运行pySHACL对比（可选）
        pyshacl_result = None
        if rdf_file.exists():
            try:
                logger.info("运行pySHACL验证进行对比...")
                pyshacl_result = self.pyshacl_validator.validate_data(
                    shacl_file, str(rdf_file)
                )
            except Exception as e:
                logger.warning(f"pySHACL验证失败: {e}")
        
        # 7. 合并结果
        result = {
            **conversion_result,
            **run_result,
            'wikidata_stats': {
                'entity_type': entity_type,
                'sample_size': wikidata_data.get('count', 0),
                'entities_fetched': len(wikidata_data.get('entities', [])),
                'rdf_file': str(rdf_file),
                'facts_dir': str(data_dir)
            },
            'violation_analysis': violation_analysis
        }
        
        if pyshacl_result:
            result['pyshacl_comparison'] = self._compare_validation_results(
                run_result, pyshacl_result, violation_analysis
            )
        
        return result
    
    def _compare_validation_results(self, souffle_result: Dict, pyshacl_result: Dict,
                                   violation_analysis: Dict) -> Dict:
        """比较Soufflé和pySHACL的验证结果"""
        comparison = {
            'souffle_violations': souffle_result.get('violations_count', 0),
            'pyshacl_violations': pyshacl_result['validation']['violations_count'],
            'souffle_time': souffle_result.get('performance', {}).get('execution_time', 0),
            'pyshacl_time': pyshacl_result['performance']['execution_time'],
            'souffle_memory': souffle_result.get('performance', {}).get('memory_used_mb', 0),
            'pyshacl_memory': pyshacl_result['performance']['memory_used_mb']
        }
        
        # 计算加速比和内存效率
        if comparison['pyshacl_time'] > 0:
            comparison['speedup'] = comparison['pyshacl_time'] / comparison['souffle_time']
        else:
            comparison['speedup'] = 0
        
        if comparison['pyshacl_memory'] > 0:
            comparison['memory_efficiency'] = comparison['pyshacl_memory'] / comparison['souffle_memory']
        else:
            comparison['memory_efficiency'] = 0
        
        # 检查结果一致性
        comparison['results_consistent'] = abs(comparison['souffle_violations'] - 
                                              comparison['pyshacl_violations']) <= 5
        
        # 添加违规类型比较
        if 'by_constraint' in violation_analysis:
            comparison['violation_types'] = violation_analysis['by_constraint']
        
        return comparison
    
    def generate_validation_report(self, validation_result: Dict[str, Any], 
                                 output_file: str = None) -> str:
        """生成详细的验证报告 - 增强版"""
        report_lines = [
            "# SHACL验证报告",
            f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "## 1. 转换统计",
            f"- SHACL文件: {validation_result.get('stats', {}).get('input_file', 'N/A')}",
            f"- Shape数量: {validation_result.get('parser_stats', {}).get('shapes_count', 0)}",
            f"- 属性约束: {validation_result.get('parser_stats', {}).get('total_properties', 0)}",
            f"- 生成规则: {validation_result.get('generator_stats', {}).get('rules_count', 0)}",
            f"- 声明数量: {validation_result.get('generator_stats', {}).get('declarations_count', 0)}",
            f"- 优化: {'是' if validation_result.get('stats', {}).get('optimized') else '否'}",
            ""
        ]
        
        # 验证结果
        if validation_result.get('success'):
            report_lines.extend([
                "## 2. 验证结果",
                "✅ 验证成功完成",
                f"- 输出目录: {validation_result.get('output_dir', 'output')}",
                f"- 发现违规: {validation_result.get('violations_count', 0)}",
                ""
            ])
            
            # 违规分析
            if 'violation_analysis' in validation_result:
                analysis = validation_result['violation_analysis']
                report_lines.extend([
                    "### 违规分析",
                    f"- 总违规数: {analysis.get('total', 0)}",
                    "",
                    "#### 按约束类型:",
                ])
                for constraint, count in analysis.get('by_constraint', {}).items():
                    report_lines.append(f"  - {constraint}: {count}")
                report_lines.append("")
        else:
            report_lines.extend([
                "## 2. 验证结果",
                "❌ 验证失败",
                f"- 错误信息: {validation_result.get('error', '未知错误')}",
                ""
            ])
        
        # 性能数据
        if 'performance' in validation_result:
            perf = validation_result['performance']
            report_lines.extend([
                "## 3. 性能指标",
                f"- 执行时间: {perf.get('execution_time', 0):.3f} 秒",
                f"- 内存使用: {perf.get('memory_used_mb', 0):.2f} MB",
                f"- 违规数量: {perf.get('violations_count', 0)}",
                ""
            ])
        
        # Wikidata统计
        if 'wikidata_stats' in validation_result:
            ws = validation_result['wikidata_stats']
            report_lines.extend([
                "## 4. Wikidata数据统计",
                f"- 实体类型: {ws['entity_type']}",
                f"- 请求样本: {ws['sample_size']}",
                f"- 获取实体: {ws['entities_fetched']}",
                f"- RDF文件: {ws['rdf_file']}",
                f"- Facts目录: {ws['facts_dir']}",
                ""
            ])
        
        # pySHACL对比
        if 'pyshacl_comparison' in validation_result:
            comp = validation_result['pyshacl_comparison']
            report_lines.extend([
                "## 5. 与pySHACL对比",
                "",
                "### 违规数量",
                f"- Soufflé: {comp['souffle_violations']}",
                f"- pySHACL: {comp['pyshacl_violations']}",
                f"- 结果一致: {'✅ 是' if comp['results_consistent'] else '❌ 否'}",
                "",
                "### 性能对比",
                f"- Soufflé时间: {comp['souffle_time']:.3f} 秒",
                f"- pySHACL时间: {comp['pyshacl_time']:.3f} 秒",
                f"- **加速比: {comp['speedup']:.2f}x**",
                "",
                f"- Soufflé内存: {comp['souffle_memory']:.2f} MB",
                f"- pySHACL内存: {comp['pyshacl_memory']:.2f} MB",
                f"- **内存效率: {comp['memory_efficiency']:.2f}x**",
                ""
            ])
            
            if 'violation_types' in comp:
                report_lines.extend([
                    "### 违规类型分布",
                ])
                for vtype, count in comp['violation_types'].items():
                    report_lines.append(f"- {vtype}: {count}")
                report_lines.append("")
        
        # 约束类型统计
        if 'constraint_types' in validation_result.get('parser_stats', {}):
            ct = validation_result['parser_stats']['constraint_types']
            report_lines.extend([
                "## 6. 约束类型分布",
                *[f"- {k}: {v}" for k, v in sorted(ct.items())],
                ""
            ])
        
        # 建议和总结
        report_lines.extend([
            "## 7. 总结",
            "",
            self._generate_summary(validation_result),
            ""
        ])
        
        report_content = "\n".join(report_lines)
        
        # 保存报告
        if output_file:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(report_content)
            logger.info(f"验证报告已保存到: {output_file}")
        
        return report_content
    
    def _generate_summary(self, result: Dict) -> str:
        """生成验证总结"""
        summary_parts = []
        
        if result.get('success'):
            violations = result.get('violations_count', 0)
            if violations == 0:
                summary_parts.append("✅ 数据完全符合SHACL约束")
            else:
                summary_parts.append(f"⚠️ 发现 {violations} 个违规需要处理")
            
            if 'pyshacl_comparison' in result:
                comp = result['pyshacl_comparison']
                if comp['speedup'] > 1:
                    summary_parts.append(f"🚀 Soufflé比pySHACL快 {comp['speedup']:.1f} 倍")
                if comp['memory_efficiency'] < 1:
                    summary_parts.append(f"💾 Soufflé内存使用更少")
        else:
            summary_parts.append("❌ 验证过程出现错误，请检查日志")
        
        return " | ".join(summary_parts)
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取转换器的统计信息"""
        return {
            'parser_stats': self.parser.get_statistics(),
            'generator_stats': self.generator.get_statistics(),
            'conversion_stats': self.conversion_stats
        }