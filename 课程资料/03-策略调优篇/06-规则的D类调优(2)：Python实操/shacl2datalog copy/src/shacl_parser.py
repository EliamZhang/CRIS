#!/usr/bin/env python3
"""
增强的SHACL解析器 - 支持完整的SHACL Core约束
"""

from typing import Dict, List, Optional, Set, Tuple, Any, Union
from dataclasses import dataclass, field
import logging
from rdflib import Graph, Namespace, URIRef, Literal, BNode
from rdflib.namespace import SH, XSD, RDF, RDFS

logger = logging.getLogger(__name__)

@dataclass
class PropertyConstraint:
    """完整的属性约束类"""
    path: str
    # Cardinality constraints
    min_count: Optional[int] = None
    max_count: Optional[int] = None
    # Value type constraints
    datatype: Optional[str] = None
    node_kind: Optional[str] = None
    # Value range constraints
    min_inclusive: Optional[float] = None
    max_inclusive: Optional[float] = None
    min_exclusive: Optional[float] = None
    max_exclusive: Optional[float] = None
    # String constraints
    min_length: Optional[int] = None
    max_length: Optional[int] = None
    pattern: Optional[str] = None
    flags: Optional[str] = None
    language_in: Optional[List[str]] = None
    unique_lang: bool = False
    # Logical constraints
    in_values: List[str] = field(default_factory=list)
    has_value: Optional[str] = None
    # Property pair constraints
    equals: Optional[str] = None
    disjoint: Optional[str] = None
    less_than: Optional[str] = None
    less_than_or_equals: Optional[str] = None
    # Shape-based constraints
    class_constraint: Optional[str] = None
    node_shape: Optional[str] = None
    property_shape: Optional[str] = None
    not_constraint: Optional[str] = None
    and_constraints: List[str] = field(default_factory=list)
    or_constraints: List[str] = field(default_factory=list)
    xone_constraints: List[str] = field(default_factory=list)
    # Qualified shapes
    qualified_value_shape: Optional[str] = None
    qualified_min_count: Optional[int] = None
    qualified_max_count: Optional[int] = None
    qualified_value_shapes_disjoint: bool = False
    # Closed shapes
    closed: bool = False
    ignored_properties: List[str] = field(default_factory=list)
    # Other
    name: Optional[str] = None
    description: Optional[str] = None
    message: Optional[str] = None
    severity: Optional[str] = None
    deactivated: bool = False
    group: Optional[str] = None
    order: Optional[float] = None
    default_value: Optional[str] = None

@dataclass
class NodeShape:
    """完整的节点形状类"""
    uri: str
    # Targets
    target_class: Optional[str] = None
    target_node: List[str] = field(default_factory=list)
    target_subjects_of: List[str] = field(default_factory=list)
    target_objects_of: List[str] = field(default_factory=list)
    # Properties
    properties: List[PropertyConstraint] = field(default_factory=list)
    # Logical constraints
    not_constraint: Optional[str] = None
    and_constraints: List[str] = field(default_factory=list)
    or_constraints: List[str] = field(default_factory=list)
    xone_constraints: List[str] = field(default_factory=list)
    # Closed shapes
    closed: bool = False
    ignored_properties: List[str] = field(default_factory=list)
    # Other
    name: Optional[str] = None
    description: Optional[str] = None
    message: Optional[str] = None
    severity: Optional[str] = None
    deactivated: bool = False
    property_shapes: List[PropertyConstraint] = field(default_factory=list)

