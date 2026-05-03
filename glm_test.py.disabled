import os
import sys
import subprocess

# Set GLM API key
os.environ['GLM_API_KEY'] = "e9e8d21009de48cbbf5c8716723b657c.sBWLPPEgla698Mls"

# Run the batch test
cmd = [sys.executable, "src/tepsa_api_batch.py", "--run-id", "glm_batch", "--max-tasks", "50", "--policy-ids", "pl_glm_47,pl_glm_47_flashx", "--providers", "GLM"]
print("Running command:", " ".join(cmd))
result = subprocess.run(cmd, capture_output=True, text=True)

print("STDOUT:")
print(result.stdout)
print("STDERR:")
print(result.stderr)
print("Return code:", result.returncode)