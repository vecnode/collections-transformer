import os
import requests
from PIL import Image
from transformers import Blip2Processor, Blip2ForConditionalGeneration
import traceback
from datetime import datetime
import base64
import io

blip2_processor = None
blip2_model = None
blip2_model_name = None

def init_blip2(force_cpu=False):
    """Initialize Blip2 model"""
    global blip2_processor, blip2_model, blip2_model_name
    
    blip2_model_name = os.environ.get('BLIP2_MODEL_NAME', 'Salesforce/blip2-opt-2.7b')
    
    import torch
    
    # Determine device
    if force_cpu:
        device = "cpu"
        print(f"Initializing Blip2 model on CPU (forced)")
    else:
        device = "cuda" if torch.cuda.is_available() else "cpu"
        print(f"Initializing Blip2 model: {blip2_model_name} on {device}")
    
    try:
        # Load processor and model
        blip2_processor = Blip2Processor.from_pretrained(blip2_model_name)
        
        # Use lower precision on GPU to save memory
        model_dtype = None
        if device == "cuda":
            try:
                # Load model with float16, then explicitly move all components to CUDA
                blip2_model = Blip2ForConditionalGeneration.from_pretrained(
                    blip2_model_name,
                    torch_dtype=torch.float16  # Use half precision to save memory
                )
                # Explicitly move all components to CUDA
                blip2_model = blip2_model.to(device)
                model_dtype = torch.float16
                print(f"Loaded Blip2 with float16 precision for memory efficiency")
            except Exception as e:
                print(f"Warning: Could not load with float16/device_map, trying alternative: {e}")
                try:
                    # Fallback: load then move
                    blip2_model = Blip2ForConditionalGeneration.from_pretrained(
                        blip2_model_name,
                        torch_dtype=torch.float16
                    )
                    blip2_model = blip2_model.to(device)
                    model_dtype = torch.float16
                    print(f"Loaded Blip2 with float16 and moved to {device}")
                except Exception as e2:
                    print(f"Warning: Could not load with float16, using float32: {e2}")
                    blip2_model = Blip2ForConditionalGeneration.from_pretrained(blip2_model_name)
                    blip2_model = blip2_model.to(device)
                    model_dtype = torch.float32
        else:
            blip2_model = Blip2ForConditionalGeneration.from_pretrained(blip2_model_name)
            blip2_model = blip2_model.to(device)
            model_dtype = torch.float32
        
        # Ensure all model components are explicitly on the correct device
        # Blip2 has multiple sub-models (vision, qformer, language_model) that need to be on same device
        if hasattr(blip2_model, 'vision_model'):
            blip2_model.vision_model = blip2_model.vision_model.to(device)
        if hasattr(blip2_model, 'qformer'):
            blip2_model.qformer = blip2_model.qformer.to(device)
        if hasattr(blip2_model, 'language_model'):
            blip2_model.language_model = blip2_model.language_model.to(device)
        if hasattr(blip2_model, 'language_projection'):
            blip2_model.language_projection = blip2_model.language_projection.to(device)
        
        # Final check: verify ALL parameters are on the correct device
        # This catches any parameters that might have been missed
        wrong_device_params = []
        for name, param in blip2_model.named_parameters():
            if param.device.type != device.type if hasattr(device, 'type') else str(param.device) != str(device):
                wrong_device_params.append(f"{name} on {param.device}")
                param.data = param.data.to(device)
        
        if wrong_device_params:
            print(f"WARNING: Found {len(wrong_device_params)} parameters on wrong device, moved them:")
            for param_info in wrong_device_params[:5]:  # Print first 5
                print(f"  - {param_info}")
        
        blip2_model.eval()  # Set to evaluation mode
        
        # Clear cache after loading
        if device == "cuda":
            torch.cuda.empty_cache()
        
        print(f"Blip2 model loaded successfully on {device}")
        
    except Exception as e:
        print(f"Error initializing Blip2 model: {e}")
        print(traceback.format_exc())
        raise

