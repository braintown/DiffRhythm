import subprocess
import os

def generate_and_separate_audio():
    # 第一步：生成音乐
    infer_cmd = [
        "python3", "infer/infer.py",
        "--lrc-path", "infer/example/eg_cn_full.lrc",
        "--ref-prompt", " pure music, hopeful mood, piano.",
        "--audio-length", "95",
        "--repo_id", "ASLP-lab/DiffRhythm-full",
        "--output-dir", "output/new",
        "--chunked"
    ]
    subprocess.run(infer_cmd, check=True)

    # 第二步：分离人声
    output_path = os.path.abspath("output") 
    docker_cmd = [
        "docker", "run",
        "--env", "HTTP_PROXY=http://10.7.100.40:9910",
        "--env", "HTTPS_PROXY=http://10.7.100.40:9910",
        "-v", f"{output_path}:/output",
        "researchdeezer/spleeter",
        "separate", "-p", "spleeter:2stems", "-o", "/output", "-i", "/output/new/output.wav"
    ]
    subprocess.run(docker_cmd, check=True)

# 第三步：裁剪前10秒
    input_file = os.path.join(output_path, "output", "accompaniment.wav")
    if not os.path.exists(input_file):  # 添加文件存在检查
        raise FileNotFoundError(f"Input file not found: {input_file}")

    output_dir = os.path.join(output_path, "finish")
    os.makedirs(output_dir, exist_ok=True)
    output_file = os.path.join(output_dir, "accompaniment_new.wav")
    ffmpeg_cmd = [
        "ffmpeg", "-i", input_file,
        "-ss", "0", "-t", "10",
        "-c", "copy", output_file
    ]
    subprocess.run(ffmpeg_cmd, check=True)

if __name__ == "__main__":
    generate_and_separate_audio()