# LM Studio Chat Template Patching for Tool-Calling Models

## The Problem

Some GGUF models ship with strict Jinja chat templates that block tool call IDs that don't match a rigid format (e.g., `tool_call.id|length != 9`). When Hermes uses longer tool call IDs than the template expects, the model raises a Jinja exception and generation fails with:

```
Error: Jinja Exception: Tool call IDs should be alphanumeric strings with length 9!
```

Cydonia 22B v1.3 is a notable example.

## Fix — Replace the template

In LM Studio, open the model's **Settings → Edit template** and replace with a simple ChatML-compatible template that preserves `bos_token` and `eos_token`:

```jinja
{# Handle optional system message #}
{%- if messages[0]["role"] == "system" %}
    {%- set system_message = messages[0]["content"] %}
{% endif %}
{# Start with BOS token #}
{{- bos_token }}
{# Render user/assistant pairs #}
{% for message in messages %}
  {% if message["role"] == "user" %}
    {%- if loop.last and system_message is defined %}
      {{- "[INST] " + system_message + "\\n\\n" + message["content"] + "[/INST]" }}
    {% else %}
      {{- "[INST] " + message["content"] + "[/INST]" }}
    {% endif %}
  {% elif message["role"] == "assistant" %}
      {{- " " + message["content"]|trim + eos_token }}
  {% endif %}
{% endfor %}
```

**Critical elements:**
- `{{- bos_token }}` and `{{ eos_token }}` — many models require these for proper tokenization
- `[INST]`/`[/INST]` — Mistral/ChatML format expected by Cydonia and similar models
- No tool-specific logic — tool call messages are silently skipped, preventing template parsing failures
- The system message is prepended to the first user message (common Mistral convention)

After pasting the template, click **Save & Reload** in LM Studio.

## Alternative — Remove only the ID-length check

If you want to keep the original template's tool-handling logic, find around line 62:
```jinja
{%- if not tool_call.id is defined or tool_call.id|length != 9 %}
    {{- raise_exception("Tool call IDs should be alphanumeric strings with length 9!") }}
{%- endif %}
```

Change to:
```jinja
{%- if not tool_call.id is defined %}
    {{- raise_exception("Tool call ID is missing!") }}
{%- endif %}
```

This preserves all existing functionality while accepting Hermes' longer tool call IDs.