from flask import Flask, request, jsonify
import subprocess
import os
import time 

app = Flask(__name__)

@app.route('/generate', methods=['POST'])
def generate_and_separate_audio():
    # 获取请求参数
    data = request.json
    ref_prompt = data.get('ref_prompt', ' pure music, hopeful mood, piano.')
    # start_time = data.get('start_time', 0)
    duration = data.get('duration', 10)

    # 第一步：生成音乐
    infer_cmd = [
        "python3", "infer/infer.py",
        "--lrc-path", "infer/example/eg_cn_full.lrc",
        "--ref-prompt", ref_prompt,
        "--audio-length","95" if  duration <= 95 else "285",
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

    # 第三步：裁剪音频
    input_file = os.path.join(output_path, "output", "accompaniment.wav")
    if not os.path.exists(input_file):
        return jsonify({"error": f"Input file not found: {input_file}"}), 404

    output_dir = os.path.join(output_path, "finish")
    os.makedirs(output_dir, exist_ok=True)
    # 使用时间戳生成唯一文件名
    timestamp = int(time.time())
    output_file = os.path.join(output_dir, f"accompaniment_{timestamp}.wav")
    ffmpeg_cmd = [
        "ffmpeg", "-i", input_file,
        "-ss", "0", "-t", str(duration),
        "-c", "copy", output_file
    ]
    subprocess.run(ffmpeg_cmd, check=True)

    return jsonify({
        "status": "success",
        "output_file": output_file
    })

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)