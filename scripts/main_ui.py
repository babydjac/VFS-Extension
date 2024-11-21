import os
import sys
import gradio as gr
import shutil
import glob
from PIL import Image
import subprocess
import math
import cv2
import torch
from transparent_background import Remover
from moviepy.video.io.ImageSequenceClip import ImageSequenceClip
import numpy as np

# Ensure the script directory is added to the Python module search path
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPT_DIR not in sys.path:
    sys.path.append(SCRIPT_DIR)

# Paths
WEBUI_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "../../.."))
PARENT_DIR = os.path.dirname(WEBUI_ROOT)

# Utility Functions
def sort_frames_numerically(folder_path):
    return sorted(
        [os.path.join(folder_path, f) for f in os.listdir(folder_path) if f.lower().endswith(('.png', '.jpg', '.jpeg'))],
        key=lambda x: int(''.join(filter(str.isdigit, os.path.basename(x)))),
    )

def interpolate_frames(img1, img2, num_intermediate_frames):
    """Generate intermediate frames between two images using optical flow."""
    prev = cv2.cvtColor(np.array(img1), cv2.COLOR_RGB2GRAY)
    next = cv2.cvtColor(np.array(img2), cv2.COLOR_RGB2GRAY)

    # Calculate dense optical flow
    flow = cv2.calcOpticalFlowFarneback(
        prev, next, None, 0.5, 3, 15, 3, 5, 1.2, 0
    )

    intermediate_frames = []
    for t in range(1, num_intermediate_frames + 1):
        alpha = t / (num_intermediate_frames + 1)
        warped = cv2.addWeighted(np.array(img1), 1 - alpha, np.array(img2), alpha, 0)
        intermediate_frames.append(Image.fromarray(warped.astype(np.uint8)))

    return intermediate_frames

# Frame Extraction Function
def extract_frames(video_file, project_title):
    output_dir = os.path.join(PARENT_DIR, project_title, "video_frames")
    os.makedirs(output_dir, exist_ok=True)
    temp_video_path = os.path.join(output_dir, "uploaded_video.mp4")
    shutil.copy(video_file.name, temp_video_path)

    try:
        fps_command = f"ffprobe -v 0 -of csv=p=0 -select_streams v:0 -show_entries stream=r_frame_rate {temp_video_path}"
        fps_output = subprocess.check_output(fps_command, shell=True).decode().strip()
        numerator, denominator = map(int, fps_output.split('/'))
        video_fps = numerator / denominator
    except Exception as e:
        return None, f"Error extracting FPS: {e}"

    fps_file = os.path.join(output_dir, "fps.txt")
    with open(fps_file, "w") as f:
        f.write(str(video_fps))

    frame_path_template = os.path.join(output_dir, "%05d.png")
    ffmpeg_command = f"ffmpeg -i {temp_video_path} -qscale:v 2 -f image2 -c:v png {frame_path_template}"
    subprocess.call(ffmpeg_command, shell=True)

    frame_paths = sorted(glob.glob(os.path.join(output_dir, "*.png")))
    preview_images = [Image.open(frame) for frame in frame_paths[:5]]
    return preview_images, f"Frames saved to {output_dir}. FPS: {video_fps:.2f}"

# Mask Creation Function
def create_masks(project_title, use_fast_mode=False, use_jit=True):
    frame_dir = os.path.join(PARENT_DIR, project_title, "video_frames")
    mask_dir = os.path.join(PARENT_DIR, project_title, "video_masks")
    os.makedirs(mask_dir, exist_ok=True)

    try:
        device = "cuda" if torch.cuda.is_available() else "cpu"
        remover = Remover(fast=use_fast_mode, jit=use_jit, device=device)
    except Exception as e:
        return f"Error initializing Remover: {e}"

    frame_paths = sorted(glob.glob(os.path.join(frame_dir, "*.png")))
    for frame_path in frame_paths:
        base_name = os.path.basename(frame_path)
        image = Image.open(frame_path).convert("RGB")
        try:
            mask = remover.process(image, type="map")
            if isinstance(mask, Image.Image):
                mask = mask.convert("L")
            else:
                mask = Image.fromarray(mask).convert("L")
            mask.save(os.path.join(mask_dir, base_name))
        except Exception as e:
            return f"Error processing frame {base_name}: {e}"

    return f"Masks saved to {mask_dir}"

