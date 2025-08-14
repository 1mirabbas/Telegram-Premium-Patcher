#!/bin/bash

# Clean up previous files and directories
rm -rf signed_tg.apk.idsig android-app-hack.keystore signed_tg.apk

# Variables
KEYSTORE_NAME="android-app-hack.keystore"
ALIAS_NAME="alias_name_test"
APK_NAME="unsigned_tg.apk"
SIGNED_APK="signed_tg.apk"
PASSWORD="testtest"

# Step 1: Generate Keystore
echo "Generating keystore..."
keytool -genkey -v -keystore ./$KEYSTORE_NAME -alias $ALIAS_NAME -keyalg RSA -keysize 2048 -validity 365 \
  -storepass $PASSWORD -keypass $PASSWORD \
  -dname "CN=John Doe, OU=Development, O=MyCompany, L=MyCity, S=MyState, C=US"
if [ $? -ne 0 ]; then
    echo "Keystore generation failed."
    exit 1
fi

# Step 2: Sign APK with jarsigner
echo "Signing APK..."
jarsigner -verbose -sigalg SHA256withRSA -digestalg SHA-256 -keystore $KEYSTORE_NAME $APK_NAME $ALIAS_NAME \
  -storepass $PASSWORD
if [ $? -ne 0 ]; then
    echo "APK signing failed."
    exit 1
fi

# Step 3: Align APK with zipalign
echo "Aligning APK..."
zipalign -v 4 $APK_NAME $SIGNED_APK
if [ $? -ne 0 ]; then
    echo "APK alignment failed."
    exit 1
fi

# Step 4: Verify APK alignment
echo "Verifying APK alignment..."
zipalign -c -v 4 $SIGNED_APK
if [ $? -ne 0 ]; then
    echo "APK alignment verification failed."
    exit 1
fi

# Step 5: Sign APK with apksigner
echo "Signing APK with apksigner..."
apksigner sign --ks $KEYSTORE_NAME --ks-key-alias $ALIAS_NAME --key-pass pass:$PASSWORD --ks-pass pass:$PASSWORD $SIGNED_APK
if [ $? -ne 0 ]; then
    echo "APK signing with apksigner failed."
    exit 1
fi

# Step 6: Verify APK signature
echo "Verifying APK signature..."
apksigner verify $SIGNED_APK
if [ $? -ne 0 ]; then
    echo "APK signature verification failed."
    exit 1
fi

echo "Process completed successfully!"