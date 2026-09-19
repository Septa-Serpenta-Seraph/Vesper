#!/usr/bin/env python3
"""Flatten a ComfyUI UI-format workflow JSON into API-format prompt.

Correct link mapping (verified 2026-08-12 while building the LTX-2.3 I2V
payload): walk each UI node's `inputs` (name -> link id), resolve links via
the top-level `links` table [link_id, src_node, src_slot, dst_node, dst_slot,
type], and fill unlinked inputs from `widgets_values` in object_info input
order. A naive "widgets fill everything" flattener produces wrong links
(e.g. VAE/image/latent all pointing at the checkpoint node) — use this one.

Usage: flatten_comfy_workflow.py <ui_workflow.json> <object_info.json> <out_api.json>
object_info: save from http://127.0.0.1:8188/object_info via the SSH tunnel.

After flattening, apply the post-flatten fix table in the parent skill
(ClownSampler swap, GemmaAPITextEncode removal, bit_depth, dynamic-COMBO
dotted flat keys, model filenames, LoadImage input file).
"""
import json
import sys


def flatten(ui, objinfo):
    nodes = {str(n["id"]): n for n in ui["nodes"]}
    # link: [link_id, src_node, src_slot, dst_node, dst_slot, type]
    link_map = {}
    for link in ui.get("links", []):
        if len(link) >= 5:
            link_map[link[0]] = (link[1], link[2])

    prompt = {}
    for nid, n in nodes.items():
        ntype = n.get("type", "")
        # skip non-node UI elements
        if ntype in ("MarkdownNote", "Note", "PreviewAudio"):
            continue
        if ntype not in objinfo:
            print(f"  !! node {nid} type {ntype} NOT in object_info", file=sys.stderr)
            continue

        info = objinfo[ntype]
        # ordered input spec: required + optional
        input_spec = []
        for section in ("required", "optional"):
            for name, spec in info.get("input", {}).get(section, {}).items():
                input_spec.append((name, spec))

        # map UI inputs by name -> link id
        ui_inputs = {}
        for inp in n.get("inputs", []):
            ui_inputs[inp["name"]] = inp.get("link")

        widgets = list(n.get("widgets_values", []))
        wi = 0
        inputs = {}
        for iname, spec in input_spec:
            if iname in ui_inputs and ui_inputs[iname] is not None:
                link_id = ui_inputs[iname]
                if link_id in link_map:
                    src_node, src_slot = link_map[link_id]
                    inputs[iname] = [str(src_node), src_slot]
                    continue
            # no link: consume widget in order
            if wi < len(widgets):
                inputs[iname] = widgets[wi]
                wi += 1
        prompt[nid] = {"class_type": ntype, "inputs": inputs}
    return prompt


if __name__ == "__main__":
    ui_path, obj_path, out_path = sys.argv[1], sys.argv[2], sys.argv[3]
    ui = json.load(open(ui_path))
    obj = json.load(open(obj_path))
    prompt = flatten(ui, obj)
    json.dump(prompt, open(out_path, "w"), indent=2)
    print(f"flattened {len(prompt)} nodes -> {out_path}")
