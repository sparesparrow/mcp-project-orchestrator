/**
 * @file tls1_3.h
 * @brief TLS 1.3 protocol header - Application Layer
 * 
 * This header defines the TLS 1.3 protocol interface
 * following DDD principles. This layer orchestrates domain objects
 * to fulfill business requirements without implementing crypto algorithms.
 * 
 * Layer: Application (SSL/TLS) - Use Case Orchestration
 * Dependencies: Domain layer interfaces, no crypto implementation
 */

#ifndef TLS1_3_H
#define TLS1_3_H

#include <stdint.h>
#include <stddef.h>

#ifdef __cplusplus
extern "C" {
#endif

/**
 * @brief TLS 1.3 handshake states
 */
typedef enum {
    TLS_STATE_CLIENT_HELLO,
    TLS_STATE_SERVER_HELLO,
    TLS_STATE_CHANGE_CIPHER_SPEC,
    TLS_STATE_FINISHED,
    TLS_STATE_APPLICATION_DATA,
    TLS_STATE_ERROR
} tls_handshake_state_t;

/**
 * @brief TLS operation results
 */
typedef enum {
    TLS_SUCCESS = 0,
    TLS_ERROR_INVALID_PARAM = -1,
    TLS_ERROR_INVALID_STATE = -2,
    TLS_ERROR_INVALID_MESSAGE = -3,
    TLS_ERROR_INVALID_BLOCK_SIZE = -4,
    TLS_ERROR_MEMORY_ALLOCATION = -5,
    TLS_ERROR_CRYPTO_FAILURE = -6,
    TLS_ERROR_UNSUPPORTED_MESSAGE = -7
} tls_result_t;

/**
 * @brief TLS 1.3 context structure (opaque)
 */
typedef struct tls1_3_context tls1_3_context_t;

/**
 * @brief Initialize TLS 1.3 context
 * 
 * @param ctx TLS context to initialize
 * @return tls_result_t Operation result
 */
tls_result_t tls1_3_init(tls1_3_context_t *ctx);

/**
 * @brief Process TLS 1.3 handshake message
 * 
 * @param ctx TLS context
 * @param data Handshake message data
 * @param data_len Length of handshake message
 * @return tls_result_t Operation result
 */
tls_result_t tls1_3_process_handshake(tls1_3_context_t *ctx, 
                                     const uint8_t *data, 
                                     size_t data_len);

/**
 * @brief Encrypt application data
 * 
 * @param ctx TLS context
 * @param plaintext Plaintext data to encrypt
 * @param plaintext_len Length of plaintext data
 * @param ciphertext Buffer for encrypted data
 * @param ciphertext_len Length of encrypted data
 * @return tls_result_t Operation result
 */
tls_result_t tls1_3_encrypt_data(tls1_3_context_t *ctx, 
                                const uint8_t *plaintext, 
                                size_t plaintext_len,
                                uint8_t *ciphertext, 
                                size_t *ciphertext_len);

/**
 * @brief Decrypt application data
 * 
 * @param ctx TLS context
 * @param ciphertext Encrypted data to decrypt
 * @param ciphertext_len Length of encrypted data
 * @param plaintext Buffer for decrypted data
 * @param plaintext_len Length of decrypted data
 * @return tls_result_t Operation result
 */
tls_result_t tls1_3_decrypt_data(tls1_3_context_t *ctx, 
                                const uint8_t *ciphertext, 
                                size_t ciphertext_len,
                                uint8_t *plaintext, 
                                size_t *plaintext_len);

/**
 * @brief Get current handshake state
 * 
 * @param ctx TLS context
 * @return tls_handshake_state_t Current handshake state
 */
tls_handshake_state_t tls1_3_get_state(const tls1_3_context_t *ctx);

/**
 * @brief Clean up TLS 1.3 context
 * 
 * @param ctx TLS context to clean up
 */
void tls1_3_cleanup(tls1_3_context_t *ctx);

#ifdef __cplusplus
}
#endif

#endif // TLS1_3_H