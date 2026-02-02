#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试知识图谱引擎的核心功能
包括：
1. 生成课程蓝图
2. 扩展特定章节
3. 数据持久化
"""

import json
import os
import sys
from kg_engine import KGEngine, KGNode

def test_kg_engine():
    print("="*50)
    print("测试知识图谱引擎")
    print("="*50)
    
    # 1. 初始化引擎（应该加载现有数据）
    print("\n1. 初始化知识图谱引擎...")
    engine = KGEngine()
    print(f"   当前节点数量: {len(engine.nodes)}")
    
    # 2. 如果没有节点，生成蓝图
    if not engine.nodes:
        print("\n2. 生成课程蓝图...")
        course_info = "我想建设一门《人工智能导论》课程，面向计算机专业本科生"
        print(f"   课程信息: {course_info}")
        
        data = engine.generate_blueprint(course_info)
        nodes_info = data.get("nodes", []) if isinstance(data, dict) else data
        
        print(f"   生成的章节数量: {len(nodes_info)}")
        for i, node in enumerate(nodes_info):
            print(f"   {i+1}. {node['name']} (类型: {node['type']}, 层级: {node['level']})")
            # 添加到引擎
            kg_node = KGNode(node['name'], node['type'], node['level'])
            engine.add_node(kg_node)
        
        print(f"   引擎中节点数量: {len(engine.nodes)}")
    else:
        print("\n2. 使用现有数据继续测试")
    
    # 3. 显示当前节点
    print("\n3. 当前知识图谱节点:")
    for i, node in enumerate(engine.nodes):
        parent_name = node.parent.name if node.parent else "无"
        print(f"   {i+1}. {node.name} (类型: {node.node_type}, 层级: {node.level}, 父节点: {parent_name})")
    
    # 4. 测试扩展章节
    print("\n4. 测试扩展章节功能...")
    if engine.nodes:
        # 选择第一个章节进行扩展
        parent_node = engine.nodes[0]
        print(f"   扩展章节: {parent_node.name}")
        
        # 执行扩展
        context = "这是一门面向计算机专业本科生的人工智能导论课程"
        expanded_data = engine.expand_node(parent_node.name, context)
        expanded_nodes = expanded_data.get("nodes", []) if isinstance(expanded_data, dict) else expanded_data
        
        print(f"   扩展生成的节点数量: {len(expanded_nodes)}")
        for i, n in enumerate(expanded_nodes):
            # 确定层级（父节点层级+1）
            level = parent_node.level + 1
            
            # 创建新节点
            node = KGNode(n['name'], n.get('type', '知识点'), level, parent_node)
            
            # 添加分类和标签
            if 'classification' in n:
                node.classification = n['classification']
            if 'tags' in n:
                node.tags = n['tags']
            if 'pre_nodes' in n:
                node.pre_nodes = n['pre_nodes']
            if 'post_nodes' in n:
                node.post_nodes = n['post_nodes']
            if 'related_nodes' in n:
                node.related_nodes = n['related_nodes']
            if 'description' in n:
                node.description = n['description']
            
            # 添加到引擎
            engine.add_node(node)
            
            print(f"   {i+1}. {node.name} (类型: {node.node_type}, 层级: {node.level}, 分类: {node.classification}, 标签: {node.tags})")
        
        print(f"   扩展后引擎中节点总数: {len(engine.nodes)}")
    
    # 5. 验证数据持久化
    print("\n5. 验证数据持久化...")
    # 保存数据
    engine.save_to_file()
    print("   数据已保存到文件")
    
    # 检查文件是否存在
    if os.path.exists("kg_data.json"):
        print("   数据文件存在")
        with open("kg_data.json", "r", encoding="utf-8") as f:
            saved_data = json.load(f)
        print(f"   保存的节点数量: {len(saved_data)}")
    else:
        print("   数据文件不存在，持久化失败")
        return False
    
    # 6. 重新初始化引擎，验证加载功能
    print("\n6. 重新初始化引擎，验证数据加载...")
    new_engine = KGEngine()
    print(f"   重新加载后节点数量: {len(new_engine.nodes)}")
    
    if len(new_engine.nodes) == len(engine.nodes):
        print("   数据加载成功！")
    else:
        print("   数据加载失败！")
        return False
    
    # 7. 显示最终的知识结构
    print("\n7. 最终知识结构:")
    for i, node in enumerate(new_engine.nodes):
        parent_name = node.parent.name if node.parent else "无"
        print(f"   {i+1}. {node.name} (类型: {node.node_type}, 层级: {node.level}, 父节点: {parent_name}, 分类: {node.classification}, 标签: {node.tags})")
    
    print("\n" + "="*50)
    print("测试完成！")
    print("="*50)
    return True

if __name__ == "__main__":
    success = test_kg_engine()
    sys.exit(0 if success else 1)