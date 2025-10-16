#include "crypto_utils.h"
#include <openssl/evp.h>
#include <openssl/rand.h>
#include <openssl/sha.h>
#include <iomanip>
#include <sstream>

std::string encrypt_aes256_gcm(const std::string& plaintext, const std::string& key) {
    if (key.length() != 32) {
        return ""; // Key must be 32 bytes for AES-256
    }
    
    EVP_CIPHER_CTX* ctx = EVP_CIPHER_CTX_new();
    if (!ctx) {
        return "";
    }
    
    // Generate random IV
    unsigned char iv[12]; // GCM uses 12-byte IV
    if (RAND_bytes(iv, sizeof(iv)) != 1) {
        EVP_CIPHER_CTX_free(ctx);
        return "";
    }
    
    // Initialize encryption
    if (EVP_EncryptInit_ex(ctx, EVP_aes_256_gcm(), NULL, 
                          reinterpret_cast<const unsigned char*>(key.c_str()), iv) != 1) {
        EVP_CIPHER_CTX_free(ctx);
        return "";
    }
    
    // Encrypt
    std::vector<unsigned char> ciphertext(plaintext.length() + EVP_CIPHER_block_size(EVP_aes_256_gcm()));
    int len;
    int ciphertext_len;
    
    if (EVP_EncryptUpdate(ctx, ciphertext.data(), &len,
                         reinterpret_cast<const unsigned char*>(plaintext.c_str()), 
                         plaintext.length()) != 1) {
        EVP_CIPHER_CTX_free(ctx);
        return "";
    }
    ciphertext_len = len;
    
    if (EVP_EncryptFinal_ex(ctx, ciphertext.data() + len, &len) != 1) {
        EVP_CIPHER_CTX_free(ctx);
        return "";
    }
    ciphertext_len += len;
    
    // Get authentication tag
    unsigned char tag[16];
    if (EVP_CIPHER_CTX_ctrl(ctx, EVP_CTRL_GCM_GET_TAG, 16, tag) != 1) {
        EVP_CIPHER_CTX_free(ctx);
        return "";
    }
    
    EVP_CIPHER_CTX_free(ctx);
    
    // Combine IV + ciphertext + tag
    std::stringstream ss;
    ss << std::hex << std::setfill('0');
    
    // Add IV
    for (int i = 0; i < 12; i++) {
        ss << std::setw(2) << static_cast<int>(iv[i]);
    }
    
    // Add ciphertext
    for (int i = 0; i < ciphertext_len; i++) {
        ss << std::setw(2) << static_cast<int>(ciphertext[i]);
    }
    
    // Add tag
    for (int i = 0; i < 16; i++) {
        ss << std::setw(2) << static_cast<int>(tag[i]);
    }
    
    return ss.str();
}

std::string decrypt_aes256_gcm(const std::string& ciphertext, const std::string& key) {
    if (key.length() != 32 || ciphertext.length() < 56) { // 24 (IV) + 32 (tag) minimum
        return "";
    }
    
    EVP_CIPHER_CTX* ctx = EVP_CIPHER_CTX_new();
    if (!ctx) {
        return "";
    }
    
    // Parse hex string
    std::vector<unsigned char> data;
    for (size_t i = 0; i < ciphertext.length(); i += 2) {
        std::string byte_str = ciphertext.substr(i, 2);
        data.push_back(static_cast<unsigned char>(std::stoi(byte_str, nullptr, 16)));
    }
    
    if (data.size() < 28) { // 12 (IV) + 16 (tag) minimum
        EVP_CIPHER_CTX_free(ctx);
        return "";
    }
    
    // Extract components
    unsigned char iv[12];
    std::copy(data.begin(), data.begin() + 12, iv);
    
    std::vector<unsigned char> encrypted_data(data.begin() + 12, data.end() - 16);
    unsigned char tag[16];
    std::copy(data.end() - 16, data.end(), tag);
    
    // Initialize decryption
    if (EVP_DecryptInit_ex(ctx, EVP_aes_256_gcm(), NULL,
                          reinterpret_cast<const unsigned char*>(key.c_str()), iv) != 1) {
        EVP_CIPHER_CTX_free(ctx);
        return "";
    }
    
    // Decrypt
    std::vector<unsigned char> plaintext(encrypted_data.size() + EVP_CIPHER_block_size(EVP_aes_256_gcm()));
    int len;
    int plaintext_len;
    
    if (EVP_DecryptUpdate(ctx, plaintext.data(), &len,
                         encrypted_data.data(), encrypted_data.size()) != 1) {
        EVP_CIPHER_CTX_free(ctx);
        return "";
    }
    plaintext_len = len;
    
    // Set authentication tag
    if (EVP_CIPHER_CTX_ctrl(ctx, EVP_CTRL_GCM_SET_TAG, 16, tag) != 1) {
        EVP_CIPHER_CTX_free(ctx);
        return "";
    }
    
    if (EVP_DecryptFinal_ex(ctx, plaintext.data() + len, &len) != 1) {
        EVP_CIPHER_CTX_free(ctx);
        return "";
    }
    plaintext_len += len;
    
    EVP_CIPHER_CTX_free(ctx);
    
    return std::string(reinterpret_cast<char*>(plaintext.data()), plaintext_len);
}

std::string generate_aes256_key() {
    unsigned char key[32];
    if (RAND_bytes(key, sizeof(key)) != 1) {
        return "";
    }
    
    std::stringstream ss;
    ss << std::hex << std::setfill('0');
    for (int i = 0; i < 32; i++) {
        ss << std::setw(2) << static_cast<int>(key[i]);
    }
    
    return ss.str();
}

std::string sha256_hash(const std::string& input) {
    unsigned char hash[SHA256_DIGEST_LENGTH];
    SHA256_CTX sha256;
    SHA256_Init(&sha256);
    SHA256_Update(&sha256, input.c_str(), input.length());
    SHA256_Final(hash, &sha256);
    
    std::stringstream ss;
    ss << std::hex << std::setfill('0');
    for (int i = 0; i < SHA256_DIGEST_LENGTH; i++) {
        ss << std::setw(2) << static_cast<int>(hash[i]);
    }
    
    return ss.str();
}