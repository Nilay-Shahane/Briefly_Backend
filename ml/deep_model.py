import os
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
import torch  # Import torch to handle device placement

# Global variables
tokenizer = None 
model = None

def load():
    # FIX 1: Declare globals so we update the variables outside this function
    global tokenizer, model
    
    try:
        print('-- Checking Deep Model --')
        base_path = os.path.dirname(os.path.abspath(__file__)) 
        local_path = os.path.join(base_path, 'artifacts', 'distilbart_model')
        
        model_name = "sshleifer/distilbart-cnn-12-6"

        if os.path.exists(os.path.join(local_path, "config.json")):
            print(f'-- Loading from LOCAL path: {local_path} --')
            load_path = local_path
        else:
            print(f'-- Local model not found. Downloading: {model_name} --')
            load_path = model_name

        tokenizer = AutoTokenizer.from_pretrained(load_path)
        model = AutoModelForSeq2SeqLM.from_pretrained(load_path)
        
        # Optimization: Move to GPU if available
        device = "cuda" if torch.cuda.is_available() else "cpu"
        model.to(device)
        
        print(f'-- Deep Summarizer model loaded successfully on {device} --')
        
    except Exception as e:
        print(f'-- CRITICAL ERROR loading deep model: {e} --')

def predict(text: str, max_length: int ) -> str:
    global tokenizer, model
    
    if not model or not tokenizer:
        print("Model not loaded, attempting lazy load...")
        load()
        if not model:
            return "Error: Deep Model failed to load."

    # Preprocess
    clean_text = text.strip().replace("\n", " ")
    
    # Determine device
    device = model.device
    max_input_length = tokenizer.model_max_length


    # Tokenize (Move inputs to the same device as model)
    inputs = tokenizer(
        clean_text,
        max_length=max_input_length,
        truncation=True,
        return_tensors="pt"
    ).to(device)


    # FIX 2: Relax constraints. 
    # forcing min_length == max_length usually produces repetitive garbage.
    max_length = min(max_length, 200)
    summary_ids = model.generate(
    inputs["input_ids"],
    max_length=max_length,
    min_length=int(max_length * 0.5),
    do_sample=True,
    top_p=0.9,
    temperature=0.8,
    no_repeat_ngram_size=3,
    repetition_penalty=1.2
)



    return tokenizer.decode(summary_ids[0], skip_special_tokens=True)