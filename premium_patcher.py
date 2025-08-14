import requests
import subprocess
import shutil
import os

def download_telegram_apk():
    print("Downloading Telegram.apk...")
    url = "https://telegram.org/dl/android/apk"
    response = requests.get(url, stream=True)
    
    if response.status_code == 200:
        with open("Telegram.apk", "wb") as apk_file:
            for chunk in response.iter_content(chunk_size=1024):
                if chunk:
                    apk_file.write(chunk)
        print("✅ Downloaded APK: Telegram.apk")
    else:
        print("❌ Failed to download APK! Status code:", response.status_code)

def get_apk_sha256():
    result = subprocess.run(
        ["keytool", "-printcert", "-jarfile", "Telegram.apk"],
        capture_output=True,
        text=True
    )
    if result.returncode == 0:
        for line in result.stdout.splitlines():
            if "SHA256:" in line:
                sha256_value = line.split("SHA256:")[1].strip().replace(":", "")
                print("🔐 SHA-256 value:", sha256_value)
                return sha256_value
    else:
        print("❌ Failed to get SHA-256. Error:", result.stderr)
        return None

def decompile_apk():
    if os.path.exists("Decompile"):
        shutil.rmtree("Decompile")
    result = subprocess.run(
        ["apktool", "d", "-r", "Telegram.apk", "-o", "Decompile"],
        capture_output=True,
        text=True
    )
    if result.returncode == 0:
        print("📦 APK successfully decompiled → 'Decompile/'")
    else:
        print("❌ Decompilation failed:", result.stderr)

def edit_smali_file(output_dir, sha256_value):
    smali_file_path = None
    for root, dirs, files in os.walk(output_dir):
        if "AndroidUtilities.smali" in files:
            smali_file_path = os.path.join(root, "AndroidUtilities.smali")
            break

    if smali_file_path:
        try:
            with open(smali_file_path, 'r') as file:
                lines = file.readlines()

            with open(smali_file_path, 'w') as file:
                inside_function = False
                for line in lines:
                    if ".method" in line and "getCertificateSHA256Fingerprint" in line:
                        inside_function = True
                        file.write('.method public static getCertificateSHA256Fingerprint()Ljava/lang/String;\n')
                        file.write('    .locals 1\n\n')
                        file.write(f'    const-string v0, "{sha256_value}"\n\n')
                        file.write('    return-object v0\n')
                        file.write('.end method\n')
                    elif inside_function and ".end method" in line:
                        inside_function = False
                    elif not inside_function:
                        file.write(line)
            print("🛠️ AndroidUtilities.smali has been modified.")
        except Exception as e:
            print("❌ Failed to edit AndroidUtilities.smali:", str(e))
    else:
        print("❌ AndroidUtilities.smali not found.")

def replace_ispremium_with_constant_true(output_dir):
    userconfig_path = None
    for root, dirs, files in os.walk(output_dir):
        if "UserConfig.smali" in files:
            userconfig_path = os.path.join(root, "UserConfig.smali")
            break

    if userconfig_path:
        try:
            with open(userconfig_path, 'r') as file:
                lines = file.readlines()

            with open(userconfig_path, 'w') as file:
                inside_method = False
                method_written = False

                for line in lines:
                    if ".method" in line and "isPremium()Z" in line:
                        inside_method = True
                        method_written = True
                        file.write(".method public isPremium()Z\n")
                        file.write("    .locals 1\n\n")
                        file.write("    const/4 v0, 0x1\n\n")
                        file.write("    return v0\n\n")
                        file.write("    iget-object v0, p0, Lorg/telegram/messenger/UserConfig;->currentUser:Lorg/telegram/tgnet/TLRPC$User;\n\n")
                        file.write("    if-nez v0, :cond_0\n\n")
                        file.write("    const/4 v0, 0x0\n\n")
                        file.write("    return v0\n\n")
                        file.write("    :cond_0\n")
                        file.write("    iget-boolean v0, v0, Lorg/telegram/tgnet/TLRPC$User;->premium:Z\n\n")
                        file.write("    return v0\n")
                        file.write(".end method\n")
                        continue
                    if inside_method:
                        if ".end method" in line:
                            inside_method = False
                        continue
                    else:
                        file.write(line)

            if method_written:
                print("🟢 isPremium() method has been overridden to always return true.")
            else:
                print("⚠️ isPremium() method not found, no changes made.")
        except Exception as e:
            print("❌ An error occurred:", str(e))
    else:
        print("❌ UserConfig.smali file not found.")

def build_apk():
    result = subprocess.run(
        ["apktool", "b", "Decompile", "-r"],
        capture_output=True,
        text=True
    )
    if result.returncode == 0:
        print("📦 APK successfully rebuilt.")
        built_apk_path = os.path.join("Decompile", "dist", "Telegram.apk")
        if os.path.exists(built_apk_path):
            shutil.copy2(built_apk_path, "unsigned_tg.apk")
            print("📤 Copied as unsigned_tg.apk.")
            try:
                subprocess.run(["./signer.sh"], check=True)
                print("🔏 APK successfully signed with signer.sh.")
            except subprocess.CalledProcessError as e:
                print("❌ Error while running signer.sh:", e)
        else:
            print("❌ Rebuilt APK not found.")
    else:
        print("❌ APK build failed:", result.stderr)

# 🔄 Main process chain
download_telegram_apk()                                   # 1. Download APK
sha256_value = get_apk_sha256()                           # 2. Get SHA256 fingerprint
decompile_apk()                                           # 3. Decompile APK
if sha256_value:
    edit_smali_file("Decompile", sha256_value)            # 4. Bypass SHA check
replace_ispremium_with_constant_true("Decompile")         # 5. Override isPremium() to return true
build_apk()                                               # 6. Build + sign

