
# VFS Extension for Stable Diffusion WebUI

## Overview
The VFS (Video Frame Stylizer) Extension is a transformative plugin for the Stable Diffusion WebUI that allows users to convert videos into stylized animations. This tool processes videos by breaking them down into frames, creating masks, extracting keyframes, and supporting seamless Img2Img workflows. 

## Features
- **Frame Extraction**: Supports multiple video formats like .mp4, .mov, .avi, and organizes extracted frames numerically in a project directory.
- **Mask Creation**: Uses the transparent-background library to automatically generate precise masks for video frames with options for Fast and JIT mode.
- **Keyframe Extraction**: Efficient algorithms identify significant frames, with options to include the first and last frames of a video.
- **File Management**: Includes functionalities to rename Img2Img output files and generate paths for streamlined batch processing.
- **Project Structure**: Outputs are organized into intuitive directories (video_frames, video_masks, keyframes, etc.), making it easy to manage large projects.
- **User Interface**: Features a clean, tabbed interface built with Gradio, providing an intuitive setup for handling projects.

## Installation

### Clone the Repository
\`\`\`bash
git clone https://github.com/babydjac/VFS-Extension.git
\`\`\`
Place the cloned repository into your Stable Diffusion WebUI extensions folder.

### Install Dependencies
\`\`\`bash
pip install -r requirements.txt
\`\`\`
Restart your Stable Diffusion WebUI to apply changes.

## Usage
### Step 1: Frame Extraction
1. Upload a video file in the "Frame Xtract" tab.
2. Enter a Project Title to organize output into a dedicated folder.
3. Click "Extract Frames" and preview the initial frames in the gallery.

### Step 2: Mask Creation
1. Navigate to the "Mask Xtract" tab.
2. Re-enter the Project Title used in Frame Extraction.
3. Adjust settings (Fast Mode or JIT Mode) if needed and generate masks.

### Step 3: Keyframe Extraction
1. Access the "Keyframe Xtract" tab.
2. Input the Project Title and decide on frame inclusion at the video's boundaries.
3. Extract and organize keyframes into folders.

### Step 4: Img2Img Paths
1. Use the "Img2Img Path" tab to generate paths for batch processing.

### Step 5: Rename Files
1. In the "Rename Files" tab, input the Project Title to update filenames in the img2img_output folder for better organization.

## Advanced Configuration
- **Masking Parameters**: Customize masking parameters by adjusting the create_masks function in main_ui.py.
- **Keyframe Splitting**: Manage the distribution of keyframes into subfolders based on the max_keyframes_per_folder setting.
- **Rename Logic**: Modify the rename_files function to apply custom file renaming logic.

## Project Directory Structure
After using VFS Extension, your project folder will organize outputs as follows:

\`\`\`
<Project_Title>/
├── video_frames/
│   ├── 00001.png
│   ├── 00002.png
│   └── ...
├── video_masks/
│   ├── 00001.png
│   ├── 00002.png
│   └── ...
├── keyframes/
│   ├── 00001.png
│   ├── 00008.png
│   └── ...
├── img2img_output/
│   ├── stylized_01.png
│   ├── stylized_02.png
│   └── ...
\`\`\`

## Troubleshooting
- **Extension Not Visible in WebUI**: Check the repository placement in the extensions folder and restart the WebUI.
- **Error in Masking**: Confirm installation of transparent-background==1.3.2 and GPU support.
- **Keyframes Not Detected**: Ensure frames are extracted prior to keyframe extraction.

## Contributing
Contributions are welcome! To contribute:
1. Fork the repository on GitHub.
2. Create a new branch for your feature or fix.
3. Submit a pull request with a detailed description of your changes.

## License
This project is licensed under the MIT License - see the LICENSE file for details.
