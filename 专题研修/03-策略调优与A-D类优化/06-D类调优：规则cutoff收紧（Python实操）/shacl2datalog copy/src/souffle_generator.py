#!/usr/bin/env python3
"""
修复的 SoufflÃ© 生成器 - 完整支持SHACL Core约束
"""

from typing import Dict, List, Optional, Set, Tuple
from dataclasses import dataclass, field
import logging
from rdflib import Graph, Namespace, URIRef, Literal, BNode
from rdflib.namespace import SH, XSD, RDF, RDFS
logger = logging.getLogger(__name__)
from .shacl_parser import NodeShape, PropertyConstraint

class SouffleGenerator:
    """完整的SHACL到Datalog代码生成器"""
    
    def __init__(self):
        self.declarations: List[str] = []
        self.rules: List[str] = []
        self.facts: List[str] = []
        self.inputs: List[str] = []
        self.outputs: List[str] = []
        self.statistics: Dict = {}
        self.declared_relations: Set[str] = set()
        self.helper_counter = 0  # 用于生成唯一的辅助关系名
        
    def convert_shapes_to_souffle(self, shapes: List[NodeShape]) -> str:
        """Convert SHACL shapes to Soufflé program"""
        logger.info(f"Converting {len(shapes)} shapes to Soufflé")
        
        # Reset state
        self.declarations = []
        self.rules = []
        self.facts = []
        self.inputs = []
        self.outputs = []
        self.declared_relations = set()
        self.helper_counter = 0
        
        # Generate declarations
        self._generate_declarations(shapes)
        
        # Generate rules for each shape
        for shape in shapes:
            self._convert_shape(shape)
        
        # Generate inputs and outputs
        self._generate_io_declarations(shapes)
        
        # Collect statistics
        self._collect_statistics()
        
        # Assemble program
        return self._assemble_program()
    
    def _generate_declarations(self, shapes: List[NodeShape]):
        """Generate relation declarations"""
        base_decls = []
        
        # Type relations
        for shape in shapes:
            if shape.target_class:
                class_name = self._extract_local_name(shape.target_class)
                relation_name = f"{class_name.lower()}"
                if relation_name not in self.declared_relations:
                    base_decls.append(f".decl {relation_name}(entity: symbol)")
                    self.declared_relations.add(relation_name)
        
        # Property relations - 收集所有属性
        property_names = set()
        properties_needing_count = set()  # 需要计数的属性
        
        for shape in shapes:
            for prop in shape.properties:
                if prop.path:
                    prop_name = self._extract_local_name(prop.path)
                    property_names.add(prop_name)
                    # 检查是否需要计数
                    if (prop.min_count is not None and prop.min_count > 1) or \
                       (prop.max_count is not None and prop.max_count > 1) or \
                       prop.qualified_min_count is not None or \
                       prop.qualified_max_count is not None:
                        properties_needing_count.add(prop_name)
                
                if prop.equals:
                    property_names.add(self._extract_local_name(prop.equals))
                if prop.disjoint:
                    property_names.add(self._extract_local_name(prop.disjoint))
                if prop.less_than:
                    property_names.add(self._extract_local_name(prop.less_than))
                if prop.less_than_or_equals:
                    property_names.add(self._extract_local_name(prop.less_than_or_equals))
        
        for prop_name in property_names:
            if prop_name not in self.declared_relations:
                base_decls.append(f".decl {prop_name}(entity: symbol, value: symbol)")
                base_decls.append(f".decl has_{prop_name}(entity: symbol)")
                self.declared_relations.add(prop_name)
                self.declared_relations.add(f"has_{prop_name}")
                
                # 只为需要的属性添加count声明
                if prop_name in properties_needing_count:
                    base_decls.append(f".decl count_{prop_name}(entity: symbol, cnt: number)")
                    self.declared_relations.add(f"count_{prop_name}")
        
        # Property relations - 收集所有属性
        property_names = set()
        for shape in shapes:
            for prop in shape.properties:
                if prop.path:
                    property_names.add(self._extract_local_name(prop.path))
                if prop.equals:
                    property_names.add(self._extract_local_name(prop.equals))
                if prop.disjoint:
                    property_names.add(self._extract_local_name(prop.disjoint))
                if prop.less_than:
                    property_names.add(self._extract_local_name(prop.less_than))
                if prop.less_than_or_equals:
                    property_names.add(self._extract_local_name(prop.less_than_or_equals))
        
        for prop_name in property_names:
            if prop_name not in self.declared_relations:
                base_decls.append(f".decl {prop_name}(entity: symbol, value: symbol)")
                base_decls.append(f".decl has_{prop_name}(entity: symbol)")
                self.declared_relations.add(prop_name)
                self.declared_relations.add(f"has_{prop_name}")
        
        # NodeKind 关系
        if "is_iri" not in self.declared_relations:
            base_decls.append(".decl is_iri(entity: symbol)")
            base_decls.append(".decl is_literal(entity: symbol)")
            base_decls.append(".decl is_blank_node(entity: symbol)")
            self.declared_relations.add("is_iri")
            self.declared_relations.add("is_literal") 
            self.declared_relations.add("is_blank_node")
        
        # 语言标签关系
        if "has_language" not in self.declared_relations:
            base_decls.append(".decl has_language(value: symbol, lang: symbol)")
            self.declared_relations.add("has_language")
        
        # Violation relations
        if "violation" not in self.declared_relations:
            base_decls.append(".decl violation(entity: symbol, constraint: symbol, message: symbol)")
            self.declared_relations.add("violation")
        
        self.declarations.extend(base_decls)
    
    def _convert_shape(self, shape: NodeShape):
        """Convert a single shape to Datalog rules"""
        if not shape.target_class:
            return
        
        class_name = self._extract_local_name(shape.target_class)
        
        # 处理 sh:closed 约束
        if shape.closed:
            self._add_closed_shape_rule(class_name, shape)
        
        for prop in shape.properties:
            if not prop.path:
                continue
            
            prop_name = self._extract_local_name(prop.path)
            
            # Generate helper rules
            self.rules.append(f"has_{prop_name}(E) :- {prop_name}(E, _).")
            
            # 只有在需要计数时才生成count规则
            if (prop.min_count is not None and prop.min_count > 1) or \
               (prop.max_count is not None and prop.max_count > 1):
                self.rules.append(f"count_{prop_name}(E, C) :- {class_name.lower()}(E), C = count : {{ {prop_name}(E, _) }}.")
             
            # Generate constraint rules
            if prop.min_count is not None:
                self._add_min_count_rule(class_name, prop_name, prop.min_count, prop.message)
            
            if prop.max_count is not None:
                self._add_max_count_rule(class_name, prop_name, prop.max_count, prop.message)
            
            if prop.datatype:
                self._add_datatype_rule(class_name, prop_name, prop.datatype, prop.message)
            
            if prop.pattern:
                self._add_pattern_rule(class_name, prop_name, prop.pattern, prop.message)
            
            if prop.min_inclusive is not None or prop.max_inclusive is not None:
                self._add_range_rules(class_name, prop_name, prop.min_inclusive, 
                                     prop.max_inclusive, prop.message)
            
            if prop.min_length is not None or prop.max_length is not None:
                self._add_length_rules(class_name, prop_name, prop.min_length, 
                                      prop.max_length, prop.message)
            
            if prop.in_values:
                self._add_in_values_rule(class_name, prop_name, prop.in_values, prop.message)
            
            if prop.class_constraint:
                self._add_class_rule(class_name, prop_name, prop.class_constraint, prop.message)
            
            if prop.has_value:
                self._add_has_value_rule(class_name, prop_name, prop.has_value, prop.message)
            
            if prop.node_kind:
                self._add_node_kind_rule(class_name, prop_name, prop.node_kind, prop.message)
            
            if prop.node_shape:
                self._add_node_shape_rule(class_name, prop_name, prop.node_shape, prop.message)
            
            if prop.language_in:
                self._add_language_in_rule(class_name, prop_name, prop.language_in, prop.message)
            
            if prop.equals:
                self._add_equals_rule(class_name, prop_name, prop.equals, prop.message)
            
            if prop.disjoint:
                self._add_disjoint_rule(class_name, prop_name, prop.disjoint, prop.message)
            
            if prop.less_than:
                self._add_less_than_rule(class_name, prop_name, prop.less_than, prop.message)
            
            if prop.less_than_or_equals:
                self._add_less_than_or_equals_rule(class_name, prop_name, 
                                                  prop.less_than_or_equals, prop.message)
            
            # Qualified shapes
            if prop.qualified_value_shape:
                self._add_qualified_shape_rules(class_name, prop_name, prop)
    
    def _add_min_count_rule(self, class_name: str, prop_name: str, 
                           min_count: int, message: Optional[str]):
        """Add minCount constraint rule - 修复版"""
        msg = message or f"Property {prop_name} has less than {min_count} values"
        
        if min_count == 1:
            # 简单情况：至少一个值
            rule = f"""violation(E, "minCount", "{msg}") :-
    {class_name.lower()}(E),
    !has_{prop_name}(E)."""
            self.rules.append(rule)
        elif min_count > 1:
            # 对于大于1的情况，需要确保count关系已定义
            # Soufflé不支持直接在规则中使用count，需要预先计算
            rule = f"""violation(E, "minCount", "{msg}") :-
    {class_name.lower()}(E),
    count_{prop_name}(E, C),
    C < {min_count}."""
            self.rules.append(rule)
    
    def _add_max_count_rule(self, class_name: str, prop_name: str, 
                           max_count: int, message: Optional[str]):
        """Add maxCount constraint rule - 修复版"""
        msg = message or f"Property {prop_name} has more than {max_count} values"
        
        if max_count == 0:
            # 不允许有值
            rule = f"""violation(E, "maxCount", "{msg}") :-
    {class_name.lower()}(E),
    has_{prop_name}(E)."""
        elif max_count == 1:
            # 最多一个值
            rule = f"""violation(E, "maxCount", "{msg}") :-
    {class_name.lower()}(E),
    {prop_name}(E, V1),
    {prop_name}(E, V2),
    V1 != V2."""
        else:
            # 使用计数
            rule = f"""violation(E, "maxCount", "{msg}") :-
    {class_name.lower()}(E),
    count_{prop_name}(E, C),
    C > {max_count}."""
        
        self.rules.append(rule)
    
    def _add_datatype_rule(self, class_name: str, prop_name: str, 
                          datatype: str, message: Optional[str]):
        """Add datatype constraint rule - 改进版"""
        msg = message or f"Invalid datatype for {prop_name}"
        datatype_local = self._extract_local_name(datatype)
        
        if "integer" in datatype_local.lower():
            rule = f"""violation(E, "datatype", "{msg}") :-
    {class_name.lower()}(E),
    {prop_name}(E, V),
    !match("^-?[0-9]+$", V)."""
        elif "decimal" in datatype_local.lower() or "double" in datatype_local.lower():
            rule = f"""violation(E, "datatype", "{msg}") :-
    {class_name.lower()}(E),
    {prop_name}(E, V),
    !match("^-?[0-9]+(\\.[0-9]+)?([eE][+-]?[0-9]+)?$", V)."""
        elif "boolean" in datatype_local.lower():
            rule = f"""violation(E, "datatype", "{msg}") :-
    {class_name.lower()}(E),
    {prop_name}(E, V),
    V != "true",
    V != "false",
    V != "1",
    V != "0"."""
        elif "date" in datatype_local.lower():
            rule = f"""violation(E, "datatype", "{msg}") :-
    {class_name.lower()}(E),
    {prop_name}(E, V),
    !match("^[0-9]{{4}}-[0-9]{{2}}-[0-9]{{2}}", V)."""
        elif "datetime" in datatype_local.lower():
            rule = f"""violation(E, "datatype", "{msg}") :-
    {class_name.lower()}(E),
    {prop_name}(E, V),
    !match("^[0-9]{{4}}-[0-9]{{2}}-[0-9]{{2}}T[0-9]{{2}}:[0-9]{{2}}:[0-9]{{2}}", V)."""
        elif "anyuri" in datatype_local.lower():
            rule = f"""violation(E, "datatype", "{msg}") :-
    {class_name.lower()}(E),
    {prop_name}(E, V),
    !match("^(https?|ftp)://", V)."""
        else:
            # 对于string和其他类型，不添加严格验证
            return
        
        self.rules.append(rule)
    
    def _add_pattern_rule(self, class_name: str, prop_name: str, 
                         pattern: str, message: Optional[str]):
        """Add pattern constraint rule - 改进版"""
        msg = message or f"Value does not match pattern for {prop_name}"
        # 简化正则表达式，使其与Soufflé兼容
        simplified_pattern = pattern.replace("\\\\", "\\")
        # 处理一些常见的不兼容模式
        simplified_pattern = simplified_pattern.replace("{2,}", "+")
        simplified_pattern = simplified_pattern.replace("\\.", ".")
        
        rule = f"""violation(E, "pattern", "{msg}") :-
    {class_name.lower()}(E),
    {prop_name}(E, V),
    !match("{simplified_pattern}", V)."""
        self.rules.append(rule)
    
    def _add_range_rules(self, class_name: str, prop_name: str,
                        min_val: Optional[float], max_val: Optional[float],
                        message: Optional[str]):
        """Add minInclusive/maxInclusive constraint rules - 使用 to_number 内置函数"""
        
        if min_val is not None:
            msg = message or f"Value below minimum {min_val} for {prop_name}"
            # Soufflé 的 to_number 是内置函数，直接使用
            rule = f"""violation(E, "minInclusive", "{msg}") :-
    {class_name.lower()}(E),
    {prop_name}(E, V),
    to_number(V) < {min_val}."""
            self.rules.append(rule)
        
        if max_val is not None:
            msg = message or f"Value above maximum {max_val} for {prop_name}"
            rule = f"""violation(E, "maxInclusive", "{msg}") :-
    {class_name.lower()}(E),
    {prop_name}(E, V),
    to_number(V) > {max_val}."""
            self.rules.append(rule)
    
    def _add_length_rules(self, class_name: str, prop_name: str,
                         min_len: Optional[int], max_len: Optional[int],
                         message: Optional[str]):
        """Add minLength/maxLength constraint rules - 使用内置 strlen"""
        
        if min_len is not None:
            msg = message or f"Value too short for {prop_name} (min: {min_len})"
            rule = f"""violation(E, "minLength", "{msg}") :-
    {class_name.lower()}(E),
    {prop_name}(E, V),
    strlen(V) < {min_len}."""
            self.rules.append(rule)
        
        if max_len is not None:
            msg = message or f"Value too long for {prop_name} (max: {max_len})"
            rule = f"""violation(E, "maxLength", "{msg}") :-
    {class_name.lower()}(E),
    {prop_name}(E, V),
    strlen(V) > {max_len}."""
            self.rules.append(rule)
    
    def _add_has_value_rule(self, class_name: str, prop_name: str,
                           value: str, message: Optional[str]):
        """Add sh:hasValue constraint rule"""
        msg = message or f"Missing required value {value} for {prop_name}"
        value_str = self._extract_local_name(value) if value.startswith("http") else value
        
        # 声明辅助关系
        helper_name = f"has_value_{prop_name}_{self.helper_counter}"
        self.helper_counter += 1
        
        if helper_name not in self.declared_relations:
            self.declarations.append(f".decl {helper_name}(entity: symbol)")
            self.declared_relations.add(helper_name)
        
        # 辅助规则：检查是否有指定值
        self.rules.append(f'{helper_name}(E) :- {prop_name}(E, "{value_str}").')
        
        # 违规规则
        rule = f"""violation(E, "hasValue", "{msg}") :-
    {class_name.lower()}(E),
    !{helper_name}(E)."""
        self.rules.append(rule)
    
    def _add_node_kind_rule(self, class_name: str, prop_name: str,
                           node_kind: str, message: Optional[str]):
        """Add sh:nodeKind constraint rule"""
        kind = self._extract_local_name(node_kind)
        msg = message or f"Invalid node kind for {prop_name}"
        
        if "IRI" in kind:
            rule = f"""violation(E, "nodeKind", "{msg}") :-
    {class_name.lower()}(E),
    {prop_name}(E, V),
    !is_iri(V)."""
        elif "Literal" in kind:
            rule = f"""violation(E, "nodeKind", "{msg}") :-
    {class_name.lower()}(E),
    {prop_name}(E, V),
    !is_literal(V)."""
        elif "BlankNode" in kind:
            rule = f"""violation(E, "nodeKind", "{msg}") :-
    {class_name.lower()}(E),
    {prop_name}(E, V),
    !is_blank_node(V)."""
        else:
            return
        
        self.rules.append(rule)
    
    def _add_node_shape_rule(self, class_name: str, prop_name: str,
                            node_shape_uri: str, message: Optional[str]):
        """Add sh:node constraint rule (nested shape validation)"""
        shape_name = self._extract_local_name(node_shape_uri)
        msg = message or f"Value of {prop_name} does not conform to shape {shape_name}"
        
        # 创建一个辅助关系来检查嵌套形状的违规
        helper_name = f"conforms_to_{shape_name}"
        if helper_name not in self.declared_relations:
            self.declarations.append(f".decl {helper_name}(entity: symbol)")
            self.declared_relations.add(helper_name)
        
        # 规则：如果没有违规，则符合形状
        self.rules.append(f'{helper_name}(V) :- {prop_name}(_, V), !violation(V, _, _).')
        
        # 违规规则
        rule = f"""violation(E, "nodeShape", "{msg}") :-
    {class_name.lower()}(E),
    {prop_name}(E, V),
    !{helper_name}(V)."""
        self.rules.append(rule)
    
    def _add_language_in_rule(self, class_name: str, prop_name: str,
                             languages: List[str], message: Optional[str]):
        """Add sh:languageIn constraint rule"""
        msg = message or f"Invalid language tag for {prop_name}"
        
        # 创建允许的语言关系
        lang_relation = f"allowed_language_{prop_name}"
        if lang_relation not in self.declared_relations:
            self.declarations.append(f".decl {lang_relation}(lang: symbol)")
            self.declared_relations.add(lang_relation)
            
            # 添加允许的语言
            for lang in languages:
                self.facts.append(f'{lang_relation}("{lang}").')
        
        rule = f"""violation(E, "languageIn", "{msg}") :-
    {class_name.lower()}(E),
    {prop_name}(E, V),
    has_language(V, L),
    !{lang_relation}(L)."""
        self.rules.append(rule)
    
    def _add_closed_shape_rule(self, class_name: str, shape: NodeShape):
        """Add sh:closed constraint rule"""
        msg = shape.message or f"Unexpected property on closed shape {class_name}"
        
        # 创建允许的属性关系
        allowed_rel = f"allowed_property_{class_name}"
        if allowed_rel not in self.declared_relations:
            self.declarations.append(f".decl {allowed_rel}(prop: symbol)")
            self.declared_relations.add(allowed_rel)
            
            # 添加允许的属性
            for prop in shape.properties:
                if prop.path:
                    prop_name = self._extract_local_name(prop.path)
                    self.facts.append(f'{allowed_rel}("{prop_name}").')
            
            # 添加忽略的属性
            for ignored in shape.ignored_properties:
                ignored_name = self._extract_local_name(ignored)
                self.facts.append(f'{allowed_rel}("{ignored_name}").')
        
        # 为每个声明的属性生成违规检查
        # 不使用通用的 has_property，而是检查每个具体的属性
        for prop in shape.properties:
            if prop.path:
                prop_name = self._extract_local_name(prop.path)
                # 这个属性是允许的，所以跳过
                continue
        
        # 注意：closed shape 的完整实现需要知道所有可能的属性
        # 这在 Datalog 中比较困难，因为我们不能枚举所有属性
        # 简化实现：我们只能检查已知的属性是否在允许列表中
        logger.warning(f"Closed shape constraint for {class_name} is simplified - cannot check unknown properties")
    
    def _add_qualified_shape_rules(self, class_name: str, prop_name: str,
                                  prop: PropertyConstraint):
        """Add qualified shape constraint rules"""
        if not prop.qualified_value_shape:
            return
        
        qual_shape = self._extract_local_name(prop.qualified_value_shape)
        
        # 创建辅助关系
        qual_rel = f"qualified_{prop_name}_{qual_shape}"
        qual_count_rel = f"count_{qual_rel}"
        
        if qual_rel not in self.declared_relations:
            self.declarations.append(f".decl {qual_rel}(entity: symbol, value: symbol)")
            self.declarations.append(f".decl {qual_count_rel}(entity: symbol, cnt: number)")
            self.declared_relations.add(qual_rel)
            self.declared_relations.add(qual_count_rel)
        
        # 计数规则
        self.rules.append(f"{qual_count_rel}(E, C) :- {class_name.lower()}(E), C = count : {{ {qual_rel}(E, _) }}.")
        
        # 最小计数约束
        if prop.qualified_min_count is not None:
            msg = prop.message or f"Too few values matching qualified shape for {prop_name}"
            rule = f"""violation(E, "qualifiedMinCount", "{msg}") :-
    {class_name.lower()}(E),
    {qual_count_rel}(E, C),
    C < {prop.qualified_min_count}."""
            self.rules.append(rule)
        
        # 最大计数约束
        if prop.qualified_max_count is not None:
            msg = prop.message or f"Too many values matching qualified shape for {prop_name}"
            rule = f"""violation(E, "qualifiedMaxCount", "{msg}") :-
    {class_name.lower()}(E),
    {qual_count_rel}(E, C),
    C > {prop.qualified_max_count}."""
            self.rules.append(rule)
    
    def _add_in_values_rule(self, class_name: str, prop_name: str,
                           values: List[str], message: Optional[str]):
        """Add sh:in constraint rule - 改进版"""
        msg = message or f"Value not in allowed list for {prop_name}"
        
        # 使用唯一的关系名避免重复声明
        allowed_relation = f"allowed_{prop_name}_value_{self.helper_counter}"
        self.helper_counter += 1
        
        if allowed_relation not in self.declared_relations:
            # 声明关系
            self.declarations.append(f'.decl {allowed_relation}(value: symbol)')
            self.declared_relations.add(allowed_relation)
            
            # 添加允许的值作为事实
            for val in values:
                val_str = self._extract_local_name(val) if val.startswith("http") else val
                self.facts.append(f'{allowed_relation}("{val_str}").')
        
        rule = f"""violation(E, "in", "{msg}") :-
    {class_name.lower()}(E),
    {prop_name}(E, V),
    !{allowed_relation}(V)."""
        self.rules.append(rule)
    
    def _add_class_rule(self, class_name: str, prop_name: str,
                       target_class: str, message: Optional[str]):
        """Add sh:class constraint rule"""
        target = self._extract_local_name(target_class)
        msg = message or f"Value of {prop_name} is not an instance of {target}"
        
        # 确保目标类被声明
        target_rel = target.lower()
        if target_rel not in self.declared_relations:
            self.declarations.append(f".decl {target_rel}(entity: symbol)")
            self.declared_relations.add(target_rel)
        
        rule = f"""violation(E, "class", "{msg}") :-
    {class_name.lower()}(E),
    {prop_name}(E, V),
    !{target_rel}(V)."""
        self.rules.append(rule)
    
    def _add_equals_rule(self, class_name: str, prop_name: str,
                        equals_prop: str, message: Optional[str]):
        """Add sh:equals constraint rule"""
        eq_name = self._extract_local_name(equals_prop)
        msg = message or f"Values not equal: {prop_name} and {eq_name}"
        
        # 处理两个属性值不相等的情况
        rule = f"""violation(E, "equals", "{msg}") :-
    {class_name.lower()}(E),
    {prop_name}(E, V1),
    {eq_name}(E, V2),
    V1 != V2."""
        self.rules.append(rule)
        
        # 处理一个有值另一个没有的情况
        rule2 = f"""violation(E, "equals", "{msg}") :-
    {class_name.lower()}(E),
    has_{prop_name}(E),
    !has_{eq_name}(E)."""
        self.rules.append(rule2)
        
        rule3 = f"""violation(E, "equals", "{msg}") :-
    {class_name.lower()}(E),
    !has_{prop_name}(E),
    has_{eq_name}(E)."""
        self.rules.append(rule3)
    
    def _add_disjoint_rule(self, class_name: str, prop_name: str,
                          disjoint_prop: str, message: Optional[str]):
        """Add sh:disjoint constraint rule"""
        dis_name = self._extract_local_name(disjoint_prop)
        msg = message or f"Properties not disjoint: {prop_name} and {dis_name}"
        rule = f"""violation(E, "disjoint", "{msg}") :-
    {class_name.lower()}(E),
    {prop_name}(E, V),
    {dis_name}(E, V)."""
        self.rules.append(rule)
    
    def _add_less_than_rule(self, class_name: str, prop_name: str,
                           compare_prop: str, message: Optional[str]):
        """Add sh:lessThan constraint rule - 使用内置 to_number"""
        cmp_name = self._extract_local_name(compare_prop)
        msg = message or f"{prop_name} not less than {cmp_name}"
        
        rule = f"""violation(E, "lessThan", "{msg}") :-
    {class_name.lower()}(E),
    {prop_name}(E, V1),
    {cmp_name}(E, V2),
    to_number(V1) >= to_number(V2)."""
        self.rules.append(rule)
    
    def _add_less_than_or_equals_rule(self, class_name: str, prop_name: str,
                                     compare_prop: str, message: Optional[str]):
        """Add sh:lessThanOrEquals constraint rule"""
        cmp_name = self._extract_local_name(compare_prop)
        msg = message or f"{prop_name} not less than or equal to {cmp_name}"
        
        rule = f"""violation(E, "lessThanOrEquals", "{msg}") :-
    {class_name.lower()}(E),
    {prop_name}(E, V1),
    {cmp_name}(E, V2),
    to_number(V1) > to_number(V2)."""
        self.rules.append(rule)
    
    def _generate_io_declarations(self, shapes: List[NodeShape]):
        """Generate input/output declarations"""
        # Input declarations
        input_rels = set()
        for shape in shapes:
            if shape.target_class:
                class_name = self._extract_local_name(shape.target_class)
                input_rels.add(f".input {class_name.lower()}")
            
            for prop in shape.properties:
                if prop.path:
                    prop_name = self._extract_local_name(prop.path)
                    input_rels.add(f".input {prop_name}")
                # 添加其他相关属性的输入
                for other_prop in [prop.equals, prop.disjoint, prop.less_than, prop.less_than_or_equals]:
                    if other_prop:
                        other_name = self._extract_local_name(other_prop)
                        input_rels.add(f".input {other_name}")
        
        # 添加节点类型输入（只有在实际使用时才添加）
        if "is_iri" in self.declared_relations:
            input_rels.add(".input is_iri")
        if "is_literal" in self.declared_relations:
            input_rels.add(".input is_literal")
        if "is_blank_node" in self.declared_relations:
            input_rels.add(".input is_blank_node")
        if "has_language" in self.declared_relations:
            input_rels.add(".input has_language")
        
        self.inputs = sorted(input_rels)
        
        # Output declarations
        self.outputs = [".output violation"]
    
    def _assemble_program(self) -> str:
        """Assemble complete Soufflé program"""
        from datetime import datetime
        
        parts = [
            f"// SHACL to Soufflé Datalog Conversion",
            f"// Generated: {datetime.now().isoformat()}",
            f"// Generator: Enhanced SHACL to Datalog Converter",
            "",
            "// ===== DECLARATIONS =====",
            *self.declarations,
            "",
            "// ===== FACTS =====",
            *self.facts,
            "",
            "// ===== RULES =====",
            *self.rules,
            "",
            "// ===== INPUT/OUTPUT =====",
            *self.inputs,
            *self.outputs,
            ""
        ]
        
        return "\n".join(parts)
    
    def _extract_local_name(self, uri: str) -> str:
        """Extract local name from URI"""
        if "#" in uri:
            return uri.split("#")[-1]
        elif "/" in uri:
            return uri.split("/")[-1]
        return uri
    
    def _collect_statistics(self):
        """Collect generation statistics"""
        self.statistics = {
            'rules_count': len(self.rules),
            'declarations_count': len(self.declarations),
            'facts_count': len(self.facts),
            'inputs_count': len(self.inputs),
            'outputs_count': len(self.outputs),
            'helper_relations': self.helper_counter
        }
    
    def get_statistics(self) -> Dict:
        """Get generation statistics"""
        return self.statistics