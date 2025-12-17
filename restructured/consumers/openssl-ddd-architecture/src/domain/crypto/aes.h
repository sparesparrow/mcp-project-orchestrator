/**
 * @file aes.h
 * @brief AES (Advanced Encryption Standard) header - Domain Layer
 * 
 * This header defines the AES cryptographic algorithm interface
 * following DDD principles. This is pure domain logic with no external dependencies.
 * 
 * Layer: Domain (Crypto) - Business Logic Core
 * Dependencies: None (pure cryptographic computations)
 */

#ifndef AES_H
#define AES_H

#include <stdint.h>
#include <stddef.h>

#ifdef __cplusplus
extern "C" {
#endif

/**
 * @brief AES key sizes
 */
typedef enum {
    AES_KEY_128 = 128,
    AES_KEY_192 = 192,
    AES_KEY_256 = 256
} aes_key_size_t;

/**
 * @brief AES operation results
 */
typedef enum {
    AES_SUCCESS = 0,
    AES_ERROR_INVALID_PARAM = -1,
    AES_ERROR_INVALID_KEY_SIZE = -2,
    AES_ERROR_INVALID_BLOCK_SIZE = -3,
    AES_ERROR_MEMORY_ALLOCATION = -4
} aes_result_t;

/**
 * @brief AES context structure (opaque)
 */
typedef struct aes_context aes_context_t;

/**
 * @brief Initialize AES context with key
 * 
 * @param ctx AES context to initialize
 * @param key Encryption/decryption key
 * @param key_size Key size (128, 192, or 256 bits)
 * @return aes_result_t Operation result
 */
aes_result_t aes_init(aes_context_t *ctx, const uint8_t *key, aes_key_size_t key_size);

/**
 * @brief Encrypt a single AES block (16 bytes)
 * 
 * @param ctx Initialized AES context
 * @param input Plaintext block (16 bytes)
 * @param output Ciphertext block (16 bytes)
 * @return aes_result_t Operation result
 */
aes_result_t aes_encrypt_block(aes_context_t *ctx, const uint8_t input[16], uint8_t output[16]);

/**
 * @brief Decrypt a single AES block (16 bytes)
 * 
 * @param ctx Initialized AES context
 * @param input Ciphertext block (16 bytes)
 * @param output Plaintext block (16 bytes)
 * @return aes_result_t Operation result
 */
aes_result_t aes_decrypt_block(aes_context_t *ctx, const uint8_t input[16], uint8_t output[16]);

/**
 * @brief Clean up AES context and clear sensitive data
 * 
 * @param ctx AES context to clean up
 */
void aes_cleanup(aes_context_t *ctx);

#ifdef __cplusplus
}
#endif

#endif // AES_H