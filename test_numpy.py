import subprocess
print(subprocess.run(["pip", "install", "-e", "."], capture_output=True, text=True).stdout)
