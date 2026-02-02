import gradio as gr
import pandas as pd
import json
from kg_engine import KGEngine, KGNode
import os

# Initialize Engine
engine = KGEngine()

def process_chat(message, history):
    # In Gradio 6, chat history should be a list of dictionaries with 'role' and 'content' keys
    # Start with empty list to ensure correct format
    formatted_history = []
    
    # Only process history if it's a list
    if isinstance(history, list):
        for item in history:
            if isinstance(item, dict) and "role" in item and "content" in item:
                # Already in correct format
                formatted_history.append(item)
            elif isinstance(item, (list, tuple)) and len(item) == 2:
                # Convert from tuple format to dict format
                formatted_history.append({"role": "user", "content": item[0]})
                formatted_history.append({"role": "assistant", "content": item[1]})
            # Skip any other invalid formats
    
    # Add current user message - this is required for proper chat flow
    formatted_history.append({"role": "user", "content": message})
    
    # Handle clear command first
    if "清除" in message or "重置" in message:
        engine.clear_nodes()
        formatted_history.append({"role": "assistant", "content": "知识图谱已清除。您可以重新开始生成课程蓝图。"})
        return formatted_history
    
    # Parse JSON input if possible
    parsed_input = None
    is_json_input = False
    
    if message.strip().startswith('{') and message.strip().endswith('}'):
        try:
            parsed_input = json.loads(message)
            is_json_input = True
        except json.JSONDecodeError:
            pass
    
    # Initialize response
    response = ""
    
    # Handle JSON input
    if is_json_input and parsed_input:
        input_type = parsed_input.get("type", "")
        
        if input_type == "blueprint":
            course_name = parsed_input.get("course", "")
            target_level = parsed_input.get("target_level", "")
            goal = parsed_input.get("goal", "")
            source_text = parsed_input.get("source_text", "")
            
            course_info = f"课程名称：{course_name}\n目标级别：{target_level}\n课程目标：{goal}\n课程描述：{source_text}"
            
            data = engine.generate_blueprint(course_info)
            nodes_info = data.get("nodes", []) if isinstance(data, dict) else data
            added_count = 0
            for n in nodes_info:
                if not isinstance(n, dict) or 'name' not in n or 'type' not in n or 'level' not in n:
                    continue
                
                node = KGNode(n['name'], n['type'], n['level'])
                engine.add_node(node)
                added_count += 1
            response = f"蓝图生成完成，包含 {added_count} 个章节。现在您可以请求扩展特定章节。"
        
        elif input_type == "expand":
            node_name = parsed_input.get("node_name", "")
            section_text = parsed_input.get("section_text", "")
            
            if node_name:
                parent_node = next((node for node in engine.nodes if node.name == node_name), None)
                if parent_node:
                    # Get context from all user messages
                    user_contents = []
                    for msg in formatted_history:
                        if msg.get("role") == "user" and "content" in msg:
                            content = msg["content"]
                            # Ensure content is string
                            if isinstance(content, str):
                                user_contents.append(content)
                            elif isinstance(content, (list, dict)):
                                # Convert non-string content to string
                                user_contents.append(str(content))
                    context = "".join(user_contents)
                    
                    if section_text:
                        if isinstance(section_text, str):
                            context += f"\n\n章节内容：{section_text}"
                        else:
                            context += f"\n\n章节内容：{str(section_text)}"
                    
                    expanded_data = engine.expand_node(node_name, context)
                    expanded_nodes = expanded_data.get("nodes", []) if isinstance(expanded_data, dict) else expanded_data
                    
                    added_count = 0
                    for n in expanded_nodes:
                        if not isinstance(n, dict) or 'name' not in n:
                            continue
                        
                        level = parent_node.level + 1
                        node_type = n.get('type', '知识点')
                        
                        node = KGNode(n['name'], node_type, level, parent_node)
                        
                        if 'classification' in n:
                            node.classification = n['classification']
                        if 'tags' in n:
                            node.tags = n['tags']
                        if 'pre_nodes' in n and isinstance(n['pre_nodes'], (list, tuple)):
                            node.pre_nodes = n['pre_nodes']
                        if 'post_nodes' in n and isinstance(n['post_nodes'], (list, tuple)):
                            node.post_nodes = n['post_nodes']
                        if 'related_nodes' in n and isinstance(n['related_nodes'], (list, tuple)):
                            node.related_nodes = n['related_nodes']
                        if 'description' in n:
                            node.description = n['description']
                        
                        engine.add_node(node)
                        added_count += 1
                    
                    response = f"已扩展章节 '{node_name}'，添加了 {added_count} 个子节点。您可以继续扩展其他章节或查看当前知识结构。"
                else:
                    response = f"未找到名称为 '{node_name}' 的节点。请检查节点名称是否正确。"
            else:
                response = "扩展请求缺少 'node_name' 字段。"
        
        else:
            response = f"不支持的输入类型：{input_type}。支持的类型：'blueprint'（生成蓝图）、'expand'（扩展章节）。"
    
    # Handle free text input
    else:
        if not engine.nodes:
            data = engine.generate_blueprint(message)
            nodes_info = data.get("nodes", []) if isinstance(data, dict) else data
            added_count = 0
            for n in nodes_info:
                if not isinstance(n, dict) or 'name' not in n or 'type' not in n or 'level' not in n:
                    continue
                
                node = KGNode(n['name'], n['type'], n['level'])
                engine.add_node(node)
                added_count += 1
            response = f"蓝图生成完成，包含 {added_count} 个章节。现在您可以请求扩展特定章节。"
        else:
            import re
            
            current_nodes = [node.name for node in engine.nodes]
            matched_node = None
            
            expansion_keywords = ["扩展", "详细", "深入", "展开", "细化", "分解"]
            has_expansion_keyword = any(keyword in message for keyword in expansion_keywords)
            
            if has_expansion_keyword or len(engine.nodes) > 0:
                for node_name in sorted(current_nodes, key=len, reverse=True):
                    if node_name in message:
                        matched_node = node_name
                        break
                
                if not matched_node:
                    chapter_match = re.search(r"(第\d+章|第\d+节|章节\d+)", message)
                    if chapter_match:
                        chapter_num = int(re.search(r"\d+", chapter_match.group()).group())
                        if chapter_num <= len(engine.nodes):
                            matched_node = engine.nodes[chapter_num - 1].name
                
                if not matched_node and has_expansion_keyword and engine.nodes:
                    matched_node = engine.nodes[0].name
            
            if matched_node:
                parent_node = next((node for node in engine.nodes if node.name == matched_node), None)
                if parent_node:
                    # Get context from all user messages
                    user_contents = []
                    for msg in formatted_history:
                        if msg.get("role") == "user" and "content" in msg:
                            content = msg["content"]
                            # Ensure content is string
                            if isinstance(content, str):
                                user_contents.append(content)
                            elif isinstance(content, (list, dict)):
                                # Convert non-string content to string
                                user_contents.append(str(content))
                    context = "".join(user_contents)
                    
                    expanded_data = engine.expand_node(matched_node, context)
                    expanded_nodes = expanded_data.get("nodes", []) if isinstance(expanded_data, dict) else expanded_data
                    
                    added_count = 0
                    for n in expanded_nodes:
                        if not isinstance(n, dict) or 'name' not in n:
                            continue
                        
                        level = parent_node.level + 1
                        node_type = n.get('type', '知识点')
                        
                        node = KGNode(n['name'], node_type, level, parent_node)
                        
                        if 'classification' in n:
                            node.classification = n['classification']
                        if 'tags' in n:
                            node.tags = n['tags']
                        if 'pre_nodes' in n and isinstance(n['pre_nodes'], (list, tuple)):
                            node.pre_nodes = n['pre_nodes']
                        if 'post_nodes' in n and isinstance(n['post_nodes'], (list, tuple)):
                            node.post_nodes = n['post_nodes']
                        if 'related_nodes' in n and isinstance(n['related_nodes'], (list, tuple)):
                            node.related_nodes = n['related_nodes']
                        if 'description' in n:
                            node.description = n['description']
                        
                        engine.add_node(node)
                        added_count += 1
                    
                    response = f"已扩展章节 '{matched_node}'，添加了 {added_count} 个子节点。您可以继续扩展其他章节或查看当前知识结构。"
            else:
                response = "已理解您的输入。当前知识结构已更新。您可以查看当前图谱或导出为Excel。"
    
    # Add assistant response
    formatted_history.append({"role": "assistant", "content": response})
    
    # Final safety check - ensure all items in history are valid
    final_history = []
    for item in formatted_history:
        if isinstance(item, dict) and "role" in item and "content" in item:
            final_history.append(item)
    
    return final_history

