import json
import pandas as pd
from typing import List, Dict, Optional
from openai import OpenAI
from config import OPEN_API_KEY, OPEN_API_BASE, OPEN_API_MODEL
import os

# Initialize OpenAI client with configuration
client = OpenAI(
    api_key=OPEN_API_KEY,
    base_url=OPEN_API_BASE
)

# Data persistence file path
DATA_FILE = "kg_data.json"

class KGNode:
    def __init__(self, name: str, node_type: str, level: int, parent=None):
        self.name = name
        self.node_type = node_type  # '分类' or '知识点'
        self.level = level
        self.parent = parent
        self.pre_nodes = []
        self.post_nodes = []
        self.related_nodes = []
        self.tags = []
        self.classification = "" # 事实性, 概念性, 程序性, 元认知
        self.description = ""

    def to_dict(self):
        return {
            "name": self.name,
            "type": self.node_type,
            "level": self.level,
            "parent": self.parent.name if self.parent else None,
            "pre": ";".join(self.pre_nodes),
            "post": ";".join(self.post_nodes),
            "related": ";".join(self.related_nodes),
            "tags": ";".join(self.tags),
            "class": self.classification,
            "desc": self.description
        }
        
    @classmethod
    def from_dict(cls, data):
        """Create KGNode from dictionary, without parent reference"""
        node = cls(
            name=data["name"],
            node_type=data["type"],
            level=data["level"]
        )
        # Fix: Handle empty strings correctly
        node.pre_nodes = data["pre"].split(";") if data["pre"] else []
        node.post_nodes = data["post"].split(";") if data["post"] else []
        node.related_nodes = data["related"].split(";") if data["related"] else []
        node.tags = data["tags"].split(";") if data["tags"] else []
        node.classification = data["class"]
        node.description = data["desc"]
        return node

