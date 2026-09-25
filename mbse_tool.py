import streamlit as st
import graphviz
import json
import tempfile
import os

def export_to_sysml_v2(nodes, edges):
    lines = []
    lines.append("package MBSE_Model {")
    lines.append("")

    for n in nodes:
        safe_name = n["name"].replace(" ", "_")
        desc = n.get("description", "").replace("\n", " ")
        lines.append(f"  part {safe_name} {{")
        if desc:
            lines.append(f'    doc "{desc}";')
        lines.append(f'    // Step: {n.get("step","")} | Method: {n.get("method","")}')
        lines.append("  }")
        lines.append("")

    for e in edges:
        src = e["source"].replace(" ", "_")
        tgt = e["target"].replace(" ", "_")
        lines.append(f"  dependency {src}_to_{tgt} from {src} to {tgt};")

    lines.append("")
    lines.append("}")

    return "\n".join(lines)

st.set_page_config(layout="wide", page_title="Unified MBSE Modeling Tool")

st.markdown(
    """
    <style>
    html, body, [class*="css"]  {
        font-size: 0.9rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("🛠️ Unified MBSE Modeling Tool")

METHODOLOGY_STEPS = {
     "OOSEM": [
         "Stakeholder Needs",
         "System Requirements",
         "Logical Architecture",
         "Implementation",
         "Verification",
     ],
     "V-Model": [
         "User Requirements",
         "System Requirements",
         "System Design",
         "Subsystem Design",
         "Module Design",
         "Implementation",
         "Unit Verification",
         "Subsystem Verification",
         "System Verification",
         "Acceptance Verification",
     ],
     "RFLP": ["Requirements Layer", "Function Layer", "Logical Layer", "Physical Layer"],
     "PPR": ["Product", "Process", "Resources"],
 }


STEP_OPTIONS = []

COMMON_STEPS = ["System Requirements", "Implementation", "Verification"]

for step in COMMON_STEPS:
    STEP_OPTIONS.append(f"{step} (OOSEM)")
    STEP_OPTIONS.append(f"{step} (V-Model)")

for method, steps in METHODOLOGY_STEPS.items():
    for step in steps:
        if step not in COMMON_STEPS:
            STEP_OPTIONS.append(step)

if "nodes" not in st.session_state:
    st.session_state.nodes = []
if "edges" not in st.session_state:
    st.session_state.edges = []
if "uploaded_once" not in st.session_state:
    st.session_state.uploaded_once = False

st.sidebar.header("📦 Import / Export")

uploaded_file = st.sidebar.file_uploader("Upload MBSE JSON", type=["json"])
if uploaded_file and not st.session_state.uploaded_once:
    try:
        data = json.load(uploaded_file)
        st.session_state.nodes = data.get("nodes", [])
        st.session_state.edges = data.get("edges", [])
        st.session_state.uploaded_once = True
        st.success("✅ JSON uploaded successfully")
        st.rerun()
    except Exception as e:
        st.error(f"Failed to upload JSON: {e}")

st.sidebar.download_button(
    label="⬇️ Download MBSE JSON",
    data=json.dumps(
        {"nodes": st.session_state.nodes, "edges": st.session_state.edges}, indent=2
    ),
    file_name="mbse_model.json",
    mime="application/json",
)

sysml_text = export_to_sysml_v2(st.session_state.nodes, st.session_state.edges)

st.sidebar.download_button(
    label="⬇️ Download SysML v2 (.sysml)",
    data=sysml_text,
    file_name="mbse_model.sysml",
    mime="text/plain",
)

if st.sidebar.button("🔄 Reset App"):
    st.session_state.clear()
    st.rerun()

mode = st.sidebar.radio("Mode", ["Add / Edit Model", "OOSEM", "V-Model", "RFLP", "PPR"])


def get_nodes_for_method(method):
    return [n for n in st.session_state.nodes if n.get("method") == method]


def get_edges_for_nodes(nodes):
    return [
        e for e in st.session_state.edges if e["source"] in [n["name"] for n in nodes]
    ]


if mode == "Add / Edit Model":
    st.subheader("📋 Existing Nodes")
    if st.session_state.nodes:
        st.dataframe(st.session_state.nodes)
    else:
        st.info("No nodes yet.")

    st.subheader("➕ Add Node")
    with st.form("add_node_form", clear_on_submit=True):
        node_name = st.text_input("Node Name")
        node_desc = st.text_area("Description")
        step_choice = st.selectbox("Step", STEP_OPTIONS)

        if "(" in step_choice:
            step_name = step_choice.split(" (")[0]
            method_name = step_choice.split("(")[-1][:-1]
        else:
            step_name = step_choice
            method_name = next(
                (m for m, steps in METHODOLOGY_STEPS.items() if step_name in steps), ""
            )

        if st.form_submit_button("Add Node"):
            if node_name:
                node_id = len(st.session_state.nodes)
                st.session_state.nodes.append(
                    {
                        "id": node_id,
                        "name": node_name,
                        "description": node_desc,
                        "step": step_name,
                        "method": method_name,
                    }
                )
                st.success(f"Node '{node_name}' added under {method_name}")
                st.rerun()
            else:
                st.error("Node name cannot be empty.")

    st.subheader("🔗 Add Edge")
    if st.session_state.nodes:
        source_node = st.selectbox(
            "Source Node", [n["name"] for n in st.session_state.nodes]
        )
        target_node_options = [
            n["name"] for n in st.session_state.nodes if n["name"] != source_node
        ]
        if target_node_options:
            target_node = st.selectbox("Target Node", target_node_options)
            if st.button("Add Edge"):
                st.session_state.edges.append(
                    {"source": source_node, "target": target_node}
                )
                st.success(f"Edge added: {source_node} → {target_node}")
                st.rerun()
        else:
            st.info("No valid target node available.")

else:
    method = mode
    nodes = get_nodes_for_method(method)
    edges = get_edges_for_nodes(nodes)

    st.subheader(f"{method} Graph")
    if nodes:
        dot = graphviz.Digraph()
        dot.attr(rankdir="LR")
        step_colors = {
            step: color
            for step, color in zip(
                METHODOLOGY_STEPS[method],
                [
                    "lightblue",
                    "lightgreen",
                    "lightpink",
                    "lightyellow",
                    "lightcoral",
                    "orange",
                    "violet",
                    "khaki",
                    "lightsalmon",
                    "plum",
                ],
            )
        }
        for n in nodes:
            label = f"{n['name']}\n({n['step']})\n{n['description']}"
            dot.node(
                n["name"],
                label=label,
                shape="box",
                style="filled",
                fillcolor=step_colors.get(n["step"], "white"),
                fontsize="16",
            )
        for e in edges:
            dot.edge(e["source"], e["target"], fontsize="14")
        st.graphviz_chart(dot)

        # ------------------ PDF/JPEG download functionality ------------------
        with tempfile.TemporaryDirectory() as tmpdirname:
            png_path = os.path.join(tmpdirname, "graph.png")
            pdf_path = os.path.join(tmpdirname, "graph.pdf")
            dot.render(
                filename=os.path.join(tmpdirname, "graph"), format="png", cleanup=True
            )
            dot.render(
                filename=os.path.join(tmpdirname, "graph"), format="pdf", cleanup=True
            )

            with open(png_path, "rb") as f:
                st.download_button(
                    "⬇️ Download Graph as JPEG",
                    data=f,
                    file_name="graph.jpeg",
                    mime="image/jpeg",
                )
            with open(pdf_path, "rb") as f:
                st.download_button(
                    "⬇️ Download Graph as PDF",
                    data=f,
                    file_name="graph.pdf",
                    mime="application/pdf",
                )
        # --------------------------------------------------------------------

    else:
        st.info("No nodes to display in this graph.")

    st.subheader("✏️ Edit / Delete Node")
    if nodes:
        selected_node = st.selectbox(
            "Select Node", nodes, format_func=lambda x: x["name"]
        )
        new_name = st.text_input("Name", selected_node["name"])
        new_desc = st.text_area("Description", selected_node["description"])
        new_step = st.selectbox(
            "Step",
            [
                (
                    f"{s} ({selected_node['method']})"
                    if s in ["System Requirements", "Implementation", "Verification"]
                    else s
                )
                for s in METHODOLOGY_STEPS[method]
            ],
            index=METHODOLOGY_STEPS[method].index(selected_node["step"]),
        )

        col1, col2 = st.columns(2)
        if col1.button("Update Node"):
            original_node = next(
                n for n in st.session_state.nodes if n["id"] == selected_node["id"]
            )
            old_name = original_node["name"]
            if "(" in new_step:
                step_name = new_step.split(" (")[0]
            else:
                step_name = new_step
            original_node["name"] = new_name
            original_node["description"] = new_desc
            original_node["step"] = step_name

            for e in st.session_state.edges:
                if e["source"] == old_name:
                    e["source"] = new_name
                if e["target"] == old_name:
                    e["target"] = new_name
            st.success("Node updated")
            st.rerun()

        if col2.button("Delete Node"):
            st.session_state.nodes = [
                n for n in st.session_state.nodes if n["id"] != selected_node["id"]
            ]
            st.session_state.edges = [
                e
                for e in st.session_state.edges
                if e["source"] != selected_node["name"]
                and e["target"] != selected_node["name"]
            ]
            st.success("Node deleted")
            st.rerun()

    st.subheader("✏️ Edit / Delete Edge")
    if edges:
        selected_edge_index = st.selectbox(
            "Select Edge",
            range(len(edges)),
            format_func=lambda i: f"{edges[i]['source']} → {edges[i]['target']}",
        )
        selected_edge = edges[selected_edge_index]

        node_names = [n["name"] for n in nodes]
        new_source = st.selectbox(
            "Source Node",
            node_names,
            index=node_names.index(selected_edge["source"]),
        )

        target_options = [n for n in node_names if n != new_source]
        if selected_edge["target"] not in target_options:
            target_options.append(selected_edge["target"])

        new_target = st.selectbox(
            "Target Node",
            target_options,
            index=target_options.index(selected_edge["target"]),
        )

        col1, col2 = st.columns(2)
        if col1.button("Update Edge"):
            # Use the object itself, not the index
            selected_edge["source"] = new_source
            selected_edge["target"] = new_target
            st.success("Edge updated")
            st.rerun()
        if col2.button("Delete Edge"):
            # Safe removal using object
            st.session_state.edges.remove(selected_edge)
            st.success("Edge deleted")
            st.rerun()