def get_current_table():
    if not engine.nodes:
        return pd.DataFrame(columns=["Type", "Name", "Level", "Parent", "Classification", "Tags"])
    data = [n.to_dict() for n in engine.nodes]
    # Create a more user-friendly view
    view_data = []
    for d in data:
        view_data.append({
            "Type": d["type"],
            "Name": d["name"],
            "Level": d["level"],
            "Parent": d["parent"],
            "Classification": d["class"],
            "Tags": d["tags"]
        })
    return pd.DataFrame(view_data)

def get_editable_table():
    """Get editable table data"""
    return engine.get_editiable_data()

def save_edited_nodes(edited_data):
    """Save edited nodes data"""
    try:
        if edited_data is None or len(edited_data) == 0:
            return "没有可保存的数据", ""
        
        # Get original node names to track changes
        original_names = set(node.name for node in engine.nodes)
        
        # Process each row
        for idx, row in edited_data.iterrows():
            # Get node name directly from the single column
            if pd.isna(row["节点名称"]) or not row["节点名称"]:
                continue
            
            node_name = str(row["节点名称"]).strip()
            
            # Determine level based on context (simplified approach)
            # For new nodes, we'll default to level 1
            # For existing nodes, we'll keep their current level
            level = 1
            existing_node = engine.get_node_by_name(node_name)
            if existing_node:
                level = existing_node.level
            
            node_data = {
                "name": node_name,
                "type": str(row["节点类型"]).strip() if pd.notna(row["节点类型"]) else "知识点",
                "level": level,
                "classification": str(row["知识点分类"]).strip() if pd.notna(row["知识点分类"]) else "",
                "description": str(row["节点说明"]).strip() if pd.notna(row["节点说明"]) else "",
                "tags": str(row["标签"]).strip() if pd.notna(row["标签"]) else "",
                "pre_nodes": str(row["前置节点"]).strip() if pd.notna(row["前置节点"]) else "",
                "post_nodes": str(row["后置节点"]).strip() if pd.notna(row["后置节点"]) else "",
                "related_nodes": str(row["关联节点"]).strip() if pd.notna(row["关联节点"]) else ""
            }
            
            # Check if node exists
            if node_name in original_names:
                engine.update_node(node_name, node_data)
            else:
                # Add new node
                engine.add_node_from_dict(node_data)
        
        # Return success message and refresh table
        return "保存成功！知识结构已更新。", engine.get_editiable_data()
    except Exception as e:
        return f"保存失败：{str(e)}", engine.get_editiable_data()