# Keyframe Extraction Function
def extract_keyframes(project_title, include_first_last=False, max_keyframes_per_folder=20):
    frame_dir = os.path.join(PARENT_DIR, project_title, "video_frames")
    keyframe_dir = os.path.join(PARENT_DIR, project_title, "keyframes")

    if not os.path.exists(frame_dir):
        return "Ensure 'video_frames' directory exists in the project folder."

    frame_paths = sorted(glob.glob(os.path.join(frame_dir, "*.png")))

    if len(frame_paths) < 2:
        return "Not enough frames for keyframe extraction."

    os.makedirs(keyframe_dir, exist_ok=True)
    keyframe_indices = []

    for i in range(len(frame_paths)):
        if include_first_last and (i == 0 or i == len(frame_paths) - 1):
            keyframe_indices.append(i)
        elif i % 8 == 0:
            keyframe_indices.append(i)

    if len(keyframe_indices) <= max_keyframes_per_folder:
        for idx in keyframe_indices:
            shutil.copy(frame_paths[idx], os.path.join(keyframe_dir, os.path.basename(frame_paths[idx])))
        return "Keyframes saved to root project directory."

    num_chunks = math.ceil(len(keyframe_indices) / max_keyframes_per_folder)
    for chunk_index in range(num_chunks):
        subfolder_name = str(chunk_index + 1)
        subfolder_path = os.path.join(PARENT_DIR, project_title, subfolder_name)
        os.makedirs(os.path.join(subfolder_path, "video_frames"), exist_ok=True)
        os.makedirs(os.path.join(subfolder_path, "keyframes"), exist_ok=True)

        start_idx = int(chunk_index * max_keyframes_per_folder)
        end_idx = int(min((chunk_index + 1) * max_keyframes_per_folder, len(keyframe_indices)))
        current_keyframe_indices = keyframe_indices[start_idx:end_idx]

        for idx in current_keyframe_indices:
            shutil.copy(frame_paths[idx], os.path.join(subfolder_path, "video_frames", os.path.basename(frame_paths[idx])))
            shutil.copy(frame_paths[idx], os.path.join(subfolder_path, "keyframes", os.path.basename(frame_paths[idx])))

    return f"Keyframes split into {num_chunks} folders."

# Rename Function
def rename_files(project_title):
    # Define the base project directory
    project_dir = os.path.join(PARENT_DIR, project_title)
    
    if not os.path.exists(project_dir):
        return f"Project directory '{project_title}' does not exist under '{PARENT_DIR}'."

    # List to collect all 'img2img_output' directories
    img2img_output_dirs = []

    # Walk through the project directory and all subdirectories
    for root, dirs, files in os.walk(project_dir):
        if "img2img_output" in dirs:
            img2img_output_dirs.append(os.path.join(root, "img2img_output"))

    if not img2img_output_dirs:
        return f"No 'img2img_output' folders found in project: {project_title}. Check your project structure."

    renamed_count = 0

    # Iterate through each found 'img2img_output' directory
    for output_dir in img2img_output_dirs:
        print(f"Searching in: {output_dir}")  # Debugging statement
        for file_path in sorted(glob.glob(os.path.join(output_dir, "*.png"))):
            file_name = os.path.basename(file_path)
            print(f"Found file: {file_name}")  # Debugging statement

            # Look for files with a hyphen in their name
            if "-" in file_name:
                new_name = file_name.split("-")[-1]  # Take everything after the last hyphen
                new_path = os.path.join(output_dir, new_name)

                # Avoid overwriting existing files
                if not os.path.exists(new_path):
                    os.rename(file_path, new_path)
                    renamed_count += 1
                    print(f"Renamed {file_name} to {new_name}")  # Debugging statement
                else:
                    print(f"Skipping rename for {file_name}, target {new_name} already exists.")  # Debugging statement

    if renamed_count == 0:
        return "No files were renamed. Ensure file names contain hyphens and are located in 'img2img_output' folders."

    return f"Renamed {renamed_count} files across all 'img2img_output' folders in project: {project_title}."