class KGEngine:
    def __init__(self):
        self.nodes: List[KGNode] = []
        self.load_from_file()

    def add_node(self, node: KGNode):
        self.nodes.append(node)
        self.save_to_file()

    def generate_blueprint(self, course_info: str):
        # Use regular string with .format() to avoid f-string brace issues
        prompt_template = """
        Act as an educational expert. Based on the course info: "{course_info}", 
        generate a high-level course blueprint (Chapter/Module level).
        Return a JSON OBJECT with a key 'nodes' that contains an array of objects.
        Each node object should have: "name", "type" (always '分类'), "level" (1 or 2).
        - IMPORTANT: DO NOT include chapter numbers like "第一章:", "第二章:" etc. in the node names.
        - Just use the pure chapter name, e.g., "数据分析基础" instead of "第一章: 数据分析基础".
        - STRICTLY LIMIT: Generate EXACTLY 5-8 main chapters (no more than 8 nodes).
        Example format:
        {{
            "nodes": [
                {{"name": "数据分析基础", "type": "分类", "level": 1}},
                {{"name": "Python编程入门", "type": "分类", "level": 1}}
            ]
        }}
        """
        
        # Use .format() with safe escaping
        prompt = prompt_template.format(course_info=course_info)
        try:
            response = client.chat.completions.create(
                model=OPEN_API_MODEL,
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"}
            )
            data = json.loads(response.choices[0].message.content)
            return data
        except Exception as e:
            print(f"Error generating blueprint: {e}")
            return {"nodes": []}

    def expand_node(self, parent_name: str, context: str):
        # Use regular string with .format() to avoid f-string brace issues
        prompt_template = """
        Expand the node "{parent_name}" within the context of "{context}".
        Provide sub-categories ('分类') or knowledge points ('知识点').
        Return a JSON OBJECT with a key 'nodes' that contains an array of objects.
        - STRICTLY LIMIT: Generate EXACTLY 3-5 sub-nodes (no more than 5 nodes).
        - IMPORTANT: DO NOT include chapter numbers like "第一章:", "第二章:" etc. in the node names.
        For knowledge points, include:
        - "classification": '事实性', '概念性', '程序性', or '元认知'
        - "tags": list from ['重点', '难点', '考点', '课程思政']
        - "pre_nodes": list of logical prerequisites
        Example format:
        {{
            "nodes": [
                {{
                    "name": "数据分析基础", 
                    "type": "知识点", 
                    "classification": "概念性",
                    "tags": ["重点"]
                }}
            ]
        }}
        """
        
        # Use .format() with safe escaping
        prompt = prompt_template.format(parent_name=parent_name, context=context)
        try:
            response = client.chat.completions.create(
                model=OPEN_API_MODEL,
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"}
            )
            data = json.loads(response.choices[0].message.content)
            return data
        except Exception as e:
            print(f"Error expanding node: {e}")
            return {"nodes": []}
        
    def save_to_file(self):
        """Save current nodes to JSON file"""
        nodes_data = []
        for node in self.nodes:
            node_dict = node.to_dict()
            # Remove parent reference to avoid circular dependency
            # We'll rebuild parent relationships when loading
            nodes_data.append(node_dict)
        
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(nodes_data, f, ensure_ascii=False, indent=2)
            
    def load_from_file(self):
        """Load nodes from JSON file"""
        if os.path.exists(DATA_FILE):
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                nodes_data = json.load(f)
                
            # First pass: Create all nodes without parent references
            temp_nodes = []
            for node_data in nodes_data:
                node = KGNode.from_dict(node_data)
                temp_nodes.append(node)
            
            # Second pass: Build parent-child relationships
            for i, node_data in enumerate(nodes_data):
                if node_data["parent"]:
                    parent_name = node_data["parent"]
                    parent_node = next((n for n in temp_nodes if n.name == parent_name), None)
                    if parent_node:
                        temp_nodes[i].parent = parent_node
            
            self.nodes = temp_nodes
    
    def clear_nodes(self):
        """Clear all nodes and update file"""
        self.nodes = []
        if os.path.exists(DATA_FILE):
            os.remove(DATA_FILE)

    def get_node_by_name(self, name: str):
        """Get node by name"""
        return next((node for node in self.nodes if node.name == name), None)

    def update_node(self, old_name: str, new_data: dict):
        """Update an existing node with new data"""
        node = self.get_node_by_name(old_name)
        if not node:
            return False
        
        # Update node attributes
        if "name" in new_data and new_data["name"]:
            node.name = new_data["name"]
        if "type" in new_data and new_data["type"]:
            node.node_type = new_data["type"]
        if "level" in new_data and new_data["level"]:
            node.level = int(new_data["level"])
        if "classification" in new_data:
            node.classification = new_data["classification"]
        if "description" in new_data:
            node.description = new_data["description"]
        
        # Handle list fields
        if "tags" in new_data:
            if isinstance(new_data["tags"], str):
                node.tags = [t.strip() for t in new_data["tags"].split(";") if t.strip()]
            elif isinstance(new_data["tags"], (list, tuple)):
                node.tags = [str(t).strip() for t in new_data["tags"] if t]
        
        if "pre_nodes" in new_data:
            if isinstance(new_data["pre_nodes"], str):
                node.pre_nodes = [t.strip() for t in new_data["pre_nodes"].split(";") if t.strip()]
            elif isinstance(new_data["pre_nodes"], (list, tuple)):
                node.pre_nodes = [str(t).strip() for t in new_data["pre_nodes"] if t]
        
        if "post_nodes" in new_data:
            if isinstance(new_data["post_nodes"], str):
                node.post_nodes = [t.strip() for t in new_data["post_nodes"].split(";") if t.strip()]
            elif isinstance(new_data["post_nodes"], (list, tuple)):
                node.post_nodes = [str(t).strip() for t in new_data["post_nodes"] if t]
        
        if "related_nodes" in new_data:
            if isinstance(new_data["related_nodes"], str):
                node.related_nodes = [t.strip() for t in new_data["related_nodes"].split(";") if t.strip()]
            elif isinstance(new_data["related_nodes"], (list, tuple)):
                node.related_nodes = [str(t).strip() for t in new_data["related_nodes"] if t]
        
        self.save_to_file()
        return True

    def delete_node(self, name: str):
        """Delete a node by name"""
        node = self.get_node_by_name(name)
        if not node:
            return False
        
        # Remove node from list
        self.nodes = [n for n in self.nodes if n.name != name]
        
        # Remove this node as parent from other nodes
        for n in self.nodes:
            if n.parent and n.parent.name == name:
                n.parent = None
        
        self.save_to_file()
        return True

    def delete_nodes_batch(self, names: list):
        """Delete multiple nodes by names"""
        for name in names:
            self.delete_node(name)
        return True

    def add_node_from_dict(self, node_data: dict):
        """Add a new node from dictionary data"""
        if not node_data.get("name") or not node_data.get("type"):
            return False
        
        # Find parent if specified
        parent = None
        if "parent" in node_data and node_data["parent"]:
            parent = self.get_node_by_name(str(node_data["parent"]))
        
        level = int(node_data.get("level", 1))
        node = KGNode(
            name=node_data["name"],
            node_type=node_data["type"],
            level=level,
            parent=parent
        )
        
        if "classification" in node_data:
            node.classification = node_data["classification"]
        if "description" in node_data:
            node.description = node_data["description"]
        
        # Handle list fields
        if "tags" in node_data:
            if isinstance(node_data["tags"], str):
                node.tags = [t.strip() for t in node_data["tags"].split(";") if t.strip()]
            elif isinstance(node_data["tags"], (list, tuple)):
                node.tags = [str(t).strip() for t in node_data["tags"] if t]
        
        if "pre_nodes" in node_data:
            if isinstance(node_data["pre_nodes"], str):
                node.pre_nodes = [t.strip() for t in node_data["pre_nodes"].split(";") if t.strip()]
            elif isinstance(node_data["pre_nodes"], (list, tuple)):
                node.pre_nodes = [str(t).strip() for t in node_data["pre_nodes"] if t]
        
        if "post_nodes" in node_data:
            if isinstance(node_data["post_nodes"], str):
                node.post_nodes = [t.strip() for t in node_data["post_nodes"].split(";") if t.strip()]
            elif isinstance(node_data["post_nodes"], (list, tuple)):
                node.post_nodes = [str(t).strip() for t in node_data["post_nodes"] if t]
        
        if "related_nodes" in node_data:
            if isinstance(node_data["related_nodes"], str):
                node.related_nodes = [t.strip() for t in node_data["related_nodes"].split(";") if t.strip()]
            elif isinstance(node_data["related_nodes"], (list, tuple)):
                node.related_nodes = [str(t).strip() for t in node_data["related_nodes"] if t]
        
        self.add_node(node)
        return True

    def get_editiable_data(self):
        """Get nodes data for editable table"""
        if not self.nodes:
            return pd.DataFrame(columns=["节点类型", "节点名称", "前置节点", "后置节点", "关联节点", "标签", "知识点分类", "节点说明"])
        
        # Sort nodes by level and parent relationship
        def get_node_key(node):
            """Generate a sort key for node based on hierarchy"""
            if not node.parent:
                return (node.level, node.name)
            else:
                parent_key = get_node_key(node.parent)
                return parent_key + (node.level, node.name)
        
        # Sort nodes
        sorted_nodes = sorted(self.nodes, key=get_node_key)
        
        data = []
        for node in sorted_nodes:
            row = {
                "节点类型": node.node_type,
                "节点名称": node.name,
                "前置节点": ";".join(node.pre_nodes) if node.pre_nodes else "",
                "后置节点": ";".join(node.post_nodes) if node.post_nodes else "",
                "关联节点": ";".join(node.related_nodes) if node.related_nodes else "",
                "标签": ";".join(node.tags) if node.tags else "",
                "知识点分类": node.classification,
                "节点说明": node.description
            }
            data.append(row)
        
        return pd.DataFrame(data)

    def export_to_excel(self, filename: str):
        rows = []
        for node in self.nodes:
            row = {
                "节点类型*": node.node_type,
                "节点名称1": node.name if node.level == 1 else "",
                "节点名称2": node.name if node.level == 2 else "",
                "节点名称3": node.name if node.level == 3 else "",
                "节点名称4": node.name if node.level == 4 else "",
                "节点名称5": node.name if node.level == 5 else "",
                "节点名称6": node.name if node.level == 6 else "",
                "节点名称7": node.name if node.level == 7 else "",
                "前置节点": ";".join(node.pre_nodes),
                "后置节点": ";".join(node.post_nodes),
                "关联节点": ";".join(node.related_nodes),
                "标签": ";".join(node.tags),
                "知识点分类": node.classification,
                "节点说明": node.description
            }
            rows.append(row)
        
        # Add instruction row as per template (Row 1 is usually instructions)
        # But here we just follow the column structure
        df = pd.DataFrame(rows)
        cols = ["节点类型*", "节点名称1", "节点名称2", "节点名称3", "节点名称4", "节点名称5", "节点名称6", "节点名称7", 
                "前置节点", "后置节点", "关联节点", "标签", "知识点分类", "节点说明"]
        
        # Ensure all columns exist
        for col in cols:
            if col not in df.columns:
                df[col] = ""
        
        df = df[cols]
        # Rename columns to match the image precisely if needed (B-H are all '节点名称')
        # In the image, B-H columns are all titled "节点名称"
        # We will use the titles from the image for the final export
        display_cols = ["节点类型*", "节点名称", "节点名称", "节点名称", "节点名称", "节点名称", "节点名称", "节点名称", 
                        "前置节点", "后置节点", "关联节点", "标签", "知识点分类", "节点说明"]
        
        df.columns = display_cols
        # Use openpyxl engine explicitly for better compatibility
        df.to_excel(filename, index=False, engine='openpyxl')
        return filename

    def visualize(self):
        import networkx as nx
        import matplotlib.pyplot as plt
        import matplotlib
        matplotlib.use('Agg') # Non-interactive backend
        
        # Fix Chinese font issue
        plt.rcParams['font.sans-serif'] = ['SimHei', 'Arial Unicode MS', 'DejaVu Sans']
        plt.rcParams['axes.unicode_minus'] = False
        
        G = nx.DiGraph()
        for node in self.nodes:
            G.add_node(node.name, type=node.node_type)
            if node.parent:
                G.add_edge(node.parent.name, node.name, rel='child')
            for pre in node.pre_nodes:
                G.add_edge(pre, node.name, rel='pre')
        
        plt.figure(figsize=(10, 8))
        pos = nx.spring_layout(G)
        nx.draw(G, pos, with_labels=True, node_size=2000, node_color="skyblue", font_size=10, font_weight="bold", arrows=True)
        plt.title("Course Knowledge Graph Visualization")
        
        img_path = "kg_viz.png"
        plt.savefig(img_path)
        plt.close()
        return img_path