def delete_selected_nodes_by_name(names_to_delete):
    """Delete selected nodes by names"""
    try:
        if not names_to_delete or len(names_to_delete) == 0:
            return "请先选择要删除的节点", engine.get_editiable_data()
        
        # Delete nodes
        for name in names_to_delete:
            engine.delete_node(name)
        
        deleted_count = len(names_to_delete)
        return f"已删除 {deleted_count} 个节点", engine.get_editiable_data()
    except Exception as e:
        return f"删除失败：{str(e)}", engine.get_editiable_data()

def add_new_node():
    """Add a new empty row for creating a node"""
    current_data = engine.get_editiable_data()
    
    # Create a new empty row
    new_row = pd.DataFrame({
        "节点类型": ["知识点"],
        "节点名称": [""],
        "前置节点": [""],
        "后置节点": [""],
        "关联节点": [""],
        "标签": [""],
        "知识点分类": [""],
        "节点说明": [""]
    })
    
    # Concatenate
    updated_data = pd.concat([current_data, new_row], ignore_index=True)
    
    return updated_data

def clear_knowledge_graph():
    engine.clear_nodes()
    # Return empty chat history in correct Gradio format
    return []

def export_excel():
    path = "course_kg_export.xlsx"
    engine.export_to_excel(path)
    return path

