from datasets import Dataset
import pandas as pd
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM, DataCollatorForSeq2Seq, TrainingArguments, Trainer
from peft import LoraConfig, TaskType, get_peft_model

def process_func(example, tokenizer, system_prompt="You are a helpful assistant.", max_length=1024):
    """
    Qwen2 数据预处理函数

    Args:
        example: 训练样本
        tokenizer: 分词器
        system_prompt: 系统角色提示，默认为通用助手
        max_length: 最大token长度

    Returns:
        预处理后的模型输入字典
    """
    full_prompt = (
        f"<|im_start|>system\n{system_prompt}<|im_end|>\n"
        f"<|im_start|>user\n{example['instruction'] + example['input']}<|im_end|>\n"
        f"<|im_start|>assistant\n{example['output']}<|im_end|>"
    )

    encoded = tokenizer(
        full_prompt,
        truncation=True,
        max_length=max_length,
        add_special_tokens=False
    )

    prompt_length = len(tokenizer(
        f"<|im_start|>system\n{system_prompt}<|im_end|>\n"
        f"<|im_start|>user\n{example['instruction'] + example['input']}<|im_end|>\n"
        f"<|im_start|>assistant\n",
        )['input_ids']
    )

    labels = encoded['input_ids'].copy()
    labels[:prompt_length] = [-100] * prompt_length

    return {
        "input_ids": encoded['input_ids'],
        "attention_mask": encoded['attention_mask'],
        "labels": labels
    }


model_path = "/root/autodl-tmp/model/Qwen25_1_5b"

model = AutoModelForCausalLM.from_pretrained(
    model_path,
    torch_dtype=torch.float16,   
    device_map="auto"           
)

tokenizer = AutoTokenizer.from_pretrained(
    model_path,
    trust_remote_code=True       
)

#训练数据集
df = pd.read_json('/root/autodl-tmp/model/datasets/medData.json')
ds = Dataset.from_pandas(df)

tokenized_id = ds.map(
    lambda x: process_func(
        x,
        tokenizer=tokenizer,   
        system_prompt="你是一个智能药房主理人，你需要回答用户询问的药品信息"
    ),
    remove_columns=ds.column_names
)

config = LoraConfig(
    task_type=TaskType.CAUSAL_LM,
    target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
    r=8,
    lora_alpha=32,
    lora_dropout=0.1,
    inference_mode=False
)



model = get_peft_model(model, config)

model.print_trainable_parameters()

args = TrainingArguments(
    output_dir="/root/autodl-tmp/model/output/qwen2.5_1.5b_instruct_lora_0830_3",
    num_train_epochs=20,
    learning_rate=1e-4,

    per_device_train_batch_size=2,    
    gradient_accumulation_steps=4,    

    save_on_each_node=False,           

    gradient_checkpointing=False,      
    bf16=True,                         

    logging_steps=10,
    save_steps=100,
)

if args.gradient_checkpointing:
    model.enable_input_require_grads()

trainer = Trainer(
    model=model,               
    args=args,                  # 必需: 训练参数
    train_dataset=tokenized_id, # 必需: 训练数据集
    data_collator=DataCollatorForSeq2Seq( # 必需: 数据整理器
        tokenizer=tokenizer,
        padding=True,
    ),
)

trainer.train()
