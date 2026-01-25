import gradio as gr
import pandas as pd
import json
from kg_engine import KGEngine, KGNode
import os

# Initialize Engine
engine = KGEngine()

def process_chat(message, history):
    # Process chat messages with intelligent logic
    if not engine.nodes:
        # First interaction: Generate Blueprint
        data = engine.generate_blueprint(message)
        nodes_info = data.get("nodes", []) if isinstance(data, dict) else data
        for n in nodes_info:
            node = KGNode(n['name'], n['type'], n['level'])
            engine.add_node(node)
        return f"蓝图生成完成，包含 {len(nodes_info)} 个章节。现在您可以请求扩展特定章节。"
    else:
        # Subsequent interactions: Check if user wants to expand a chapter
        # Extract parent node name from message if it contains "扩展" or "详细" or "深入"
        import re
        
        # Get all current node names for matching
        current_nodes = [node.name for node in engine.nodes]
        
        # Check if user wants to expand a specific node
        matched_node = None
        for node_name in current_nodes:
            if node_name in message:
                matched_node = node_name
                break
        
        if matched_node:
            # Expand the matched node
            parent_node = next((node for node in engine.nodes if node.name == matched_node), None)
            if parent_node:
                # Get context from previous messages
                context = "".join([msg[1] for msg in history]) if history else message
                
                # Expand the node
                expanded_data = engine.expand_node(matched_node, context)
                expanded_nodes = expanded_data.get("nodes", []) if isinstance(expanded_data, dict) else expanded_data
                
                # Add expanded nodes to engine
                for n in expanded_nodes:
                    # Determine level (parent level + 1)
                    level = parent_node.level + 1
                    
                    # Create new node with parent reference
                    node = KGNode(n['name'], n.get('type', '知识点'), level, parent_node)
                    
                    # Add classification and tags if present
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
                    
                    # Add to engine
                    engine.add_node(node)
                
                return f"已扩展章节 '{matched_node}'，添加了 {len(expanded_nodes)} 个子节点。您可以继续扩展其他章节或查看当前知识结构。"
        
        # If no specific node to expand, just acknowledge
        return "已理解您的输入。当前知识结构已更新。您可以查看当前图谱或导出为Excel。"

def get_current_table():
    if not engine.nodes:
        return pd.DataFrame(columns=["Type", "Name", "Level", "Parent"])
    data = [n.to_dict() for n in engine.nodes]
    return pd.DataFrame(data)

def export_excel():
    path = "course_kg_export.xlsx"
    engine.export_to_excel(path)
    return path

with gr.Blocks(title="生长型课程知识图谱 AI 助手") as demo:
    gr.Markdown("# 生长型课程知识图谱 AI 助手")
    gr.Markdown("支持课程知识结构从“总体蓝图”逐步生长为“完整课程体系”。符合真实教学过程与教师认知方式。")
    
    with gr.Tab("AI 规划"):
        chatbot = gr.Chatbot(label="与 AI 讨论课程结构")
        msg = gr.Textbox(label="输入课程名称、描述或建设要求", placeholder="例如：我想建设一门《人工智能导论》课程...")
        clear = gr.Button("清除对话")
        
        msg.submit(process_chat, [msg, chatbot], [chatbot])
        clear.click(lambda: None, None, chatbot, queue=False)

    with gr.Tab("知识结构预览"):
        refresh_btn = gr.Button("刷新预览")
        table_view = gr.Dataframe(label="当前知识点列表")
        refresh_btn.click(get_current_table, outputs=table_view)
        
    with gr.Tab("导出与图示"):
        with gr.Row():
            export_btn = gr.Button("导出为系统导入模板 (Excel)")
            viz_btn = gr.Button("生成可视化图谱")
            
        file_output = gr.File(label="下载 Excel 模板")
        export_btn.click(export_excel, outputs=file_output)
        
        gr.Markdown("### 知识图谱可视化")
        viz_output = gr.Image(label="知识图谱预览")
        viz_btn.click(lambda: engine.visualize(), outputs=viz_output)

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7860)
