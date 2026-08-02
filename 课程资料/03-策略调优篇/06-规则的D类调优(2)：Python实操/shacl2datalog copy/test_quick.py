# test_quick.py - 创建这个文件来快速测试
#!/usr/bin/env python3
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from src.converter import SHACLToSouffleConverter

# 创建简单的测试SHACL
test_shacl = """
@prefix sh: <http://www.w3.org/ns/shacl#> .
@prefix ex: <http://example.org/> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .

ex:PersonShape a sh:NodeShape ;
    sh:targetClass ex:Person ;
    sh:property [
        sh:path ex:name ;
        sh:minCount 1 ;
        sh:datatype xsd:string ;
    ] .
"""

# 保存测试文件
Path("examples").mkdir(exist_ok=True)
with open("examples/test.ttl", "w") as f:
    f.write(test_shacl)

# 测试转换
converter = SHACLToSouffleConverter()
result = converter.convert_file("examples/test.ttl")

if result['success']:
    print("✅ 转换成功!")
    print("生成的Datalog程序：")
    print(result['program'][:500])  # 只打印前500字符
else:
    print(f"❌ 转换失败: {result.get('error')}")