with gr.Blocks(title="生长型课程知识图谱 AI 助手") as demo:
    gr.Markdown("# 生长型课程知识图谱 AI 助手")
    gr.Markdown("支持课程知识结构从“总体蓝图”逐步生长为“完整课程体系”。符合真实教学过程与教师认知方式。")
    
    with gr.Tab("AI 规划"):
        chatbot = gr.Chatbot(label="与 AI 讨论课程结构")
        msg = gr.Textbox(
            label="输入课程信息或扩展请求（支持JSON格式）", 
            placeholder="示例1（生成蓝图）：{\"type\": \"blueprint\", \"course\": \"Python数据分析\", \"target_level\": \"入门级\", \"goal\": \"构建基于Python的数据分析思维基础\", \"source_text\": \"本课程介绍Python作为数据分析的基础工具...\"}\n示例2（扩展章节）：{\"type\": \"expand\", \"node_name\": \"蓝图中的父节点\", \"section_text\": \"手动输入需要扩展的关键内容（可以是AI总结的章节内容）\"}\n示例3（自由输入）：我想建设一门《人工智能导论》课程",
            lines=6,
            scale=2,
            interactive=True
        )
        with gr.Row():
            submit_btn = gr.Button("提交")
            clear_chat = gr.Button("清除对话")
            clear_kg = gr.Button("清除知识图谱")
        
        gr.Markdown("### 支持的输入格式：")
        gr.Markdown("1. **生成蓝图**：")
        gr.Code(
            value='''{
  "type": "blueprint",
  "course": "Python数据分析",
  "target_level": "入门级",
  "goal": "构建基于Python的数据分析思维基础",
  "source_text": "本课程介绍Python作为数据分析的基础工具..."
}''',
            language="json"
        )
        gr.Markdown("2. **扩展章节**：")
        gr.Code(
            value='''{
  "type": "expand",
  "node_name": "蓝图中的父节点",
  "section_text": "手动输入需要扩展的关键内容（可以是AI总结的章节内容）"
}''',
            language="json"
        )
        gr.Markdown("3. **自由输入**：直接输入课程描述或扩展请求（可控性较差）")
        
        msg.submit(process_chat, [msg, chatbot], [chatbot])
        submit_btn.click(process_chat, [msg, chatbot], [chatbot])
        # Use simple lambda functions that only return empty list
        # Clear chat history only
        def clear_chat_only():
            return []
        
        # Clear both knowledge graph and chat history
        def clear_all():
            engine.clear_nodes()
            return []
        
        clear_chat.click(clear_chat_only, outputs=chatbot)
        clear_kg.click(clear_all, outputs=chatbot)

    with gr.Tab("知识结构预览"):
        gr.Markdown("### 知识结构手动编辑")
        gr.Markdown("您可以手动编辑、添加或删除节点，以调整AI生成的知识结构。")
        gr.Markdown("#### 编辑说明：")
        gr.Markdown('- **固定标签**：包括：重点、难点、考点、课程思政，可根据需要自定义标签，多个标签之间用英文分号";"隔开')
        gr.Markdown("- **知识点分类**：包括：事实性、概念性、程序性、元认知，每个知识点只能填入一个知识点分类，分类不支持填写知识点分类")
        gr.Markdown("- **节点说明**：仅支持输入文本，暂不支持图片、公式等")
        gr.Markdown("- **长度限制**：单个分类或知识点长度最长256字符，知识点后不可填写子级节点")
        
        with gr.Row():
            add_node_btn = gr.Button("添加节点")
            save_btn = gr.Button("保存修改")
            delete_btn = gr.Button("删除选中")
            refresh_btn = gr.Button("刷新")
        
        # State to track selected row
        selected_row = gr.State(value=None)
        
        # Editable DataFrame component
        editable_table = gr.Dataframe(
            value=get_editable_table,
            headers=["节点类型", "节点名称", "前置节点", "后置节点", "关联节点", "标签", "知识点分类", "节点说明"],
            interactive=True,
            label="可编辑的知识节点列表",
            datatype=["str", "str", "str", "str", "str", "str", "str", "str"],
            max_height=500
        )
        
        # Status message
        status_msg = gr.Textbox(label="状态信息", interactive=False)
        
        # Button actions
        refresh_btn.click(get_editable_table, outputs=editable_table)
        
        def handle_add_node():
            return add_new_node()
        
        add_node_btn.click(handle_add_node, outputs=editable_table)
        
        def handle_save(edited_df):
            message, _ = save_edited_nodes(edited_df)
            # Refresh table after save
            updated_df = engine.get_editiable_data()
            return message, updated_df
        
        save_btn.click(handle_save, inputs=editable_table, outputs=[status_msg, editable_table])
        
        def on_table_select(current_df, evt: gr.SelectData):
            if evt is None or not evt.index:
                return current_df, None
            # Store selected row data
            row_idx = evt.index[0]
            if row_idx < len(current_df):
                row = current_df.iloc[row_idx]
                if pd.notna(row["名称"]) and row["名称"]:
                    return current_df, [str(row["名称"]).strip()]
            return current_df, None
        
        def handle_delete_with_state(current_df, selected_names):
            if not selected_names or len(selected_names) == 0:
                return current_df, "请先选择要删除的节点", None
            message, updated_df = delete_selected_nodes_by_name(selected_names)
            return updated_df, message, None
        
        # Connect select event
        editable_table.select(on_table_select, inputs=editable_table, outputs=[editable_table, selected_row])
        
        # Connect delete button
        delete_btn.click(handle_delete_with_state, inputs=[editable_table, selected_row], outputs=[editable_table, status_msg, selected_row])
        
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
    demo.launch(server_name="0.0.0.0", server_port=7861)
