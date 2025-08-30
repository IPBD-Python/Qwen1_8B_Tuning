import gradio as gr
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline
from peft import PeftModel

base_model_path = "/root/autodl-tmp/model/Qwen25_1_5b"
lora_model_path = "/root/autodl-tmp/model/output/qwen2.5_1.5b_instruct_lora_0830_3/checkpoint-880"

tokenizer = AutoTokenizer.from_pretrained(base_model_path, trust_remote_code=True)

base_model = AutoModelForCausalLM.from_pretrained(
    base_model_path,
    torch_dtype=torch.float16,
    device_map="auto"
)

ft_model = AutoModelForCausalLM.from_pretrained(
    base_model_path,
    torch_dtype=torch.float16,
    device_map="auto"
)
ft_model = PeftModel.from_pretrained(ft_model, lora_model_path)

def generate_stream(model, tokenizer, prompt, max_new_tokens=512):
    inputs = tokenizer(prompt, return_tensors="pt").to(model.device)

    output_ids = model.generate(
        **inputs,
        max_new_tokens=max_new_tokens,
        do_sample=False,
        pad_token_id=tokenizer.eos_token_id
    )

    full_text = tokenizer.decode(output_ids[0], skip_special_tokens=True)

    if full_text.startswith(prompt):
        generated = full_text[len(prompt):].strip()
    else:
        generated = full_text.strip()

    yield generated


def compare_models(user_input):
    base_out = next(generate_stream(base_model, tokenizer, user_input))
    ft_out = next(generate_stream(ft_model, tokenizer, user_input))
    return base_out, ft_out


with gr.Blocks() as demo:
    gr.Markdown("## 药品问答模型对比 （原始模型 vs 微调模型）")

    with gr.Row():
        user_input = gr.Textbox(label="请输入药品相关问题", lines=3, placeholder="例如：请告诉我黄连的信息")

    with gr.Row():
        base_output = gr.Textbox(label="原始模型输出")
        ft_output = gr.Textbox(label="微调模型输出")

    submit_btn = gr.Button("生成回答")

    submit_btn.click(
        fn=compare_models,
        inputs=user_input,
        outputs=[base_output, ft_output]
    )

demo.launch(server_name="0.0.0.0", server_port=7860)
