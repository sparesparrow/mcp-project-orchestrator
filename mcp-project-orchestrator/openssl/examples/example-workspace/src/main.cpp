#include <iostream>
#include <openssl/evp.h>
#include <openssl/rand.h>
#include "crypto_utils.h"

int main() {
    std::cout << "OpenSSL Example with Cursor AI Configuration" << std::endl;
    
    // Initialize OpenSSL
    OpenSSL_add_all_algorithms();
    
    // Test random number generation
    unsigned char random_bytes[32];
    if (RAND_bytes(random_bytes, sizeof(random_bytes)) != 1) {
        std::cerr << "Failed to generate random bytes" << std::endl;
        return 1;
    }
    
    std::cout << "Generated random bytes successfully" << std::endl;
    
    // Test encryption
    std::string plaintext = "Hello, OpenSSL!";
    std::string encrypted = encrypt_aes256_gcm(plaintext, "secret_key_32_bytes_long_12345");
    
    if (encrypted.empty()) {
        std::cerr << "Encryption failed" << std::endl;
        return 1;
    }
    
    std::cout << "Encryption successful" << std::endl;
    
    // Test decryption
    std::string decrypted = decrypt_aes256_gcm(encrypted, "secret_key_32_bytes_long_12345");
    
    if (decrypted != plaintext) {
        std::cerr << "Decryption failed" << std::endl;
        return 1;
    }
    
    std::cout << "Decryption successful" << std::endl;
    std::cout << "Original: " << plaintext << std::endl;
    std::cout << "Decrypted: " << decrypted << std::endl;
    
    // Cleanup
    EVP_cleanup();
    
    return 0;
}