def get_blip2_multimodal_response(primer_message, user_message, images, max_words=None):
    """Handle multimodal requests with images using Blip2"""
    global blip2_processor, blip2_model
    
    try:
        print("\n" + "=" * 80)
        print("BLIP2 MULTIMODAL API CALL")
        print("=" * 80)
        
        if blip2_processor is None or blip2_model is None:
            print("Blip2 model not initialized, initializing now...")
            init_blip2()
        
        print(f"Model: {blip2_model_name}")
        print(f"System Prompt: {primer_message[:100]}...")
        print(f"User Message: {user_message}")
        print(f"Images Count: {len(images)}")
        
        # Process each image
        responses = []
        for idx, image_data in enumerate(images):
            try:
                # Decode base64 image
                if isinstance(image_data, str):
                    # Remove data URI prefix if present
                    if image_data.startswith('data:image'):
                        image_data = image_data.split(',', 1)[1]
                    image_bytes = base64.b64decode(image_data)
                else:
                    image_bytes = image_data
                
                # Convert to PIL Image
                image = Image.open(io.BytesIO(image_bytes))
                print(f"[IMAGE {idx + 1}] Processed: {image.size}")
                
                # For Blip2, use pure image captioning (no text prompt) to get actual descriptions
                # This is the recommended approach per Blip2 documentation
                print(f"[BLIP2] Using pure image captioning (no text prompt)")
                
                # Get device and dtype from model before processing
                import torch
                device = next(blip2_model.parameters()).device
                model_dtype = next(blip2_model.parameters()).dtype
                
                # Process image without text prompt for pure captioning
                # Ensure processor creates tensors on the correct device
                inputs = blip2_processor(images=image, return_tensors="pt")
                
                # Move all inputs to same device and dtype as model
                # This ensures all tensors are on the same device
                # CRITICAL: All input tensors must be on the same device as the model
                for key, value in inputs.items():
                    if isinstance(value, torch.Tensor):
                        if value.dtype.is_floating_point:
                            inputs[key] = value.to(device=device, dtype=model_dtype)
                        else:
                            inputs[key] = value.to(device=device)
                
                # Verify all inputs are on correct device (debugging)
                print(f"[DEVICE CHECK] Model on: {device}, dtype: {model_dtype}")
                for key, value in inputs.items():
                    if isinstance(value, torch.Tensor):
                        if value.device.type != device.type if hasattr(device, 'type') else str(value.device) != str(device):
                            print(f"  WARNING: {key} is on {value.device}, expected {device}")
                        else:
                            print(f"  OK: {key} on {value.device}, dtype={value.dtype}")
                
                # Check GPU memory before generation
                if device == "cuda":
                    torch.cuda.empty_cache()  # Clear cache before generation
                    free_memory = torch.cuda.get_device_properties(0).total_memory - torch.cuda.memory_allocated(0)
                    print(f"[GPU MEMORY] Free: {free_memory / 1024**3:.2f} GB")
                
                # Generate response
                print(f"[GENERATING RESPONSE FOR IMAGE {idx + 1}]")
                # Calculate max_length based on max_words if provided, otherwise use a higher default for detailed descriptions
                # Default to 300 tokens (was 200) to encourage longer, more detailed descriptions
                max_length = int(max_words * 1.5) if max_words else 300
                
                try:
                    # Use generation parameters that encourage descriptive output
                    # Reduce num_beams on GPU if memory is tight
                    num_beams = 3 if device == "cuda" else 5
                    
                    with torch.no_grad():  # Disable gradient computation to save memory
                        generated_ids = blip2_model.generate(
                            **inputs, 
                            max_new_tokens=max_length,
                            num_beams=num_beams,
                            do_sample=True,
                            temperature=0.8,  # Increased from 0.7 to encourage more variation and detail
                            top_p=0.95,  # Increased from 0.9 to allow more diverse token selection
                            repetition_penalty=1.3,  # Increased from 1.2 to reduce repetition and encourage longer outputs
                            min_length=20  # Ensure minimum length for meaningful descriptions
                        )
                    
                    # Decode the full generated sequence (pure caption, no prompt to remove)
                    generated_text = blip2_processor.batch_decode(generated_ids, skip_special_tokens=True)[0].strip()
                    
                    # Ensure we have actual content
                    if len(generated_text) < 10:
                        print(f"[WARNING] Generated text is very short: '{generated_text}'")
                    
                    # Clear intermediate tensors
                    del generated_ids, inputs
                    if device == "cuda":
                        torch.cuda.empty_cache()
                    
                    responses.append(generated_text)
                    print(f"[RESPONSE {idx + 1}]\n{generated_text}\n")
                    
                except torch.cuda.OutOfMemoryError as oom_error:
                    print(f"[CUDA OOM] GPU out of memory, attempting CPU fallback...")
                    # Clear GPU cache
                    if device == "cuda":
                        torch.cuda.empty_cache()
                        del inputs
                    
                    # Try to reinitialize on CPU
                    try:
                        print("[FALLBACK] Reinitializing Blip2 on CPU...")
                        init_blip2(force_cpu=True)
                        
                        # Reprocess on CPU with pure image captioning
                        device = "cpu"
                        model_dtype = next(blip2_model.parameters()).dtype
                        inputs = blip2_processor(images=image, return_tensors="pt")
                        # Move all inputs to CPU with correct dtype
                        inputs = {k: v.to(device=device, dtype=model_dtype if v.dtype.is_floating_point else v.dtype) 
                                 for k, v in inputs.items()}
                        
                        with torch.no_grad():
                            generated_ids = blip2_model.generate(
                                **inputs, 
                                max_new_tokens=max_length,
                                num_beams=3,
                                do_sample=True,
                                temperature=0.7,
                                top_p=0.9,
                                repetition_penalty=1.2
                            )
                        
                        # Decode full sequence (pure caption, no prompt)
                        generated_text = blip2_processor.batch_decode(generated_ids, skip_special_tokens=True)[0].strip()
                        
                        del generated_ids, inputs
                        responses.append(generated_text)
                        print(f"[RESPONSE {idx + 1} (CPU)]\n{generated_text}\n")
                        
                    except Exception as cpu_error:
                        print(f"[ERROR] CPU fallback also failed: {cpu_error}")
                        responses.append(f"Error: Out of memory on GPU and CPU fallback failed")
                
            except Exception as img_error:
                print(f"Error processing image {idx + 1}: {img_error}")
                print(traceback.format_exc())
                # Clear cache on error
                import torch
                if torch.cuda.is_available():
                    torch.cuda.empty_cache()
                responses.append(f"Error processing image: {str(img_error)}")
        
        # Combine responses if multiple images
        if len(responses) == 1:
            response_text = responses[0]
        else:
            response_text = "\n\n".join([f"Image {i+1}: {resp}" for i, resp in enumerate(responses)])
        
        llm_end_time_ms = round(datetime.now().timestamp() * 1000)
        
        # Blip2 doesn't provide token usage, so we estimate
        estimated_tokens = len(response_text.split()) * 1.3
        token_usage = {
            "prompt_tokens": int(estimated_tokens * 0.3),
            "completion_tokens": int(estimated_tokens * 0.7),
            "total_tokens": int(estimated_tokens)
        }
        
        print(f"[TOKEN USAGE (ESTIMATED)]")
        print(f"Total Tokens: {token_usage['total_tokens']}")
        
        # Final memory cleanup
        import torch
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
            allocated = torch.cuda.memory_allocated(0) / 1024**3
            print(f"[GPU MEMORY AFTER] Allocated: {allocated:.2f} GB")
        
        print("=" * 80 + "\n")
        
        return {
            "status": "200",
            "res": response_text,
            "end": llm_end_time_ms,
            "token": token_usage
        }
    
    except Exception as e:
        print("\n" + "=" * 80)
        print("ERROR in get_blip2_multimodal_response")
        print("=" * 80)
        print(str(e))
        print(traceback.format_exc())
        print("=" * 80 + "\n")
        return {
            "status": "400",
            "error": str(e)
        }