# Img2Img Path Function
def generate_img2img_paths(project_title):
    keyframe_dirs = sorted(glob.glob(os.path.join(PARENT_DIR, project_title, "[0-9]*")))
    paths = []

    if not keyframe_dirs:
        paths.append(f"Input: {os.path.join(PARENT_DIR, project_title, 'keyframes')}")
        paths.append(f"Mask: {os.path.join(PARENT_DIR, project_title, 'video_masks')}")
        paths.append(f"Output: {os.path.join(PARENT_DIR, project_title, 'img2img_output')}")
    else:
        for subfolder in keyframe_dirs:
            input_dir = os.path.join(subfolder, "keyframes")
            mask_dir = os.path.join(subfolder, "video_masks")
            output_dir = os.path.join(subfolder, "img2img_output")
            paths.append(f"Input: {input_dir}\nMask: {mask_dir}\nOutput: {output_dir}")

    return "\n\n".join(paths)

# UI
def main_ui():
    with gr.Blocks() as vfs_interface:
        with gr.Tabs():
            with gr.Tab("Frame Xtract"):
                video_file = gr.File(label="Upload Video", file_types=[".mp4", ".mov", ".avi"])
                project_title = gr.Textbox(label="Project Title")
                extract_button = gr.Button("Extract Frames")
                frame_preview = gr.Gallery(label="Frame Previews", columns=5, height="auto")
                output_message = gr.Markdown()

                extract_button.click(
                    fn=extract_frames,
                    inputs=[video_file, project_title],
                    outputs=[frame_preview, output_message]
                )

            with gr.Tab("Mask Xtract"):
                project_title_mask = gr.Textbox(label="Project Title")
                fast_mode = gr.Checkbox(label="Use Fast Mode", value=False)
                jit_mode = gr.Checkbox(label="Use JIT Mode", value=True)
                create_mask_button = gr.Button("Create Masks")
                mask_output_message = gr.Markdown()

                create_mask_button.click(
                    fn=create_masks,
                    inputs=[project_title_mask, fast_mode, jit_mode],
                    outputs=[mask_output_message]
                )

            with gr.Tab("Keyframe Xtract"):
                project_title_keyframe = gr.Textbox(label="Project Title")
                include_first_last = gr.Checkbox(label="Include First and Last Frame", value=False)
                extract_keyframes_button = gr.Button("Extract Keyframes")
                keyframe_output_message = gr.Markdown()

                extract_keyframes_button.click(
                    fn=extract_keyframes,
                    inputs=[project_title_keyframe, include_first_last],
                    outputs=[keyframe_output_message]
                )

            with gr.Tab("Img2Img Path"):
                project_title_batch = gr.Textbox(label="Project Title")
                batch_button = gr.Button("Generate Paths")
                batch_output_message = gr.Markdown()

                batch_button.click(
                    fn=generate_img2img_paths,
                    inputs=[project_title_batch],
                    outputs=[batch_output_message]
                )

            with gr.Tab("Rename Files"):
                project_title_rename = gr.Textbox(label="Project Title")
                rename_button = gr.Button("Rename Files")
                rename_output_message = gr.Markdown()

                rename_button.click(
                    fn=rename_files,
                    inputs=[project_title_rename],
                    outputs=[rename_output_message]
                )

    return vfs_interface

from modules import script_callbacks
script_callbacks.on_ui_tabs(lambda: [(main_ui(), "VFS", "vfs")])