class SHACLParser:
    """增强的SHACL解析器，支持所有Core约束"""
    
    def __init__(self):
        self.shapes: List[NodeShape] = []
        self.property_shapes: Dict[str, PropertyConstraint] = {}
        self.prefixes: Dict[str, str] = {}
        self.statistics: Dict[str, Any] = {}
        self.graph: Optional[Graph] = None
        
    def parse_shacl_file(self, file_path: str) -> List[NodeShape]:
        """解析SHACL文件并提取所有形状"""
        logger.info(f"Parsing SHACL file: {file_path}")
        
        graph = Graph()
        graph.parse(file_path, format="turtle")
        
        return self.parse_shacl_graph(graph)
    
    def parse_shacl_graph(self, graph: Graph) -> List[NodeShape]:
        """解析SHACL图并提取形状"""
        self.graph = graph
        shapes = []
        
        # 提取前缀
        self._extract_prefixes(graph)
        
        # 查找所有NodeShapes
        shape_subjects = set()
        for s in graph.subjects(RDF.type, SH.NodeShape):
            shape_subjects.add(s)
        
        # 同时查找隐式的NodeShapes（有sh:targetClass但没有显式类型的）
        for s in graph.subjects(SH.targetClass, None):
            shape_subjects.add(s)
        
        # 解析PropertyShapes（可能被引用）
        for s in graph.subjects(RDF.type, SH.PropertyShape):
            prop_shape = self._parse_property_shape(graph, s)
            if prop_shape:
                self.property_shapes[str(s)] = prop_shape
        
        # 解析每个NodeShape
        for shape_uri in shape_subjects:
            shape = self._parse_node_shape(graph, shape_uri)
            if shape and not shape.deactivated:
                shapes.append(shape)
                logger.info(f"Parsed shape: {shape.uri}")
        
        self.shapes = shapes
        self._collect_statistics()
        logger.info(f"Total shapes parsed: {len(shapes)}")
        
        return shapes
    
    def _extract_prefixes(self, graph: Graph):
        """提取命名空间前缀"""
        for prefix, namespace in graph.namespaces():
            if prefix:
                self.prefixes[prefix] = str(namespace)
    
    def _parse_node_shape(self, graph: Graph, shape_uri: URIRef) -> Optional[NodeShape]:
        """解析单个节点形状"""
        shape = NodeShape(uri=str(shape_uri))
        
        # 检查是否停用
        for obj in graph.objects(shape_uri, SH.deactivated):
            if self._parse_boolean(obj):
                shape.deactivated = True
                return shape
        
        # 解析目标
        for obj in graph.objects(shape_uri, SH.targetClass):
            shape.target_class = str(obj)
            
        for obj in graph.objects(shape_uri, SH.targetNode):
            shape.target_node.append(str(obj))
            
        for obj in graph.objects(shape_uri, SH.targetSubjectsOf):
            shape.target_subjects_of.append(str(obj))
            
        for obj in graph.objects(shape_uri, SH.targetObjectsOf):
            shape.target_objects_of.append(str(obj))
        
        # 解析元数据
        for obj in graph.objects(shape_uri, SH.name):
            shape.name = str(obj)
        for obj in graph.objects(shape_uri, SH.description):
            shape.description = str(obj)
        for obj in graph.objects(shape_uri, SH.message):
            shape.message = str(obj)
        for obj in graph.objects(shape_uri, SH.severity):
            shape.severity = str(obj)
        
        # 解析closed和ignoredProperties
        for obj in graph.objects(shape_uri, SH.closed):
            shape.closed = self._parse_boolean(obj)
        for obj in graph.objects(shape_uri, SH.ignoredProperties):
            ignored = self._parse_rdf_list(graph, obj)
            shape.ignored_properties.extend(ignored)
        
        # 解析逻辑约束
        for obj in graph.objects(shape_uri, SH['not']):
            shape.not_constraint = str(obj)
        for obj in graph.objects(shape_uri, SH['and']):
            shape.and_constraints = self._parse_rdf_list(graph, obj)
        for obj in graph.objects(shape_uri, SH['or']):
            shape.or_constraints = self._parse_rdf_list(graph, obj)
        for obj in graph.objects(shape_uri, SH.xone):
            shape.xone_constraints = self._parse_rdf_list(graph, obj)
        
        # 解析属性约束
        for prop_node in graph.objects(shape_uri, SH.property):
            constraint = self._parse_property_constraint(graph, prop_node)
            if constraint:
                shape.properties.append(constraint)
        
        # 也检查直接在形状上的属性约束
        direct_constraint = self._parse_property_constraint(graph, shape_uri, is_direct=True)
        if direct_constraint and direct_constraint.path:
            shape.properties.append(direct_constraint)
        
        return shape
    
    def _parse_property_shape(self, graph: Graph, prop_uri: URIRef) -> Optional[PropertyConstraint]:
        """解析PropertyShape"""
        return self._parse_property_constraint(graph, prop_uri)
    
    def _parse_property_constraint(self, graph: Graph, prop_node: URIRef, 
                                  is_direct: bool = False) -> Optional[PropertyConstraint]:
        """解析属性约束 - 完整版本"""
        # 获取路径
        path = None
        for obj in graph.objects(prop_node, SH.path):
            path = str(obj)
            break
        
        if not path and not is_direct:
            return None
        
        constraint = PropertyConstraint(path=path if path else "")
        
        # 解析所有约束参数
        constraint_mappings = {
            # Cardinality
            SH.minCount: ('min_count', int),
            SH.maxCount: ('max_count', int),
            # Types
            SH.datatype: ('datatype', str),
            SH.nodeKind: ('node_kind', str),
            # Ranges
            SH.minInclusive: ('min_inclusive', float),
            SH.maxInclusive: ('max_inclusive', float),
            SH.minExclusive: ('min_exclusive', float),
            SH.maxExclusive: ('max_exclusive', float),
            # Strings
            SH.minLength: ('min_length', int),
            SH.maxLength: ('max_length', int),
            SH.pattern: ('pattern', str),
            SH.flags: ('flags', str),
            SH.uniqueLang: ('unique_lang', bool),
            # Values
            SH.hasValue: ('has_value', str),
            # Property pairs
            SH.equals: ('equals', str),
            SH.disjoint: ('disjoint', str),
            SH.lessThan: ('less_than', str),
            SH.lessThanOrEquals: ('less_than_or_equals', str),
            # Shapes
            SH['class']: ('class_constraint', str),
            SH.node: ('node_shape', str),
            SH.property: ('property_shape', str),
            SH['not']: ('not_constraint', str),
            # Qualified
            SH.qualifiedValueShape: ('qualified_value_shape', str),
            SH.qualifiedMinCount: ('qualified_min_count', int),
            SH.qualifiedMaxCount: ('qualified_max_count', int),
            SH.qualifiedValueShapesDisjoint: ('qualified_value_shapes_disjoint', bool),
            # Other
            SH.name: ('name', str),
            SH.description: ('description', str),
            SH.message: ('message', str),
            SH.severity: ('severity', str),
            SH.deactivated: ('deactivated', bool),
            SH.group: ('group', str),
            SH.order: ('order', float),
            SH.defaultValue: ('default_value', str),
        }
        
        # 处理标准约束
        for pred, obj in graph.predicate_objects(prop_node):
            if pred in constraint_mappings:
                attr_name, attr_type = constraint_mappings[pred]
                try:
                    if attr_type == int:
                        setattr(constraint, attr_name, int(obj))
                    elif attr_type == float:
                        setattr(constraint, attr_name, float(obj))
                    elif attr_type == bool:
                        setattr(constraint, attr_name, self._parse_boolean(obj))
                    else:
                        setattr(constraint, attr_name, str(obj))
                except (ValueError, TypeError) as e:
                    logger.warning(f"Error parsing {attr_name}: {e}")
                    if attr_type != bool:
                        setattr(constraint, attr_name, str(obj))
        
        # 解析列表值约束
        for obj in graph.objects(prop_node, SH['in']):
            constraint.in_values = self._parse_value_list(graph, obj)
        
        for obj in graph.objects(prop_node, SH.languageIn):
            constraint.language_in = self._parse_rdf_list(graph, obj)
        
        # 解析逻辑约束列表
        for obj in graph.objects(prop_node, SH['and']):
            constraint.and_constraints = self._parse_rdf_list(graph, obj)
        for obj in graph.objects(prop_node, SH['or']):
            constraint.or_constraints = self._parse_rdf_list(graph, obj)
        for obj in graph.objects(prop_node, SH.xone):
            constraint.xone_constraints = self._parse_rdf_list(graph, obj)
        
        # 解析closed
        for obj in graph.objects(prop_node, SH.closed):
            constraint.closed = self._parse_boolean(obj)
        
        # 解析ignoredProperties
        for obj in graph.objects(prop_node, SH.ignoredProperties):
            constraint.ignored_properties = self._parse_rdf_list(graph, obj)
        
        return constraint if (constraint.path or is_direct) else None
    
    def _parse_rdf_list(self, graph: Graph, list_node) -> List[str]:
        """解析RDF列表"""
        result = []
        current = list_node
        
        while current and current != RDF.nil:
            first = None
            for obj in graph.objects(current, RDF.first):
                first = str(obj)
                break
            if first:
                result.append(first)
            
            # 获取列表的剩余部分
            next_node = None
            for obj in graph.objects(current, RDF.rest):
                next_node = obj
                break
            
            current = next_node
        
        return result
    
    def _parse_value_list(self, graph: Graph, list_node) -> List[str]:
        """解析值列表（可能包含字面量和URI）"""
        result = []
        current = list_node
        
        while current and current != RDF.nil:
            first = None
            for obj in graph.objects(current, RDF.first):
                if isinstance(obj, Literal):
                    first = str(obj)
                else:
                    first = str(obj)
                break
            if first:
                result.append(first)
            
            # 获取列表的剩余部分
            next_node = None
            for obj in graph.objects(current, RDF.rest):
                next_node = obj
                break
            
            current = next_node
        
        return result
    
    def _parse_boolean(self, obj) -> bool:
        """解析布尔值"""
        if isinstance(obj, Literal):
            return str(obj).lower() in ['true', '1', 'yes']
        return str(obj).lower() in ['true', '1', 'yes']
    
    def _collect_statistics(self):
        """收集解析统计信息"""
        total_properties = sum(len(shape.properties) for shape in self.shapes)
        
        # 统计约束类型
        constraint_types = {}
        for shape in self.shapes:
            # 统计形状级约束
            if shape.closed:
                constraint_types['closed'] = constraint_types.get('closed', 0) + 1
            if shape.not_constraint:
                constraint_types['not'] = constraint_types.get('not', 0) + 1
            if shape.and_constraints:
                constraint_types['and'] = constraint_types.get('and', 0) + 1
            if shape.or_constraints:
                constraint_types['or'] = constraint_types.get('or', 0) + 1
            if shape.xone_constraints:
                constraint_types['xone'] = constraint_types.get('xone', 0) + 1
            
            # 统计属性约束
            for prop in shape.properties:
                if prop.min_count is not None:
                    constraint_types['minCount'] = constraint_types.get('minCount', 0) + 1
                if prop.max_count is not None:
                    constraint_types['maxCount'] = constraint_types.get('maxCount', 0) + 1
                if prop.datatype:
                    constraint_types['datatype'] = constraint_types.get('datatype', 0) + 1
                if prop.pattern:
                    constraint_types['pattern'] = constraint_types.get('pattern', 0) + 1
                if prop.min_inclusive is not None:
                    constraint_types['minInclusive'] = constraint_types.get('minInclusive', 0) + 1
                if prop.max_inclusive is not None:
                    constraint_types['maxInclusive'] = constraint_types.get('maxInclusive', 0) + 1
                if prop.min_exclusive is not None:
                    constraint_types['minExclusive'] = constraint_types.get('minExclusive', 0) + 1
                if prop.max_exclusive is not None:
                    constraint_types['maxExclusive'] = constraint_types.get('maxExclusive', 0) + 1
                if prop.min_length is not None:
                    constraint_types['minLength'] = constraint_types.get('minLength', 0) + 1
                if prop.max_length is not None:
                    constraint_types['maxLength'] = constraint_types.get('maxLength', 0) + 1
                if prop.node_kind:
                    constraint_types['nodeKind'] = constraint_types.get('nodeKind', 0) + 1
                if prop.has_value:
                    constraint_types['hasValue'] = constraint_types.get('hasValue', 0) + 1
                if prop.equals:
                    constraint_types['equals'] = constraint_types.get('equals', 0) + 1
                if prop.disjoint:
                    constraint_types['disjoint'] = constraint_types.get('disjoint', 0) + 1
                if prop.less_than:
                    constraint_types['lessThan'] = constraint_types.get('lessThan', 0) + 1
                if prop.less_than_or_equals:
                    constraint_types['lessThanOrEquals'] = constraint_types.get('lessThanOrEquals', 0) + 1
                if prop.in_values:
                    constraint_types['in'] = constraint_types.get('in', 0) + 1
                if prop.class_constraint:
                    constraint_types['class'] = constraint_types.get('class', 0) + 1
                if prop.node_shape:
                    constraint_types['node'] = constraint_types.get('node', 0) + 1
                if prop.language_in:
                    constraint_types['languageIn'] = constraint_types.get('languageIn', 0) + 1
                if prop.unique_lang:
                    constraint_types['uniqueLang'] = constraint_types.get('uniqueLang', 0) + 1
                if prop.qualified_value_shape:
                    constraint_types['qualifiedShape'] = constraint_types.get('qualifiedShape', 0) + 1
                if prop.not_constraint:
                    constraint_types['not'] = constraint_types.get('not', 0) + 1
                if prop.and_constraints:
                    constraint_types['and'] = constraint_types.get('and', 0) + 1
                if prop.or_constraints:
                    constraint_types['or'] = constraint_types.get('or', 0) + 1
                if prop.xone_constraints:
                    constraint_types['xone'] = constraint_types.get('xone', 0) + 1
        
        self.statistics = {
            'shapes_count': len(self.shapes),
            'property_shapes_count': len(self.property_shapes),
            'total_properties': total_properties,
            'prefixes_count': len(self.prefixes),
            'constraint_types': constraint_types,
            'target_classes': len(set(s.target_class for s in self.shapes if s.target_class)),
            'closed_shapes': sum(1 for s in self.shapes if s.closed),
            'deactivated_shapes': sum(1 for s in self.shapes if s.deactivated)
        }
    
    def get_statistics(self) -> Dict:
        """获取解析统计信息"""
        return self.statistics
    
    def get_shape_by_uri(self, uri: str) -> Optional[NodeShape]:
        """根据URI获取形状"""
        for shape in self.shapes:
            if shape.uri == uri:
                return shape
        return None
    
    def get_property_shape_by_uri(self, uri: str) -> Optional[PropertyConstraint]:
        """根据URI获取属性形状"""
        return self.property_shapes.get(uri)