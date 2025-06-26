from flask import Flask, request, jsonify
import subprocess

app = Flask(__name__)


@app.route('/run', methods=['POST'])
def run_prompt():
    data = request.get_json()
    prompt = data.get('prompt', '')

    result = subprocess.run(
        ["./main", "-m", "phi-2.Q3_K_S.gguf", "-p", prompt],
        cwd="./llama.cpp",
        capture_output=True,
        text=True
    )

    return jsonify({"output": result.stdout.strip()})


if __name__ == "__main__":
    app.run(host="localhost", port=8080)
