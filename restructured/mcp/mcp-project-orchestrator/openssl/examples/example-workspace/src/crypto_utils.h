#ifndef CRYPTO_UTILS_H
#define CRYPTO_UTILS_H

#include <string>
#include <vector>

/**
 * Encrypt a string using AES-256-GCM.
 * 
 * @param plaintext The text to encrypt
 * @param key The encryption key (must be 32 bytes)
 * @return The encrypted data as a hex string, or empty string on error
 */
std::string encrypt_aes256_gcm(const std::string& plaintext, const std::string& key);

/**
 * Decrypt a string using AES-256-GCM.
 * 
 * @param ciphertext The encrypted data as a hex string
 * @param key The decryption key (must be 32 bytes)
 * @return The decrypted text, or empty string on error
 */
std::string decrypt_aes256_gcm(const std::string& ciphertext, const std::string& key);

/**
 * Generate a random key for AES-256.
 * 
 * @return A 32-byte random key as a hex string
 */
std::string generate_aes256_key();

/**
 * Hash a string using SHA-256.
 * 
 * @param input The string to hash
 * @return The hash as a hex string
 */
std::string sha256_hash(const std::string& input);

#endif // CRYPTO_UTILS_H